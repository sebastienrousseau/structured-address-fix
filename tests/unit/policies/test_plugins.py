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

"""Tests for the premium-pack SDK and offline entitlement checks."""

from __future__ import annotations

from typing import Any

import pytest

from structured_address_fix.errors import (
    PackIntegrityError,
    PackNotLicensedError,
)
from structured_address_fix.plugins import (
    PolicyPack,
    is_policy_class,
    register_policy,
    verify_entitlement,
)
from structured_address_fix.policies.base import BasePolicy


class _GoodPolicy(BasePolicy):
    """A minimal valid policy for pack construction."""

    id = "good-policy"
    title = "Good"
    tier = "premium"

    def assess(self, address, ctx):
        """Return no findings."""
        return []


def _make_pack(**overrides: Any) -> PolicyPack:
    """Build a pack instance, overriding class attributes/methods."""
    attrs: dict[str, Any] = {
        "id": "good",
        "version": "1.0",
        "policies": [_GoodPolicy],
    }
    attrs.update(overrides)
    pack_cls = type("_Pack", (PolicyPack,), attrs)
    return pack_cls()


# -- register_policy decorator ----------------------------------------------


def test_register_policy_marks_class() -> None:
    """The decorator tags a class and returns it unchanged."""

    @register_policy
    class Tagged:
        """A tagged class."""

    assert is_policy_class(Tagged)
    assert Tagged.__name__ == "Tagged"


def test_undecorated_class_is_not_marked() -> None:
    """An undecorated class is not seen as a policy."""

    class Plain:
        """An untagged class."""

    assert not is_policy_class(Plain)


# -- PolicyPack -------------------------------------------------------------


def test_entitlement_key_default_shape() -> None:
    """The default entitlement key combines id and version."""
    assert _make_pack().entitlement_key() == "good@1.0"


# -- verify_entitlement: success + licensing --------------------------------


def test_verify_entitlement_accepts_licensed_pack() -> None:
    """A well-formed, licensed pack verifies without raising."""
    assert verify_entitlement(_make_pack(), {"good@1.0"}) is None


def test_verify_entitlement_refuses_unlicensed_pack() -> None:
    """A well-formed pack not in the allowed set is refused."""
    with pytest.raises(PackNotLicensedError) as exc:
        verify_entitlement(_make_pack(), set())
    assert exc.value.context["entitlement_key"] == "good@1.0"


# -- verify_entitlement: integrity failures ---------------------------------


def test_integrity_rejects_empty_id() -> None:
    """An empty pack id fails integrity."""
    with pytest.raises(PackIntegrityError):
        verify_entitlement(_make_pack(id=""), {"good@1.0"})


def test_integrity_rejects_bad_version() -> None:
    """A non-numeric version fails integrity."""
    with pytest.raises(PackIntegrityError) as exc:
        verify_entitlement(_make_pack(version="latest"), {"good@1.0"})
    assert exc.value.context["version"] == "latest"


def test_integrity_rejects_empty_policy_list() -> None:
    """A pack with no policies fails integrity."""
    with pytest.raises(PackIntegrityError):
        verify_entitlement(_make_pack(policies=[]), {"good@1.0"})


def test_integrity_rejects_non_policy_member() -> None:
    """A policy list member that is not a policy class fails integrity."""
    with pytest.raises(PackIntegrityError):
        verify_entitlement(_make_pack(policies=[object]), {"good@1.0"})


def test_integrity_rejects_bad_key_shape() -> None:
    """An entitlement key with no ``@`` fails the key-shape check."""

    def _bad_key(self: PolicyPack) -> str:
        return "not-a-valid-key"

    pack = _make_pack(entitlement_key=_bad_key)
    with pytest.raises(PackIntegrityError) as exc:
        verify_entitlement(pack, {"good@1.0"})
    assert exc.value.context["key"] == "not-a-valid-key"
