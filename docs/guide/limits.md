# Guarantees and limits

What this service promises, what it has been measured at, and what it deliberately does not do.

## What it guarantees

**Every roster is re-verified against every rule** by a plain function that imports no solver: a second, independent reading of [`rules.md`](rules.md). Nothing is returned unchecked. That matters most on the two fallback rungs no solver stands behind: a greedy repair, and the last known good roster.

**Something always comes back on a replan.** exact → time-boxed with the gap reported → greedy repair → last known good. See [`api.md`](api.md#the-answer). A *cold* solve cannot make this promise: greedy needs an incumbent to repair.

**A roster is reproducible offline, on any machine.** Every solve's input, profile version and seed are persisted by you, and the same input returns the same roster, not merely the same objective value. That is a repaired claim rather than an assumed one: the optimum was degenerate, so the model now pins the optimal value *and* picks one point in the optimal set by a canonical criterion. CI proves it on a different `ortools` build from the one every committed artifact was recorded with.

**With one qualification, and it is open** ([`D-154`](../decisions.md#d-154)). The canonical criterion is a sum of squared ordinals, and sums of squares can tie, so it does not always pick a single roster. Every committed case is stable and two rosters that tie have been produced deliberately. Treat this as *reproducible in practice on this configuration*, not as a proof.

**A shortfall is priced, not hidden.** Coverage has a soft floor, so an impossible week comes back one person short with an explanation instead of coming back empty.

**Nothing unlawful is offered.** Relaxing a statutory parameter with no recorded derogation basis is refused before any solve, in `what_if` and in the override recommendations alike.

**Every guarantee above starts at the payload, and none of them reaches behind it.** The model and the checker are independent of each other, but they read the same input. A time offset converted wrong (a week containing a clock change treated as `day * 24 + hour` ([`api.md`](api.md#time-is-hours-from-the-horizon-start))) or a `max_hours_this_week` resolved wrong from the reference period is planned against and then certified against, and the two agree. Independence catches a rule read two ways. It cannot catch a week described wrong, and that description is computed in your system, where nothing here tests it.

## Measured

84 cases × 4 methods × 3 solver seeds × 3 time budgets: 2,520 runs. Times in milliseconds, disruption is the D2 score, `changes` counts assignments differing from the incumbent.

**Weeks that could be fully staffed before the disruption**: 72 cases:

| Method | p50 end-to-end | p95 end-to-end | Disruption | Changes | Short |
| --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 10.5 | 22.8 | 307.3 | 12.36 | 0.15 |
| Greedy nearest-eligible repair | 1.2 | 2.8 | 53.6 | 1.94 | 0.31 |
| Cold solve, disruption objective | 10.4 | 22.6 | 65.3 | 2.40 | 0.15 |
| **Warm-started replan** | 10.6 | 21.9 | 65.3 | 2.40 | 0.15 |

**The objective is what does the work.** Against the cost baseline, mean changed assignments fall from 12.4 to 2.4 on identical instances at identical coverage. A cold cost re-solve reshuffles a third of a published week to absorb one sick call, because nothing in its objective prefers the roster people were already told about.

**The warm start is a rounding error beside that**: about 9% of search time, invisible end to end.

**Greedy ties the optimum on 71 of 84 cases**, and its lower average disruption is not a win: it gets there by leaving more shifts unstaffed. On the 13 cases where it left an extra hole, the repair needed a chain: move an uninvolved person so somebody else becomes free. No planner reading a printed roster finds that. So the honest claim is not that the optimiser beats a planner on the common case; it is that **it never leaves a shift uncovered that could have been covered**, and it is right on the case a planner cannot see.

**Time budget makes no difference here.** Every one of the 2,520 runs returned a proven optimum; the longest search was 15.4 ms.

### Where it stops

About **40 employees over four weeks**. Beyond that, model construction dominates: 527 seconds to build an 8-million-variable instance.

That is where this implementation stops rather than where the formulation does, and it is **not** a loop waiting to be written faster ([`gate-cost.md`](../studies/gate-cost.md)). Building the model by hand, straight into the solver's own data structure, is slower than the library call it replaces. The cost is creating millions of objects from Python, so lifting the ceiling means emitting fewer of them or leaving Python, not batching.

Every performance figure above is a statement about a **one-week horizon**. Instance size grows linearly with the horizon; search does not.

## Choosing a disruption metric

Five definitions, each nesting the one before it. **D2 is the shipped default.**

Each is a term in the objective the solver minimises. The formulation those terms sit in (the decision variable, what the objective sums, and why coverage shortfall must dominate) is [`model.md`](../internals/model.md#objective), on the internals side: it describes how the service works today and is **not part of the contract**, so read it to understand the choice below, not to depend on it.

| ID | Definition | Status |
| --- | --- | --- |
| D0 | Count of changed assignments | rejected: a published cancellation and an unpublished move score alike |
| D1 | D0 weighted by publication state | superseded |
| D2 | D1 × notice multiplier, with a step at 24h | **shipped default** |
| D3 | D2 with paired changes recognised as one move, priced by change type | configurable |
| D4 | D3 + a per-employee concentration penalty | configurable |

They produce different rosters on **10 of 84** cases, and the divergence is entirely D0/D1/D2 against D3/D4: within each side, nothing separates them on this distribution.

**Take D3 if your weeks have room to move people.** D0–D2 count changed slots; D3 pairs a drop with an add for the same person on the same day and calls it one move. The worked case: Ana holds a morning shift and Bram the evening of the same day, and Ana becomes unavailable in the morning only. D2 calls a third person in (two changes). D3 instead moves Ana to the evening and Bram to the morning: four slots, but two *moves*. Both are defensible answers to the same disruption.

**The metrics only diverge where there is slack.** On a tightly covered week there is exactly one legal repair, so every metric returns it and the choice is invisible. D3 additionally needs a *move* to be available: another open shift the same day. **D4 is unexercised by the committed set**, because a concentration penalty needs two events on one person and median damage is one assignment.

## Trading disruption against cost and coverage

Four levels, and only two of them trade:

| Level | Mechanism |
| --- | --- |
| Hard rules | Constraints. Not in the objective at all |
| Coverage and qualification shortfall | Priced, and **must dominate** |
| Disruption | D2 by default |
| Cost | Traded against disruption at `cost_weight`, which ships at `0` and stays inert until employees carry different rates: see below |

**`shortfall_weight` must dominate, and the bound is derived rather than chosen.** Understaffing reduces disruption (an unstaffed shift is a shift nobody was moved onto) so a shortfall weight set too low means the optimiser buys stability by leaving shifts empty. That looks like a tuning problem and is an ordering error:

```
shortfall_weight  >  max_{(d,s)} req[d, s]  ×  max_change_weight
```

A weight scale that breaks this is rejected as a malformed request, not accepted as a preference.

**`cost_weight` ships at `0`.** The cost model is `Σ work_minutes × hourly_rate`, with no overtime premium, no flexi wage cap, no weekend or night differential, and no distinction between marginal and sunk labour. A weight on a number that cannot tell two equal-hours rosters apart would add noise and no signal, so the shipped objective is pure disruption. Read the cost axis as *paid hours*, not as euros.

**Why it cannot tell them apart, exactly.** `hourly_rate` is optional and nothing supplies it (not the demo scenario, not the generator) so every employee costs `1.0` and every assignment of a 7.5-hour shift costs the same whoever takes it. Coverage cannot exceed `required`, because `R-COVER`'s ceiling is gated to zero overage. So at equal coverage the total is a constant, and switching cost on reorders nothing: every method in the table above reports the same **284.5 paid hours**. The one thing the term can still move is coverage itself (fewer people rostered is cheaper) which is why `shortfall_weight` must dominate it by a derived bound rather than a chosen number.

**It is an extension point, not a hole.** Give two employees different rates and the term becomes live immediately, with no model change: a flexi-jobber and a full-timer on the same shift stop being interchangeable, and cost starts trading against disruption at whatever `cost_weight` says. What is missing is the wage data, not the encoding. The term also stays in the objective for a second reason: the cold-cost baseline the headline claim is measured against is *defined* by switching it on ([`benchmarks.md`](../benchmarks.md)), so it is exercised on all 84 cases even though no tenant profile uses it.

The default exchange rate, if you switch cost on: **one published change at short notice ≈ two hours of overtime premium.** That is a hypothesis written down so it can be argued with, not a measurement.

## What is deliberately absent

| Gap | Why |
| --- | --- |
| Five rules declared but not encoded: `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` | Each is sourced to an instrument but has no predicate (no conditions written out) yet. Enabling one is rejected rather than silently ignored |
| A real cost model | Needs wage data. The term is in the objective and inert on uniform rates: see `cost_weight` above |
| Preferences that reach past one week | The objective is measured inside the horizon. A rolling weekend balance carries across, but nothing else does |
| Capture and replay of real rosters | Needs authorization and real vendor payloads |
| A horizon over four weeks | Answered, but no committed benchmark case runs at more than one |

## The largest caveat in the evidence

**The committed benchmark set solves its own incumbent.** Every number above shows a replan beats a re-solve *given a roster this model would produce*.

Half of that gap is closed. Published rosters from the nurse-rostering set (produced by other people, other tools, other objectives) reproduce the headline claim by **4.6× to 37×**, against about 5× on the committed set. They also found what a synthetic set could not: **eight of thirteen published rosters have a past this model calls illegal.**

What is still missing is a real Belgian horeca corpus.

---

*Full method, instance distribution and caveats: [`benchmarks.md`](../benchmarks.md). The foreign rosters: [`foreign-incumbent.md`](../studies/foreign-incumbent.md). Where the project stands in full: [`STATE.md`](../STATE.md).*
