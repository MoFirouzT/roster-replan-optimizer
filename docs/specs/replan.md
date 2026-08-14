# Replan

The objective. [`rules.md`](rules.md) owns what is *legal*; this file owns what is *preferable*.

> **Status: D0–D4 defined and measured, D2 shipped.** The comparison the file called for is in
> [`studies/disruption-metrics.md`](../studies/disruption-metrics.md), and warm starting is measured
> under `D-082`.
>
> **T2 closes without the wage data**, so the two remaining `[TODO]`s stand and their owner has moved:
> the cost model is still a flat rate, and the exchange rate is still uncalibrated. Neither can be
> settled from first principles, and the corpus that would settle them is
> [`capture.md`](capture.md)'s. `benchmarks.md` reports the consequence rather than working around it —
> with a flat rate and a hard coverage ceiling every fully staffed roster costs the same, so the cost
> axis of the frontier collapses and `D-050`'s sweep has nothing to trace yet.

## What disruption is a function of

Disruption compares the roster being produced against the one people were already told about
(`D-005`). It is a function of three things, and forgetting the third is the usual mistake:

1. **The incumbent** `x̄` — what the roster was.
2. **The publication state** — how much of it people actually know. An unpublished draft can be
   reshuffled freely; a published week cannot.
3. **`now`** — how much notice a change gives. The same change is cheap two weeks out and expensive
   tonight.

The atomic unit is a **changed assignment**: a pair `(e, d, s)` where `x[e, d, s] ≠ x̄[e, d, s]`. Two
kinds exist, and they are not equivalent:

- **drop** — `x̄ = 1, x = 0`. Someone was told they would work and now will not.
- **add** — `x̄ = 0, x = 1`. Someone is asked to work when they had been told they were free.

An add is *not* free merely because nothing was un-promised. A published roster communicates rest as
well as work, and being called in on a day off is among the most disruptive things a replan can do.
This is why publication state attaches to **slots rather than to assignments**: what was published is
the whole plan for that slot, including its emptiness.

### Publication state, concretely

`published_through` — hours from the horizon start, supplied by the caller, exactly parallel to `now`
and on the same scale as every other time quantity (see [`model.md`](model.md#input-contract)). A slot
`(d, s)` is published iff `start(d, s) < published_through` (`D-051`). One number, easy for a caller to get right, and it
matches the dominant real pattern: *"the schedule is out through Sunday the 14th."*

**Limitation, stated:** a wave-published roster — some shifts announced, others held back within the
same horizon — is not representable. The general form is a set `published ⊆ O`, deferred until a tenant
actually needs it. `published_through` is a special case of it, so the generalisation is additive.

## The five definitions

All five are defensible. They produce different rosters, and **that fact is the deliverable** — the T2
study exists to show it rather than to assert it.

> **Measured** in [`studies/disruption-metrics.md`](../studies/disruption-metrics.md). They diverge on
> 23 of the 72 committed cases, and where they do, each scores the other's answer at roughly double
> its own optimum. But the divergence is entirely **D0/D1/D2 against D3/D4**: within each side nothing
> separates them on that distribution. D0, D1 and D2 agree because a disruption damages a *given* slot,
> so `P × N` is a constant factor across every candidate repair and a constant factor reorders nothing
> — the weights need a choice of *which* slot to disturb, which these scenarios never offer. D3 and D4
> agree because the concentration penalty needs two events on one person, and median damage is one
> assignment (`D-086`).

> **They only diverge where there is slack, and this constrains T2's generator.** On a tightly covered
> instance there is exactly one legal repair, so every metric returns it and the choice of metric is
> invisible. An instance generator that does not vary **coverage tightness** would therefore report "the
> metrics agree" — as a property of the instances, not of the metrics. The generator's tightness
> parameter is not one knob among several; it is the one that decides whether the study can see anything
> at all.
>
> **Necessary, and not sufficient** (`D-060`). The mechanism held — the `tight` class diverges on 0 of
> 6 cases — but slack alone does not predict divergence, and the week-level minimum slot slack the
> instance set records predicts it not at all. What D3 additionally needs is a *move* to be available:
> another open shift on the same day that a rostered person could be shifted to. That is a property of
> the damaged day, and no generator axis varies it yet.
>
> A worked divergence, small enough to check by hand and used as a test: Ana holds a morning and Bram the
> evening of the same day; Ana becomes unavailable in the morning only. D2 counts changed slots and calls
> a third person in for the morning (two changes). D3 pairs changes per person and instead moves Ana to
> the evening and Bram to the morning (four slots, but two *moves*). Both are defensible answers to the
> same disruption, which is the whole claim.

| ID | Definition | Status |
|---|---|---|
| D0 | Count of changed assignments | rejected — a published cancellation and an unpublished move score alike |
| D1 | D0 weighted by publication state | superseded |
| D2 | D1 × notice multiplier, with a step at 24h | **shipped default** (`D-006`) |
| D3 | D2 with paired changes recognised as one move, priced by change type | configurable |
| D4 | D3 + convex per-employee concentration penalty | configurable |

Each nests the one before it, which is what makes the study a clean comparison: D1 with both weights
equal *is* D0, D2 with a flat multiplier *is* D1. The escalation is not five unrelated ideas.

### D0 — count

```
D0 = |{ (e, d, s) : x[e, d, s] ≠ x̄[e, d, s] }|
```

**Rejected**, and retained only as the study's baseline. It scores a cancellation of a published shift
tonight identically to a swap inside next month's draft, which is not a rounding error — it is the
entire question the project is about.

### D1 — weighted by publication state

```
D1 = Σ_{changed (e,d,s)}  P(d, s)

P(d, s) = published_weight   if start(d, s) < published_through
          draft_weight       otherwise
```

`draft_weight` is small but **not zero** (`D-052`). Zero would leave the optimiser indifferent among draft
rosters, and indifference costs two things worth keeping: stable output across runs, and a warm start
that resembles its hint. A small weight buys both and distorts nothing, because the number of
assignments is pinned by coverage rather than chosen freely.

### D2 — weighted by notice `[shipped]`

```
D2 = Σ_{changed (e,d,s)}  P(d, s) × N(d, s)

notice(d, s) = start(d, s) − now
N(d, s)      = the multiplier of the first band whose threshold notice falls within
```

Default bands: **notice < 24h → ×4**, otherwise **×1**. A step rather than a smooth decay, for two
reasons: contractual and statutory notice periods are themselves steps (`R-PUB-NOTICE`), and a step is
easy to explain to a planner, where a decay curve invites argument about its shape. The band table is a
parameter, so a tenant that wants a second step at 72h configures one.

**D2 depends on `now`.** The same pair of rosters scores differently at different times of day, which is
correct and worth stating: golden tests must therefore pin `now`, not only the instance.

### D3 — change type, and moves counted once

D0–D2 all count a moved shift twice — once as a drop, once as an add (`D-053`). To the person it
happened to it is one event:
*"your Saturday moved from the morning to the evening."* D3 is the definition that notices.

Per `(employee, day)`, let `drops` and `adds` be the counts of changed slots of each kind. Then:

```
moves            = min(drops, adds)
residual_drops   = drops − moves
residual_adds    = adds − moves

D3 = Σ_{e,d}  P(d) × N(d) × ( W_move·moves + W_cancel·residual_drops + W_callin·residual_adds )
```

Default ordering **`W_callin > W_cancel > W_move`**: being newly called in imposes most, losing an
expected shift next, having one moved within a day least.

**That ordering is a hypothesis about human preference, not a measurement**, and it is the single most
falsifiable claim in this file. T2's capture-and-replay work can test it directly: real planners
resolving real disruptions reveal which trade they actually make. If the corpus contradicts the
ordering, the ordering changes and this paragraph becomes a `decisions.md` entry.

**Simplification, stated** (`D-054`). `P` and `N` are evaluated per **day** here rather than per slot,
read from the day's **anchor slot** — its earliest *open* shift. A change is communicated about a day, and pairing
drops with adds requires a common granularity.

The anchor is deliberately the earliest open shift and **not** the earliest *affected* one, which is the
more intuitive choice and is wrong twice over: the weight would depend on which slots the solution
changed, making the objective non-linear, and it would be impossible to match between the model's encoding and
an independent scorer, since one iterates variables and the other iterates changes. Solution-independence
is not a nice-to-have here — it is what makes the two readings comparable at all.

The cost is that a move from an early shift to a late one inside a long day is priced by the day's
earliest notice rather than by the affected shift's.

**`extend` is not in D3, and cannot be** (`D-056`). The outline listed extending a shift as a change type; with
fixed shift instances a shift's boundaries are data, so there is no roster the model can express in
which one is extended. It becomes representable in T5's generation mode and is a change type only there.

### D4 — concentration

Five changes to one person is worse than one change to five, and any **sum** over changes is blind to
the difference. D4 adds a convex penalty on each employee's event count:

```
events_e = Σ_d ( moves + residual_drops + residual_adds )
D4       = D3 + concentration_weight × Σ_e f(events_e)
```

`f` is convex with escalating marginal cost — `f(0)=0, f(1)=1, f(2)=3, f(3)=6`, the triangular numbers,
so the *n*-th change to one person costs *n*.

**Encoding** (`D-055`). A convex piecewise-linear function of an integer variable needs no piecewise
machinery when it is being minimised: introduce `t_e` and lower-bound it by every segment's line.

```
t_e ≥ k · events_e − k(k−1)/2     for k = 1 … concentration_tiers
minimise Σ_e t_e
```

Because `f` is convex and the objective pushes `t_e` down, `t_e` settles at `max_k(...) = f(events_e)`
exactly. Linear, no products, no auxiliary booleans. This is why D4 does not need the max-term the
outline reached for: a max-term is the `concentration_tiers = 1` special case, and it is insensitive to
everything below the maximum.

## Trading disruption against cost and coverage

**Decision: weighted, not lexicographic** (`D-049`) — and the reason is that the frontier is the
deliverable.

Lexicographic ordering (feasibility → disruption → cost) guarantees disruption is never traded away, but
it also means no cost saving however large buys one unit of disruption. That collapses the
disruption/cost Pareto frontier to a single point, and that frontier is the headline chart in
[`benchmarks.md`](../benchmarks.md). An objective that makes the money chart trivial is the wrong
objective.

So the objective is a weighted sum, and the exchange rate `cost_weight` is **swept** to trace the
frontier rather than fixed by assertion (`D-050`). The honest claim is not "here is the correct exchange rate" but
*"we cannot know your exchange rate; here is the frontier, and here is our default and why."*

### The four levels, and why only two of them trade

| Level | Mechanism |
|---|---|
| Hard rules | Constraints. Not in the objective at all — see `rules.md` |
| Coverage and qualification shortfall | Priced, and **must dominate** — see below |
| Disruption | D2 by default |
| Cost | Traded against disruption at `cost_weight` |

### The domination bound is derivable, not chosen (`D-057`)

Understaffing reduces disruption: an unstaffed shift is a shift nobody was moved onto. So if the
shortfall weight is too low, **the optimiser buys stability by leaving shifts empty** — a failure mode
that would look like a tuning problem and is actually an ordering error.

The bound is computable. Leaving one shift instance unstaffed avoids at most `req[d, s]` changed
assignments, each worth at most the largest per-change weight the metric can produce:

```
shortfall_weight  >  max_{(d,s)} req[d, s]  ×  max_change_weight
```

where `max_change_weight = published_weight × max(band multipliers)`, further multiplied by
`W_callin` and the top concentration tier under D3 and D4.

**This is validated at profile load rather than trusted** — `validation.md` owns the check. A weight
scale that violates it is a malformed request, not a preference.

### The default exchange rate is a hypothesis

Default: **one published change at short notice ≈ two hours of overtime premium.** Written down so it
can be argued with, which is the whole point of stating an exchange rate instead of tuning until the
output looks reasonable.

It is not a measurement. Calibrating it needs the T2 corpus — real planners choosing between paying
overtime and moving someone reveal their own rate. `[TODO]` after capture.

### The cost model is a placeholder

`cost = Σ work_minutes × hourly_rate(e)`, with a uniform rate when none is supplied.

Deliberately thin. Overtime premiums, flexi-job rates — the horeca flexi wage cap is a real constraint
on this — weekend and night differentials, and the difference between marginal and sunk labour cost all
belong here and none are modelled. **`[TODO]` T2**, alongside the wage data that would make them
meaningful. Until then, cost differences between two rosters of equal hours are zero, which is honest
but blunt, and the frontier's cost axis should be read as *paid hours* rather than as euros.

**And `cost_weight` ships at `0`**, so the term is not merely blunt — it is switched off, and the
shipped objective is pure disruption. That is the right default while the cost model is a placeholder:
a weight on a number that cannot tell two equal-hours rosters apart would add noise and no signal. T2
sweeps it (`D-050`), which is when the cost axis starts to mean anything.

## Understaffing: hard or soft

Settled in [`rules.md`](rules.md#r-cover--coverage): **hard ceiling, soft floor**, ratified under
`D-008` — a hard floor cannot answer 16 of the 72 committed cases, eight of them weeks that were
fully staffable until the disruption. The consequence for this file is the domination bound above, and one more worth naming: with a
soft floor, coverage has been *priced against stability*. That is a real choice. A planner who would
always rather be short than move someone is expressing an exchange rate, and this model lets them
configure it instead of pretending the question does not arise.

Historical shortfall — on a shift that has already started — is excluded from the objective. No replan
can repair it, and including it adds a constant that makes two runs with different `now` incomparable.

## Warm starting

Tomorrow's roster is ~95% of today's, so the previous solution is a strong hint: `add_hint` on every
assignment variable from the incumbent.

The hint is a **separate argument to `solve`** rather than being read off `instance.incumbent`, even
though the shipped replan passes the same roster to both. Fusing them would make the measurement below
impossible to take: solving with the objective and without the hint is precisely the baseline that
separates the two effects.

**Measured, and it is not a null** (`D-082`). A warm-started replan is faster than a cold
*cost-objective* solve for two independent reasons — the hint, and the fact that a disruption
objective has its optimum near the incumbent — so only the cold *disruption-objective* baseline can
tell them apart. Paired on case and solver seed across the committed set, the hint reduces CP-SAT's
search time on 201 of 216 runs, median paired ratio 0.907.

**And it is small.** That is 9% of a 3 ms search, invisible in end-to-end latency because building
the model costs about 5 ms. The objective is what carries the result: it cuts mean disruption from
323 to 66 against the cost baseline, and the hint is a rounding error beside it. The hint never
changes the answer, which is asserted rather than assumed — a hint implemented as a constraint would
return the best roster that keeps the damage and report it as the optimum.

## Generation as cold start

Generation is a replan from an empty incumbent. No separate formulation, and now the reason can be
stated rather than asserted:

With `x̄ = ∅` every assignment is an add on an unpublished slot, so every change carries the same weight
`draft_weight`, and the number of changes equals the number of assignments — which coverage pins.
Disruption is therefore **constant across all rosters achieving the same coverage**, and the objective
reduces to cost. The metric does not need a special case because it degenerates into one.

One caveat, since the constancy is not quite unconditional: rosters with *different* coverage outcomes
have different assignment counts, so a shortfall would reduce disruption. The domination bound above is
what stops that mattering, which is the same bound for the same reason.

A cold solve also needs a tie-breaker, because cost is indifferent to *who* works. A small
peak-workload term serves: it is a tie-breaker for plausibility, explicitly **not** a fairness model.
The fairness model is the next section.

## Fairness: rolling balance of unpopular shifts `[shipped]`

`PLAN.md` scoped this as *"fairness objectives beyond disruption concentration"*, and the word
**beyond** is doing the work. This repo already had two things called fairness and this is neither of
them: `D-091`'s round-robin is fairness between *tenants in the queue*, and D4's concentration spreads
*changes* across people. Both are about the replan. This one is about the roster — who ends up working
the shifts nobody wants, over time (`D-108`).

**Unpopularity is declared, not derived.** Which shifts are unpopular is a social fact about a tenant,
not a property this system can compute: a late shift is a burden in one restaurant and the sought-after
one in another. The profile names them, the same way it names everything else that is policy rather
than law.

**The balance is rolling, so it needs history the horizon does not contain.** One week cannot be fair
on its own — somebody has to work Saturday. Each employee therefore carries the count they have already
worked over a stated window, exactly as they already carry
`consecutive_days_worked_before_horizon` for `R-CONSEC-DAYS`.

```
unpopular_e = unpopular_shifts_before_horizon_e + Σ_{d, s ∈ unpopular_shifts} x[e, d, s]
Fairness    = fairness_weight × Σ_e g(unpopular_e)
g(n)        = max_k ( k·n − k(k−1)/2 )       for k = 1 … fairness_tiers
```

`g` is D4's triangular escalation applied to a different quantity, and it is encoded the same way — one
variable per employee, lower-bounded by every segment's line (`D-055`). Convex rather than a
`max − min` range term for the reason D4 gives: a range term is the `tiers = 1` case and is blind to
everything between the extremes, so it equalises the two ends and ignores everybody in the middle.

Minimising a convex function of counts whose **total is fixed by coverage** is what produces balance:
the cheapest way to spend a fixed number of unpopular shifts is to spread them.

**The escalation flattens past `fairness_tiers`, and that is a real bound.** `g` is convex only up to
the tier count; beyond it the marginal cost is constant, so every employee whose rolling total already
exceeds `fairness_tiers` sits in the linear region where the term no longer distinguishes them. A
window long enough to push everybody past it therefore switches fairness off while appearing to be
configured. The window and the tier count have to be chosen together, and `validation.py` warns when
the supplied priors already exceed the tiers.

### Fairness makes understaffing attractive, and the bound has to grow

An unstaffed unpopular shift is one nobody's count went up for, so fairness — like disruption before it
(`D-057`) — pays for coverage failures. The domination bound extends rather than being re-derived:

```
shortfall_weight  >  max_{(d,s)} req[d, s] × ( max_change_weight + fairness_weight × fairness_tiers )
```

`fairness_tiers` is `g`'s steepest slope, so it is the most one additional unpopular assignment can
cost. **Validated at load, not trusted**, on the same footing as the disruption half of the bound —
a fairness weight that breaks it is a malformed request rather than an aggressive preference.
