# The remediation model

Assessment and remediation flow through a small set of frozen Pydantic
entities. This page describes how they fit together, from a single risk finding
up to the result envelope a caller receives.

## Findings

A `RiskFinding` is one compliance risk located in an address or message:

```python
class RiskFinding(BaseModel):        # frozen
    code: FindingCode                # e.g. FindingCode.UNSTRUCTURED_ONLY
    severity: Severity               # INFO | WARNING | ERROR | CRITICAL
    message: str
    policy_id: str                   # which policy raised it
    location: str = "/"              # JSON pointer into the source message
    party_role: PartyRole | None = None
    rulebook_clause: str | None = None
    rejects_payment: bool = False
```

`location` is a JSON pointer into the source document (or `"/"` for a bare
address), so a finding always points back to the exact element that raised it.
`rejects_payment` distinguishes a finding that will bounce the payment from one
that is merely advisory. See [policies](policies.md) for the finding-code
catalogue.

## Patch operations

A remediation is expressed as reversible, RFC 6902-shaped edits:

```python
class PatchOperation(BaseModel):     # frozen
    op: PatchOp                      # SET | REMOVE | MOVE
    path: str                        # JSON pointer to the target element
    value: str | None = None
    from_: str | None = None         # serialises as "from"; MOVE only
    reason_code: FindingCode         # the finding this operation resolves
    source_token: str | None = None  # the originating AdrLine fragment
    confidence: float = 1.0          # 0.0..1.0, from the deriving heuristic
```

Every operation is self-justifying. It records **why** it exists
(`reason_code`), **where its value came from** (`source_token` — the `AdrLine`
fragment a heuristic split, when applicable), and **how confident** the
heuristic was (`confidence`). This makes an entire remediation auditable
element by element.

The three op kinds:

- `SET` — populate a structured element (e.g. set `StrtNm` from a parsed
  `AdrLine` token).
- `REMOVE` — drop a now-redundant element (e.g. an `AdrLine` fully absorbed
  into structured fields).
- `MOVE` — relocate a value from one path to another (`from_` → `path`).

## Suggestions

A `RemediationSuggestion` is the proposed transformation of **one** address,
fully explained:

```python
class RemediationSuggestion(BaseModel):          # frozen
    before: CanonicalAddress
    after: CanonicalAddress
    operations: tuple[PatchOperation, ...] = ()
    resolved_findings: tuple[FindingCode, ...] = ()
    residual_findings: tuple[RiskFinding, ...] = ()
    explanation: str = ""
```

`residual_findings` is the honest part of the model: it captures what
remediation **could not** resolve — a missing town no heuristic could infer, a
non-Latin character set that needs transliteration by a human — so the gap
between the remediated address and full compliance is always visible. Compare
`before.classification` with `after.classification` to see the promotion (for
example `unstructured → hybrid`).

## Result envelopes

Two top-level, serializable envelopes are returned by the services facade.

`ValidationReport` — the read-only outcome of `assess`:

```python
class ValidationReport(BaseModel):               # frozen
    policy_id: str
    message_type: MessageType | None = None
    assessed_addresses: int = 0
    findings: tuple[RiskFinding, ...] = ()
    is_compliant: bool = True
```

`RemediationResult` — the outcome of `remediate`: a report plus the proposed
fixes and, optionally, the patched XML:

```python
class RemediationResult(BaseModel):              # frozen
    policy_id: str
    message_type: MessageType | None = None
    assessed_addresses: int = 0
    findings: tuple[RiskFinding, ...] = ()
    suggestions: tuple[RemediationSuggestion, ...] = ()
    is_compliant_before: bool = True
    is_compliant_after: bool = True
    patched_xml: str | None = None
```

`is_compliant_before` / `is_compliant_after` bracket the remediation so a caller
can see, in one comparison, whether applying the suggestions would clear the
policy. `patched_xml` is populated only when the caller asks for the rewritten
document.

## Applying a remediation

The suggestions and patch operations are a **proposal**. Because every
`PatchOperation` is reversible and carries its `reason_code`, `source_token`,
and `confidence`, a host can present the change for review, apply only the
high-confidence operations, or route low-confidence ones to an operator. The
library never mutates a live payment on your behalf; you decide what to apply.
