# Security Policy

The structured-address-fix maintainers take the security of this project
seriously. This document explains which versions receive security updates and
how to report a vulnerability responsibly.

structured-address-fix is the core ISO 20022 postal-address remediation
library: it detects, scores, and remediates non-compliant postal addresses in
payment messages (pacs.008, pain.001, and siblings) ahead of the 14 November
2026 cliff, and it is the shared engine that the thin
[`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp)
server wraps.

## Supported Versions

Security fixes are applied to the latest released minor version. While the
project is in its `0.x` series, only the most recent release line receives
security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |
| < 0.0.1 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

We support coordinated disclosure. To report a vulnerability, use either of the
following private channels:

- **GitHub Security Advisories** (preferred): open a private report via the
  repository's
  [Security tab → "Report a vulnerability"](https://github.com/sebastienrousseau/structured-address-fix/security/advisories/new).
- **Email**: contact the maintainer at
  [sebastian.rousseau@gmail.com](mailto:sebastian.rousseau@gmail.com).

When reporting, please include as much of the following as possible:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a proof-of-concept.
- The affected version(s) and environment (Python version, OS).
- Any known mitigations or workarounds.

## Response Timeline

We aim to meet the following targets, on a best-effort basis:

| Stage                     | Target                          |
| ------------------------- | ------------------------------- |
| Acknowledge receipt       | Within 3 business days          |
| Initial assessment        | Within 7 business days          |
| Fix or mitigation plan    | Within 30 days of confirmation  |
| Public disclosure         | Coordinated, after a fix ships  |

We will keep you informed of progress throughout the process and will credit
reporters in the advisory unless anonymity is requested.

## Scope

The following are in scope:

- The `structured_address_fix` library as published in this repository,
  including the domain models, policy rulebooks, XML adapters, and the
  services facade.
- XML parsing paths reached through the adapters, including XXE / billion-laughs
  / DOCTYPE handling. Untrusted ISO 20022 documents are parsed with
  `defusedxml`, never the standard-library XML parser.
- Handling of caller-supplied addresses and messages, and the payloads
  returned to callers (validation reports, remediation results, error
  envelopes).
- Input validation for ISO 20022 element lengths, country codes, and the
  address-classification logic.
- The premium rule-pack plugin loader: entry-point discovery and the
  entitlement / integrity checks that gate third-party packs.

The following are generally out of scope:

- Vulnerabilities in third-party dependencies (please report those upstream;
  we will track and update affected dependencies via Dependabot).
- Issues requiring a compromised host, malicious local configuration, or
  physical access.
- Denial of service caused by intentionally malformed, multi-gigabyte inputs
  beyond documented usage.
- The correctness of a *remediation suggestion* as a business decision: the
  library proposes explainable, reversible patches and always reports residual
  findings, but the caller remains responsible for approving a change before it
  is applied to a live payment.

Thank you for helping keep structured-address-fix and its users safe.

## NIST SSDF practice mapping

This repository follows the practices of the **NIST Secure Software
Development Framework (SP 800-218 Rev 1.1)**. The table below maps
each SSDF practice that applies to an open-source Python library to
the concrete control(s) that implement it in this repo.

| SSDF practice | How this repo addresses it |
| :--- | :--- |
| **PO.1** Define security requirements | This `SECURITY.md`, plus the in-scope/out-of-scope sections above. |
| **PO.3** Implement supporting toolchains | `pyproject.toml`; `.github/workflows/ci.yml` (test + lint + security scan); `.github/workflows/scorecard.yml`. |
| **PO.4** Define and use criteria for software security checks | CI enforces tests on Python 3.12/3.13 with a 100% line + branch coverage gate, ruff lint, black formatting, mypy --strict, bandit security scan, and interrogate docstring coverage; Scorecard runs weekly. |
| **PO.5** Implement and maintain secure environments | PyPI Trusted Publishing (OIDC, no long-lived tokens); branch protection + signed commits on `main`; per-workflow `permissions:` minimisation. |
| **PS.1** Protect all forms of code from unauthorized access and tampering | Signed commits (SSH ed25519); branch protection; required PR reviews; `persist-credentials: false` on Scorecard checkout. |
| **PS.2** Provide a mechanism for verifying software release integrity | Signed git tags; `actions/attest-build-provenance` SLSA L3 provenance attestations; PEP 740 sigstore attestations on PyPI uploads (`pypa/gh-action-pypi-publish` with `attestations: true`). |
| **PS.3** Archive and protect each software release | GitHub Releases pin the exact `dist/*` artifacts; CycloneDX 1.6 + SPDX 2.3 SBOMs and a pip-licenses manifest attached to every release; PyPI is the immutable archive. |
| **PW.1** Design software to mitigate security risks | Untrusted XML is parsed via `defusedxml` (no XXE / billion-laughs); the services facade raises a typed `StructuredAddressError` taxonomy with safe `context`, so hosts can serialise `{"error": ...}` payloads rather than leaking tracebacks. |
| **PW.4** Reuse well-secured software when feasible | Dependencies pinned via pyproject; Dependabot grouped weekly + separate security-update group; updates reviewed before merge. |
| **PW.5** Adhere to secure coding practices | `ruff`, `bandit -ll`, strict `mypy`, code review on every PR. |
| **PW.6** Configure build processes to improve security | Reproducible builds via `poetry build` with locked dependencies; CI uses SHA-pinned action versions and hash-pinned `pip` installs; minimum-required GH Actions permissions. |
| **PW.7** Review and analyze human-readable code | All changes go through PRs with required review; CodeQL static analysis runs on push/PR; ruff + mypy + bandit on every change. |
| **PW.8** Test executable code | pytest across Python 3.12 + 3.13 at 100% line + branch coverage, plus Hypothesis property tests over the classification and remediation logic. |
| **PW.9** Configure software with secure defaults | The XML adapters default to `defusedxml`; premium packs are opt-in and gated by entitlement + integrity checks; the canonical model is frozen and `extra="forbid"`. |
| **RV.1** Identify and confirm vulnerabilities on an ongoing basis | Dependabot; `bandit` in CI; OpenSSF Scorecard weekly; GitHub Security Advisories accept reports. |
| **RV.2** Assess, prioritise, and remediate vulnerabilities | Coordinated-disclosure timeline above (3-day ack / 7-day assessment / 30-day fix); CHANGELOG + advisory at fix publication. |
| **RV.3** Analyze root causes | Each security advisory captures root cause + remediation in the GitHub Security Advisory body; lessons feed back into added regression tests. |

Cross-suite practices (organisation roles, multi-package release governance) are
owned by the upstream sebastienrousseau ISO 20022 suite governance.

## Accepted OpenSSF Scorecard findings

The suite runs [OpenSSF Scorecard](https://securityscorecards.dev/) weekly and
treats its results as advisory. The checks below are **accepted risks**: they
cannot be resolved by code or configuration for a single-maintainer
open-source project, and are recorded here so their status is explicit.

- **Branch-Protection** — `main` is protected: pull requests are required,
  with a required status check (`Lint & Type Check`), dismissal of stale
  reviews, linear history, and no force-pushes or deletions. Scorecard's
  highest tier also wants `enforce_admins` enabled; we deliberately leave it
  **off** so the sole maintainer can still merge approved release/security
  PRs without a second account (see [`MAINTAINERS.md`](MAINTAINERS.md)). This
  is an accepted trade-off.
- **Code-Review** — Scorecard expects each change to be approved by a
  *second* reviewer. With a single maintainer this is structurally
  impossible; changes still go through pull requests with CI gating.
  Accepted until a second maintainer joins.
- **Maintained** — a heuristic over recent commit/issue cadence that can lag
  immediately after a release lull. The project is actively maintained (see
  the commit history and the lockstep release process).
- **Fuzzing** — no continuous fuzzing harness ships in v0.1. The parsing
  surface is small and defusedxml-backed, and inputs are exercised by the
  property-based test suite; a ClusterFuzzLite target may be added in a
  later release. Accepted for now.
- **CII-Best-Practices** — the project is not yet registered for an OpenSSF
  Best Practices badge (a manual enrolment). Accepted until enrolled.

All **code-fixable** Scorecard checks are satisfied: Pinned-Dependencies
(SHA-pinned GitHub Actions + hash-pinned `pip` installs), Token-Permissions
(least-privilege workflow tokens), and SAST (CodeQL on push/PR).
