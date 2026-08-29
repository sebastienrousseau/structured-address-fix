#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What the November 2026 cutover costs to prepare for.

The structured-address cliff is a **screening** problem before it is a
fixing one. A bank does not ask "how do I repair this address"; it asks
"how many of the four million addresses I hold will fail, and which
ones". That shape -- everything cheaply, then less work on fewer items --
is what this measures.

The library offers three stages, and they differ by roughly two orders of
magnitude:

* **classify** decides structured / hybrid / unstructured. It is a shape
  test over fields that are already parsed, and it costs well under a
  microsecond. This is the stage you run over everything.
* **assess** applies a policy and produces findings. Single-digit
  microseconds. Run it on what classification flagged.
* **remediate** produces a patch. Tens of microseconds. Run it on what
  assessment said was worth fixing.

The second thing worth measuring is that **cost rises with how broken the
address is**. A fully structured address is cheapest to remediate because
there is least to do; an unstructured one costs roughly twice as much.
That is the opposite of the usual worry -- there is no pathological
input here that explodes -- but it does mean an estate's cost is driven
by its *worst* addresses, not its average, so a portfolio that is 90%
clean is much cheaper than the mean suggests.

Run::

    python benches/bench_address_pipeline.py
    python benches/bench_address_pipeline.py --json
    python benches/bench_address_pipeline.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from structured_address_fix import CanonicalAddress  # noqa: E402
from structured_address_fix.services import facade  # noqa: E402

#: The three shapes the cutover cares about, worst last.
SHAPES: dict[str, CanonicalAddress] = {
    "structured": CanonicalAddress(
        street_name="Baker Street",
        building_number="221B",
        post_code="NW1 6XE",
        town_name="London",
        country="GB",
    ),
    "hybrid": CanonicalAddress(
        town_name="London",
        country="GB",
        post_code="NW1 6XE",
        address_lines=("Flat 2",),
    ),
    "unstructured": CanonicalAddress(
        country="GB",
        address_lines=("Flat 2", "221B Baker Street", "London NW1 6XE"),
    ),
}

STAGES = (
    ("classify", facade.classify_address),
    ("assess", facade.assess_address),
    ("remediate", facade.remediate_address),
)


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def run(quick: bool) -> dict:
    repeats = 200 if quick else 2_000
    rows = []
    for shape, address in SHAPES.items():
        row = {
            "shape": shape,
            "classification": str(facade.classify_address(address)),
        }
        for name, call in STAGES:
            row[f"{name}_us"] = (
                _best(lambda c=call, a=address: c(a), repeats) * 1e6
            )
        rows.append(row)
    return {"rows": rows}


def render(results: dict) -> None:
    rows = results["rows"]
    print(
        f"  {'shape':<14}{'classify us':>13}{'assess us':>12}"
        f"{'remediate us':>15}"
    )
    for row in rows:
        print(
            f"  {row['shape']:<14}{row['classify_us']:>13.2f}"
            f"{row['assess_us']:>12.2f}{row['remediate_us']:>15.2f}"
        )

    worst = rows[-1]
    print(
        f"\n  Three stages, roughly two orders of magnitude apart. Classify "
        f"is a shape test over\n  fields that are already parsed "
        f"({worst['classify_us']:.2f} us), so it is the stage you run over "
        f"the whole\n  estate: a million addresses is well under a second. "
        f"Assess and remediate are for the\n  subset each previous stage "
        f"hands you."
    )

    best_rem = rows[0]["remediate_us"]
    worst_rem = worst["remediate_us"]
    if best_rem:
        print(
            f"\n  Remediation costs {worst_rem / best_rem:.1f}x more for an "
            f"unstructured address than a structured\n  one -- there is "
            f"simply more to do. Nothing here degrades pathologically, but "
            f"it does mean\n  an estate's bill is set by its worst "
            f"addresses rather than its average, so a portfolio\n  that is "
            f"mostly clean is cheaper than the mean would suggest."
        )
    print(
        f"\n  At {worst_rem:.0f} us, remediating a million unstructured "
        f"addresses is about "
        f"{worst_rem * 1_000_000 / 1e6:.0f} seconds\n  of compute. The "
        f"cutover is a data problem, not a throughput one."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="fewer repeats, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
