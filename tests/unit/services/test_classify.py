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

"""Tests for the classification use-cases (address + message shape)."""

from __future__ import annotations

from structured_address_fix import services
from structured_address_fix.domain import CanonicalAddress
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
)

_PAIN_NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"


def _cdtr(structured: bool) -> str:
    """Return a Cdtr party block, structured or unstructured."""
    if structured:
        return (
            "<Cdtr><Nm>Cred</Nm><PstlAdr>"
            "<StrtNm>Rue de Rivoli</StrtNm>"
            "<TwnNm>Paris</TwnNm><Ctry>FR</Ctry>"
            "</PstlAdr></Cdtr>"
        )
    return (
        "<Cdtr><Nm>Cred</Nm><PstlAdr>"
        "<AdrLine>Somewhere</AdrLine>"
        "</PstlAdr></Cdtr>"
    )


def _pain001(*creditors_structured: bool) -> str:
    """Wrap a debtor plus N creditor transactions in a pain.001 envelope."""
    txs = "".join(
        f"<CdtTrfTxInf>{_cdtr(structured)}</CdtTrfTxInf>"
        for structured in creditors_structured
    )
    return (
        f'<Document xmlns="{_PAIN_NS}"><CstmrCdtTrfInitn><PmtInf>'
        "<Dbtr><Nm>Deb</Nm><PstlAdr>"
        "<StrtNm>X</StrtNm><TwnNm>London</TwnNm><Ctry>GB</Ctry>"
        "</PstlAdr></Dbtr>"
        f"{txs}"
        "</PmtInf></CstmrCdtTrfInitn></Document>"
    )


def test_classify_structured_address(gb_structured: CanonicalAddress) -> None:
    """A structured address classifies as STRUCTURED."""
    assert (
        services.classify_address(gb_structured)
        is AddressClassification.STRUCTURED
    )


def test_classify_hybrid_address(gb_hybrid: CanonicalAddress) -> None:
    """A town+country address with residual AdrLine is HYBRID."""
    assert services.classify_address(gb_hybrid) is AddressClassification.HYBRID


def test_classify_unstructured_address(
    gb_unstructured: CanonicalAddress,
) -> None:
    """An AdrLine-only address (no town) is UNSTRUCTURED."""
    assert (
        services.classify_address(gb_unstructured)
        is AddressClassification.UNSTRUCTURED
    )


def test_classify_no_country_unstructured(
    no_country_unstructured: CanonicalAddress,
) -> None:
    """An address with no country at all is UNSTRUCTURED."""
    assert (
        services.classify_address(no_country_unstructured)
        is AddressClassification.UNSTRUCTURED
    )


def test_classify_message_maps_each_role(pacs008_xml: str) -> None:
    """Each distinct party role maps to its own classification."""
    message_type, by_role = services.classify_message(pacs008_xml)

    assert message_type is MessageType.PACS_008
    assert by_role == {
        PartyRole.DEBTOR: AddressClassification.STRUCTURED,
        PartyRole.CREDITOR: AddressClassification.UNSTRUCTURED,
        PartyRole.DEBTOR_AGENT: AddressClassification.STRUCTURED,
        PartyRole.CREDITOR_AGENT: AddressClassification.STRUCTURED,
    }


def test_classify_message_keeps_least_compliant_for_repeated_role() -> None:
    """A role appearing more than once keeps its worst classification.

    Three creditors — structured, unstructured, structured — exercise all
    three branches of the reduction: the first seeds the map (``existing is
    None``), the second is strictly worse and replaces it, and the third is
    better and is discarded.
    """
    xml = _pain001(True, False, True)

    message_type, by_role = services.classify_message(xml)

    assert message_type is MessageType.PAIN_001
    assert by_role[PartyRole.DEBTOR] is AddressClassification.STRUCTURED
    assert by_role[PartyRole.CREDITOR] is AddressClassification.UNSTRUCTURED


def test_classify_message_single_structured_role_kept() -> None:
    """A lone structured occurrence of a role is reported as-is."""
    _, by_role = services.classify_message(_pain001(True))

    assert by_role[PartyRole.CREDITOR] is AddressClassification.STRUCTURED
