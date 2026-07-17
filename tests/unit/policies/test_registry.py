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

"""Tests for policy registration, lookup, and plugin discovery."""

from __future__ import annotations

import pytest

from structured_address_fix.errors import (
    PackNotLicensedError,
    PolicyConflictError,
    UnknownPolicyError,
)
from structured_address_fix.plugins import PolicyPack
from structured_address_fix.policies import (
    Cbpr2026Policy,
    PolicyContext,
    PolicyRegistry,
    default_registry,
    load_plugins,
)
from structured_address_fix.policies.base import BasePolicy


class _PremiumPolicy(BasePolicy):
    """A trivial premium policy used to exercise plugin discovery."""

    id = "acme-premium"
    title = "Acme Premium"
    tier = "premium"

    def assess(self, address, ctx):
        """Return no findings."""
        return []


class _AcmePack(PolicyPack):
    """A well-formed premium pack advertising one policy."""

    id = "acme"
    version = "1.0"
    policies = [_PremiumPolicy]


class _FakeEntryPoint:
    """A stand-in for ``importlib.metadata.EntryPoint``."""

    def __init__(self, pack_cls: type[PolicyPack]) -> None:
        self._pack_cls = pack_cls

    def load(self) -> type[PolicyPack]:
        """Return the pack class this entry point references."""
        return self._pack_cls


def test_register_and_get() -> None:
    """A registered policy is retrievable by id."""
    registry = PolicyRegistry()
    policy = Cbpr2026Policy()
    registry.register(policy)
    assert registry.get("cbpr-2026") is policy


def test_duplicate_registration_conflicts() -> None:
    """Registering the same id twice raises a conflict."""
    registry = PolicyRegistry()
    registry.register(Cbpr2026Policy())
    with pytest.raises(PolicyConflictError) as exc:
        registry.register(Cbpr2026Policy())
    assert exc.value.context["policy_id"] == "cbpr-2026"


def test_get_unknown_raises() -> None:
    """Looking up an unregistered id raises ``UnknownPolicyError``."""
    registry = PolicyRegistry()
    with pytest.raises(UnknownPolicyError) as exc:
        registry.get("nope")
    assert exc.value.context["policy_id"] == "nope"


def test_default_registry_lists_four_builtins() -> None:
    """The default registry carries the four OSS policies."""
    infos = default_registry.list_policies()
    ids = {info.id for info in infos}
    assert ids == {"cbpr-2026", "generic-structured", "sepa", "hvps-plus"}
    assert all(info.tier == "oss" for info in infos)


def test_default_registry_policies_are_usable() -> None:
    """A policy fetched from the default registry can assess and target."""
    from structured_address_fix.domain import CanonicalAddress

    policy = default_registry.get("cbpr-2026")
    address = CanonicalAddress(
        town_name="Paris", country="FR", street_name="R"
    )
    assert policy.assess(address, PolicyContext()) == []
    assert policy.target(address).address_lines == ()


def test_load_plugins_registers_licensed_pack() -> None:
    """A licensed pack's policies are registered from an entry point."""
    registry = PolicyRegistry()
    load_plugins(
        registry,
        allowed_keys={"acme@1.0"},
        entry_points=[_FakeEntryPoint(_AcmePack)],
    )
    assert registry.get("acme-premium").tier == "premium"


def test_load_plugins_refuses_unlicensed_pack() -> None:
    """An unlicensed pack is refused and nothing is registered."""
    registry = PolicyRegistry()
    with pytest.raises(PackNotLicensedError):
        load_plugins(
            registry,
            entry_points=[_FakeEntryPoint(_AcmePack)],
        )
    with pytest.raises(UnknownPolicyError):
        registry.get("acme-premium")


def test_load_plugins_default_group_discovers_nothing() -> None:
    """With no injected eps and no installed packs, discovery is a no-op."""
    registry = PolicyRegistry()
    returned = load_plugins(
        registry, group="structured_address_fix.nonexistent_group"
    )
    assert returned is registry
    assert registry.list_policies() == []
