# Service

> **Status: outline.** Spec-first component — fill before implementing (T3).

## Pattern

Async job queue. POST enqueue / GET poll / DELETE cancel.

Synchronous HTTP works only for sub-second solves; at 30s–5min it produces timeouts, retries that
re-trigger expensive solves, request pile-up, no progress feedback and no cancellation. Event-driven
suits continuous replanning but makes *"why did my roster change?"* hard to answer.

## Statelessness

Payload in, payload out. **No database reads inside the solver service.** This is what makes solves
testable, replayable, and reproducible offline from a persisted input — debugging optimisation in
production is close to impossible without it.

## Contracts

Pydantic at the boundary. Versioned API contracts, so a model change never breaks a caller.

## Fallback ladder `[built — roster_replan/ladder.py]`

exact → time-boxed with the gap **reported, not hidden** → greedy repair → last known good.
Never return nothing.

| Rung | Promise | Reached when |
| --- | --- | --- |
| `exact` | proven optimal, gap 0 | the solve finished inside its budget |
| `time-boxed` | feasible, **gap reported** | the budget ran out with a solution in hand |
| `greedy` | legal, not optimal | the model had no solution to give |
| `incumbent` | what was published, violations named | greedy had nothing to repair from |

**`exact` and `time-boxed` are one solve, not two.** CP-SAT returns the best solution found
*and* the best proven bound when a time limit stops it, so re-solving with a smaller budget
to "try the fast rung first" would spend the budget twice to learn the same thing. Which rung
an answer came from is read off the outcome, not decided in advance.

**The ladder imports no web layer.** The intricate part stays small and testable; the
boundary stays boring. `ladder.py` knows nothing about HTTP, jobs or queues.

Three things about it are consequences rather than choices, and each is asserted by test:

- **The lower rungs are replan-only.** Greedy repairs an incumbent and last-known-good
  returns one, so "never return nothing" is a promise about *replanning*. The cold path
  cannot keep it.
- **A cold solve is never infeasible** — the empty roster satisfies every hard constraint,
  because the coverage floor is soft (`D-018`). Impossible demand comes back priced, not
  refused, so the only way a cold solve fails is exhaustion.
- **The `incumbent` rung can return an illegal roster, deliberately.** After a disruption the
  published roster is usually already broken. It is returned with its violations named and
  marked as the floor rather than a repair.

**Every rung is reachable by construction**, because none of them is reachable by accident:
no instance in the committed set takes more than 12.4 ms, so `time-boxed`, `greedy` and
`incumbent` would otherwise ship untested. `tests/test_ladder.py` forces each one, and the
mutation harness carries a mutant per rung.

### A timeout is not an infeasibility (`D-089`)

The ladder's first version reported one as the other, because `solve` returned an empty
`list[Gate]` for both. See the record; the fix is a third return type, and the distinction
matters most to T4's explainer, which is specified to turn a core into prose.

## Telemetry

Web observability says nothing about solver health: latency and error rate stay green while the
optimiser quietly returns garbage. Required signals: solve-time distribution, terminating status
(optimal / feasible / infeasible / timeout), objective value, optimality gap, constraint-violation
count from the checker, fallback rate.

## Runtime

Solver workloads are not web workloads — CPU-bound, memory-hungry, bursty, long-running.
Autoscale on queue depth, not CPU. Right-size solver threads to container cores (CP-SAT with 8
workers in a 1-vCPU container is *slower*). Cache the compiled model per tenant; at these instance
sizes, building the model can cost more than solving it. Backpressure and weighted scheduling across
tenants so one large customer cannot starve two thousand small ones.

## Tool surface `[T4]`

`solve`, `replan`, `explain_infeasibility`, `what_if`, `validate_profile` exposed as callable tools
over this API. `what_if` — *"what if I hire one more flexi-jobber?"* — is a parameter sweep over
existing machinery and the question owners actually ask.

## Boundary discipline

Everything around the solver stays deliberately boring — endpoints, validation, queue handling,
error mapping — so a non-specialist can read and change it. The intricate part is small and heavily
tested.
