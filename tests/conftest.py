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

"""Shared, cross-suite fixtures for the service, integration, and
property tests.

Fixtures here are deliberately named distinctly (``gb_*``, ``us_*``,
``*_address``) so they never clash with the FR-shaped finding-matrix
fixtures defined in ``tests/unit/policies/conftest.py``; the two conftests
are additive. The cliff-relative ``POST_CLIFF`` / ``PRE_CLIFF`` dates are
exposed both as module constants and as fixtures for convenience.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from structured_address_fix.domain import CanonicalAddress

#: An assessment date on or after the 14 November 2026 cliff.
POST_CLIFF: date = date(2026, 12, 1)

#: An assessment date comfortably before the cliff.
PRE_CLIFF: date = date(2026, 1, 1)

#: Path to the bundled four-party pacs.008 fixture.
PACS008_FIXTURE: Path = (
    Path(__file__).parent / "fixtures" / "messages" / "pacs008_three_party.xml"
)


@pytest.fixture()
def post_cliff() -> date:
    """An ``as_of`` date on the far side of the November 2026 cliff."""
    return POST_CLIFF


@pytest.fixture()
def pre_cliff() -> date:
    """An ``as_of`` date before the November 2026 cliff."""
    return PRE_CLIFF


@pytest.fixture()
def gb_structured() -> CanonicalAddress:
    """A fully structured GB address: town + country + structured detail."""
    return CanonicalAddress(
        street_name="Baker Street",
        building_number="221B",
        post_code="NW1 6XE",
        town_name="London",
        country="GB",
    )


@pytest.fixture()
def gb_hybrid() -> CanonicalAddress:
    """A hybrid GB address: town + country plus one residual AdrLine."""
    return CanonicalAddress(
        town_name="London",
        country="GB",
        post_code="NW1 6XE",
        address_lines=("Flat 2",),
    )


@pytest.fixture()
def gb_unstructured() -> CanonicalAddress:
    """An unstructured GB address: country + AdrLine only, no town."""
    return CanonicalAddress(
        country="GB",
        address_lines=("Flat 2", "221B Baker Street", "London NW1 6XE"),
    )


@pytest.fixture()
def no_country_unstructured() -> CanonicalAddress:
    """An unstructured address with no country at all (AdrLine only)."""
    return CanonicalAddress(
        address_lines=("1 Infinite Loop", "Cupertino CA 95014"),
    )


@pytest.fixture()
def us_unstructured() -> CanonicalAddress:
    """An unstructured US address: country + AdrLine only, no town."""
    return CanonicalAddress(
        country="US",
        address_lines=("1 Infinite Loop", "Cupertino CA 95014"),
    )


@pytest.fixture()
def bad_country_address() -> CanonicalAddress:
    """An unstructured address whose country is a non-ISO code (``ZZ``)."""
    return CanonicalAddress(country="ZZ", address_lines=("somewhere",))


@pytest.fixture()
def pacs008_xml() -> str:
    """The raw XML of the four-party pacs.008 fixture message."""
    return PACS008_FIXTURE.read_text(encoding="utf-8")
