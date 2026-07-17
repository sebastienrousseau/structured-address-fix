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

"""Tests for reading addressed parties out of ISO 20022 messages."""

from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement

import pytest

from structured_address_fix.adapters.xml_reader import (
    _party_name,
    read_addresses,
)
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
)
from structured_address_fix.errors import (
    InvalidAddressError,
    MalformedXMLError,
    UnsupportedMessageTypeError,
)

_FIXTURE = (
    Path(__file__).parents[3]
    / "tests"
    / "fixtures"
    / "messages"
    / "pacs008_three_party.xml"
)

_NS = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"


def _pacs008(inner: str) -> str:
    """Wrap ``inner`` transaction XML in a pacs.008 Document envelope."""
    return (
        f'<Document xmlns="{_NS}"><FIToFICstmrCdtTrf>'
        f"{inner}"
        f"</FIToFICstmrCdtTrf></Document>"
    )


def test_reads_all_parties_from_fixture() -> None:
    """The 4-party fixture yields one party per PstlAdr in role order."""
    xml = _FIXTURE.read_text(encoding="utf-8")
    message_type, parties = read_addresses(xml)

    assert message_type is MessageType.PACS_008
    roles = [p.role for p in parties]
    assert roles == [
        PartyRole.DEBTOR,
        PartyRole.CREDITOR,
        PartyRole.DEBTOR_AGENT,
        PartyRole.CREDITOR_AGENT,
    ]


def test_party_fields_and_pointer() -> None:
    """A structured debtor is parsed with name, address and pointer."""
    xml = _FIXTURE.read_text(encoding="utf-8")
    _, parties = read_addresses(xml)
    debtor = next(p for p in parties if p.role is PartyRole.DEBTOR)

    assert debtor.name == "Acme Debtor Ltd"
    assert debtor.address.town_name == "London"
    assert debtor.address.country == "GB"
    assert debtor.address.building_number == "42"
    assert debtor.address.classification is AddressClassification.STRUCTURED
    assert (
        debtor.location
        == "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/Dbtr/PstlAdr"
    )


def test_agent_name_from_fininstnid() -> None:
    """An agent's name is read from FinInstnId/Nm."""
    xml = _FIXTURE.read_text(encoding="utf-8")
    _, parties = read_addresses(xml)
    agent = next(p for p in parties if p.role is PartyRole.DEBTOR_AGENT)
    assert agent.name == "Debtor Bank"
    assert "FinInstnId/PstlAdr" in agent.location


def test_adr_line_only_is_unstructured() -> None:
    """A creditor with AdrLine only classifies as unstructured."""
    xml = _FIXTURE.read_text(encoding="utf-8")
    _, parties = read_addresses(xml)
    creditor = next(p for p in parties if p.role is PartyRole.CREDITOR)
    assert creditor.address.address_lines == (
        "1 Infinite Loop",
        "Cupertino CA 95014",
    )
    assert (
        creditor.address.classification is AddressClassification.UNSTRUCTURED
    )


def test_multiple_transactions_get_indexed_pointers() -> None:
    """Repeated CdtTrfTxInf elements produce indexed pointers."""
    tx = (
        "<CdtTrfTxInf><Dbtr><Nm>D{n}</Nm>"
        "<PstlAdr><TwnNm>Town{n}</TwnNm><Ctry>GB</Ctry>"
        "<StrtNm>S{n}</StrtNm></PstlAdr></Dbtr></CdtTrfTxInf>"
    )
    xml = _pacs008(tx.format(n=0) + tx.format(n=1))
    _, parties = read_addresses(xml)

    debtors = [p for p in parties if p.role is PartyRole.DEBTOR]
    assert len(debtors) == 2
    assert (
        debtors[0].location
        == "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/0/Dbtr/PstlAdr"
    )
    assert (
        debtors[1].location
        == "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/1/Dbtr/PstlAdr"
    )
    assert debtors[1].address.town_name == "Town1"


def test_missing_pstladr_yields_no_party() -> None:
    """A party element with no PstlAdr contributes no addressed party."""
    xml = _pacs008(
        "<CdtTrfTxInf><Dbtr><Nm>No Address</Nm></Dbtr></CdtTrfTxInf>"
    )
    _, parties = read_addresses(xml)
    assert parties == ()


def test_unknown_child_elements_skipped() -> None:
    """Unrecognised and empty PstlAdr children are ignored."""
    xml = _pacs008(
        "<CdtTrfTxInf><Dbtr><PstlAdr>"
        "<TwnNm>London</TwnNm><Ctry>GB</Ctry>"
        "<StrtNm>High St</StrtNm>"
        "<Unknown>ignored</Unknown><PstCd>  </PstCd>"
        "</PstlAdr></Dbtr></CdtTrfTxInf>"
    )
    _, parties = read_addresses(xml)
    address = parties[0].address
    assert address.town_name == "London"
    assert address.post_code is None


def test_malformed_xml_raises() -> None:
    """Non-well-formed XML raises MalformedXMLError."""
    with pytest.raises(MalformedXMLError):
        read_addresses("<Document><unclosed>")


def test_unknown_namespace_raises() -> None:
    """A non-ISO namespace raises UnsupportedMessageTypeError."""
    with pytest.raises(UnsupportedMessageTypeError):
        read_addresses('<Document xmlns="urn:example:foo"><X/></Document>')


def test_unmodelled_message_type_raises() -> None:
    """A recognised but unmodelled message type raises."""
    ns = "urn:iso:std:iso:20022:tech:xsd:pacs.009.001.08"
    with pytest.raises(UnsupportedMessageTypeError):
        read_addresses(f'<Document xmlns="{ns}"><X/></Document>')


def test_invalid_address_raises() -> None:
    """A PstlAdr breaking a canonical invariant raises InvalidAddressError."""
    xml = _pacs008(
        "<CdtTrfTxInf><Dbtr><PstlAdr>"
        "<TwnNm>London</TwnNm><Ctry>USA</Ctry>"
        "</PstlAdr></Dbtr></CdtTrfTxInf>"
    )
    with pytest.raises(InvalidAddressError):
        read_addresses(xml)


def test_party_name_helper_edge_cases() -> None:
    """_party_name handles a missing parent, absent Nm and empty Nm."""
    assert _party_name(None) is None

    parent = Element("Dbtr")
    assert _party_name(parent) is None

    empty = Element("Dbtr")
    SubElement(empty, "Nm").text = "   "
    assert _party_name(empty) is None

    named = Element("Dbtr")
    SubElement(named, "Nm").text = "Acme"
    assert _party_name(named) == "Acme"
