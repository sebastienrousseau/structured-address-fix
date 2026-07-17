# Contributing to structured-address-fix

Thank you for your interest in contributing to structured-address-fix. This
guide covers the development workflow and standards.

`structured-address-fix` is the core ISO 20022 postal-address remediation
library of the sebastienrousseau ISO 20022 suite. It supersedes and generalises
`pacs008.standards.address`, and it is the shared engine wrapped by the thin
[`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp)
server, so most behaviour lives here in the core library.

## Development Setup

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git with SSH commit signing configured

### Setup

```bash
# Clone and install
git clone git@github.com:sebastienrousseau/structured-address-fix.git
cd structured-address-fix
poetry install

# Verify
poetry run pytest tests/ -q
```

### On macOS

```bash
brew install python@3.12 poetry
```

### On Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip
pip install poetry
```

### On WSL

```bash
sudo apt install python3 python3-pip
pip install poetry
# Ensure ~/.local/bin is in PATH
```

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
3. **Make changes** — follow the coding standards below
4. **Run tests** (the coverage gate is 100% line + branch):
   ```bash
   poetry run pytest tests/ -v
   ```
5. **Run linters**:
   ```bash
   poetry run ruff check structured_address_fix/
   poetry run mypy structured_address_fix/
   poetry run black --check structured_address_fix/ tests/
   ```
6. **Sign and commit**:
   ```bash
   git commit -S -m "feat: add my feature"
   ```
7. **Push** and open a pull request

## Commit Signing (Required)

All commits **must** be signed with SSH or GPG.

### SSH Signing

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519
git config --global commit.gpgsign true
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add the HVPS+ residual-AdrLine rule to the hvps-plus policy
fix: preserve building_number when splitting a two-line AdrLine
docs: document the entry-point stanza for a premium rule pack
test: cover the STRUCTURED_FIELD_OVERFLOW finding
refactor: extract the per-country AdrLine heuristic dispatch
```

## Coding Standards

- **Line length:** 79 characters (enforced by Black + Ruff)
- **Type hints:** Required on all public functions (mypy strict)
- **Docstrings:** Required on all public classes and functions (interrogate
  enforces 100% coverage)
- **Finding + policy identifiers are a public API:** a `FindingCode` or
  `PolicyId` value's meaning is fixed once released. A changed rule earns a
  **new** code rather than repurposing an existing one.
- **Tests:** Every new rule, heuristic, or behaviour change must include tests;
  the suite keeps 100% line + branch coverage. Prefer a Hypothesis property
  test for classification and remediation invariants.

## Testing

```bash
# Full suite
poetry run pytest tests/ -v

# Single file
poetry run pytest tests/test_classification.py -v
```

## Pull Request Checklist

- [ ] All tests pass (`poetry run pytest`)
- [ ] Coverage stays at 100% line + branch
- [ ] Linters pass (`ruff check`, `mypy`, `black --check`)
- [ ] Commits are signed
- [ ] PR title follows conventional commit format
- [ ] New rules include tests and a rulebook-clause citation where applicable

## License

By contributing, you agree that your contributions will be licensed under
the [Apache License 2.0](LICENSE).
