# Error taxonomy

Every error raised by the domain, services, and adapters is a subclass of
`StructuredAddressError`. Each carries a stable, machine-readable `code` and an
optional safe `context` dictionary, so a wrapping transport (MCP / REST / LSP)
can catch at the boundary and return an `{"error": {...}}` payload rather than
leaking a traceback.

```python
class StructuredAddressError(Exception):
    code: str = "SAF_ERROR"

    def __init__(self, message: str, *, context: dict | None = None) -> None:
        ...
        self.message = message
        self.context = context or {}
```

Distinguish these typed errors — invalid input, an unknown policy, an
unresolvable finding — from a Pydantic `ValidationError`, which is what
`CanonicalAddress` raises when a *field* invariant is violated (an over-length
element, more than seven `AdrLine`s, a non-two-letter country).

## The hierarchy

```
StructuredAddressError                (SAF_ERROR)
├── InputError                        (SAF_INPUT)
│   ├── MalformedXMLError             (SAF_MALFORMED_XML)
│   ├── UnsupportedMessageTypeError   (SAF_UNSUPPORTED_MESSAGE)
│   ├── AddressNotFoundError          (SAF_ADDRESS_NOT_FOUND)
│   └── InvalidAddressError           (SAF_INVALID_ADDRESS)
├── PolicyError                       (SAF_POLICY)
│   ├── UnknownPolicyError            (SAF_UNKNOWN_POLICY)
│   └── PolicyConflictError           (SAF_POLICY_CONFLICT)
├── RemediationError                  (SAF_REMEDIATION)
│   ├── UnresolvableFindingError      (SAF_UNRESOLVABLE)
│   └── PatchApplicationError         (SAF_PATCH_FAILED)
└── EntitlementError                  (SAF_ENTITLEMENT)
    ├── PackNotLicensedError          (SAF_PACK_NOT_LICENSED)
    └── PackIntegrityError            (SAF_PACK_INTEGRITY)
```

## Codes

| Code | Exception | Meaning |
| :--- | :--- | :--- |
| `SAF_ERROR` | `StructuredAddressError` | Base class for every error the package raises |
| `SAF_INPUT` | `InputError` | The caller's input was malformed or unsupported |
| `SAF_MALFORMED_XML` | `MalformedXMLError` | The document could not be parsed as XML |
| `SAF_UNSUPPORTED_MESSAGE` | `UnsupportedMessageTypeError` | Not a recognised ISO 20022 message type |
| `SAF_ADDRESS_NOT_FOUND` | `AddressNotFoundError` | No postal address at the requested location |
| `SAF_INVALID_ADDRESS` | `InvalidAddressError` | The address violates a canonical-model invariant |
| `SAF_POLICY` | `PolicyError` | Base for policy-resolution failures |
| `SAF_UNKNOWN_POLICY` | `UnknownPolicyError` | The requested policy id is not registered |
| `SAF_POLICY_CONFLICT` | `PolicyConflictError` | Two policies claim the same id in the registry |
| `SAF_REMEDIATION` | `RemediationError` | Base for remediation failures |
| `SAF_UNRESOLVABLE` | `UnresolvableFindingError` | No heuristic can resolve a finding into a patch |
| `SAF_PATCH_FAILED` | `PatchApplicationError` | A patch could not be applied to the target document |
| `SAF_ENTITLEMENT` | `EntitlementError` | Base for premium-pack entitlement failures |
| `SAF_PACK_NOT_LICENSED` | `PackNotLicensedError` | The caller is not entitled to the requested pack |
| `SAF_PACK_INTEGRITY` | `PackIntegrityError` | A pack failed its signature or version integrity check |

## Handling pattern

Catch the base class at the transport boundary and serialise:

```python
from structured_address_fix.errors import StructuredAddressError

try:
    report = assess(message_xml, policy=policy_id)
except StructuredAddressError as exc:
    return {"error": {"code": exc.code, "message": exc.message,
                      "context": exc.context}}
```

The `context` dictionary is deliberately safe to serialise — it carries
structured, non-sensitive detail (the offending policy id, the location that had
no address) rather than raw internal state.
