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

"""Tests for the ISO 20022 PstlAdr path tables and type detection."""

from __future__ import annotations

import pytest

from structured_address_fix.adapters.xpath import (
    detect_message_type,
    paths_for,
)
from structured_address_fix.domain.enums import MessageType, PartyRole
from structured_address_fix.errors import UnsupportedMessageTypeError


def test_pacs008_paths_cover_four_parties() -> None:
    """pacs.008 maps debtor, creditor and both agents."""
    paths = paths_for(MessageType.PACS_008)
    assert set(paths) == {
        PartyRole.DEBTOR,
        PartyRole.CREDITOR,
        PartyRole.DEBTOR_AGENT,
        PartyRole.CREDITOR_AGENT,
    }
    assert paths[PartyRole.DEBTOR].endswith("Dbtr/PstlAdr")
    assert "FinInstnId" in paths[PartyRole.DEBTOR_AGENT]


def test_pain001_paths_cover_debtor_and_creditor() -> None:
    """pain.001 maps the PmtInf-level debtor and per-tx creditor."""
    paths = paths_for(MessageType.PAIN_001)
    assert set(paths) == {PartyRole.DEBTOR, PartyRole.CREDITOR}
    assert paths[PartyRole.DEBTOR].startswith("CstmrCdtTrfInitn/PmtInf")


def test_paths_for_unmodelled_type_raises() -> None:
    """A recognised but unmodelled message type has no path table."""
    with pytest.raises(UnsupportedMessageTypeError):
        paths_for(MessageType.PACS_009)
    with pytest.raises(UnsupportedMessageTypeError):
        paths_for(MessageType.CAMT_053)


def test_detect_from_clark_tag() -> None:
    """The message type is detected from a Clark-notation root tag."""
    tag = "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}Document"
    assert detect_message_type(tag) is MessageType.PACS_008


def test_detect_from_namespace() -> None:
    """The message type is detected from a bare namespace URI."""
    ns = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"
    assert detect_message_type(ns) is MessageType.PAIN_001


def test_detect_pacs009_and_camt053() -> None:
    """pacs.009 and camt.053 tokens are recognised."""
    assert detect_message_type("...:pacs.009.001.08") is MessageType.PACS_009
    assert detect_message_type("...:camt.053.001.08") is MessageType.CAMT_053


def test_detect_unknown_raises() -> None:
    """An unrecognised document type raises."""
    with pytest.raises(UnsupportedMessageTypeError):
        detect_message_type("urn:example:not-a-message")
