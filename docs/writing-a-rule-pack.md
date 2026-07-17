# Writing a rule pack

The four built-in policies cover the open, published scheme rules. Requirements
that are proprietary, correspondent-specific, or jurisdiction-specific are
better shipped as **premium rule packs**: separately installable Python
distributions that register additional policies through an entry point. This
page describes the contract.

The core never bundles a pack. A pack is discovered automatically once
installed, contributes its own policy ids and finding codes, and is gated at
load time by entitlement + integrity checks.

## 1. Advertise the pack via an entry point

Register your pack under the `structured_address_fix.policies` entry-point
group. The name is the policy id callers will pass to `assess` / `remediate`;
the value points at the `PolicyPack` object your distribution exposes:

```toml
# pyproject.toml of your pack distribution
[project]
name = "acme-saf-pack"
version = "1.0.0"
dependencies = ["structured-address-fix>=0.1"]

[project.entry-points."structured_address_fix.policies"]
acme-correspondent-2026 = "acme_saf_pack:PACK"
```

Poetry projects use the equivalent stanza:

```toml
[tool.poetry.plugins."structured_address_fix.policies"]
acme-correspondent-2026 = "acme_saf_pack:PACK"
```

If two installed packs claim the same policy id, resolution raises
`PolicyConflictError` (see the [error taxonomy](error-taxonomy.md)).

## 2. Implement the rulebook

A pack inspects a `CanonicalAddress` and returns `RiskFinding`s. Reuse the
shared domain vocabulary so downstream code keys on findings uniformly. Custom,
pack-specific finding codes carry their **own** prefix (never `SAF`) so they can
never collide with the core codes:

```python
# acme_saf_pack/__init__.py
from structured_address_fix.domain import (
    CanonicalAddress, FindingCode, RiskFinding, Severity,
)


def check(address: CanonicalAddress, *, location: str) -> list[RiskFinding]:
    """Raise the pack's findings against a single address.

    ``location`` is the JSON pointer to the address's ``PstlAdr`` element, so
    findings thread back to the exact node.
    """
    findings: list[RiskFinding] = []

    # Example: this correspondent profile insists on a post code.
    if address.post_code is None:
        findings.append(
            RiskFinding(
                code=FindingCode.MISSING_TOWN,   # or a pack-specific code
                severity=Severity.ERROR,
                message="Correspondent profile requires a post code.",
                policy_id="acme-correspondent-2026",
                location=location,
                rulebook_clause="ACME-MP 4.2",
                rejects_payment=True,
            )
        )
    return findings
```

## 3. Bind it into a `PolicyPack`

Expose the object named in your entry point. A pack binds its policy id to the
`check` callable and declares its metadata (id, version, and — for a commercial
pack — its entitlement + integrity material):

```python
# acme_saf_pack/__init__.py (continued)
from structured_address_fix.plugins import PolicyPack

PACK = PolicyPack(
    policy_id="acme-correspondent-2026",
    version="1.0.0",
    check=check,
)
```

## 4. Entitlement and integrity (commercial packs)

For a paid pack, the loader enforces two gates before a pack's rules run:

- **Entitlement** — the caller must be licensed for the pack. A pack the caller
  is not entitled to raises `PackNotLicensedError` (`SAF_PACK_NOT_LICENSED`).
- **Integrity** — the pack must pass its signature / version check. A tampered
  or mismatched pack raises `PackIntegrityError` (`SAF_PACK_INTEGRITY`).

Both are subclasses of `EntitlementError`, so a host can catch the family and
surface a licensing prompt distinctly from an input or policy error.

## 5. Test it like the core

A pack should hold itself to the same bar as the core library: 100% line +
branch coverage on its rules, a Hypothesis property test over the address
shapes it cares about, and a regression test pinning each finding code's meaning
(codes are a stable public API — a changed rule earns a new code, never a
repurposed one).

## Checklist

- [ ] Entry point registered under `structured_address_fix.policies`
- [ ] `check` returns `RiskFinding`s with your `policy_id` and a `location`
- [ ] Custom finding codes use a non-`SAF` prefix
- [ ] `PolicyPack` object exposed at the entry-point target
- [ ] Entitlement + integrity material set for a commercial pack
- [ ] Tests pin every finding code and cover the classification edges
