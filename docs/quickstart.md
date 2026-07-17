# Quick start

This tour takes you from install to a remediated address in a few minutes.

## 1. Install

`structured-address-fix` requires Python 3.12+ and pulls in only `pydantic`,
`defusedxml`, and `xmlschema`.

```sh
python -m pip install structured-address-fix
```

## 2. Classify an address

`CanonicalAddress` is the ISO 20022 `PostalAddress27` type, re-exported from the
package root. It is frozen, rejects extra fields, enforces the per-element
maximum lengths as construction invariants, and classifies itself per CBPR+
UG2026 into one of three shapes:

| Classification | Shape | Cliff status |
| :--- | :--- | :--- |
| `STRUCTURED` | `TwnNm` + `Ctry` + at least one other structured field, **no** `AdrLine` | Target |
| `HYBRID` | `TwnNm` + `Ctry` + 1–2 residual `AdrLine` lines | Minimum bar |
| `UNSTRUCTURED` | anything else (typically `AdrLine`-only) | Rejected from 2026-11-14 |

```python
from structured_address_fix import CanonicalAddress

unstructured = CanonicalAddress(
    address_lines=("221B Baker Street", "London NW1 6XE", "United Kingdom"),
)
assert unstructured.classification.value == "unstructured"

structured = CanonicalAddress(
    building_number="221B",
    street_name="Baker Street",
    post_code="NW1 6XE",
    town_name="London",
    country="GB",
)
assert structured.classification.value == "structured"
```

Field names are snake_case translations of the ISO 20022 element names; each
carries a `serialization_alias` so you can round-trip to the wire:

```python
structured.model_dump(by_alias=True, exclude_none=True)
# {'BldgNb': '221B', 'StrtNm': 'Baker Street', 'PstCd': 'NW1 6XE',
#  'TwnNm': 'London', 'Ctry': 'GB', ...}
```

Construction fails with a Pydantic `ValidationError` if an element exceeds its
ISO 20022 maximum length, if more than seven `address_lines` are supplied, or if
`country` is not a two-letter code.

## 3. Assess a message

The `structured_address_fix.services` facade is the top-level entry point.
`assess` walks every party that carries a `PstlAdr` (debtor, creditor, agents,
ultimate parties), scores each address against a policy, and returns a read-only
[`ValidationReport`](remediation-model.md):

```python
from structured_address_fix.services import assess

report = assess(pacs008_xml, policy="cbpr-2026")
print(report.is_compliant, report.assessed_addresses)
for finding in report.findings:
    print(finding.code, finding.severity, finding.party_role, finding.message)
```

If you omit `policy`, the default is `cbpr-2026` (overridable with the
`SAF_DEFAULT_POLICY` environment variable).

## 4. Remediate

`remediate` adds the proposed fixes. Each
[`RemediationSuggestion`](remediation-model.md) carries the `before` and `after`
address, the reversible `PatchOperation`s that get you there, and any
`residual_findings` no heuristic could resolve:

```python
from structured_address_fix.services import remediate

result = remediate(pacs008_xml, policy="cbpr-2026")
for s in result.suggestions:
    print(s.before.classification, "->", s.after.classification)
    for op in s.operations:
        print(f"  {op.op} {op.path}  ({op.reason_code}, conf={op.confidence})")
    for residual in s.residual_findings:
        print(f"  residual: {residual.code} {residual.message}")

print(result.is_compliant_before, "->", result.is_compliant_after)
```

Remediation is best-effort and explainable: a low-confidence or unresolvable
`AdrLine` fragment is reported as a residual finding for a human to resolve,
never silently guessed. Review the suggestion before applying it to a live
payment.

## 5. Next steps

- [Policies](policies.md) — pick the right rulebook for your scheme.
- [The remediation model](remediation-model.md) — the full shape of findings,
  patches, and results.
- [The November 2026 cutover](nov-2026-cutover.md) — the deadline in context.

> The `assess` / `remediate` facade, the built-in policy rulebooks, and the
> XML adapters land in the v0.1.x series (see [`../ROADMAP.md`](../ROADMAP.md)).
> The `CanonicalAddress` classification shown above works today.
