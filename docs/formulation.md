# The model on one page

What is solved, in one reading.
Sets, variables, objective, constraint families, and where each lives in the specs and the code.

> **A derived reading, not a spec.**
> Nothing here is the source of truth for anything.
> [`specs/model.md`](specs/model.md) owns the input contract, [`specs/replan.md`](specs/replan.md) owns the objective, [`specs/rules.md`](specs/rules.md) owns every rule predicate.
> This page exists so a reader can see the shape before reading 12,000 words of it.

## The problem

A published roster exists and something has broken it — a sick call, a demand change, a withdrawn availability.
Produce a legal roster for the rest of the week that **differs from the published one as little as possible**, rather than the cheapest legal roster.
Shifts that have already started are pinned; shifts people have been told about are expensive to change, and more expensive the less notice the change gives.
Generation is the same solve with no incumbent, not a second feature.

## Sets and data

```
E, e            employees
D, d            days in the horizon, 0-indexed from its start
W, w            weeks in the horizon, week(d) = d // 7
T, s            shift types — a start time and a length
O ⊆ D × T       open shift instances, the (d, s) pairs with req[d, s] > 0
K, k            skills

req[d, s]                    required headcount
start(d, s), end(d, s)       bounds in hours from the horizon start, half-open [start, end)
span(d, s)                   end − start, gross, breaks included
work_hours(d, s)             span − break_hours(s), net working time
now                          the replan instant, in hours
published_through            slots starting before this are published
x̄[e, d, s]                   the incumbent — absent on a cold solve
```

Every time quantity is **hours from the horizon start**, never a calendar timestamp.
Gross and net are both carried because the rules disagree on which they mean: `R-MIN-SHIFT` reads `span`, the hour ceilings read `work_hours`.
Collapsing them would make one rule silently wrong by about a break per shift.

Four quantities are **computed by the caller and never recomputed here** — `max_hours_this_week[e]`, `consecutive_days_worked_before_horizon[e]`, `last_shift_end_before_horizon[e]` and `unpopular_shifts_before_horizon[e]`.
A week boundary is an artifact of the payload, not of an employee's working life, and these carry the history the horizon cannot see.
`max_hours_this_week` is the one that matters most: it is the rolling reference period resolved into a single number, which is what lets the horizon stay at one week.
The checker verifies against the supplied budget and must never recompute it — a checker that invents its own budget is testing the caller, not the roster.

## Decision variables

```
x[e, d, s]      bool   employee e works shift instance (d, s)
u[d, s]         int    coverage shortfall — R-COVER's slack, priced
o[d, s]         int    coverage overage — gated to zero
v[d, s, k]      int    qualified-coverage shortfall — R-SKILL-MIX, soft entries only
w[e, d]         bool   e works at all on day d, reified for R-CONSEC-DAYS
r[e, w, j]      bool   R-WEEKLY-REST candidate-window selector
```

A variable exists for every pair surviving presolve, **and additionally for every pair the incumbent assigned**, eligible or not ([`D-058`](decisions.md#d-058)).
Without that second case an illegal past cannot be represented, and a deviation from it cannot be counted — so the objective would understate exactly the change the replan exists to make.

## Objective

Minimised as a single weighted sum ([`D-049`](decisions.md#d-049)), assembled in [`roster_replan/disruption.py`](../roster_replan/disruption.py):

```
min   shortfall_weight × Σ u[d, s]          (d, s) not in the past
    + mix_shortfall_weight × Σ v[d, s, k]
    + cost_weight × cost(x)
    + disruption(x, x̄)
    + fairness(x)
```

The shipped disruption metric is **D2** — every changed assignment weighted by publication state and by notice:

```
D2 = Σ_{(e,d,s) : x ≠ x̄}  P(d, s) × N(d, s)

P(d, s) = published_weight if start(d, s) < published_through, else draft_weight
N(d, s) = 4 if start(d, s) − now < 24h, else 1
```

D0 and D1 are the same sum with weights switched off; D3 pairs a drop with an add so a move counts once; D4 adds a convex penalty for concentrating damage on one person.
All five are defined and measured in [`specs/replan.md`](specs/replan.md); on this instance distribution D0, D1 and D2 agree with each other and D3 with D4.

**The ordering is derived, not tuned** ([`D-057`](decisions.md#d-057)).
Understaffing reduces disruption — nobody is moved onto a shift nobody works — so the shortfall weight must dominate or the optimiser buys stability by leaving shifts empty:

```
shortfall_weight  >  max_{(d,s)} req[d, s] × max_change_weight
```

Validated at profile load rather than trusted.
Historical shortfall is excluded from the sum: no replan repairs a started shift, and keeping it makes two runs with different `now` incomparable.

## Constraint families

Every rule carries a stable ID used identically in this page, the spec, the model, the checker, the `Violation` objects and the explainer.
Predicates and parameters are in [`specs/rules.md`](specs/rules.md); each ID below links to its section.

| Rule | What it says | How it is enforced |
| --- | --- | --- |
| [`R-COVER`](specs/rules.md#rule-r-cover) | each open shift is staffed to `req` | hard ceiling via `o = 0`, soft floor via `u` |
| [`R-SKILL-MIX`](specs/rules.md#rule-r-skill-mix) | a shift's roster holds *m* people with a skill | rows; soft entries get slack `v` |
| [`R-PIN-PAST`](specs/rules.md#rule-r-pin-past) | shifts starting before `now` are immutable | gated equalities, not constant substitution |
| [`R-AVAIL`](specs/rules.md#rule-r-avail) · [`R-SKILL`](specs/rules.md#rule-r-skill) · [`R-FLEXI-ELIG`](specs/rules.md#rule-r-flexi-elig) · [`R-DIMONA-FLX`](specs/rules.md#rule-r-dimona-flx) | eligibility | **entirely by presolve** — variables removed, not rows added |
| [`R-REST-GAP`](specs/rules.md#rule-r-rest-gap) | minimum rest between consecutive shifts | pairwise inequalities |
| [`R-WEEKLY-REST`](specs/rules.md#rule-r-weekly-rest) | one uninterrupted weekly rest | anchored candidate windows, selected by `r` |
| [`R-MAX-DAILY`](specs/rules.md#rule-r-max-daily) · [`R-MAX-WEEKLY`](specs/rules.md#rule-r-max-weekly) · [`R-MAX-PERIOD`](specs/rules.md#rule-r-max-period) | hour ceilings, per day / week / reference period | linear sums over `work_hours` |
| [`R-CONSEC-DAYS`](specs/rules.md#rule-r-consec-days) | maximum consecutive working days | sliding window over `w[e, d]` |
| [`R-MIN-BLOCK`](specs/rules.md#rule-r-min-block) · [`R-MIN-DAYS-OFF`](specs/rules.md#rule-r-min-days-off) · [`R-MAX-WEEKENDS`](specs/rules.md#rule-r-max-weekends) · [`R-MAX-SHIFT-TYPE`](specs/rules.md#rule-r-max-shift-type) · [`R-MIN-HOURS`](specs/rules.md#rule-r-min-hours) · [`R-SUCCESSION`](specs/rules.md#rule-r-succession) · [`R-DAY-OFF`](specs/rules.md#rule-r-day-off) | shape of a person's week | optional, profile-gated |

Two rules are **not** roster constraints: `R-MIN-SHIFT` is input validation, and the reference-period ceiling arrives as a caller-supplied budget rather than a longer horizon.

## What the solver is asked to do with it

**Every hard constraint instance is gated on an assumption literal.**
Not decoration: it is what lets a failed solve name the conflicting rule instances, and what lets `violations()` report a roster rather than merely refuse it.
It costs about 21% of search time and half the variables — 534 gates against 183 assignment variables on `headline/0` — and that is the price of the explainer, stated as a number ([`D-001`](decisions.md#d-001)).

**Presolve removes a quarter of the model** before the solver sees it, and keeps the reason each pair was removed, so an assignment to an ineligible person is reported rather than invisible ([`D-045`](decisions.md#d-045)).

**The optimum is canonical.**
The optimal value alone does not pick a roster — the optimal face is usually wide — so the value is pinned and a canonical criterion minimised over it.
Before that, which roster came back was decided by the ortools binary rather than by the specification, on 24 of 84 replans, and no test noticed ([`D-119`](decisions.md#d-119)).

## Size, and where it stops

A committed case is 8–25 employees over a one-week horizon: a few hundred assignment variables, ~5 ms to build, ~3 ms to search, and every one of 2,268 benchmark runs returned `OPTIMAL`.
Build time dominates search at this size, which is why the performance work went to model construction rather than to search tuning.

The ceiling is known rather than guessed ([`D-127`](decisions.md#d-127)): the largest foreign instance tried reaches about 8M variables and 527 s of **model construction**, and returns no roster.
The first genuinely hard searches this project has seen came from the same import — 7.71 s to prove optimality, against a committed-set maximum of 15.4 ms.

**That ceiling is a property of this implementation, not of the formulation** ([`D-147`](decisions.md#d-147)).
The 527 s is a Python loop emitting constraints one at a time; the same model handed to the same solver by a faster builder would start searching sooner, and nothing in the encoding above requires it to be slow.
So *where it stops* means where this code stops, and the number is quoted that way throughout — it bounds what the service can answer today, and says nothing about whether the model is the right one at that size.
Whether batching the construction moves it has not been measured, which is why the claim here is scoped rather than hopeful.

## Where to go next

- **Is it legal?** [`specs/rules.md`](specs/rules.md) — the registry, then the rule.
- **Is it preferable?** [`specs/replan.md`](specs/replan.md) — the five metrics and what they trade.
- **What does a caller send?** [`specs/model.md`](specs/model.md) — the input contract.
- **How is any of it known to be true?** [`specs/validation.md`](specs/validation.md) — the checker and the test layers.
- **Does it hold up?** [`benchmarks.md`](benchmarks.md), then [`studies/README.md`](studies/README.md).
