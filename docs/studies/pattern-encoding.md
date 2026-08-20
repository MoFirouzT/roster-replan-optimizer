# Pattern/column variables against assignment booleans

**Question.** [`model.md`](../specs/model.md) calls pattern variables "dramatically stronger
formulations, evaluated as a study at these instance sizes", and [`D-009`](../decisions.md#d-009) had been open since the model was first written.

**Answer.** Competitive on a replan, catastrophic on a cold week. Enumerating patterns and solving
takes about the same total time as the assignment model when most of the horizon is pinned — and on a
cold week it **fails to prove optimality within 30 seconds on 5 of 6 cases** (re-verified over the
widened set — [`D-107`](../decisions.md#d-107)), against roughly 20
milliseconds for the assignment model. [`D-009`](../decisions.md#d-009) closes in favour of assignment booleans, and not
narrowly.

    uv run python -m benchmarks.studies --only patterns

## The formulation is real, not a sketch

One boolean per (employee, legal weekly pattern), exactly one true per employee. Coverage sums the
chosen patterns' slots. **Every per-employee rule disappears from the model** — rest gaps, daily and
weekly hours, consecutive days, weekly rest, the pinned past — because a pattern breaking one is
never enumerated. What is left is coverage, skill mix and the objective.

The objective survives intact, which is the formulation's most attractive property. D0–D2 price
disruption per changed slot, so a pattern's disruption is a **constant** computed at enumeration time
and the model is linear in the pattern booleans with no auxiliary variables at all. D3 and D4 would
carry over the same way, decomposing per employee-day and per employee.

Patterns are validated by the **checker**, not by re-deriving the rules — the same independent oracle
the greedy baseline uses, for the same reason. And the study checks that both formulations reach the
same optimum before comparing any timing.

## Replan: a tie, for a reason that is not about the formulation

| case | patterns | enumerate | build | search | **total** | assignment |
| --- | --- | --- | --- | --- | --- | --- |
| `small/0` | 36 | 4.7 ms | 0.8 | 1.0 | **6.5 ms** | 7.5 ms |
| `headline/0` | 50 | 7.7 | 1.2 | 1.2 | **10.1** | 10.9 |
| `loose/0` | 62 | 7.1 | 1.3 | 1.0 | **9.4** | 9.2 |
| `tight/0` | 51 | 8.4 | 1.2 | 1.2 | **10.9** | 10.9 |
| `scarce-skill/0` | 48 | 7.0 | 1.2 | 1.2 | **9.5** | 9.6 |
| `large/0` | 122 | 30.7 | 4.7 | 2.6 | **38.1** | 24.1 |

Thirty-six to 122 patterns for a whole tenant is a startlingly small number, and the reason is
`R-PIN-PAST` rather than anything clever: `now` sits at day 5, hour 9, so **five of the seven days are
already pinned** and the enumeration ranges over two days. The pattern space of a replan is small
because a replan is mostly not a choice.

Note that it already loses at 25 employees, where enumeration alone costs more than the entire
assignment solve.

## Cold: it does not finish

The same tenants with the whole horizon open — the honest test of whether enumeration scales.

| case | patterns | enumerate | search | total | assignment | outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `headline/0` | 9,740 | 1,200 ms | 30,001 | 31,254 | 29 ms | no proof (feasible only) |
| `loose/0` | 4,694 | 445 | 30,001 | 30,471 | 24 | no proof |
| `tight/0` | 9,740 | 1,233 | 30,001 | 31,288 | 19 | no proof |
| `small/0` | 5,180 | 526 | 29,983 | 30,549 | 122 | no proof |
| `scarce-skill/0` | 5,254 | 538 | 30,002 | 30,572 | 21 | no proof |
| `large/0` | 19,495 | 6,674 | 7,905 | 14,712 | 87 | same optimum |

Two independent failures, and the second is the serious one:

**Enumeration alone is 20 to 60 times the assignment model's entire solve.** 1.2 seconds to build a
catalogue against 29 milliseconds to answer the question. This is a fixed cost per tenant per horizon
and could be cached, so on its own it would be an argument about caching rather than about
formulations.

**The pattern model cannot prove optimality.** Five of six cold cases hit a 30-second limit with a
feasible solution and no proof, where the assignment model proves optimality in about 20
milliseconds. That is not a cost that caching removes. With no incumbent the objective is peak plus
cost, which is close to indifferent, and thousands of near-identical pattern columns give CP-SAT an
enormous symmetric search space with nothing to guide it. The formulation that was supposed to be
"dramatically stronger" is dramatically weaker here, and the mechanism is the one symmetry breaking
was invented for — the pattern encoding *creates* the symmetry that
[`symmetry-breaking.md`](symmetry-breaking.md) found the assignment model does not have.

## What this does not say

It does not say column-based formulations are wrong for rostering. It says **explicit enumeration** is
wrong at this horizon and these sizes. The standard technique is column generation — start with a few
patterns and generate more from the dual prices — which is a different project, needs an LP relaxation
CP-SAT does not expose, and would be evaluated against an assignment model that already answers in 20
milliseconds.

It also does not travel to longer horizons, in the direction people expect. At a four-week reference
period the enumeration is `4^28` rather than `4^7`, so explicit enumeration gets worse, not better.
The regime where patterns win is one where each employee has few legal patterns and coverage is the
hard part — which is the replan case, which the assignment model already handles in 10 milliseconds.

**[`D-009`](../decisions.md#d-009) closes: assignment booleans, measured, not assumed.**
