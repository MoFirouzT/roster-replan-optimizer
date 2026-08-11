# Replan

> **Status: outline.** The thesis document. Must be complete before T2 opens — golden test
> objective values come from here.

## The disruption metric

Five definitions, escalating. All are defensible; they produce different rosters, and that fact is
the point.

| ID | Definition | Status |
|---|---|---|
| D0 | Count of changed assignments | rejected — a published cancellation and an unpublished move score alike |
| D1 | Weighted by publication state (unpublished ≈ free, published costs, past pinned) | superseded |
| D2 | D1 + weighted by notice horizon, with a step at 24h | **shipped default** |
| D3 | D2 + weighted by change type (cancel / extend / shift / newly called in) | configurable |
| D4 | D3 + concentration penalty — five changes to one person is worse than one change to five | configurable |

`[TODO]` Exact formulation of each. D4 needs a max-term or convex per-employee penalty, not a sum.

## Commensuration with cost and coverage

`[TODO — decision required]` Lexicographic (feasibility → disruption → cost) or weighted. If
weighted, state the exchange rate explicitly — *one published-shift change ≈ €X overtime* — rather
than tuning weights until the output looks reasonable.

## Understaffing: hard or soft

`[TODO — decision required]` If `R-COVER` is soft, its penalty sits on the same scale as disruption
and coverage has been priced against stability. That is a defensible choice and an explicit one.

## Warm starting

Tomorrow's roster is ~95% of today's. Hints from the previous solution, and the measured speedup —
isolated from the objective effect by the cold disruption-objective baseline in `benchmarks.md`.

## Generation as cold start

Generation is a replan from an empty roster: nothing is published, nothing is pinned, disruption is
zero for every assignment. No separate formulation.
