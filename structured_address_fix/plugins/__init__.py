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

"""The premium rule-pack SDK.

Third parties ship premium policies by subclassing :class:`PolicyPack`,
listing their policy classes (each optionally tagged with
:func:`register_policy`), and exposing the pack through the
``structured_address_fix.policies`` entry-point group. The registry
discovers packs, verifies their entitlement offline (see
:mod:`structured_address_fix.plugins.licensing`), and registers the
policies of any pack the host is licensed for.
"""

from __future__ import annotations

import abc
from typing import ClassVar

from structured_address_fix.plugins.licensing import verify_entitlement
from structured_address_fix.policies.base import AddressPolicy

#: Attribute stamped onto policy classes tagged with
#: :func:`register_policy`.
_POLICY_MARKER = "__saf_policy__"


def register_policy[C: type](cls: C) -> C:
    """Mark ``cls`` as a policy for pack discovery, returning it unchanged.

    The mark is a convenience for pack authors and readers; a pack still
    lists its policies explicitly in :attr:`PolicyPack.policies`.
    """
    setattr(cls, _POLICY_MARKER, True)
    return cls


def is_policy_class(cls: type) -> bool:
    """Return ``True`` if ``cls`` was tagged with :func:`register_policy`."""
    return bool(getattr(cls, _POLICY_MARKER, False))


class PolicyPack(abc.ABC):
    """Base class for a distributable bundle of premium policies.

    Concrete packs set :attr:`id`, :attr:`version`, and :attr:`policies`.
    :meth:`entitlement_key` returns the opaque key the host must hold to
    load the pack; override it to key licensing on something other than the
    default ``"<id>@<version>"``.
    """

    id: ClassVar[str]
    version: ClassVar[str]
    policies: ClassVar[list[type[AddressPolicy]]]

    def entitlement_key(self) -> str:
        """Return the entitlement key the host must be licensed for."""
        return f"{self.id}@{self.version}"


__all__ = [
    "AddressPolicy",
    "PolicyPack",
    "is_policy_class",
    "register_policy",
    "verify_entitlement",
]
