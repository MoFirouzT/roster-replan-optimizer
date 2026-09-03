# What the gates cost, and paying for them only when they are read

**Status:** Implemented 2026-09-03
**Depends on:** [`model.md`](model.md), whose formulation this changes the emission of.

## Objective

Settle on measurement what the per-instance assumption literals cost, and whether the model
construction ceiling is a Python loop that a faster builder would lift.

**As scoped, this component was to make the literals a cost paid only when a core is read.**
The measurement rejected that, so what shipped is the switch that made the measurement
possible and the record of what it found. The trail is in *Decisions* below.

## Motivation

[`D-127`](../decisions.md#d-127) states where the model stops and leaves one question open in
writing:

> The ceiling is this implementation's, not the formulation's. 527 seconds is a Python loop
> emitting constraints one at a time, so it bounds what this service answers today and says
> nothing about whether the encoding is right at that size. Whether batching construction
> moves it is **not** measured.

Five documents carry the second half of that claim
([`limits.md`](../guide/limits.md), [`internals/model.md`](../internals/model.md),
[`design.md`](../internals/design.md), [`model.md`](model.md) and the record itself), and none
of them measures it. It is the largest unmeasured claim left in the repository, and it is
load-bearing: a reader is being told the ceiling is incidental.

The question behind it is worth more than the answer. Every hard constraint instance carries
its own literal ([`D-002`](../decisions.md#d-002)), and the ratio of literals to assignment
variables grows with instance size: about 2.9 to 1 on a committed case, 23 to 1 on instance 13, and
**12 to 1 on the largest foreign instance, where they are 89% of the whole model**. The literals are
read in exactly one place,
`solve` returning a core on `INFEASIBLE`, and on a feasible solve they buy nothing.

## Canonical reference

[`internals/model.md`](../internals/model.md) owns the formulation, including the gate
section and the statement of where the model stops.
[`guide/rules.md`](../guide/rules.md) owns the predicates.

**This component adds no predicate and changes no feasible set.** It changes when the literals
are emitted, not what they mean, so the *Model encoding* bullet of every rule stays true as
written. The one canonical statement it may falsify is the "Python build loop" sentence, and
correcting that is a build task below.

## Governing reference

None. Nothing here touches a statutory parameter.

## Parameters and configuration

No profile or payload parameter. One build switch, which joins the four in
[`model.md`](model.md) as a **study switch** rather than the supported mode this spec first
proposed:

```text
build(instance, gated=True)     gated=False emits every hard constraint unconditionally
```

Nothing a caller sends reaches it. `solve` builds gated, as it always did.

## Interfaces

```text
model.build(instance, gated: bool = True) -> Built
model.solve(instance, ...)                -> unchanged signature and unchanged return types
model.violations(roster, instance)        -> unchanged
```

**`solve` is unchanged**, which is the component's result rather than an omission. The
two-phase rebuild this spec proposed is not there: an ungated model handed in through `built=`
and proved infeasible raises, because it holds no literal to read a core from and an empty core
would report that no rules conflict.

`Built` gains a `gated` flag, and `Built.gate` returns the empty enforcement list when it is
false, so every call site is untouched and the constraint enters the proto exactly as an
unconditional one.

## Layering

None. `model.py` keeps its position and imports nothing new.

## Build tasks

- [x] `gated` parameter on `build`, defaulting to today's behaviour
- [!] two-phase `solve`: **not built.** The measurement rejected it before it was worth
  writing, and `solve` now raises rather than inventing an empty core from an ungated model
- [x] the direct-proto measurement recorded as a null, with the numbers that produced it
- [!] re-measure the foreign scale table under the ungated build: **not done.** The switch is
  rejected, so a scale table taken under it would measure a configuration nothing runs
- [x] the study, [`gate-cost.md`](../studies/gate-cost.md), reproducible by
  `uv run python -m benchmarks.studies --only gates`
- [x] correct the "Python build loop" sentence: [`limits.md`](../guide/limits.md),
  [`internals/model.md`](../internals/model.md), [`design.md`](../internals/design.md),
  [`model.md`](model.md) and [`D-127`](../decisions.md#d-127) itself, through
  [`D-153`](../decisions.md#d-153)
- [x] the records: [`D-153`](../decisions.md#d-153) and [`D-154`](../decisions.md#d-154)
- [x] the mutant `model-ungated-still-gates`, caught by `tests/test_studies.py`

## Test contract

- **Studies** (`tests/test_studies.py`): `ungated` joins the variant table, so the same
  equivalence check the other four switches face applies here: the ungated build must reach the
  identical optimum on all five sample cases. Two dedicated tests carry the rest, that an
  ungated build states the same variables and the same constraint count with no literal at all,
  and that an ungated model proved infeasible raises rather than returning an empty core.
- **Golden** (`tests/test_golden.py`): the committed rosters are unchanged. This was the gate
  while `solve` was going to change; it now guards the fact that `solve` did not.
- **Differential** (`tests/test_differential.py`): unchanged and green. The checker never saw
  the gates, so a change confined to their emission cannot move it, and a failure here would
  have meant the feasible set moved.
- **Mutant**: `model-ungated-still-gates` makes `gated=False` keep the literals, so the study
  compares a model with itself and reports a null that is the harness. Named catcher:
  `tests/test_studies.py`, confirmed caught.

## Acceptance gate

*Blocks:* nothing. No component is waiting on this.

- [x] Roster identical to the committed golden: `tests/test_golden.py` green, and `solve` is
  unchanged, so no committed artifact moved
- [!] Core identical to the gated build on every infeasible case: **not applicable.** The
  two-phase rebuild was not built, so there is no second core to compare. An ungated model now
  raises instead
- [!] Median end-to-end saving of at least 20% over the committed set: **met and rejected.**
  30% off total, helping on 28 of 28 paired cases, and the switch is still not shipped, because
  the same change loses the proof of optimality on 3 of 8 tight-week instances
- [x] Full suite green: 948 passed
- [x] Mutant caught by its named layer. Verdict `unverifiable` rather than `clean`: the tree
  was dirty, which [`CLAUDE.md`](../../CLAUDE.md) allows while a layer is being proved

## Measured results

The reader-facing write-up is [`gate-cost.md`](../studies/gate-cost.md). What follows is the
builder's record, including the two measurements that were wrong on the way.

**The direct-proto builder is a null, and it is the answer to
[`D-127`](../decisions.md#d-127)'s open question.** Writing constraints into the `CpModel`
proto by hand, bypassing the Python expression machinery, is **slower** than the wrapper:
5.01 µs against 3.75 µs per gated two-term linear constraint. Emitting the same constraint as
a three-literal clause is 3.93 µs through the wrapper and 3.01 µs written directly, so the
best available rewrite is about 1.2×. `protobuf` already resolves to the C `upb`
implementation, and the floor is 1.35 µs to create a bool variable at all. Batching
construction does not move the ceiling, because the cost is building millions of protobuf
objects from Python rather than the loop that asks for them.

**What moves is emitting fewer of them**, and it moves a long way on the committed set: half
the variables, 15% off build, 52% off search, helping on 28 of 28 paired cases. Then it loses
the proof of optimality on 3 of 8 tight-week instances, and the switch is rejected. The tables
are in the study.

On instance 13, 120 staff over four weeks, the gated build emits **1,416,134 literals against
60,480 assignment variables** and takes about 18 s, of which the literals are 19%.

On instance 23, 100 staff over 52 weeks, it emits **7,143,329 literals against 582,382 assignment
variables**, 89% of the model, over a **606 s build** that presolve then strips with 7,132,828
applications of `enforcement: true literal`.

### Two things this got wrong before it got them right

**A shared literal fixed true is not the same as no literal.** The first implementation handed
every constraint one literal pinned to true, a five-line change against thirty call sites, and
it was chosen on an emission benchmark showing true ungating was worth only 12% more. That
benchmark measured the wrong thing. The shared-literal model keeps every constraint *enforced*,
and it lost the proof of optimality on the same instances the real ungated build later did. The
cheap version was rejected for the right reason only after it had been shipped into the working
tree and the suite had failed.

**`only_enforce_if([])` is what makes true ungating a small change.** An empty enforcement list
writes no literal, and the resulting proto is byte-identical to an unconditional constraint, so
the thirty call sites never had to move. That was checked against a hand-built proto rather than
assumed.

**The first measurement was taken without `_canonicalise` and was misleading.** It reported the
roster matching on only 15 of 24 cases, which read as a broken reproducibility promise. The
probe had called the solver directly and skipped phase two. What it had actually found was
[`D-154`](../decisions.md#d-154), one level down and genuinely broken.

## Out of scope

- **Large neighbourhood search.** Retired by [`D-104`](../decisions.md#d-104) and re-bounded
  by [`D-127`](../decisions.md#d-127); un-retiring it is a separate component and a larger one.
- **A controlled scaling sweep.** The foreign table stays the size evidence. Filling the range
  between its points is worth doing and is not this.
- **Coarser gates.** Reducing the literal count by widening what one literal covers trades
  away the coordinate `checker.py` matches on, which is the trade
  [`encoding-levers.md`](../studies/encoding-levers.md#rest-gaps-as-intervals) already refused once.
- **Fixing [`D-154`](../decisions.md#d-154).** Found here, recorded here, and left open here.
- **Any change to the feasible set**, the objective, or a rule predicate.

## Decisions

1. **Should the builder write the proto directly?** **Resolved: no** (2026-09-03). Measured at
   0.7× for linear constraints and 1.2× at best for clauses, against a wrapper that is already
   backed by C. The measurement is kept and published as a null, because it is what
   [`D-127`](../decisions.md#d-127) asked for and a reader who wonders the same thing deserves
   the number rather than the reasoning.
2. **Ungated by default, or gated by default?** **Resolved: ungated by default in `solve`,
   gated available on `build`** (2026-09-03). The core is needed on `INFEASIBLE` alone, which
   is already the slow and rare path, and paying for it twice there is cheaper than paying for
   it on every feasible solve. `build` keeps `gated=True` as its default so that every existing
   caller, including the studies, is unaffected by the parameter's arrival.
3. **Is a rebuild acceptable on the infeasible path?** **Resolved: the question never
   arrived** (2026-09-03). The ungated build is not shipped, so there is no rebuild. `solve`
   raises on an ungated infeasibility instead, because an empty core says "no rules conflict"
   about a week where they do.
4. **Does this bound [`D-127`](../decisions.md#d-127) or supersede it?** **Resolved: bounds it**
   (2026-09-03). The envelope is unchanged at about 40 employees over four weeks; what changes
   is the explanation attached to it, and [`D-153`](../decisions.md#d-153) carries that.
5. **Does the reporting promise survive?** **Resolved: yes, untouched** (2026-09-03). `solve`
   and `violations()` are unchanged and every returned roster is still verified by `checker.py`,
   which never read a gate.
6. **What is done about [`D-154`](../decisions.md#d-154)?** **Resolved: recorded, not fixed**
   (2026-09-03). A criterion that cannot tie needs weights no two subsets can share, and a
   superincreasing sequence overflows int64 long before 60,000 variables. That is a design
   question and does not belong inside the component that tripped over it.

---

*The ledger: [`README.md`](README.md). The reasoning behind the shape of this file:
[`documentation.md`](documentation.md#specs-for-the-built-components).*
