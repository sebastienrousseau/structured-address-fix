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

"""Tests for applying remediation patches back onto ISO 20022 messages."""

from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import canonicalize

import pytest

from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.adapters.xml_writer import (
    _prolog,
    apply_operations,
)
from structured_address_fix.domain.findings import FindingCode
from structured_address_fix.domain.remediation import PatchOp, PatchOperation
from structured_address_fix.errors import (
    MalformedXMLError,
    PatchApplicationError,
)

_FIXTURE = (
    Path(__file__).parents[3]
    / "tests"
    / "fixtures"
    / "messages"
    / "pacs008_three_party.xml"
)

_NS = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"
_PSTLADR = "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/Dbtr/PstlAdr"


def _doc(pstladr_inner: str) -> str:
    """Wrap ``pstladr_inner`` in a single-debtor pacs.008 document."""
    return (
        f'<Document xmlns="{_NS}"><FIToFICstmrCdtTrf><CdtTrfTxInf>'
        f"<Dbtr><PstlAdr>{pstladr_inner}</PstlAdr></Dbtr>"
        f"</CdtTrfTxInf></FIToFICstmrCdtTrf></Document>"
    )


def _set(path: str, value: str | None) -> PatchOperation:
    """Build a SET operation for brevity."""
    return PatchOperation(
        op=PatchOp.SET,
        path=path,
        value=value,
        reason_code=FindingCode.MISSING_TOWN,
    )


def test_empty_operations_round_trip() -> None:
    """No operations round-trips the document (whitespace aside)."""
    xml = _FIXTURE.read_text(encoding="utf-8")
    out = apply_operations(xml, [])
    assert canonicalize(xml_data=xml, strip_text=True) == canonicalize(
        xml_data=out, strip_text=True
    )
    assert out.startswith("<?xml")


def test_set_replaces_existing_element() -> None:
    """SET on an existing element replaces its text."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    out = apply_operations(xml, [_set(f"{_PSTLADR}/TwnNm", "Paris")])
    _, parties = read_addresses(out)
    assert parties[0].address.town_name == "Paris"


def test_set_creates_element_before_adrline() -> None:
    """A new structured element is inserted ahead of AdrLine."""
    xml = _doc(
        "<TwnNm>London</TwnNm><Ctry>GB</Ctry><AdrLine>42 High St</AdrLine>"
    )
    out = apply_operations(xml, [_set(f"{_PSTLADR}/StrtNm", "High Street")])
    assert out.index("StrtNm") < out.index("AdrLine")
    _, parties = read_addresses(out)
    assert parties[0].address.street_name == "High Street"


def test_set_creates_element_without_adrline() -> None:
    """A new element with no AdrLine present is appended."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    out = apply_operations(xml, [_set(f"{_PSTLADR}/StrtNm", "High Street")])
    _, parties = read_addresses(out)
    assert parties[0].address.street_name == "High Street"


def test_set_appends_new_adrline_by_index() -> None:
    """SET on an out-of-range AdrLine index appends a new line."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry><AdrLine>Line 1</AdrLine>")
    out = apply_operations(xml, [_set(f"{_PSTLADR}/AdrLine/1", "Line 2")])
    _, parties = read_addresses(out)
    assert parties[0].address.address_lines == ("Line 1", "Line 2")


def test_set_on_document_without_namespace() -> None:
    """SET works on an unqualified document (no namespace to register)."""
    xml = "<Document><A><PstlAdr><TwnNm>X</TwnNm></PstlAdr></A></Document>"
    out = apply_operations(
        xml,
        [
            _set("/Document/A/PstlAdr/TwnNm", "Y"),
            _set("/Document/A/PstlAdr/Ctry", "GB"),
        ],
    )
    assert "<TwnNm>Y</TwnNm>" in out
    assert "<Ctry>GB</Ctry>" in out
    assert not out.startswith("<?xml")


def test_remove_existing_element() -> None:
    """REMOVE drops the addressed element."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    op = PatchOperation(
        op=PatchOp.REMOVE,
        path=f"{_PSTLADR}/TwnNm",
        reason_code=FindingCode.HYBRID_RESIDUAL_ADRLINE,
    )
    out = apply_operations(xml, [op])
    _, parties = read_addresses(out)
    assert parties[0].address.town_name is None


def test_remove_absent_element_is_noop() -> None:
    """REMOVE of an absent element leaves the document intact."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    op = PatchOperation(
        op=PatchOp.REMOVE,
        path=f"{_PSTLADR}/StrtNm",
        reason_code=FindingCode.HYBRID_RESIDUAL_ADRLINE,
    )
    out = apply_operations(xml, [op])
    _, parties = read_addresses(out)
    assert parties[0].address.town_name == "London"


def test_move_transplants_element_text() -> None:
    """MOVE removes the source and recreates it at the destination."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry><PstBx>PO 1</PstBx>")
    op = PatchOperation(
        op=PatchOp.MOVE,
        path=f"{_PSTLADR}/Dept",
        from_=f"{_PSTLADR}/PstBx",
        reason_code=FindingCode.STRUCTURED_FIELD_OVERFLOW,
    )
    out = apply_operations(xml, [op])
    _, parties = read_addresses(out)
    assert parties[0].address.post_box is None
    assert parties[0].address.department == "PO 1"


def test_move_without_from_raises() -> None:
    """A MOVE with no 'from' pointer is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    op = PatchOperation(
        op=PatchOp.MOVE,
        path=f"{_PSTLADR}/Dept",
        reason_code=FindingCode.STRUCTURED_FIELD_OVERFLOW,
    )
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [op])


def test_move_missing_source_raises() -> None:
    """A MOVE whose source element is absent is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    op = PatchOperation(
        op=PatchOp.MOVE,
        path=f"{_PSTLADR}/Dept",
        from_=f"{_PSTLADR}/PstBx",
        reason_code=FindingCode.STRUCTURED_FIELD_OVERFLOW,
    )
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [op])


def test_set_missing_parent_raises() -> None:
    """SET whose parent PstlAdr is missing is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [_set("/Document/Nope/PstlAdr/TwnNm", "X")])


def test_remove_missing_parent_raises() -> None:
    """REMOVE whose parent is missing is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    op = PatchOperation(
        op=PatchOp.REMOVE,
        path="/Document/Nope/PstlAdr/TwnNm",
        reason_code=FindingCode.HYBRID_RESIDUAL_ADRLINE,
    )
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [op])


def test_empty_pointer_raises() -> None:
    """An empty pointer is rejected as a patch failure."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [_set("/", "X")])


def test_leading_index_pointer_raises() -> None:
    """A pointer starting with an index segment is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [_set("/0/TwnNm", "X")])


def test_single_segment_pointer_raises() -> None:
    """A single-segment pointer has no parent to resolve."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [_set("/TwnNm", "X")])


def test_wrong_root_pointer_raises() -> None:
    """A pointer whose root name mismatches the document is rejected."""
    xml = _doc("<TwnNm>London</TwnNm><Ctry>GB</Ctry>")
    with pytest.raises(PatchApplicationError):
        apply_operations(xml, [_set("/Wrong/PstlAdr/TwnNm", "X")])


def test_malformed_xml_raises() -> None:
    """Non-well-formed XML raises MalformedXMLError."""
    with pytest.raises(MalformedXMLError):
        apply_operations("<Document><unclosed>", [])


def test_prolog_variants() -> None:
    """_prolog returns the declaration only when one is present and closed."""
    assert _prolog('<?xml version="1.0"?>\n<a/>') == '<?xml version="1.0"?>\n'
    assert _prolog("<a/>") == ""
    assert _prolog("<?xml unterminated") == ""
