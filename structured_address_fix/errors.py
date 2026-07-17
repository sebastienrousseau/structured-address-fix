# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The exception taxonomy for structured-address-fix.

Every error raised by the domain, services, and adapters is a subclass of
:class:`StructuredAddressError` and carries a stable ``code`` plus safe
``context``. The MCP transport catches these at the boundary and returns
``{"error": {...}}`` payloads rather than leaking tracebacks, mirroring
the convention used across the ISO 20022 MCP suite.
"""

from __future__ import annotations

from typing import Any


class StructuredAddressError(Exception):
    """Base class for every error this package raises."""

    #: Stable, machine-readable error code (overridden per subclass).
    code: str = "SAF_ERROR"

    def __init__(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        """Store the human-readable message and optional structured context."""
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = context or {}


# --- Input errors: the caller supplied something invalid -------------------


class InputError(StructuredAddressError):
    """The caller's input was malformed or unsupported."""

    code = "SAF_INPUT"


class MalformedXMLError(InputError):
    """The supplied document could not be parsed as XML."""

    code = "SAF_MALFORMED_XML"


class UnsupportedMessageTypeError(InputError):
    """The document is not a recognized ISO 20022 message type."""

    code = "SAF_UNSUPPORTED_MESSAGE"


class AddressNotFoundError(InputError):
    """No postal address was found at the requested location."""

    code = "SAF_ADDRESS_NOT_FOUND"


class InvalidAddressError(InputError):
    """The supplied address violates a canonical-model invariant."""

    code = "SAF_INVALID_ADDRESS"


# --- Policy errors ---------------------------------------------------------


class PolicyError(StructuredAddressError):
    """Base class for policy-resolution failures."""

    code = "SAF_POLICY"


class UnknownPolicyError(PolicyError):
    """The requested policy id is not registered."""

    code = "SAF_UNKNOWN_POLICY"


class PolicyConflictError(PolicyError):
    """Two policies claim the same id in the registry."""

    code = "SAF_POLICY_CONFLICT"


# --- Remediation errors ----------------------------------------------------


class RemediationError(StructuredAddressError):
    """Base class for remediation failures."""

    code = "SAF_REMEDIATION"


class UnresolvableFindingError(RemediationError):
    """No heuristic can resolve a finding into a patch operation."""

    code = "SAF_UNRESOLVABLE"


class PatchApplicationError(RemediationError):
    """A patch operation could not be applied to the target document."""

    code = "SAF_PATCH_FAILED"


# --- Entitlement errors (premium rule packs) -------------------------------


class EntitlementError(StructuredAddressError):
    """Base class for premium-pack entitlement failures."""

    code = "SAF_ENTITLEMENT"


class PackNotLicensedError(EntitlementError):
    """The caller is not entitled to the requested premium pack."""

    code = "SAF_PACK_NOT_LICENSED"


class PackIntegrityError(EntitlementError):
    """A premium pack failed its signature or version integrity check."""

    code = "SAF_PACK_INTEGRITY"
