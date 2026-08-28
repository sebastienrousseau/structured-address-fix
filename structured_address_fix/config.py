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

#: The date SWIFT CBPR+ UG2026 originally set for the structured address
#: cutover. Retained because it is the date every scheme planned around and
#: the one users still ask about — not because it binds.
ANNOUNCED_CUTOVER: date = date(2026, 11, 14)

#: The day Swift accepted a community request to extend the migration and
#: deferred every payments change in Standards Release 2026.
#: https://www.swift.com/news-events/news/swift-accepts-community-request-extend-structured-address-migration-iso-20022-payment-messages
CUTOVER_DEFERRED_ON: date = date(2026, 8, 27)

#: The date the requirement actually binds from, or ``None`` while there is
#: not one. Swift will confirm replacement timing by December 2026 at the
#: latest; until it does, no date has force, and reporting one as binding
#: tells a bank to plan around something that has been withdrawn.
#:
#: The requirement itself was agreed by the community in 2023 and stands.
#: Only its timing moved, so findings are unaffected — a message that would
#: have been rejected still would be, once the rule takes effect.
BINDING_CUTOVER: date | None = None

#: Deprecated alias for :data:`ANNOUNCED_CUTOVER`. Kept so that existing
#: callers keep importing successfully; it names a date that no longer binds,
#: so prefer :data:`BINDING_CUTOVER` and handle ``None``.
NOV_2026_CLIFF: date = ANNOUNCED_CUTOVER

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
