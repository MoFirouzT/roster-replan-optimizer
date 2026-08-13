# Studies index

Analyses behind decisions, including **nulls and rejected alternatives**.

Their value is almost entirely as interview material, so being able to find one again is the point. One line per
study, **including the ones that found no effect** — a measured null is a stronger signal than an
unmeasured win.

| Study | Question | Outcome |
|---|---|---|
| `disruption-metrics.md` | Do D0–D4 produce different rosters? | `[TODO — T2]` |
| `warm-start.md` | Speedup from hinting the previous solution, isolated from the objective effect | **9% of search time** (median paired ratio 0.907, faster on 201/216), invisible end to end. `D-082`, [`benchmarks.md`](../benchmarks.md) |
| `presolve.md` | Eliminating impossible (employee, shift) pairs before the solver | `[TODO — T2]` |
| `symmetry-breaking.md` | Lexicographic ordering over interchangeable employees — and how much the disruption objective already breaks | `[TODO — T2]` |
| `regular-constraint.md` | `regular` automaton vs. linear expansion for legal shift sequences | `[TODO — T2]` |
| `pattern-encoding.md` | Pattern/column variables vs. assignment booleans at 8–25 employees | `[TODO — T2]` |
| `time-budget.md` | Solution quality at 1s / 5s / 30s | **No curve to draw**: all 2,160 runs returned `OPTIMAL`, longest search 12.4 ms. A result about the instance distribution, not the solver. [`benchmarks.md`](../benchmarks.md) |
