# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-07-17

### Changed

- Lockstep release with `structured-address-fix-mcp` 0.0.2. No functional
  changes to the core since 0.0.1.

## [0.0.1] - 2026-07-17

The **initial release**: the core domain model, error taxonomy, and
configuration for ISO 20022 postal-address remediation ahead of the
14 November 2026 CBPR+ / HVPS+ / T2 / CHAPS / Fedwire cliff. This is the
shared engine that `pacs008` and a thin
[`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp)
server will build on.

### Added

- **Domain layer** (`structured_address_fix.domain`), pure Pydantic v2
  entities with zero I/O:
  - `CanonicalAddress` — the ISO 20022 `PostalAddress27` complex type,
    canonicalized and self-classifying. Field names are snake_case
    translations of the XML element names with `serialization_alias`es that
    speak ISO 20022 back out via `model_dump(by_alias=True)`; per-field maximum
    lengths are enforced as validation invariants; the model is `frozen` and
    `extra="forbid"`. A `classification` computed field returns
    `STRUCTURED` / `HYBRID` / `UNSTRUCTURED` per CBPR+ UG2026.
  - `AddressedParty` — binds a `CanonicalAddress` to its `PartyRole` and a
    JSON pointer locating its `PstlAdr` element.
  - `RiskFinding` + `FindingCode` (SAF001–SAF008) — the stable, wire-facing
    catalogue of compliance risks a policy can raise.
  - `PatchOperation` + `PatchOp` + `RemediationSuggestion` — RFC 6902-shaped,
    reversible edits that record the finding they resolve, the source
    `AdrLine` token, and the deriving heuristic's confidence, so remediation
    is fully explainable.
  - `ValidationReport` + `RemediationResult` — the read-only assessment and
    remediation envelopes.
  - Wire-facing enums: `AddressClassification`, `Severity`, `PartyRole`,
    `MessageType`, `PolicyId`.
- **Error taxonomy** (`structured_address_fix.errors`) — the
  `StructuredAddressError` base plus input, policy, remediation, and
  premium-pack-entitlement subclasses, each carrying a stable `code` and safe
  `context`.
- **Configuration** (`structured_address_fix.config`) — the load-bearing
  `NOV_2026_CLIFF` date constant and the environment-overridable
  `default_policy_id()`.
- **Supply chain** — 100% line + branch coverage gate, mypy `--strict`,
  ruff + black, bandit, interrogate 100% docstring coverage, OpenSSF
  Scorecard, CodeQL, and a release pipeline with SLSA build provenance +
  PEP 740 sigstore attestations and CycloneDX + SPDX + pip-licenses SBOMs.

### Notes

- The built-in policy rulebooks, XML adapters, per-country heuristics, and the
  `assess` / `remediate` services facade are on the v0.0.x roadmap; see
  [`ROADMAP.md`](ROADMAP.md).

[0.0.2]: https://github.com/sebastienrousseau/structured-address-fix/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/structured-address-fix/releases/tag/v0.0.1
