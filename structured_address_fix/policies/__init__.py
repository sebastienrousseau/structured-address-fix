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

"""The policy layer: the address-policy contract and its built-ins.

Re-exports the policy protocol and context, the registry types, and the
four open-source policies so callers can import everything they need from
``structured_address_fix.policies``.
"""

from structured_address_fix.policies.base import (
    AddressPolicy,
    BasePolicy,
    PolicyContext,
    PolicyTier,
)
from structured_address_fix.policies.cbpr_2026 import Cbpr2026Policy
from structured_address_fix.policies.generic_structured import (
    GenericStructuredPolicy,
)
from structured_address_fix.policies.hvps_plus import HvpsPlusPolicy
from structured_address_fix.policies.registry import (
    PolicyInfo,
    PolicyRegistry,
    default_registry,
    load_plugins,
)
from structured_address_fix.policies.sepa import SepaPolicy

__all__ = [
    "AddressPolicy",
    "BasePolicy",
    "Cbpr2026Policy",
    "GenericStructuredPolicy",
    "HvpsPlusPolicy",
    "PolicyContext",
    "PolicyInfo",
    "PolicyRegistry",
    "PolicyTier",
    "SepaPolicy",
    "default_registry",
    "load_plugins",
]
