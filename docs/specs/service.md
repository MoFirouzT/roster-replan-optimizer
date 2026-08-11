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

## Fallback ladder

exact → time-boxed with the gap **reported, not hidden** → greedy repair → last known good.
Never return nothing.

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
