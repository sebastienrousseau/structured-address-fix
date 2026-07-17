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

"""Domain layer: pure entities and their invariants, with zero I/O."""

from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
    PolicyId,
    Severity,
)
from structured_address_fix.domain.findings import FindingCode, RiskFinding
from structured_address_fix.domain.party import AddressedParty
from structured_address_fix.domain.remediation import (
    PatchOp,
    PatchOperation,
    RemediationSuggestion,
)
from structured_address_fix.domain.result import (
    RemediationResult,
    ValidationReport,
)

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
]
