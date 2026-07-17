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

"""United States address splitter.

Anchors on a ``STATE ZIP`` token (e.g. ``CA 95014`` or ``DC 20500-0003``)
whose two-letter part is a genuine US state/territory code. The chunk
before the anchor yields the town; the state populates ``CtrySubDvsn``.
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
from structured_address_fix.adapters.iso3166 import is_us_state
from structured_address_fix.domain.address import (
    MAX_COUNTRY_SUB_DIVISION,
    MAX_POST_CODE,
)

_US_STATE_ZIP = re.compile(r"\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b")


def split(lines: list[str], country: str) -> HeuristicResult:
    """Split US address lines into structured fields.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code (``"US"``).

    Returns:
        A :class:`HeuristicResult` with ``0.9`` confidence when a valid
        ``STATE ZIP`` token anchored the split, else ``0.4`` for the
        last-line fallback. A ``STATE ZIP`` whose state is not a real US
        code is ignored and treated as no anchor.
    """
    pst_cd: str | None = None
    twn_nm: str | None = None
    ctry_sub_dvsn: str | None = None
    remaining: list[str] = []

    for i, line in enumerate(lines):
        match = _US_STATE_ZIP.search(line)
        if match and is_us_state(match.group(1)):
            ctry_sub_dvsn = match.group(1)
            pst_cd = match.group(2)
            before = line[: match.start()].rstrip(" ,;")
            if before:
                # ``before`` is non-empty after stripping trailing
                # separators, so its final comma-segment is always a
                # non-empty town candidate.
                twn_nm = before.split(",")[-1].strip()
                rest_of_line = ",".join(before.split(",")[:-1]).strip()
                line_remainder = [rest_of_line] if rest_of_line else []
                remaining = [
                    ln for j, ln in enumerate(lines) if j != i
                ] + line_remainder
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
        country_sub_division=clip(ctry_sub_dvsn, MAX_COUNTRY_SUB_DIVISION),
        country=country,
        address_lines=pack_adr_lines(remaining),
        confidence=confidence,
    )
