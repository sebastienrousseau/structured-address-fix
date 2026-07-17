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

"""Apply patch operations to an ISO 20022 document.

A thin, explicit seam over :func:`structured_address_fix.adapters.
xml_writer.apply_operations` so that producing a patched document is a
separate, deliberate step from proposing the patch — payments are only
ever transformed on request, never as a side effect of assessment.
"""

from __future__ import annotations

from collections.abc import Sequence

from structured_address_fix.adapters.xml_writer import apply_operations
from structured_address_fix.domain.remediation import PatchOperation


def apply(xml: str, operations: Sequence[PatchOperation]) -> str:
    """Return ``xml`` with ``operations`` applied.

    With no operations the document is returned unchanged (the adapter
    round-trips it); otherwise each operation is applied to the element
    its JSON pointer addresses.
    """
    if not operations:
        return xml
    return apply_operations(xml, operations)
