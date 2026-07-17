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

"""The party entity: a named actor in a message with a postal address.

An :class:`AddressedParty` binds a :class:`CanonicalAddress` to the role
it plays in a message and to a JSON pointer locating its ``PstlAdr``
element, so findings and patches can be threaded back to the exact node.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from structured_address_fix.domain.address import CanonicalAddress
from structured_address_fix.domain.enums import PartyRole


class AddressedParty(BaseModel):
    """A party in an ISO 20022 message that carries a postal address."""

    model_config = ConfigDict(frozen=True)

    role: PartyRole
    name: str | None = None
    address: CanonicalAddress
    location: str
    """JSON pointer to this party's ``PstlAdr`` element in the message."""
