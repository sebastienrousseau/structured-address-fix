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

"""United Kingdom address splitter.

Anchors on a UK postcode (e.g. ``SW1A 1AA``). Text sharing the postcode's
line becomes the town; failing that, the preceding line is used.
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

_UK_POSTCODE = re.compile(
    r"\b([A-Z]{1,2}[0-9][A-Z0-9]?)\s*([0-9][A-Z]{2})\b",
    re.IGNORECASE,
)


def split(lines: list[str], country: str) -> HeuristicResult:
    """Split UK address lines into structured fields.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code (``"GB"``).

    Returns:
        A :class:`HeuristicResult` with ``0.9`` confidence when a UK
        postcode anchored the split, else ``0.4`` for the last-line
        fallback.
    """
    pst_cd: str | None = None
    twn_nm: str | None = None
    remaining: list[str] = []

    for i, line in enumerate(lines):
        match = _UK_POSTCODE.search(line)
        if match:
            pst_cd = f"{match.group(1).upper()} {match.group(2).upper()}"
            same_line_rest = (
                line[: match.start()] + line[match.end() :]
            ).strip(" ,;")
            if same_line_rest:
                twn_nm = same_line_rest
                remaining = [ln for j, ln in enumerate(lines) if j != i]
            elif i > 0:
                twn_nm = lines[i - 1]
                remaining = [
                    ln for j, ln in enumerate(lines) if j != i and j != i - 1
                ]
            else:
                remaining = lines[i + 1 :]
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
