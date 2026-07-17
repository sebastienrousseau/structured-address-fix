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

"""Shared continental-European ``<5 digits> <town>`` splitter.

Germany (``PLZ Ort``) and France (``code postal Ville``) share the same
line shape: a five-digit postcode immediately followed by the town name.
The country-specific modules supply their own compiled pattern.
"""

from __future__ import annotations

import re

from structured_address_fix.adapters.heuristics.base import (
    CONFIDENCE_ANCHOR,
    CONFIDENCE_FALLBACK,
    HeuristicResult,
    clip,
    clip_town,
    pack_adr_lines,
)
from structured_address_fix.domain.address import MAX_POST_CODE


def split_continental(
    lines: list[str],
    country: str,
    pattern: re.Pattern[str],
) -> HeuristicResult:
    """Split a continental-European address on a ``<5 digits> <town>`` line.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code.
        pattern: The compiled postcode pattern (capturing postcode then
            town).

    Returns:
        A :class:`HeuristicResult` with ``0.9`` confidence when the
        pattern anchored the split, else ``0.4`` for the last-line
        fallback.
    """
    pst_cd: str | None = None
    twn_nm: str | None = None
    remaining: list[str] = []

    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            pst_cd = match.group(1)
            twn_nm = match.group(2).strip()
            remaining = [ln for j, ln in enumerate(lines) if j != i]
            break

    if pst_cd is None:
        twn_nm = lines[-1]
        remaining = lines[:-1]
        confidence = CONFIDENCE_FALLBACK
    else:
        confidence = CONFIDENCE_ANCHOR

    return HeuristicResult(
        town_name=clip_town(twn_nm),
        post_code=clip(pst_cd, MAX_POST_CODE),
        country=country,
        address_lines=pack_adr_lines(remaining),
        confidence=confidence,
    )
