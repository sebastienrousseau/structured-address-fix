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

"""Remediation entities: patch operations and suggestions.

A :class:`PatchOperation` is an RFC 6902-shaped edit whose ``path`` is a
JSON pointer into the ISO 20022 message (e.g. an element under
``.../PstlAdr``). Every operation records *why* it exists (the finding it
resolves), *where its value came from* (the originating ``AdrLine``
fragment, when applicable), and *how confident* the deriving heuristic
was, so remediation is fully explainable and auditable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.findings import FindingCode, RiskFinding


class PatchOp(StrEnum):
    """The kind of edit a :class:`PatchOperation` performs."""

    SET = "set"
    REMOVE = "remove"
    MOVE = "move"


class PatchOperation(BaseModel):
    """A single, reversible edit that moves an address toward compliance.

    Immutable. ``from_`` serializes as ``"from"`` (an RFC 6902 keyword)
    and is populated only for ``MOVE`` operations.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    op: PatchOp
    path: str
    value: str | None = None
    from_: str | None = Field(default=None, alias="from")
    reason_code: FindingCode
    source_token: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class RemediationSuggestion(BaseModel):
    """The proposed transformation of one address, fully explained.

    ``residual_findings`` captures what remediation could *not* resolve
    (e.g. a missing town that no heuristic could infer), so a caller can
    always see the gap between the remediated address and full compliance.
    """

    model_config = ConfigDict(frozen=True)

    before: CanonicalAddress
    after: CanonicalAddress
    operations: tuple[PatchOperation, ...] = ()
    resolved_findings: tuple[FindingCode, ...] = ()
    residual_findings: tuple[RiskFinding, ...] = ()
    explanation: str = ""
