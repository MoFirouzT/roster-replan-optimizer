# Benchmarks

> **Status: outline.** Filled in T2. Every `[B-n]` placeholder in the README resolves from here.

## The scaling axis

Three possible problems: (i) one instance too big, (ii) too many instances, (iii) too slow
interactively. **This is (ii) and (iii).** Benchmarks measure throughput and interactive latency
across many small tenants, not one large monolith. Answering the decomposition question when the
real problem is throughput is reciting, not diagnosing.

## Instance distribution

An undefined distribution makes a p95 unfalsifiable. Generator parameters, all seeded and committed:

- tenant size (8–25 employees)
- coverage tightness (slack ratio between demand and eligible supply)
- skill scarcity
- flexi-job / student / permanent contract mix
- availability density
- **disruption event**: single sick call · multiple absences · demand spike · late availability
  withdrawal
- event timing: day of week and hour — the Saturday 09:00 sick call is the headline class

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
