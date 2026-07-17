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

"""Offline entitlement verification for premium rule packs.

Verification is intentionally offline and deterministic: it performs
structural (pack shape) and key-shape checks only and makes **no network
calls**. A pack that is malformed fails with :class:`PackIntegrityError`;
a well-formed pack the host is not licensed for fails with
:class:`PackNotLicensedError`. Hosts supply the set of entitlement keys
they hold out of band (config, environment, a signed manifest they have
already validated), so this function never needs to reach a server.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from typing import TYPE_CHECKING

from structured_address_fix.errors import (
    PackIntegrityError,
    PackNotLicensedError,
)

if TYPE_CHECKING:
    from structured_address_fix.plugins import PolicyPack

#: A pack version must be a dotted numeric string (e.g. ``1.0`` or
#: ``2.3.1``).
_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?$")

#: An entitlement key must be a non-trivial ``token@token`` style string.
_KEY_RE = re.compile(r"^[A-Za-z0-9][\w.-]*@[\w.\-]+$")


def _require(condition: bool, message: str, **context: object) -> None:
    """Raise :class:`PackIntegrityError` when ``condition`` is false."""
    if not condition:
        raise PackIntegrityError(message, context=dict(context))


def verify_entitlement(
    pack: PolicyPack, allowed_keys: Collection[str]
) -> None:
    """Verify ``pack`` is well-formed and licensed by ``allowed_keys``.

    Raises :class:`PackIntegrityError` if the pack is structurally invalid
    (bad id, version, policy list, or entitlement key shape) and
    :class:`PackNotLicensedError` if the pack is sound but its entitlement
    key is not present in ``allowed_keys``. Returns ``None`` on success.

    This check is fully offline; ``allowed_keys`` is the host's own record
    of what it is entitled to.
    """
    _require(
        isinstance(pack.id, str) and bool(pack.id),
        "Pack id must be a non-empty string.",
    )
    _require(
        isinstance(pack.version, str)
        and _VERSION_RE.match(pack.version) is not None,
        "Pack version must be a dotted numeric string.",
        version=pack.version,
    )
    _require(
        isinstance(pack.policies, list) and len(pack.policies) > 0,
        "Pack must declare at least one policy.",
    )
    for policy in pack.policies:
        _require(
            isinstance(getattr(policy, "id", None), str)
            and callable(getattr(policy, "assess", None)),
            "Pack policy is not a valid AddressPolicy class.",
            policy=repr(policy),
        )

    key = pack.entitlement_key()
    _require(
        isinstance(key, str) and _KEY_RE.match(key) is not None,
        "Pack entitlement key has an invalid shape.",
        key=key,
    )

    if key not in allowed_keys:
        raise PackNotLicensedError(
            f"Pack {pack.id!r} is not licensed.",
            context={"entitlement_key": key},
        )
