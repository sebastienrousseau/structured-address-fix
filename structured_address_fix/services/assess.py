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

"""Assessment use-cases: score an address or a whole message against a
policy and return an explainable :class:`ValidationReport`."""

from __future__ import annotations

from datetime import date

from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import MessageType
from structured_address_fix.domain.findings import RiskFinding
from structured_address_fix.domain.party import AddressedParty
from structured_address_fix.domain.result import ValidationReport
from structured_address_fix.policies.base import AddressPolicy, PolicyContext


def _context(
    as_of: date | None,
    country_hint: str | None = None,
    message_type: MessageType | None = None,
) -> PolicyContext:
    """Build a :class:`PolicyContext`, honoring an explicit ``as_of``."""
    if as_of is None:
        return PolicyContext(
            country_hint=country_hint, message_type=message_type
        )
    return PolicyContext(
        as_of=as_of, country_hint=country_hint, message_type=message_type
    )


def _is_compliant(findings: tuple[RiskFinding, ...]) -> bool:
    """Return ``True`` when no finding would reject the payment."""
    return not any(f.rejects_payment for f in findings)


def _relocate(
    findings: list[RiskFinding], party: AddressedParty
) -> list[RiskFinding]:
    """Re-anchor bare findings onto a party's message location + role."""
    return [
        f.model_copy(
            update={"location": party.location, "party_role": party.role}
        )
        for f in findings
    ]


def assess_address(
    address: CanonicalAddress,
    policy: AddressPolicy,
    *,
    as_of: date | None = None,
    country_hint: str | None = None,
) -> ValidationReport:
    """Assess a single address against ``policy``."""
    ctx = _context(as_of, country_hint=country_hint)
    findings = tuple(policy.assess(address, ctx))
    return ValidationReport(
        policy_id=policy.id,
        assessed_addresses=1,
        findings=findings,
        is_compliant=_is_compliant(findings),
    )


def assess_message(
    xml: str,
    policy: AddressPolicy,
    *,
    as_of: date | None = None,
) -> ValidationReport:
    """Assess every addressed party in an ISO 20022 message."""
    message_type, parties = read_addresses(xml)
    findings: list[RiskFinding] = []
    for party in parties:
        ctx = _context(
            as_of,
            country_hint=party.address.country,
            message_type=message_type,
        )
        findings.extend(_relocate(policy.assess(party.address, ctx), party))
    findings_tuple = tuple(findings)
    return ValidationReport(
        policy_id=policy.id,
        message_type=message_type,
        assessed_addresses=len(parties),
        findings=findings_tuple,
        is_compliant=_is_compliant(findings_tuple),
    )
