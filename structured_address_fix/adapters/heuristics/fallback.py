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

"""Best-effort splitter for countries without a dedicated heuristic.

The last line is promoted to ``town_name`` and everything before it is
packed into the residual address lines. Confidence is always ``0.4``
because no postcode anchor is consulted.
"""

from __future__ import annotations

from structured_address_fix.adapters.heuristics.base import (
    CONFIDENCE_FALLBACK,
    HeuristicResult,
    clip_town,
    pack_adr_lines,
)


def split(lines: list[str], country: str) -> HeuristicResult:
    """Promote the last line to town for an unhandled country.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code.

    Returns:
        A :class:`HeuristicResult` with ``0.4`` fallback confidence.
    """
    twn_nm = lines[-1]
    remaining = lines[:-1]
    return HeuristicResult(
        town_name=clip_town(twn_nm),
        country=country,
        address_lines=pack_adr_lines(remaining),
        confidence=CONFIDENCE_FALLBACK,
    )
