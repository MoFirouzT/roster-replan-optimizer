# Quickstart

```bash
uv sync
uv run python -m roster_replan.demo scenarios/saturday_sick_call.json
```

E02 has called in sick for a Saturday evening shift. The roster for the rest of the week is already published.

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

## What you are looking at

**One assignment changed.** Everyone else keeps the shift they were told about. That is the whole point of the service: it reproduces the published roster with the least deviation from it, rather than re-solving the week for the cheapest legal answer.

**The shift stays short, and that is the honest outcome.** Nobody could legally replace E02. Coverage is a priced floor rather than a hard requirement, so the solver returns a roster one person short instead of returning nothing — and then says why, person by person, against the rule that blocked each one.

**Every line of the explanation is derived.** The blocker counts come from the checker re-verifying the roster; the overrides come from re-solving a disposable copy of the instance. No model wrote any of it.

**Overrides are grouped by where the rule's authority comes from, never ranked across the groups.** Ignoring a skill requirement is a call the planner already owns. Asking somebody to work further into a budget a statute caps is a different kind of ask, and being no more expensive does not make it the one to try first.

## The scenario file

`scenarios/saturday_sick_call.json` is the real wire format, so it doubles as a worked example of what a caller sends. [`api.md`](api.md) describes it field by field.

## Next

- Using the service — [`configuring.md`](configuring.md), then [`api.md`](api.md).
- The rules it enforces — [`rules.md`](rules.md).
- What it guarantees and where it stops — [`limits.md`](limits.md).
- Changing the code — [`design.md`](../internals/design.md).
