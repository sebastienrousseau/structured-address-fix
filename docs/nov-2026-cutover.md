# The November 2026 cutover

The single most load-bearing constant in this library is a date. It is defined
once, in `structured_address_fix.config`:

```python
from structured_address_fix.config import NOV_2026_CLIFF
NOV_2026_CLIFF   # datetime.date(2026, 11, 14)
```

From this date, the long "coexistence" period during which ISO 20022 messages
could still carry fully unstructured postal addresses ends across the major
cross-border and high-value schemes. An address that is `AdrLine`-only becomes
non-compliant and liable to rejection.

## Three shapes, one target

CBPR+ UG2026 recognises three address shapes. This library classifies every
address into one of them (see [the quick start](quickstart.md) for the rules):

| Shape | What it is | Status from the cliff |
| :--- | :--- | :--- |
| **Structured** | `TwnNm` + `Ctry` + structured detail, no `AdrLine` | Fully compliant — the target |
| **Hybrid** | `TwnNm` + `Ctry` + 1–2 residual `AdrLine` lines | Accepted — the minimum bar |
| **Unstructured** | `AdrLine`-only (no town / country) | **Rejected** |

The job of `structured-address-fix` is to move addresses up this ladder —
`unstructured → hybrid → structured` — before the deadline forces the issue,
and to tell you honestly (via residual findings) about anything it could not
promote.

## The schemes

The deadline is not a single switch but a cluster of aligned scheme cutovers in
the same window. The one that binds first is the reference date the library
uses.

- **SWIFT CBPR+ (cross-border)** — the UG2026 usage guidelines end
  unstructured-address coexistence on **14 November 2026**. This is the binding
  reference date, `NOV_2026_CLIFF`, because it is the earliest and the widest in
  reach. The `cbpr-2026` policy encodes these rules.
- **HVPS+ / RTGS market infrastructures** — the high-value systems (the
  Eurosystem's **T2**, the Bank of England's **CHAPS**, the Bank of Canada's
  **Lynx**, and others) align their structured-address expectations to the same
  coexistence-end window under HVPS+ market practice. The `hvps-plus` policy
  encodes these.
- **Fedwire (US)** — the Federal Reserve's own ISO 20022 cutover lands on
  **16 November 2026**, two days after the SWIFT date. Because the SWIFT date
  binds first for any message that touches the cross-border network, `14
  November 2026` remains the reference used throughout the library.

Because the dates cluster rather than coincide exactly, treat `NOV_2026_CLIFF`
as the point by which you want every relevant address already remediated,
not the moment to start.

## What to do before the cliff

1. **Assess your outbound and inbound traffic.** Run `assess` over a
   representative sample of `pacs.008` / `pain.001` messages against
   `cbpr-2026` (and `hvps-plus` if you settle over an RTGS). Count how many
   addresses are `UNSTRUCTURED` today.
2. **Remediate what you can, automatically.** Run `remediate` to turn
   `AdrLine`-only addresses into hybrid or structured ones with explainable,
   reversible patches.
3. **Route the residue to a human.** Every fragment a heuristic could not
   resolve is reported as a residual finding, not silently guessed — the short
   list of addresses that genuinely need manual data enrichment.
4. **Re-assess.** Confirm `is_compliant_after` clears the policy for the
   remediated set, and fold the check into CI or a pre-submission gate so new
   traffic stays compliant.

## Why "fix" and not just "flag"

Detection alone leaves you with a backlog and a deadline. `structured-address-
fix` pairs every finding with a proposed, auditable remediation so the work of
becoming compliant is mechanised — while keeping a human in the loop for exactly
the cases where a machine should not guess.
