"""The tenant profile, and the two checks that reject a bad one before it is saved.

`config.md` gives four stages, and confines the LLM to the first: parse, validate
structurally, validate semantically, probe feasibility. Stages 2 to 4 are deterministic, so
they are built first and work with no model available — *"deterministic profile editing
works fully with no LLM; the NL layer is an accelerator, never a dependency."*

This module is stages 3 and 4. Stage 2 already exists as `validation.validate_instance`,
which answers *is this payload lawful*; this answers a different question, and the difference
is worth stating because they are easy to merge and should not be.

## Contradiction is not the same as infeasibility

`validate_instance` looks at one request. A **contradiction** is a property of the profile
alone: `min_period_hours` above `max_daily_hours` means no shift of any length is legal for
anyone, whatever week you hand it. That is knowable without a solver, without a workforce,
and without a single open shift — and it is the error worth catching, because it will
otherwise surface as a mystifying empty roster at 09:00 on a Saturday.

**Subsumption is the quieter failure.** A rule that can never bind is not wrong, it is inert:
`max_consecutive_days` of 9 over a seven-day horizon forbids nothing. Nothing breaks, and the
tenant believes a protection is in force that is not. So it is reported — as a remark rather
than a defect, because the profile is still valid and the caller may have meant it.

## The probe needs a week, and it is the caller's week

Stage 4 solves a sample week under the candidate profile. The sample is supplied rather than
generated here: a synthetic week would probe a workforce the tenant does not have, and this
module has no business inventing one. It also keeps the core free of `benchmarks`, which is
not a runtime dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .domain import Disruption, Instance, RuleParams, ShiftType
from .explain import explain
from .model import solve
from .validation import InputDefect, validate_instance

# The rules `rules.md` marks optional. A tenant that does not enable one never pays for it,
# which is the whole reason the profile carries them as data rather than the model carrying
# them as code.
OPTIONAL_RULES = (
    "R-STUDENT-QUOTA",
    "R-SUNDAY",
    "R-BREAK",
    "R-PT-MIN",
    "R-PUB-NOTICE",
)


@dataclass(frozen=True, slots=True)
class Profile:
    """What "optimal" means for one tenant, as a document.

    `version` is carried so a solve can record which profile produced it, which is what
    `PLAN.md`'s replay requirement needs: an input, a seed and a profile version.
    """

    version: str
    shift_types: tuple[ShiftType, ...]
    params: RuleParams
    disruption: Disruption
    enabled_optional_rules: frozenset[str] = field(default_factory=frozenset)

    def applied_to(self, instance: Instance) -> Instance:
        """The instance as this profile would have it solved."""
        return replace(
            instance,
            shift_types=self.shift_types,
            params=self.params,
            disruption=self.disruption,
        )


@dataclass(frozen=True, slots=True)
class Remark:
    """A rule that is valid but does nothing. Not a defect -- the caller may have meant it."""

    field: str
    message: str


# --- Stage 3: contradiction ---------------------------------------------------------


def contradictions(profile: Profile) -> list[InputDefect]:
    """Rules that cannot all hold, knowable from the profile alone.

    Every check here is a statement about the *parameters*, not about any week. That is what
    makes it worth running at configuration time: a contradiction found here is one that
    would otherwise appear as an unexplained empty roster on a Saturday morning.
    """
    found: list[InputDefect] = []
    params = profile.params
    horizon_hours = 7 * 24.0

    shortest = min((s.span_hours for s in profile.shift_types), default=0.0)
    longest = max((s.span_hours for s in profile.shift_types), default=0.0)
    longest_work = max((s.work_hours for s in profile.shift_types), default=0.0)

    if params.min_period_hours > longest and profile.shift_types:
        found.append(
            InputDefect(
                field="params.min_period_hours",
                message=(
                    f"a shift must last at least {params.min_period_hours:g}h, but the "
                    f"longest shift in the catalogue is {longest:g}h — no shift is legal"
                ),
                observed=params.min_period_hours,
                required=f"<= {longest:g}",
            )
        )

    if params.min_weekly_rest_hours >= horizon_hours:
        found.append(
            InputDefect(
                field="params.min_weekly_rest_hours",
                message=(
                    f"weekly rest of {params.min_weekly_rest_hours:g}h needs a gap at least "
                    f"as long as the {horizon_hours:g}h horizon — nobody can ever work"
                ),
                observed=params.min_weekly_rest_hours,
                required=f"< {horizon_hours:g}",
            )
        )

    # A rest gap at or beyond a full day makes consecutive working days impossible, so a
    # `max_consecutive_days` above 1 describes a pattern the rest gap forbids.
    if params.min_rest_hours >= 24.0 and (params.max_consecutive_days or 0) > 1:
        found.append(
            InputDefect(
                field="params.min_rest_hours",
                message=(
                    f"a rest gap of {params.min_rest_hours:g}h prevents working two days "
                    f"running, but max_consecutive_days is "
                    f"{params.max_consecutive_days} — the two cannot both be intended"
                ),
                observed=params.min_rest_hours,
                required="< 24 if consecutive days are allowed",
            )
        )

    if params.max_consecutive_days is not None and params.max_consecutive_days < 1:
        found.append(
            InputDefect(
                field="params.max_consecutive_days",
                message="max_consecutive_days below 1 forbids working at all",
                observed=params.max_consecutive_days,
                required=">= 1",
            )
        )

    if profile.shift_types and params.min_rest_hours + longest > 2 * 24.0:
        found.append(
            InputDefect(
                field="params.min_rest_hours",
                message=(
                    f"a {longest:g}h shift followed by {params.min_rest_hours:g}h of rest "
                    f"spans more than two days, so no employee can work twice in a week "
                    f"without breaching one of them"
                ),
                observed=params.min_rest_hours,
                required=f"<= {2 * 24.0 - longest:g}",
            )
        )

    unknown = profile.enabled_optional_rules - set(OPTIONAL_RULES)
    if unknown:
        found.append(
            InputDefect(
                field="enabled_optional_rules",
                message=(
                    f"unknown optional rules {sorted(unknown)}; the profile-gated rules are "
                    f"{list(OPTIONAL_RULES)}"
                ),
                observed=sorted(unknown),
                required=list(OPTIONAL_RULES),
            )
        )

    # Every optional rule is declared in the registry and none is encoded yet, so enabling
    # one promises enforcement that does not exist. Silently accepting it is the failure
    # `rules.md` warns about: a registry that describes intent rather than code.
    unenforced = profile.enabled_optional_rules & set(OPTIONAL_RULES)
    if unenforced:
        found.append(
            InputDefect(
                field="enabled_optional_rules",
                message=(
                    f"{sorted(unenforced)} are declared in the registry but not encoded in "
                    f"the model, so enabling them would promise enforcement that does not "
                    f"happen"
                ),
                observed=sorted(unenforced),
                required="none, until they are encoded",
            )
        )

    # Only when *some* shift is legal. If none is, the defect above already says so, and
    # reporting both gives two messages for one problem — the second reads as an additional
    # fault and sends the reader looking for a second fix.
    if shortest and longest >= params.min_period_hours > shortest:
        found.append(
            InputDefect(
                field="params.min_period_hours",
                message=(
                    f"the shortest shift in the catalogue is {shortest:g}h, below the "
                    f"{params.min_period_hours:g}h minimum shift length — that shift can "
                    f"never be staffed"
                ),
                observed=shortest,
                required=f">= {params.min_period_hours:g}",
            )
        )

    return found


# --- Stage 3b: subsumption ----------------------------------------------------------


def remarks(profile: Profile, *, days: int = 7) -> list[Remark]:
    """Rules that are valid and cannot bind. Reported, not rejected.

    The tenant believes a protection is in force. It is not, and nothing will ever fail to
    tell them so — which is exactly why it is worth saying at configuration time.
    """
    found: list[Remark] = []
    params = profile.params

    if params.max_consecutive_days is not None and params.max_consecutive_days >= days:
        found.append(
            Remark(
                field="params.max_consecutive_days",
                message=(
                    f"max_consecutive_days of {params.max_consecutive_days} cannot bind over "
                    f"a {days}-day horizon, so it forbids nothing"
                ),
            )
        )

    longest = max((s.span_hours for s in profile.shift_types), default=0.0)
    if longest and params.min_rest_hours <= 24.0 - longest:
        found.append(
            Remark(
                field="params.min_rest_hours",
                message=(
                    f"a rest gap of {params.min_rest_hours:g}h is shorter than the "
                    f"{24.0 - longest:g}h that separates two same-time shifts on "
                    f"consecutive days, so it never binds on a daily pattern"
                ),
            )
        )

    if profile.disruption.cost_weight == 0:
        found.append(
            Remark(
                field="disruption.cost_weight",
                message=(
                    "cost_weight is 0, so cost is switched off entirely and the objective is "
                    "pure disruption"
                ),
            )
        )

    if profile.disruption.metric in ("D0", "D1"):
        found.append(
            Remark(
                field="disruption.metric",
                message=(
                    f"{profile.disruption.metric} ignores notice, so a change tonight is "
                    f"priced the same as one next month"
                ),
            )
        )

    return found


# --- Stage 4: feasibility probe -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class Probe:
    """What a sample week did under a candidate profile."""

    solved: bool
    shortfall: int
    blocking: tuple[str, ...]
    defects: tuple[InputDefect, ...] = ()

    @property
    def clean(self) -> bool:
        return self.solved and not self.shortfall and not self.defects


def probe(profile: Profile, sample: Instance, *, seed: int = 7, time_limit: float = 30.0) -> Probe:
    """Solve a sample week under the candidate profile, and report what blocked it.

    Rejection returns through the explainer, as `config.md` asks: the same machinery a
    planner sees at 09:00 is the machinery a config error is caught by, so the two cannot
    drift into describing the rules differently.
    """
    instance = profile.applied_to(sample)

    defects = validate_instance(instance)
    if defects:
        return Probe(solved=False, shortfall=0, blocking=(), defects=tuple(defects))

    outcome = solve(instance, seed=seed, time_limit=time_limit)
    roster = getattr(outcome, "roster", None)
    if roster is None:
        return Probe(solved=False, shortfall=0, blocking=("no roster could be found",))

    findings = explain(roster, instance)
    blocking = tuple(
        rule for finding in findings for rule in finding.by_rule()
    )
    return Probe(
        solved=True,
        shortfall=sum(f.short for f in findings),
        blocking=tuple(sorted(set(blocking))),
    )


def review(
    profile: Profile, sample: Instance | None = None, *, seed: int = 7
) -> tuple[list[InputDefect], list[Remark], Probe | None]:
    """Stages 3 and 4 together: contradictions, remarks, and a probe if a sample is given.

    The probe is skipped when the profile already contradicts itself. Solving an instance
    built from parameters that cannot all hold would produce an infeasibility whose
    explanation is *the profile*, reported as though it were about the week.
    """
    defects = contradictions(profile)
    notes = remarks(profile)
    if defects or sample is None:
        return defects, notes, None
    return defects, notes, probe(profile, sample, seed=seed)
