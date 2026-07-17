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

"""Read addressed parties out of an ISO 20022 message.

:func:`read_addresses` parses the document with ``defusedxml`` (XXE-safe),
identifies the message type from the ``Document`` namespace, walks to every
``PstlAdr`` element named in the :mod:`xpath` table, and returns one
:class:`~structured_address_fix.domain.party.AddressedParty` per located
address. Each party carries a JSON pointer to its ``PstlAdr`` element so
findings and patches can be threaded back to the exact node.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from xml.etree.ElementTree import Element, ParseError

from defusedxml.ElementTree import fromstring
from pydantic import ValidationError

from structured_address_fix.adapters import xpath
from structured_address_fix.adapters._xmlutil import (
    children_named,
    local_name,
)
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import MessageType
from structured_address_fix.domain.party import AddressedParty
from structured_address_fix.errors import (
    InvalidAddressError,
    MalformedXMLError,
)

# ISO 20022 ``PstlAdr`` child element local names -> CanonicalAddress
# fields. ``AdrLine`` is handled separately as a repeating element.
_ELEMENT_TO_FIELD: dict[str, str] = {
    "Dept": "department",
    "SubDept": "sub_department",
    "StrtNm": "street_name",
    "BldgNb": "building_number",
    "BldgNm": "building_name",
    "Flr": "floor",
    "PstBx": "post_box",
    "Room": "room",
    "PstCd": "post_code",
    "TwnNm": "town_name",
    "TwnLctnNm": "town_location_name",
    "DstrctNm": "district_name",
    "CtrySubDvsn": "country_sub_division",
    "Ctry": "country",
}


def read_addresses(
    xml: str,
) -> tuple[MessageType, tuple[AddressedParty, ...]]:
    """Parse ``xml`` and return its message type and addressed parties.

    Args:
        xml: The raw ISO 20022 XML document.

    Returns:
        A ``(message_type, parties)`` tuple. ``parties`` holds one
        :class:`AddressedParty` per ``PstlAdr`` element found, ordered by
        party role then document position.

    Raises:
        MalformedXMLError: if ``xml`` is not well-formed XML.
        UnsupportedMessageTypeError: if the ``Document`` namespace is not a
            recognised message type, or has no modelled path table.
        InvalidAddressError: if a located ``PstlAdr`` violates a canonical
            address invariant (e.g. an over-length element).
    """
    try:
        root: Element = fromstring(xml)
    except ParseError as exc:
        raise MalformedXMLError(
            f"could not parse XML: {exc}", context={"detail": str(exc)}
        ) from exc

    message_type = xpath.detect_message_type(root.tag)
    table = xpath.paths_for(message_type)

    root_prefix = f"/{local_name(root.tag)}"
    parties: list[AddressedParty] = []

    for role, path in table.items():
        segments = path.split("/")
        for pstladr, pointer, parent in _walk(
            root, segments, root_prefix, None
        ):
            address = _build_address(pstladr, pointer)
            parties.append(
                AddressedParty(
                    role=role,
                    name=_party_name(parent),
                    address=address,
                    location=pointer,
                )
            )

    return message_type, tuple(parties)


def _walk(
    element: Element,
    segments: list[str],
    prefix: str,
    parent: Element | None,
) -> Iterator[tuple[Element, str, Element | None]]:
    """Yield ``(target, pointer, parent)`` for each element matching a path.

    Args:
        element: The current element being descended.
        segments: Remaining local-name path segments.
        prefix: The JSON pointer accumulated so far.
        parent: The parent of ``element`` (``None`` at the root).

    Yields:
        A ``(target, pointer, parent)`` tuple per matched leaf, where an
        occurrence index is appended to the pointer only for repeated
        same-named siblings.
    """
    if not segments:
        yield element, prefix, parent
        return

    name = segments[0]
    rest = segments[1:]
    matches = children_named(element, name)
    multi = len(matches) > 1
    for idx, child in enumerate(matches):
        child_prefix = f"{prefix}/{name}"
        if multi:
            child_prefix = f"{child_prefix}/{idx}"
        yield from _walk(child, rest, child_prefix, element)


def _build_address(pstladr: Element, pointer: str) -> CanonicalAddress:
    """Build a :class:`CanonicalAddress` from a ``PstlAdr`` element.

    Args:
        pstladr: The ``PstlAdr`` element.
        pointer: The JSON pointer to ``pstladr`` (used for error context).

    Returns:
        The canonical address parsed from the element's children.

    Raises:
        InvalidAddressError: if the parsed values violate a canonical
            address invariant.
    """
    fields: dict[str, Any] = {}
    address_lines: list[str] = []

    for child in pstladr:
        tag = local_name(child.tag)
        text = (child.text or "").strip()
        if not text:
            continue
        if tag == "AdrLine":
            address_lines.append(text)
        else:
            field = _ELEMENT_TO_FIELD.get(tag)
            if field is not None:
                fields[field] = text

    try:
        return CanonicalAddress(address_lines=tuple(address_lines), **fields)
    except ValidationError as exc:
        raise InvalidAddressError(
            f"invalid PstlAdr at {pointer}: {exc}",
            context={"location": pointer},
        ) from exc


def _party_name(parent: Element | None) -> str | None:
    """Return the ``Nm`` sibling text of a ``PstlAdr``'s parent element.

    Args:
        parent: The element enclosing the ``PstlAdr`` (a party or
            ``FinInstnId`` element), or ``None``.

    Returns:
        The stripped ``Nm`` text, or ``None`` if absent or empty.
    """
    if parent is None:
        return None
    for child in children_named(parent, "Nm"):
        text = (child.text or "").strip()
        if text:
            return text
    return None
