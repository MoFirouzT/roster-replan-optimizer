# The job service

**Status:** Implemented 2026-08-20
**Reconstructed 2026-09-02** from [`service/`](../../roster_replan/service),
[`ladder.py`](../../roster_replan/ladder.py), [`guide/api.md`](../guide/api.md),
[`studies/model-cache.md`](../studies/model-cache.md), the mutant catalogue, and the commits
of 2026-08-13 to 2026-08-20, and **it is not the work order this component was built from**:
this project had none
([`documentation.md`](documentation.md#specs-for-the-built-components)).
**Depends on:** [`model.md`](model.md) and [`validation.md`](validation.md).

## Objective

An HTTP surface that takes a replan, runs it as a job, and **never returns nothing**:
every answer is a roster or a named reason, re-verified by the independent checker before
it leaves.

## Motivation

Solves take real time, so a synchronous request either blocks or lies about how long it
will take. That decides the shape: enqueue, poll, cancel.

The harder half is what happens when the solve does not go well. A planner whose Saturday
just fell apart is not helped by a `500`, and is actively harmed by a plausible roster
nobody checked. The ladder exists so that degrading is a described state rather than an
accident.

## Canonical reference

[`guide/api.md`](../guide/api.md) owns the routes, the request schema, the four
caller-computed quantities, what is rejected before any solve, the ladder, the tool
surface, health, and what is not built. The recommendation surface it documents is
specified in [`tools.md`](tools.md).

## Governing reference

None. Nothing here rests on a published source.

## Parameters and configuration

Concurrency is chosen first and each solve gets an equal share of what remains, so their
product fits the box. `model.solve` defaults to `workers=1`. **CP-SAT with 8 workers in a
1-vCPU container is slower**, and over-subscription is not merely wasteful: the portfolio
search assumes the threads it was promised.

## Interfaces

| Route | Behaviour |
| --- | --- |
| `POST /v1/replans` | `202`, a job id, a `Location`. `422` and the defects if unlawful |
| `GET /v1/replans/{id}` | The job, and its answer once terminal |
| `DELETE /v1/replans/{id}` | Cancel. Terminal jobs come back unchanged |
| `GET /v1/tools`, `POST /v1/tools/{name}` | The five tools, synchronous |
| `GET /v1/health` | Solver health, which is not HTTP health |

**A rejected request still gets a job id**, so a caller's flow is the same either way and
the defects sit at the URL a result would have occupied.

The wire schema in `service/contracts.py` is **its own schema, not a serialisation of the
domain** ([`D-090`](../decisions.md#d-090)), held to it by a round-trip identity test
rather than by convention, so an internal change never breaks a caller.

## Layering

- *The solver core never reaches the service layer.*
- *The natural-language layer is an accelerator: nothing deterministic reaches it.*
  `roster_replan.service` may not import `roster_replan.nl` or `anthropic`.
- *The shared schema depends on nothing.*

**No language model is reachable from this service**, and that is a contract rather than
a convention. Everything the service answers is derived.

## Build tasks

- [x] Async job queue over synchronous HTTP: enqueue, poll, cancel
      ([`D-010`](../decisions.md#d-010)).
- [x] A stateless solver behind an in-process queue that is not
      ([`D-011`](../decisions.md#d-011)).
- [x] Per-tenant queues that rotate, so one large tenant cannot starve the small ones
      ([`D-091`](../decisions.md#d-091)).
- [x] The four-rung ladder, with the gap reported rather than hidden.
- [x] Re-verify every returned roster with the independent checker.
- [x] Report solver health as distributions, with `rungs` and `fallback_rate`.

## Test contract

| Claim | Layer |
| --- | --- |
| The queue rotates rather than serving one FIFO | `test_service.py::service-queue-is-a-plain-fifo` |
| The wire round-trip loses nothing | four `service` mutants, each dropping one field |
| Lawfulness is validated at the head of every solve | `service-skips-lawfulness-validation` |
| Solver threads respect the concurrency choice | `service-solver-threads-ignore-concurrency` |
| Each rung is reached when it should be, and no other | `test_ladder.py`, four mutants |
| The ladder checks its own output | `ladder-skips-the-checker-on-its-own-output` |

**The time-boxed rung is tested by handing the ladder a time-boxed answer, not by racing
a budget** ([`D-122`](../decisions.md#d-122)). A test that tries to make a solver run out
of time is a test of the machine it runs on.

## Acceptance gate

*Blocks:* nothing downstream; this is the outer surface.

- [x] Nothing comes back unchecked. Every returned roster is re-verified by a plain
      function that imports no solver, which matters most on the two rungs no solver
      stands behind.
- [x] A timeout and an infeasibility are different answers, and the response says which
      ([`D-094`](../decisions.md#d-094)).
- [x] `violations_returned` is counted by the independent checker rather than by the
      solver marking its own work.
- [!] **The per-tenant compiled-model cache the design asked for got 0 hits in 144
      solves, and was deleted.** A replan changes the model's own inputs, so the key was a
      claim that went stale ([`model-cache.md`](../studies/model-cache.md),
      [`D-149`](../decisions.md#d-149)). At 3 ms of search against 5 ms of build,
      caching the compiled model was the obvious thing to try and it was wrong.
- [!] **The time-boxed rung is unexercised by any committed benchmark case.** Every one of
      2,268 runs returned `OPTIMAL`, so the ladder is built for a regime this distribution
      does not reach ([`benchmark-set.md`](benchmark-set.md)).
- [!] **Cancelling does not stop the CPU work.** The job is marked cancelled at once and
      its result discarded, so the caller's contract holds, but the search runs to its
      budget.

## Measured results

**A `200` from this API means a roster came back, not that it was a good one.** The
ladder guarantees an answer, so a service falling to its greedy rung on every request
looks perfect to any HTTP monitor. `rungs` and `fallback_rate` exist to make that visible,
and distributions are p50/p95/max rather than means, because a mean hides the tail and the
tail is what a budget is set against.

**A cold solve is never infeasible**, because the coverage floor is priced rather than
required ([`D-047`](../decisions.md#d-047)). Impossible demand comes back short. The only
way a cold solve fails is exhaustion, and the lower two rungs are replan-only: greedy
repairs an incumbent and last-known-good returns one, so *never return nothing* is a
promise about replanning.

**The `incumbent` rung can return an illegal roster, deliberately.** After a disruption
the published roster is usually already broken, so it comes back with its violations
named, marked as the floor rather than as a repair.

**The guarantee starts at the payload** ([`D-150`](../decisions.md#d-150)). Offsets must
be computed by subtracting two zone-aware instants, never as `day * 24 + hour`: in
`Europe/Brussels` two weeks a year are 167 or 169 hours long, and an hour of drift is a
rest gap this service certifies and an inspector does not. **Nothing here can catch
that**, and the limit is written where a caller reads it rather than assumed.

## Out of scope

- **An external queue store.** State lives in a dict, so replicas do not share a queue and
  a restart loses it. The solver is stateless, so swapping in Redis or SQS touches nothing
  below `service/` ([`D-011`](../decisions.md#d-011)).
- **A metrics backend.** The signals are on `/v1/health`; pushing them somewhere is a
  deployment choice.
- **Interrupting a running solve.**
- **Weighted fairness across tenants.** Round-robin, not weighted
  ([`D-091`](../decisions.md#d-091)).
- **Any tool that writes.** All five are read-only; `validate_profile` checks and reports
  and the save is the caller's. A tool a model can call should not be able to persist a
  policy.
- **Defaulting an omitted field.** `omitted is never defaulted`: an empty `flexi_eligible`
  would *deny* eligibility where the caller merely forgot to say, and neither that nor a
  defaulted weekly budget is detectable downstream, because both produce a perfectly
  plausible roster.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Sync or async?** Async ([`D-010`](../decisions.md#d-010)) for replans, synchronous
   for tools, because a tool call is somebody asking a question and waiting.

2. **Is the wire schema the domain schema?** No
   ([`D-090`](../decisions.md#d-090)), and the two are held together by a round-trip test.

3. **Does a degraded answer look like a good one?** No
   ([`D-094`](../decisions.md#d-094)). A timeout and an infeasibility are different
   answers, and the gap on the time-boxed rung is reported rather than hidden.

4. **Does validation degrade into a best-effort solve?** No. A non-empty result rejects
   the request outright, because a malformed request has no meaningful optimum
   ([`D-040`](../decisions.md#d-040)).

5. **Is a horizon longer than a week allowed?** Yes for whole weeks, no for part of one
   ([`D-113`](../decisions.md#d-113)). A horizon ending part-way through a week leaves a
   stub that weekly rest cannot fit inside.

6. **Is the recommendation list a sixth tool?** No, a library function
   ([`tools.md`](tools.md)). A ranked list of ways to override labour rules, handed to a
   model, reads as an instruction however it is grouped.

---

*The ledger: [`README.md`](README.md). The contract:
[`guide/api.md`](../guide/api.md). The reasoning:
[`decisions.md`](../decisions.md).*
