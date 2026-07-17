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

"""Enumerations shared across the domain layer.

These are stable, wire-facing vocabularies: their string values are part
of the public API (they appear in serialized findings, patches, and MCP
tool payloads), so a value's meaning is never repurposed once shipped.
"""

from __future__ import annotations

from enum import StrEnum


class AddressClassification(StrEnum):
    """How an ISO 20022 postal address is shaped, per CBPR+ UG2026.

    - ``STRUCTURED`` — ``TwnNm`` + ``Ctry`` plus other structured detail
      and no ``AdrLine``.
    - ``HYBRID`` — ``TwnNm`` + ``Ctry`` plus 1..2 residual ``AdrLine``.
    - ``UNSTRUCTURED`` — ``AdrLine`` only; rejected from the cliff date.
    """

    STRUCTURED = "structured"
    HYBRID = "hybrid"
    UNSTRUCTURED = "unstructured"


class Severity(StrEnum):
    """Severity of a risk finding, ordered least to most serious."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PartyRole(StrEnum):
    """ISO 20022 party roles that carry a postal address.

    Values are the ISO 20022 XML element local names, so they double as
    the path segment used to locate the party in a message.
    """

    DEBTOR = "Dbtr"
    CREDITOR = "Cdtr"
    DEBTOR_AGENT = "DbtrAgt"
    CREDITOR_AGENT = "CdtrAgt"
    ULTIMATE_DEBTOR = "UltmtDbtr"
    ULTIMATE_CREDITOR = "UltmtCdtr"
    INITIATING_PARTY = "InitgPty"


class MessageType(StrEnum):
    """ISO 20022 message types this package can assess and remediate."""

    PACS_008 = "pacs.008"
    PACS_009 = "pacs.009"
    PAIN_001 = "pain.001"
    CAMT_053 = "camt.053"


class PolicyId(StrEnum):
    """Identifiers for the built-in (open-source) address policies.

    Premium rule packs register their own identifiers dynamically via the
    plugin registry; those are plain strings and are intentionally not
    enumerated here.
    """

    CBPR_2026 = "cbpr-2026"
    SEPA = "sepa"
    HVPS_PLUS = "hvps-plus"
    GENERIC_STRUCTURED = "generic-structured"
