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

"""Shared address fixtures for the policy finding-matrix tests.

Each fixture returns a :class:`CanonicalAddress` in a specific
classification / defect shape so the per-policy tests can drive a
consistent matrix.
"""

from __future__ import annotations

import pytest

from structured_address_fix.domain import CanonicalAddress


@pytest.fixture()
def structured() -> CanonicalAddress:
    """A fully structured address: town + country + structured detail."""
    return CanonicalAddress(
        town_name="Paris", country="FR", street_name="Rue de Rivoli"
    )


@pytest.fixture()
def hybrid() -> CanonicalAddress:
    """A hybrid address: town + country + one residual AdrLine."""
    return CanonicalAddress(
        town_name="Paris", country="FR", address_lines=("Flat 2",)
    )


@pytest.fixture()
def unstructured() -> CanonicalAddress:
    """A fully unstructured address: AdrLine only, no town/country."""
    return CanonicalAddress(
        address_lines=("123 Main St", "Apt 4", "Springfield")
    )


@pytest.fixture()
def missing_country() -> CanonicalAddress:
    """Town present, country absent (classifies as unstructured)."""
    return CanonicalAddress(town_name="Paris", street_name="Rue")


@pytest.fixture()
def missing_town() -> CanonicalAddress:
    """Country present, town absent."""
    return CanonicalAddress(country="FR", street_name="Rue")


@pytest.fixture()
def bad_country() -> CanonicalAddress:
    """Structured shape with a non-ISO country code."""
    return CanonicalAddress(
        town_name="Nowhere", country="ZZ", street_name="Rue"
    )


@pytest.fixture()
def overflow() -> CanonicalAddress:
    """Hybrid shape carrying an over-length (71-char) AdrLine."""
    return CanonicalAddress(
        town_name="Paris", country="FR", address_lines=("x" * 71,)
    )
