# Benchmarks

*Assumes: the objective every method is scored on, [`model.md`](internals/model.md); the rules an instance must satisfy, [`rules.md`](guide/rules.md).*

## The scaling axis

Slowness has three possible causes here:
(i) a single instance too big to solve, (ii) too many instances to get through, (iii) one instance too slow to feel interactive.
**This benchmark is about (ii) and (iii)** throughput across many small tenants, and the latency any one of them feels while waiting on a solve, not a single large roster that needs to be broken into pieces.
Asking how to decompose a large instance answers a question this system does not ask.

## Instance distribution

An undefined distribution makes a p95 unfalsifiable.
Generator parameters, all seeded and committed, one per axis:

| Parameter | Range | Axis |
| --- | --- | --- |
| `employees` | 8–25 | tenant size |
| `demand_ratio` | required shift-hours as a share of total weekly budget | coverage tightness |
| `scarce_skill_share` | share of employees holding the scarce skill | skill scarcity |
| `flexi_share` | share on a flexi contract | contract mix |
| `availability_density` | share of (employee, day) pairs with nothing declared | availability |
| `event` | sick call · multiple absences · demand spike · availability withdrawal | disruption type |
| `event_day`, `event_hour` | day index and clock hour | event timing: **Saturday 09:00 is the headline class** |

**This table hides two decisions: what `demand_ratio` actually means, and why there's no student share.**

`demand_ratio` is a *target*:
what gets reported is what the instance turned out to be, not what was asked for ([`D-070`](decisions.md#d-070)).
Availability and skill scarcity narrow what the solver can actually staff, so realised tightness is measured over the pairs that survive the model's own presolve and reported
as four numbers;
measured demand ratio, minimum slot slack, count of slots with zero slack, and
count of slots no roster can staff.
[`D-060`](decisions.md#d-060) makes tightness the knob that decides whether the D0–D4 study can see anything at all, so reporting the nominal figure instead would quietly settle the study's answer.

**There is no student share** ([`D-072`](decisions.md#d-072)).
`R-STUDENT-QUOTA` is profile-gated and not yet encoded, so a student parameter would move no constraint;
a knob attached to nothing would make this table look richer than the distribution actually is.

Low demand is expressed by opening fewer shift instances, not by thinning a full grid ([`D-071`](decisions.md#d-071)).
Instance size varies with tightness, so solve-time comparisons across tightness must report both.

## A case is a scenario, not an instance

A replan is a function of a published roster and something that went wrong with it.
The generator matches that:
it runs in two phases ([`D-068`](decisions.md#d-068)); build a week, solve it cold, publish the result as the incumbent, then inject the event.
The whole horizon is published, which is both the realistic replan case and the hardest one, since every change is priced at `published_weight` ([`D-051`](decisions.md#d-051)).

**The incumbent is solved by the system under test** ([`D-069`](decisions.md#d-069));
the benchmark's weak point, stated rather than buried.
These numbers can show a replan beats a re-solve *given* a roster this model would produce;
they cannot show the model matches what real planners publish. Only a captured corpus of rosters real planners published can carry that second claim, which is why capture and replay is scheduled rather than optional ([the ledger](specs/README.md) records what it fixed in advance and what blocks it).

**Partly answered from outside** ([`D-125`](decisions.md#d-125), [`studies/foreign-incumbent.md`](studies/foreign-incumbent.md)).
Published solutions from the nurse-rostering benchmark set are rosters other people's solvers produced, optimising an objective this project does not implement.
Used as incumbents, they reproduce the headline claim by **4.6× to 37×**, against about 5× on this set.
That is not the captured corpus, nurse rosters from published research, not Belgian horeca rosters from a vendor, but it is the sharpest form of the objection that the incumbent is *always* this project's own output, and it no longer holds.

## The committed set

Fourteen scenario classes, six seeds each: 84 cases, listed in `benchmarks/manifest.json`. Twelve
of those classes are the original set; `busy` and `overloaded` were added later, for the reason
recorded in [`D-105`](decisions.md#d-105) and described under *Sampling the coverage axis* below.

    uv run python -m benchmarks.suite --write

**The set is its seeds.** Generation is deterministic, so a class name and a seed name an instance
exactly: what is committed is a manifest of fingerprints, not 84 payloads ([`D-073`](decisions.md#d-073)). Each case
carries two: `week` over the generated payload, and `incumbent` over the solved base roster. A
`week` hash that holds while the incumbent moves means a solver change, and the instances stay
comparable across it; both moving means a generator change, and they do not ([`D-074`](decisions.md#d-074)).

Every class varies **one** axis from `headline`: the Saturday 09:00 sick call on a mid-sized
tenant with slack, so a difference in results has one candidate explanation, not several. Classes
that differ only in the disruption event generate the *same published week* at a given seed, which
makes the event axis a controlled comparison rather than a comparison of instances ([`D-076`](decisions.md#d-076)).

| Class | Varies |
| --- | --- |
| `headline` |: the Saturday 09:00 sick call |
| `loose`, `busy`, `tight`, `overloaded` | coverage tightness, at 0.35, 0.80, 0.90 and 0.95 ([`D-105`](decisions.md#d-105)) |
| `small`, `large` | 8 and 25 employees |
| `scarce-skill` | scarce skill held by a quarter of staff |
| `flexi-heavy` | 60% flexi contracts |
| `thin-availability` | availability density 0.60 |
| `multi-absence`, `demand-spike`, `withdrawal` | the other three event types |
| `early-notice` | the same disruption with days of notice instead of hours |

**Nothing is filtered** ([`D-075`](decisions.md#d-075)). Twelve of the 84 cases start from a week that cannot be fully
staffed, and `scarce-skill` is chronically short by design; they stay in, with `base_shortfall`,
`short_slots` and `damage` recorded per case. Filtering at generation would prune the distribution
down to the cases that flatter the thesis, and do it where nobody can see. Which cases to exclude
is instead an analysis decision, made here:

- **Results are segmented by `base_shortfall`, never pooled across it.** A week that was already
  short poses a capacity question; a week that was fully staffed poses a repair question. Averaging
  them answers neither.
- **`demand-spike` on a tight week degenerates**, and is reported separately. When the extra
  headcount cannot be staffed by anyone, the optimal replan changes nothing and absorbs the
  shortfall: correct behaviour, and no evidence about repair quality.

## Methods compared

| Method | Isolates |
| --- | --- |
| Cold re-solve, cost objective | the status quo |
| Greedy nearest-eligible repair | the human default: "just call someone" |
| Cold solve, disruption objective | the objective effect, separated from warm starting |
| Warm-started replan | the thesis |

Both axes for all four: solve time (p50/p95), disruption score (D2), cost delta. A method that is
fast and disruptive has not won.

**Every method is scored on the same yardstick**: the scenario's shipped D2 profile, whatever it
optimised ([`D-079`](decisions.md#d-079)). Scoring each under its own objective would make the table a tautology: the
cost solve would report zero disruption, because its profile prices none. The shared scale also
buys one checkable invariant: no method may score below the disruption solve on `Score.total`,
since that solve is optimal.

**Two clocks, not one** ([`D-081`](decisions.md#d-081)). At these sizes a search takes about 3 ms and building the model
in Python takes about 5 ms, so an end-to-end stopwatch mostly measures model construction, which is
identical for all four methods. The first version of this harness reported exactly that, and made
the four methods look equally fast for a reason that had nothing to do with any of them. End-to-end
is the latency a caller sees; search time is the only number that compares one search against
another.

**The cost baseline keeps the incumbent attached** ([`D-080`](decisions.md#d-080)). It solves the same instance with the
same pinned past, under a profile whose change weights are all zero. Solving with no incumbent at
all would unpin the past: a baseline free to reassign shifts that have already started is not a
baseline for anything.

**The cost column reports paid hours, not euros**, which is how `replan.md` says to read it until
wage data lands. `cost_weight` ships at 0 and the cost model is a flat rate ([`D-050`](decisions.md#d-050)), so
`Score.cost` is identically zero, and a column of it would report the weight rather than the cost.
Paid hours are computed directly instead, and turn out to be nearly constant: a hard coverage
ceiling fixes the number of assignments, so every fully staffed roster costs the same. That is what
makes the cold baseline indifferent ([`D-080`](decisions.md#d-080)), and what collapses the cost axis of the frontier.
The disruption axis stays sound regardless: a cold solve has no reason to resemble the incumbent,
which is the entire point.

## Results

    uv run python -m benchmarks.run --write

84 cases × 4 methods × 3 solver seeds × 3 time budgets: 2,520 runs, segmented on `base_shortfall`
and never pooled across it, per the rule above. Times are milliseconds; disruption is the D2 score;
`changes` is the raw count of assignments differing from the incumbent; `short` is unstaffed
positions. **The tables report the 5 s budget**; the quality columns are identical at 1 s and 30 s:
the time-budget null, restated on the wider set.

**Weeks that could be fully staffed before the event**: 72 cases, the repair question:

| Method | p50 end-to-end | p95 end-to-end | p50 search | p95 search | Disruption | Changes | Short | Paid hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 10.5 | 22.8 | 3.61 | 10.52 | 307.3 | 12.36 | 0.15 | 284.5 |
| Greedy nearest-eligible repair | 1.2 | 2.8 | n/a | n/a | 53.6 | 1.94 | 0.31 | 283.3 |
| Cold solve, disruption objective | 10.4 | 22.6 | 3.58 | 10.74 | 65.3 | 2.40 | 0.15 | 284.5 |
| **Warm-started replan** | 10.6 | 21.9 | **3.31** | **8.61** | 65.3 | 2.40 | 0.15 | 284.5 |

**Weeks already short before the event**: 12 cases, the capacity question:

| Method | p50 end-to-end | p95 end-to-end | p50 search | p95 search | Disruption | Changes | Short | Paid hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 9.8 | 11.0 | 3.49 | 4.17 | 266.1 | 9.36 | 1.42 | 259.4 |
| Greedy nearest-eligible repair | 2.7 | 4.7 | n/a | n/a | 55.0 | 1.75 | 1.58 | 258.1 |
| Cold solve, disruption objective | 9.9 | 10.9 | 3.41 | 4.29 | 65.0 | 2.25 | 1.42 | 259.4 |
| **Warm-started replan** | 9.6 | 11.2 | **3.19** | **3.66** | 65.0 | 2.25 | 1.42 | 259.4 |

### What the numbers say

**The objective is what does the work.** Against the cost baseline, the disruption profile cuts
mean disruption from 307 to 65 and mean changed assignments from 12.4 to 2.4, on identical
instances with identical coverage. A cold cost re-solve reshuffles a third of a published week to
absorb one sick call, because nothing in its objective prefers the roster people have already been
told about.

**The warm start helps, modestly, and only on the search clock** ([`D-082`](decisions.md#d-082)). Paired on case, solver
seed and budget (84 cases × 3 seeds × 3 budgets, 756 pairs) the hint reduces search time on 662 of
them, median paired ratio 0.906. That reproduces [`D-082`](decisions.md#d-082)'s figure of 0.907 (72 cases × 3 seeds at
one budget, 216 pairs), the extra budgets adding replicas rather than new evidence, since search
time does not depend on the budget once every solve finishes well inside it. It never changes the
answer, which is the property the tests assert. `replan.md` asked for this to be filed either way:
it is not a null, but it is a rounding error beside the objective effect, and calling the system
"warm-started" oversells the part of it that is warm.

**The cost baseline is indifferent, and its disruption number carries the proof.** Across three
solver seeds on the same case, its disruption moves by a median of 100 points and by up to 260, on
52 of the 84 cases. The disruption methods move by **zero**, on every case, at every seed. [`D-080`](decisions.md#d-080)
predicted exactly this from the structure: flat cost, hard coverage ceiling, so every fully
staffed roster costs the same and CP-SAT returns whichever it reaches first, which is why a single
seed's number would have been an accident reported as a result. It is also a result the service depends on:
the shipped objective is reproducible across seeds without being asked to be.

**Greedy ties the optimum on 71 of 84 cases** ([`D-083`](decisions.md#d-083), [`D-105`](decisions.md#d-105)). Wherever it matched the optimal
coverage, it matched the optimal disruption exactly, every time. Its lower *average* disruption is
not a win: it gets there by leaving more shifts unstaffed (0.31 against 0.15 on clean weeks),
which is precisely the trade the shortfall weight is set to refuse. On the 13 cases where it left
an extra hole: `tight/2`, `tight/4`, `small/5`, `large/2`, `flexi-heavy/5`, `thin-availability/2`,
`thin-availability/3`, `multi-absence/2`, `busy/2`, `busy/5`, `overloaded/1`, `overloaded/4`,
`overloaded/5`: the repair needed a chain: move an uninvolved person so somebody else becomes
free. No planner reading a printed roster finds that, and greedy by construction does not look for
it.

The first eight are the original set's, reproduced case for case; the last five are from the two
classes [`D-105`](decisions.md#d-105) added. That split is the point: **the tie rate is a property of where the set
samples.**

So the honest claim at this scale is not that the optimiser beats the planner on the common case:
it is that the optimiser never leaves a shift uncovered that could have been covered, and is right
on the case the planner cannot see. **Median damage across the set is 1 assignment, and the maximum
is 3**, an axis this distribution does not vary; [`D-083`](decisions.md#d-083) records why it was not widened after the
fact.

### Sampling the coverage axis

The original twelve classes put 60 of 72 cases at a demand ratio of ~0.70 and left nothing between
0.73 and 0.89: what varying one axis at a time from a slack baseline produces. That is right for
attribution, since a difference then has one candidate explanation, but it samples the ends of the
coverage axis and not the middle, which is where the methods separate:

| Class | Demand ratio | Greedy ties | Greedy short | Optimal short |
| --- | --- | --- | --- | --- |
| `loose` | 0.35 | 6/6 | 0.00 | 0.00 |
| `headline` | 0.70 | 6/6 | 0.17 | 0.17 |
| `busy` | 0.80 | 4/6 | 0.33 | **0.00** |
| `tight` | 0.90 | 4/6 | 1.00 | 0.67 |
| `overloaded` | 0.95 | 3/6 | 1.17 | 0.67 |

`busy` is the cleanest row: full coverage was available, and the optimiser found it on every seed,
while greedy missed it on two. Read down the tie column and the headline claim reads differently:
greedy is indistinguishable from the optimum on a slack week, and loses one case in two on a
stretched one.

**Conjunction was tried first and rejected** ([`D-105`](decisions.md#d-105)). Piling demand, skill scarcity and thin
availability together produces weeks that are *structurally* short, and there greedy ties 6 of 6 at
every setting tried: both methods leave the same unfillable holes. Hardening the benchmark that
way makes it blind rather than sharper. It does not make the search harder either: across the
generator's whole range, up to 105% demand and 40 employees, every solve returns `OPTIMAL` in 3 to
11 ms, and the structurally short cases are *faster* than the baseline.

## The frontier

Disruption vs. coverage, per scenario class. Cost is not the second axis it was expected to be:
paid hours are constant within a class ([`D-080`](decisions.md#d-080), above), so that axis of the frontier degenerates.
**Coverage is the axis the trade-off actually runs along**, and it is a real trade: greedy buys a
lower disruption score by leaving shifts short.

Mean disruption per class at the 5 s budget, with unstaffed positions in the last column as
greedy/optimal:

| Class | Cold cost | Greedy | Cold disruption | Warm replan | Short g/o |
| --- | --- | --- | --- | --- | --- |
| `headline` | 292 | 63 | 63 | 63 | 0.17 / 0.17 |
| `loose` | 243 | 70 | 70 | 70 | 0.00 / 0.00 |
| `busy` | 232 | 32 | 57 | 57 | 0.33 / 0.00 |
| `tight` | 229 | 28 | 58 | 58 | 1.00 / 0.67 |
| `overloaded` | 223 | 48 | 73 | 73 | 1.17 / 0.67 |
| `small` | 219 | 53 | 73 | 73 | 0.17 / 0.00 |
| `large` | 618 | 63 | 73 | 73 | 0.17 / 0.00 |
| `scarce-skill` | 279 | 65 | 65 | 65 | 1.67 / 1.67 |
| `flexi-heavy` | 232 | 33 | 43 | 43 | 0.67 / 0.50 |
| `thin-availability` | 200 | 32 | 57 | 57 | 0.50 / 0.17 |
| `multi-absence` | 324 | 152 | 167 | 167 | 0.83 / 0.67 |
| `demand-spike` | 318 | 30 | 30 | 30 | 0.00 / 0.00 |
| `withdrawal` | 292 | 63 | 63 | 63 | 0.17 / 0.17 |
| `early-notice` | 517 | 20 | 20 | 20 | 0.00 / 0.00 |

Read the greedy and warm columns together with the last one. Wherever greedy shows a *lower*
disruption than the optimal solve: `tight`, `small`, `large`, `flexi-heavy`, `thin-availability`,
`multi-absence`: it is also short more often, and the difference is exactly the shifts it failed
to fill. Where coverage matches, the two agree to the point.

`early-notice` is the cleanest read on the notice multiplier: given days of notice instead of
hours, the same disruption scores 20 against `headline`'s 63, while the cost baseline goes *up* to
517, because a cold solve reshuffles the whole week regardless of when it was told.

## Quality vs. time budget

**The curve is flat, and the reason is that the question does not arise at this size.** Every
solver run over the whole set (2,268 of them, across the 1 s, 5 s and 30 s budgets) returned
`OPTIMAL`, and the longest search anywhere was **15.4 ms**. No answer changed with the budget on
any of the 756 (case, method, seed) triples, so the three budgets are indistinguishable case by
case ([`D-107`](decisions.md#d-107)): nothing was ever cut off, so there is no anytime behaviour to plot and no quality
to trade for time.

That is a result about the instance distribution, not the solver: stated rather than shown as
three identical bars. A one-week horizon over 8–25 employees and 21 shift instances is small for
CP-SAT. The fallback ladder (exact, then time-boxed with a reported gap, then greedy) is
designed for a regime this set does not reach, and honestly, its time-boxed rung is currently
unexercised by any committed benchmark. What the numbers here do support is the opposite
scheduling concern: at 3 ms of search against 5 ms of model construction, the thing worth caching
is the compiled model, which is what T3 tried and [`D-149`](decisions.md#d-149) then removed: it hit nothing, and its key went stale.

## Reproduction

    uv run python -m benchmarks.suite --write     # regenerate the instance manifest
    uv run python -m benchmarks.run --write       # regenerate results.json

Deterministic given the code: generation is seeded per case ([`D-073`](decisions.md#d-073)), and every solve carries an
explicit solver seed. The numbers above are from `benchmarks/results.json` at
`generator_version: 1`, solver seeds `7, 11, 13`, budgets 1 s / 5 s / 30 s.

**One worker per solve.** `model.solve` defaults to `workers=1` and the benchmark does not change
it, so these figures are single-threaded, with a 1:1 thread-to-core ratio by construction. That is
the right default for a throughput problem across many small tenants: the scaling axis stated at
the top of this file: where cores are better spent on concurrent tenants than on parallel search
within one. A multi-worker sweep would be a separate study, and is not one of these numbers.

Hardware: Apple Silicon (arm64), macOS 27.0, Python 3.12.13, `ortools` 9.15.6755. Wall-clock
figures in milliseconds will move with the machine; the paired comparisons: warm against cold,
seed against seed: are ratios on one machine, and are the ones meant to travel.
