# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The address-policy contract and the shared assessment toolkit.

This module defines three things the rest of the policy layer builds on:

* :class:`PolicyContext` — the small, immutable envelope of the facts a
  policy needs beyond the address itself (the assessment date, an
  optional country hint, and the message type under review).
* :class:`AddressPolicy` — the runtime-checkable :class:`typing.Protocol`
  every policy satisfies, whether it is a built-in or a premium plugin.
* :class:`BasePolicy` — an abstract base that concrete policies subclass
  to inherit the shared finding builders (missing town/country, non-ISO
  country, ``AdrLine`` overflow, structured-field overflow, hybrid
  residual) so each policy body stays short and consistent.

Clause citations for findings are loaded lazily from the JSON files under
``structured_address_fix/data/rulebook_clauses``.
"""

from __future__ import annotations

import abc
import json
from collections.abc import Mapping
from datetime import date
from functools import cache
from importlib import resources
from typing import ClassVar, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from structured_address_fix.config import NOV_2026_CLIFF
from structured_address_fix.domain.address import (
    MAX_ADDRESS_LINE,
    MAX_ADDRESS_LINE_COUNT,
    MAX_BUILDING_NAME,
    MAX_BUILDING_NUMBER,
    MAX_COUNTRY_SUB_DIVISION,
    MAX_DEPARTMENT,
    MAX_DISTRICT_NAME,
    MAX_FLOOR,
    MAX_POST_BOX,
    MAX_POST_CODE,
    MAX_ROOM,
    MAX_STREET_NAME,
    MAX_SUB_DEPARTMENT,
    MAX_TOWN_LOCATION_NAME,
    MAX_TOWN_NAME,
    CanonicalAddress,
)
from structured_address_fix.domain.enums import MessageType, Severity
from structured_address_fix.domain.findings import FindingCode, RiskFinding

#: Policy tiers. ``oss`` policies ship with the package; ``premium``
#: policies arrive through the licensed plugin registry.
PolicyTier = Literal["oss", "premium"]

#: The ISO 20022 ``PostalAddress27`` maximum length for each structured
#: element, keyed by :class:`CanonicalAddress` field name. Scheme profiles
#: may pass a tightened mapping to
#: :meth:`BasePolicy._structured_field_overflow`.
ISO_STRUCTURED_LIMITS: Mapping[str, int] = {
    "department": MAX_DEPARTMENT,
    "sub_department": MAX_SUB_DEPARTMENT,
    "street_name": MAX_STREET_NAME,
    "building_number": MAX_BUILDING_NUMBER,
    "building_name": MAX_BUILDING_NAME,
    "floor": MAX_FLOOR,
    "post_box": MAX_POST_BOX,
    "room": MAX_ROOM,
    "post_code": MAX_POST_CODE,
    "town_name": MAX_TOWN_NAME,
    "town_location_name": MAX_TOWN_LOCATION_NAME,
    "district_name": MAX_DISTRICT_NAME,
    "country_sub_division": MAX_COUNTRY_SUB_DIVISION,
}

# The canonical source of truth for ISO 3166-1 alpha-2 validation is
# ``structured_address_fix.adapters.iso3166``; :func:`iso_country_is_valid`
# prefers it via a lazy import and only falls back to this bundled set when
# that adapter is not importable, so this module loads cleanly regardless
# of build ordering.
_ISO_3166_1_ALPHA_2: frozenset[str] = frozenset(
    (
        "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG "
        "BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI "
        "CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH "
        "ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ "
        "GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT "
        "JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS "
        "LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU "
        "MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG "
        "PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG "
        "SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK "
        "TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU "
        "WF WS YE YT ZA ZM ZW"
    ).split()
)


def iso_country_is_valid(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid ISO 3166-1 alpha-2 code.

    Prefers the canonical ``adapters.iso3166`` implementation via a lazy
    import; when that module is not yet importable, it falls back to the
    bundled :data:`_ISO_3166_1_ALPHA_2` set so callers behave identically
    either way. Matching is case-insensitive.
    """
    try:
        from structured_address_fix.adapters.iso3166 import (
            is_iso_3166_1_alpha_2,
        )
    except ImportError:
        return value.upper() in _ISO_3166_1_ALPHA_2
    return is_iso_3166_1_alpha_2(value)


@cache
def _load_clauses(policy_id: str) -> Mapping[str, str]:
    """Load and cache the rulebook clause map for ``policy_id``.

    Reads ``data/rulebook_clauses/<policy_id>.json`` and returns a mapping
    of clause key to short, citable text.
    """
    resource = (
        resources.files("structured_address_fix")
        / "data"
        / "rulebook_clauses"
        / f"{policy_id}.json"
    )
    raw = json.loads(resource.read_text(encoding="utf-8"))
    return {str(key): str(text) for key, text in raw.items()}


class PolicyContext(BaseModel):
    """Immutable context for a single policy assessment.

    Kept deliberately small: a policy reasons about the address plus the
    date the assessment is made (which decides cliff wording), an optional
    ISO 3166-1 alpha-2 country hint, and the ISO 20022 message type under
    review.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    as_of: date = Field(default_factory=date.today)
    country_hint: str | None = None
    message_type: MessageType | None = None


@runtime_checkable
class AddressPolicy(Protocol):
    """The contract every address policy satisfies.

    Runtime-checkable so the registry can defensively verify that a
    plugin-supplied object really is a policy. Implementations expose three
    class-level identity attributes and two methods.
    """

    #: Stable policy identifier (matches a rulebook-clause file name).
    id: ClassVar[str]
    #: Human-readable policy title.
    title: ClassVar[str]
    #: Distribution tier: ``"oss"`` or ``"premium"``.
    tier: ClassVar[PolicyTier]

    def assess(
        self, address: CanonicalAddress, ctx: PolicyContext
    ) -> list[RiskFinding]:
        """Return every risk finding this policy raises for ``address``."""
        ...

    def target(self, address: CanonicalAddress) -> CanonicalAddress:
        """Return the ideal compliant shape of ``address`` for this policy."""
        ...


class BasePolicy(abc.ABC):
    """Abstract base providing shared finding builders for policies.

    Concrete policies set :attr:`id`, :attr:`title`, and :attr:`tier`, then
    implement :meth:`assess` by composing the ``_*`` helpers below. The
    default :meth:`target` returns the address with residual ``AdrLine``
    cleared, which is the compliant shape for every built-in policy.
    """

    id: ClassVar[str]
    title: ClassVar[str]
    tier: ClassVar[PolicyTier] = "oss"

    @abc.abstractmethod
    def assess(
        self, address: CanonicalAddress, ctx: PolicyContext
    ) -> list[RiskFinding]:
        """Return every risk finding this policy raises for ``address``."""
        raise NotImplementedError

    def target(self, address: CanonicalAddress) -> CanonicalAddress:
        """Return ``address`` with any residual ``AdrLine`` removed.

        This is the ideal compliant shape for the built-in policies: the
        same structured data, but no unstructured residue. Missing
        ``town_name`` / ``country`` cannot be invented here and are left to
        remediation.
        """
        return address.model_copy(update={"address_lines": ()})

    # -- Clause + finding builders ------------------------------------------

    def _clause(self, key: str) -> str:
        """Return the citable rulebook text for ``key`` under this policy."""
        return _load_clauses(self.id)[key]

    def _finding(
        self,
        code: FindingCode,
        severity: Severity,
        message: str,
        clause: str,
        *,
        rejects_payment: bool = False,
        location: str = "/",
    ) -> RiskFinding:
        """Build a :class:`RiskFinding` stamped with this policy's id."""
        return RiskFinding(
            code=code,
            severity=severity,
            message=message,
            policy_id=self.id,
            location=location,
            rulebook_clause=self._clause(clause),
            rejects_payment=rejects_payment,
        )

    # -- Shared structural checks -------------------------------------------

    def _missing_town(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        rejects_payment: bool = False,
    ) -> RiskFinding | None:
        """Flag a missing ``town_name`` (``TwnNm``), else ``None``."""
        if address.town_name is not None:
            return None
        return self._finding(
            FindingCode.MISSING_TOWN,
            severity,
            "Town Name (TwnNm) is missing.",
            clause,
            rejects_payment=rejects_payment,
        )

    def _missing_country(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        rejects_payment: bool = False,
    ) -> RiskFinding | None:
        """Flag a missing ``country`` (``Ctry``), else ``None``."""
        if address.country is not None:
            return None
        return self._finding(
            FindingCode.MISSING_COUNTRY,
            severity,
            "Country (Ctry) is missing.",
            clause,
            rejects_payment=rejects_payment,
        )

    def _non_iso_country(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        rejects_payment: bool = False,
    ) -> RiskFinding | None:
        """Flag a present-but-invalid ISO country code, else ``None``."""
        if address.country is None or iso_country_is_valid(address.country):
            return None
        return self._finding(
            FindingCode.NON_ISO_COUNTRY_CODE,
            severity,
            f"Country {address.country!r} is not a valid ISO 3166-1 "
            "alpha-2 code.",
            clause,
            rejects_payment=rejects_payment,
            location="/Ctry",
        )

    def _adrline_overflow(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        max_lines: int = MAX_ADDRESS_LINE_COUNT,
        rejects_payment: bool = False,
    ) -> RiskFinding | None:
        """Flag too many ``AdrLine`` or an over-length line, else ``None``."""
        too_many = len(address.address_lines) > max_lines
        too_long = any(
            len(line) > MAX_ADDRESS_LINE for line in address.address_lines
        )
        if not (too_many or too_long):
            return None
        return self._finding(
            FindingCode.ADRLINE_OVERFLOW,
            severity,
            f"AdrLine exceeds the permitted {max_lines} lines of "
            f"{MAX_ADDRESS_LINE} characters.",
            clause,
            rejects_payment=rejects_payment,
            location="/AdrLine",
        )

    def _structured_field_overflow(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        limits: Mapping[str, int] = ISO_STRUCTURED_LIMITS,
        rejects_payment: bool = False,
    ) -> list[RiskFinding]:
        """Flag every structured field longer than its ``limits`` maximum."""
        findings: list[RiskFinding] = []
        for name, maximum in limits.items():
            value = getattr(address, name)
            if value is not None and len(value) > maximum:
                findings.append(
                    self._finding(
                        FindingCode.STRUCTURED_FIELD_OVERFLOW,
                        severity,
                        f"Structured field {name!r} exceeds its "
                        f"{maximum}-character maximum.",
                        clause,
                        rejects_payment=rejects_payment,
                        location=f"/{name}",
                    )
                )
        return findings

    def _hybrid_residual(
        self,
        address: CanonicalAddress,
        *,
        severity: Severity,
        clause: str,
        rejects_payment: bool = False,
    ) -> RiskFinding | None:
        """Flag residual ``AdrLine`` on a hybrid address, else ``None``."""
        if not address.address_lines:
            return None
        return self._finding(
            FindingCode.HYBRID_RESIDUAL_ADRLINE,
            severity,
            "Hybrid address still carries residual AdrLine text.",
            clause,
            rejects_payment=rejects_payment,
            location="/AdrLine",
        )


def compact(
    *parts: RiskFinding | list[RiskFinding] | None,
) -> list[RiskFinding]:
    """Flatten optional findings and finding lists into one flat list.

    ``None`` parts are dropped, lists are extended, and single findings are
    appended, preserving order.
    """
    out: list[RiskFinding] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, list):
            out.extend(part)
        else:
            out.append(part)
    return out


def cliff_phrase(ctx: PolicyContext) -> str:
    """Return cliff wording keyed on ``ctx.as_of`` versus the cliff date.

    ``"in force from"`` before the November 2026 cliff, ``"since"`` on or
    after it. The finding stands either way; only the wording changes.
    """
    if ctx.as_of < NOV_2026_CLIFF:
        return "in force from"
    return "since"
