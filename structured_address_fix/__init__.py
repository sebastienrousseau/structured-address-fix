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

"""structured-address-fix: ISO 20022 postal-address remediation.

Detects, scores, and remediates non-compliant postal addresses in ISO
20022 payment messages ahead of the 14 November 2026 cliff, when fully
unstructured addresses are rejected across the major cross-border and
high-value schemes. The public surface is the :mod:`structured_address_fix.
services` facade; the domain models are re-exported here for convenience.
"""

from structured_address_fix.domain import (
    AddressClassification,
    AddressedParty,
    CanonicalAddress,
    FindingCode,
    MessageType,
    PartyRole,
    PatchOp,
    PatchOperation,
    PolicyId,
    RemediationResult,
    RemediationSuggestion,
    RiskFinding,
    Severity,
    ValidationReport,
)

__version__ = "0.0.2"

__all__ = [
    "AddressClassification",
    "AddressedParty",
    "CanonicalAddress",
    "FindingCode",
    "MessageType",
    "PartyRole",
    "PatchOp",
    "PatchOperation",
    "PolicyId",
    "RemediationResult",
    "RemediationSuggestion",
    "RiskFinding",
    "Severity",
    "ValidationReport",
    "__version__",
]
