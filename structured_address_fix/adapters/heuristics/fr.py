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

"""France address splitter: five-digit code postal followed by the Ville."""

from __future__ import annotations

import re

from structured_address_fix.adapters.heuristics.base import HeuristicResult
from structured_address_fix.adapters.heuristics.continental import (
    split_continental,
)

_FR_POSTCODE = re.compile(r"\b(\d{5})\s+([^\d]{2,})")


def split(lines: list[str], country: str) -> HeuristicResult:
    """Split a French address on its ``code postal Ville`` line.

    Args:
        lines: Cleaned, non-empty address lines.
        country: The ISO 3166-1 alpha-2 country code (``"FR"``).

    Returns:
        A :class:`HeuristicResult` for the French address.
    """
    return split_continental(lines, country, _FR_POSTCODE)
