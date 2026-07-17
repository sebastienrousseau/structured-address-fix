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

"""Package configuration and shared constants.

The November 2026 cliff date is the single most load-bearing constant in
the package: from this date, fully unstructured postal addresses are
rejected across SWIFT CBPR+, HVPS+, T2 RTGS, CHAPS, Fedwire, and Lynx.
"""

from __future__ import annotations

import os
from datetime import date

from structured_address_fix.domain.enums import PolicyId

#: The binding global deadline — 14 November 2026 (SWIFT CBPR+ UG2026).
#: Fedwire's own cutover is 16 November 2026, but the SWIFT date binds
#: first, so it is the reference used throughout.
NOV_2026_CLIFF: date = date(2026, 11, 14)

#: The default policy applied when a caller does not name one.
DEFAULT_POLICY_ID: str = PolicyId.CBPR_2026.value


def default_policy_id() -> str:
    """Return the default policy id, overridable via the environment.

    Reads ``SAF_DEFAULT_POLICY`` when set and non-empty; otherwise falls
    back to :data:`DEFAULT_POLICY_ID`. Kept as a function (not a
    module-level read) so tests and hosts can change the environment
    without re-importing the package.
    """
    override = os.environ.get("SAF_DEFAULT_POLICY", "").strip()
    return override or DEFAULT_POLICY_ID
