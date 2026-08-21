# Why the system is shaped this way

> **A derived reading, not a source of truth.** Nothing here owns a claim. [`rules.md`](../guide/rules.md) owns every rule predicate (the conditions each rule imposes), [`model.md`](model.md) owns the formulation, [`api.md`](../guide/api.md) owns the contract. This page exists so that a reader meets the argument before the notation.
>
> Every load-bearing sentence links the record that settled it. Those records are in [`decisions.md`](../archive/decisions.md), and following them is the point.

## 1. The commitment

Someone calls in sick at 09:00 on Saturday. The conventional answer is to re-solve the week, which returns a roster that is optimal, legal, and heavily reshuffled — people whose shifts were never in question get moved so the solver can shave a marginal cost.

This service optimises **deviation from the published roster** instead of cost from scratch ([`D-005`](../archive/decisions.md#d-005)). Every other choice on this page is downstream of that one.

Two consequences arrive immediately. The incumbent is an *input*, so the service needs a way to say which parts of it are already published and which are still draft. And a replan can only be compared to another replan **on observables** — assignments moved, shifts left short — never on objective values ([`D-015`](../archive/decisions.md#d-015)), because two methods optimising different objectives produce incomparable numbers by construction.

**Generation is not a second feature.** It is the same solve with no incumbent supplied — the cold-start case ([`D-109`](../archive/decisions.md#d-109)). Treating it as a separate mode would have meant two objectives, two code paths and two sets of tests for one problem.

## 2. What disruption is, and what it may trade against

Five definitions were built, D0 through D4, each nesting the one before it. **D2 ships**: changed assignments, weighted by publication state, multiplied by how little notice the change gives ([`D-006`](../archive/decisions.md#d-006)). D3 and D4 are configurable and measured.

The objective is a **weighted sum, not a lexicographic ordering** ([`D-049`](../archive/decisions.md#d-049)). Lexicographic ordering guarantees disruption is never traded away, but it also means no cost saving however large buys one unit of disruption — which collapses the disruption/cost frontier to a single point. That frontier is the deliverable, so an objective that makes it trivial is the wrong objective. The exchange rate is **swept to trace the frontier rather than fixed by assertion** ([`D-050`](../archive/decisions.md#d-050)): the honest claim is not *here is the correct rate* but *we cannot know yours; here is the frontier, and here is our default and why*.

**Coverage is the one deliberate exception to hard rules.** Its ceiling is hard and its floor is soft ([`D-018`](../archive/decisions.md#d-018)), because a disruption often has no legal repair and *one short on Saturday, here is what it costs* is the answer a planner can act on. Forcing every shortfall to zero leaves 16 of 72 committed cases with no answer at all.

That has a price, and it is recorded rather than absorbed: once the floor is soft, the empty roster satisfies every hard rule, so **a cold solve is essentially never infeasible** ([`D-047`](../archive/decisions.md#d-047)). Infeasibility survives only in two narrow places — an incumbent whose past already breaks a rule, and a parameter no roster can satisfy. The explainer is therefore scoped around shortfalls, not around infeasibility ([`D-097`](../archive/decisions.md#d-097)); one built for the rare case first would be built for the wrong one.

And because understaffing *reduces* disruption, the shortfall weight has to dominate everything else. That bound is **derived, not tuned** ([`D-057`](../archive/decisions.md#d-057)), and validated at the boundary — a weight scale that breaks it is a malformed request, not a preference.

## 3. Rules are data, and each one names its authority

**Hard rules are constraints, not large penalties** ([`D-002`](../archive/decisions.md#d-002)). A penalised legal rule produces a roster that is *cheaply illegal*, which is not a state this service may return. It also moves every semantic claim into a weight nobody can falsify: a rule you can buy your way out of is a price, not a rule.

That is a claim worth measuring rather than asserting, and it was: pricing a hard rule instead of prohibiting it works on easy weeks and fails completely on hard ones, where **no weight works at all** ([`D-128`](../archive/decisions.md#d-128)). The easy distribution alone would have produced the opposite answer.

Classification is settled by one question, not by preference: *when the only otherwise-legal roster violates this rule, what should the service return?* **Nothing, and an explanation** → hard. **The best compromise, priced and flagged** → soft. Everything soft makes the differential harness assert `true ⟺ true`; everything hard means no shortfall is representable and a planner one person short is told only *infeasible*.

**Hard does not mean unrelaxable.** Every hard constraint instance is gated on an assumption literal, so relaxation is explicit, per-instance and reportable rather than hidden in a weight.

**Every statutory rule names an instrument** ([`D-145`](../archive/decisions.md#d-145)). A legality claim with no source is a guess, and the checker is the component whose whole value is that it is not one. Two of those searches came back negative and the negative is the finding — there is no 24-hour Dimona deadline and no horeca 3h48 minimum, and both are recorded where the rule that would have carried them lives.

**No rule threshold is ever defaulted in shared code** ([`D-039`](../archive/decisions.md#d-039)). The payload carries every parameter explicitly. A shared threshold is exactly the bug the test layers cannot detect, because both readings would be wrong in the same direction.

## 4. Two readings of one registry

The rules are implemented **twice** — once as a CP-SAT encoding, once as plain Python over a returned roster — and compared automatically on every run ([`D-003`](../archive/decisions.md#d-003)).

This is structural rather than a nice-to-have. Under any formulation without hard-constraint guarantees — a penalty inside a local search, a time-boxed solve accepting a gap — feasibility is not guaranteed by construction. Independent verification is the only thing that makes a legality claim true rather than assumed.

The original phrasing was *they share no code*, which cannot be implemented as written: the harness must feed the identical instance to both, so something is shared. The line is drawn by **what a shared item could hide** ([`D-038`](../archive/decisions.md#d-038)):

- **Shared — the payload schema.** A bug here corrupts both readings identically and the harness cannot see it. But neither can it hide a *rule* bug, which is what the harness exists to catch.
- **Shared — the stated conventions.** Half-open interval overlap, start-day attribution, `work_hours = span − break_hours`. These are definitions the registry fixes, not readings of it.
- **Never shared — predicates and thresholds.** Which slot pairs conflict, how a streak is counted, and every number: 11 hours, 35 hours, 3 hours, 6 days.

An import-linter contract holds the module boundary. **The parameter discipline is a review obligation**, because no linter can tell a shared constant from a coincidentally equal one.

Because soft violations are still violations, the harness cannot compare feasibility bits — `checker_feasible` is nearly always true once a shortfall is representable. **It compares violation sets** ([`D-041`](../archive/decisions.md#d-041)).

Underneath both sits brute-force enumeration on micro-instances ([`D-004`](../archive/decisions.md#d-004)): the solver is not trusted to grade its own work. And underneath *that* is the mutation harness ([`D-077`](../archive/decisions.md#d-077)), which breaks the code deliberately and names the layer that must object. It has found four blind spots behind fully green suites, and five times it has been confidently wrong about itself. See [`testing.md`](testing.md).

## 5. Why CP-SAT, and what it costs

**Not speed.** Measured, CP-SAT loses: SCIP proves the same optimum faster on 24 of 24 cases, and the MILP alternative is fully built rather than argued about ([`D-001`](../archive/decisions.md#d-001)).

It ships for three capabilities MILP cannot supply:

1. **Assumption literals, and therefore infeasibility cores** — the object the explainer consumes. MILP has no assumption mechanism.
2. **`violations()`** — fixing every assignment and maximising true gate literals leaves precisely the violated constraints false, so one solve enumerates them all ([`D-044`](../archive/decisions.md#d-044)). Without it the model can only refuse a roster.
3. **Non-linear expressiveness** — D3 and D4 pair changes through `min(drops, adds)`, which MILP needs auxiliary binaries and big-M for.

The price is a number rather than an intuition: **21% of search time and half the variables** go to the gating that buys the first two — 534 gate literals against 183 assignment variables on one headline case. That is the real cost of the explainer.

One finding travels beyond that record: **MILP's default relative gap is unsafe at this objective's scale and fails silently.** With `shortfall_weight` at 100,000 so coverage dominates, a `1e-4` gap is about ten changed shifts, reported as optimal.

The variables are **assignment booleans, not patterns or columns** ([`D-009`](../archive/decisions.md#d-009)) — also built in full and compared. Pattern variables fail to prove optimality within 30 seconds on a cold week the assignment model answers in about 20 milliseconds.

## 6. One week, and who pays for the boundary

The horizon is a week. Belgian labour law measures average hours over a **rolling reference period** of a quarter or a year, so a per-week ceiling is an approximation — and one that is wrong in both directions.

The obvious fix is a longer horizon, and it was **measured rather than assumed** ([`D-116`](../archive/decisions.md#d-116)). A longer horizon buys nothing: four weeks solved at once and four weeks solved one at a time reach identical coverage on every case tried, and under pressure the single solve is two to six times slower. Both reasons originally given for the rejection turned out to be wrong — size grows linearly, not exponentially — and the rejection was upheld on different grounds.

So the reference period is **resolved by the caller and enters as data** ([`D-014`](../archive/decisions.md#d-014)). Three more quantities join it for the same structural reason: a week boundary is an artifact of the payload, not of an employee's working life. Without them every horizon boundary silently resets the rules that span it.

The cost is stated rather than hidden: **correctness depends on a computation this service does not perform**, and the checker must verify against the supplied budget rather than inventing its own.

What this cannot express is a preference reaching across weeks — *I worked last weekend, so not this one*. One such term ships, a rolling balance of unpopular shifts ([`D-108`](../archive/decisions.md#d-108)), and it shipped without a way for a tenant to reach it ([`D-131`](../archive/decisions.md#d-131)). The rest are surveyed in [`preferences.md`](../archive/preferences.md).

## 7. How an answer explains itself, and where a model may speak

**The solver proves; the model renders.** Never the reverse ([`D-013`](../archive/decisions.md#d-013)).

The explainer starts with shortfalls, because that is the common case, and it answers **from the checker** rather than from the solver ([`D-097`](../archive/decisions.md#d-097)) — the component whose whole job is to be independent of the thing being explained. Infeasibility is the rare case, and it returns a minimal core over rule instances rather than a bare `INFEASIBLE`.

**An unlawful hypothetical is refused, not answered** ([`D-098`](../archive/decisions.md#d-098)). *Just shorten the rest gap* is the most dangerous output available from a tool a planner might trust, so relaxing a statutory parameter with no recorded derogation basis is rejected before any solve.

Override recommendations are **grouped by provenance and never ranked across the groups** ([`D-144`](../archive/decisions.md#d-144)). Disruption cannot order two asks of different kinds, and a single flat list says otherwise by its shape — the top line reads as the recommendation.

**The confinement on the language model is a schema, not an instruction** ([`D-101`](../archive/decisions.md#d-101)). `StatedPolicy` has no field for an objective weight and none for enabling a rule the solver does not enforce. A rule the model cannot state is a rule it cannot break. Fields are designed against the *compiled* schema rather than the Python type, because an open mapping compiles to an object that can hold nothing — a defect this project shipped once and caught by measurement.

## 8. Stateless, async, and never nothing

**Async by construction** ([`D-010`](../archive/decisions.md#d-010)). Synchronous HTTP works only for sub-second solves; at 30 s to 5 min it produces timeouts, retries that re-trigger expensive solves, request pile-up, no progress feedback and no cancellation.

**The solver reads nothing** ([`D-011`](../archive/decisions.md#d-011)). Payload in, payload out, no database. That is what makes a solve testable, replayable and reproducible offline — debugging optimisation in production is close to impossible without it. The queue itself is in-process and that is the honest limit: replicas do not share it and a restart loses it, but swapping in Redis touches nothing below `service/`.

**The ladder imports no web layer.** The intricate part stays small and testable; the boundary stays boring, so a non-specialist can read and change it.

Reproducibility needed repair rather than assertion. The optimum was **degenerate**: the same input returned different rosters at the same objective value, and no test could see it because none looked at *which* optimum. The model now pins the value and picks one point in the optimal set by a canonical criterion ([`D-119`](../archive/decisions.md#d-119)) — at 61% of search time, paid deliberately. CI runs a **different `ortools` build** from the one every committed artifact was recorded with, because a claim about determinism across machines needs a foreign binary to test it ([`D-121`](../archive/decisions.md#d-121)).

Fixing it then **blinded two test layers**, and the mutation harness is what noticed ([`D-124`](../archive/decisions.md#d-124)). Reproducibility and observability were trading against each other and only one side had been priced.

**Nothing memoises a built model.** A per-tenant compiled-model cache was built, measured at **0 hits in 144 replan solves** — a replan changes the model's own inputs — and later deleted outright ([`D-149`](../archive/decisions.md#d-149)), because its key was a claim about what changes a model and that claim went stale without anything noticing. The latency win that was actually available came from profiling: memoising `Instance.window` removed 20% of build time ([`D-092`](../archive/decisions.md#d-092)), which is larger than presolve and larger than every other lever in the set.

## 9. Where the evidence stops

The committed benchmark set **solves its own incumbent**, which was for a long time the largest gap in the evidence here. Half of it is closed: published rosters from outside this project reproduce the headline claim by a wider margin than the synthetic set does, and they exposed what a generator could not — ten of thirteen have a past this model calls illegal.

They also found **where the model stops** ([`D-127`](../archive/decisions.md#d-127)): about 40 employees over four weeks, at 527 seconds of model construction on 8 million variables. That ceiling is where this Python stops, not where the formulation does ([`D-147`](../archive/decisions.md#d-147)).

What remains missing is a real Belgian horeca corpus. The full account is [`finish.md`](../archive/finish.md), which lists six places a claim in this repository turned out to be false.

---

*Every record: [`decisions.md`](../archive/decisions.md), by [ID](../archive/decisions.md#lookup) or [by theme](../archive/decisions.md#by-theme). Every measurement, including the nulls: [`studies/`](../archive/studies/README.md).*
