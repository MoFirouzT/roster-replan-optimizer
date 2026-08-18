# Development

For what this project is and how to see it work, start with [`quickstart.md`](quickstart.md).
This is the workflow for running the suite and contributing.

## Running the suite

The suite and the import contracts are the two things CI runs on every push:

```bash
uv run pytest -q          # 949 tests, about 2 minutes
uv run lint-imports       # the 11 contracts that carry the independence rule
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

## What the model is trusted to do, on a manager's own words

`quickstart.md` shows the deterministic half of this project: a scenario in, a repair and an
explanation out, nothing derived by a model. This is the other half — [`roster_replan/nl.py`](../roster_replan/nl.py)'s
policy parse — captured once against text messier than anything in the eval suite, so the
capability can be read rather than re-run.

The input is a manager's weekly debrief: two roster complaints, an aside about a colleague, and
three policy statements buried inside it — one of which contradicts another.

```text
Last week was rough. Sarah closed Thursday and opened Friday and was clearly exhausted, David
keeps asking for more weekend shifts, and honestly Saturday evening felt understaffed the whole
night. Going forward, staff need at least eleven hours between shifts, no exceptions. Also, if we
change someone's shift with less than a day's notice, that should count as four times worse than a
change we give them plenty of warning for. And I know it's tight, but let's allow eight hours
between shifts on Sundays going forward, we just don't have the staff.
```

`nl.propose()` runs all four stages of `config.md` — parse, convert, contradiction/subsumption
check, and a feasibility probe against a real week — and stops short of saving anything:

```text
=== stated (extracted fields only) ===
  min_rest_hours: 11.0
  short_notice_hours: 24.0
  short_notice_multiplier: 4

=== verdict ===
Accepted as candidate (2 remark(s)).

=== remarks ===
  params.min_rest_hours: a rest gap of 11h is shorter than the 16h that separates two same-time
    shifts on consecutive days, so it never binds on a daily pattern
  disruption.cost_weight: cost_weight is 0, so cost is switched off entirely and the objective is
    pure disruption

=== probe (solved against scenarios/saturday_sick_call.json) ===
Probe(solved=True, shortfall=1, blocking=('R-AVAIL', 'R-MAX-DAILY', 'R-MAX-WEEKLY', 'R-REST-GAP',
  'R-SKILL'))
```

Three things worth reading in that transcript rather than past it:

**The roster complaints extracted nothing, and nothing was invented in their place.** Sarah,
David and Saturday's understaffing are real sentences about a real week, and `StatedPolicy` has no
field for any of them — they are not policy, so nothing fires. Nothing here would tell a caller
"3 roster notes were dropped"; that silence is the schema working as designed, not a gap in it.

**The eleven-hour rule was accepted, and the model still told the caller it does nothing.** A
manager who says "eleven hours, no exceptions" believes that is a live constraint. Stage 3
(`remarks()`) checked it against the shift catalogue and found the gap between same-time shifts on
consecutive days is already 16 hours — the rule the manager just stated cannot ever bind. That
is not a rejection; it is the profile telling the tenant their protection is inert, which is
exactly the failure `profile.py` exists to catch before it reaches a Saturday roster.

**The Sunday exception never made it into the profile at all.** It has no cited legal basis, and
`min_rest_hours` is a single week-wide figure — there is nowhere in the schema to write a
day-scoped carve-out. Run twice, the model handled that clause two different ways: once by naming
the contradiction explicitly in `unclear`, once by dropping the clause without comment. Neither run
wrote an unlawful figure or invented a field the schema does not have — which is `D-101`'s
confinement argument holding on live, unscripted text, even though the two runs disagree on how
loudly to say so.

Reproduce it (one call, a few cents) with a policy sentence of your own — `uv run python -c` and
`nl.propose(text, client, version=..., sample=instance)`, `client` from `benchmarks.nl_eval._client()`
and `instance` from any scenario in `scenarios/`.
