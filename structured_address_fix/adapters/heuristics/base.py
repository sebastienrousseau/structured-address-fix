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

"""Shared types and helpers for the country-aware address heuristics.

Ported from ``pacs008.standards.address``. The behavioural change from the
original is the return type: rather than a bare ``PostalAddress``, each
country splitter yields a :class:`HeuristicResult` carrying the derived
structured fields, the residual free-form ``address_lines``, and a
``confidence`` score in ``[0, 1]`` that downstream remediation copies onto
each :class:`~structured_address_fix.domain.remediation.PatchOperation`.

Confidence is assigned by anchor quality:

- ``0.9`` when a country-specific postcode/state anchor matched, so town
  and postcode were located structurally.
- ``0.4`` when no anchor matched and the last line was promoted to
  ``town_name`` as a best-effort fallback.
- ``0.0`` when the input carried no usable content at all.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from structured_address_fix.domain.address import (
    MAX_ADDRESS_LINE,
    MAX_HYBRID_ADDRESS_LINE_COUNT,
    MAX_TOWN_NAME,
)

#: Confidence when a postcode/state anchor located town and postcode.
CONFIDENCE_ANCHOR: float = 0.9

#: Confidence when the last line was promoted to town as a fallback.
CONFIDENCE_FALLBACK: float = 0.4

#: Confidence when the input carried no usable content.
CONFIDENCE_EMPTY: float = 0.0


class HeuristicResult(BaseModel):
    """The structured fields a splitter recovered from free-form lines.

    Immutable. ``street_name`` is included for completeness — the current
    country splitters do not infer it, so it is always ``None`` for now —
    while ``town_name``, ``post_code`` and ``country_sub_division`` are
    populated when an anchor is found. ``address_lines`` holds the residual
    free-form text, capped at the CBPR+ hybrid limit of two lines.
    """

    model_config = ConfigDict(frozen=True)

    town_name: str | None = None
    post_code: str | None = None
    country_sub_division: str | None = None
    street_name: str | None = None
    country: str
    address_lines: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


def clip(value: str | None, maximum: int) -> str | None:
    """Truncate ``value`` to ``maximum`` characters, preserving ``None``.

    Args:
        value: The string to clip, or ``None``.
        maximum: The maximum permitted length.

    Returns:
        ``None`` if ``value`` is ``None``, else ``value`` truncated to
        ``maximum`` characters.
    """
    if value is None:
        return None
    return value[:maximum]


def pack_adr_lines(remaining: Sequence[str]) -> tuple[str, ...]:
    """Pack residual lines into the hybrid ``AdrLine`` cap.

    Whitespace-only lines are dropped, each surviving line is truncated to
    the 70-character ISO 20022 maximum, and at most two lines are kept to
    respect the CBPR+ UG2026 hybrid cap.

    Args:
        remaining: The leftover free-form lines.

    Returns:
        Up to two cleaned, length-clamped address lines.
    """
    cleaned = [line.strip() for line in remaining if line and line.strip()]
    return tuple(
        line[:MAX_ADDRESS_LINE]
        for line in cleaned[:MAX_HYBRID_ADDRESS_LINE_COUNT]
    )


def clip_town(value: str | None) -> str | None:
    """Clip a candidate town name to the ISO 20022 ``TwnNm`` maximum.

    Args:
        value: The candidate town name, or ``None``.

    Returns:
        The clipped town name, or ``None``.
    """
    return clip(value, MAX_TOWN_NAME)
