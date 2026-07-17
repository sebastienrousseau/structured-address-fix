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

"""Top-level result envelopes returned by the service layer.

:class:`ValidationReport` is the read-only outcome of assessing a message
or address; :class:`RemediationResult` adds the proposed fixes and,
optionally, the patched XML. Both are the explainable, serializable shapes
the MCP tools hand back to a client.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from structured_address_fix.domain.enums import MessageType
from structured_address_fix.domain.findings import RiskFinding
from structured_address_fix.domain.remediation import RemediationSuggestion


class ValidationReport(BaseModel):
    """The outcome of assessing addresses against a policy."""

    model_config = ConfigDict(frozen=True)

    policy_id: str
    message_type: MessageType | None = None
    assessed_addresses: int = 0
    findings: tuple[RiskFinding, ...] = ()
    is_compliant: bool = True


class RemediationResult(BaseModel):
    """A validation report plus proposed remediation and optional patch."""

    model_config = ConfigDict(frozen=True)

    policy_id: str
    message_type: MessageType | None = None
    assessed_addresses: int = 0
    findings: tuple[RiskFinding, ...] = ()
    suggestions: tuple[RemediationSuggestion, ...] = ()
    is_compliant_before: bool = True
    is_compliant_after: bool = True
    patched_xml: str | None = None
