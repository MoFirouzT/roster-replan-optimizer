# The benchmark set, the generator, and four methods

**Status:** Implemented 2026-08-14
**Reconstructed 2026-09-02** from [`benchmarks/`](../../benchmarks),
[`repair.py`](../../roster_replan/repair.py), [`benchmarks.md`](../benchmarks.md), the
studies cited below, the mutant catalogue, and the commits of 2026-08-13 to 2026-08-14.
**It is not the work order this component was built from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`model.md`](model.md) and [`disruption.md`](disruption.md), whose
objective every method is scored on.

## Objective

A seeded instance generator, a committed set of scenarios drawn from it, and four methods
measured on the same yardstick, so the claim that a disruption objective beats a cold
re-solve is a number rather than an argument.

## Motivation

The product claim is that replanning beats re-solving. Nothing in the model proves that,
and an undefined instance distribution makes a p95 unfalsifiable. This component exists
to define the distribution, commit it, and measure the claim on it, including against a
baseline that was expected to lose.

## Canonical reference

[`benchmarks.md`](../benchmarks.md) owns the scaling axis, the instance distribution, the
committed set, the four methods, the results tables, the frontier, and the reproduction
commands. [`guide/limits.md`](../guide/limits.md) owns what a reader should take from
them.

## Governing reference

None for the generator. The nurse-rostering benchmark set used later as a source of
foreign incumbents is cited in [`cross-week-rules.md`](cross-week-rules.md).

## Parameters and configuration

Seven generator axes, all seeded: `employees` 8 to 25, `demand_ratio`,
`scarce_skill_share`, `flexi_share`, `availability_density`, `event`, and
`event_day`/`event_hour`. `headline` is Saturday 09:00.

`demand_ratio` is a **target rather than a measurement**: what is reported is what the
instance turned out to be, over the pairs surviving the model's own presolve
([`D-070`](../decisions.md#d-070)). Reporting the nominal figure instead would quietly
settle the D0 to D4 study's answer, because tightness is the knob that decides whether it
can see anything at all.

## Interfaces

```bash
uv run python -m benchmarks.suite --write     # regenerate the instance manifest
uv run python -m benchmarks.run --write       # regenerate results.json
```

**The set is its seeds.** Generation is deterministic, so a class name and a seed name an
instance exactly, and what is committed is a manifest of fingerprints rather than 84
payloads ([`D-073`](../decisions.md#d-073)). Each case carries two fingerprints, `week`
and `incumbent`, so a stale manifest says which layer moved
([`D-074`](../decisions.md#d-074)).

## Layering

*The greedy baseline is solver-free*, and the contract carries two claims at once
([`D-078`](../decisions.md#d-078)): as a baseline it must not be the solver in disguise,
and as the third rung of the fallback ladder it must work when the solver did not.

*The penalty search is solver-free* covers the annealing study.

## Build tasks

- [x] A seeded generator, one parameter per axis.
- [x] Two-phase case construction: build a week, solve it cold, publish it as the
      incumbent, then inject the event ([`D-068`](../decisions.md#d-068)).
- [x] Commit fourteen classes at six seeds, by fingerprint.
- [x] Implement the four methods, including a solver-free greedy repair.
- [x] Score every method on the scenario's shipped D2 profile, whatever it optimised.
- [x] Segment results on `base_shortfall` and never pool across it.

## Test contract

| Claim | Layer |
| --- | --- |
| The generator varies the axis it says it varies | `test_generator.py`, seven mutants |
| The committed set is what the manifest says | `test_suite.py`, seven mutants |
| Each method is the method it claims to be | `test_methods.py`, four mutants |
| Greedy never calls the solver and never touches the pinned past | `test_methods.py`, plus the import contract |
| The penalty search is a real search | `test_anneal.py`, four mutants; `test_weights.py`, two |

`methods-hint-implemented-as-a-constraint` is the load-bearing one: a hint written as a
constraint would return the best roster that keeps the damage and report it as the
optimum.

## Acceptance gate

*Blocks:* the product claim.

- [x] **The objective is what does the work.** Against the cost baseline, mean disruption
      falls from **307 to 65** and mean changed assignments from **12.4 to 2.4**, on
      identical instances with identical coverage.
- [x] Nothing is filtered out of the set ([`D-075`](../decisions.md#d-075)). Twelve of 84
      cases start from a week that cannot be fully staffed; they stay in, with
      `base_shortfall` recorded, and the analysis segments rather than the generator
      pruning.
- [x] Every solver run returns `OPTIMAL`. **2,268 of 2,268**, longest search 15.4 ms.
- [!] **The warm start is a rounding error.** Paired on case, seed and budget, the hint
      reduces search time on **662 of 756** runs at a median paired ratio of **0.906**:
      9% of a 3 ms search, invisible beside a 5 ms build. It never changes the answer
      ([`D-082`](../decisions.md#d-082), [`warm-start.md`](../studies/warm-start.md)).
      Calling the system warm-started oversells the part of it that is warm.
- [!] **Greedy ties the optimum on 71 of 84 cases** ([`D-105`](../decisions.md#d-105)).
      That is the honest reading of a baseline expected to be weak. Its lower *average*
      disruption is not a win: it gets there by leaving more shifts unstaffed, 0.31
      against 0.15 on clean weeks, which is exactly the trade the shortfall weight
      refuses. On the 13 cases where it left an extra hole, the repair needed a chain, and
      greedy by construction does not look for one.
- [!] **There is no quality curve to draw.** No answer changed across the 1 s, 5 s and
      30 s budgets on any of the 756 triples, because nothing was ever cut off
      ([`time-budget.md`](../studies/time-budget.md),
      [`D-107`](../decisions.md#d-107)). That is a result about the distribution, stated
      rather than shown as three identical bars, and it leaves the ladder's time-boxed
      rung unexercised by any committed case.

## Measured results

**The distribution itself is a finding.** The original twelve classes put 60 of 72 cases
at a demand ratio of about 0.70 and left nothing between 0.73 and 0.89, which is what
varying one axis at a time from a slack baseline produces. The middle is where the
methods separate:

| Class | Demand ratio | Greedy ties | Greedy short | Optimal short |
| --- | --- | --- | --- | --- |
| `loose` | 0.35 | 6/6 | 0.00 | 0.00 |
| `headline` | 0.70 | 6/6 | 0.17 | 0.17 |
| `busy` | 0.80 | 4/6 | 0.33 | **0.00** |
| `tight` | 0.90 | 4/6 | 1.00 | 0.67 |
| `overloaded` | 0.95 | 3/6 | 1.17 | 0.67 |

**Sampling the ends of the coverage axis would have given the wrong answer**
([`D-105`](../decisions.md#d-105)). `busy` is the cleanest row: full coverage was
available, the optimiser found it on every seed, and greedy missed it on two.

**Conjunction was tried first and rejected.** Piling demand, skill scarcity and thin
availability together produces weeks that are structurally short, and there greedy ties
6 of 6 at every setting: both methods leave the same unfillable holes. Hardening the
benchmark that way makes it blind rather than sharper.

**The cost baseline is indifferent, and its own numbers prove it.** Across three solver
seeds on one case its disruption moves by a median of 100 points and by up to 260, on 52
of 84 cases. The disruption methods move by **zero**, on every case at every seed
([`D-080`](../decisions.md#d-080)). A single seed's number would have been an accident
reported as a result.

**Pricing a hard rule was measured and the easy distribution gives the wrong answer**
([`penalty-search.md`](../studies/penalty-search.md),
[`D-128`](../decisions.md#d-128)). On the committed set there is a penalty setting that is
both safe and near-optimal, which taken alone reads as a partial falsification of
[`D-002`](../decisions.md#d-002). On the one genuinely hard instance this project has, no
setting works at all.

## Out of scope

- **Decomposing a large instance.** The scaling axis is throughput across many small
  tenants and the latency one of them feels, not a single large roster.
- **A student share.** `R-STUDENT-QUOTA` is not encoded, so the knob would move no
  constraint and would make this table look richer than the distribution is
  ([`D-072`](../decisions.md#d-072)).
- **Widening the set after the fact to manufacture a gap against greedy**
  ([`D-083`](../decisions.md#d-083)). Median damage across the set is 1 assignment and the
  maximum is 3, an axis this distribution does not vary, and that is recorded rather than
  fixed by adding cases that flatter the thesis.
- **Committing benchmark results as a claim.** The analysis is committed; the numbers are
  regenerated ([`D-084`](../decisions.md#d-084)).
- **A multi-worker sweep.** Every figure is single-threaded at one worker per solve,
  which is the right default for a throughput problem.
- **Absolute milliseconds as a guarantee.** The timing balance is committed and asserted;
  wall-clock figures move with the machine ([`D-096`](../decisions.md#d-096)).

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Is a case an instance or a scenario?** A scenario: a published week and something
   that went wrong with it ([`D-068`](../decisions.md#d-068)). A replan is a function of
   both.

2. **Is the incumbent hand-built?** No, solved cold by the system under test
   ([`D-069`](../decisions.md#d-069)). **This is the benchmark's weak point and it is
   stated rather than buried**: these numbers show a replan beats a re-solve *given a
   roster this model would produce*. [`cross-week-rules.md`](cross-week-rules.md) closes
   the half of that which was not blocked.

3. **How is low demand expressed?** By opening fewer shift instances, not by thinning a
   full grid ([`D-071`](../decisions.md#d-071)). Instance size then varies with tightness,
   so a solve-time comparison across tightness has to report both.

4. **Is every method scored on its own objective?** No, on one yardstick
   ([`D-079`](../decisions.md#d-079)). Scoring each under its own would make the table a
   tautology: the cost solve would report zero disruption, because its profile prices
   none.

5. **Do classes that differ only in the event share a base week?** Yes
   ([`D-076`](../decisions.md#d-076)), which makes the event axis a controlled comparison
   rather than a comparison of instances.

6. **Is search time reported separately from end to end?** Yes
   ([`D-081`](../decisions.md#d-081)), and the record's premise later died at one week:
   the canonical optimum moved the build-to-search balance from 1.52 to 0.985, and the
   test pinning the old claim was retired rather than updated
   ([`D-119`](../decisions.md#d-119)).

---

*The ledger: [`README.md`](README.md). The numbers:
[`benchmarks.md`](../benchmarks.md). Every measurement:
[`studies/`](../studies/README.md).*
