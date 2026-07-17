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

"""The HVPS+ high-value address policy.

HVPS+ is the strictest built-in: it rejects unstructured addresses like
CBPR+, but it also leans towards structured-only by escalating hybrid
residual ``AdrLine`` from a warning to an ``ERROR`` that rejects the
payment. Structural checks match the CBPR+ severities.
"""

from __future__ import annotations

from typing import ClassVar

from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import (
    AddressClassification,
    PolicyId,
    Severity,
)
from structured_address_fix.domain.findings import FindingCode, RiskFinding
from structured_address_fix.policies.base import (
    BasePolicy,
    PolicyContext,
    PolicyTier,
    compact,
)


class HvpsPlusPolicy(BasePolicy):
    """HVPS+ high-value address policy — structured-only leaning."""

    id: ClassVar[str] = PolicyId.HVPS_PLUS.value
    title: ClassVar[str] = "HVPS+ high-value structured address"
    tier: ClassVar[PolicyTier] = "oss"

    def assess(
        self, address: CanonicalAddress, ctx: PolicyContext
    ) -> list[RiskFinding]:
        """Assess ``address`` against the strict HVPS+ requirements."""
        classification = address.classification

        classification_findings: list[RiskFinding] = []
        if classification is AddressClassification.UNSTRUCTURED:
            classification_findings = compact(
                self._missing_town(
                    address,
                    severity=Severity.CRITICAL,
                    clause="mandatory_town",
                    rejects_payment=True,
                ),
                self._missing_country(
                    address,
                    severity=Severity.CRITICAL,
                    clause="mandatory_country",
                    rejects_payment=True,
                ),
                self._finding(
                    FindingCode.UNSTRUCTURED_ONLY,
                    Severity.CRITICAL,
                    "Unstructured address is rejected by HVPS+.",
                    "reject_unstructured",
                    rejects_payment=True,
                ),
            )
        elif classification is AddressClassification.HYBRID:
            classification_findings = compact(
                self._hybrid_residual(
                    address,
                    severity=Severity.ERROR,
                    clause="structured_only",
                    rejects_payment=True,
                )
            )

        return classification_findings + compact(
            self._non_iso_country(
                address,
                severity=Severity.ERROR,
                clause="non_iso_country",
            ),
            self._adrline_overflow(
                address,
                severity=Severity.ERROR,
                clause="adrline_overflow",
            ),
            self._structured_field_overflow(
                address,
                severity=Severity.ERROR,
                clause="structured_overflow",
            ),
        )
