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

"""Unit tests for the policy contract and shared assessment toolkit."""

from __future__ import annotations

import sys
import types
from datetime import date

import pytest
from pydantic import ValidationError

from structured_address_fix.domain import (
    CanonicalAddress,
    FindingCode,
    MessageType,
    Severity,
)
from structured_address_fix.policies.base import (
    ISO_STRUCTURED_LIMITS,
    AddressPolicy,
    BasePolicy,
    PolicyContext,
    cliff_phrase,
    compact,
    iso_country_is_valid,
)

_ISO_MODULE = "structured_address_fix.adapters.iso3166"


class _Probe(BasePolicy):
    """Minimal concrete policy exposing the shared helpers for testing."""

    id = "cbpr-2026"
    title = "probe"
    tier = "oss"

    def assess(self, address, ctx):  # pragma: no cover - unused here
        """Return no findings; the probe drives helpers directly."""
        return []


@pytest.fixture()
def probe() -> _Probe:
    """Return a probe policy bound to the CBPR clause file."""
    return _Probe()


def _addr(**kwargs: object) -> CanonicalAddress:
    """Build a :class:`CanonicalAddress` from keyword fields."""
    return CanonicalAddress(**kwargs)  # type: ignore[arg-type]


# -- PolicyContext ----------------------------------------------------------


def test_policy_context_defaults_as_of_to_today() -> None:
    """An unspecified ``as_of`` defaults to today's date."""
    ctx = PolicyContext()
    assert ctx.as_of == date.today()
    assert ctx.country_hint is None
    assert ctx.message_type is None


def test_policy_context_is_frozen() -> None:
    """The context is immutable and accepts the documented fields."""
    ctx = PolicyContext(
        as_of=date(2026, 1, 1),
        country_hint="GB",
        message_type=MessageType.PACS_008,
    )
    assert ctx.message_type is MessageType.PACS_008
    with pytest.raises(ValidationError):
        ctx.country_hint = "FR"  # type: ignore[misc]


# -- Protocol conformance ---------------------------------------------------


def test_base_policy_satisfies_protocol(probe: _Probe) -> None:
    """A ``BasePolicy`` subclass is a runtime ``AddressPolicy``."""
    assert isinstance(probe, AddressPolicy)


def test_non_policy_is_not_an_address_policy() -> None:
    """An unrelated object is not an ``AddressPolicy``."""
    assert not isinstance(object(), AddressPolicy)


# -- iso_country_is_valid (lazy import + fallback) --------------------------


def test_iso_valid_falls_back_when_adapter_absent() -> None:
    """The bundled set is used when the adapter cannot be imported."""
    original = sys.modules.get(_ISO_MODULE)
    sys.modules[_ISO_MODULE] = None  # force ImportError on import
    try:
        assert iso_country_is_valid("GB") is True
        assert iso_country_is_valid("us") is True  # fallback upper-cases
        assert not iso_country_is_valid("ZZ")
    finally:
        if original is not None:
            sys.modules[_ISO_MODULE] = original
        else:
            sys.modules.pop(_ISO_MODULE, None)


def test_iso_valid_prefers_adapter_when_importable() -> None:
    """When the adapter is importable, it is used in preference."""
    fake = types.ModuleType(_ISO_MODULE)
    calls: list[str] = []

    def _is(value: str) -> bool:
        calls.append(value)
        return value == "QQ"

    fake.is_iso_3166_1_alpha_2 = _is  # type: ignore[attr-defined]
    original = sys.modules.get(_ISO_MODULE)
    sys.modules[_ISO_MODULE] = fake
    try:
        assert iso_country_is_valid("QQ") is True
        assert iso_country_is_valid("GB") is False
    finally:
        if original is not None:
            sys.modules[_ISO_MODULE] = original
        else:
            sys.modules.pop(_ISO_MODULE, None)
    assert calls == ["QQ", "GB"]


# -- Finding builders -------------------------------------------------------


def test_missing_town_present_and_absent(probe: _Probe) -> None:
    """The town check fires only when ``town_name`` is absent."""
    present = _addr(town_name="Paris", country="FR")
    assert (
        probe._missing_town(
            present, severity=Severity.ERROR, clause="mandatory_town"
        )
        is None
    )
    absent = _addr(country="FR", address_lines=("x",))
    finding = probe._missing_town(
        absent,
        severity=Severity.CRITICAL,
        clause="mandatory_town",
        rejects_payment=True,
    )
    assert finding is not None
    assert finding.code is FindingCode.MISSING_TOWN
    assert finding.rejects_payment is True
    assert finding.policy_id == "cbpr-2026"
    assert finding.rulebook_clause


def test_missing_country_present_and_absent(probe: _Probe) -> None:
    """The country check fires only when ``country`` is absent."""
    present = _addr(town_name="Paris", country="FR")
    assert (
        probe._missing_country(
            present, severity=Severity.ERROR, clause="mandatory_country"
        )
        is None
    )
    absent = _addr(town_name="Paris", address_lines=("x",))
    finding = probe._missing_country(
        absent, severity=Severity.ERROR, clause="mandatory_country"
    )
    assert finding is not None
    assert finding.code is FindingCode.MISSING_COUNTRY


def test_non_iso_country_none_valid_invalid(probe: _Probe) -> None:
    """The ISO check skips absent/valid codes and flags invalid ones."""
    absent = _addr(address_lines=("x",))
    assert (
        probe._non_iso_country(
            absent, severity=Severity.ERROR, clause="non_iso_country"
        )
        is None
    )
    valid = _addr(town_name="Paris", country="FR")
    assert (
        probe._non_iso_country(
            valid, severity=Severity.ERROR, clause="non_iso_country"
        )
        is None
    )
    invalid = _addr(town_name="Nowhere", country="ZZ")
    finding = probe._non_iso_country(
        invalid, severity=Severity.ERROR, clause="non_iso_country"
    )
    assert finding is not None
    assert finding.code is FindingCode.NON_ISO_COUNTRY_CODE
    assert finding.location == "/Ctry"


def test_adrline_overflow_count_and_length(probe: _Probe) -> None:
    """Overflow fires on too many lines or an over-length line."""
    ok = _addr(town_name="Paris", country="FR", address_lines=("short",))
    assert (
        probe._adrline_overflow(
            ok, severity=Severity.ERROR, clause="adrline_overflow"
        )
        is None
    )
    too_many = _addr(
        town_name="Paris",
        country="FR",
        address_lines=("a", "b", "c"),
    )
    finding = probe._adrline_overflow(
        too_many,
        severity=Severity.ERROR,
        clause="adrline_overflow",
        max_lines=2,
    )
    assert finding is not None
    assert finding.code is FindingCode.ADRLINE_OVERFLOW
    too_long = _addr(
        town_name="Paris",
        country="FR",
        address_lines=("x" * 71,),
    )
    assert (
        probe._adrline_overflow(
            too_long, severity=Severity.ERROR, clause="adrline_overflow"
        )
        is not None
    )


def test_structured_field_overflow_under_and_over(probe: _Probe) -> None:
    """Structured overflow fires only when a field exceeds its limit."""
    address = _addr(town_name="Paris", country="FR", street_name="Rue")
    assert (
        probe._structured_field_overflow(
            address,
            severity=Severity.ERROR,
            clause="structured_overflow",
        )
        == []
    )
    tight = probe._structured_field_overflow(
        address,
        severity=Severity.ERROR,
        clause="structured_overflow",
        limits={"street_name": 2},
    )
    assert len(tight) == 1
    assert tight[0].code is FindingCode.STRUCTURED_FIELD_OVERFLOW
    assert tight[0].location == "/street_name"


def test_hybrid_residual_present_and_absent(probe: _Probe) -> None:
    """Hybrid residual fires only when address lines remain."""
    without = _addr(town_name="Paris", country="FR", street_name="Rue")
    assert (
        probe._hybrid_residual(
            without, severity=Severity.WARNING, clause="hybrid_residual"
        )
        is None
    )
    with_lines = _addr(
        town_name="Paris", country="FR", address_lines=("Apt 1",)
    )
    finding = probe._hybrid_residual(
        with_lines, severity=Severity.WARNING, clause="hybrid_residual"
    )
    assert finding is not None
    assert finding.code is FindingCode.HYBRID_RESIDUAL_ADRLINE


# -- target -----------------------------------------------------------------


def test_target_clears_residual_address_lines(probe: _Probe) -> None:
    """The default target strips residual ``AdrLine`` and keeps data."""
    address = _addr(
        town_name="Paris",
        country="FR",
        street_name="Rue",
        address_lines=("Apt 1",),
    )
    target = probe.target(address)
    assert target.address_lines == ()
    assert target.street_name == "Rue"
    assert target.town_name == "Paris"


# -- compact / cliff_phrase -------------------------------------------------


def test_compact_flattens_none_list_and_single(probe: _Probe) -> None:
    """``compact`` drops ``None``, extends lists, and appends singles."""
    single = probe._finding(
        FindingCode.UNSTRUCTURED_ONLY,
        Severity.CRITICAL,
        "msg",
        "reject_unstructured",
    )
    result = compact(None, single, [single, single])
    assert result == [single, single, single]


def test_cliff_phrase_before_and_after() -> None:
    """The cliff phrase switches at the November 2026 cliff date."""
    assert cliff_phrase(PolicyContext(as_of=date(2026, 1, 1))) == (
        "in force from"
    )
    assert cliff_phrase(PolicyContext(as_of=date(2026, 12, 1))) == "since"


def test_iso_structured_limits_cover_all_detail_fields() -> None:
    """The ISO limit table exposes every structured detail field."""
    assert "street_name" in ISO_STRUCTURED_LIMITS
    assert ISO_STRUCTURED_LIMITS["town_name"] == 35
