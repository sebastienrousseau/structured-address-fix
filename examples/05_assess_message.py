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

"""Assess every addressed party in a pacs.008 message.

Run: ``python examples/05_assess_message.py``
"""

from __future__ import annotations

from datetime import date

from structured_address_fix import services

PACS008 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <CdtTrfTxInf>
      <Dbtr>
        <Nm>Acme Debtor Ltd</Nm>
        <PstlAdr>
          <StrtNm>High Street</StrtNm><BldgNb>42</BldgNb>
          <PstCd>SW1A 1AA</PstCd><TwnNm>London</TwnNm><Ctry>GB</Ctry>
        </PstlAdr>
      </Dbtr>
      <Cdtr>
        <Nm>Beta Creditor</Nm>
        <PstlAdr>
          <Ctry>US</Ctry>
          <AdrLine>1 Infinite Loop</AdrLine>
          <AdrLine>Cupertino CA 95014</AdrLine>
        </PstlAdr>
      </Cdtr>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>
"""


def main() -> None:
    """Assess the message and print each finding with its location."""
    report = services.assess_message(
        PACS008, "cbpr-2026", as_of=date(2026, 12, 1)
    )

    print(f"message type:  {report.message_type}")
    print(f"addresses:     {report.assessed_addresses}")
    print(f"compliant:     {report.is_compliant}")
    for finding in report.findings:
        role = finding.party_role.value if finding.party_role else "?"
        print(
            f"    [{role}] {finding.code.value} at {finding.location}: "
            f"{finding.message}"
        )


if __name__ == "__main__":
    main()
