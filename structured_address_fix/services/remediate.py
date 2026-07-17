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

"""Remediation use-case: turn a non-compliant address into an explained
set of patch operations plus the resulting compliant address.

Remediation is deterministic and offline. Structured fields are derived
from the legacy ``AdrLine`` text by the country-aware heuristics in
:mod:`structured_address_fix.adapters.heuristics`; each derived value
becomes a :class:`PatchOperation` that records the finding it resolves,
the source token it came from, and the heuristic's confidence.
"""

from __future__ import annotations

from datetime import date

from structured_address_fix.adapters.heuristics import split_unstructured
from structured_address_fix.adapters.heuristics.base import HeuristicResult
from structured_address_fix.adapters.iso3166 import is_iso_3166_1_alpha_2
from structured_address_fix.domain.address import (
    MAX_STREET_NAME,
    CanonicalAddress,
)
from structured_address_fix.domain.findings import FindingCode, RiskFinding
from structured_address_fix.domain.remediation import (
    PatchOp,
    PatchOperation,
    RemediationSuggestion,
)
from structured_address_fix.policies.base import AddressPolicy
from structured_address_fix.services.assess import _context

#: Map canonical field name -> ISO 20022 element local name (the segment
#: used to build a patch operation's JSON pointer).
_FIELD_TO_ELEMENT: dict[str, str] = {
    "street_name": "StrtNm",
    "post_code": "PstCd",
    "town_name": "TwnNm",
    "country_sub_division": "CtrySubDvsn",
    "country": "Ctry",
}

#: The finding each derived field resolves.
_FIELD_TO_REASON: dict[str, FindingCode] = {
    "town_name": FindingCode.MISSING_TOWN,
    "country": FindingCode.MISSING_COUNTRY,
    "post_code": FindingCode.UNSTRUCTURED_ONLY,
    "country_sub_division": FindingCode.UNSTRUCTURED_ONLY,
    "street_name": FindingCode.UNSTRUCTURED_ONLY,
}


def _derive(
    address: CanonicalAddress, country_hint: str | None
) -> HeuristicResult | None:
    """Run the country heuristic if a usable country code is available."""
    country = address.country or country_hint
    if country is None or not is_iso_3166_1_alpha_2(country):
        return None
    if not address.address_lines:
        return None
    return split_unstructured(address.address_lines, country)


def _build_after(
    address: CanonicalAddress, derived: HeuristicResult, base: str
) -> tuple[CanonicalAddress, list[PatchOperation]]:
    """Merge heuristic output onto ``address`` and record the operations.

    Remediation drives the address to the fully structured form: derived
    town / post code / subdivision are set, any residual free-form text is
    promoted into ``street_name`` (so no data is lost), and every original
    ``AdrLine`` is removed. Because the XML writer drops the first
    ``AdrLine`` occurrence per ``REMOVE``, one ``REMOVE`` is emitted per
    original line, so the operation list reproduces ``after`` exactly.
    """
    fields = address.model_dump(exclude={"classification"})
    operations: list[PatchOperation] = []
    source = address.address_lines[0] if address.address_lines else None

    for field, element in _FIELD_TO_ELEMENT.items():
        new_value = getattr(derived, field)
        if new_value is not None and fields.get(field) != new_value:
            fields[field] = new_value
            operations.append(
                PatchOperation(
                    op=PatchOp.SET,
                    path=f"{base}/{element}",
                    value=new_value,
                    reason_code=_FIELD_TO_REASON[field],
                    source_token=source,
                    confidence=derived.confidence,
                )
            )

    residual = derived.address_lines
    if residual and fields.get("street_name") is None:
        street = ", ".join(residual)[:MAX_STREET_NAME]
        fields["street_name"] = street
        operations.append(
            PatchOperation(
                op=PatchOp.SET,
                path=f"{base}/StrtNm",
                value=street,
                reason_code=FindingCode.UNSTRUCTURED_ONLY,
                source_token=residual[0],
                confidence=derived.confidence,
            )
        )

    for _ in address.address_lines:
        operations.append(
            PatchOperation(
                op=PatchOp.REMOVE,
                path=f"{base}/AdrLine",
                reason_code=FindingCode.HYBRID_RESIDUAL_ADRLINE,
                confidence=derived.confidence,
            )
        )
    fields["address_lines"] = ()

    after = CanonicalAddress.model_validate(fields)
    return after, operations


def remediate_address(
    address: CanonicalAddress,
    policy: AddressPolicy,
    *,
    country_hint: str | None = None,
    as_of: date | None = None,
    base_pointer: str = "",
) -> RemediationSuggestion:
    """Propose the compliant form of ``address`` under ``policy``.

    ``base_pointer``
    prefixes every operation's path so message-level callers can anchor
    operations at the party's ``PstlAdr`` element; it defaults to ``""``
    for a bare address.
    """
    ctx = _context(as_of, country_hint=country_hint)
    findings_before = policy.assess(address, ctx)
    derived = _derive(address, country_hint)

    if derived is None:
        return RemediationSuggestion(
            before=address,
            after=address,
            operations=(),
            resolved_findings=(),
            residual_findings=tuple(findings_before),
            explanation=_explain(0, tuple(findings_before)),
        )

    after, operations = _build_after(address, derived, base_pointer)
    findings_after = policy.assess(after, ctx)
    residual_codes = {f.code for f in findings_after}
    resolved = tuple(
        f.code for f in findings_before if f.code not in residual_codes
    )
    return RemediationSuggestion(
        before=address,
        after=after,
        operations=tuple(operations),
        resolved_findings=resolved,
        residual_findings=tuple(findings_after),
        explanation=_explain(len(operations), tuple(findings_after)),
    )


def _explain(n_operations: int, residual: tuple[RiskFinding, ...]) -> str:
    """Compose a human-readable explanation of a remediation."""
    if n_operations == 0:
        if residual:
            return (
                "No automatic remediation was possible; "
                f"{len(residual)} finding(s) remain unresolved."
            )
        return "Address already meets the policy; no changes needed."
    base = f"Applied {n_operations} change(s) derived from address lines."
    if residual:
        return f"{base} {len(residual)} finding(s) still require attention."
    return f"{base} The address now meets the policy."
