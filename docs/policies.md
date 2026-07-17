# Policies

A **policy** is a rulebook. It inspects a `CanonicalAddress` (in the context of
the message it came from) and raises `RiskFinding`s, each keyed by a stable
`FindingCode` and carrying a `Severity`. Selecting a policy chooses *which* rules
apply and *how serious* each is; the finding codes themselves are shared across
policies so downstream code can key on them uniformly.

## Built-in policies

Four policies ship with the core library. Their identifiers are the
`PolicyId` enum values:

| `PolicyId` | Value | Scope |
| :--- | :--- | :--- |
| `CBPR_2026` | `cbpr-2026` | SWIFT CBPR+ UG2026 cross-border requirements — the Nov-2026 cliff rules. **The default.** |
| `SEPA` | `sepa` | SEPA credit-transfer address expectations |
| `HVPS_PLUS` | `hvps-plus` | HVPS+ high-value / RTGS market-practice (T2, CHAPS, Fedwire, Lynx) |
| `GENERIC_STRUCTURED` | `generic-structured` | Scheme-agnostic structured-vs-unstructured hygiene |

The default is `cbpr-2026`. It can be overridden per call, or globally with the
`SAF_DEFAULT_POLICY` environment variable:

```python
from structured_address_fix.config import default_policy_id
default_policy_id()   # "cbpr-2026", unless SAF_DEFAULT_POLICY is set
```

Requesting an unregistered policy id raises `UnknownPolicyError` (see the
[error taxonomy](error-taxonomy.md)).

## Finding codes

Finding codes are a **stable public API**: a code's meaning is fixed once
released, and a changed rule earns a new code rather than repurposing an
existing one. The core codes carry the `SAF` prefix; premium rule-pack codes
carry their own prefixes so they never collide.

| Code | Name | Raised when |
| :--- | :--- | :--- |
| `SAF001` | `UNSTRUCTURED_ONLY` | The address is `AdrLine`-only; rejected from the cliff date |
| `SAF002` | `MISSING_COUNTRY` | No `Ctry` element; mandatory for cross-border from the cliff |
| `SAF003` | `MISSING_TOWN` | No `TwnNm` element; mandatory for the hybrid minimum bar |
| `SAF004` | `ADRLINE_OVERFLOW` | More than seven `AdrLine` lines, or a line over 70 characters |
| `SAF005` | `HYBRID_RESIDUAL_ADRLINE` | A structured address still carries residual `AdrLine` text |
| `SAF006` | `NON_ISO_COUNTRY_CODE` | `Ctry` is not a valid ISO 3166-1 alpha-2 code |
| `SAF007` | `NON_LATIN_CHARACTERS` | The address contains characters outside the SWIFT-permitted set |
| `SAF008` | `STRUCTURED_FIELD_OVERFLOW` | A structured element exceeds its ISO 20022 maximum length |

## Severity

Each finding carries a `Severity`, ordered least to most serious: `INFO`,
`WARNING`, `ERROR`, `CRITICAL`. A `RiskFinding` also flags `rejects_payment`
when the underlying scheme would reject the message outright (rather than merely
truncating or warning), so a caller can triage "will bounce" from "should fix".

## How policies differ

The same finding code can carry a different severity, or simply not apply, under
a different policy. For example:

- Under `cbpr-2026`, `SAF001` (`UNSTRUCTURED_ONLY`) is a payment-rejecting
  `ERROR` from the cliff date — the whole reason this library exists.
- Under `generic-structured`, the same `SAF001` may be a `WARNING`: the address
  is structurally weak, but this scheme-agnostic profile makes no claim about a
  specific scheme's rejection behaviour.
- `sepa` and `hvps-plus` tighten or relax individual element expectations to
  match their respective market-practice guidelines.

Consult [the November 2026 cutover](nov-2026-cutover.md) for the scheme-by-scheme
picture behind `cbpr-2026` and `hvps-plus`.

## Premium policies

Additional policies — proprietary market-practice profiles, correspondent
overlays — install as separate distributions and register through the
`structured_address_fix.policies` entry point. See
[writing a rule pack](writing-a-rule-pack.md).
