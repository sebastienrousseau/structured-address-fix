# structured-address-fix documentation

`structured-address-fix` is the core ISO 20022 postal-address remediation
library: it detects, scores, and remediates non-compliant postal addresses in
payment messages (`pacs.008`, `pain.001`, and siblings) ahead of the
**14 November 2026** cliff, when fully unstructured addresses are rejected
across SWIFT CBPR+, HVPS+, T2 RTGS, CHAPS, Fedwire, and Lynx.

## Start here

- [Quick start](quickstart.md) — install, classify an address, assess and
  remediate a message.
- [The November 2026 cutover](nov-2026-cutover.md) — what changes, per scheme,
  and why structured beats hybrid beats unstructured.

## Reference

- [Policies](policies.md) — the four built-in rulebooks (`cbpr-2026`, `sepa`,
  `hvps-plus`, `generic-structured`) and the finding codes they raise.
- [The remediation model](remediation-model.md) — how findings, patch
  operations, suggestions, and result envelopes fit together.
- [Error taxonomy](error-taxonomy.md) — the `StructuredAddressError` hierarchy
  and every stable error `code`.

## Extending

- [Writing a rule pack](writing-a-rule-pack.md) — publish a premium `PolicyPack`
  discovered through the `structured_address_fix.policies` entry point.

## Layers

| Layer | Module | Responsibility |
| :--- | :--- | :--- |
| Domain | `structured_address_fix.domain` | Pure Pydantic entities and invariants |
| Policies | `structured_address_fix.policies` | Rulebooks that raise findings |
| Adapters | `structured_address_fix.adapters` | `defusedxml` parsing + `AdrLine` heuristics |
| Services | `structured_address_fix.services` | The `assess` / `remediate` facade |
| Plugins | `structured_address_fix.plugins` | The premium rule-pack SDK |

The domain layer and error taxonomy shipped in v0.0.1. The policies, adapters,
and services facade land in the v0.0.x series; see
[`../ROADMAP.md`](../ROADMAP.md).
