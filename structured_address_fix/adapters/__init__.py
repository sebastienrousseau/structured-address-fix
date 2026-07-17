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

"""Adapters layer: I/O boundaries around the pure domain.

This package translates between the outside world and the domain entities:

- :mod:`iso3166` — offline ISO 3166-1 alpha-2 and US-state validation.
- :mod:`heuristics` — country-aware unstructured-to-hybrid address splitting.
- :mod:`xpath` — ISO 20022 ``PstlAdr`` location tables and message-type
  detection.
- :mod:`xml_reader` — parse a message into addressed parties (XXE-safe).
- :mod:`xml_writer` — apply remediation patches back onto a message.
"""

from __future__ import annotations

from structured_address_fix.adapters.heuristics import (
    HeuristicResult,
    split_unstructured,
)
from structured_address_fix.adapters.iso3166 import (
    ALPHA2_CODES,
    US_STATES,
    is_iso_3166_1_alpha_2,
    is_us_state,
)
from structured_address_fix.adapters.xml_reader import read_addresses
from structured_address_fix.adapters.xml_writer import apply_operations
from structured_address_fix.adapters.xpath import (
    detect_message_type,
    paths_for,
)

__all__ = [
    "ALPHA2_CODES",
    "US_STATES",
    "HeuristicResult",
    "apply_operations",
    "detect_message_type",
    "is_iso_3166_1_alpha_2",
    "is_us_state",
    "paths_for",
    "read_addresses",
    "split_unstructured",
]
