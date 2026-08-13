# Benchmarks

> **Status: generator built, results outstanding.** The instance distribution below is
> reconciled with `benchmarks/generator.py`. Everything under *Results* is still T2's to fill, and
> every `[B-n]` placeholder in the README resolves from here.

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

## Methods compared

| Method | Isolates |
|---|---|
| Cold re-solve, cost objective | the status quo |
| Greedy nearest-eligible repair | the human default — "just call someone" |
| Cold solve, disruption objective | the objective effect, separated from warm starting |
| Warm-started replan | the thesis |

Both axes for all four: solve time (p50/p95), disruption score (D2), cost delta. A method that is
fast and disruptive has not won.

## Results

`[TODO — T2]`

## The frontier

Disruption vs. cost/coverage, per scenario class. The trade-off is a choice, not a constant:
absorbing a Saturday sick call costs either a few more euros or a few more disrupted people, and
the planner picks the point. **This chart goes in the README.**

`[TODO — T2]`

## Quality vs. time budget

Disruption achieved at 1s / 5s / 30s. Supports returning a good-enough answer immediately and
improving it in the background while the planner reads it.

`[TODO — T2]`

## Reproduction

`[TODO]` Command, seed, hardware, container core count and solver thread count. A benchmark whose
thread-to-core ratio is unstated is not reproducible.
