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

"""Policy discovery, lookup, and premium-pack loading.

:class:`PolicyRegistry` maps policy ids to policy instances. The
module-level :data:`default_registry` is pre-populated with the four
built-in open-source policies. :func:`load_plugins` extends a registry
with premium policies discovered through the
``structured_address_fix.policies`` entry-point group, refusing any pack
the host is not licensed for.
"""

from __future__ import annotations

from collections.abc import Iterable
from importlib import metadata
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from structured_address_fix.errors import (
    PolicyConflictError,
    UnknownPolicyError,
)
from structured_address_fix.plugins import PolicyPack, verify_entitlement
from structured_address_fix.policies.base import AddressPolicy, PolicyTier
from structured_address_fix.policies.cbpr_2026 import Cbpr2026Policy
from structured_address_fix.policies.generic_structured import (
    GenericStructuredPolicy,
)
from structured_address_fix.policies.hvps_plus import HvpsPlusPolicy
from structured_address_fix.policies.sepa import SepaPolicy

#: The default entry-point group premium packs advertise under.
DEFAULT_PLUGIN_GROUP = "structured_address_fix.policies"


class PolicyInfo(BaseModel):
    """Immutable summary of a registered policy, for listings and menus."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    tier: PolicyTier


class _EntryPointLike(Protocol):
    """The slice of ``importlib.metadata.EntryPoint`` this module needs."""

    def load(self) -> type[PolicyPack]:
        """Import and return the referenced :class:`PolicyPack` subclass."""
        ...


class PolicyRegistry:
    """A mutable registry of address policies keyed by policy id."""

    def __init__(self) -> None:
        """Create an empty registry."""
        self._policies: dict[str, AddressPolicy] = {}

    def register(self, policy: AddressPolicy) -> None:
        """Register ``policy``.

        Raises :class:`PolicyConflictError` if another policy is already
        registered under the same id.
        """
        if policy.id in self._policies:
            raise PolicyConflictError(
                f"A policy with id {policy.id!r} is already registered.",
                context={"policy_id": policy.id},
            )
        self._policies[policy.id] = policy

    def get(self, policy_id: str) -> AddressPolicy:
        """Return the policy registered under ``policy_id``.

        Raises :class:`UnknownPolicyError` if no such policy is registered.
        """
        try:
            return self._policies[policy_id]
        except KeyError:
            raise UnknownPolicyError(
                f"No policy is registered under id {policy_id!r}.",
                context={"policy_id": policy_id},
            ) from None

    def list_policies(self) -> list[PolicyInfo]:
        """Return a :class:`PolicyInfo` for every registered policy."""
        return [
            PolicyInfo(id=policy.id, title=policy.title, tier=policy.tier)
            for policy in self._policies.values()
        ]


def load_plugins(
    registry: PolicyRegistry,
    *,
    group: str = DEFAULT_PLUGIN_GROUP,
    allowed_keys: Iterable[str] = (),
    entry_points: Iterable[_EntryPointLike] | None = None,
) -> PolicyRegistry:
    """Discover premium packs and register the licensed ones on ``registry``.

    Iterates the ``group`` entry points (or the injected ``entry_points``
    iterable, which makes discovery testable without installed packages),
    loads each :class:`PolicyPack`, verifies its entitlement against
    ``allowed_keys``, and registers every policy of each licensed pack.

    ``allowed_keys`` defaults to empty, so premium packs are strictly
    opt-in: with no keys supplied, every discovered pack is refused with
    :class:`~structured_address_fix.errors.PackNotLicensedError`.
    """
    allowed = frozenset(allowed_keys)
    eps: Iterable[_EntryPointLike]
    if entry_points is None:
        eps = metadata.entry_points(group=group)
    else:
        eps = entry_points

    for entry_point in eps:
        pack = entry_point.load()()
        verify_entitlement(pack, allowed)
        for policy_cls in pack.policies:
            registry.register(policy_cls())
    return registry


def _build_default_registry() -> PolicyRegistry:
    """Build a registry pre-populated with the four built-in policies."""
    registry = PolicyRegistry()
    registry.register(Cbpr2026Policy())
    registry.register(GenericStructuredPolicy())
    registry.register(SepaPolicy())
    registry.register(HvpsPlusPolicy())
    return registry


#: The package-wide default registry, carrying the four OSS policies.
default_registry: PolicyRegistry = _build_default_registry()
