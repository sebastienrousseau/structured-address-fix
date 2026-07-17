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

"""Preview the patch operations remediation would apply (a dry run).

Run: ``python examples/07_preview_patch.py``
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
    """Print the operations without mutating the source document."""
    operations = services.preview_patch(
        PACS008, "cbpr-2026", as_of=date(2026, 12, 1)
    )

    print(f"{len(operations)} operation(s) would be applied:")
    for op in operations:
        print(
            f"    {op.op.value:>6} {op.path} = {op.value!r} "
            f"(reason={op.reason_code.value}, conf={op.confidence})"
        )


if __name__ == "__main__":
    main()
