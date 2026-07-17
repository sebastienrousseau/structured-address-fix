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

"""Classification use-cases: how an address (or every address in a
message) is shaped, independent of any policy."""

from __future__ import annotations

from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
)


def classify_address(address: CanonicalAddress) -> AddressClassification:
    """Return the CBPR+ classification of a single address."""
    return address.classification


def classify_message(
    xml: str,
) -> tuple[MessageType, dict[PartyRole, AddressClassification]]:
    """Classify every addressed party in an ISO 20022 message.

    Returns the detected message type and a mapping of each party role to
    its address classification. When a role appears more than once, the
    least-compliant classification for that role is reported.
    """
    message_type, parties = read_addresses(xml)
    order = {
        AddressClassification.STRUCTURED: 0,
        AddressClassification.HYBRID: 1,
        AddressClassification.UNSTRUCTURED: 2,
    }
    result: dict[PartyRole, AddressClassification] = {}
    for party in parties:
        current = party.address.classification
        existing = result.get(party.role)
        if existing is None or order[current] > order[existing]:
            result[party.role] = current
    return message_type, result
