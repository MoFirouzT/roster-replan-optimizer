# Do D0–D4 produce different rosters?

**Question.** [`replan.md`](../internals/model.md) defines five metrics, ships D2, and asserts that the
fact they produce different rosters is the deliverable rather than a problem to settle. This study
tests that, and tests the constraint [`D-060`](../decisions.md#d-060) puts on it: that they can only diverge where there is
slack.

**Answer.** Yes, on 10 of the 84 committed cases, and where they diverge, they diverge severely:
each metric scores the other's answer at roughly double its own optimum. But the divergence is
**entirely between D0/D1/D2 on one side and D3/D4 on the other**. Within each side, nothing separates
them on this instance set. [`D-060`](../decisions.md#d-060) survives as a mechanism and fails as a test, because the quantity
it was going to be tested against turns out to be the wrong one.

> **Re-measured after [`D-119`](../decisions.md#d-119), and the rate moved a long way: 26 of 84 became 10 of 84** ([`D-120`](../decisions.md#d-120)).
> Nothing about the method changed and nothing about it could: `metrics.py` builds its own models
> and never calls `model.solve`, so canonicalising the optimum cannot reach it. **The instances
> changed.** A canonical incumbent is a different published roster, so the event lands on a different
> person and every replan in the set is a new one. The divergence rate is a property of the instances,
> and it turns out to be a far less robust number than the structure underneath it, which held: the
> same split between D0/D1/D2 and D3/D4, the same ~100% symmetric regret, and a worked example that
> reproduces to the point on a different seed of the same class.

    uv run python -m benchmarks.metrics --write

## Comparing rosters is the wrong measurement

The obvious method (solve under each metric, ask whether the rosters differ) reports 49 of 84 and
is worthless. A metric usually has **many** optimal rosters, and which one comes back is the solver's
search order, so two rosters differing says nothing about whether the two metrics wanted different
things. D0 in particular has an enormous tie set: it would "disagree" with everything, including with
itself at a different seed.

That is the same failure the cost baseline in [`benchmarks.md`](../benchmarks.md) exhibits, and it is
worth naming twice: **an indifferent objective produces arbitrary output that looks like a finding.**

## What is measured instead: regret, by lexicographic solve

For an ordered pair `(a, b)`, the question worth asking is what committing to `a` costs in `b`, *at
best*:

1. Solve under `a`. Call its optimal objective `V_a`.
2. Solve again minimising `b`, subject to `a`'s objective equalling `V_a`: the best `b`-roster among
   **all** of `a`'s optima, which is the most charitable reading of `a` available.
3. `regret(a → b)` is that roster's `b` score, minus `b`'s own optimum.

`regret(a → b) > 0` is a genuine conflict: no roster optimal under `a` is optimal under `b`, so the
choice between them changes who works, whatever the solver's tie-breaking does. Ties can neither
manufacture a finding nor hide one. Scoring is by `scoring.py`, the independent reading, on the
returned roster: never by reading an objective value back out of the solver.

## The regret matrix

84 cases, seed 7. Each cell: cases where committing to the row metric costs something in the column
metric, and the mean regret over those cases.

| commit to ↓ · pay in → | D0 | D1 | D2 | D3 | D4 |
| --- | --- | --- | --- | --- | --- |
| **D0** | n/a | 0/84 | 0/84 | 10/84 · 420.0 | 10/84 · 419.8 |
| **D1** | 0/84 | n/a | 0/84 | 10/84 · 420.0 | 10/84 · 419.8 |
| **D2** | 0/84 | 0/84 | n/a | 10/84 · 420.0 | 10/84 · 419.8 |
| **D3** | 10/84 · 2.2 | 10/84 · 22.0 | 10/84 · 34.0 | n/a | 0/84 |
| **D4** | 10/84 · 2.2 | 10/84 · 22.0 | 10/84 · 34.0 | 0/84 | n/a |

**The raw asymmetry is a units artifact, not a finding.** D3 multiplies by change-type weights of
6–14, so its scores live on a larger scale. Normalised against the paying metric's own optimum, the
median regret is **100% in both directions**: each metric scores the other's answer at about twice
its own optimum. They disagree symmetrically and badly.

### D0, D1 and D2 never conflict on this set

Zero in all six ordered pairs. Publication weighting and notice weighting change *nothing* about
which roster is optimal here, and the reason is structural rather than lucky: the whole week is
published ([`D-051`](../decisions.md#d-051)), and a disruption damages a **specific slot**, so every candidate repair changes
that same slot. `P × N` is then a constant factor multiplying every option equally, and a constant
factor cannot reorder anything.

D1 and D2 earn their weights when a repair can choose *which* slot to disturb: trading a change
tonight against a change next week. That choice does not arise when the hole is given, which is the
shape of every scenario in this set. It is not evidence that the weights are wrong; it is evidence
that this distribution does not pose the question they answer.

### D3 and D4 never conflict either

Also zero, in both directions, on all 84. The convex concentration penalty never bites, because it
takes two events landing on **one person** to make `f` non-linear (`f(1)=1, f(2)=3`), and median damage
here is one assignment. Even `multi-absence`, which takes out three people, gives each of them one
event.

**This is a real null and it is worth stating plainly: D4 is unexercised by the committed set.**
Anything claiming D4 behaves well is claiming it from the micro-instances, not from here.

## The one real divergence, worked

`early-notice/0`, the first conflicting case, reproduces `replan.md`'s Ana/Bram example exactly,
which is worth something, since that example was invented at spec time to argue the metrics *could*
differ, and here it arises on its own from a seeded generator.

This derivation was originally written against `early-notice/1`, whose divergence [`D-119`](../decisions.md#d-119) removed
along with the rest of the old instances. **Seed 0 reproduces every number in the table below
exactly**: the same two-against-four slots, the same 20/240 and 40/120. That is the more useful
fact than either seed: the divergence is a property of the *class*, not of the one instance the study
happened to inspect first.

Employee 6 is published on day 3, shift 0, and becomes unavailable.

| | D2's answer | D3's answer |
| --- | --- | --- |
| what happens | employee 6 drops; **employee 5 is called in** | employee 6 **moves** to shift 2; employee 3 moves from shift 2 to shift 0 |
| changed slots | 2 | 4 |
| D2 score | **20** | 40 |
| D3 score | 240 | **120** |

The arithmetic is checkable by hand. Notice here is more than 24 hours, so `N = 1`, and everything is
published, so `P = 10`. D3 prices its own answer as two moves: `10 × 6 × 2 = 120`. It prices D2's
answer as one cancellation plus one call-in: `10 × 10 + 10 × 14 = 240`. D2 prices by changed slots:
2 against 4, so `20` against `40`. **Each thinks the other is exactly twice as bad**, and both are
right about their own definition.

This is the whole claim of the five-metric design in one case. D2 minimises how many people are
touched. D3 minimises how much anyone's life changes, and will touch twice as many people to avoid
calling one person in on a day off. Neither is the correct answer to a question the data can settle.

## [`D-060`](../decisions.md#d-060): right mechanism, wrong instrument

[`D-060`](../decisions.md#d-060) says divergence requires slack: a tightly covered week has one legal repair, so every metric
returns it. The class breakdown supports the mechanism cleanly at one end:

| class | D2/D3 conflict |
| --- | --- |
| `scarce-skill`, `thin-availability` | 2/6 |
| `headline`, `tight`, `busy`, `flexi-heavy`, `withdrawal`, `early-notice` | 1/6 |
| `loose`, `overloaded`, `small`, `large`, `multi-absence`, `demand-spike` | **0/6** |

`demand-spike` never diverges for a structural reason that survived the re-measurement: an added
headcount is a pure call-in with nothing to pair it against, so D3 has no move available and agrees
with D2 by default.

**`tight` now diverges once, and that is the clean `0/6` the previous run reported gone** ([`D-120`](../decisions.md#d-120)).
It is not a refutation of [`D-060`](../decisions.md#d-060) so much as a demotion of this table: a class name is a *target*
demand ratio, and what decides divergence is the room at the slot the event actually damaged. The
repair-slack table below says that far more sharply than this one now does.

### The coverage axis, now that it has five points ([`D-106`](../decisions.md#d-106))

Until [`D-105`](../decisions.md#d-105) widened the set this class breakdown held **one** class at the tight end, and a single
zero cannot distinguish *tightness* from something peculiar to that class. There are now five points
on the axis, and they make a shape:

| demand ratio | class | conflict |
| --- | --- | --- |
| 0.35 | `loose` | **0/6** |
| 0.70 | `headline` | 1/6 |
| 0.80 | `busy` | 1/6 |
| 0.90 | `tight` | 1/6 |
| 0.95 | `overloaded` | **0/6** |

Two things follow, and neither is what the first run of this table reported ([`D-120`](../decisions.md#d-120)).

**The curve is gone.** Divergence used to rise to 4/6 at 0.70 and fall to zero by 0.90; it is now
flat at one case across the middle three and zero at both ends. Whatever shape the coverage axis has,
this set at this rate cannot resolve it: six cases per point and ten conflicts in total is not
enough to draw a curve through, and the previous run drew one anyway.

**Both ends still suppress divergence, and for the two different reasons already given.** `overloaded`
at 0.95 has one legal repair, which is [`D-060`](../decisions.md#d-060)'s mechanism. `loose` at 0.35 has the opposite problem
and it is [`D-071`](../decisions.md#d-071)'s: low demand is expressed by opening **fewer shift instances**, not by thinning a
full grid, so a loose week has fewer shifts on the damaged day for D3 to move somebody into.
Divergence needs slack *and* somewhere to put people, and the loose end runs out of the second while
gaining the first.

That is the same missing condition the rest of this study names: whether a **move** is available on
the damaged day: arriving from the other direction. It is a property of the day, the set does not
vary it, and both ends of the coverage axis suppress it for different reasons.

But the **week-level minimum slot slack recorded in the instance set does not predict divergence**:

| week minimum slot slack | −2 | −1 | 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| conflict | 2/3 | 1/6 | 3/12 | 0/19 | 3/29 | 1/11 | 0/4 |

Non-monotone, and the most-constrained bucket has the highest rate. The instrument is at fault rather
than the claim: `min_slot_slack` is a minimum over 21 slots, and a week can hold one impossible slot
and abundant room everywhere else. The repair happens where the damage is. Measured **at the damaged
slot** (`metrics.repair_slack`), the picture improves but does not become a law:

| slack at the repair | −2 | −1 | 0 | 1 | 2 | 3 | 4 | 5 | 6+ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| conflict | 0/1 | 0/2 | 0/1 | 0/9 | 0/10 | 0/7 | 0/10 | 0/4 | **10/40** |

**This is the sharpest the study has ever been, and it got sharper by accident** ([`D-120`](../decisions.md#d-120)). Every one
of the ten divergences sits in the top bucket and every other bucket is a clean zero: where the
previous instance set scattered conflicts across six of eight buckets. Read as a necessary condition
it is now exact on this set: **no case with fewer than six spare eligible people at the damaged slot
diverges at all.** Read as a sufficient one it is still nowhere close, at 10 of 40.

**Conclusion: slack is necessary and nowhere near sufficient.** The missing condition is structural,
and the worked example above names it: D3 diverges from D2 only when a **move** is available, meaning
another open shift on the same day that a rostered person could be shifted to. That is a property of
the damaged *day*, not of the week and not of the slot, and the committed set does not vary it, so
this study can report the correlation and not a clean law. A generator axis over same-day shift
availability is the honest way to close it, and it is named in [`D-085`](../decisions.md#d-085) rather than bolted on here.

## What this changes

Nothing about the shipped default. D2 remains the shipped metric under [`D-006`](../decisions.md#d-006), and this study
strengthens rather than weakens that: D2 is indistinguishable from D0 and D1 on this distribution, so
the simplest of the three that prices what planners react to is the right one to carry.

What it does change is the **status of D3**. `replan.md` describes the `W_callin > W_cancel > W_move`
ordering as the most falsifiable claim in the file, and this study shows that the ordering is not
academic: on a third of the cases it selects a materially different roster, at roughly double the D2
cost. Whether real planners make that trade is exactly what capture-and-replay is for, and this
result raises the value of that corpus rather than settling anything without it.
