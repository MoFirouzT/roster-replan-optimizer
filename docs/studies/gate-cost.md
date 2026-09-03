# What the gates cost, and what a faster builder would buy

**Question.** [`D-127`](../decisions.md#d-127) states where the model stops and leaves one thing
open in writing: the ceiling is *"a Python loop emitting constraints one at a time"* and
*"whether batching construction moves it is not measured"*. Five documents repeat the first half.
Behind it sits a second question nobody had asked: every hard constraint instance carries its own
literal ([`D-002`](../decisions.md#d-002)), the count reaches **1,416,134 literals against 60,480
assignment variables** on the largest foreign instance that still builds, and they are read on one
path only. What are they costing the other solves?

**Answer. Two nulls, and the second one reverses the question.** A faster builder does not exist
inside Python: writing the proto by hand is *slower* than the wrapper it bypasses. And the gates
are not a tax on the solve. Removing them halves the variables and takes 30% off the solve on the
committed set, and then **loses the proof of optimality outright** on a tight week, turning 0.045 s
into a 30 s timeout. The literals are carrying search, not only reporting.

    uv run python -m benchmarks.studies --only gates

## Conditions

ortools 9.15.6755, protobuf 6.33.6 resolving to the C `upb` implementation, Python 3.12, macOS on
Apple silicon. **Single worker unless a row says otherwise**, seed 7, which is how
[`benchmarks.md`](../benchmarks.md) measures everything. The committed figures are the median over
168 solves: the 84 committed cases, each solved as a replan and as a cold week.

The gated model is built as it ships and its literals are passed to `add_assumptions`. The ungated
model is `build(gated=False)`: the same feasible set, stated with no per-instance literal.

## A faster builder is not available

The claim under test is that construction is slow because of how it is written, so writing it
another way would speed it up. It is not.

| Emitting one gated two-term constraint | per constraint |
| --- | --- |
| `model.add(x + y <= 1).only_enforce_if(g)`, as shipped | 3.75 µs |
| the same, written straight into the `CpModelProto` | **5.01 µs** |
| `add_bool_or([¬x, ¬y, ¬g])`, the clause form of the same thing | 3.93 µs |
| the clause, written straight into the proto | 3.01 µs |
| `new_bool_var` alone, no constraint at all | 1.35 µs |

**Bypassing the Python wrapper is slower than using it.** The wrapper is already backed by C, and
hand-writing repeated protobuf field access from Python costs more than the expression machinery it
replaces. The best rewrite available is the clause form written directly, at about **1.2×**, and it
is not free: a clause states the same thing only for the two-term case, so it is not a general
substitution for the linear constraints.

The floor is the point. Creating a boolean at all costs 1.35 µs and emitting any constraint costs
about 3 µs, so a model of 2.2 million constraints costs seconds to state in Python whatever the
loop looks like. **The cost is building millions of protobuf objects, not the loop that asks for
them**, and batching does not move it.

[`D-127`](../decisions.md#d-127)'s sentence therefore stands as a bound and falls as an
explanation. Where the model stops is still about 40 employees over four weeks. What is now
measured is that a faster builder is not what would lift it.

## What the gates cost, and what they buy

On instance 13 of the foreign set, 120 staff over four weeks, the shipped build takes about 18 s
and emits 1,416,134 literals. Handing every constraint one shared literal instead cuts that to
14.6 s: **the literals are 19% of build**, in line with the 21% of search
[`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) already measured.

Across the committed set the saving is large and looks free. Paired per case, best of five runs,
28 cases, through [`lab.py`](../../benchmarks/lab.py):

| quantity | ratio, ungated over gated | helped | hurt |
| --- | --- | --- | --- |
| variables | 0.484 | 28 | 0 |
| constraints | 1.000 | 0 | 0 |
| build | 0.851 | 28 | 0 |
| search | 0.475 | 28 | 0 |
| total | 0.698 | 28 | 0 |

**Half the variables, 15% off build, 52% off search, and it helps on 28 of 28.** Constraint count is
untouched, which is the check that the two models state the same thing.

Under the shipped objective, fairness terms included, across all 84 cases solved both as a replan
and as a cold week: both builds prove optimality on **168 of 168** and agree on the objective
**168 of 168**.

On this distribution the gates are an overhead worth removing, and that reading is wrong.

### Where it breaks

The committed set is loose enough that the bound is easy to close whatever the model looks like.
`tight_week` is not: eight interchangeable staff, 37 slots, **34.7 net hours each against a
38-hour cap**, so the weekly ceiling binds nearly everywhere. It is run as a replan around a sick
call, plus the seven relaxations of its own rules that the property suite uses for monotonicity.

| instance | gated | ungated |
| --- | --- | --- |
| base | `OPTIMAL` 0.048 s | `OPTIMAL` 7.715 s |
| shorter rest gap | `OPTIMAL` 0.045 s | `OPTIMAL` 20.033 s |
| less weekly rest | `OPTIMAL` 0.045 s | **`FEASIBLE` 30 s** |
| consecutive days off | `OPTIMAL` 0.045 s | **`FEASIBLE` 30 s** |
| more consecutive days | `OPTIMAL` 0.044 s | **`FEASIBLE` 30 s** |
| bigger weekly budget | `OPTIMAL` 0.048 s | `OPTIMAL` 2.882 s |
| bigger daily maximum | `OPTIMAL` 0.050 s | `OPTIMAL` 7.770 s |
| absences lifted | `OPTIMAL` 0.039 s | `OPTIMAL` 1.699 s |

**Three of the eight lose the proof of optimality outright**, and the five that keep it pay 35× to
445×. Every one of these is a legal week a tenant could ask for.

Isolating phase one on *less weekly rest*:

| | workers | status | time | bound | optimum |
| --- | --- | --- | --- | --- | --- |
| Gated, assumptions passed | 1 | `OPTIMAL` | 0.014 s | 480 | 480 |
| Ungated | 1 | `FEASIBLE` | 30.0 s | **−7980** | 480 |
| Ungated | 8 | `OPTIMAL` | 0.019 s | 480 | 480 |

**The ungated search finds the optimum immediately and cannot prove it.** It holds a roster scoring
480 the whole time; what it cannot do is lift the bound off −7980. Eight workers close it in 19 ms,
so this is a property of the single-worker search rather than of the model's difficulty. Every
number in [`benchmarks.md`](../benchmarks.md) is single-threaded, which is the configuration this
matters in.

**Why the literals help is not established here.** Two shapes were tried and both are slow: no
literal at all, and one shared literal fixed true. So it is not the enforcement machinery being
weak, since the shared-literal model keeps that machinery and still fails. What the fast
configuration has that neither of the others does is many distinct literals fixed by
`add_assumptions`. This study measures that difference and does not explain it, and saying so beats
inventing a mechanism.

## What this changes

**`gated=False` is a study switch, not a mode.** It joins the four in
[`model.py`](../../roster_replan/model.py) that exist so a rejected alternative stays measurable.
Shipping it would trade 30% of the solve on the easy distribution for a solver that cannot prove
optimality on the next tight week it meets, and the fallback ladder would report that as a time-boxed
answer with a gap rather than as a defect.

It also gives [`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) its missing code. That study's *CP-SAT,
ungated* row had no committed way to reproduce it before this switch existed.

**[`D-002`](../decisions.md#d-002) is confirmed on a reason it was not chosen for.** The gates were
justified as the reporting apparatus: what lets a failed solve name the conflicting rule instances.
They are also doing search work, and the honest reading of the 21% in
[`cp-sat-vs-milp.md`](cp-sat-vs-milp.md) is that it is what the gates cost **on a distribution
where the bound is easy to close**, not what they cost in general.

**The committed set could not have found this**, and that is the third time. 168 of 168 solves are
untroubled by removing the gates; the failure is on seven hand-built relaxations of a single week.
[`D-105`](../decisions.md#d-105) read easy solves as nothing being hard,
[`D-127`](../decisions.md#d-127) corrected that with foreign data, and
[`penalty-search.md`](penalty-search.md) found the easy set would have falsified
[`D-002`](../decisions.md#d-002) outright. The generator's distribution is where this project
cannot see itself.

## Found on the way: the canonical optimum is not canonical

Perturbing the model exposed a defect that has nothing to do with gating.

[`D-119`](../decisions.md#d-119) makes the roster a function of the model rather than of the search
by pinning the optimal value and minimising a canonical criterion over the optimal set. The
criterion is `Σ ordinal² · x` ([`model.md`](../internals/model.md)). **Sums of squares collide**, so
the criterion is not a total order and the promise does not hold. On `flexi-heavy/2`, the gated and
ungated builds both return a proved optimum, both report `canonical`, and they differ by six
assignments:

```text
objective    3        vs   3
criterion    299796   vs   299796
only in one    ordinals 6, 85, 161      6² + 85² + 161²  = 33182
only in other  ordinals 7, 83, 162      7² + 83² + 162²  = 33182
```

The committed manifest was stable because seed 7 on the shipped model happened to land on the same
tied roster every time, not because the roster was determined. This is the same failure
[`reproducibility.md`](reproducibility.md) reports, one level further in: that study removed the
degeneracy the search could see, and left a smaller set the criterion cannot separate.

It is recorded rather than fixed here. A criterion that cannot tie needs weights no two subsets can
share, and the obvious ones overflow long before 60,000 variables, so this is a design question and
not a patch. See [`D-154`](../decisions.md#d-154).

---

*Behind this: [`D-153`](../decisions.md#d-153) and [`D-154`](../decisions.md#d-154), and the work order
[`gating-cost.md`](../specs/gating-cost.md). The index: [`README.md`](README.md).*
