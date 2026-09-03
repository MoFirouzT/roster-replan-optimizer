# Five ways to make this faster, and why none of them ships

**Question.** [`D-127`](../decisions.md#d-127) put a number on where the model stops, about 40
employees over four weeks, and left the obvious follow-up open: can that be moved? This is the
sweep of every lever available without changing what the model means.

**Answer. Five levers, five nulls, and the nulls have one cause between them.** A hand-written
model builder is *slower* than the library it would replace. Removing the assumption literals
loses the proof of optimality. The interval rest-gap encoding cuts variables by 7.1× and searches
more slowly. Parallel workers change a replan not at all. And the instance generator cannot reach
the sizes where any of it would matter.

**Nothing here has a performance problem.** A committed case is 8 to 25 employees over one week
and proves optimality in about 3 ms, so there is no latency to recover. Every null below is a
statement about that regime rather than about the lever, which is the single most important thing
to carry away from this page.

*Assumes: the envelope in [`limits.md`](../guide/limits.md); the formulation in
[`model.md`](../internals/model.md).*

## Conditions

ortools 9.15.6755, protobuf 6.33.6 resolving to the C `upb` implementation, Python 3.12, macOS on
Apple silicon. **Single worker except where a row says otherwise**, seed 7, which is how
[`benchmarks.md`](../benchmarks.md) measures everything. Foreign instances are the nurse-rostering
imports described in [`foreign-incumbent.md`](foreign-incumbent.md).

## The five

| lever | measured | verdict |
| --- | --- | --- |
| Write the `CpModelProto` by hand | 5.01 µs per constraint against the wrapper's 3.75 | **slower** |
| Drop the per-instance gate literals | 15% off build, 52% off search, then no proof of optimality | **rejected** |
| `R-REST-GAP` as intervals rather than pairs | 7.1× fewer variables, slower search at every size | **rejected** |
| Parallel search workers | 0.38 s at 1, 4 and 8 workers on the same replan | **null** |
| A larger instance to justify any of it | the generator tops out well inside the envelope | **not reachable** |

### A faster builder does not exist inside Python

Bypassing the Python expression machinery and writing constraints straight into the proto costs
**5.01 µs** per gated two-term constraint against the wrapper's **3.75 µs**. `protobuf` already
resolves to its C implementation, and creating one boolean at all costs 1.35 µs. The cost is
making millions of objects from Python, not the loop that asks for them, so batching does not
move it. Full numbers in [`gate-cost.md`](gate-cost.md).

That closes [`D-127`](../decisions.md#d-127)'s open question negatively. Getting past the build
ceiling means emitting fewer objects or leaving Python, and only the second is untried.

### The gates are not the overhead they look like

Removing the assumption literals halves the variables and takes 30% off the solve on the committed
set, helping on 28 of 28 paired cases. On a tight week it then fails to prove optimality on three
of eight instances, holding a roster scoring 480 for 30 s while the bound sits at −7980. They are
carrying search, not only reporting ([`D-153`](../decisions.md#d-153)).

### The interval rest-gap encoding wins on size and loses on time

[`encoding-levers.md`](encoding-levers.md#rest-gaps-as-intervals) rejected `rest="intervals"` at one week and said
plainly that the scaling claim behind it was never tested, because this project's horizon is one
week. It is tested now.

On foreign instance 13, 120 staff over four weeks, it cuts the model from **910,608 variables to
128,080** and the build from 9.73 s to 5.86 s. That is the predicted win and it is large.

It does not survive contact with the search. Across a generated sweep of 12 to 100 employees over
1 to 8 weeks, it is **slower to search at nearly every point**: 5.74 s against 7.51 s at 50 staff
over 8 weeks, 1.57 s against 1.66 s at 25 over 8. The one-week verdict holds out to eight weeks.

It also cannot be timed where it wins. Every large foreign instance is refused before search,
because its incumbent has an illegal past ([`foreign-incumbent.md`](foreign-incumbent.md)), so the
encoding that shrinks the biggest model is the one whose search nobody can measure there.

### Parallel workers do nothing for a replan

Foreign instance 6, the largest replan that still solves, at 1, 4 and 8 workers: **`OPTIMAL` in
0.38 s every time**, to two decimals.

Workers do matter to a model without gates, where 8 of them turn a 30 s timeout into 19 ms
([`gate-cost.md`](gate-cost.md)), and to a cold solve at four weeks, where no worker count is
enough and all three return `UNKNOWN` at 120 s. Neither is the shipped replan path. `num_workers`
also parallelises **search only**; the build is single-threaded and must finish first, so it
cannot touch the ceiling that actually binds.

### The generator cannot reach the sizes that would justify any of this

A controlled sweep, employees against horizon, single worker, 60 s budget:

| staff × weeks | variables | build | search | status |
| --- | --- | --- | --- | --- |
| 12 × 1 | 1,051 | 0.01 s | 0.01 s | `OPTIMAL` |
| 100 × 1 | 8,337 | 0.07 s | 0.05 s | `OPTIMAL` |
| 50 × 4 | 16,084 | 0.19 s | 1.12 s | `OPTIMAL` |
| 50 × 8 | 32,064 | 0.63 s | 5.74 s | `OPTIMAL` |
| **100 × 8** | **63,611** | 1.86 s | **60 s** | **`FEASIBLE`** |

**This bounds [`D-105`](../decisions.md#d-105) from the other side.** That record concluded the
generator cannot produce a hard instance, having swept 8 to 25 employees over one week. It can, at
100 employees over 8 weeks, which is four times the staff and eight times the horizon this service
claims. The generator is not the limitation; the envelope is.

For scale, the whole sweep is roughly **50× smaller** than the foreign instances at the same
nominal size: 100 staff over 8 weeks is 63,611 variables against instance 13's 910,608 at 120 over
4, because these instances carry three shift types where theirs carry many more.

## What would actually move it

Named so that the next person starts from the measurements rather than from the list.

**Emit fewer objects.** The only build-side lever with evidence behind it. The gates are 89% of
the largest model ([`gate-cost.md`](gate-cost.md)) and presolve deletes them, but removing them
costs the optimality proof, so this needs an encoding change rather than a switch.

**Leave Python for construction.** Untried, and the only untried build-side lever. Expect a large
factor; expect also that it buys a model whose search is still unmeasured at that size.

**Restrict to a neighbourhood of the incumbent.** The objective prices deviation, so a solution
scoring `Z` changes at most `Z / min_change_weight` assignments, and that bound is sound because
every objective term is a non-negative weight on a non-negative quantity. It restricts the
*search*; restricting the *model* needs a reduced-cost argument, which is column generation, which
[`encoding-levers.md`](encoding-levers.md#pattern-variables) has already measured the enumeration form of.

**Roll the horizon.** [`horizon.md`](horizon.md) already measured four weeks solved one at a time
reaching identical coverage to four solved at once. It is a heuristic whose correctness lives
entirely in the carried boundary state, and [`D-123`](../decisions.md#d-123) is the standing lesson
about getting that wrong.

None of these is scheduled. [`D-156`](../decisions.md#d-156) closes the effort, and the reason is
not that the levers are bad but that the regime does not need them.

---

*Behind this: [`D-156`](../decisions.md#d-156), and [`D-153`](../decisions.md#d-153) for the two
levers measured in [`gate-cost.md`](gate-cost.md). The index: [`README.md`](README.md).*
