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

"""Remediate a message with ``apply=True`` and print the patched XML.

Run: ``python examples/06_remediate_apply_message.py``
"""

from __future__ import annotations

from datetime import date

from structured_address_fix import services

PACS008 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <CdtTrfTxInf>
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
    """Apply remediation and show the before/after compliance and XML."""
    result = services.remediate_message(
        PACS008, "cbpr-2026", apply=True, as_of=date(2026, 12, 1)
    )

    print(f"compliant before: {result.is_compliant_before}")
    print(f"compliant after:  {result.is_compliant_after}")
    print("--- patched XML ---")
    print(result.patched_xml)


if __name__ == "__main__":
    main()
