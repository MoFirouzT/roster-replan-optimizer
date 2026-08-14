"""A committed timing balance, so a documented millisecond cannot rot unnoticed.

## Why this exists, and why it is narrow

`D-092` cut model build time from about 7 ms to about 5 ms, and **six documents went on
quoting 7 ms** — two specs, two studies, `benchmarks.md` and a decision record. Nothing
caught it. The full suite was green, the mutation harness was green, and `test_specs.py`
checks rule IDs, decision IDs and links but has no opinion about numbers.

What the incident actually taught is narrower than "measurements rot", and it is the reason
this file guards one quantity rather than auditing every figure in the repo:

- **Paired ratios did not rot.** Every level-1 study reports *treatment over control on the
  same instance*, and re-running them after `D-092` moved the ratios by about a point and
  changed no verdict. A ratio divides out whatever the shared baseline does.
- **The absolute figure did.** "About 7 ms" is a statement about the baseline itself, so a
  20% change to the baseline falsified it directly.

So the studies' ratios need no guard — they defend themselves. What needs one is the
baseline the prose describes in milliseconds, and the next section is about why that is
still not asserted directly.

## What is asserted is the ratio, not the milliseconds

The obvious guard is a band around the absolute figures, and the first version of this file
was exactly that — with a 40% band, wide enough to survive a slower laptop. It would not
have caught `D-092`, whose shift was 26%. A guard loose enough to be portable is too loose
to detect the thing it exists for, which makes the absolute figure the wrong quantity to
assert on.

**`build / search` is the right one.** It is what the prose actually reasons from — `D-081`
separates the two clocks because build costs more, and `D-093` rejects the compiled-model
cache partly on that balance — and it is far more portable than either number alone, because
a faster machine shrinks both. `D-092` moved it from about 2.3 to about 1.6, a 30% change in
a quantity that hardware largely cancels out of, so a 20% band catches it and tolerates the
laptop.

The milliseconds are still recorded, because they are what the documents quote and a reader
needs something to compare against. They are asserted only against a deliberately loose
sanity band — enough to catch an order-of-magnitude regression, not a machine.

## Two of these are calibrated, and calibrated tests do not travel

`timings.json` was measured on one machine, and the ratio guard is portable *enough* for
another laptop rather than portable in general. A shared CI runner is two to four times
slower at Python and by a different factor at CP-SAT's C++ search, so both quantities move
and the ratio between them moves too. Marked `machine` and deselected in CI (`D-114`);
widening the band instead is the mistake `D-096` already refused.

There is no longer a third test asserting that build outruns search: canonicalisation
levelled the two clocks, and `D-119` retires the claim rather than restating it.

Regenerate deliberately, and say why in `decisions.md`:

    uv run python -m tests.timings --write
"""

from __future__ import annotations

import json
import pathlib
import statistics
import time

import pytest

from benchmarks import suite
from roster_replan.model import build, solve

RECORD = pathlib.Path(__file__).with_name("timings.json")

# The ratio is the real guard: portable across machines, and the quantity the prose reasons
# from. The absolute band is a sanity check only -- see the module docstring.
RATIO_TOLERANCE = 0.20
ABSOLUTE_TOLERANCE = 2.00

CASES = [f"{name}/0" for name in ("headline", "tight", "small", "large", "loose", "scarce-skill")]


def measure() -> dict:
    """Build and search p50 over a fixed set of cases, best of five each.

    Minimum of repeats rather than mean, for the reason `lab.py` gives: wall-clock noise is
    one-sided, so the fastest run is the cleanest estimate of the underlying cost.
    """
    builds, searches = [], []

    for case in CASES:
        instance = suite.build(case).instance
        best_build = min(
            _timed_build(instance) for _ in range(5)
        )
        best_search = min(
            solve(instance, time_limit=30.0).search_seconds for _ in range(5)
        )
        builds.append(best_build)
        searches.append(best_search)

    build_p50 = 1000 * statistics.median(builds)
    search_p50 = 1000 * statistics.median(searches)
    return {
        "build_p50_ms": round(build_p50, 2),
        "search_p50_ms": round(search_p50, 2),
        "build_over_search": round(build_p50 / search_p50, 3),
        "cases": CASES,
    }


def _timed_build(instance) -> float:
    started = time.perf_counter()
    build(instance)
    return time.perf_counter() - started


def load() -> dict:
    return json.loads(RECORD.read_text())


@pytest.mark.machine
def test_the_build_to_search_balance_still_holds():
    """The guard that would have caught `D-092`.

    The failure message names the documents to fix, because the figure lives in prose rather
    than in one constant — and the whole point of the incident this guards against is that
    nobody knew where it was quoted.
    """
    expected = load()["build_over_search"]
    actual = measure()["build_over_search"]
    drift = abs(actual - expected) / expected

    assert drift <= RATIO_TOLERANCE, (
        f"build/search is {actual} against a committed {expected} "
        f"({100 * drift:.0f}% drift).\n\n"
        f"This ratio is what the prose reasons from, so a real shift means the milliseconds "
        f"quoted in docs/benchmarks.md, docs/specs/replan.md and docs/studies/ are now "
        f"wrong. Fix those, then `uv run python -m tests.timings --write` and record why in "
        f"decisions.md."
    )


@pytest.mark.machine
@pytest.mark.parametrize("quantity", ["build_p50_ms", "search_p50_ms"])
def test_the_absolute_timings_are_the_right_order_of_magnitude(quantity):
    """A loose sanity band. Deliberately not the real guard: see the module docstring."""
    expected = load()[quantity]
    actual = measure()[quantity]

    assert abs(actual - expected) / expected <= ABSOLUTE_TOLERANCE, (
        f"{quantity} is {actual} ms against a committed {expected} ms, which is beyond a "
        f"factor this band can explain by hardware alone"
    )


# `test_build_still_dominates_search` was here, and it is deliberately gone (`D-119`).
#
# It asserted the ordering `D-081` and `D-093` reason from — that building the model costs
# more than searching it. Canonicalising the optimum added a second search, and the balance
# went from 1.52 to about 0.985: the two clocks are now level at a one-week horizon. The
# premise is retired rather than re-asserted, because a test that pins a claim the code no
# longer makes is worse than no test.
#
# The ratio guard above still watches the balance, and it is the thing that would notice it
# moving again. `D-116` had already found the crossover sitting between one week and two;
# canonicalisation brought it forward to one.


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="overwrite timings.json")
    args = parser.parse_args()

    current = measure()
    print(json.dumps(current, indent=2))
    if args.write:
        RECORD.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"\nwrote {RECORD}")
