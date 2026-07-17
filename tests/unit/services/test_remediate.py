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

"""Branch-exhaustive tests for the remediation use-case."""

from __future__ import annotations

from datetime import date

from structured_address_fix.adapters.heuristics.base import HeuristicResult
from structured_address_fix.domain import (
    AddressClassification,
    CanonicalAddress,
)
from structured_address_fix.domain.findings import FindingCode, RiskFinding
from structured_address_fix.domain.remediation import PatchOp
from structured_address_fix.policies.registry import default_registry
from structured_address_fix.services.assess import _context
from structured_address_fix.services.remediate import (
    _build_after,
    _derive,
    _explain,
    remediate_address,
)

_CBPR = default_registry.get("cbpr-2026")
_AS_OF = date(2026, 12, 1)


def _reject_finding() -> RiskFinding:
    """A minimal rejecting finding for exercising ``_explain``."""
    return RiskFinding(
        code=FindingCode.UNSTRUCTURED_ONLY,
        severity="critical",
        message="rejected",
        policy_id="cbpr-2026",
        rejects_payment=True,
    )


# -- _derive branches -------------------------------------------------------


def test_derive_none_when_country_and_hint_absent(
    no_country_unstructured: CanonicalAddress,
) -> None:
    """No country and no hint -> the heuristic is not run."""
    assert _derive(no_country_unstructured, None) is None


def test_derive_none_when_country_invalid(
    bad_country_address: CanonicalAddress,
) -> None:
    """A present-but-invalid country code -> the heuristic is not run."""
    assert _derive(bad_country_address, None) is None


def test_derive_none_when_no_address_lines() -> None:
    """A usable country but no AdrLine text -> nothing to derive from."""
    address = CanonicalAddress(country="GB")
    assert _derive(address, None) is None


def test_derive_runs_with_valid_country_and_lines(
    gb_unstructured: CanonicalAddress,
) -> None:
    """A valid country plus AdrLine text runs the country heuristic."""
    result = _derive(gb_unstructured, None)

    assert result is not None
    assert result.country == "GB"
    assert result.town_name == "London"


def test_derive_uses_country_hint_when_country_none(
    no_country_unstructured: CanonicalAddress,
) -> None:
    """When the address has no country, the hint drives the heuristic."""
    result = _derive(no_country_unstructured, "US")

    assert result is not None
    assert result.country == "US"


# -- remediate_address: derived paths ---------------------------------------


def test_remediate_unstructured_gb_emits_confident_ops(
    gb_unstructured: CanonicalAddress,
) -> None:
    """A GB unstructured address yields anchored, high-confidence ops."""
    suggestion = remediate_address(gb_unstructured, _CBPR, as_of=_AS_OF)

    ops = suggestion.operations
    # Remediation drives to the fully structured form: derived fields are
    # set, residual free-form text is promoted to StrtNm, and every
    # original AdrLine is removed.
    assert {op.path for op in ops} == {
        "/PstCd",
        "/TwnNm",
        "/StrtNm",
        "/AdrLine",
    }
    assert all(op.confidence == 0.9 for op in ops)
    set_ops = [op for op in ops if op.op is PatchOp.SET]
    remove_ops = [op for op in ops if op.op is PatchOp.REMOVE]
    assert all(op.source_token == "Flat 2" for op in set_ops)
    assert len(remove_ops) == 3  # one per original AdrLine
    town = next(op for op in set_ops if op.path == "/TwnNm")
    assert town.value == "London"
    assert town.reason_code is FindingCode.MISSING_TOWN
    assert FindingCode.MISSING_TOWN in suggestion.resolved_findings
    # The address is now fully structured -> no residual findings.
    assert suggestion.residual_findings == ()
    assert suggestion.after.classification is AddressClassification.STRUCTURED
    assert "now meets the policy" in suggestion.explanation


def test_remediate_no_op_for_field_already_present(
    gb_unstructured: CanonicalAddress,
) -> None:
    """A derived value equal to the existing one emits no operation.

    ``gb_unstructured`` already carries ``country="GB"``, which the GB
    heuristic re-derives identically, so no ``/Ctry`` operation is emitted
    (the field-already-present no-op branch).
    """
    suggestion = remediate_address(gb_unstructured, _CBPR, as_of=_AS_OF)

    paths = {op.path for op in suggestion.operations}
    assert "/Ctry" not in paths


def test_remediate_fully_consumed_lines_emits_remove() -> None:
    """When the heuristic consumes every line, an AdrLine REMOVE is issued."""
    address = CanonicalAddress(
        country="GB", address_lines=("London SW1A 1AA",)
    )

    suggestion = remediate_address(address, _CBPR, as_of=_AS_OF)

    remove_ops = [
        op for op in suggestion.operations if op.op is PatchOp.REMOVE
    ]
    assert len(remove_ops) == 1
    assert remove_ops[0].path == "/AdrLine"
    assert remove_ops[0].reason_code is FindingCode.HYBRID_RESIDUAL_ADRLINE
    assert suggestion.after.address_lines == ()
    assert suggestion.residual_findings == ()
    assert "now meets the policy" in suggestion.explanation


def test_remediate_uses_country_hint_when_country_absent(
    no_country_unstructured: CanonicalAddress,
) -> None:
    """A supplied hint lets remediation add the missing country."""
    suggestion = remediate_address(
        no_country_unstructured,
        _CBPR,
        country_hint="US",
        as_of=_AS_OF,
    )

    ctry = next(op for op in suggestion.operations if op.path == "/Ctry")
    assert ctry.value == "US"
    assert ctry.reason_code is FindingCode.MISSING_COUNTRY
    assert suggestion.after.country == "US"


def test_remediate_base_pointer_prefixes_paths(
    gb_unstructured: CanonicalAddress,
) -> None:
    """``base_pointer`` anchors every operation path at the party element."""
    suggestion = remediate_address(
        gb_unstructured,
        _CBPR,
        as_of=_AS_OF,
        base_pointer="/Document/Cdtr/PstlAdr",
    )

    assert all(
        op.path.startswith("/Document/Cdtr/PstlAdr/")
        for op in suggestion.operations
    )


# -- remediate_address: no-derive paths -------------------------------------


def test_remediate_unresolvable_when_no_country(
    no_country_unstructured: CanonicalAddress,
) -> None:
    """No country and no hint -> before==after, findings unresolved."""
    suggestion = remediate_address(
        no_country_unstructured, _CBPR, as_of=_AS_OF
    )

    assert suggestion.after == suggestion.before
    assert suggestion.operations == ()
    assert suggestion.resolved_findings == ()
    assert suggestion.residual_findings  # findings carried through
    assert "No automatic remediation" in suggestion.explanation


def test_remediate_invalid_country_is_unresolvable(
    bad_country_address: CanonicalAddress,
) -> None:
    """An invalid ISO country cannot be remediated automatically."""
    suggestion = remediate_address(bad_country_address, _CBPR, as_of=_AS_OF)

    assert suggestion.operations == ()
    assert suggestion.after == suggestion.before


def test_remediate_compliant_address_is_noop(
    gb_structured: CanonicalAddress,
) -> None:
    """A compliant structured address needs no changes."""
    suggestion = remediate_address(gb_structured, _CBPR, as_of=_AS_OF)

    assert suggestion.operations == ()
    assert suggestion.after == suggestion.before
    assert suggestion.residual_findings == ()
    assert (
        suggestion.explanation
        == "Address already meets the policy; no changes needed."
    )


# -- _build_after ------------------------------------------------------------


def test_build_after_stamps_source_token(
    gb_unstructured: CanonicalAddress,
) -> None:
    """Every derived op records the first address line as its source.

    ``_build_after`` is only ever reached with a non-empty ``address_lines``
    (``_derive`` returns ``None`` otherwise), so ``source`` is always the
    first line; the ``else None`` arm of that expression is unreachable
    through the public path and is not asserted here.
    """
    derived = _derive(gb_unstructured, None)
    assert derived is not None

    after, operations = _build_after(gb_unstructured, derived, "")

    assert operations
    # SET operations carry the source token; REMOVE operations do not.
    assert all(
        op.source_token == "Flat 2"
        for op in operations
        if op.op is PatchOp.SET
    )
    assert after.town_name == "London"


def test_build_after_clears_all_lines_and_promotes_residual() -> None:
    """``_build_after`` always empties AdrLine and promotes residual text.

    Residual free-form lines the heuristic could not classify are joined
    into ``street_name`` (no data is lost), and one REMOVE is emitted per
    original AdrLine so the operations reproduce ``after`` exactly.
    """
    address = CanonicalAddress(
        country="GB", address_lines=("Keep me", "Also me")
    )
    derived = HeuristicResult(
        country="GB",
        town_name="London",
        address_lines=("Keep me", "Also me"),
    )

    after, operations = _build_after(address, derived, "")

    assert after.address_lines == ()
    assert after.street_name == "Keep me, Also me"
    remove_ops = [op for op in operations if op.op is PatchOp.REMOVE]
    assert len(remove_ops) == 2  # one per original line
    assert after.town_name == "London"


# -- _explain: all four branches --------------------------------------------


def test_explain_no_ops_already_compliant() -> None:
    """Zero ops and no residual -> the 'already meets' message."""
    assert (
        _explain(0, ())
        == "Address already meets the policy; no changes needed."
    )


def test_explain_no_ops_with_residual() -> None:
    """Zero ops but residual findings -> the 'no remediation' message."""
    text = _explain(0, (_reject_finding(),))

    assert text.startswith("No automatic remediation was possible")
    assert "1 finding(s) remain unresolved" in text


def test_explain_ops_fully_resolved() -> None:
    """Some ops and no residual -> the 'now meets the policy' message."""
    text = _explain(2, ())

    assert text.endswith("The address now meets the policy.")
    assert "Applied 2 change(s)" in text


def test_explain_ops_with_residual() -> None:
    """Some ops but residual findings -> the 'still require attention' text."""
    text = _explain(3, (_reject_finding(),))

    assert "Applied 3 change(s)" in text
    assert "1 finding(s) still require attention" in text


def test_context_reused_by_remediate(
    gb_unstructured: CanonicalAddress,
) -> None:
    """Assessment inside remediation shares the assess-layer context."""
    ctx = _context(_AS_OF, country_hint="GB")
    before = _CBPR.assess(gb_unstructured, ctx)

    suggestion = remediate_address(
        gb_unstructured, _CBPR, country_hint="GB", as_of=_AS_OF
    )

    # Resolved + residual codes partition the before-findings' codes.
    before_codes = {f.code for f in before}
    residual_codes = {f.code for f in suggestion.residual_findings}
    assert set(suggestion.resolved_findings) <= before_codes
    assert residual_codes <= (
        before_codes | {FindingCode.HYBRID_RESIDUAL_ADRLINE}
    )
