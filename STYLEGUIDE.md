<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `structured-address-fix` style guide

`structured-address-fix` follows the cross-suite conventions of the
sebastienrousseau ISO 20022 suite. Those conventions are the single source of
truth for:

- Voice + spelling conventions (British prose, American code, no em-dashes,
  no emojis outside the standard checkmark/cross in supported-versions
  tables).
- README structure + badge order.
- CHANGELOG structure (Keep-a-Changelog + Quality gates + Suite alignment).
- SECURITY.md structure (including the NIST SSDF practice mapping and the
  accepted-Scorecard-findings section).
- SUPPORT.md / CONTRIBUTING.md structure.
- CI floor (test + lint + type-check + security + docstring-coverage gates,
  plus release-only provenance/SBOM gates).
- PR style (conventional commits + signed commits + branch policy).
- Branch naming, issue filing, naming conventions.

## Local additions

`structured-address-fix` adds a few core-library conventions:

- **Stable vocabularies.** `FindingCode`, `PolicyId`, and every wire-facing
  enum value is a public API. Once a value ships, its meaning is fixed; a
  changed rule earns a **new** code rather than repurposing an existing one.

  ```
  SAF001  UNSTRUCTURED_ONLY       # never re-point this at a different rule
  cbpr-2026                       # a policy id, stable across releases
  ```

- **ISO 20022 field names.** Domain field names are snake_case translations of
  the ISO 20022 XML element names (`StrtNm` → `street_name`), and each field's
  `serialization_alias` carries the original element name so
  `model_dump(by_alias=True)` speaks ISO 20022 back out.

- **Explainable remediation.** Every `PatchOperation` records *why* it exists
  (the finding it resolves), *where its value came from* (the source
  `AdrLine` token, when applicable), and *how confident* the heuristic was.
  Remediation must never be a black box.

## Updating

If you find divergence between this repo's practice and the suite conventions,
the suite wins; open a PR to align this repo (and/or fix the deviation).
