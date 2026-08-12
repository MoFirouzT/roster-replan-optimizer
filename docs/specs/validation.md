# Validation

Two independent layers, often confused, with different jobs:

- **Input validation** — is this payload well-formed and lawful *as a request*? Runs before any solve.
- **The checker** — does this roster satisfy the rules? Runs on every solution the suite produces.

Conflating them is how a caller's arithmetic error gets reported as a solver defect. The dividing
question is whether the fault could be fixed by a different roster. If no roster could fix it, it is
input validation.

## Input validation

`validate_instance(instance) -> list[InputDefect]`. Runs at profile load and at the head of every
solve. A non-empty result rejects the request; it never degrades into a best-effort solve, because a
request that is not well-formed has no meaningful optimum.

What lands here, and why each is *not* a roster property:

| Check | Why not the checker |
|---|---|
| `R-MIN-SHIFT` — every shift type meets the minimum period | No reachable roster can violate it; the catalogue either does or does not. See `rules.md` |
| `max_hours_this_week[e]` within the absolute weekly ceiling | A too-large budget is a bad payload. Reporting it as `R-MAX-WEEKLY` blames the solver for the caller's arithmetic |
| `max_daily_hours[e]` within the lawful derogation ladder | Same shape: the ceiling is a property of the contract, not of the assignment |
| A derogated parameter carries a non-empty `derogation_basis` | A legality claim with no source is the thing `rules.md` exists to prevent |
| A legal `R-SKILL-MIX` entry carries a provenance string | As above, per entry |
| `now` and the incumbent are both present, or both absent | A replan missing either is malformed, not defaulted — see `R-PIN-PAST` |
| `flexi_eligible` / `dimona_ok` present for every flexi employee | Absence must never default to `true`; that would invent an eligibility the NSSO did not grant |
| Every rule parameter is supplied explicitly | The independence rule forbids central defaults for rule thresholds |
| Horizon begins at or after `now` on a cold solve | Otherwise `R-PIN-PAST` has past shifts and no incumbent to pin them to |

`InputDefect` carries the offending field path, the observed value, and the constraint it broke. It is a
distinct type from `Violation`: the two are never mixed in one list, because they have different
audiences — a caller fixes a defect, a planner reads a violation.

## The independent checker

`check(roster, instance) -> list[Violation]`. Plain Python. **Imports no solver.** Stateless.

A second reading of [`rules.md`](rules.md), written without reference to the model implementation.
Shares the payload schema and the stated conventions with the model, and **shares no rule predicate or
threshold** — see [the independence rule](rules.md#independence-rule) for exactly where that line falls
and why it is not "shares no code". Enforced by an import-linter contract in CI, plus a review
obligation the linter cannot discharge.

Structurally required, not a nice-to-have: under any formulation without hard-constraint guarantees
(penalties inside a local search, or a time-boxed solve accepting a gap), feasibility is not guaranteed
by construction. Independent verification is the only thing that makes a legality claim true rather
than assumed.

`Violation` carries: rule ID, employee, day, shift, and the observed vs. required values.

### Soft violations are still violations

With `R-COVER`'s floor soft and some `R-SKILL-MIX` entries soft, a returned roster can be *optimal* and
still carry violations. The checker reports them, flagged `soft`, and does not treat them as failures.

This changes what the differential harness may assert. `checker_feasible` is nearly always true once a
coverage shortfall is representable — the empty roster satisfies every hard rule — so an
`is_feasible ⟺ is_feasible` assertion would be vacuous. **The harness compares violation sets.**

### What the checker must not do

Three prohibitions, each corresponding to a way a well-meaning checker becomes a test of something
other than the roster:

1. **Never recompute a caller-supplied quantity.** Not `max_hours_this_week`, not
   `consecutive_days_worked_before_horizon`, not `flexi_eligible`. A checker that derives its own budget
   from a reference period it cannot see is testing the caller, and will disagree with the model for
   reasons that are defects in neither.
2. **Never read the solver's own slack.** `R-COVER`'s shortfall is recounted from the roster, not read
   from `u`. A checker that trusts the solver's arithmetic is verifying addition.
3. **Never consume the model's eligibility mask.** `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and
   `R-DIMONA-FLX` are all enforced by presolve elimination, so the mask *is* the thing under test.

## Test layers

| Layer | Asserts |
|---|---|
| Input validation | Malformed payloads rejected with the right field path; a valid payload produces no defects |
| Brute force **(a)** | N≤6, 3 days, ≤2 shift types: enumerate every roster, `checker` hard-feasible set **equals** model feasible set |
| Brute force **(b)** | Same instances: solver objective **equals** enumerated optimum, for every metric D0–D4. The enumeration is scored by `scoring.py`, never by the model |
| Differential | Random rosters (mostly infeasible): `checker_violations(r)` **equals** `model_violations(r)`, as sets of `(rule, coordinates)`; mismatch prints the rule ID |
| Property | Idempotent replan on a no-change input, and a fixed point under repetition · identical output under a fixed seed, and one optimum across seeds · monotone objective under rule relaxation · past shifts never modified, including when changing them would help |
| Metamorphic | Employee relabelling leaves the objective invariant; day permutation leaves it invariant **only on a day-decoupled cold instance** — see below |
| Golden | Committed scenarios with committed objective values; a diff fails CI until a `decisions.md` entry justifies it |

**Suite-wide invariant:** every test that produces a solution asserts zero **hard** checker violations on
it, and that the solve reached `OPTIMAL`. Soft violations are recorded, not asserted away.

Realised as a shared `solved()` helper rather than enforced automatically — so a test calling the solver
directly opts out, and should have a reason to. The `OPTIMAL` half matters more than it looks: a test
comparing objectives across relaxations or against enumeration is meaningless on a time-limited
`FEASIBLE`, and the failure would read as a wrong objective rather than as a truncated search.

### Brute force lands in two stages

The gate in `PLAN.md` reads "solver objective equals enumerated optimum", which needs an objective — and
the disruption metric is specified late in T1. As written the gate depended on an artifact scheduled
after it.

Rather than pull the metric forward, the layer splits. **(a)** compares *feasible sets* and needs only
the checker, so it was available as soon as the checker existed and catches the large majority of
encoding errors: a wrong threshold, an inverted inequality, a forgotten horizon boundary. **(b)** adds
the objective assertion. Stage (a) is not a weaker version of the gate; it is the half that does not need
preference to be defined.

**Both stages are now in.** Stage (b) requires a second, independent reading of the *objective* for the
same reason stage (a) needs one of the rules: an enumeration that asks the model what a roster is worth
proves only that the model agrees with itself. `scoring.py` evaluates `replan.md` directly and is
forbidden by contract from importing the model's encoding.

**Stage (b) needs an instance whose incumbent contains a presolved-away pair**, and did not have one at
first. Because presolve removes ineligible pairs, an employee who *became* unavailable has no variable —
so the drop that the replan exists to perform was invisible to the objective, and the model understated
it. Every micro-instance happened to have a clean incumbent, so the layer passed while the bug was live.
The regression case is committed; the general lesson is that a ground-truth layer only covers the
structures its instances contain.

### Building the differential harness

Feasibility-checking a fixed roster in CP-SAT is fixing all variables and solving, so the harness is
small. Build it early.

`model_violations(r)` needs the model to *report* rather than merely refuse. Fix all assignment
variables to `r`, solve, and read which assumption literals appear in the infeasibility core — the same
machinery the T4 explainer uses, which is the second reason the assumption literals in `rules.md` are
not optional. A model that only answers `INFEASIBLE` can be differentially tested against a checker's
feasibility bit and nothing more, and that comparison is the vacuous one.

Random roster generation should be biased toward *nearly* feasible rosters. Uniformly random assignments
violate `R-COVER` immediately and never exercise the interesting rules, so generate by perturbing solved
rosters: swap two assignments, move one shift, drop a person.

### Day permutation is conditional, and the condition is not small

This table previously claimed day permutation "stays structure-consistent" without qualification. **That
is false**, and three separate couplings make it so:

- `R-REST-GAP` and `R-WEEKLY-REST` constrain adjacent and consecutive days.
- `R-CONSEC-DAYS` counts runs, and `{0,1,2}` is one run of three where `{0,2,4}` is three runs of one.
- D1 and D2 read publication state and notice from absolute start times, so permuting days reprices every
  change.

The relation holds under stated preconditions: one shift type per day separated by more than
`min_rest_hours`, no consecutive-day limit, weekly rest loose enough not to bind, and a **cold** solve —
where the objective is cost plus the peak tie-breaker and neither reads the calendar.

The negative case is also committed: one employee and two *adjacent* days with `max_consecutive_days = 1`
must leave a shift unstaffed, while the same two shifts moved apart are both coverable. That test exists
so the preconditions above cannot later be dropped as apparent boilerplate.

### Relaxation monotonicity excludes coverage

Relaxing a *rule* expands the feasible set without touching the objective function, so the optimum can
only improve or hold. Relaxing **coverage** is different: it changes the objective itself through the
shortfall term, so it is not a relaxation in this sense and comparing optima across it is meaningless.

A monotonicity suite in which every relaxation is inert passes vacuously, so one test asserts that at
least one relaxation actually moves the objective.

### Two stated comparison rules

The two readings do not report at identical granularity everywhere, and pretending otherwise would
either weaken the harness to rule-level or produce failures that are not defects. Both narrowings are
recorded here with their cost, and neither may be widened without a `decisions.md` entry.

**`R-CONSEC-DAYS` is compared at `(rule, employee)`, dropping the day.** The checker names the first
breaching day of a run; the model gates every sliding window that breaches, so a long run produces one
finding on one side and several on the other. *Cost:* a day-coordinate error in this one rule is not
caught by the harness.

**Rosters that assign a presolved-away pair are compared on eligibility findings only.** This is the
larger of the two and it took a failing test to state correctly. Presolve *removes* ineligible pairs, so
such an assignment is not representable in the model at all — and the consequence is broader than
coverage. The model cannot count that body toward headcount, toward the employee's weekly or daily
hours, toward a consecutive-day streak, or toward a rest gap. Every aggregating rule is affected. The
only thing the model has an opinion about is *why the pair was excluded*.

*Cost:* nothing aggregate is compared on those rosters. It is bought back by comparing the two
eligibility derivations directly — pair by pair, over every instance variant, for `R-AVAIL`, `R-SKILL`,
`R-FLEXI-ELIG` and `R-DIMONA-FLX`. That is a stronger test than a headcount comparison would have been,
because it localises a disagreement to the eligibility rule that caused it rather than surfacing it as a
coverage mismatch three rules away.
