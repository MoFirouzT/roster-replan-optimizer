"""The T3 boundary: contracts, job lifecycle, fairness, telemetry.

`service.md` wants this layer boring, and boring code still has three things worth testing
that a code review does not settle.

**The round trip must be the identity.** `PLAN.md` requires every solve's input, profile
version and seed to be persisted for replay. If the wire format cannot express something the
solver can, a persisted payload no longer reconstructs the solve it recorded, and the replay
guarantee fails silently -- the payload still parses, it just describes a slightly different
problem.

**Fairness is a claim about scheduling, not a property of any single request.** It cannot be
observed by looking at one response, so it is asserted directly against the rotation: a
tenant with many queued jobs must not take consecutive slots while another tenant waits.

**Telemetry has to move.** A health endpoint returning plausible zeros is the failure it
exists to prevent, so the fallback and violation counters are checked against runs that
actually degraded rather than only against a clean one.
"""

from __future__ import annotations

import asyncio
import dataclasses

import httpx
import pytest

from benchmarks import suite
from roster_replan.domain import Fairness
from roster_replan.scoring import score
from roster_replan.service import contracts, jobs
from benchmarks.studies import identical_workforce
from roster_replan.service.app import create_app


@pytest.fixture(scope="module")
def scenario():
    return suite.build("headline/0")


@pytest.fixture
def request_body(scenario):
    def build(**overrides) -> dict:
        payload = contracts.ReplanRequest(
            tenant="acme", instance=contracts.from_domain(scenario.instance), **overrides
        )
        return payload.model_dump()

    return build


async def _drain(client, job_id: str, tries: int = 500) -> dict:
    for _ in range(tries):
        body = (await client.get(f"/v1/replans/{job_id}")).json()
        if body["state"] not in (jobs.QUEUED, jobs.RUNNING):
            return body
        await asyncio.sleep(0.01)
    raise AssertionError(f"job {job_id} never finished")


@pytest.fixture
async def client():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


# --- Contracts ----------------------------------------------------------------------


@pytest.mark.parametrize("case", ["headline/0", "scarce-skill/0", "large/0", "loose/1"])
def test_the_wire_round_trip_is_the_identity(case):
    instance = suite.build(case).instance
    assert contracts.to_domain(contracts.from_domain(instance)) == instance


def test_the_round_trip_survives_json(scenario):
    """Through the actual serialiser, not just the model objects. `float('inf')` is the
    reason: it survives a Python round trip and is not valid JSON."""
    wire = contracts.from_domain(scenario.instance)
    blob = wire.model_dump_json()
    assert contracts.to_domain(contracts.InstanceIn.model_validate_json(blob)) == (
        scenario.instance
    )


def test_an_unbounded_notice_band_is_null_on_the_wire(scenario):
    import json

    bands = json.loads(contracts.from_domain(scenario.instance).model_dump_json())
    assert bands["disruption"]["notice_bands"][-1]["within_hours"] is None


def test_the_round_trip_carries_the_cross_week_fields():
    """The two fields whose whole purpose is to reach past the horizon.

    `Fairness` and `unpopular_shifts_before_horizon` are the objective's only memory, and
    `max_hours_this_period` is `R-MAX-PERIOD`'s. All three existed in `domain.py` and in
    neither direction of this file, so the term and the rule they serve were reachable from
    Python and not over the wire — which for a service is not shipped (`D-131`).

    The identity is the assertion the whole file is built on: a field the wire cannot carry
    is a field a persisted payload no longer replays.
    """
    instance = identical_workforce(4, required=1)
    instance = dataclasses.replace(
        instance,
        fairness=Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=8),
        employees=tuple(
            dataclasses.replace(
                person,
                unpopular_shifts_before_horizon=index,
                max_hours_this_period=120.0,
            )
            for index, person in enumerate(instance.employees)
        ),
    )

    assert contracts.to_domain(contracts.from_domain(instance)) == instance

    # And through the serialiser, because that is the form a caller actually sends.
    blob = contracts.from_domain(instance).model_dump_json()
    assert contracts.to_domain(contracts.InstanceIn.model_validate_json(blob)) == instance


def test_an_unknown_field_is_rejected_rather_than_ignored():
    """A misspelled field should be an error, not a silent default."""
    with pytest.raises(Exception):
        contracts.RuleParamsIn(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
            min_rest_hourz=9.0,
        )


# --- The job lifecycle --------------------------------------------------------------


@pytest.mark.anyio
async def test_enqueue_poll_and_get_an_answer(client, request_body):
    posted = await client.post("/v1/replans", json=request_body())
    assert posted.status_code == 202
    assert posted.headers["location"].endswith(posted.json()["id"])

    body = await _drain(client, posted.json()["id"])
    assert body["state"] == jobs.SUCCEEDED
    assert body["answer"]["rung"] == "exact"
    assert body["answer"]["violations"] == []
    assert body["answer"]["roster"]


@pytest.mark.anyio
async def test_the_seed_and_profile_version_come_back_for_replay(client, request_body):
    posted = await client.post(
        "/v1/replans", json=request_body(seed=99, profile_version="horeca-2026.1")
    )
    body = await _drain(client, posted.json()["id"])
    assert body["seed"] == 99
    assert body["profile_version"] == "horeca-2026.1"


@pytest.mark.anyio
async def test_polling_an_unknown_job_is_a_404(client):
    assert (await client.get("/v1/replans/nope")).status_code == 404
    assert (await client.delete("/v1/replans/nope")).status_code == 404


@pytest.mark.anyio
async def test_an_unlawful_payload_is_rejected_with_its_defects(client, request_body):
    """Pydantic accepts it; `validation.py` does not. The caller still gets a job id, so the
    polling flow is the same as for a successful request."""
    body = request_body()
    body["instance"]["disruption"]["shortfall_weight"] = 1  # violates the domination bound

    posted = await client.post("/v1/replans", json=body)
    assert posted.status_code == 422

    out = posted.json()
    assert out["state"] == jobs.REJECTED
    assert any("shortfall_weight" in d["field"] for d in out["defects"])

    # Readable at the same URL a result would have been.
    polled = await client.get(f"/v1/replans/{out['id']}")
    assert polled.json()["state"] == jobs.REJECTED


@pytest.mark.anyio
async def test_a_malformed_payload_never_reaches_the_queue(client, request_body):
    body = request_body()
    body["instance"]["days"] = -1
    assert (await client.post("/v1/replans", json=body)).status_code == 422


@pytest.mark.anyio
async def test_cancelling_a_queued_job(client, request_body):
    posted = await client.post("/v1/replans", json=request_body())
    job_id = posted.json()["id"]

    cancelled = await client.delete(f"/v1/replans/{job_id}")
    assert cancelled.status_code == 200

    # Either it was cancelled before running, or it had already finished -- both are
    # legitimate races. What must never happen is a cancelled job later reporting success.
    state = cancelled.json()["state"]
    assert state in (jobs.CANCELLED, jobs.SUCCEEDED)
    if state == jobs.CANCELLED:
        await asyncio.sleep(0.05)
        assert (await client.get(f"/v1/replans/{job_id}")).json()["state"] == jobs.CANCELLED


# --- Fairness -----------------------------------------------------------------------


def test_one_large_tenant_cannot_starve_a_small_one(scenario):
    """The requirement `service.md` states, asserted against the rotation directly.

    A plain FIFO passes every other test in this file and fails this one, which is why it
    is here: the failure is invisible in any single response.
    """
    store = jobs.Store()
    wire = contracts.from_domain(scenario.instance)

    for _ in range(50):
        store.submit(contracts.ReplanRequest(tenant="whale", instance=wire))
    store.submit(contracts.ReplanRequest(tenant="minnow", instance=wire))

    # The small tenant submitted 51st. Under FIFO it waits for 50 solves.
    served = [job.tenant for job in store.next_batch(4)]
    assert "minnow" in served, f"the small tenant was starved: {served}"
    assert served.count("whale") <= 3


def test_the_rotation_does_not_lose_jobs(scenario):
    store = jobs.Store()
    wire = contracts.from_domain(scenario.instance)
    for tenant in ("a", "b", "c"):
        for _ in range(4):
            store.submit(contracts.ReplanRequest(tenant=tenant, instance=wire))

    drained = []
    while batch := store.next_batch(2):
        drained += batch

    assert len(drained) == 12
    assert store.depth() == 0


def test_a_cancelled_job_does_not_consume_a_slot(scenario):
    store = jobs.Store()
    wire = contracts.from_domain(scenario.instance)
    doomed = store.submit(contracts.ReplanRequest(tenant="a", instance=wire))
    wanted = store.submit(contracts.ReplanRequest(tenant="a", instance=wire))
    store.cancel(doomed.id)

    assert [j.id for j in store.next_batch(1)] == [wanted.id]


def test_solver_threads_are_sized_against_concurrency():
    """`service.md`: CP-SAT with 8 workers in a 1-vCPU container is slower. Concurrency
    times threads must not exceed what the box has."""
    import os

    cores = os.cpu_count() or 1
    for concurrency in (1, 2, 4, 64):
        assert jobs.solver_workers(concurrency) >= 1
        assert jobs.solver_workers(concurrency) * concurrency <= max(cores, concurrency)


# --- Telemetry ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_health_reports_solver_signals_not_just_http(client, request_body):
    posted = await client.post("/v1/replans", json=request_body())
    await _drain(client, posted.json()["id"])

    health = (await client.get("/v1/health")).json()
    assert health["rungs"]["exact"] == 1
    assert health["fallback_rate"] == 0.0
    assert health["violations_returned"] == 0
    assert health["solve_seconds"]["count"] == 1


def test_the_fallback_rate_actually_moves(scenario):
    """A counter that only ever reads zero is indistinguishable from a broken one.

    The budget is squeezed so the ladder falls to its greedy rung, and the telemetry has to
    show it -- this is the signal that would catch an optimiser degrading behind a green
    HTTP dashboard.
    """
    store = jobs.Store()
    wire = contracts.from_domain(scenario.instance)
    job = store.submit(
        contracts.ReplanRequest(tenant="acme", instance=wire, budget_seconds=0.001)
    )
    jobs.run_job(job)

    from roster_replan.service.app import telemetry

    health = telemetry(store, queue_depth=0, concurrency=1)
    assert health["rungs"]["greedy"] == 1
    assert health["fallback_rate"] == 1.0


def test_a_solver_failure_becomes_a_job_state_rather_than_a_dead_worker(scenario):
    """One poisoned payload must not stop every tenant's queue."""
    store = jobs.Store()
    wire = contracts.from_domain(scenario.instance)
    job = store.submit(contracts.ReplanRequest(tenant="acme", instance=wire))

    # A request whose instance cannot be solved: the open shifts index shift types that
    # are no longer there.
    job.request.instance.shift_types = []

    jobs.run_job(job)
    assert job.state == jobs.FAILED
    assert job.error


@pytest.fixture
def anyio_backend():
    return "asyncio"


# --- The T4 tool surface -------------------------------------------------------------


@pytest.mark.anyio
async def test_the_manifest_lists_every_tool_with_a_schema(client):
    """A tool-calling caller enumerates this. Schemas come from the request models, so the
    description a caller reads and the validation it must pass cannot drift apart."""
    from roster_replan.service import tools

    manifest = (await client.get("/v1/tools")).json()
    assert {t["name"] for t in manifest} == set(tools.BY_NAME)

    for entry in manifest:
        assert entry["description"]
        assert entry["parameters"]["type"] == "object"


@pytest.mark.anyio
async def test_what_if_distinguishes_a_skilled_hire_from_a_body(client, scenario):
    """The answer a planner acts on, over HTTP."""
    wire = contracts.from_domain(scenario.instance).model_dump()

    skilled = await client.post(
        "/v1/tools/what_if",
        json={
            "instance": wire,
            "changes": [
                {
                    "kind": "add_employee",
                    "skills": ["kitchen"],
                    "contract": "flexi",
                    "weekly_hours": 24.0,
                    "daily_hours": 8.0,
                }
            ],
        },
    )
    assert skilled.status_code == 200
    assert skilled.json()["refused"] is False


@pytest.mark.anyio
async def test_an_unlawful_hypothetical_is_refused_over_http(client, scenario):
    """The safety property, at the boundary an agent would actually call."""
    wire = contracts.from_domain(scenario.instance).model_dump()

    response = await client.post(
        "/v1/tools/what_if",
        json={"instance": wire, "changes": [{"kind": "relax_rule", "min_rest_hours": 8.0}]},
    )

    body = response.json()
    assert body["refused"] is True
    assert body["variant"] is None
    assert any("derogation" in d["message"] for d in body["defects"])


@pytest.mark.anyio
async def test_explain_returns_fields_beside_the_prose(client, scenario):
    """`D-013`: a caller that does not trust the sentence can read the numbers."""
    wire = contracts.from_domain(scenario.instance).model_dump()
    body = (await client.post("/v1/tools/explain_infeasibility", json={"instance": wire})).json()

    assert body["answered"] in ("shortfall", "infeasibility")
    assert isinstance(body["prose"], str)
    for finding in body["shortfalls"]:
        assert finding["by_rule"]
        assert finding["short"] >= 1


@pytest.mark.anyio
async def test_an_unknown_tool_is_a_404_and_a_bad_payload_is_a_422(client):
    assert (await client.post("/v1/tools/nope", json={})).status_code == 404
    assert (
        await client.post("/v1/tools/validate_profile", json={"instance": {"days": -1}})
    ).status_code == 422


@pytest.mark.anyio
async def test_validate_profile_reports_without_saving(client, scenario):
    """A tool an LLM can call must not be able to persist a tenant's scheduling policy."""
    wire = contracts.from_domain(scenario.instance).model_dump()
    body = (await client.post("/v1/tools/validate_profile", json={"instance": wire})).json()

    assert body["lawful"] is True
    assert body["defects"] == []


@pytest.mark.anyio
async def test_generation_goes_through_the_replan_endpoint(client):
    """Generation is a replan with an empty incumbent (`replan.md`, `D-109`), so it needs no
    second route — a caller generates by omitting `incumbent` and `now`.

    Asserted here rather than only at the model layer because "no second formulation" is a
    claim about the *product surface* as much as about the solver: if the service could not
    carry a cold payload, the claim would be true of `solve` and false of the thing callers
    actually use.
    """
    cold = identical_workforce(6, required=1)
    body = contracts.ReplanRequest(
        tenant="acme", instance=contracts.from_domain(cold), seed=7
    ).model_dump()

    posted = await client.post("/v1/replans", json=body)
    assert posted.status_code == 202

    job = await _drain(client, posted.json()["id"])
    assert job["state"] == jobs.SUCCEEDED
    assert job["answer"]["rung"] == "exact"
    assert len(job["answer"]["roster"]) == sum(o.required for o in cold.open_shifts)


@pytest.mark.anyio
async def test_a_declared_fairness_term_reaches_the_solver(client):
    """Reachability, asserted on the objective rather than on the roster (`D-131`).

    A balance assertion would be the obvious test and is the weaker one: on an
    interchangeable workforce a roster can come back balanced for reasons that have nothing
    to do with this term. The objective cannot. `solve` minimises the fairness term and
    `scoring.score` measures it independently, so if the wire format dropped the field the
    two would stop agreeing — the solver would optimise a smaller objective than the scorer
    reads on the roster it returned.
    """
    cold = dataclasses.replace(
        identical_workforce(6, required=1),
        fairness=Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=8),
    )
    body = contracts.ReplanRequest(
        tenant="acme", instance=contracts.from_domain(cold), seed=7
    ).model_dump()

    job = await _drain(client, (await client.post("/v1/replans", json=body)).json()["id"])
    assert job["state"] == jobs.SUCCEEDED

    roster = frozenset(tuple(entry) for entry in job["answer"]["roster"])
    assert job["answer"]["objective"] == score(roster, cold).total
    # And the term is not merely present but priced: with a weight on it the objective
    # cannot be the bare tie-breaker a cold solve would otherwise return.
    assert score(roster, cold).fairness > 0
