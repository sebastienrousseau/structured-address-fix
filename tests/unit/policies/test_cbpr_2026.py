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

"""Finding-matrix tests for the flagship CBPR+ UG2026 policy."""

from __future__ import annotations

from datetime import date

from structured_address_fix.domain import (
    CanonicalAddress,
    FindingCode,
    Severity,
)
from structured_address_fix.policies import Cbpr2026Policy, PolicyContext

POLICY = Cbpr2026Policy()
CTX = PolicyContext(as_of=date(2026, 12, 1))


def _by_code(
    address: CanonicalAddress,
) -> dict[FindingCode, tuple[Severity, bool]]:
    """Map each finding's code to its (severity, rejects_payment)."""
    return {
        f.code: (f.severity, f.rejects_payment)
        for f in POLICY.assess(address, CTX)
    }


def test_identity() -> None:
    """The policy advertises its stable id, title, and tier."""
    assert POLICY.id == "cbpr-2026"
    assert POLICY.tier == "oss"
    assert POLICY.title


def test_structured_passes(structured: CanonicalAddress) -> None:
    """A fully structured address raises no findings."""
    assert POLICY.assess(structured, CTX) == []


def test_hybrid_flags_residual_warning(hybrid: CanonicalAddress) -> None:
    """A hybrid address is permitted but its residual line warns."""
    matrix = _by_code(hybrid)
    assert matrix == {
        FindingCode.HYBRID_RESIDUAL_ADRLINE: (Severity.WARNING, False)
    }


def test_unstructured_rejected(unstructured: CanonicalAddress) -> None:
    """Unstructured raises missing town + country + unstructured, all crit."""
    matrix = _by_code(unstructured)
    assert matrix == {
        FindingCode.MISSING_TOWN: (Severity.CRITICAL, True),
        FindingCode.MISSING_COUNTRY: (Severity.CRITICAL, True),
        FindingCode.UNSTRUCTURED_ONLY: (Severity.CRITICAL, True),
    }


def test_missing_country_only(missing_country: CanonicalAddress) -> None:
    """Town present but country absent: no missing-town finding."""
    matrix = _by_code(missing_country)
    assert matrix == {
        FindingCode.MISSING_COUNTRY: (Severity.CRITICAL, True),
        FindingCode.UNSTRUCTURED_ONLY: (Severity.CRITICAL, True),
    }


def test_bad_country_flagged(bad_country: CanonicalAddress) -> None:
    """A structured address with a non-ISO country flags SAF006 only."""
    matrix = _by_code(bad_country)
    assert matrix == {
        FindingCode.NON_ISO_COUNTRY_CODE: (Severity.ERROR, False)
    }


def test_overflow_flagged(overflow: CanonicalAddress) -> None:
    """An over-length hybrid line flags both residual and overflow."""
    matrix = _by_code(overflow)
    assert matrix == {
        FindingCode.HYBRID_RESIDUAL_ADRLINE: (Severity.WARNING, False),
        FindingCode.ADRLINE_OVERFLOW: (Severity.ERROR, False),
    }


def test_cliff_wording_before_and_after(
    unstructured: CanonicalAddress,
) -> None:
    """The unstructured message wording tracks the assessment date."""
    before = Cbpr2026Policy().assess(
        unstructured, PolicyContext(as_of=date(2026, 1, 1))
    )
    after = Cbpr2026Policy().assess(
        unstructured, PolicyContext(as_of=date(2026, 12, 1))
    )
    before_msg = next(
        f.message for f in before if f.code is FindingCode.UNSTRUCTURED_ONLY
    )
    after_msg = next(
        f.message for f in after if f.code is FindingCode.UNSTRUCTURED_ONLY
    )
    assert "in force from" in before_msg
    assert "since" in after_msg


def test_target_clears_residual(hybrid: CanonicalAddress) -> None:
    """The policy target removes residual AdrLine."""
    assert POLICY.target(hybrid).address_lines == ()
