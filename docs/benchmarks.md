# Benchmarks

> **Status: the four-method comparison is measured and reported.** The distribution, the committed
> set and the results below are reconciled with `benchmarks/generator.py`, `benchmarks/suite.py`,
> `benchmarks/methods.py` and `benchmarks/run.py`, and every `[B-n]` placeholder in the README now
> resolves from here. The D0–D4 study is in
> [`studies/disruption-metrics.md`](studies/disruption-metrics.md). Still outstanding for T2: the
> level-1 model studies, and capture-and-replay.

## The scaling axis

Three possible problems: (i) one instance too big, (ii) too many instances, (iii) too slow
interactively. **This is (ii) and (iii).** Benchmarks measure throughput and interactive latency
across many small tenants, not one large monolith. Answering the decomposition question when the
real problem is throughput is reciting, not diagnosing.

## Instance distribution

An undefined distribution makes a p95 unfalsifiable. Generator parameters, all seeded and
committed, one per axis:

| Parameter | Range | Axis |
| --- | --- | --- |
| `employees` | 8–25 | tenant size |
| `demand_ratio` | required shift-hours as a share of total weekly budget | coverage tightness |
| `scarce_skill_share` | share of employees holding the scarce skill | skill scarcity |
| `flexi_share` | share on a flexi contract | contract mix |
| `availability_density` | share of (employee, day) pairs with nothing declared | availability |
| `event` | sick call · multiple absences · demand spike · availability withdrawal | disruption type |
| `event_day`, `event_hour` | day index and clock hour | event timing — **Saturday 09:00 is the headline class** |

**Two things about this list are decisions, not mechanics.**

`demand_ratio` is a *target*, and what gets reported is what the instance turned out to be
(`D-070`). Realised tightness is measured after availability and skill scarcity have had their say,
over the pairs surviving the model's own presolve, and it is reported as four numbers: measured
demand ratio, minimum slot slack, count of slots with zero slack, and count of slots no roster can
staff. `D-060` makes tightness the knob that decides whether the D0–D4 study can see anything at
all, so a nominal figure would quietly settle the study's answer.

**There is no student share** (`D-072`). `R-STUDENT-QUOTA` is profile-gated and not yet encoded, so
a student parameter would move no constraint — and a knob attached to nothing makes this table look
richer than the distribution actually is.

Low demand is expressed by opening fewer shift instances rather than by thinning a full grid
(`D-071`), so instance size varies with tightness and solve-time comparisons across tightness have
to report both.

## A case is a scenario, not an instance

A replan is a function of a published roster and something that went wrong with it, so the generator
runs in two phases (`D-068`): build a week, solve it cold and publish the result as the incumbent,
then inject the event. The whole horizon is published, which is both the realistic replan case and
the hardest one — every change is priced at `published_weight` (`D-051`).

**The incumbent is solved by the system under test** (`D-069`). That is the weak point of this
benchmark and it is stated rather than buried: these numbers can show that a replan beats a re-solve
*given* a roster this model would produce, not that the model matches what real planners publish.
Only the captured corpus in [`specs/capture.md`](specs/capture.md) can carry that second claim, which
is why it is scheduled rather than optional.

**Partly answered from outside** (`D-125`, [`studies/foreign-incumbent.md`](studies/foreign-incumbent.md)).
Published solutions from the nurse-rostering benchmark set are rosters produced by other people's
solvers optimising an objective this project does not implement, and used as incumbents they
reproduce the headline claim by **4.6× to 37×** where this set shows about 5×. That is not the captured
corpus — they are nurse rosters from published research rather than Belgian horeca rosters from a
vendor — but the sharpest form of the objection, that the incumbent is *always* this project's own
output, no longer holds.

## The committed set

Fourteen scenario classes, six seeds each — 84 cases, listed in `benchmarks/manifest.json`.
Twelve of those classes are the original set; `busy` and `overloaded` were added after it, for a
measured reason recorded in `D-105` and described under *Sampling the coverage axis* below.

    uv run python -m benchmarks.suite --write

**The set is its seeds.** Generation is deterministic, so a class name and a seed name an instance
exactly, and what is committed is a manifest of fingerprints rather than 84 payloads (`D-073`). Each
case carries two: `week` over the generated payload, and `incumbent` over the solved base roster. A
`week` hash that holds while incumbents move is a solver change and the instances stay comparable
across it; both moving is a generator change and they do not (`D-074`).

Every class varies **one** axis from `headline` — the Saturday 09:00 sick call on a mid-sized tenant
with slack — so a difference in results has one candidate explanation rather than several. Classes
that differ only in the disruption event generate the *same published week* at a given seed, which
is what makes the event axis a controlled comparison rather than a comparison of instances
(`D-076`).

| Class | Varies |
| --- | --- |
| `headline` | — the Saturday 09:00 sick call |
| `loose`, `busy`, `tight`, `overloaded` | coverage tightness, at 0.35, 0.80, 0.90 and 0.95 (`D-105`) |
| `small`, `large` | 8 and 25 employees |
| `scarce-skill` | scarce skill held by a quarter of staff |
| `flexi-heavy` | 60% flexi contracts |
| `thin-availability` | availability density 0.60 |
| `multi-absence`, `demand-spike`, `withdrawal` | the other three event types |
| `early-notice` | the same disruption with days of notice instead of hours |

**Nothing is filtered** (`D-075`). Twelve of the 84 cases start from a week that cannot be fully
staffed, and `scarce-skill` is chronically short by design. They stay in with `base_shortfall`,
`short_slots` and `damage` recorded per case, because filtering at generation prunes the
distribution to the cases that flatter the thesis and does it where nobody can see. Which cases to
exclude is an analysis decision and it is made here:

- **Results are segmented by `base_shortfall`, never pooled across it.** A week that was already
  short poses a capacity question; a week that was fully staffed poses a repair question. Averaging
  them produces a number that answers neither.
- **`demand-spike` on a tight week degenerates** and is reported separately. When the extra headcount
  cannot be staffed by anyone, the optimal replan changes nothing and absorbs the shortfall — correct
  behaviour, and no evidence about repair quality.

## Methods compared

| Method | Isolates |
|---|---|
| Cold re-solve, cost objective | the status quo |
| Greedy nearest-eligible repair | the human default — "just call someone" |
| Cold solve, disruption objective | the objective effect, separated from warm starting |
| Warm-started replan | the thesis |

Both axes for all four: solve time (p50/p95), disruption score (D2), cost delta. A method that is
fast and disruptive has not won.

**Every method is scored on the same yardstick** — the scenario's shipped D2 profile — whatever it
optimised (`D-079`). Scoring each under its own objective would make the table a tautology: the cost
solve would report zero disruption because its profile prices none. The shared scale also gives the
results one checkable invariant, which is that no method may score below the disruption solve on
`Score.total`, because that solve is optimal.

**Two clocks, not one** (`D-081`). At these sizes a search takes about 3 ms and building the model in
Python takes about 5 ms, so an end-to-end stopwatch mostly measures model construction — identical
for all four methods. The first version of this harness reported exactly that and made the four
methods look equally fast for a reason that has nothing to do with any of them. End-to-end is the
latency a caller sees; search time is the only number that compares one search against another.

**The cost baseline keeps the incumbent attached** (`D-080`). It solves the same instance with the
same pinned past, under a profile whose change weights are all zero. Solving with no incumbent at all
would unpin the past, and a baseline free to reassign shifts that have already started is not a
baseline for anything.

**The cost column reports paid hours, not euros**, which is how `replan.md` says to read it until
wage data lands. `cost_weight` ships at 0 and the cost model is a flat rate (`D-050`), so `Score.cost`
is identically zero and a column of it would report the weight rather than the cost. Paid hours are
computed directly instead, and they turn out to be nearly constant — a hard coverage ceiling fixes the
number of assignments, so every fully staffed roster costs the same. That is what makes the cold
baseline indifferent (`D-080`) and what collapses the cost axis of the frontier. The disruption axis
of the comparison is sound regardless: a cold solve has no reason to resemble the incumbent, which is
the entire point.

## Results

    uv run python -m benchmarks.run --write

84 cases × 4 methods × 3 solver seeds × 3 time budgets — 2,520 runs. Segmented on `base_shortfall`
and never pooled across it, per the rule stated above. Times are milliseconds; disruption is the D2
score; `changes` is the raw count of assignments differing from the incumbent; `short` is unstaffed
positions. **The tables report the 5 s budget**; the quality columns are identical at 1 s and 30 s,
which is the time-budget null restated on the wider set.

**Weeks that were fully staffable before the event** — 72 cases, the repair question:

| Method | p50 end-to-end | p95 end-to-end | p50 search | p95 search | Disruption | Changes | Short | Paid hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 10.5 | 22.8 | 3.61 | 10.52 | 307.3 | 12.36 | 0.15 | 284.5 |
| Greedy nearest-eligible repair | 1.2 | 2.8 | — | — | 53.6 | 1.94 | 0.31 | 283.3 |
| Cold solve, disruption objective | 10.4 | 22.6 | 3.58 | 10.74 | 65.3 | 2.40 | 0.15 | 284.5 |
| **Warm-started replan** | 10.6 | 21.9 | **3.31** | **8.61** | 65.3 | 2.40 | 0.15 | 284.5 |

**Weeks already short before the event** — 12 cases, the capacity question:

| Method | p50 end-to-end | p95 end-to-end | p50 search | p95 search | Disruption | Changes | Short | Paid hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 9.8 | 11.0 | 3.49 | 4.17 | 266.1 | 9.36 | 1.42 | 259.4 |
| Greedy nearest-eligible repair | 2.7 | 4.7 | — | — | 55.0 | 1.75 | 1.58 | 258.1 |
| Cold solve, disruption objective | 9.9 | 10.9 | 3.41 | 4.29 | 65.0 | 2.25 | 1.42 | 259.4 |
| **Warm-started replan** | 9.6 | 11.2 | **3.19** | **3.66** | 65.0 | 2.25 | 1.42 | 259.4 |

### What the numbers say

**The objective is what does the work.** Against the cost baseline the disruption profile cuts mean
disruption from 307 to 65 and mean changed assignments from 12.4 to 2.4, on identical instances with
identical coverage. A cold cost re-solve reshuffles a third of a published week to absorb one sick
call, because nothing in its objective prefers the roster people have already been told about.

**The warm start helps, modestly, and only on the search clock** (`D-082`). Paired on case and solver
seed and budget, the hint reduces search time on 662 of 756 runs, median paired ratio 0.906 — about
9% of a 3 ms search, reproducing `D-082`'s figure of 0.907 on a set 17% larger. It never changes the answer, which is the property the tests assert. `replan.md` asked for
this to be filed either way: it is not a null, but it is a rounding error beside the objective
effect, and calling the system "warm-started" oversells the part of it that is warm.

**The cost baseline is indifferent, and its disruption number carries the proof.** Across three
solver seeds on the same case its disruption moves by a median of 100 points and by up to 260, on 52
of the 84 cases. The disruption methods move by **zero** on every case at every seed. That is what
`D-080` predicted from the structure — flat cost, hard coverage ceiling, so every fully staffed
roster costs the same and CP-SAT returns whichever it reaches first — and it is why a single seed's
number would have been an accident reported as a result. It is also a T3 result in advance: the
shipped objective is reproducible across seeds without being asked to be.

**Greedy ties the optimum on 71 of 84 cases** (`D-083`, `D-105`). Where it matched the optimal coverage, it
matched the optimal disruption exactly — every time. Its lower *average* disruption is not a win: it
gets there by leaving more shifts unstaffed (0.31 against 0.15 on clean weeks), which is precisely
the trade the shortfall weight is set to refuse. On the 13 cases where it left an extra hole —
`tight/2`, `tight/4`, `small/5`, `large/2`, `flexi-heavy/5`, `thin-availability/2`,
`thin-availability/3`, `multi-absence/2`, `busy/2`, `busy/5`, `overloaded/1`, `overloaded/4`,
`overloaded/5` — the repair needed a chain: move an uninvolved person so somebody else becomes free.
No planner reading a printed roster finds that, and greedy by construction does not look for it.

The first eight are the original set's, reproduced case for case; the last five are the two classes
added in `D-105`. That split is the point: **the tie rate is a property of where the set samples.**

So the honest claim at this scale is not that the optimiser beats the planner on the common case. It
is that it never leaves a shift uncovered that could have been covered, and it is right on the case
the planner cannot see. **Median damage across the set is 1 assignment and the maximum is 3**, which
is the axis this distribution does not vary; `D-083` records why it was not widened after the fact.

### Sampling the coverage axis

The original twelve classes put 60 of 72 cases at a demand ratio of ~0.70 and left nothing between
0.73 and 0.89. That is what varying one axis at a time from a slack baseline produces, and it is
right for attribution — a difference has one candidate explanation — but it samples the ends of the
coverage axis and not the middle, which is where the methods separate:

| Class | Demand ratio | Greedy ties | Greedy short | Optimal short |
| --- | --- | --- | --- | --- |
| `loose` | 0.35 | 6/6 | 0.00 | 0.00 |
| `headline` | 0.70 | 6/6 | 0.17 | 0.17 |
| `busy` | 0.80 | 4/6 | 0.33 | **0.00** |
| `tight` | 0.90 | 4/6 | 1.00 | 0.67 |
| `overloaded` | 0.95 | 3/6 | 1.17 | 0.67 |

`busy` is the cleanest row: full coverage was available and the optimiser found it on every seed,
while greedy missed it on two. Read down the tie column and the headline claim reads differently —
greedy is indistinguishable from the optimum on a slack week and loses one case in two on a
stretched one.

**Conjunction was tried first and rejected** (`D-105`). Piling demand, skill scarcity and thin
availability together produces weeks that are *structurally* short, and there greedy ties 6 of 6 at
every setting tried: both methods leave the same unfillable holes. Hardening that way makes the
benchmark blind rather than sharper. It does not make the search harder either — across the
generator's whole range, up to 105% demand and 40 employees, every solve returns `OPTIMAL` in 3 to
11 ms, and the structurally short cases are *faster* than the baseline.

## The frontier

Disruption vs. coverage, per scenario class. Cost is not the second axis it was expected to be — with
a flat rate and a hard coverage ceiling, every fully staffed roster costs the same, so paid hours are
constant within a class and the frontier degenerates on that axis. **Coverage is the axis the
trade-off actually runs along**, and it is a real trade: greedy buys a lower disruption score by
leaving shifts short.

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
disruption than the optimal solve — `tight`, `small`, `large`, `flexi-heavy`, `thin-availability`,
`multi-absence` — it is also short more often, and the difference is exactly the shifts it failed to
fill. Where coverage matches, the two agree to the point.

`early-notice` is the cleanest read on the notice multiplier: the same disruption, given days of
notice instead of hours, scores 20 against `headline`'s 63, while the cost baseline goes *up* to 517
because a cold solve reshuffles the whole week regardless of when it was told.

## Quality vs. time budget

**The curve is flat, and the reason is that the question does not arise at this size.** Every solver
run over the whole set — 2,268 of them across the 1 s, 5 s and 30 s budgets — returned `OPTIMAL`, and
the longest search anywhere was **15.4 ms**. No answer changed with the budget on any of the 756
(case, method, seed) triples, so the three budgets are indistinguishable case by case (`D-107`). Nothing was ever cut off by a budget, so there is no
anytime behaviour to plot and no quality to trade for time.

That is a result about the instance distribution rather than about the solver, and it is stated
rather than shown as three identical bars. A one-week horizon over 8–25 employees and 21 shift
instances is small for CP-SAT. The T3 fallback ladder — exact, then time-boxed with a reported gap,
then greedy — is designed for a regime this set does not reach, and the honest position is that its
time-boxed rung is currently unexercised by any committed benchmark. What the numbers here do
support is the opposite scheduling concern: at 3 ms of search against 5 ms of model construction, the
thing worth caching is the compiled model, which is what T3 already plans.

## Reproduction

    uv run python -m benchmarks.suite --write     # regenerate the instance manifest
    uv run python -m benchmarks.run --write       # regenerate results.json

Deterministic given the code: generation is seeded per case (`D-073`) and every solve carries an
explicit solver seed. The numbers above are from `benchmarks/results.json` at
`generator_version: 1`, solver seeds `7, 11, 13`, budgets 1 s / 5 s / 30 s.

**One worker per solve.** `model.solve` defaults to `workers=1` and the benchmark does not change it,
so these figures are single-threaded and the thread-to-core ratio is 1:1 by construction. That is the
right default for a throughput problem across many small tenants — the scaling axis stated at the top
of this file — where cores are better spent on concurrent tenants than on parallel search within one.
A multi-worker sweep would be a separate study and is not one of these numbers.

Hardware: Apple Silicon (arm64), macOS 27.0, Python 3.12.13, `ortools` 9.15.6755. Wall-clock figures
in milliseconds will move with the machine; the paired comparisons — warm against cold, seed against
seed — are ratios on one machine and are the ones meant to travel.
