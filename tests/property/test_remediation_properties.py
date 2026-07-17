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

"""Property-based invariants for remediation.

The strategies are deliberately small and the deadline generous so the
suite stays inside the default (non-``perf``, non-``stress``) coverage gate
without flaking on slower CI hardware.
"""

from __future__ import annotations

from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from structured_address_fix.domain import CanonicalAddress
from structured_address_fix.domain.enums import Severity
from structured_address_fix.policies.registry import default_registry
from structured_address_fix.services.assess import _context
from structured_address_fix.services.remediate import remediate_address

_CBPR = default_registry.get("cbpr-2026")
_AS_OF = date(2026, 12, 1)

_SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.WARNING: 1,
    Severity.ERROR: 2,
    Severity.CRITICAL: 3,
}

# A small pool of tokens that yield a mix of anchored and fallback splits.
_TOKENS = st.sampled_from(
    [
        "Flat 2",
        "221B Baker Street",
        "London SW1A 1AA",
        "Manchester M1 1AE",
        "Somewhere",
        "1 Infinite Loop",
        "Cupertino CA 95014",
    ]
)

_COUNTRY = st.sampled_from(["GB", "US", "FR", "DE"])

_LINES = st.lists(_TOKENS, min_size=1, max_size=3)

_SETTINGS = settings(max_examples=40, deadline=None)


def _worst_rejecting_rank(findings: object) -> int:
    """Return the highest severity rank among rejecting findings, or -1."""
    ranks = [
        _SEVERITY_RANK[f.severity]
        for f in findings  # type: ignore[attr-defined]
        if f.rejects_payment
    ]
    return max(ranks, default=-1)


@given(lines=_LINES, country=_COUNTRY)
@_SETTINGS
def test_remediation_converges_to_a_fixpoint(
    lines: list[str], country: str
) -> None:
    """Repeated remediation reaches a stable fixpoint that emits no ops.

    Remediation is convergent rather than single-step idempotent: a second
    pass may still clear a residual line the first pass promoted a town
    from. Iterating therefore reaches a fixpoint after which remediating
    again yields no operations and leaves the address unchanged.
    """
    address = CanonicalAddress(country=country, address_lines=tuple(lines))

    for _ in range(6):
        step = remediate_address(address, _CBPR, as_of=_AS_OF)
        if step.after == address:
            break
        address = step.after

    final = remediate_address(address, _CBPR, as_of=_AS_OF)
    assert final.after == address
    assert final.operations == ()


@given(
    town=st.sampled_from(["London", "Paris", "Berlin"]),
    country=_COUNTRY,
    street=st.sampled_from(["High Street", "Rue de Rivoli"]),
)
@_SETTINGS
def test_structured_address_is_a_noop(
    town: str, country: str, street: str
) -> None:
    """A fully structured address is never modified by remediation."""
    address = CanonicalAddress(
        town_name=town, country=country, street_name=street
    )

    suggestion = remediate_address(address, _CBPR, as_of=_AS_OF)

    assert suggestion.operations == ()
    assert suggestion.after == address


@given(lines=_LINES, country=_COUNTRY)
@_SETTINGS
def test_remediation_never_worsens_rejection_severity(
    lines: list[str], country: str
) -> None:
    """Remediation never introduces a worse rejecting finding than before."""
    address = CanonicalAddress(country=country, address_lines=tuple(lines))
    ctx = _context(_AS_OF, country_hint=country)
    findings_before = _CBPR.assess(address, ctx)

    suggestion = remediate_address(address, _CBPR, as_of=_AS_OF)

    before_rank = _worst_rejecting_rank(findings_before)
    after_rank = _worst_rejecting_rank(suggestion.residual_findings)
    assert after_rank <= before_rank
