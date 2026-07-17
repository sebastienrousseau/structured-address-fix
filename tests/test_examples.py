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

"""Every ``examples/*.py`` script must run to a clean exit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).parents[1] / "examples"
_SCRIPTS = sorted(_EXAMPLES_DIR.glob("*.py"))


def test_examples_directory_is_populated() -> None:
    """Guard against the glob silently matching nothing."""
    assert _SCRIPTS, "no example scripts were discovered"


@pytest.mark.parametrize("script", _SCRIPTS, ids=[s.name for s in _SCRIPTS])
def test_example_runs_cleanly(script: Path) -> None:
    """Run the example as a subprocess and assert exit code 0."""
    completed = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, (
        f"{script.name} exited {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert completed.stdout.strip(), f"{script.name} produced no output"
