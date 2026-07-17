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

"""ISO 20022 ``PstlAdr`` location tables.

For each supported :class:`~structured_address_fix.domain.enums.MessageType`
this module maps every party role that carries a postal address to the
slash-separated element path (by local name, relative to the ``Document``
root) where that party's ``PstlAdr`` element lives. Paths are matched on
local names so they are namespace-agnostic; the concrete namespace and the
message type are recovered from the ``Document`` namespace URI by
:func:`detect_message_type`.

Only pacs.008 and pain.001 are modelled here. The other members of
:class:`MessageType` are recognised by :func:`detect_message_type` but have
no path table yet, so :func:`paths_for` raises for them.
"""

from __future__ import annotations

from collections.abc import Mapping

from structured_address_fix.domain.enums import MessageType, PartyRole
from structured_address_fix.errors import UnsupportedMessageTypeError

# pacs.008 FI-to-FI customer credit transfer. Debtor/creditor addresses
# live on the transaction; agent addresses live under FinInstnId.
_PACS_008_PATHS: Mapping[PartyRole, str] = {
    PartyRole.DEBTOR: "FIToFICstmrCdtTrf/CdtTrfTxInf/Dbtr/PstlAdr",
    PartyRole.CREDITOR: "FIToFICstmrCdtTrf/CdtTrfTxInf/Cdtr/PstlAdr",
    PartyRole.DEBTOR_AGENT: (
        "FIToFICstmrCdtTrf/CdtTrfTxInf/DbtrAgt/FinInstnId/PstlAdr"
    ),
    PartyRole.CREDITOR_AGENT: (
        "FIToFICstmrCdtTrf/CdtTrfTxInf/CdtrAgt/FinInstnId/PstlAdr"
    ),
}

# pain.001 customer credit transfer initiation. The debtor address sits at
# the PmtInf level; each creditor address sits on its transaction.
_PAIN_001_PATHS: Mapping[PartyRole, str] = {
    PartyRole.DEBTOR: "CstmrCdtTrfInitn/PmtInf/Dbtr/PstlAdr",
    PartyRole.CREDITOR: ("CstmrCdtTrfInitn/PmtInf/CdtTrfTxInf/Cdtr/PstlAdr"),
}

_PATH_TABLES: Mapping[MessageType, Mapping[PartyRole, str]] = {
    MessageType.PACS_008: _PACS_008_PATHS,
    MessageType.PAIN_001: _PAIN_001_PATHS,
}


def paths_for(message_type: MessageType) -> Mapping[PartyRole, str]:
    """Return the ``PartyRole`` -> ``PstlAdr`` path table for a message.

    Args:
        message_type: The ISO 20022 message type.

    Returns:
        A mapping of each addressed party role to the slash-separated
        local-name path of its ``PstlAdr`` element, relative to the
        ``Document`` root.

    Raises:
        UnsupportedMessageTypeError: if no path table is modelled for
            ``message_type`` (e.g. pacs.009, camt.053).
    """
    table = _PATH_TABLES.get(message_type)
    if table is None:
        raise UnsupportedMessageTypeError(
            f"no PstlAdr path table for message type {message_type.value!r}",
            context={"message_type": message_type.value},
        )
    return table


def detect_message_type(root_tag_or_namespace: str) -> MessageType:
    """Identify the ISO 20022 message type from a namespace or root tag.

    Accepts either a bare namespace URI (e.g.
    ``"urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"``) or a Clark-notation
    root tag (e.g. ``"{urn:...:pacs.008.001.08}Document"``). The message type
    is recognised by the ``pacs.008`` / ``pain.001`` / ``pacs.009`` /
    ``camt.053`` document-type token in the string.

    Args:
        root_tag_or_namespace: The namespace URI or Clark-notation tag.

    Returns:
        The matching :class:`MessageType`.

    Raises:
        UnsupportedMessageTypeError: if no known message-type token is
            present.
    """
    for message_type in MessageType:
        if message_type.value in root_tag_or_namespace:
            return message_type
    raise UnsupportedMessageTypeError(
        "unrecognised ISO 20022 document type; expected one of "
        f"{[m.value for m in MessageType]}",
        context={"namespace": root_tag_or_namespace},
    )
