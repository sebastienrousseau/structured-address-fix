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

"""Country-aware unstructured-to-hybrid address heuristics.

:func:`split_unstructured` dispatches free-form address lines to a
country-specific splitter (``GB``, ``US``, ``DE``, ``FR``, ``JP``) or the
best-effort fallback, returning a :class:`HeuristicResult` that carries the
recovered structured fields plus a ``confidence`` score for downstream
patch operations. Ported from ``pacs008.standards.address.from_unstructured``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from structured_address_fix.adapters.heuristics import (
    de,
    fallback,
    fr,
    gb,
    jp,
    us,
)
from structured_address_fix.adapters.heuristics.base import (
    CONFIDENCE_EMPTY,
    HeuristicResult,
)
from structured_address_fix.adapters.iso3166 import is_iso_3166_1_alpha_2
from structured_address_fix.errors import InvalidAddressError

_Splitter = Callable[[list[str], str], HeuristicResult]

_HANDLERS: dict[str, _Splitter] = {
    "GB": gb.split,
    "US": us.split,
    "DE": de.split,
    "FR": fr.split,
    "JP": jp.split,
}


def split_unstructured(
    lines: Sequence[str],
    country: str,
) -> HeuristicResult:
    """Split unstructured address lines into a country-aware hybrid form.

    Country-specific heuristics cover ``GB``, ``US``, ``DE``, ``FR`` and
    ``JP``; every other country falls back to promoting the last line to
    ``town_name``. Empty or whitespace-only input yields a country-only
    result with ``0.0`` confidence.

    Args:
        lines: Free-form address lines from legacy data. Empty and
            whitespace-only lines are skipped.
        country: The ISO 3166-1 alpha-2 country code (e.g. ``"GB"``).

    Returns:
        A :class:`HeuristicResult` carrying the derived structured fields,
        residual ``address_lines``, and a heuristic ``confidence``.

    Raises:
        InvalidAddressError: if ``country`` is not a valid ISO 3166-1
            alpha-2 code.
    """
    if not is_iso_3166_1_alpha_2(country):
        raise InvalidAddressError(
            "country must be ISO 3166-1 alpha-2 (e.g. 'GB', 'US'); "
            f"got {country!r}",
            context={"country": country},
        )

    cleaned = [line.strip() for line in lines if line and line.strip()]
    if not cleaned:
        return HeuristicResult(country=country, confidence=CONFIDENCE_EMPTY)

    handler = _HANDLERS.get(country, fallback.split)
    return handler(cleaned, country)


__all__ = ["HeuristicResult", "split_unstructured"]
