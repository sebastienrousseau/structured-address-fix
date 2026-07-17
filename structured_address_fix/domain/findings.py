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

"""Risk findings raised by policies against a canonical address.

Finding codes are a stable public API: a code's meaning is fixed once
released, and a changed rule earns a new code rather than repurposing an
existing one. Callers key remediation, dashboards, and rulebook citations
off these codes, so they must never drift.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from structured_address_fix.domain.enums import PartyRole, Severity


class FindingCode(StrEnum):
    """Stable identifiers for every risk a policy can raise.

    The ``SAF`` prefix namespaces these against pack-specific codes, which
    carry their own prefixes.
    """

    UNSTRUCTURED_ONLY = "SAF001"
    """Address is ``AdrLine``-only; rejected from the cliff date."""

    MISSING_COUNTRY = "SAF002"
    """No ``Ctry`` element; mandatory for cross-border from the cliff."""

    MISSING_TOWN = "SAF003"
    """No ``TwnNm`` element; mandatory for the hybrid minimum bar."""

    ADRLINE_OVERFLOW = "SAF004"
    """More than seven ``AdrLine`` lines, or a line over 70 characters."""

    HYBRID_RESIDUAL_ADRLINE = "SAF005"
    """Structured address still carries residual ``AdrLine`` text."""

    NON_ISO_COUNTRY_CODE = "SAF006"
    """``Ctry`` is not a valid ISO 3166-1 alpha-2 code."""

    NON_LATIN_CHARACTERS = "SAF007"
    """Address contains characters outside the SWIFT-permitted set."""

    STRUCTURED_FIELD_OVERFLOW = "SAF008"
    """A structured element exceeds its ISO 20022 maximum length."""


class RiskFinding(BaseModel):
    """A single compliance risk located in an address or message.

    Immutable. ``location`` is a JSON pointer into the source message (or
    ``"/"`` for a bare address), so a finding always points back to the
    exact element that raised it.
    """

    model_config = ConfigDict(frozen=True)

    code: FindingCode
    severity: Severity
    message: str
    policy_id: str
    location: str = "/"
    party_role: PartyRole | None = None
    rulebook_clause: str | None = None
    rejects_payment: bool = False
