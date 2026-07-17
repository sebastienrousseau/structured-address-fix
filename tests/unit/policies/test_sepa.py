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

"""Finding-matrix tests for the SEPA rulebook policy."""

from __future__ import annotations

from structured_address_fix.domain import (
    CanonicalAddress,
    FindingCode,
    Severity,
)
from structured_address_fix.policies import PolicyContext, SepaPolicy

POLICY = SepaPolicy()
CTX = PolicyContext()


def _by_code(
    address: CanonicalAddress,
) -> dict[FindingCode, tuple[Severity, bool]]:
    """Map each finding's code to its (severity, rejects_payment)."""
    return {
        f.code: (f.severity, f.rejects_payment)
        for f in POLICY.assess(address, CTX)
    }


def test_identity() -> None:
    """The policy advertises its stable id and tier."""
    assert POLICY.id == "sepa"
    assert POLICY.tier == "oss"


def test_structured_passes(structured: CanonicalAddress) -> None:
    """Town + country present with no overflow raises nothing."""
    assert POLICY.assess(structured, CTX) == []


def test_two_lines_within_cap() -> None:
    """Two residual AdrLine are within the SEPA cap."""
    address = CanonicalAddress(
        town_name="Paris", country="FR", address_lines=("a", "b")
    )
    assert POLICY.assess(address, CTX) == []


def test_missing_town(missing_town: CanonicalAddress) -> None:
    """A missing town is a non-rejecting SEPA error."""
    assert _by_code(missing_town) == {
        FindingCode.MISSING_TOWN: (Severity.ERROR, False)
    }


def test_missing_country(missing_country: CanonicalAddress) -> None:
    """A missing country rejects the payment under SEPA."""
    assert _by_code(missing_country) == {
        FindingCode.MISSING_COUNTRY: (Severity.ERROR, True)
    }


def test_bad_country(bad_country: CanonicalAddress) -> None:
    """A non-ISO country is a SEPA error."""
    assert _by_code(bad_country) == {
        FindingCode.NON_ISO_COUNTRY_CODE: (Severity.ERROR, False)
    }


def test_adrline_cap_exceeded() -> None:
    """More than two AdrLine breaches the SEPA cap."""
    address = CanonicalAddress(
        town_name="Paris", country="FR", address_lines=("a", "b", "c")
    )
    assert _by_code(address) == {
        FindingCode.ADRLINE_OVERFLOW: (Severity.ERROR, False)
    }
