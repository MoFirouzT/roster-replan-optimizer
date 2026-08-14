"""Stage 1 of `config.md`: a policy described in English, turned into a candidate profile.

The only part of this project that needs a language model, and the last piece of T4. Every
stage downstream of it — structural validation, contradiction and subsumption checks, the
feasibility probe — is deterministic and already built (`D-099`), so this module produces a
candidate and hands it straight to machinery that can refuse it.

    uv sync --extra nl     # the SDK is an optional dependency, never a runtime one

## The model is confined, and the confinement is structural

`D-012` requires the model produce only artifacts a deterministic layer can reject. Three
things enforce that here rather than asking for it.

**The schema is narrow and human-shaped.** `StatedPolicy` below carries only what a tenant
would actually *say* — "eleven hours between shifts", "nobody works more than six days
running", "a change inside a day is four times worse". It does **not** carry
`shortfall_weight`, `concentration_tiers`, or `peak_weight`: those are derived, and
`shortfall_weight` in particular is bound by the domination proof in `D-057`. A model cannot
propose an unsafe weight scale because the schema gives it nowhere to write one.

**Structured outputs, not free-form JSON.** The response is constrained to the schema by the
API, so a malformed parse is a validation error rather than a plausible-looking profile.
The constraint is real rather than advisory, and that cuts both ways: a field the schema
cannot express is a field the model **cannot** report, however clearly the text states it
(`D-101`). Every field here is therefore checked against the schema the API compiles, not
against the Python type that looks right.

**Nothing is saved.** `propose` returns a candidate and its review. Accepting it is the
caller's, exactly as `config.md` requires — a model-driven path must not be able to persist a
tenant's scheduling policy.

## Why this works without a key

`parse` takes an injected client. The tests drive it with a stub, so the whole pipeline —
schema, conversion, review, rejection — is exercised with no API access at all. That is the
same property `config.md` demands of the product: *deterministic profile editing works fully
with no LLM; the NL layer is an accelerator, never a dependency.*
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal

from pydantic import BaseModel, Field

from .domain import NoticeBand, RuleParams, ShiftType, shipped_d2
from .profile import Profile, Remark, review
from .validation import InputDefect

MODEL = "claude-opus-5"

# Bumped whenever SYSTEM or the schema changes. `config.md` requires the model and prompt
# version to travel with a config change, for the same reason a solve carries its seed and
# profile version: an output nobody can reproduce cannot be argued with later.
PROMPT_VERSION = "nl-2026.2"

SYSTEM = """\
You convert a scheduling policy written in plain language into a structured profile.

Extract only what the text states or clearly implies. Do not supply industry defaults for
anything the text is silent about — leave those fields unset. A tenant who does not mention
weekly rest has not agreed to a weekly rest rule, and inventing one imposes a constraint
nobody asked for. Leaving a field unset is how you report a silence; do not also describe
the silence in `unclear`.

Belgian labour law sets statutory minima (11 hours between shifts, 35 hours of weekly rest).
A policy may state a shorter period only under a recorded derogation; if the text mentions
one, record it in `derogations` with the source verbatim. Do not soften a stated figure to make
it lawful — report what the text says and let validation reject it.\
"""


# The three parameters `validation.py` will ask for a basis for. Naming them as an enum
# rather than taking free text is what makes a reported derogation *land*: the basis is
# looked up by parameter name, so "rest between shifts" would validate as no basis at all.
DEROGABLE = Literal["min_rest_hours", "min_weekly_rest_hours", "min_period_hours"]


class DerogationIn(BaseModel):
    """One lawful relaxation of a statutory parameter, with the authority for it.

    A list of pairs rather than a mapping, because a mapping cannot be expressed: an open
    `dict[str, str]` compiles to an object with no properties and `additionalProperties`
    forbidden — a field that can never hold anything (`D-101`).
    """

    parameter: DEROGABLE = Field(description="The parameter the tenant is going below")
    basis: str = Field(
        description="The authority cited for it — a CBA, a royal decree — verbatim from the text"
    )


class ShiftTypeIn(BaseModel):
    """One shift in the tenant's catalogue."""

    label: str = Field(description="The tenant's own name for the shift, e.g. 'Morning', 'M', 'Late'")
    start_hour: float = Field(ge=0, lt=24, description="Start time as hours past midnight; 15:30 is 15.5")
    span_hours: float = Field(gt=0, description="Total clock time from start to end, breaks included")
    break_hours: float = Field(ge=0, description="Unpaid break within the span. 0 if not stated")


class StatedPolicy(BaseModel):
    """What a tenant said, and nothing else.

    Every rule field is optional. An unset field means *the text did not say*, which is a
    different claim from a default — and the distinction is load-bearing: `domain.py` rejects
    a missing threshold rather than defaulting it, precisely so a silence cannot become a
    silent rule.
    """

    shift_types: list[ShiftTypeIn] = Field(
        default_factory=list, description="Every shift the policy describes"
    )

    min_rest_hours: float | None = Field(
        default=None, description="Minimum hours between the end of one shift and the start of the next"
    )
    min_weekly_rest_hours: float | None = Field(
        default=None, description="Minimum unbroken rest period per week"
    )
    min_period_hours: float | None = Field(
        default=None, description="Shortest shift the tenant will roster"
    )
    max_consecutive_days: int | None = Field(
        default=None, description="Most days in a row anyone may work"
    )
    derogations: list[DerogationIn] = Field(
        default_factory=list,
        description=(
            "Only when the text cites authority for going below a statutory minimum. Leave "
            "empty otherwise — a shorter period with no authority is reported as stated and "
            "rejected downstream, not quietly justified here"
        ),
    )

    short_notice_hours: float | None = Field(
        default=None,
        description="The notice threshold below which a change counts as short notice, if stated",
    )
    short_notice_multiplier: int | None = Field(
        default=None,
        description="How many times worse a short-notice change is than one with full notice, if stated",
    )

    unclear: list[str] = Field(
        default_factory=list,
        description=(
            "Only what this schema cannot express, or what the text leaves genuinely "
            "unresolved. Not an assumptions log: if you resolved a phrase to a figure and "
            "filled the field, it does not belong here. Nor is a silence unclear — an "
            "unset field already reports that the text did not mention it"
        ),
    )


def parse(text: str, client: Any, *, model: str = MODEL) -> StatedPolicy:
    """English to a candidate policy, via structured outputs.

    `client` is injected rather than constructed here. That keeps the module importable and
    testable with no API key, and it keeps credential handling at the edge where the caller
    already has it.

    Effort is `low` deliberately: this is a short extraction over a short document, and the
    schema does the constraining. Thinking is left on — disabling it on this model has
    documented failure modes and buys little on a task this size.
    """
    response = client.messages.parse(
        model=model,
        max_tokens=4096,
        system=SYSTEM,
        output_config={"effort": "low"},
        output_format=StatedPolicy,
        messages=[{"role": "user", "content": text}],
    )
    return response.parsed_output


def to_profile(stated: StatedPolicy, *, version: str, base: Profile | None = None) -> Profile:
    """A candidate profile from what the tenant said, with the rest inherited.

    Unset fields fall back to `base` when one is supplied — the amendment case, where a
    tenant is changing part of an existing policy — and otherwise to the shipped defaults.
    **Silence never invents a rule**: it carries the previous value forward, which is what a
    tenant editing a policy means by not mentioning something.

    The objective weights the model never sees are taken whole from `shipped_d2()`, so
    `shortfall_weight` keeps the value `D-057`'s domination bound requires and
    `validation.py` re-checks anyway.
    """
    fallback_params = base.params if base else RuleParams(
        min_rest_hours=11.0,
        min_weekly_rest_hours=35.0,
        min_period_hours=3.0,
        max_consecutive_days=6,
    )
    fallback_shifts = base.shift_types if base else ()
    disruption = base.disruption if base else shipped_d2()

    params = RuleParams(
        min_rest_hours=_or(stated.min_rest_hours, fallback_params.min_rest_hours),
        min_weekly_rest_hours=_or(
            stated.min_weekly_rest_hours, fallback_params.min_weekly_rest_hours
        ),
        min_period_hours=_or(stated.min_period_hours, fallback_params.min_period_hours),
        max_consecutive_days=_or(
            stated.max_consecutive_days, fallback_params.max_consecutive_days
        ),
        derogation_basis=dict(fallback_params.derogation_basis)
        | {d.parameter: d.basis for d in stated.derogations},
    )

    if stated.short_notice_hours is not None or stated.short_notice_multiplier is not None:
        within = _or(stated.short_notice_hours, 24.0)
        multiplier = _or(stated.short_notice_multiplier, 4)
        disruption = replace(
            disruption,
            notice_bands=(NoticeBand(within, multiplier), NoticeBand(float("inf"), 1)),
        )

    shifts = tuple(
        ShiftType(
            label=s.label,
            start_hour=s.start_hour,
            span_hours=s.span_hours,
            break_hours=s.break_hours,
        )
        for s in stated.shift_types
    )

    return Profile(
        version=version,
        shift_types=shifts or fallback_shifts,
        params=params,
        disruption=disruption,
        # Never set from a parse. The five optional rules are declared and unencoded, so
        # enabling one promises enforcement that does not happen (`D-099`) -- a model must
        # not be able to turn one on by describing it.
        enabled_optional_rules=base.enabled_optional_rules if base else frozenset(),
    )


def _or(value, fallback):
    return fallback if value is None else value


def describe(profile: Profile) -> str:
    """A profile in canonical English — the other half of `config.md`'s round trip.

    Deliberately flat and repetitive. This is not the prose a tenant should read; it is the
    text `parse` is asked to read back, and a sentence written to sound natural is a
    sentence that makes a failed round trip ambiguous between the renderer and the parse.

    **What the round trip proves is coverage, not comprehension** — author and reader are
    the same person here, which is why `config.md` calls it close to a tautology. What it
    does catch is a field this renderer forgets: the value silently falls back on the way
    home, and the profiles it is run against disagree with the shipped defaults precisely so
    that fallback is visible.
    """
    params = profile.params
    lines = []

    if profile.shift_types:
        shifts = "; ".join(
            f"{s.label} starts at {_clock(s.start_hour)} and lasts {s.span_hours:g} hours"
            + (f", including {s.break_hours * 60:g} minutes of unpaid break" if s.break_hours else "")
            for s in profile.shift_types
        )
        lines.append(f"The shifts we run are: {shifts}.")

    lines.append(
        f"There must be at least {params.min_rest_hours:g} hours between the end of one "
        f"shift and the start of the next."
    )
    lines.append(
        f"Everyone must get at least {params.min_weekly_rest_hours:g} hours of unbroken "
        f"rest each week."
    )
    lines.append(f"We never roster a shift shorter than {params.min_period_hours:g} hours.")
    if params.max_consecutive_days is not None:
        lines.append(f"Nobody works more than {params.max_consecutive_days} days in a row.")

    for name, basis in sorted(params.derogation_basis.items()):
        lines.append(f"Our figure for {name} is permitted under {basis}.")

    bands = profile.disruption.notice_bands
    if bands:
        lines.append(
            f"Changing a shift less than {bands[0].within_hours:g} hours beforehand is "
            f"{bands[0].multiplier} times as bad as changing it with more notice."
        )

    return "\n".join(lines)


def _clock(hours: float) -> str:
    """Local rather than borrowed from `prose.py`, where it is private.

    Three lines of formatting duplicated is not the sharing the independence rule is about
    — that rule is about thresholds, where a shared constant hides a disagreement.
    """
    minutes = int(round(hours * 60)) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class Proposal:
    """A candidate profile, the deterministic verdict on it, and where it came from.

    Nothing is saved. `model` and `prompt_version` travel with the proposal because
    `config.md` requires them to accompany a config change, and this layer is not the one
    that stores things — the caller that accepts a candidate is.

    `stated` is the response. Structured outputs mean the model's output *is* the schema
    instance, so there is no separate raw text that could disagree with it.
    """

    def __init__(
        self,
        stated: StatedPolicy,
        candidate: Profile,
        defects: list[InputDefect],
        remarks: list[Remark],
        probe=None,
        *,
        model: str = MODEL,
        prompt_version: str = PROMPT_VERSION,
    ):
        self.stated = stated
        self.candidate = candidate
        self.defects = defects
        self.remarks = remarks
        self.probe = probe
        self.model = model
        self.prompt_version = prompt_version

    @property
    def acceptable(self) -> bool:
        """No contradictions, and the probe (if run) found a legal roster.

        Deliberately not "the probe was fully staffed": a policy that leaves a shift short on
        the sample week may be exactly the policy the tenant has (`scarce-skill` is a real
        tenant shape), and refusing it would reject a correct configuration.
        """
        if self.defects:
            return False
        return self.probe is None or self.probe.solved

    def summary(self) -> str:
        if self.defects:
            reasons = "; ".join(d.message for d in self.defects)
            return f"Rejected: {reasons}"
        notes = f" ({len(self.remarks)} remark(s))" if self.remarks else ""
        unclear = (
            f" Unclear: {'; '.join(self.stated.unclear)}" if self.stated.unclear else ""
        )
        return f"Accepted as candidate{notes}.{unclear}"


def propose(
    text: str,
    client: Any,
    *,
    version: str,
    sample=None,
    base: Profile | None = None,
    model: str = MODEL,
) -> Proposal:
    """All four stages of `config.md`, in order, ending in a verdict rather than a save."""
    stated = parse(text, client, model=model)
    candidate = to_profile(stated, version=version, base=base)
    defects, remarks, probe = review(candidate, sample)
    return Proposal(stated, candidate, defects, remarks, probe, model=model)
