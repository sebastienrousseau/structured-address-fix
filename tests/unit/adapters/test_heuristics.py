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

"""Tests for the country-aware unstructured-to-hybrid heuristics.

Ports the intent of ``pacs008``'s own ``from_unstructured`` tests and adds
assertions on the new ``confidence`` score and residual ``address_lines``.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from structured_address_fix.adapters.heuristics import (
    HeuristicResult,
    split_unstructured,
)
from structured_address_fix.adapters.heuristics.base import (
    CONFIDENCE_ANCHOR,
    CONFIDENCE_EMPTY,
    CONFIDENCE_FALLBACK,
)
from structured_address_fix.errors import InvalidAddressError

# --- GB --------------------------------------------------------------------


def test_gb_postcode_alone_on_last_line() -> None:
    """Postcode on its own line promotes the preceding line to town."""
    result = split_unstructured(["London", "SW1A 1AA"], "GB")
    assert result.post_code == "SW1A 1AA"
    assert result.town_name == "London"
    assert result.country == "GB"
    assert result.confidence == CONFIDENCE_ANCHOR


def test_gb_town_and_postcode_same_line() -> None:
    """Town sharing the postcode's line becomes the town name."""
    result = split_unstructured(["42 High Street", "London SW1A 1AA"], "GB")
    assert result.post_code == "SW1A 1AA"
    assert result.town_name == "London"
    assert result.address_lines == ("42 High Street",)
    assert result.confidence == CONFIDENCE_ANCHOR


def test_gb_lowercase_postcode_normalised() -> None:
    """A lower-case postcode is upper-cased and spaced."""
    result = split_unstructured(["London sw1a 1aa"], "GB")
    assert result.post_code == "SW1A 1AA"


def test_gb_postcode_first_line_no_town() -> None:
    """Postcode alone on the first line leaves the town unknown."""
    result = split_unstructured(["SW1A 1AA", "Extra"], "GB")
    assert result.post_code == "SW1A 1AA"
    assert result.town_name is None
    assert result.address_lines == ("Extra",)


def test_gb_no_postcode_falls_back_to_last_line() -> None:
    """With no postcode the last line becomes the town at 0.4 confidence."""
    result = split_unstructured(["42 High Street", "Townless"], "GB")
    assert result.town_name == "Townless"
    assert result.post_code is None
    assert result.confidence == CONFIDENCE_FALLBACK


# --- US --------------------------------------------------------------------


def test_us_city_state_zip() -> None:
    """A ``City, ST ZIP`` line yields town, postcode and subdivision."""
    result = split_unstructured(
        ["1 Infinite Loop", "Cupertino, CA 95014"], "US"
    )
    assert result.post_code == "95014"
    assert result.town_name == "Cupertino"
    assert result.country_sub_division == "CA"
    assert result.confidence == CONFIDENCE_ANCHOR


def test_us_zip_plus_four() -> None:
    """A ZIP+4 postcode is captured intact."""
    result = split_unstructured(
        ["1600 Pennsylvania Ave NW", "Washington, DC 20500-0003"], "US"
    )
    assert result.post_code == "20500-0003"
    assert result.country_sub_division == "DC"


def test_us_extra_before_town_kept_as_line() -> None:
    """Text before the town on the anchor line survives as a residual."""
    result = split_unstructured(["Attn: Ops, Cambridge, MA 02139"], "US")
    assert result.town_name == "Cambridge"
    assert result.country_sub_division == "MA"
    assert result.address_lines == ("Attn: Ops",)


def test_us_state_zip_first_line_no_town() -> None:
    """A bare ``ST ZIP`` first line leaves the town unknown."""
    result = split_unstructured(["CA 95014", "Suite 5"], "US")
    assert result.country_sub_division == "CA"
    assert result.town_name is None


def test_us_state_zip_preceding_line_town() -> None:
    """A bare ``ST ZIP`` line promotes the preceding line to town."""
    result = split_unstructured(["Springfield", "IL 62701"], "US")
    assert result.town_name == "Springfield"
    assert result.country_sub_division == "IL"


def test_us_invalid_state_falls_back() -> None:
    """A ``ST ZIP`` whose state is not real is ignored (fallback)."""
    result = split_unstructured(["1 Test Street", "Smalltown, ZZ 12345"], "US")
    assert result.country_sub_division is None
    assert result.confidence == CONFIDENCE_FALLBACK


# --- DE / FR ---------------------------------------------------------------


def test_de_plz_ort() -> None:
    """A German ``PLZ Ort`` line yields postcode and town."""
    result = split_unstructured(["Friedrichstrasse 100", "10117 Berlin"], "DE")
    assert result.post_code == "10117"
    assert result.town_name == "Berlin"
    assert result.confidence == CONFIDENCE_ANCHOR


def test_de_no_plz_falls_back() -> None:
    """Without a PLZ the German splitter falls back to the last line."""
    result = split_unstructured(["Ortsteil", "Berlin"], "DE")
    assert result.town_name == "Berlin"
    assert result.confidence == CONFIDENCE_FALLBACK


def test_fr_code_postal_ville() -> None:
    """A French ``code postal Ville`` line yields postcode and town."""
    result = split_unstructured(["1 Rue de la Paix", "75001 Paris"], "FR")
    assert result.post_code == "75001"
    assert result.town_name == "Paris"
    assert result.confidence == CONFIDENCE_ANCHOR


# --- JP --------------------------------------------------------------------


def test_jp_postcode_with_marker() -> None:
    """A ``〒NNN-NNNN`` marked postcode is captured; rest is the town."""
    result = split_unstructured(["1-1 Chiyoda", "〒100-0001 Tokyo"], "JP")
    assert result.post_code == "100-0001"
    assert result.town_name == "Tokyo"
    assert result.confidence == CONFIDENCE_ANCHOR


def test_jp_postcode_without_marker() -> None:
    """A bare ``NNN-NNNN`` postcode on a town line is captured."""
    result = split_unstructured(["Tokyo 100-0001"], "JP")
    assert result.post_code == "100-0001"
    assert result.town_name == "Tokyo"


def test_jp_postcode_alone_uses_next_line() -> None:
    """A postcode-only line promotes the following line to town."""
    result = split_unstructured(["100-0001", "Tokyo"], "JP")
    assert result.post_code == "100-0001"
    assert result.town_name == "Tokyo"


def test_jp_postcode_on_last_line_no_town() -> None:
    """A postcode-only last line leaves the town unknown."""
    result = split_unstructured(["Chiyoda", "100-0001"], "JP")
    assert result.post_code == "100-0001"
    assert result.town_name is None
    assert result.address_lines == ("Chiyoda",)


def test_jp_no_postcode_falls_back() -> None:
    """Without a postcode the Japanese splitter falls back."""
    result = split_unstructured(["Chiyoda", "Tokyo"], "JP")
    assert result.post_code is None
    assert result.town_name == "Tokyo"
    assert result.confidence == CONFIDENCE_FALLBACK


# --- Fallback / dispatch ---------------------------------------------------


def test_fallback_unknown_country_passes_through() -> None:
    """An unhandled country promotes the last line to town."""
    result = split_unstructured(["Street 1", "City", "Region"], "IT")
    assert result.country == "IT"
    assert result.town_name == "Region"
    assert result.confidence == CONFIDENCE_FALLBACK


def test_empty_input_returns_country_only() -> None:
    """Empty input yields a country-only result at 0.0 confidence."""
    result = split_unstructured([], "GB")
    assert result.country == "GB"
    assert result.town_name is None
    assert result.address_lines == ()
    assert result.confidence == CONFIDENCE_EMPTY


def test_whitespace_only_lines_skipped() -> None:
    """Blank and whitespace-only lines are dropped before splitting."""
    result = split_unstructured(["   ", "", "London", "SW1A 1AA"], "GB")
    assert result.post_code == "SW1A 1AA"
    assert result.town_name == "London"


def test_invalid_country_hint_rejected() -> None:
    """An invalid country hint raises InvalidAddressError."""
    with pytest.raises(InvalidAddressError, match="ISO 3166-1 alpha-2"):
        split_unstructured(["foo"], "ZZZ")


def test_lowercase_country_hint_rejected() -> None:
    """A lower-case country hint is rejected."""
    with pytest.raises(InvalidAddressError):
        split_unstructured(["foo"], "gb")


def test_adr_line_capped_at_two() -> None:
    """Residual lines are capped at the hybrid limit of two."""
    result = split_unstructured(["L1", "L2", "L3", "L4", "L5", "London"], "GB")
    assert len(result.address_lines) <= 2


def test_long_adr_line_truncated_to_70_chars() -> None:
    """A residual line over 70 characters is truncated."""
    result = split_unstructured(["x" * 100, "London SW1A 1AA"], "GB")
    for line in result.address_lines:
        assert len(line) <= 70


def test_result_is_frozen() -> None:
    """HeuristicResult is immutable."""
    result = split_unstructured(["London SW1A 1AA"], "GB")
    assert isinstance(result, HeuristicResult)
    with pytest.raises(ValidationError):
        result.confidence = 0.1  # type: ignore[misc]
