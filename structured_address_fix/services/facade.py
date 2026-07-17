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

"""The single service facade for structured-address-fix.

This is the shared surface the CLI, a REST API, and the MCP server all
call — mirroring the ``services`` facade convention used across the ISO
20022 suite. It resolves a policy id to a registered policy and delegates
to the assess / remediate / classify use-cases, returning explainable,
JSON-serializable result models.
"""

from __future__ import annotations

from datetime import date

from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.config import default_policy_id
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
)
from structured_address_fix.domain.findings import RiskFinding
from structured_address_fix.domain.remediation import PatchOperation
from structured_address_fix.domain.result import (
    RemediationResult,
    ValidationReport,
)
from structured_address_fix.policies.base import AddressPolicy
from structured_address_fix.policies.registry import (
    PolicyInfo,
    PolicyRegistry,
    default_registry,
)
from structured_address_fix.services import assess as _assess
from structured_address_fix.services import classify as _classify
from structured_address_fix.services import remediate as _remediate
from structured_address_fix.services.apply_patch import apply as _apply


def _resolve(policy_id: str | None, registry: PolicyRegistry) -> AddressPolicy:
    """Resolve a policy id (or the default) to a registered policy."""
    return registry.get(policy_id or default_policy_id())


def list_policies(
    *, registry: PolicyRegistry = default_registry
) -> list[PolicyInfo]:
    """List the policies available in ``registry``."""
    return registry.list_policies()


def classify_address(address: CanonicalAddress) -> AddressClassification:
    """Classify a single address."""
    return _classify.classify_address(address)


def classify_message(
    xml: str,
) -> tuple[MessageType, dict[PartyRole, AddressClassification]]:
    """Classify every addressed party in an ISO 20022 message."""
    return _classify.classify_message(xml)


def assess_address(
    address: CanonicalAddress,
    policy_id: str | None = None,
    *,
    as_of: date | None = None,
    country_hint: str | None = None,
    registry: PolicyRegistry = default_registry,
) -> ValidationReport:
    """Assess a single address against a policy."""
    policy = _resolve(policy_id, registry)
    return _assess.assess_address(
        address, policy, as_of=as_of, country_hint=country_hint
    )


def assess_message(
    xml: str,
    policy_id: str | None = None,
    *,
    as_of: date | None = None,
    registry: PolicyRegistry = default_registry,
) -> ValidationReport:
    """Assess every addressed party in an ISO 20022 message."""
    policy = _resolve(policy_id, registry)
    return _assess.assess_message(xml, policy, as_of=as_of)


def remediate_address(
    address: CanonicalAddress,
    policy_id: str | None = None,
    *,
    country_hint: str | None = None,
    as_of: date | None = None,
    registry: PolicyRegistry = default_registry,
) -> RemediationResult:
    """Assess and remediate a single address."""
    policy = _resolve(policy_id, registry)
    before = _assess.assess_address(
        address, policy, as_of=as_of, country_hint=country_hint
    )
    suggestion = _remediate.remediate_address(
        address, policy, country_hint=country_hint, as_of=as_of
    )
    after_compliant = not any(
        f.rejects_payment for f in suggestion.residual_findings
    )
    return RemediationResult(
        policy_id=policy.id,
        assessed_addresses=1,
        findings=before.findings,
        suggestions=(suggestion,),
        is_compliant_before=before.is_compliant,
        is_compliant_after=after_compliant,
    )


def remediate_message(
    xml: str,
    policy_id: str | None = None,
    *,
    apply: bool = False,
    as_of: date | None = None,
    registry: PolicyRegistry = default_registry,
) -> RemediationResult:
    """Assess and remediate every addressed party in a message.

    When ``apply`` is true the derived operations are applied and the
    patched document is returned in :attr:`RemediationResult.patched_xml`.
    """
    policy = _resolve(policy_id, registry)
    message_type, parties = read_addresses(xml)

    findings: list[RiskFinding] = []
    suggestions = []
    operations: list[PatchOperation] = []
    for party in parties:
        report = _assess.assess_address(
            party.address,
            policy,
            as_of=as_of,
            country_hint=party.address.country,
        )
        findings.extend(
            f.model_copy(
                update={
                    "location": party.location,
                    "party_role": party.role,
                }
            )
            for f in report.findings
        )
        suggestion = _remediate.remediate_address(
            party.address,
            policy,
            country_hint=party.address.country,
            as_of=as_of,
            base_pointer=party.location,
        )
        suggestions.append(suggestion)
        operations.extend(suggestion.operations)

    patched = _apply(xml, operations) if apply else None
    before_compliant = not any(f.rejects_payment for f in findings)
    after_compliant = not any(
        f.rejects_payment for s in suggestions for f in s.residual_findings
    )
    return RemediationResult(
        policy_id=policy.id,
        message_type=message_type,
        assessed_addresses=len(parties),
        findings=tuple(findings),
        suggestions=tuple(suggestions),
        is_compliant_before=before_compliant,
        is_compliant_after=after_compliant,
        patched_xml=patched,
    )


def preview_patch(
    xml: str,
    policy_id: str | None = None,
    *,
    as_of: date | None = None,
    registry: PolicyRegistry = default_registry,
) -> tuple[PatchOperation, ...]:
    """Return the patch operations remediation would apply, without
    applying them (a dry run)."""
    result = remediate_message(
        xml, policy_id, apply=False, as_of=as_of, registry=registry
    )
    return tuple(op for s in result.suggestions for op in s.operations)
