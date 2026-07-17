<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `structured-address-fix` governance

This document describes how `structured-address-fix` is run, how decisions are
made, and how to take on responsibility for it. `structured-address-fix` is part
of the sebastienrousseau ISO 20022 suite; the suite-wide governance is shared
across the sibling repositories. This document covers the core-library-specific
bits.

## Mission and scope

`structured-address-fix` is the shared ISO 20022 postal-address remediation
engine: it detects, scores, and remediates non-compliant addresses in payment
messages ahead of the 14 November 2026 cliff, and it is the core wrapped by the
thin
[`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp)
server. Changes are weighed against a single criterion: **correctness,
security, and clarity over feature breadth**.

A change is in-scope if it improves the domain model, a built-in policy
rulebook, an XML adapter, an AdrLine → structured heuristic, or the services
facade; or if it sharpens the plugin contract for premium rule packs. A change
is out-of-scope if it belongs in a transport wrapper (MCP / REST / LSP server),
or if it ships a rule pack that should live behind the entry-point plugin
boundary rather than in the open-source core.

## Roles + decision making

| Role | Who | Can |
| :--- | :--- | :--- |
| **Maintainer** | Listed in [`MAINTAINERS.md`](MAINTAINERS.md) | Merge PRs, cut releases, triage, set direction |
| **Contributor** | Anyone with a merged PR | Propose changes, review, discuss |
| **User** | Everyone | File issues, ask questions, request features |

- Day-to-day changes land via PR with maintainer approval (conventional
  commits + signed commits + branch policy from the suite STYLEGUIDE).
- Larger changes (a new built-in policy, a new finding code, a change to the
  plugin contract, dependency additions) require a tracking GitHub Issue +
  72-hour comment window + maintainer agreement.
- Releases are cut against a milestone; signed tag + OIDC publish to PyPI with
  PEP 740 attestations.
- Security disclosures: 3-day ack / 7-day assessment / 30-day fix per
  [`SECURITY.md`](SECURITY.md).

## Stability guarantees

`FindingCode`, `PolicyId`, `AddressClassification`, and the wire-facing enum
values are a **public API**. Their string values appear in serialized findings,
patches, and downstream tool payloads, so a value's meaning is never repurposed
once shipped: a changed rule earns a new code. This is enforced socially in
review and, from v1.0, by SemVer.

## Cross-suite consistency

All packages in the suite share the same CI floor, release pipeline, and
governance documents. Cross-suite policy changes land in the core suite
governance first, then mirror to the sibling packages.

## Becoming a maintainer

See the path in [`MAINTAINERS.md`](MAINTAINERS.md).

## Updating this document

PR with the 72-hour comment window for anything material. The lead
maintainer has final say but engages with substantive feedback before
merging.
