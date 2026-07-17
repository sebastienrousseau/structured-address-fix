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

"""Tests for the assessment use-cases and their private helpers."""

from __future__ import annotations

from datetime import date

from structured_address_fix import services
from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.domain import CanonicalAddress
from structured_address_fix.domain.enums import MessageType, PartyRole
from structured_address_fix.policies.registry import default_registry
from structured_address_fix.services.assess import (
    _context,
    _is_compliant,
    _relocate,
    assess_address,
    assess_message,
)

_CBPR = default_registry.get("cbpr-2026")


def test_assess_compliant_address_has_no_findings(
    gb_structured: CanonicalAddress, post_cliff: date
) -> None:
    """A fully structured address is compliant with zero findings."""
    report = services.assess_address(
        gb_structured, "cbpr-2026", as_of=post_cliff
    )

    assert report.is_compliant is True
    assert report.findings == ()
    assert report.assessed_addresses == 1
    assert report.policy_id == "cbpr-2026"


def test_assess_unstructured_address_rejects(
    gb_unstructured: CanonicalAddress, post_cliff: date
) -> None:
    """An unstructured address raises rejecting findings and fails."""
    report = services.assess_address(
        gb_unstructured, "cbpr-2026", as_of=post_cliff
    )

    assert report.is_compliant is False
    assert any(f.rejects_payment for f in report.findings)


def test_assess_wording_differs_across_the_cliff(
    gb_unstructured: CanonicalAddress, pre_cliff: date, post_cliff: date
) -> None:
    """The cliff phrase changes on either side of the deadline."""
    before = services.assess_address(
        gb_unstructured, "cbpr-2026", as_of=pre_cliff
    )
    after = services.assess_address(
        gb_unstructured, "cbpr-2026", as_of=post_cliff
    )

    before_msg = " ".join(f.message for f in before.findings)
    after_msg = " ".join(f.message for f in after.findings)
    assert "in force from" in before_msg
    assert "since" in after_msg


def test_assess_address_accepts_country_hint(
    no_country_unstructured: CanonicalAddress, post_cliff: date
) -> None:
    """The ``country_hint`` parameter is accepted and assessment runs."""
    report = services.assess_address(
        no_country_unstructured,
        "cbpr-2026",
        as_of=post_cliff,
        country_hint="US",
    )

    assert report.is_compliant is False


def test_assess_address_default_as_of_is_today(
    gb_structured: CanonicalAddress,
) -> None:
    """With no ``as_of`` the default (today) is used and assessment runs."""
    report = services.assess_address(gb_structured, "cbpr-2026")

    assert report.is_compliant is True


def test_assess_message_relocates_findings(pacs008_xml: str) -> None:
    """Message findings carry the party's JSON pointer and role."""
    report = services.assess_message(pacs008_xml, "cbpr-2026")

    assert report.message_type is MessageType.PACS_008
    assert report.assessed_addresses == 4
    assert report.findings, "the unstructured creditor must raise findings"
    for finding in report.findings:
        assert finding.location != "/"
        assert finding.party_role is not None
    creditor_findings = [
        f for f in report.findings if f.party_role is PartyRole.CREDITOR
    ]
    assert creditor_findings
    assert all("/Cdtr/PstlAdr" in f.location for f in creditor_findings)


def test_context_default_branch_uses_today() -> None:
    """``_context(None)`` builds a context defaulting ``as_of`` to today."""
    ctx = _context(None)

    assert ctx.as_of == date.today()
    assert ctx.country_hint is None
    assert ctx.message_type is None


def test_context_explicit_branch_honours_as_of() -> None:
    """``_context`` with an explicit date pins ``as_of`` and passes hints."""
    ctx = _context(
        date(2026, 12, 1),
        country_hint="GB",
        message_type=MessageType.PACS_008,
    )

    assert ctx.as_of == date(2026, 12, 1)
    assert ctx.country_hint == "GB"
    assert ctx.message_type is MessageType.PACS_008


def test_is_compliant_helper() -> None:
    """``_is_compliant`` is False iff any finding rejects the payment."""
    assert _is_compliant(()) is True

    report = assess_address(
        CanonicalAddress(address_lines=("nowhere",)),
        _CBPR,
        as_of=date(2026, 12, 1),
    )
    assert _is_compliant(report.findings) is False


def test_relocate_helper_reanchors_findings(pacs008_xml: str) -> None:
    """``_relocate`` stamps a party's location and role onto findings."""
    _, parties = read_addresses(pacs008_xml)
    creditor = next(p for p in parties if p.role is PartyRole.CREDITOR)
    bare = _CBPR.assess(creditor.address, _context(date(2026, 12, 1)))
    assert bare, "the unstructured creditor must raise bare findings"
    assert all(f.location == "/" for f in bare)

    relocated = _relocate(bare, creditor)

    assert all(f.location == creditor.location for f in relocated)
    assert all(f.party_role is PartyRole.CREDITOR for f in relocated)


def test_assess_message_direct_helper(pacs008_xml: str) -> None:
    """The low-level ``assess_message`` returns a located report."""
    report = assess_message(pacs008_xml, _CBPR, as_of=date(2026, 12, 1))

    assert report.message_type is MessageType.PACS_008
    assert report.is_compliant is False
