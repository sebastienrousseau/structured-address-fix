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

"""Finding-matrix tests for the generic structural baseline policy."""

from __future__ import annotations

from structured_address_fix.domain import (
    CanonicalAddress,
    FindingCode,
    Severity,
)
from structured_address_fix.policies import (
    GenericStructuredPolicy,
    PolicyContext,
)

POLICY = GenericStructuredPolicy()
CTX = PolicyContext()


def _codes(address: CanonicalAddress) -> dict[FindingCode, Severity]:
    """Map each finding's code to its severity."""
    return {f.code: f.severity for f in POLICY.assess(address, CTX)}


def test_identity() -> None:
    """The policy advertises its stable id and tier."""
    assert POLICY.id == "generic-structured"
    assert POLICY.tier == "oss"


def test_structured_passes(structured: CanonicalAddress) -> None:
    """A structured address raises no structural findings."""
    assert POLICY.assess(structured, CTX) == []


def test_hybrid_ignored(hybrid: CanonicalAddress) -> None:
    """The baseline does not enforce cliff rules on hybrid residual."""
    assert POLICY.assess(hybrid, CTX) == []


def test_unstructured_ignored(unstructured: CanonicalAddress) -> None:
    """The baseline does not reject unstructured addresses."""
    assert POLICY.assess(unstructured, CTX) == []


def test_bad_country_warns(bad_country: CanonicalAddress) -> None:
    """A non-ISO country is a baseline warning, not a rejection."""
    assert _codes(bad_country) == {
        FindingCode.NON_ISO_COUNTRY_CODE: Severity.WARNING
    }


def test_overflow_warns(overflow: CanonicalAddress) -> None:
    """An over-length AdrLine is a baseline warning."""
    assert _codes(overflow) == {FindingCode.ADRLINE_OVERFLOW: Severity.WARNING}
