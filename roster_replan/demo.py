"""One scenario, end to end, printed for a human.

    uv run python -m roster_replan.demo scenarios/horeca/saturday_sick_call.json

T0's gate was *something solves, and the output is inspectable by eye*, and nothing since
has been inspectable by eye — the suite asserts, the benchmarks tabulate, and the service
returns JSON. This is the one place the whole stack is visible at once: a published week, a
disruption, the repair, and why anything left short is left short.

It takes a **payload file** rather than a scenario name, which keeps `roster_replan` free of
`benchmarks` — the generator is not a runtime dependency — and has a second benefit worth
more: the file is the actual wire format, so the demo doubles as the worked example of what
a caller sends.

Nothing here is a separate code path. It calls the same ladder the service calls and renders
with the same `prose.py` the API returns, so a demo that looks right is evidence about the
product rather than about the demo.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .explain import explain
from .ladder import answer
from .prose import render_all, slot
from .service.contracts import ReplanRequest, to_domain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=pathlib.Path, help="a replan request, as JSON")
    parser.add_argument(
        "--weekday-of-day-zero",
        type=int,
        default=None,
        help="0 for Monday. Without it, days are printed by index — the domain has no calendar",
    )
    parser.add_argument("--budget-seconds", type=float, default=30.0)
    args = parser.parse_args(argv)

    if not args.payload.exists():
        print(f"no such payload: {args.payload}", file=sys.stderr)
        return 2

    request = ReplanRequest.model_validate_json(args.payload.read_text())
    instance = to_domain(request.instance)
    incumbent = instance.incumbent or frozenset()

    print(f"tenant {request.tenant}, profile {request.profile_version}")
    print(
        f"{len(instance.employees)} staff, {len(instance.open_shifts)} open shifts, "
        f"{len(incumbent)} assignments published"
    )
    print(f"replanning at hour {instance.now:g} of the horizon\n")

    result = answer(instance, seed=request.seed, budget_seconds=args.budget_seconds)

    print(f"answer: {result.rung} — {result.reason}")
    if result.objective is not None:
        print(f"disruption {result.objective}, gap {100 * (result.gap or 0):.1f}%")
    print(f"solved in {1000 * result.seconds:.0f} ms\n")

    changed = sorted(result.roster ^ incumbent)
    if not changed:
        print("nothing changed.")
    else:
        print(f"{len(changed)} changed assignment(s):")
        for employee, day, shift in changed:
            action = "called in " if (employee, day, shift) in result.roster else "dropped   "
            where = slot(instance, day, shift, weekday_of_day_zero=args.weekday_of_day_zero)
            print(f"  {action} {instance.employees[employee].name}  {where}")

    print()
    print(
        render_all(
            explain(result.roster, instance),
            instance,
            weekday_of_day_zero=args.weekday_of_day_zero,
        )
    )

    if result.violations:
        # Only reachable on the `incumbent` rung, where returning a broken roster is the
        # point. Loud, because a returned roster that breaks a hard rule is the worst
        # outcome this system can produce and must never be read past.
        print(f"\nWARNING: this roster breaks {len(result.violations)} hard rule(s):")
        for rule, employee, day, shift in result.violations:
            print(f"  {rule} employee={employee} day={day} shift={shift}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
