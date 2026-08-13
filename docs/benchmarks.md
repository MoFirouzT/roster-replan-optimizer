# Benchmarks

> **Status: generator and instance set built, results outstanding.** The distribution and the
> committed set below are reconciled with `benchmarks/generator.py` and `benchmarks/suite.py`.
> Everything under *Results* is still T2's to fill, and every `[B-n]` placeholder in the README
> resolves from here.

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

## The committed set

Twelve scenario classes, six seeds each — 72 cases, listed in `benchmarks/manifest.json`.

    uv run python -m benchmarks.suite --write

**The set is its seeds.** Generation is deterministic, so a class name and a seed name an instance
exactly, and what is committed is a manifest of fingerprints rather than 72 payloads (`D-073`). Each
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
| `loose`, `tight` | coverage tightness, at 0.35 and 0.90 |
| `small`, `large` | 8 and 25 employees |
| `scarce-skill` | scarce skill held by a quarter of staff |
| `flexi-heavy` | 60% flexi contracts |
| `thin-availability` | availability density 0.60 |
| `multi-absence`, `demand-spike`, `withdrawal` | the other three event types |
| `early-notice` | the same disruption with days of notice instead of hours |

**Nothing is filtered** (`D-075`). Ten of the 72 cases start from a week that cannot be fully
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

**The cost column will read as zeros until the cost model lands.** `cost_weight` ships at 0 and the
cost model is a flat rate (`D-050`), so two rosters of equal hours cost the same and the cold
baseline is not, today, a *cost* baseline. The disruption axis of that comparison is sound
regardless — a cold solve has no reason to resemble the incumbent, which is the entire point — but
the column is a placeholder and is marked as one rather than reported as a null result.

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
