"""The job queue: enqueue, poll, cancel, and fair scheduling across tenants.

`service.md` asks for an async job queue rather than synchronous HTTP, because a solve that
can take 30 seconds produces timeouts, retries that re-trigger expensive solves, request
pile-up, no progress feedback and no cancellation. This module is that queue.

## Fairness is the reason this is not a plain FIFO

*"Backpressure and weighted scheduling across tenants so one large customer cannot starve
two thousand small ones."* A single FIFO gives a tenant who submits 500 replans at 09:00 the
next 500 slots, and every other tenant waits behind them. So the queue is **per tenant**, and
the scheduler rotates: each turn takes one job from the next tenant that has one. A tenant
with 500 queued jobs gets one slot per rotation, exactly like a tenant with one.

This is round-robin rather than weighted, and the difference is deliberate. Weighting needs a
per-tenant priority that nothing in this project can currently justify — plan tier, contract
value, queue age are all real answers and none of them is derivable from a payload. Equal
shares is the defensible default, and `next_batch` is where a weight would be applied when
there is a reason for one.

## Solver threads against container cores

`service.md`: *CP-SAT with 8 workers in a 1-vCPU container is slower.* Two numbers have to
agree — how many solves run at once, and how many threads each is given. Their product is
bounded by the cores actually available, so concurrency is chosen first and each solve gets
an equal share of what is left.

## Two limits of an in-process queue, stated

**It is single-process.** State lives in a dict, so two replicas do not share a queue and a
restart loses it. That is the correct shape for the tier — `service.md` demands the *solver*
be stateless, and it is: `run_job` takes a payload and returns a payload, reads no database,
and would behave identically behind Redis or SQS. Swapping the store is a contained change
and is where a real deployment goes next.

**Cancelling a running solve does not stop the CPU work.** The job is marked cancelled
immediately and its result is discarded, so the caller's contract is honoured, but CP-SAT
keeps searching until its budget expires. Interrupting it needs a solution callback wired
through `model.solve`, which the solver core does not currently expose. Recorded here rather
than in a comment nobody reads, because the misreading — that `DELETE` frees a core — is the
kind that only shows up under load.
"""

from __future__ import annotations

import asyncio
import dataclasses
import os
import threading
import time
import uuid
from collections import deque

from ..compiled import ModelCache
from ..ladder import Answer, answer as solve_answer
from ..validation import validate_instance
from . import contracts
from .contracts import ReplanRequest

QUEUED = "queued"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
CANCELLED = "cancelled"
REJECTED = "rejected"

TERMINAL = (SUCCEEDED, FAILED, CANCELLED, REJECTED)


@dataclasses.dataclass
class Job:
    """One replan request and everything needed to replay it.

    `request` is kept in full after completion on purpose. `PLAN.md` requires every solve's
    input, profile version and seed to be persisted for replay, and a job that has discarded
    its input cannot be replayed however good its telemetry is.
    """

    id: str
    tenant: str
    request: ReplanRequest
    state: str = QUEUED
    answer: Answer | None = None
    error: str | None = None
    defects: list[dict] = dataclasses.field(default_factory=list)
    enqueued_at: float = dataclasses.field(default_factory=time.monotonic)
    started_at: float | None = None
    finished_at: float | None = None

    @property
    def done(self) -> bool:
        return self.state in TERMINAL

    @property
    def waited(self) -> float:
        started = self.started_at if self.started_at is not None else time.monotonic()
        return started - self.enqueued_at


class Store:
    """Jobs, per-tenant queues, and the rotation between them."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queues: dict[str, deque[str]] = {}
        self._rotation: deque[str] = deque()

    def __len__(self) -> int:
        return len(self._jobs)

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def all(self) -> list[Job]:
        return list(self._jobs.values())

    def submit(self, request: ReplanRequest) -> Job:
        """Validate and enqueue. A malformed request is rejected without reaching the queue.

        Rejection is a terminal state rather than an exception, so a caller who polls a
        rejected job gets the defects rather than a 404. The two input-validation layers stay
        distinct: Pydantic already answered *well-formed*, and this answers *lawful*.
        """
        instance = contracts.to_domain(request.instance)
        job = Job(id=uuid.uuid4().hex, tenant=request.tenant, request=request)
        self._jobs[job.id] = job

        defects = validate_instance(instance)
        if defects:
            job.state = REJECTED
            job.finished_at = time.monotonic()
            job.defects = [
                {
                    "field": d.field,
                    "message": d.message,
                    "observed": _plain(d.observed),
                    "required": _plain(d.required),
                }
                for d in defects
            ]
            return job

        queue = self._queues.setdefault(request.tenant, deque())
        if not queue:
            self._rotation.append(request.tenant)
        queue.append(job.id)
        return job

    def cancel(self, job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None or job.done:
            return job

        queue = self._queues.get(job.tenant)
        if queue is not None and job_id in queue:
            queue.remove(job_id)
        job.state = CANCELLED
        job.finished_at = time.monotonic()
        return job

    def next_batch(self, limit: int) -> list[Job]:
        """Up to `limit` jobs, taking one from each tenant in turn.

        The rotation is what makes this fair. A tenant re-enters the back of the rotation
        after giving up a job, so a queue of 500 and a queue of 1 are served alternately
        rather than in submission order.
        """
        picked: list[Job] = []
        seen = 0

        while len(picked) < limit and self._rotation and seen <= len(self._rotation):
            tenant = self._rotation.popleft()
            queue = self._queues.get(tenant)
            seen += 1

            if not queue:
                continue

            job = self._jobs[queue.popleft()]
            if queue:
                self._rotation.append(tenant)

            # Cancelled while queued: already terminal, and its slot is not spent.
            if job.state != QUEUED:
                continue

            picked.append(job)
            seen = 0

        return picked

    def depth(self) -> int:
        return sum(len(q) for q in self._queues.values())


def _plain(value):
    """`InputDefect.observed` is typed `object` and may hold a set or a tuple, neither of
    which survives JSON. Rendered rather than dropped: the observed value is usually the
    most useful part of a rejection."""
    if isinstance(value, (set, frozenset, tuple, list)):
        return [_plain(v) for v in sorted(value, key=repr)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


# --- Running -------------------------------------------------------------------------


def solver_workers(concurrency: int) -> int:
    """CP-SAT threads per solve, so that concurrency times threads fits the cores.

    Over-subscribing is not merely wasteful, it is slower: `service.md` names the case
    directly, and CP-SAT's portfolio search assumes the threads it was promised.
    """
    return max(1, (os.cpu_count() or 1) // max(1, concurrency))


# One compiled-model cache per worker thread, never one shared between them.
#
# `CpModel` is not thread-safe, and a shared cache would hand the *same* model object to two
# concurrent solves whenever their fingerprints matched -- both would then set an objective
# and assumptions on it at once. That is a data race producing a plausible roster, which is
# the worst shape of bug available here. Thread-local storage removes the sharing rather than
# guarding it: no lock, no leasing, and concurrency stays real.
#
# The cost is one cache per thread instead of one per process. At a default concurrency of 2
# that is a rounding error, and it buys an invariant that does not depend on getting a lock
# right.
_caches = threading.local()


def _cache() -> ModelCache:
    existing = getattr(_caches, "cache", None)
    if existing is None:
        existing = ModelCache()
        _caches.cache = existing
    return existing


def run_job(job: Job, *, workers: int = 1, cache: ModelCache | None = None) -> Job:
    """Solve one job. Pure with respect to the store: payload in, payload out.

    Runs on a worker thread because CP-SAT is blocking and CPU-bound, and running it on the
    event loop would stall every other request in the process -- including the polls asking
    how this one is doing.
    """
    instance = contracts.to_domain(job.request.instance)
    store = _cache() if cache is None else cache
    try:
        job.answer = solve_answer(
            instance,
            seed=job.request.seed,
            budget_seconds=job.request.budget_seconds,
            workers=workers,
            built=store.get(instance, tenant=job.tenant),
        )
        # A `DELETE` that landed while this was searching has already told the caller the
        # job is cancelled. Overwriting that with `succeeded` here would make the state
        # depend on which of the two finished first.
        if job.state != CANCELLED:
            job.state = SUCCEEDED
    except Exception as error:  # noqa: BLE001 -- the boundary turns any failure into a state
        # The ladder is specified never to raise for an unsolvable instance, so reaching
        # here means a bug rather than an unsatisfiable request. It still must not take the
        # worker down with it: one poisoned payload would then stop every tenant's queue.
        if job.state != CANCELLED:
            job.state = FAILED
            job.error = f"{type(error).__name__}: {error}"
    finally:
        job.finished_at = time.monotonic()
    return job


class Worker:
    """Drains the store, `concurrency` solves at a time, until stopped."""

    def __init__(self, store: Store, *, concurrency: int = 2, poll_seconds: float = 0.01):
        self.store = store
        self.concurrency = concurrency
        self.poll_seconds = poll_seconds
        self.workers = solver_workers(concurrency)
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        self._stopped.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def _loop(self) -> None:
        while not self._stopped.is_set():
            batch = self.store.next_batch(self.concurrency)
            if not batch:
                await asyncio.sleep(self.poll_seconds)
                continue

            for job in batch:
                job.state = RUNNING
                job.started_at = time.monotonic()

            await asyncio.gather(
                *(
                    asyncio.to_thread(run_job, job, workers=self.workers)
                    for job in batch
                )
            )

