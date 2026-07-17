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

"""Finding-matrix tests for the strict HVPS+ policy."""

from __future__ import annotations

from structured_address_fix.domain import (
    CanonicalAddress,
    FindingCode,
    Severity,
)
from structured_address_fix.policies import HvpsPlusPolicy, PolicyContext

POLICY = HvpsPlusPolicy()
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
    assert POLICY.id == "hvps-plus"
    assert POLICY.tier == "oss"


def test_structured_passes(structured: CanonicalAddress) -> None:
    """A fully structured address raises no findings."""
    assert POLICY.assess(structured, CTX) == []


def test_hybrid_residual_is_rejecting_error(
    hybrid: CanonicalAddress,
) -> None:
    """HVPS+ escalates residual AdrLine to a rejecting error."""
    assert _by_code(hybrid) == {
        FindingCode.HYBRID_RESIDUAL_ADRLINE: (Severity.ERROR, True)
    }


def test_unstructured_rejected(unstructured: CanonicalAddress) -> None:
    """Unstructured raises missing town + country + unstructured, all crit."""
    assert _by_code(unstructured) == {
        FindingCode.MISSING_TOWN: (Severity.CRITICAL, True),
        FindingCode.MISSING_COUNTRY: (Severity.CRITICAL, True),
        FindingCode.UNSTRUCTURED_ONLY: (Severity.CRITICAL, True),
    }


def test_bad_country(bad_country: CanonicalAddress) -> None:
    """A non-ISO country is an HVPS+ error."""
    assert _by_code(bad_country) == {
        FindingCode.NON_ISO_COUNTRY_CODE: (Severity.ERROR, False)
    }


def test_overflow(overflow: CanonicalAddress) -> None:
    """An over-length hybrid line flags rejecting residual + overflow."""
    assert _by_code(overflow) == {
        FindingCode.HYBRID_RESIDUAL_ADRLINE: (Severity.ERROR, True),
        FindingCode.ADRLINE_OVERFLOW: (Severity.ERROR, False),
    }
