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

"""Remediate an unstructured address: show before, after, and operations.

Run: ``python examples/03_remediate_address.py``
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
    """Remediate the address and print the derived patch operations."""
    result = services.remediate_address(
        ADDRESS, "cbpr-2026", as_of=date(2026, 12, 1)
    )
    suggestion = result.suggestions[0]

    print(f"compliant before: {result.is_compliant_before}")
    print(f"compliant after:  {result.is_compliant_after}")
    print(f"before lines: {suggestion.before.address_lines}")
    print(
        "after: "
        f"town={suggestion.after.town_name!r} "
        f"post_code={suggestion.after.post_code!r} "
        f"lines={suggestion.after.address_lines}"
    )
    print("operations:")
    for op in suggestion.operations:
        print(
            f"    {op.op.value:>6} {op.path} = {op.value!r} "
            f"(reason={op.reason_code.value}, conf={op.confidence})"
        )
    print(f"explanation: {suggestion.explanation}")


if __name__ == "__main__":
    main()
