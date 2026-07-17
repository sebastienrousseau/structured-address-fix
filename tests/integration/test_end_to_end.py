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

"""End-to-end assess -> remediate -> re-assess flows over a real message."""

from __future__ import annotations

from datetime import date

import pytest

from structured_address_fix import services
from structured_address_fix.domain.enums import (
    AddressClassification,
    MessageType,
    PartyRole,
)


@pytest.mark.parametrize("policy_id", ["cbpr-2026", "sepa"])
def test_assess_remediate_reassess_is_compliant(
    pacs008_xml: str, post_cliff: date, policy_id: str
) -> None:
    """A message can be assessed, remediated, and re-assessed compliant.

    The remediated document must remain valid, parseable ISO 20022 — proven
    by re-reading it through :func:`services.classify_message` and
    :func:`services.assess_message`.
    """
    before = services.assess_message(pacs008_xml, policy_id, as_of=post_cliff)
    assert before.message_type is MessageType.PACS_008

    result = services.remediate_message(
        pacs008_xml, policy_id, apply=True, as_of=post_cliff
    )
    assert result.patched_xml is not None
    assert result.is_compliant_after is True

    # The patched XML is still valid ISO 20022 and now compliant.
    message_type, by_role = services.classify_message(result.patched_xml)
    assert message_type is MessageType.PACS_008
    assert by_role

    reassessed = services.assess_message(
        result.patched_xml, policy_id, as_of=post_cliff
    )
    assert reassessed.is_compliant is True
    assert not any(f.rejects_payment for f in reassessed.findings)


def test_cbpr_flow_makes_creditor_structured(
    pacs008_xml: str, post_cliff: date
) -> None:
    """The unstructured creditor becomes fully structured under CBPR+.

    Remediation promotes residual free-form text into ``StrtNm`` and drops
    every ``AdrLine``, so the party lands in the strongest compliant form.
    """
    result = services.remediate_message(
        pacs008_xml, "cbpr-2026", apply=True, as_of=post_cliff
    )

    _, by_role = services.classify_message(result.patched_xml)

    assert by_role[PartyRole.CREDITOR] is AddressClassification.STRUCTURED
