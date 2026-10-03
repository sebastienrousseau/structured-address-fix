<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

Invariants for AI-assisted contributions to `structured-address-fix`. Read this before changing anything.

Everything here applies equally to humans and automated agents. It is addressed to agents because agents can make breaking changes across multiple files before anyone notices.

## 1. Core Invariants

1. **Strict SemVer sequencing policy**: Public releases stay on the `0.0.x` line and increment strictly by `0.0.1`. Never manually edit version numbers outside the active release branch `feat/v<next-version>`. `v0.1.0` is forbidden until `v0.0.999` exists.
2. **Coordinated Multi-Repo Ecosystem Invariant**: `structured-address-fix` and `structured-address-fix-mcp` ship as a synchronized pair. They share identical version numbers and must be released lockstep together.
3. **Single Active Release PR Invariant**: Across all repositories, there MUST be at most ONE active pull request targeting `main`, which MUST be the release iteration branch `feat/v<next-version>`.
4. **Dual licensing**: The repository is dual-licensed under Apache-2.0 OR MIT. All files must declare an SPDX license header.
5. **Single source of truth**: The version in `pyproject.toml` is the single source of truth. It must agree with `__version__`, `server.json`, `glama.json` (on the mcp pair), and `CHANGELOG.md` (verified by `scripts/verify_versions.py`).
6. **Deterministic ISO 20022 postal address remediation**: Address classification, policy assessment, and remediation must remain side-effect-free, deterministic, and idempotent.

## 2. Before You Claim To Be Done (Verification Gates)

Before concluding any task or preparing a commit, run:

```console
make check
```

Or run the individual gates:

```console
poetry run pytest
poetry run ruff check structured_address_fix/ tests/
poetry run black --check structured_address_fix/ tests/
poetry run mypy structured_address_fix/
python3 scripts/verify_versions.py
```

All unit tests and conformance tests must pass with 0 failures, 0 warnings, and 100% line and branch coverage.

## 3. Hygiene First

Before any feature, fix, or release work, check repository health:
1. Verify CI is green on `main`.
2. Ensure linter and formatter pass without warnings or new suppressions.
3. Every function must remain within the complexity ceilings (Cyclomatic ≤ 10, Cognitive ≤ 15, Halstead ≤ 30, Lines of code ≤ 60 per function, ≤ 500 per file).

## 4. Things That Look Like Bugs and Are Not

- **Ecosystem pair versioning**: `structured-address-fix` and `structured-address-fix-mcp` both sit on Python `>=3.12` and must be bumped in lockstep.
- **November 2026 Cutover**: Swift deferred the cutover on 27 August 2026 and will confirm replacement timing by December; the underlying ISO 20022 requirement stands, so date helpers report `status="deferred"`.
