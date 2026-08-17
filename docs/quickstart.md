# Quickstart

```bash
uv sync
uv run python -m roster_replan.demo scenarios/saturday_sick_call.json --weekday-of-day-zero 0
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
```

The scenario file is the real wire format, so it doubles as the worked example of what a caller
sends. The shortfall is the honest outcome: E02 called in sick and **nobody could legally replace
them** — the explanation says why, person by person, and every line is derived rather than phrased
by a model.

This is one scenario, not the 84-case benchmark set. That reproduction is in
[`benchmarks.md`](benchmarks.md).

## Running the suite

The suite and the import contracts are the two things CI runs on every push:

```bash
uv run pytest -q          # 766 tests, about a minute
uv run lint-imports       # the 10 contracts that carry the independence rule
```

CI runs the first with `-m "not machine"`, which drops the three timing guards calibrated to this
hardware ([`D-114`](decisions.md)). Everything else runs everywhere, including the benchmark
manifest's solved half — that one was deselected too until the optimum became canonical and stopped
carrying the build that produced it ([`D-119`](decisions.md), [`D-121`](decisions.md)).

## The one script that costs money

Everything above — and the whole test suite — runs with no API key. One script does not:

```bash
cp .env.example .env          # paste a key into it; .env is gitignored
uv sync --extra nl
uv run python -m benchmarks.nl_eval --free-form -k rest-plain   # one call, a few cents
uv run python -m benchmarks.nl_eval                             # 18 calls, well under a dollar
```

That is the natural-language parse measured against text its author did not render
([`D-102`](decisions.md)). It is a script rather than a test because it costs money and because a
result that depends on a model does not belong in a suite that must be reproducible.
