# CP-SAT against MILP

**Question.** [`D-001`](../decisions.md#d-001) — *CP-SAT over MILP* — was the one T1 record still owed, and
[`decisions.md`](../decisions.md) said why it stayed owed: no spec argued it, so it could not be
written without inventing a rationale nobody had. This is the comparison that was needed instead.

**Answer.** **CP-SAT is not the faster solver here, and the record now says so.** SCIP proves the same
optimum faster on **24 of 24** cases — 38% faster than the shipped configuration. CP-SAT ships anyway,
for three capabilities the project already depends on and MILP cannot supply. The honest form of
[`D-001`](../decisions.md#d-001) is *chosen for the assumption literals, at a measured cost of about 1.3 ms per solve*, not
*chosen because it is better at scheduling*.

    uv run python -m benchmarks.milp
    uv run python -m pytest tests/test_milp.py

## The comparison

`benchmarks/milp.py` states the same feasible set for a branch-and-cut solver. SCIP 10 and CBC both
ship inside `ortools`, so this needed no new dependency — and it is therefore a comparison against
**open-source** MILP, not against Gurobi, which is the main limit on what follows.

All objectives are identical on every case, asserted by `tests/test_milp.py` before any timing is
read. That makes the MILP a third reading of `rules.md` alongside the model and the checker.

| | search p50 | faster than shipped CP-SAT |
| --- | --- | --- |
| CP-SAT, gated — **what ships** | 3.30 ms | — |
| CP-SAT, ungated | 2.73 ms | — |
| **SCIP** | **2.04 ms** | **24/24** |
| CBC | 3.21 ms | 11/24 — a coin flip |

**The gates cost 21% of CP-SAT's search time**, and half of its variables. Every hard constraint
instance carries an assumption literal ([`D-002`](../decisions.md#d-002)), so the shipped model holds 534 gate literals against
183 assignment variables on `headline/0`. SCIP is given no such burden — and still wins 24/24 against
the *ungated* model, so the gap is not merely the reporting apparatus. On this problem, at this size,
branch-and-cut is simply faster.

**In end-to-end terms the difference is small.** 1.3 ms against a build that costs about 5 ms
regardless of backend ([`D-092`](../decisions.md#d-092)), so the solver choice moves roughly 15% of a request and the Python
model construction moves more.

## What MILP cannot do, which is the actual reason

Three capabilities, each already load-bearing:

**Assumption literals, and therefore infeasibility cores.** CP-SAT returns the rule instances in
conflict when a solve fails ([`D-048`](../decisions.md#d-048)), which is exactly what T4's explainer consumes and what [`D-013`](../decisions.md#d-013)
insists must come from the solver rather than from an LLM. MILP has no assumption mechanism; an IIS is
a different object with different guarantees and is not exposed through `pywraplp` at all.

**`violations()`, the differential harness's reporting surface.** With every assignment fixed,
maximising the number of true gate literals leaves precisely the violated constraints false, so one
solve enumerates every violation ([`D-044`](../decisions.md#d-044)). This trick *is* the assumption mechanism. Without it the
model can only refuse a roster, and comparing "refuses" against the checker's violation set is the
vacuous comparison [`D-065`](../decisions.md#d-065) rejects.

**Non-linear expressiveness.** D3 and D4 pair a drop with an add through `min(drops, adds)`.
`add_min_equality` states it; MILP needs auxiliary binaries and big-M per (employee, day).
`benchmarks/milp.py` **refuses** D3 and D4 rather than comparing a linearised approximation and
calling it the same problem. The `regular` automaton and `no_overlap` are in the same category —
rejected on their merits ([`D-088`](../decisions.md#d-088), [`D-089`](../decisions.md#d-089)), but they were available to reject.

## The finding that would bite hardest on a switch

**MILP's default relative MIP gap is unsafe at this objective's scale, and it fails silently.**

`pywraplp` defaults `RELATIVE_MIP_GAP` to `1e-4`. That is a *relative* tolerance, and this objective
is not on a scale where that is small: `shortfall_weight` is 100,000 so that coverage dominates
disruption ([`D-057`](../decisions.md#d-057)), so any roster leaving one shift unstaffed scores in the hundreds of thousands —
and `1e-4` of that is an absolute slack of about **30 disruption points**, roughly ten changed shifts.

At the default, SCIP returned a roster scoring 300003 and **reported it `OPTIMAL`** while 300001 was
feasible. CP-SAT is exact by default and has no equivalent knob, so the first version of this study
was timing an approximation against a proof and reporting the approximation as the winner.

It was caught by the cross-formulation equivalence test, not by reading the output — the numbers were
plausible, the status said `OPTIMAL`, and only a second formulation disagreeing exposed it. The
timings above are all with the gap forced to zero.

The general form is worth carrying beyond this study: **the weight that makes coverage dominate also
makes any relative termination criterion coarse.** Any future solver with a gap tolerance inherits
this, and the domination bound is what creates it.

## Limits of this comparison

- **Open-source MILP only.** Gurobi would likely be faster still and would not change the three
  capability arguments, which are structural rather than a matter of solver quality.
- **D0–D2 only.** D3 and D4 are refused, which is itself a result.
- **No `R-SKILL-MIX`.** It clamps to `min(minimum, headcount)`; no committed case carries an entry.
- **Replan configuration, small instances.** 8–25 employees, one week. Nothing here says how the
  ranking behaves at a four-week horizon, where the constraint counts grow differently.
