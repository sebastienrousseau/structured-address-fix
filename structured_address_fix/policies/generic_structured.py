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

"""The generic ISO 20022 structural baseline policy.

Unlike CBPR+, this policy enforces no scheme rulebook and no cliff: it
raises only structural findings that hold for any ISO 20022 postal address
— a non-ISO country code, ``AdrLine`` overflow, and structured-field
overflow — all at ``WARNING`` and none rejecting payment. It is the safe
lowest-common-denominator policy for callers who only want data hygiene.
"""

from __future__ import annotations

from typing import ClassVar

from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import PolicyId, Severity
from structured_address_fix.domain.findings import RiskFinding
from structured_address_fix.policies.base import (
    BasePolicy,
    PolicyContext,
    PolicyTier,
    compact,
)


class GenericStructuredPolicy(BasePolicy):
    """ISO 20022 structural baseline — no rulebook, no cliff."""

    id: ClassVar[str] = PolicyId.GENERIC_STRUCTURED.value
    title: ClassVar[str] = "Generic ISO 20022 structural baseline"
    tier: ClassVar[PolicyTier] = "oss"

    def assess(
        self, address: CanonicalAddress, ctx: PolicyContext
    ) -> list[RiskFinding]:
        """Assess ``address`` for purely structural ISO 20022 defects."""
        return compact(
            self._non_iso_country(
                address,
                severity=Severity.WARNING,
                clause="non_iso_country",
            ),
            self._adrline_overflow(
                address,
                severity=Severity.WARNING,
                clause="adrline_overflow",
            ),
            self._structured_field_overflow(
                address,
                severity=Severity.WARNING,
                clause="structured_overflow",
            ),
        )
