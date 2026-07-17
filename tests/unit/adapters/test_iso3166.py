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

"""Tests for the offline ISO 3166-1 alpha-2 and US-state tables."""

from __future__ import annotations

from structured_address_fix.adapters.iso3166 import (
    ALPHA2_CODES,
    US_STATES,
    is_iso_3166_1_alpha_2,
    is_us_state,
)


def test_table_has_full_official_set() -> None:
    """The packaged table carries all 249 active ISO 3166-1 codes."""
    assert len(ALPHA2_CODES) == 249


def test_known_country_accepted() -> None:
    """A valid upper-case code is recognised."""
    assert is_iso_3166_1_alpha_2("GB")
    assert is_iso_3166_1_alpha_2("US")
    assert is_iso_3166_1_alpha_2("JP")


def test_lowercase_country_rejected() -> None:
    """The check is case-sensitive: lower-case is rejected."""
    assert not is_iso_3166_1_alpha_2("gb")


def test_unknown_country_rejected() -> None:
    """A non-existent code is rejected."""
    assert not is_iso_3166_1_alpha_2("ZZ")
    assert not is_iso_3166_1_alpha_2("XX")


def test_us_states_table_size() -> None:
    """The US-state table carries 50 states plus DC."""
    assert len(US_STATES) == 51


def test_known_us_state_accepted() -> None:
    """A valid US state/territory code is recognised."""
    assert is_us_state("CA")
    assert is_us_state("DC")


def test_unknown_us_state_rejected() -> None:
    """A code that is not a US state is rejected."""
    assert not is_us_state("ZZ")
    assert not is_us_state("GB")
