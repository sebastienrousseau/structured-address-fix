<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `structured-address-fix` roadmap

## Mission

The shared ISO 20022 postal-address remediation engine for the
sebastienrousseau ISO 20022 suite — detect, score, and remediate
non-compliant postal addresses in payment messages ahead of the
**14 November 2026** CBPR+ / HVPS+ / T2 / CHAPS / Fedwire cliff, with a
domain model that supersedes and generalises `pacs008.standards.address`.

## Where we are (v0.0.2, 2026-07-17)

- **Domain layer** — Pydantic v2 entities: `CanonicalAddress`
  (ISO 20022 `PostalAddress27`, self-classifying into structured / hybrid /
  unstructured per CBPR+ UG2026), `AddressedParty`, `RiskFinding` +
  `FindingCode` (SAF001–SAF008), the RFC 6902-shaped `PatchOperation` /
  `RemediationSuggestion`, and the `ValidationReport` / `RemediationResult`
  envelopes.
- **Error taxonomy** — the `StructuredAddressError` hierarchy with stable
  `code`s and safe `context`, so a wrapping transport can serialise
  `{"error": ...}` payloads rather than leaking tracebacks.
- **Configuration** — the load-bearing `NOV_2026_CLIFF` constant and the
  overridable default policy id.

## v0.0.x — built-in policies, adapters, and the services facade

Goal: a complete, self-contained core that assesses and remediates a message
end to end.

- **Built-in policy rulebooks**: `cbpr-2026`, `sepa`, `hvps-plus`, and
  `generic-structured`, each raising the shared finding codes with rulebook
  clause citations.
- **XML adapters**: `defusedxml` parsing of pacs.008 / pain.001, party
  discovery, and per-country `AdrLine` → structured heuristics that populate
  the canonical model with recorded confidence and source tokens.
- **Services facade**: `assess(...)` → `ValidationReport` and
  `remediate(...)` → `RemediationResult`, the single public entry point the
  transport wrappers call.

## Downstream: `pacs008` migration

Goal: retire the bespoke `pacs008.standards.address` in favour of this core.

- `pacs008` takes a dependency on `structured-address-fix` and delegates its
  address linting and Nov-2026 readiness checks here, so the two stop drifting.
- A thin
  [`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp)
  server wraps the services facade for AI agents.

## Later: premium rule packs + REST / LSP reuse

Goal: extensibility and interface breadth without bloating the core.

- **Premium rule-pack SDK**: third-party `PolicyPack`s discovered via
  `structured_address_fix.policies` entry points, gated by the entitlement +
  integrity checks in the error taxonomy (`PackNotLicensedError`,
  `PackIntegrityError`).
- **Interface reuse**: the same facade behind a REST API and an LSP server, so
  every surface behaves identically — matching the pattern used elsewhere in
  the suite.

## v1.0.0 — stable core

Goal: first stable minor.

- **Domain + finding + policy vocabularies frozen**: any future value change
  becomes a SemVer event.
- **OpenSSF Best Practices** badge live.

## How to influence the roadmap

- Open an issue with the proposed rule / policy / heuristic + the scheme
  document or rulebook clause that motivates it.
- For larger items, sketch a design in the issue body.
- See [`GOVERNANCE.md`](GOVERNANCE.md) for the decision-making process.
