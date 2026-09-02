# Development

Running the suite, the contracts CI enforces, and the one script that costs money. What the layers actually prove is in [`testing.md`](testing.md).

## Running the suite

Two commands, and CI runs both on every push:

```bash
uv run pytest -q
```

```bash
uv run lint-imports
```

The second is the eleven contracts that carry the independence rule: the model and the checker never reaching each other's rule logic, the greedy baseline staying solver-free, the service never importing a language model.

The two run in **separate workflows**, `tests.yml` and `ci.yml`, and that is about the badge rather than about the build: a GitHub badge covers a whole workflow, so the suite has to be alone in one for `README.md`'s tests badge to mean the tests and not also the doc linter. `ci.yml` keeps the contracts and the doc lint.

CI runs pytest with `-m "not machine"`, which drops the three timing guards calibrated to this hardware. Everything else runs everywhere, including the benchmark manifest's solved half: that one was deselected too until the optimum became canonical and stopped carrying the build that produced it.

The mutation harness is separate and deliberate; see [`testing.md`](testing.md#the-mutation-harness).

## Repository map

```text
roster_replan/
  domain.py              the only module model and checker may both import
  model.py               the CP-SAT formulation: one reading of the registry
  checker.py             the independent second reading; imports no solver
  disruption.py          the objective
  scoring.py             its independent evaluation, forbidden from importing the model
  repair.py              the greedy baseline, solver-free by contract
  ladder.py              exact → time-boxed → greedy → last known good
  explain.py  core.py  prose.py    why a shift is short, minimal cores, planner language
  whatif.py              hypotheticals and override recommendations
  validation.py          input validation
  profile.py  nl.py      the tenant profile, and the only stage that needs a model
  service/               async job API, contracts, tool surface

benchmarks/
  generator.py           seeded instance generator
  manifest.json          the committed set, as seeds and fingerprints
  milp.py                the MILP formulation, built to be compared against
  anneal.py              the penalty-search rival, solver-free by contract
  foreign.py             the imported nurse-rostering instances
  nl_eval.py             the parse against free-form text: needs a key, so not in the suite

tests/
  micro_instances.py     29 structures, small enough to enumerate
  test_ground_truth.py   exhaustive ground truth
  test_differential.py   model ⟺ checker
  test_properties.py     invariants
  test_golden.py         committed scenarios and objective values
  test_specs.py          the checkable half of "the documentation is true"
  mutation.py            deliberate defects, each naming the layer that must catch it

scenarios/               demo data: domain specificity lives here, not in the code
```

Module docstrings carry the argument for each module's shape and name the document they implement.

## The one script that costs money

Everything above runs with no API key. One script does not:

```bash
cp .env.example .env
```

```bash
uv sync --extra nl
```

```bash
uv run python -m benchmarks.nl_eval --free-form -k rest-plain
```

That is one call and a few cents. The full run is 18 calls and well under a dollar:

```bash
uv run python -m benchmarks.nl_eval
```

It is a script rather than a test because it costs money, and because a result that depends on a model does not belong in a suite that must be reproducible.

## What the model is trusted to do, on a manager's own words

Captured once against text messier than anything in the eval suite, so the capability can be read rather than re-run. The input is a manager's weekly debrief: two roster complaints, an aside about a colleague, and three policy statements buried inside it: one of which contradicts another.

```text
Last week was rough. Sarah closed Thursday and opened Friday and was clearly exhausted, David
keeps asking for more weekend shifts, and honestly Saturday evening felt understaffed the whole
night. Going forward, staff need at least eleven hours between shifts, no exceptions. Also, if we
change someone's shift with less than a day's notice, that should count as four times worse than a
change we give them plenty of warning for. And I know it's tight, but let's allow eight hours
between shifts on Sundays going forward, we just don't have the staff.
```

`nl.propose()` runs all four stages and stops short of saving anything:

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

Three things worth reading in that transcript rather than past it.

**The roster complaints extracted nothing, and nothing was invented in their place.** Sarah, David and Saturday's understaffing are real sentences about a real week, and `StatedPolicy` has no field for any of them: they are not policy, so nothing fires. That silence is the schema working as designed.

**The eleven-hour rule was accepted, and the caller was still told it does nothing.** A manager who says *eleven hours, no exceptions* believes that is a live constraint. The subsumption check found the gap between same-time shifts on consecutive days is already 16 hours, so the rule cannot ever bind. That is not a rejection; it is the profile telling the tenant their protection is inert, which is exactly the failure profile review exists to catch before it reaches a Saturday roster.

**The Sunday exception never reached the profile at all.** It has no cited legal basis, and `min_rest_hours` is a single week-wide figure: there is nowhere in the schema to write a day-scoped carve-out. Run twice, the model handled that clause two different ways: once by naming the contradiction explicitly in `unclear`, once by dropping it without comment. Neither run wrote an unlawful figure or invented a field the schema does not have, which is the confinement argument holding on live, unscripted text even though the two runs disagree on how loudly to say so.

Reproduce it with a policy sentence of your own: `nl.propose(text, client, version=..., sample=instance)`, with `client` from `benchmarks.nl_eval._client()` and `instance` from any scenario in `scenarios/`.

## Writing documentation

The live documentation is [`../guide/`](../guide) for people using the service and [`../internals/`](.) for people changing it. It is short on purpose.

**Reasoning goes in [`decisions.md`](../decisions.md), not in a live document.** A decision record is permanently true and is amended in place with the supersession named, never rewritten. A live document is present tense and says what is so now.

**A component is not done until its documentation matches its code.** When they diverge, decide which is wrong and fix that one.

`tests/test_specs.py` checks the mechanical half: every rule in the registry exists in both readings, every decision ID cited anywhere resolves to a record, every relative link and every fragment lands somewhere real.

---

*Prose conventions and the plain-word rule: [`CLAUDE.md`](../../CLAUDE.md).*
