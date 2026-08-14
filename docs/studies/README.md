# Studies index

Analyses behind decisions, including **nulls and rejected alternatives**.

Their value is almost entirely as interview material, so being able to find one again is the point. One line per
study, **including the ones that found no effect** — a measured null is a stronger signal than an
unmeasured win.

| Study | Question | Outcome |
|---|---|---|
| [`disruption-metrics.md`](disruption-metrics.md) | Do D0–D4 produce different rosters? | **Yes, on 26/84, at ~100% relative regret both ways** — but only D0/D1/D2 against D3/D4. Within each side nothing separates them, and D4 is unexercised. Divergence peaks mid-axis and is zero by 0.90 coverage. `D-085`, `D-086`, `D-106` |
| `warm-start.md` | Speedup from hinting the previous solution, isolated from the objective effect | **9% of search time** (median paired ratio 0.907, faster on 201/216; reproduced at 0.906 on 662/756 over the widened set), invisible end to end. `D-082`, `D-105`, [`benchmarks.md`](../benchmarks.md) |
| [`presolve.md`](presolve.md) | Eliminating impossible (employee, shift) pairs before the solver | **28% off build, 14% off search, 28/28 cases** — a quarter of the model removed. Not "the largest single win" — that is `Instance.window` (`D-092`). [`D-045`] |
| [`symmetry-breaking.md`](symmetry-breaking.md) | Lexicographic ordering over interchangeable employees — and how much the disruption objective already breaks | **Null: 3 interchangeable employees across 28 cases.** Worth 20% on a workforce built to be symmetric, so the null is about the distribution. `D-087` |
| [`regular-constraint.md`](regular-constraint.md) | `regular` automaton vs. linear expansion for legal shift sequences | **Rejected: 19% slower, 28/28.** At a 7-day horizon there is exactly one window to replace, and the automaton also loses the day coordinate. `D-088` |
| [`pattern-encoding.md`](pattern-encoding.md) | Pattern/column variables vs. assignment booleans at 8–25 employees | **Rejected: no proof of optimality in 30s on 5 of 6 cold cases**, against ~20ms. Ties on replans only because the past pins the week. `D-009` |
| [`rest-gap-encoding.md`](rest-gap-encoding.md) | `R-REST-GAP` as `no_overlap` intervals vs. pairwise inequalities | **Rejected at this horizon**: 12% faster build, 16% slower search, sign of the total flips by instance family. The scaling claim is about horizon length and stays untested. `D-089` |
| [`model-cache.md`](model-cache.md) | Per-tenant compiled-model caching, as `service.md` asks for | **0 hits in 144 replan solves** — a replan changes the model's own inputs. Profiling redirected the work: memoising `Instance.window` took **20% off build**, the largest single win in the solve path. `D-092`, `D-093` |
| [`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) | CP-SAT against branch-and-cut MILP, for `D-001` | **CP-SAT is not the faster solver**: SCIP wins 24/24. It ships for assumption literals and non-linear expressiveness, at a measured ~1.3 ms. MILP's default MIP gap reported a suboptimal roster as optimal. `D-001` |
| [`nl-parse.md`](nl-parse.md) | Does the parse read a tenant's words into the right fields, and leave the others alone? | **18/18 on three consecutive runs, after 16/18.** Extraction was right first time, Dutch and adversarial cases included; both failures were `unclear` used as an assumptions log, and one of those was the eval's own preference. `D-102`, `D-103` |
| [`horizon.md`](horizon.md) | Does extending the horizon to the reference period cost what `rules.md` says, and buy anything? | **Rejection upheld, both its reasons wrong.** Size is linear (3.9× for 4× the days), four weeks answers in ~112 ms — and a longer horizon buys **nothing**: identical coverage to four chained weekly solves on every case, while being 2–6× slower under pressure. `D-081`'s build-dominates premise inverts between one week and two. `D-115`, `D-116` |
| `time-budget.md` | Solution quality at 1s / 5s / 30s | **No curve to draw**: all 2,268 solver runs returned `OPTIMAL`, longest search 15.4 ms, and no answer changed with the budget on any of 756 (case, method, seed) triples. A result about the instance distribution, not the solver. [`benchmarks.md`](../benchmarks.md) |
