# Studies index

Analyses behind decisions, **including the nulls and the rejected alternatives**.
A measured null is a stronger signal than an unmeasured win, so they are indexed the same way.

One line per study.
The line is a locator, not a summary — the study holds the method, the numbers and the caveats, and the decision records hold what was done about them.

| Study | Question | Outcome |
| --- | --- | --- |
| [`reproducibility.md`](reproducibility.md) | Does the same input return the same roster? | **No — the optimum was degenerate.** Fixed by canonicalising it, at 61% of search time. Found by CI, not by a test |
| [`disruption-metrics.md`](disruption-metrics.md) | Do D0–D4 produce different rosters? | **Yes, on 10 of 84**, and only D0/D1/D2 against D3/D4. Within each side, nothing separates them |
| [`weight-recovery.md`](weight-recovery.md) | Can a tenant's soft weights be recovered from the rosters they publish? | **No signal at all** — the objective is priced but not pivotal. Retires the learning work |
| [`penalty-search.md`](penalty-search.md) | What does pricing a hard rule instead of prohibiting it do? | **Confirms [`D-002`](../decisions.md#d-002) — and the easy set alone would have falsified it.** On the hard instance no weight works |
| [`foreign-incumbent.md`](foreign-incumbent.md) | Does the headline claim hold on a roster this project did not produce? | **Yes, by a wider margin: 4.6–37× fewer changes.** Also the first genuinely hard searches, and the model's ceiling |
| [`horizon.md`](horizon.md) | Does a longer horizon cost what the spec says, and buy anything? | **Rejection upheld, both its reasons wrong.** Size is linear; a longer horizon buys nothing |
| [`presolve.md`](presolve.md) | Eliminating impossible (employee, shift) pairs before the solver | **Shipped: 28% off build, 14% off search, 28 of 28 cases.** A quarter of the model removed |
| [`model-cache.md`](model-cache.md) | Per-tenant compiled-model caching, as [`service.md`](../../guide/api.md) asks for | **0 hits in 144 solves** — a replan changes the model's own inputs. Profiling redirected the work, and the cache was later deleted ([`D-149`](../decisions.md#d-149)) |
| [`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) | CP-SAT against branch-and-cut MILP | **CP-SAT is not the faster solver — SCIP wins 24 of 24.** It ships for assumption literals, at ~1.3 ms |
| [`warm-start.md`](warm-start.md) | Speedup from hinting the previous solution, isolated from the objective | **9% of search time**, invisible end to end. The objective is what does the work |
| [`symmetry-breaking.md`](symmetry-breaking.md) | Lexicographic ordering over interchangeable employees | **Null: 3 interchangeable employees across 28 cases.** The null is about the distribution, not the lever |
| [`regular-constraint.md`](regular-constraint.md) | `regular` automaton vs. linear expansion for shift sequences | **Rejected: 19% slower, 28 of 28.** It also loses the day coordinate |
| [`pattern-encoding.md`](pattern-encoding.md) | Pattern/column variables vs. assignment booleans | **Rejected: no proof of optimality in 30 s on 5 of 6 cold cases**, against ~20 ms |
| [`rest-gap-encoding.md`](rest-gap-encoding.md) | `R-REST-GAP` as `no_overlap` intervals vs. pairwise inequalities | **Rejected at this horizon**: faster build, slower search, and the sign flips by instance family |
| [`time-budget.md`](time-budget.md) | Solution quality at 1 s / 5 s / 30 s | **No curve to draw** — all 2,268 runs returned `OPTIMAL`, longest search 15.4 ms |
| [`mutation-harness.md`](mutation-harness.md) | How is a test layer's claim to catch something checked? | **Four blind spots found behind green suites** — and five hardenings, each one the harness being confidently wrong |
| [`nl-parse.md`](nl-parse.md) | Does the parse read a tenant's words into the right fields, and leave the rest alone? | **18/18 on three consecutive runs**, Dutch and adversarial cases included |
