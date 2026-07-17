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

"""Assess one unstructured address on both sides of the 2026 cliff.

The finding stands either way; only the rulebook wording changes.

Run: ``python examples/02_assess_address_pre_post_cliff.py``
"""

from __future__ import annotations

from datetime import date

from structured_address_fix import services
from structured_address_fix.domain import CanonicalAddress

ADDRESS = CanonicalAddress(
    country="GB",
    address_lines=("Flat 2", "221B Baker Street", "London NW1 6XE"),
)


def main() -> None:
    """Assess the same address before and after the cliff and compare."""
    for label, as_of in (
        ("pre-cliff ", date(2026, 1, 1)),
        ("post-cliff", date(2026, 12, 1)),
    ):
        report = services.assess_address(ADDRESS, "cbpr-2026", as_of=as_of)
        print(f"[{label}] compliant={report.is_compliant}")
        for finding in report.findings:
            flag = "REJECT" if finding.rejects_payment else "warn  "
            print(f"    {flag} {finding.code.value}: {finding.message}")


if __name__ == "__main__":
    main()
