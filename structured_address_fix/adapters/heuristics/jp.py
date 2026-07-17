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

"""Japan address splitter.

Anchors on a ``〒NNN-NNNN`` (or bare ``NNN-NNNN``) postcode. Text sharing
the postcode's line becomes the town; failing that, the following line is
used.
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

_JP_POSTCODE = re.compile(r"(?:〒\s*)?(\d{3}-\d{4})\b")


def split(lines: list[str], country: str) -> HeuristicResult:
    """Split a Japanese address on its postcode anchor.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code (``"JP"``).

    Returns:
        A :class:`HeuristicResult` with ``0.9`` confidence when a
        ``NNN-NNNN`` postcode anchored the split, else ``0.4`` for the
        last-line fallback.
    """
    pst_cd: str | None = None
    twn_nm: str | None = None
    remaining: list[str] = []

    for i, line in enumerate(lines):
        match = _JP_POSTCODE.search(line)
        if match:
            pst_cd = match.group(1)
            same_line_rest = (
                line[: match.start()] + line[match.end() :]
            ).strip(" ,;")
            if same_line_rest:
                twn_nm = same_line_rest
                remaining = [ln for j, ln in enumerate(lines) if j != i]
            elif i + 1 < len(lines):
                twn_nm = lines[i + 1]
                remaining = [
                    ln for j, ln in enumerate(lines) if j != i and j != i + 1
                ]
            else:
                remaining = lines[:i]
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
