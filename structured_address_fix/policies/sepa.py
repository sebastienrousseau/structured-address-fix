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

"""The SEPA rulebook address policy.

The SEPA flavour requires both Town Name and Country and caps residual
``AdrLine`` at two lines. Missing Country rejects the payment; the
remaining defects are flagged at ``ERROR`` for correction.
"""

from __future__ import annotations

from typing import ClassVar

from structured_address_fix.domain.address import (
    MAX_HYBRID_ADDRESS_LINE_COUNT,
    CanonicalAddress,
)
from structured_address_fix.domain.enums import PolicyId, Severity
from structured_address_fix.domain.findings import RiskFinding
from structured_address_fix.policies.base import (
    BasePolicy,
    PolicyContext,
    PolicyTier,
    compact,
)


class SepaPolicy(BasePolicy):
    """SEPA rulebook address policy — town + country, two-line cap."""

    id: ClassVar[str] = PolicyId.SEPA.value
    title: ClassVar[str] = "SEPA rulebook postal address"
    tier: ClassVar[PolicyTier] = "oss"

    def assess(
        self, address: CanonicalAddress, ctx: PolicyContext
    ) -> list[RiskFinding]:
        """Assess ``address`` against the SEPA rulebook requirements."""
        return compact(
            self._missing_town(
                address,
                severity=Severity.ERROR,
                clause="mandatory_town",
            ),
            self._missing_country(
                address,
                severity=Severity.ERROR,
                clause="mandatory_country",
                rejects_payment=True,
            ),
            self._non_iso_country(
                address,
                severity=Severity.ERROR,
                clause="non_iso_country",
            ),
            self._adrline_overflow(
                address,
                severity=Severity.ERROR,
                clause="adrline_cap",
                max_lines=MAX_HYBRID_ADDRESS_LINE_COUNT,
            ),
            self._structured_field_overflow(
                address,
                severity=Severity.ERROR,
                clause="structured_overflow",
            ),
        )
