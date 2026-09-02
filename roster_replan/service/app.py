"""The HTTP boundary: POST enqueue, GET poll, DELETE cancel, plus telemetry.

    uv run uvicorn roster_replan.service.app:app --reload

`internals/design.md` asks for this layer to be **deliberately boring** -- "endpoints, validation,
queue handling, error mapping -- so a non-specialist can read and change it. The intricate
part is small and heavily tested." So there is no solver logic here. Every route is a
translation between a Pydantic model and a job, and the one decision it makes is which
status code corresponds to which job state.

## Why the telemetry route exists at all

*"Web observability says nothing about solver health: latency and error rate stay green
while the optimiser quietly returns garbage."* A 200 from this API means a roster came back,
not that it was a good one -- the fallback ladder guarantees an answer, so a service falling
to its greedy rung on every request would look perfect to any HTTP monitor. `GET /v1/health`
reports the signals that would show it: the distribution of rungs, the fallback rate, the
optimality gaps and, most directly, the count of returned rosters carrying violations.
"""

from __future__ import annotations

import statistics
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response

from ..ladder import EXACT, RUNGS
from . import contracts, jobs, tools
from .contracts import API_VERSION, JobOut, ReplanRequest, answer_out

# Concurrency is a deployment knob rather than a constant, but it needs a default that is
# safe on a small container: two solves at once, each given an equal share of the cores.
CONCURRENCY = 2


def create_app(*, concurrency: int = CONCURRENCY) -> FastAPI:
    store = jobs.Store()
    worker = jobs.Worker(store, concurrency=concurrency)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()

    app = FastAPI(
        title="roster-replan",
        version=API_VERSION,
        summary="Minimum-disruption shift-roster replanning.",
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.worker = worker

    @app.post(f"/{API_VERSION}/replans", status_code=202, response_model=JobOut)
    async def enqueue(request: ReplanRequest, response: Response) -> JobOut:
        """202 with a job, or 202 with a rejection.

        A payload that Pydantic accepts but `validation.py` rejects still gets a job id and
        a `rejected` state rather than a 4xx body with no id. The caller's flow is then the
        same either way -- poll the id -- and the defects are readable at the same URL as a
        result would have been.
        """
        job = store.submit(request)
        if job.state == jobs.REJECTED:
            response.status_code = 422
        else:
            response.headers["Location"] = f"/{API_VERSION}/replans/{job.id}"
        return _out(job)

    @app.get(f"/{API_VERSION}/replans/{{job_id}}", response_model=JobOut)
    async def poll(job_id: str) -> JobOut:
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"no job {job_id}")
        return _out(job)

    @app.delete(f"/{API_VERSION}/replans/{{job_id}}", response_model=JobOut)
    async def cancel(job_id: str) -> JobOut:
        job = store.cancel(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"no job {job_id}")
        return _out(job)

    @app.get(f"/{API_VERSION}/tools")
    async def tool_manifest() -> list[dict]:
        """What a tool-calling caller enumerates, schemas included."""
        return tools.manifest()

    @app.post(f"/{API_VERSION}/tools/{{name}}")
    async def invoke(name: str, payload: dict) -> dict:
        """Synchronous, unlike `/replans`, and that is a deliberate difference.

        A tool call is exploratory — a planner or an agent asking a question and waiting for
        the answer — where an enqueued replan is production work with a budget and a
        cancellation story. Both exist because they are different interactions, not because
        one supersedes the other.
        """
        try:
            return tools.call(name, payload)
        except KeyError as unknown:
            raise HTTPException(status_code=404, detail=str(unknown)) from unknown
        except ValueError as bad:
            raise HTTPException(status_code=422, detail=str(bad)) from bad

    @app.get(f"/{API_VERSION}/health")
    async def health() -> dict:
        return telemetry(store, queue_depth=store.depth(), concurrency=concurrency)

    return app


def _out(job: jobs.Job) -> JobOut:
    return JobOut(
        id=job.id,
        state=job.state,
        tenant=job.tenant,
        seed=job.request.seed,
        profile_version=job.request.profile_version,
        answer=(
            None
            if job.answer is None
            else answer_out(job.answer, contracts.to_domain(job.request.instance))
        ),
        error=job.error,
        defects=job.defects,
    )


def telemetry(store: jobs.Store, *, queue_depth: int, concurrency: int) -> dict:
    """The solver-health signals `guide/api.md` lists, computed from finished jobs.

    Reported as a snapshot rather than pushed to a metrics backend, because the choice of
    backend is a deployment decision and the *signals* are the part this project owes. Each
    one answers a failure that leaves HTTP green:

    - `rungs` and `fallback_rate` -- the optimiser degrading quietly.
    - `violations_returned` -- the worst outcome available: a roster that breaks a hard rule
      and was still returned with a 200. Counted from the independent checker, so it is not
      the solver marking its own work.
    - `gap` -- answers that are feasible but unproven, which look identical to optimal ones
      from outside.
    """
    finished = [j for j in store.all() if j.answer is not None]
    answers = [j.answer for j in finished]
    times = [a.seconds for a in answers]
    gaps = [a.gap for a in answers if a.gap is not None]

    return {
        "api_version": API_VERSION,
        "queue_depth": queue_depth,
        "concurrency": concurrency,
        "solver_workers": jobs.solver_workers(concurrency),
        "jobs": {
            state: sum(1 for j in store.all() if j.state == state)
            for state in (
                jobs.QUEUED,
                jobs.RUNNING,
                jobs.SUCCEEDED,
                jobs.FAILED,
                jobs.CANCELLED,
                jobs.REJECTED,
            )
        },
        "rungs": {rung: sum(1 for a in answers if a.rung == rung) for rung in RUNGS},
        "fallback_rate": (
            0.0 if not answers else sum(1 for a in answers if a.rung != EXACT) / len(answers)
        ),
        "violations_returned": sum(1 for a in answers if a.violations),
        "solve_seconds": _distribution(times),
        "gap": _distribution(gaps),
    }


def _distribution(values: list[float]) -> dict:
    """p50 and p95 rather than a mean. A mean solve time hides the tail, and the tail is
    what a time budget is set against."""
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "p50": statistics.median(ordered),
        "p95": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
        "max": ordered[-1],
    }


app = create_app()
