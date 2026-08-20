"""The five tools of the service surface, as one registry with schemas a caller can enumerate.

They are `solve`, `replan`, `explain_infeasibility`, `what_if`,
`validate_profile`. Four are thin over machinery that already exists, and that is the point
rather than a shortcut — a tool surface whose tools each contain original logic is a second
implementation of the product with its own bugs.

## What makes this a tool surface and not five more endpoints

**Every tool returns structured fields *and*, where there is prose, the prose beside them**
(`D-013`). A caller that does not trust the sentence can read the numbers, and a caller that
cannot parse the numbers can read the sentence. Returning only prose would make the model's
phrasing load-bearing; returning only fields would make every consumer write its own.

**Schemas are generated from the Pydantic models**, so the description a caller sees and the
validation a request meets are the same object. A hand-written schema drifts from the handler
it describes, and the drift is invisible until a call fails.

**Nothing here decides anything.** No tool ranks options, recommends a hire, or picks a
roster among alternatives. `what_if` reports that a skilled hire fills a position and an
unskilled one does not; whether to hire is not a question this project has any standing to
answer, and a tool that answered it would be laundering a business decision through a solver.

## Read-only, and deliberately

None of the five writes. `validate_profile` checks and reports; it does not save. `config.md`
describes a profile being probed for feasibility *before* it is saved, and the save is the
caller's — a tool an LLM can call should not be able to persist a tenant's scheduling policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, Field

from ..core import minimal_core
from ..explain import explain
from ..ladder import answer as ladder_answer
from ..prose import render_all
from ..profile import Profile, review
from ..validation import validate_instance
from ..whatif import KINDS, Change, compare
from . import contracts
from .contracts import InstanceIn, Strict

SOLVE = "solve"
REPLAN = "replan"
EXPLAIN_INFEASIBILITY = "explain_infeasibility"
WHAT_IF = "what_if"
VALIDATE_PROFILE = "validate_profile"


# --- Request shapes -----------------------------------------------------------------


class SolveIn(Strict):
    """A cold solve. Generation is the replan case with an empty incumbent (`replan.md`),
    so this differs from `replan` only in what the caller supplies, not in what runs."""

    instance: InstanceIn
    seed: int = 7
    budget_seconds: float = Field(default=30.0, gt=0, le=300)


class ReplanIn(SolveIn):
    """Identical in shape. Named separately because a caller choosing a tool is choosing a
    question, and *repair what is published* is a different question from *build a week*."""


class ExplainIn(Strict):
    instance: InstanceIn
    seed: int = 7
    budget_seconds: float = Field(default=30.0, gt=0, le=300)
    weekday_of_day_zero: int | None = Field(default=None, ge=0, le=6)


class ChangeIn(Strict):
    kind: str = Field(description=f"one of {', '.join(KINDS)}")
    employee: int | None = None
    skills: list[str] = Field(default_factory=list)
    contract: str = "salaried"
    weekly_hours: float | None = None
    daily_hours: float | None = None
    day: int | None = None
    shift: int | None = None
    required: int | None = None
    min_rest_hours: float | None = None
    max_consecutive_days: int | None = None
    derogation_basis: dict[str, str] = Field(default_factory=dict)


class WhatIfIn(Strict):
    instance: InstanceIn
    changes: list[ChangeIn] = Field(min_length=1)
    seed: int = 7
    budget_seconds: float = Field(default=30.0, gt=0, le=300)


class ValidateIn(Strict):
    instance: InstanceIn
    profile_version: str = "unversioned"
    enabled_optional_rules: list[str] = Field(default_factory=list)
    probe: bool = Field(
        default=True,
        description="solve the supplied week under the profile before accepting it",
    )


# --- Handlers -----------------------------------------------------------------------


def _solve(payload: SolveIn) -> dict:
    instance = contracts.to_domain(payload.instance)
    answer = ladder_answer(
        instance, seed=payload.seed, budget_seconds=payload.budget_seconds
    )
    return contracts.answer_out(answer, instance).model_dump()


def _explain(payload: ExplainIn) -> dict:
    """The structured finding and the sentence, together.

    `D-047` re-scoped this tool before it was written: with a soft coverage floor a cold
    solve is essentially never infeasible, so its ordinary answer is *why a shift is short*.
    The name is `PLAN.md`'s and is kept, but the response says plainly which question it
    answered — a tool called `explain_infeasibility` that silently explains something else
    would be worse than one with an awkward name.
    """
    instance = contracts.to_domain(payload.instance)
    answer = ladder_answer(
        instance, seed=payload.seed, budget_seconds=payload.budget_seconds
    )
    findings = explain(answer.roster, instance)

    # The core reported is the **minimal** one, not the sufficient set the ladder carries.
    # `D-100`: asked with the objective set, CP-SAT returns 150-plus gates naming eight
    # rules where two are doing the work, and a planner handed that has no way to tell
    # which. Recomputed only when there is an infeasibility to explain.
    reduction = minimal_core(instance, seed=payload.seed) if answer.core else None

    return {
        "answered": "shortfall" if not answer.core else "infeasibility",
        "rung": answer.rung,
        "reason": answer.reason,
        "core": [
            {"rule": g.rule, "employee": g.employee, "day": g.day, "shift": g.shift}
            for g in (reduction.minimal if reduction else ())
        ],
        "core_reduced_from": len(reduction.sufficient) if reduction else 0,
        "shortfalls": [
            {
                "day": f.day,
                "shift": f.shift,
                "required": f.required,
                "assigned": f.assigned,
                "short": f.short,
                "by_rule": f.by_rule(),
                "unexplained": list(f.unexplained),
            }
            for f in findings
        ],
        "prose": render_all(
            findings, instance, weekday_of_day_zero=payload.weekday_of_day_zero
        ),
    }


def _what_if(payload: WhatIfIn) -> dict:
    instance = contracts.to_domain(payload.instance)
    changes = tuple(
        Change(
            kind=c.kind,
            employee=c.employee,
            skills=tuple(c.skills),
            contract=c.contract,
            weekly_hours=c.weekly_hours,
            daily_hours=c.daily_hours,
            day=c.day,
            shift=c.shift,
            required=c.required,
            min_rest_hours=c.min_rest_hours,
            max_consecutive_days=c.max_consecutive_days,
            derogation_basis=tuple(c.derogation_basis.items()),
        )
        for c in payload.changes
    )

    result = compare(
        instance, changes, seed=payload.seed, time_limit=payload.budget_seconds
    )
    return {
        "described": list(result.described),
        "refused": result.refused,
        "defects": [
            {"field": d.field, "message": d.message} for d in result.defects
        ],
        "baseline": _side(result.baseline),
        "variant": None if result.variant is None else _side(result.variant),
        "shortfall_delta": result.shortfall_delta,
        "disruption_delta": result.disruption_delta,
        "summary": result.summary(),
    }


def _side(outcome) -> dict:
    return {
        "shortfall": outcome.shortfall,
        "disruption": outcome.disruption,
        "changes_from_incumbent": outcome.changes_from_incumbent,
    }


def _validate(payload: ValidateIn) -> dict:
    """Stages 2 to 4 of `config.md`, and never stage 1.

    Structural lawfulness, then the profile's own contradictions and inert rules, then a
    probe if a sample week was supplied. All deterministic: *"deterministic profile editing
    works fully with no LLM; the NL layer is an accelerator, never a dependency."*

    Checks and reports. **Does not save** -- see the module docstring.
    """
    instance = contracts.to_domain(payload.instance)
    defects = validate_instance(instance)

    candidate = Profile(
        version=payload.profile_version,
        shift_types=instance.shift_types,
        params=instance.params,
        disruption=instance.disruption,
        enabled_optional_rules=frozenset(payload.enabled_optional_rules),
    )
    conflicts, notes, result = review(candidate, instance if payload.probe else None)

    return {
        "lawful": not defects and not conflicts,
        "defects": [
            {
                "field": d.field,
                "message": d.message,
                "observed": repr(d.observed),
                "required": repr(d.required),
            }
            for d in list(defects) + list(conflicts)
        ],
        "remarks": [{"field": n.field, "message": n.message} for n in notes],
        "probe": (
            None
            if result is None
            else {
                "solved": result.solved,
                "shortfall": result.shortfall,
                "blocking": list(result.blocking),
            }
        ),
    }


# --- The registry -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    request: type[BaseModel]
    handler: Callable[[Any], dict]

    def schema(self) -> dict:
        return self.request.model_json_schema()


TOOLS: tuple[Tool, ...] = (
    Tool(
        name=SOLVE,
        description=(
            "Build a roster for a week with no published incumbent. Generation is the "
            "cold-start case of replanning, not a separate mode."
        ),
        request=SolveIn,
        handler=_solve,
    ),
    Tool(
        name=REPLAN,
        description=(
            "Repair a published roster around a disruption, minimising weighted deviation "
            "from what people were already told."
        ),
        request=ReplanIn,
        handler=_solve,
    ),
    Tool(
        name=EXPLAIN_INFEASIBILITY,
        description=(
            "Explain why shifts are unstaffed, naming the rule that blocked each person. "
            "Returns structured findings and prose. True infeasibility is rare because the "
            "coverage floor is soft; the usual answer is a priced shortfall."
        ),
        request=ExplainIn,
        handler=_explain,
    ),
    Tool(
        name=WHAT_IF,
        description=(
            "Re-solve under a hypothetical change — a hire, an hours change, a demand "
            "change, a rule derogation — and report the difference. Unlawful hypotheticals "
            "are refused rather than answered."
        ),
        request=WhatIfIn,
        handler=_what_if,
    ),
    Tool(
        name=VALIDATE_PROFILE,
        description=(
            "Check a profile: structural lawfulness, contradictions between its own rules, "
            "rules that cannot bind, and a feasibility probe on the supplied week. Fully "
            "deterministic. Reports defects and remarks; does not save anything."
        ),
        request=ValidateIn,
        handler=_validate,
    ),
)

BY_NAME = {tool.name: tool for tool in TOOLS}


def manifest() -> list[dict]:
    """What a tool-calling caller enumerates. Schemas come from the models themselves, so
    the description and the validation cannot drift apart."""
    return [
        {"name": t.name, "description": t.description, "parameters": t.schema()}
        for t in TOOLS
    ]


def call(name: str, payload: dict) -> dict:
    """Dispatch by name, validating the payload against the tool's own schema."""
    tool = BY_NAME.get(name)
    if tool is None:
        raise KeyError(f"unknown tool {name!r}; expected one of {sorted(BY_NAME)}")
    return tool.handler(tool.request.model_validate(payload))
