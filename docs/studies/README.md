# Studies index

Analyses behind decisions, including **nulls and rejected alternatives**.

Their value is almost entirely as interview material, so being able to find one again is the point. One line per
study, **including the ones that found no effect** — a measured null is a stronger signal than an
unmeasured win.

| Study | Question | Outcome |
|---|---|---|
| [`disruption-metrics.md`](disruption-metrics.md) | Do D0–D4 produce different rosters? | **Yes, on 23/72, at ~100% relative regret both ways** — but only D0/D1/D2 against D3/D4. Within each side, nothing separates them here, and D4 is unexercised. `D-085`, `D-086` |
| `warm-start.md` | Speedup from hinting the previous solution, isolated from the objective effect | **9% of search time** (median paired ratio 0.907, faster on 201/216), invisible end to end. `D-082`, [`benchmarks.md`](../benchmarks.md) |
| [`presolve.md`](presolve.md) | Eliminating impossible (employee, shift) pairs before the solver | **28% off build, 16% off search, 24/24 cases** — a quarter of the model removed. Not "the largest single win": caching the compiled model is. [`D-045`] |
| [`symmetry-breaking.md`](symmetry-breaking.md) | Lexicographic ordering over interchangeable employees — and how much the disruption objective already breaks | **Null: 3 interchangeable employees across 24 cases.** Worth 20% on a workforce built to be symmetric, so the null is about the distribution. `D-087` |
| [`regular-constraint.md`](regular-constraint.md) | `regular` automaton vs. linear expansion for legal shift sequences | **Rejected: 20% slower, 24/24.** At a 7-day horizon there is exactly one window to replace, and the automaton also loses the day coordinate. `D-088` |
| [`pattern-encoding.md`](pattern-encoding.md) | Pattern/column variables vs. assignment booleans at 8–25 employees | **Rejected: no proof of optimality in 30s on 5 of 6 cold cases**, against ~20ms. Ties on replans only because the past pins the week. `D-009` |
| `time-budget.md` | Solution quality at 1s / 5s / 30s | **No curve to draw**: all 2,160 runs returned `OPTIMAL`, longest search 12.4 ms. A result about the instance distribution, not the solver. [`benchmarks.md`](../benchmarks.md) |
