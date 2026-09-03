# Studies index

Analyses behind decisions, **including the nulls and the rejected alternatives**.
A measured null is a stronger signal than an unmeasured win, so they are indexed the same way.

One line per study.
The line is a locator, not a summary: the study holds the method, the numbers and the caveats, and the decision records hold what was done about them.

*Assumes: the instance distribution these were measured on, [`benchmarks.md`](../benchmarks.md); the objective they measure against, [`model.md`](../internals/model.md).*

| Study | Question | Outcome |
| --- | --- | --- |
| [`reproducibility.md`](reproducibility.md) | Does the same input return the same roster? | **No: the optimum was degenerate.** Fixed by canonicalising it, at 61% of search time. Found by CI, not by a test |
| [`disruption-metrics.md`](disruption-metrics.md) | Do D0–D4 produce different rosters? | **Yes, on 10 of 84**, and only D0/D1/D2 against D3/D4. Within each side, nothing separates them |
| [`weight-recovery.md`](weight-recovery.md) | Can a tenant's soft weights be recovered from the rosters they publish? | **No signal at all**: the objective is priced but not pivotal. Retires the learning work |
| [`penalty-search.md`](penalty-search.md) | What does pricing a hard rule instead of prohibiting it do? | **Confirms [`D-002`](../decisions.md#d-002), and the easy set alone would have falsified it.** On the hard instance no weight works |
| [`foreign-incumbent.md`](foreign-incumbent.md) | Does the headline claim hold on a roster this project did not produce? | **Yes, by a wider margin: 4.6–37× fewer changes.** Also the first genuinely hard searches, and the model's ceiling |
| [`cross-week-reach.md`](cross-week-reach.md) | How far does the objective reach past one week, and how badly does the gap show? | **One term of the objective has memory; everything else is a function of the payload alone.** Measured against somebody else's constraint set, cold generation breaks all seven of theirs, and not in the order this project would have guessed |
| [`horizon.md`](horizon.md) | Does a longer horizon cost what the spec says, and buy anything? | **Rejection upheld, both its reasons wrong.** Size is linear; a longer horizon buys nothing |
| [`model-cache.md`](model-cache.md) | Per-tenant compiled-model caching, as [`service.md`](../guide/api.md) asks for | **0 hits in 144 solves**: a replan changes the model's own inputs. Profiling redirected the work, and the cache was later deleted ([`D-149`](../decisions.md#d-149)) |
| [`encoding-levers.md`](encoding-levers.md) | Does any textbook alternative beat the shipped encoding: presolve, symmetry, the `regular` automaton, interval rest gaps, pattern variables? | **One ships, four rejected**, and three of the four lose the same way: a global constraint carries one literal, so a failure stops naming a rule instance |
| [`scaling-levers.md`](scaling-levers.md) | Can the model be made to go further, by any lever that does not change what it means? | **Five levers, five nulls.** A hand-written builder is slower, dropping the gates loses the optimality proof, the interval encoding searches slower, workers do nothing, and the generator cannot reach the sizes that would justify any of it |
| [`gate-cost.md`](gate-cost.md) | What do the per-instance assumption literals cost, and would a faster builder lift the ceiling? | **Two nulls.** Hand-writing the proto is *slower* than the wrapper; removing the gates halves the model, takes 30% off the solve, and then loses the proof of optimality on a tight week |
| [`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) | CP-SAT against branch-and-cut MILP | **CP-SAT is not the faster solver: SCIP wins 24 of 24.** It ships for assumption literals, at ~1.3 ms |
| [`warm-start.md`](warm-start.md) | Speedup from hinting the previous solution, isolated from the objective | **9% of search time**, invisible end to end. The objective is what does the work |
| [`time-budget.md`](time-budget.md) | Solution quality at 1 s / 5 s / 30 s | **No curve to draw**: all 2,268 runs returned `OPTIMAL`, longest search 15.4 ms |
| [`mutation-harness.md`](mutation-harness.md) | How is a test layer's claim to catch something checked? | **Four blind spots found behind green suites**, and five hardenings, each one the harness being confidently wrong |
| [`nl-parse.md`](nl-parse.md) | Does the parse read a tenant's words into the right fields, and leave the rest alone? | **18/18 on three consecutive runs**, Dutch and adversarial cases included |

## Merged

A study is merged when its question is better answered beside others, never when its answer became
inconvenient. The measurement travels with it and the conditions travel with the measurement.

| Was | Where it went |
| --- | --- |
| `presolve.md` | [`encoding-levers.md`](encoding-levers.md#presolve) |
| `symmetry-breaking.md` | [`encoding-levers.md`](encoding-levers.md#symmetry-breaking) |
| `regular-constraint.md` | [`encoding-levers.md`](encoding-levers.md#the-regular-automaton) |
| `rest-gap-encoding.md` | [`encoding-levers.md`](encoding-levers.md#rest-gaps-as-intervals) |
| `pattern-encoding.md` | [`encoding-levers.md`](encoding-levers.md#pattern-variables) |

Merged on 2026-09-03. All five ran through the same harness, asked the same shape of question and
answered it the same way, and two of them turn out to explain each other: the pattern encoding
creates exactly the symmetry the symmetry study found absent.
