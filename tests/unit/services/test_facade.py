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

"""Tests for the service facade — every public entry point and branch."""

from __future__ import annotations

from datetime import date

import pytest

from structured_address_fix import services
from structured_address_fix.domain import CanonicalAddress
from structured_address_fix.domain.enums import MessageType
from structured_address_fix.errors import UnknownPolicyError
from structured_address_fix.policies.cbpr_2026 import Cbpr2026Policy
from structured_address_fix.policies.registry import PolicyRegistry
from structured_address_fix.policies.sepa import SepaPolicy

_NS = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"


def _compliant_pacs008() -> str:
    """A four-party pacs.008 whose every address is fully structured."""

    def party(tag: str, agent: bool) -> str:
        adr = (
            "<PstlAdr><StrtNm>Main</StrtNm><BldgNb>1</BldgNb>"
            "<PstCd>0001</PstCd><TwnNm>Town</TwnNm><Ctry>FR</Ctry></PstlAdr>"
        )
        if agent:
            return (
                f"<{tag}><FinInstnId><Nm>{tag}</Nm>{adr}</FinInstnId></{tag}>"
            )
        return f"<{tag}><Nm>{tag}</Nm>{adr}</{tag}>"

    inner = (
        party("Dbtr", False)
        + party("DbtrAgt", True)
        + party("CdtrAgt", True)
        + party("Cdtr", False)
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Document xmlns="{_NS}"><FIToFICstmrCdtTrf><CdtTrfTxInf>'
        f"{inner}"
        f"</CdtTrfTxInf></FIToFICstmrCdtTrf></Document>"
    )


# -- list_policies ----------------------------------------------------------


def test_list_policies_reports_builtins() -> None:
    """The default registry lists the four OSS policies with metadata."""
    infos = services.list_policies()

    by_id = {info.id: info for info in infos}
    assert {"cbpr-2026", "sepa", "hvps-plus", "generic-structured"} <= set(
        by_id
    )
    assert by_id["cbpr-2026"].tier == "oss"
    assert by_id["cbpr-2026"].title


def test_list_policies_honours_custom_registry() -> None:
    """A custom registry lists only its own policies."""
    registry = PolicyRegistry()
    registry.register(SepaPolicy())

    infos = services.list_policies(registry=registry)

    assert [info.id for info in infos] == ["sepa"]


# -- classify (facade delegation) -------------------------------------------


def test_facade_classify_address(gb_hybrid: CanonicalAddress) -> None:
    """``classify_address`` delegates to the classify use-case."""
    assert services.classify_address(gb_hybrid).value == "hybrid"


def test_facade_classify_message(pacs008_xml: str) -> None:
    """``classify_message`` returns the message type and role map."""
    message_type, by_role = services.classify_message(pacs008_xml)

    assert message_type is MessageType.PACS_008
    assert by_role


# -- assess (facade delegation + default resolution) ------------------------


def test_assess_address_default_policy_is_cbpr(
    gb_structured: CanonicalAddress,
) -> None:
    """``policy_id=None`` resolves to the cbpr-2026 default."""
    report = services.assess_address(gb_structured)

    assert report.policy_id == "cbpr-2026"


def test_assess_address_env_override(
    monkeypatch: pytest.MonkeyPatch, gb_structured: CanonicalAddress
) -> None:
    """``SAF_DEFAULT_POLICY`` overrides the default policy resolution."""
    monkeypatch.setenv("SAF_DEFAULT_POLICY", "sepa")

    report = services.assess_address(gb_structured)

    assert report.policy_id == "sepa"


def test_assess_message_via_facade(pacs008_xml: str, post_cliff: date) -> None:
    """``assess_message`` resolves a policy and reports message findings."""
    report = services.assess_message(
        pacs008_xml, "cbpr-2026", as_of=post_cliff
    )

    assert report.message_type is MessageType.PACS_008
    assert report.is_compliant is False


def test_unknown_policy_raises(gb_structured: CanonicalAddress) -> None:
    """An unregistered policy id raises ``UnknownPolicyError``."""
    with pytest.raises(UnknownPolicyError):
        services.assess_address(gb_structured, "does-not-exist")


def test_facade_honours_custom_registry(
    gb_structured: CanonicalAddress,
) -> None:
    """A custom ``registry`` is consulted for policy resolution."""
    registry = PolicyRegistry()
    registry.register(Cbpr2026Policy())

    report = services.assess_address(
        gb_structured, "cbpr-2026", registry=registry
    )
    assert report.policy_id == "cbpr-2026"

    with pytest.raises(UnknownPolicyError):
        services.assess_address(gb_structured, "sepa", registry=registry)


# -- remediate_address ------------------------------------------------------


def test_remediate_address_compliance_flags(
    gb_unstructured: CanonicalAddress, post_cliff: date
) -> None:
    """Remediating an unstructured address flips compliance to True."""
    result = services.remediate_address(
        gb_unstructured, "cbpr-2026", as_of=post_cliff
    )

    assert result.assessed_addresses == 1
    assert result.is_compliant_before is False
    assert result.is_compliant_after is True
    assert len(result.suggestions) == 1


def test_remediate_address_compliant_stays_compliant(
    gb_structured: CanonicalAddress, post_cliff: date
) -> None:
    """A compliant address stays compliant before and after."""
    result = services.remediate_address(
        gb_structured, "cbpr-2026", as_of=post_cliff
    )

    assert result.is_compliant_before is True
    assert result.is_compliant_after is True


# -- remediate_message ------------------------------------------------------


def test_remediate_message_apply_false_has_no_patch(
    pacs008_xml: str, post_cliff: date
) -> None:
    """With ``apply=False`` no patched document is produced."""
    result = services.remediate_message(
        pacs008_xml, "cbpr-2026", apply=False, as_of=post_cliff
    )

    assert result.patched_xml is None
    assert result.assessed_addresses == 4
    assert result.is_compliant_before is False
    assert result.is_compliant_after is True


def test_remediate_message_apply_true_patches(
    pacs008_xml: str, post_cliff: date
) -> None:
    """With ``apply=True`` the patched, re-assessable document is returned."""
    result = services.remediate_message(
        pacs008_xml, "cbpr-2026", apply=True, as_of=post_cliff
    )

    assert result.patched_xml is not None
    reassessed = services.assess_message(
        result.patched_xml, "cbpr-2026", as_of=post_cliff
    )
    assert reassessed.is_compliant is True


def test_remediate_message_compliant_apply_roundtrips() -> None:
    """A compliant message with no ops round-trips unchanged under apply."""
    xml = _compliant_pacs008()

    result = services.remediate_message(
        xml, "cbpr-2026", apply=True, as_of=date(2026, 12, 1)
    )

    assert result.is_compliant_before is True
    assert result.is_compliant_after is True
    assert all(s.operations == () for s in result.suggestions)
    # No operations -> the apply seam returns the input verbatim.
    assert result.patched_xml == xml


# -- preview_patch ----------------------------------------------------------


def test_preview_patch_returns_operations(
    pacs008_xml: str, post_cliff: date
) -> None:
    """``preview_patch`` returns the operations without applying them."""
    ops = services.preview_patch(pacs008_xml, "cbpr-2026", as_of=post_cliff)

    # The single unstructured creditor is driven to structured form:
    # SET PstCd/TwnNm/CtrySubDvsn/StrtNm plus one REMOVE per AdrLine.
    assert len(ops) == 6
    assert all(op.confidence == 0.9 for op in ops)


def test_preview_patch_compliant_message_is_empty() -> None:
    """A compliant message previews no operations."""
    ops = services.preview_patch(
        _compliant_pacs008(), "cbpr-2026", as_of=date(2026, 12, 1)
    )

    assert ops == ()
