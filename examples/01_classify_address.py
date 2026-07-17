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

"""Classify addresses of each CBPR+ shape (structured/hybrid/unstructured).

Run: ``python examples/01_classify_address.py``
"""

from __future__ import annotations

from structured_address_fix import services
from structured_address_fix.domain import CanonicalAddress

STRUCTURED = CanonicalAddress(
    street_name="Baker Street",
    building_number="221B",
    post_code="NW1 6XE",
    town_name="London",
    country="GB",
)
HYBRID = CanonicalAddress(
    town_name="London", country="GB", address_lines=("Flat 2",)
)
UNSTRUCTURED = CanonicalAddress(
    country="GB", address_lines=("Flat 2", "221B Baker Street", "London")
)


def main() -> None:
    """Print the classification of three example addresses."""
    for label, address in (
        ("structured", STRUCTURED),
        ("hybrid", HYBRID),
        ("unstructured", UNSTRUCTURED),
    ):
        classification = services.classify_address(address)
        print(f"{label:>13} address -> {classification.value}")


if __name__ == "__main__":
    main()
