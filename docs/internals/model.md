# The model

The whole formulation:
sets, variables, objective, constraint families, and what the solver is asked to do with them.
Rule predicates (the exact conditions a roster must satisfy) are not restated here; [`rules.md`](../guide/rules.md) owns one *Model encoding* bullet per rule.
Why the formulation is shaped this way is in [`design.md`](design.md).

*Assumes: the rule predicates in [`rules.md`](../guide/rules.md); the payload and time conventions in [`api.md`](../guide/api.md).*

## The problem

A published roster exists and something has broken it; a sick call, a demand change, a withdrawn availability.
Produce a legal roster for the rest of the week that **differs from the published one as little as possible**, rather than the cheapest legal roster.

Shifts that have already started are pinned.
Shifts people have been told about are expensive to change, and more expensive the less notice the change gives.
Generation is the same solve with no incumbent.

## Sets and data

```text
E, e            employees
D, d            days in the horizon, 0-indexed from its start
W, w            weeks in the horizon, week(d) = d // 7
T, s            shift types: a start time and a length
O ⊆ D × T       open shift instances, the (d, s) pairs with req[d, s] > 0
K, k            skills

req[d, s]                    required headcount
start(d, s), end(d, s)       bounds in hours from the horizon start, half-open [start, end)
span(d, s)                   end − start, gross, breaks included
work_hours(d, s)             span − break_hours(s), net working time
now                          the replan instant, in hours
published_through            slots starting before this are published
x̄[e, d, s]                   the incumbent: absent on a cold solve
```

Every time quantity is **hours from the horizon start**, never a calendar timestamp.
Values before the horizon are negative, which is what makes `last_shift_end_before_horizon[e]` an ordinary number rather than a special case.

Gross and net are both carried because the rules disagree on which they mean:
`R-MIN-SHIFT` reads `span`, the hour ceilings read `work_hours`.
Collapsing them would make one rule silently wrong by about a break per shift.

Four quantities are **computed by the caller and never recomputed here**:
`max_hours_this_week[e]`, `consecutive_days_worked_before_horizon[e]`, `last_shift_end_before_horizon[e]` and `unpopular_shifts_before_horizon[e]`. See [`api.md`](../guide/api.md#four-quantities-you-compute-and-this-service-never-recomputes).

The data containers, all in [`roster_replan/domain.py`](../../roster_replan/domain.py):

| Data container | Carries |
| --- | --- |
| `Instance` | `days`, `shift_types`, `employees`, `open_shifts`, `params`, and the replan inputs `now`, `incumbent`, `published_through`, `disruption` |
| `ShiftType` | `label`, `start_hour` (within its day), `span_hours`, `break_hours`; `work_hours` derived |
| `OpenShift` | `day`, `shift`, `required`, `required_skills`, `skill_mix`: the `(d, s)` pairs making up `O` |
| `Employee` | `name`, `contract`, `skills`, `absences`, `unavailability`, the caller-computed quantities, the per-day eligibility gates, and `hourly_rate` |
| `SkillMixEntry` | `skill`, `minimum`, `hard`, `provenance`: class declared per entry |
| `RuleParams` | Every rule threshold, explicit and undefaulted, plus `derogation_basis` |
| `Disruption` | Objective parameters |
| `NoticeBand` | `within_hours`, `multiplier`: tested in order, the last one unbounded |

The roster itself is a `frozenset` of `(employee, day, shift)` triples:
the assignments that are `1`.

`domain.py` is the normative schema and is **the only module the model and the checker may both import**.
What it may hold is fixed by the independence rule ([`D-038`](../decisions.md#d-038)):
data containers and the stated conventions, no rule predicate and no rule threshold.

The wire schema in `service/contracts.py` is a **separate schema**, not a serialisation of this one, so the in-process schema is free to change without breaking a caller.
The two are held together by a round-trip identity test rather than by convention.

## Decision variables

```text
x[e, d, s]      bool          employee e works shift instance (d, s)
u[d, s]         0..req[d,s]   coverage shortfall: R-COVER's slack, priced
o[d, s]         0..           coverage overage: gated to zero
v[d, s, k]      0..m          qualified-coverage shortfall: R-SKILL-MIX, soft entries only
w[e, d]         bool          e works at all on day d, reified for R-CONSEC-DAYS
r[e, w, j]      bool          R-WEEKLY-REST candidate-window selector, per week
```

**A variable exists for every pair surviving presolve, and additionally for every pair the incumbent assigned, eligible or not.**
Without that second case an already-illegal past cannot be represented, and a deviation from it cannot be counted, so the objective would silently understate exactly the change the replan exists to make.
Such a pair is still ineligible, but the exclusion becomes a **gated `x = 0`** rather than an outright fixing, so a roster assigning it is reported rather than merely rejected.

**Durations are carried in minutes.**
CP-SAT is integral and `work_hours` is not.
The conversion is arithmetic rather than a rule threshold, so it lives here rather than in the shared schema.

> **Rejected, and built in full to reject it:** pattern/column variables.
> They tie on a replan, where the pinned past leaves only 36–122 legal patterns for a whole tenant, and fail to prove optimality within 30 seconds on a cold week the assignment model answers in about 20 milliseconds.
> Thousands of near-identical columns create exactly the symmetry this model turns out not to have. [`pattern-encoding.md`](../studies/pattern-encoding.md)

## Objective

One weighted sum, assembled in [`disruption.py`](../../roster_replan/disruption.py):

```text
min   shortfall_weight × Σ u[d, s]          (d, s) not in the past
    + mix_shortfall_weight × Σ v[d, s, k]
    + cost_weight × cost(x)
    + disruption(x, x̄)
    + fairness(x)
```

`cost(x)` is `Σ work_minutes × hourly_rate` over assigned pairs. **It is inert on every instance this project has**: `hourly_rate` is never supplied, so all rates are `1.0`, and with overage gated to zero the total is fixed once coverage is. It reorders rosters only where employees carry different rates. The term stays because the cost baseline is defined by switching it on: see [`limits.md`](../guide/limits.md#trading-disruption-against-cost-and-coverage).

**Historical shortfall is excluded.**
No replan repairs a started shift, and including it adds a constant that makes two runs with different `now` incomparable.

**The ordering is derived, not tuned.**
Understaffing reduces disruption, and so does fairness (an unstaffed unpopular shift is one nobody's count went up for) so the shortfall weight must dominate both:

```text
shortfall_weight  >  max_{(d,s)} req[d, s] × ( max_change_weight + fairness_weight × fairness_tiers )
```

`max_change_weight = published_weight × max(band multipliers)`, further multiplied by `W_callin` and the top concentration tier under D3 and D4.
`fairness_tiers` is `g`'s steepest slope.
Validated at profile load rather than trusted:
a weight scale that breaks this is a malformed request.

### What disruption is a function of

Three things, and forgetting the third is the usual mistake:

1. **The incumbent** `x̄` : what the roster was.
2. **The publication state** : how much of it people actually know.
    An unpublished draft can be reshuffled freely; a published week cannot.
3. **`now`** : how much notice a change gives.
    The same change is cheap two weeks out and expensive tonight.

The atomic unit is a **changed assignment**:
a pair `(e, d, s)` where `x[e, d, s] ≠ x̄[e, d, s]`.
Two kinds exist and they are not equivalent:
a **drop** (`x̄ = 1, x = 0`), where someone was told they would work and now will not, and an **add** (`x̄ = 0, x = 1`), where someone is asked to work when they had been told they were free.

**An add is not free merely because nothing was un-promised.**
A published roster communicates rest as well as work, and being called in on a day off is among the most disruptive things a replan can do.
This is why publication state attaches to **slots rather than to assignments**:
what was published is the whole plan for that slot, including its emptiness.

`published_through` is one number, hours from the horizon start, exactly parallel to `now`.
A slot is published iff `start(d, s) < published_through`;
easy for a caller to get right, and it matches the dominant real pattern:
*the schedule is out through Sunday the 14th*.

**Limitation, stated:**
a wave-published roster, some shifts announced, others held back within the same horizon, is not representable.
The general form is a set `published ⊆ O`, deferred until a tenant needs it.
`published_through` is a special case of it, so the generalisation is additive.

### The five disruption metrics

Each nests the one before it, which is what makes the comparison clean:
D1 with both weights equal *is* D0, D2 with a flat multiplier *is* D1.

**D0: count.**
Rejected, retained as the study's baseline.

```text
D0 = |{ (e, d, s) : x[e, d, s] ≠ x̄[e, d, s] }|
```

It scores a cancellation of a published shift tonight identically to a swap inside next month's draft.

**D1: weighted by publication state.**

```text
D1 = Σ_{changed (e,d,s)}  P(d, s)
P(d, s) = published_weight  if start(d, s) < published_through, else draft_weight
```

`draft_weight` is small but **not zero**.
Zero would leave the optimiser indifferent among draft rosters, and indifference costs stable output across runs and a warm start that resembles its hint.

**D2: weighted by notice.**
*Shipped default.*

```text
D2 = Σ_{changed (e,d,s)}  P(d, s) × N(d, s)
notice(d, s) = start(d, s) − now
N(d, s)      = the multiplier of the first band whose threshold notice falls within
```

Default bands:
notice < 24 h → ×4, otherwise ×1.
A **step** rather than a smooth decay, because statutory and contractual notice periods are themselves steps, and a step is easy to explain where a decay curve invites argument about its shape.
The band table is a parameter.

**D2 depends on `now`**, so golden tests pin `now`, not only the instance.

**D3: change type, moves counted once.**

D0–D2 count a moved shift twice, once as a drop and once as an add.
To the person it happened to it is one event.
Per `(employee, day)`:

```text
moves            = min(drops, adds)
residual_drops   = drops − moves
residual_adds    = adds − moves

D3 = Σ_{e,d}  P(d) × N(d) × ( W_move·moves + W_cancel·residual_drops + W_callin·residual_adds )
```

Default ordering `W_callin > W_cancel > W_move`.
**That ordering is a hypothesis about human preference, not a measurement**, and it is the most falsifiable claim in this file.

`P` and `N` are evaluated per **day** here, read from the day's **anchor slot**; its earliest *open* shift, deliberately not its earliest *affected* one.
Affected-slot weighting would depend on which slots the solution changed, making the objective non-linear and impossible to match between the model's encoding and an independent scorer.
**Solution-independence is what makes the two readings comparable at all.**
The cost: a move inside a long day is priced by the day's earliest notice.

**`extend` is not in D3 and cannot be.**
With fixed shift instances a shift's boundaries are data, so there is no roster in which one is extended.

**D4: concentration.**
Five changes to one person is worse than one change to five, and any sum over changes is blind to the difference.

```text
events_e = Σ_d ( moves + residual_drops + residual_adds )
D4       = D3 + concentration_weight × Σ_e f(events_e)
f: triangular, f(0)=0, f(1)=1, f(2)=3, f(3)=6, so the n-th change to one person costs n
```

**Encoding.** A convex piecewise-linear function of an integer variable needs no piecewise machinery when it is minimised: lower-bound one variable by every segment's line:

```text
t_e ≥ k · events_e − k(k−1)/2     for k = 1 … concentration_tiers
minimise Σ_e t_e
```

`t_e` settles at `max_k(...) = f(events_e)` exactly.
Linear, no products, no auxiliary booleans.
A max-term is the `concentration_tiers = 1` special case and is insensitive to everything below the maximum.

**On this distribution D0, D1 and D2 agree with each other, and D3 agrees with D4.**
The divergence rate across the two sides is 10 of 84. D0–D2 agree because a disruption damages a *given* slot, so `P × N` is a constant factor across candidate repairs and reorders nothing.
D3 and D4 agree because concentration needs two events on one person and median damage is one assignment, so **D4 is unexercised by the committed set**, and that is recorded rather than inferred.
[`disruption-metrics.md`](../studies/disruption-metrics.md)

### Fairness

A third thing called fairness in this repo, and neither of the other two:
not round-robin between tenants in the queue, and not D4 spreading *changes* across people.
This one is about the roster, who ends up working the shifts nobody wants, over time.

**Unpopularity is declared, not derived.**
A late shift is a burden in one restaurant and the sought-after one in another.
`Profile.fairness` names them, carried onto the week by `applied_to`;
the request carries the per-employee history the balance is struck over.

```text
unpopular_e = unpopular_shifts_before_horizon_e + Σ_{d, s ∈ unpopular_shifts} x[e, d, s]
Fairness    = fairness_weight × Σ_e g(unpopular_e)
g(n)        = max_k ( k·n − k(k−1)/2 )       for k = 1 … fairness_tiers
```

`g` is D4's triangular escalation applied to a different quantity and encoded the same way.
Convex rather than a `max − min` range term for the same reason:
a range term equalises the two ends and ignores everybody in the middle.

Minimising a convex function of counts whose **total is fixed by coverage** is what produces balance: the cheapest way to spend a fixed number of unpopular shifts is to spread them.

**The escalation flattens past `fairness_tiers`, and that is a real bound.**
Every employee whose rolling total already exceeds the tier count sits in the linear region where the term no longer distinguishes them, so a window long enough to push everybody past it switches fairness off while appearing to be configured.
The window and the tier count have to be chosen together, and profile review says so when the supplied priors already reach the tiers: a **remark rather than a defect**, because the request is lawful and the tenant may have meant the window.

## Constraint families

| Rule | What it says | How it is enforced |
| --- | --- | --- |
| [`R-COVER`](../guide/rules-operational.md#rule-r-cover) | each open shift is staffed to `req` | hard ceiling via `o = 0`, soft floor via `u` |
| [`R-SKILL-MIX`](../guide/rules-operational.md#rule-r-skill-mix) | a shift's roster holds *m* people with a skill | rows; soft entries get slack `v` |
| [`R-PIN-PAST`](../guide/rules-operational.md#rule-r-pin-past) | shifts starting before `now` are immutable | gated equalities, not constant substitution |
| [`R-AVAIL`](../guide/rules-operational.md#rule-r-avail) · [`R-SKILL`](../guide/rules-operational.md#rule-r-skill) · [`R-FLEXI-ELIG`](../guide/rules-eligibility.md#rule-r-flexi-elig) · [`R-DIMONA-FLX`](../guide/rules-eligibility.md#rule-r-dimona-flx) | eligibility | **entirely by presolve**: variables removed, not rows added |
| [`R-REST-GAP`](../guide/rules-statutory.md#rule-r-rest-gap) | minimum rest between consecutive shifts | pairwise inequalities |
| [`R-WEEKLY-REST`](../guide/rules-statutory.md#rule-r-weekly-rest) | one uninterrupted weekly rest | anchored candidate windows, selected by `r` |
| [`R-MAX-DAILY`](../guide/rules-statutory.md#rule-r-max-daily) · [`R-MAX-WEEKLY`](../guide/rules-statutory.md#rule-r-max-weekly) · [`R-MAX-PERIOD`](../guide/rules-statutory.md#rule-r-max-period) | hour ceilings per day / week / reference period | linear sums over `work_hours` |
| [`R-CONSEC-DAYS`](../guide/rules-statutory.md#rule-r-consec-days) | maximum consecutive working days | sliding window over `w[e, d]` |
| [`R-MIN-BLOCK`](../guide/rules-statutory.md#rule-r-min-block) · [`R-MIN-DAYS-OFF`](../guide/rules-statutory.md#rule-r-min-days-off) · [`R-MAX-WEEKENDS`](../guide/rules-statutory.md#rule-r-max-weekends) · [`R-MAX-SHIFT-TYPE`](../guide/rules-statutory.md#rule-r-max-shift-type) · [`R-MIN-HOURS`](../guide/rules-statutory.md#rule-r-min-hours) · [`R-SUCCESSION`](../guide/rules-statutory.md#rule-r-succession) · [`R-DAY-OFF`](../guide/rules-statutory.md#rule-r-day-off) | the shape of a person's week | optional, profile-gated |

Two rules are **not** roster constraints:
`R-MIN-SHIFT` is input validation, and the reference-period ceiling arrives as a caller-supplied budget rather than as a longer horizon.

### Gates

**Every hard constraint instance is gated on its own boolean**, which the solver is told to hold true for this solve and hands back when it cannot.
CP-SAT calls it an *assumption literal*; this page calls it a gate.
Three things depend on it:

1. A failed solve returns the conflicting rule instances rather than a bare `INFEASIBLE`.
2. The differential harness needs the model to *report* violations, not merely refuse rosters.
    With every assignment fixed, each gate can be true exactly when its constraint holds, so **maximising the number of true gates leaves precisely the violated constraints false**; one solve enumerates them all, where a core would explain one conflict and hide the rest.
3. The *monotone objective under relaxation* property test needs relaxation to be expressible.

`R-COVER`'s ceiling is gated as `o[d, s] == 0` rather than folded into the slack's domain, so an overstaffed roster is reported instead of silently rejected.

**The core is sufficient, not minimal.**
CP-SAT returns a set of assumptions explaining the infeasibility with no guarantee it is smallest.
Iterative deletion on top (solve, drop a gate, re-solve, keep what stays necessary) belongs with the explainer.

### The `regular` automaton, rejected

`R-CONSEC-DAYS` and `R-WEEKLY-REST` are both sequence rules and both use the naive encoding.
The automaton is the textbook choice, which is why it was measured rather than assumed.

**It does not win.**
At a seven-day horizon the window count is not merely small, it is **one**, so the automaton competes against a single linear inequality over seven booleans and is 19% slower to search on 28 of 28 cases.
It also gates only per employee, where the window encoding names the day the streak breached: the coordinate the checker reports and `violations()` matches on.
Kept behind `build(sequence="automaton")` and worth revisiting beyond about two weeks.
[`regular-constraint.md`](../studies/regular-constraint.md)

## Presolve

Most `(employee, shift)` pairs are impossible: unavailable, wrong skill, wrong contract, Dimona gate.
They are eliminated before the solver sees them.

**Measured: a quarter of the model, 28% off build and 14% off search, on 28 of 28 paired cases.**
Free, as claimed, because the exclusion table is computed either way.
Not *the largest single win*, which was the earlier wording; build dominates search at these sizes, and this takes a quarter off the larger half.
The largest single win is memoising `Instance.window`. [`presolve.md`](../studies/presolve.md)

`R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX` are enforced *entirely* this way.

**The exclusion reasons are retained.**
A removed pair can never be reported by a constraint that does not exist, so presolve keeps a map from excluded pair to the rules that excluded it.
Without it an assignment to an ineligible person would be invisible rather than rejected.

This has a consequence for the differential harness that is easy to get wrong:
an assignment to an excluded pair is not representable, so the model cannot count that body toward **anything**: headcount, weekly or daily hours, a streak, a rest gap.
See [`testing.md`](testing.md#two-stated-comparison-rules).

## Symmetry breaking, measured and not shipped

Interchangeable employees create exponentially many equivalent solutions, and lexicographic ordering is the standard remedy.

**Across 24 committed cases there are 3 interchangeable employees in total, in one case.**
Ordering costs about 4% of build time and returns a coin flip on search.

The reason is not the one first assumed.
The incumbent does suppress symmetry, roughly halving it, but the larger effect is the generator giving every employee an independently sampled budget and availability, so two employees are rarely identical *before* any incumbent exists.
That also bounds the null:
on a workforce built to be interchangeable the lever is worth 20% of total time.
**The null is about the distribution, not the lever.**
[`symmetry-breaking.md`](../studies/symmetry-breaking.md)

## Warm starting

A replanned week keeps about 95% of the incumbent's assignments (2.4 changed against 42) so the incumbent is a strong hint:
`add_hint` on every assignment variable.

The hint is a **separate argument to `solve`** rather than being read off `instance incumbent`, even though the shipped replan passes the same roster to both.
Fusing them would make the measurement impossible:
solving with the objective and without the hint is precisely the baseline that separates the two effects.

**It is not a null, and it is small.**
Paired on case and solver seed, the hint reduces search time on 662 of 756 runs, median paired ratio 0.906: 9% of a 3 ms search, invisible end to end beside a 5 ms build.
The objective is what carries the result.
The hint **never changes the answer**, which is asserted rather than assumed:
a hint implemented as a constraint would return the best roster that keeps the damage and report it as the optimum.

## Generation as cold start

Generation is a replan from an empty incumbent, no separate formulation, no mode flag, no second route.
A caller generates by omitting `incumbent` and `now`.

`scoring.disruption_of` returns **0** with no incumbent:
deviation from nothing is nothing.
So cold disruption is **flat at zero everywhere**, not a positive constant proportional to the roster as this was originally derived.
Both readings rank equal-coverage rosters identically, which is why the difference went unnoticed.

The difference matters for one caveat.
The derivation warned that a shortfall would reduce disruption on a cold solve and that the domination bound is what stops it mattering.
As implemented that cannot arise:
the disruption axis is flat at every coverage level.
The shortfall term still prices the missing coverage;
the narrower true statement is that **the bound does no work on the disruption axis of a cold solve**.

**What ranks a cold roster is therefore the tie-breaker.**
Disruption is flat and `cost_weight` ships at 0, so on a cold week the peak-workload term *is* the objective value.
It is a tie-breaker for plausibility, explicitly not a fairness model.

## The canonical optimum

The optimal value alone does not pick a roster: the optimal set is usually large.
The value is pinned and a canonical criterion minimised over it.

Before that, **which roster came back was decided by the ortools binary rather than by the specification, on 24 of 84 replans, and no test noticed.**
The canonicalising phase costs 61% of search time and can itself run out of budget, in which case it says so rather than raising.
[`reproducibility.md`](../studies/reproducibility.md)

## Size, and where it stops

A committed case is 8–25 employees over one week:
a few hundred assignment variables, about 5 ms to build, about 3 ms to search, and every one of 2,268 benchmark runs returned `OPTIMAL`.
**Build dominates search at this size**, which is why the performance work went to model construction rather than search tuning.

The ceiling is known rather than guessed:
the largest foreign instance tried reaches about **8M variables and 527 s of model construction**, and returns no roster: its past is illegal, so it is refused rather than searched, and **nothing is known about search at that size** ([`D-155`](../decisions.md#d-155)).
The first genuinely hard searches this project has seen came from the same import: 7.71 s to prove optimality, re-measured at 8.43 s, against a committed-set maximum of 15.4 ms.

**That ceiling is a property of this implementation, not of the formulation.**
The 527 s is a Python loop emitting constraints one at a time, and **a faster builder is not available**: writing constraints straight into the `CpModelProto` costs 5.01 µs each against the wrapper's 3.75 µs, `protobuf` already resolves to its C implementation, and creating one boolean at all costs 1.35 µs ([`gate-cost.md`](../studies/gate-cost.md), [`D-153`](../decisions.md#d-153)). *Where it stops* means where this code stops, and getting past it means emitting fewer objects or leaving Python.
Every other lever was measured and rejected ([`scaling-levers.md`](../studies/scaling-levers.md), [`D-156`](../decisions.md#d-156)).

Build dominating search is also a statement about **one week** and not about this model in general: instance size grows linearly in the horizon, search does not.

## Not built

**The forecast interface.**
Upstream of the optimiser sits demand forecasting: availability, absences, peak moments, weather, revenue.
Structurally identical to a dispatch problem:
forecast → optimise → commit under constraints.
Nothing of it exists.

---

*Why CP-SAT rather than MILP, why assignment booleans, and what the gating costs:
[`design.md`](design.md#5-why-cp-sat-and-what-it-costs).
Every measurement behind this page:
[`studies/`](../studies/README.md).*
