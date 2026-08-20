# Quickstart

```bash
uv sync
uv run python -m roster_replan.demo scenarios/saturday_sick_call.json
```

This prints:

```text
tenant horeca-demo, profile horeca-2026.1
12 staff, 21 open shifts, 35 assignments published
replanning at hour 129 of the horizon

answer: exact — proven optimal
disruption 100040, gap 0.0%
solved in 14 ms

1 changed assignment(s):
  dropped    E02  Sat 15:00-23:00 (E)

Sat 15:00-23:00 (E) is 1 short of its 3 required staff.
  6 of the 12 staff do not hold a skill the shift requires (R-SKILL).
  5 of the 12 staff would not get the minimum rest between shifts (R-REST-GAP).
  4 of the 12 staff are absent or unavailable then (R-AVAIL).
  4 of the 12 staff would exceed their hours for the day (R-MAX-DAILY).
  E01, E05 and E08 would exceed their hours for the week (R-MAX-WEEKLY).

Cheapest single overrides that would fill Sat 15:00-23:00 (E):
  operational:
    E09  ignore kitchen skill             disruption +40
    E06  ignore kitchen skill             disruption +40
  statutory:
    E05  raise weekly-hours cap by 8h     disruption +40
```

The scenario file is the real wire format, so it doubles as the worked example of what a caller sends.
The shortfall is the honest outcome:
E02 called in sick and **nobody could legally replace them**; the explanation says why, person by person, and every line is derived rather than phrased by a model.

> **The recommendation list ranks who is closest, then checks the ranking by solving.**
> `Shortfall.by_employee()` sorts the excluded staff by how many hard rules block each one, fewest first is just a hint, since a single blocker is cheaper to override than several, not a guarantee that overriding it actually works.
> `whatif.recommend()` checks each single-blocker candidate by re-solving a disposable copy of the instance and keeps only the ones that close the shift.
> **The ranking is within a provenance, not across one** ([`D-144`](decisions.md#d-144)). Ignoring a skill requirement is a call the planner already owns; asking somebody to work further into a budget a statute caps is a different kind of ask, and being 40 points cheaper does not make it the one to try first. Nothing unlawful gets this far — a cap above the absolute ceiling is refused by `validate_instance` and the candidate never appears — but lawful is not the same as equivalent, so the two groups are printed apart rather than interleaved by a number that cannot decide between them.
> Nothing is applied:
> the real instance and roster are untouched, and *ignoring* a rule for one solve is not the same as changing that employee's real record.

This is one scenario, not the 84-case benchmark set. That reproduction is in
[`benchmarks.md`](benchmarks.md).

To run the test suite or contribute, see [`development.md`](development.md).
