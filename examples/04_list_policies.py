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

"""List the address policies available in the default registry.

Run: ``python examples/04_list_policies.py``
"""

from __future__ import annotations

from structured_address_fix import services


def main() -> None:
    """Print every registered policy's id, tier, and title."""
    print("Available policies:")
    for info in services.list_policies():
        print(f"    {info.id:<20} [{info.tier}] {info.title}")


if __name__ == "__main__":
    main()
