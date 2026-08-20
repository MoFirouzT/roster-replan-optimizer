# How any of this is known to be true

Two independent readings of [`rules.md`](../guide/rules.md), seven test layers over them, and a mutation harness over the layers. Why it is built this way is in [`design.md`](design.md#4-two-readings-of-one-registry).

## The independent checker

`check(roster, instance) -> list[Violation]`. Plain Python. **Imports no solver.** Stateless.

`Violation` carries the rule ID, employee, day, shift, and the observed against the required value.

### What it must not do

Three prohibitions, each a way a well-meaning checker becomes a test of something other than the roster:

1. **Never recompute a caller-supplied quantity.** Not `max_hours_this_week`, not `consecutive_days_worked_before_horizon`, not `flexi_eligible`. A checker that derives its own budget from a reference period it cannot see is testing the caller, and will disagree with the model for reasons that are defects in neither.
2. **Never read the solver's own slack.** `R-COVER`'s shortfall is recounted from the roster, not read from `u`. A checker that trusts the solver's arithmetic is verifying addition.
3. **Never consume the model's eligibility mask.** `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX` are enforced by presolve elimination, so the mask *is* the thing under test.

### Soft violations are still violations

With `R-COVER`'s floor soft and some `R-SKILL-MIX` entries soft, a returned roster can be **optimal and still carry violations**. The checker reports them flagged `soft` and does not treat them as failures.

That changes what the differential harness may assert. `checker_feasible` is nearly always true once a shortfall is representable — the empty roster satisfies every hard rule — so `is_feasible ⟺ is_feasible` would be vacuous. **The harness compares violation sets.**

## The layers

| Layer | Asserts |
| --- | --- |
| Input validation | Malformed payloads rejected with the right field path; a valid payload produces no defects |
| Brute force **(a)** | N ≤ 6, 3 days, ≤ 2 shift types: enumerate every roster, checker hard-feasible set **equals** model feasible set |
| Brute force **(b)** | Same instances: solver objective **equals** enumerated optimum, for every metric D0–D4. The enumeration is scored by `scoring.py`, never by the model |
| Differential | Random rosters, mostly infeasible: `checker_violations(r)` **equals** `model_violations(r)` as sets of `(rule, coordinates)`; a mismatch prints the rule ID |
| Property | Idempotent replan and a fixed point under repetition · identical output under a fixed seed, and one optimum across seeds · monotone objective under rule relaxation · past shifts never modified, including when changing them would help |
| Metamorphic | Employee relabelling leaves the objective invariant; day permutation leaves it invariant **only on a day-decoupled cold instance** |
| Golden | Committed scenarios with committed objective values; a diff fails CI until a decision record justifies it |

**Suite-wide invariant.** Every test producing a solution asserts zero **hard** checker violations on it, and that the solve reached `OPTIMAL`. Soft violations are recorded, not asserted away.

Realised as a shared `solved()` helper rather than enforced automatically, so a test calling the solver directly opts out and should have a reason to. The `OPTIMAL` half matters more than it looks: a test comparing objectives across relaxations or against enumeration is meaningless on a time-limited `FEASIBLE`, and the failure would read as a wrong objective rather than as a truncated search.

### Brute force in two stages

**(a)** compares *feasible sets* and needs only the checker, so it existed as soon as the checker did and catches the large majority of encoding errors: a wrong threshold, an inverted inequality, a forgotten horizon boundary. **(b)** adds the objective assertion.

Stage (a) is not a weaker version of the gate; it is the half that does not need preference to be defined.

Stage (b) needs a **second, independent reading of the objective** for the same reason (a) needs one of the rules: an enumeration that asks the model what a roster is worth proves only that the model agrees with itself. `scoring.py` is forbidden by contract from importing the model's encoding.

**Stage (b) needs an instance whose incumbent contains a presolved-away pair, and did not have one at first.** Because presolve removes ineligible pairs, an employee who *became* unavailable has no variable — so the drop the replan exists to perform was invisible to the objective, and the model understated it. Every micro-instance happened to have a clean incumbent, so the layer passed while the bug was live. **A ground-truth layer only covers the structures its instances contain.**

### The instance set, and how its gaps were found

Thirty-nine committed micro-instances in `tests/micro_instances.py` — Python constructors rather than a serialised format, because a schema and a loader belong with the benchmark set. Each exercises a *structure* rather than looking realistic, with `employees × open_shifts ≤ 10` so enumeration stays affordable. The bound is asserted rather than reviewed: an oversized instance would not fail, it would only make the suite slow, and a slow enumeration layer is one that eventually gets deleted instead of fixed.

Every instance runs on a **seven-day horizon** even where two shifts are open. `R-WEEKLY-REST` needs its 35-hour window inside the horizon, so on a three-day instance the rule binds everywhere for a reason belonging to the horizon rather than the roster. Lowering the parameter instead would demand a derogation basis — and inventing a legal citation to quiet the validator is exactly the dishonesty the registry exists to prevent. Enumeration cost does not depend on `days`, so the long horizon is free.

**Threshold instances exist because mutation testing found the set blind without them.** The three main shift types sit on an eight-hour grid, so every gap they can produce is 0, 8 or 16 hours — and a rest threshold of 9 hours is indistinguishable from 11. Lowering `min_rest_hours` in the model passed every ground-truth test in the suite. Probing each threshold in turn found the same blindness in the weekly budget, the daily maximum, and the gross-versus-net distinction, which only shows up for a budget in `[15.0, 16.0)`.

Five instances now bracket their thresholds from both sides. The lesson generalises past this project: **a fixture set proves a rule exists; only a fixture at the boundary proves it is enforced at the right number.**

### What the golden layer catches that brute force cannot

Stage (b) compares two independent readings, so it is blind to anything both readings take as *data* — the objective weights above all. Changing `published_weight` from 10 to 12 leaves both readings agreeing perfectly about a different optimum, and every ground-truth test passes.

The golden record catches exactly that class. Verified by mutation rather than assumed: that weight change fails the golden layer and nothing else.

```bash
uv run python -m tests.golden --write
```

Regenerate deliberately, and justify the diff.

**Rosters are recorded only where the optimum is unique**, which enumeration settles at generation time. Interchangeable employees create ties, and a tied optimum's roster is a function of solver version and search order rather than of the specification — committing one would produce failures that are not defects, and would train everyone to regenerate without reading the diff.

### Building the differential harness

Feasibility-checking a fixed roster in CP-SAT is fixing all variables and solving, so the harness is small.

`model_violations(r)` needs the model to **report** rather than merely refuse: fix all assignment variables to `r`, solve, and read which assumption literals appear in the core. A model that only answers `INFEASIBLE` can be differentially tested against a checker's feasibility bit and nothing more, and that comparison is the vacuous one.

Random rosters are biased toward *nearly* feasible ones. Uniformly random assignments violate `R-COVER` immediately and never exercise the interesting rules, so generation perturbs solved rosters: swap two assignments, move one shift, drop a person.

### Day permutation is conditional, and the condition is not small

Three couplings make unconditional day permutation false:

- `R-REST-GAP` and `R-WEEKLY-REST` constrain adjacent and consecutive days.
- `R-CONSEC-DAYS` counts runs, and `{0,1,2}` is one run of three where `{0,2,4}` is three runs of one.
- D1 and D2 read publication state and notice from absolute start times, so permuting days reprices every change.

The relation holds under stated preconditions: one shift type per day separated by more than `min_rest_hours`, no consecutive-day limit, weekly rest loose enough not to bind, and a **cold** solve, where the objective is cost plus the peak tie-breaker and neither reads the calendar.

The negative case is committed too: one employee and two *adjacent* days with `max_consecutive_days = 1` must leave a shift unstaffed, while the same two shifts moved apart are both coverable. That test exists so the preconditions cannot later be dropped as apparent boilerplate.

### Relaxation monotonicity excludes coverage

Relaxing a *rule* expands the feasible set without touching the objective function, so the optimum can only improve or hold. Relaxing **coverage** changes the objective itself through the shortfall term, so it is not a relaxation in this sense and comparing optima across it is meaningless.

A monotonicity suite in which every relaxation is inert passes vacuously, so one test asserts that at least one relaxation actually moves the objective.

<a id="two-stated-comparison-rules"></a>
### Two stated comparison rules

The two readings do not report at identical granularity everywhere. Pretending otherwise would either weaken the harness to rule level or produce failures that are not defects. **Neither narrowing may be widened without a decision record.**

**`R-CONSEC-DAYS` is compared at `(rule, employee)`, dropping the day.** The checker names the first breaching day of a run; the model gates every sliding window that breaches, so a long run produces one finding on one side and several on the other. *Cost:* a day-coordinate error in this one rule is not caught by the harness.

**Rosters that assign a presolved-away pair are compared on eligibility findings only.** This is the larger of the two and it took a failing test to state correctly. Such an assignment is not representable in the model at all, and the consequence is broader than coverage: the model cannot count that body toward headcount, toward weekly or daily hours, toward a streak, or toward a rest gap. Every aggregating rule is affected. The only thing the model has an opinion about is *why the pair was excluded*.

*Cost:* nothing aggregate is compared on those rosters. It is bought back by comparing the two eligibility derivations directly — pair by pair, over every instance variant, for `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX`. That is stronger than a headcount comparison, because it localises a disagreement to the eligibility rule that caused it rather than surfacing it as a coverage mismatch three rules away.

## The mutation harness

**A layer that has never been shown to fail is not known to work.** `tests/mutation.py` writes a deliberate defect into the source, runs the suite, and checks that the layer *named by the mutant* is the one that objects — so it answers *can this layer see this defect* rather than the weaker *does anything fail*. A layer without a mutant is a layer nobody has shown to work, and **adding a layer means adding a mutant**.

```bash
uv run python -m tests.mutation
```

It rewrites source files, so it is not part of the normal suite. A full run is about 14 minutes; a single layer (`-k service`) takes seconds and is the cheap way to settle one doubtful result.

**Read the verdict from `tests/mutation-report.json`, never from the terminal.** Reading a run's result through a pipe has twice destroyed it: `tail` truncates the per-mutant lines *and* reports its own exit status, so a run that leaked a mutated file into the working tree read as a clean pass.

```bash
jq .verdict tests/mutation-report.json
```

Four answers:

| Verdict | Means |
| --- | --- |
| `clean` | Every mutant was caught by the layer that should have caught it, in a tree the run could vouch for |
| `survivors` | A mutant went uncaught. **Worth one check before believing it** — apply it by hand and confirm it fails, rather than writing a test for ground that may already be covered |
| `unverifiable` | Every mutant was caught and **the run could not vouch for the tree it ran in**. `unvouched_for` names the paths. Diff them by hand, or re-run |
| `leaked` | The run is **void**, not passing-with-a-caveat: every mutant after the leak may have been caught by the leftover defect. `git checkout --` the named paths; format-on-save is the usual culprit |

A late write does not cost a whole re-run. Only the mutants touching the named paths are in doubt, so re-run that layer alone — **and send it somewhere else with `--report`**, or a five-mutant report replaces the hundred-mutant one it was meant to repair:

```bash
uv run python -m tests.mutation -k service --report /tmp/service-rerun.json
```

This has found four blind spots so far, each behind a fully green suite, and it has been confidently wrong about itself five times — each one a hardening. [`mutation-harness.md`](../archive/studies/mutation-harness.md)

---

*Why the two readings share a schema but never a threshold: [`design.md`](design.md#4-two-readings-of-one-registry). The four blind spots and the five hardenings: [`decisions.md`](../archive/decisions.md#by-theme), under* Ground truth, test layers, and the mutation harness.
