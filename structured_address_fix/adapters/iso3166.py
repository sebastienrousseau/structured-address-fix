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

"""Offline ISO 3166-1 alpha-2 country and US-state validation.

The country table is shipped as data, not code: the full official set of
ISO 3166-1 alpha-2 codes lives in ``data/iso3166_alpha2.json`` and is
loaded once at import time into the :data:`ALPHA2_CODES` frozenset. This
keeps validation entirely offline (no network, no third-party dependency)
while letting the code table be refreshed by editing the JSON file.

The US-state table backs the ``US`` address heuristic, which promotes a
matched ``STATE ZIP`` token to ``CtrySubDvsn`` only when the two-letter
token is a genuine US state (or territory) code.
"""

from __future__ import annotations

import json
from importlib import resources

_DATA_PACKAGE = "structured_address_fix.data"
_ALPHA2_RESOURCE = "iso3166_alpha2.json"


def _load_alpha2_codes() -> frozenset[str]:
    """Load the ISO 3166-1 alpha-2 code table from packaged data.

    Returns:
        A frozenset of the upper-case two-letter country codes.
    """
    raw = (
        resources.files(_DATA_PACKAGE)
        .joinpath(_ALPHA2_RESOURCE)
        .read_text(encoding="utf-8")
    )
    codes: list[str] = json.loads(raw)
    return frozenset(codes)


#: Every ISO 3166-1 alpha-2 country code (249 active assignments).
ALPHA2_CODES: frozenset[str] = _load_alpha2_codes()


def is_iso_3166_1_alpha_2(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid ISO 3166-1 alpha-2 code.

    The check is case-sensitive: ISO 3166-1 alpha-2 codes are upper-case,
    so ``"gb"`` is rejected while ``"GB"`` is accepted.

    Args:
        value: The candidate two-letter country code.

    Returns:
        ``True`` if ``value`` is a recognised country code.
    """
    return value in ALPHA2_CODES


#: US state, district and territory codes accepted by the US heuristic.
US_STATES: frozenset[str] = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    }
)


def is_us_state(value: str) -> bool:
    """Return ``True`` if ``value`` is a US state/territory code.

    Args:
        value: The candidate two-letter subdivision code.

    Returns:
        ``True`` if ``value`` is a recognised US state, the District of
        Columbia, or a territory carried in :data:`US_STATES`.
    """
    return value in US_STATES
