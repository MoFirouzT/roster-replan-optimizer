"""Stage 1 of `config.md`: the parse, and the things that must be true around it.

The layer under test is the one place a language model is allowed to touch, so what is
tested is mostly **confinement** rather than parsing. Three claims carry it:

**The schema is the constraint, and the schema is what the API compiles.** A field that
looks right in Python can compile to a field the model cannot write to, and no stub-driven
test of the surrounding logic would ever notice — the stub returns whatever the test asks
it to. `test_every_field_can_actually_carry_a_value` reads the compiled schema instead, and
is the test that found `D-101`.

**Silence is not a default.** An unset field means *the text did not say*, which carries
the previous value forward. A parse that overwrites an existing profile with shipped
defaults is the quiet way a tenant loses a policy they still hold.

**Nothing a model says is saved.** `propose` ends in a verdict. The deterministic layers
decide, and the only test that matters here is that a rejected candidate stays rejected.

Every test runs with a stub client and no API key, which is the same property `config.md`
demands of the product: the NL layer is an accelerator, never a dependency.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import suite
from roster_replan import nl
from roster_replan.domain import shipped_d2
from roster_replan.profile import Profile


class StubClient:
    """The API surface `parse` uses, and nothing else.

    Records the call so the request can be asserted on: the model, the effort and the
    schema handed over are part of the contract with the API, not incidental.
    """

    def __init__(self, parsed: nl.StatedPolicy):
        self._parsed = parsed
        self.calls: list[dict] = []
        self.messages = self

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"parsed_output": self._parsed})()


@pytest.fixture(scope="module")
def sample():
    return suite.build("headline/0").instance


@pytest.fixture
def base(sample):
    return Profile(
        version="horeca-2026.1",
        shift_types=sample.shift_types,
        params=sample.params,
        disruption=sample.disruption,
    )


# --- The compiled schema ------------------------------------------------------------


def _compiled_schema():
    """The schema the API is actually given, not the one pydantic prints.

    `messages.parse` runs the model's JSON schema through the SDK's transform before
    sending it, and the transform is where an unsupported construct becomes a silently
    unusable field. Asserting on the untransformed schema would miss exactly that.
    """
    pytest.importorskip("anthropic", reason="the parse is an optional extra: uv sync --extra nl")

    # Skipping is only correct for the *extra being absent*. The transform lives on a private
    # path, so if the SDK moves it this must fail rather than skip: a skipped schema test is
    # exactly the silence `D-101` slipped through, arriving a second time as a dependency bump.
    from anthropic.lib._parse._transform import transform_schema
    from pydantic import TypeAdapter

    return transform_schema(TypeAdapter(nl.StatedPolicy).json_schema())


def test_every_field_can_actually_carry_a_value():
    """A field the model cannot write to is worse than a missing field: the prompt asks for
    it, the schema forbids it, and the silence reads as *the text did not say*.

    An open mapping is the way this happens. `dict[str, str]` compiles to an object with no
    properties and `additionalProperties: false` — structurally empty (`D-101`).
    """
    schema = _compiled_schema()
    dead = [
        name
        for name, spec in schema["properties"].items()
        if spec.get("type") == "object"
        and not spec.get("properties")
        and spec.get("additionalProperties") is False
    ]
    assert not dead, f"fields the model can never fill: {dead}"


def test_the_schema_gives_no_way_to_write_a_weight():
    """`D-057`'s domination bound holds because `shortfall_weight` is derived, never stated.
    A model cannot propose an unsafe scale if the schema gives it nowhere to write one."""
    stated = set(_compiled_schema()["properties"])
    assert not stated & {
        "shortfall_weight",
        "concentration_tiers",
        "peak_weight",
        "cost_weight",
        "enabled_optional_rules",
    }


def test_a_derogation_names_a_parameter_validation_will_look_up():
    """The basis is looked up by parameter name, so free text would validate as no basis at
    all — a lawful policy reported as unlawful, with the tenant's own citation on file."""
    parameter = _compiled_schema()["$defs"]["DerogationIn"]["properties"]["parameter"]
    assert set(parameter["enum"]) == {
        "min_rest_hours",
        "min_weekly_rest_hours",
        "min_period_hours",
    }


# --- The call ------------------------------------------------------------------------


def test_parse_asks_for_the_schema_at_low_effort():
    client = StubClient(nl.StatedPolicy())
    nl.parse("nobody works more than six days running", client)

    (call,) = client.calls
    assert call["model"] == nl.MODEL
    assert call["output_format"] is nl.StatedPolicy
    assert call["output_config"] == {"effort": "low"}
    assert call["messages"] == [
        {"role": "user", "content": "nobody works more than six days running"}
    ]


def test_the_prompt_forbids_supplying_defaults():
    """The instruction is load-bearing: an industry default supplied for a silence is a rule
    the tenant never agreed to, and it arrives looking exactly like one they did."""
    assert "Do not supply industry defaults" in nl.SYSTEM


# --- Silence, and what it inherits ---------------------------------------------------


def test_silence_carries_the_previous_policy_forward(base):
    """The amendment case. A tenant changing one rule has not withdrawn the others.

    Every inherited figure here is deliberately *not* the shipped default. A base that
    already agrees with the defaults cannot tell inheritance from falling back to them, and
    the difference is the whole claim: falling back silently replaces a policy the tenant
    still holds with one they never wrote.
    """
    strict = dataclasses.replace(
        base,
        params=dataclasses.replace(
            base.params,
            min_rest_hours=13.0,
            min_weekly_rest_hours=40.0,
            min_period_hours=4.0,
            max_consecutive_days=5,
        ),
    )
    candidate = nl.to_profile(
        nl.StatedPolicy(max_consecutive_days=4), version="horeca-2026.2", base=strict
    )

    assert candidate.params.max_consecutive_days == 4, "the one thing the text stated"
    assert candidate.params.min_rest_hours == 13.0
    assert candidate.params.min_weekly_rest_hours == 40.0
    assert candidate.params.min_period_hours == 4.0
    assert candidate.shift_types == base.shift_types
    assert candidate.disruption == base.disruption


def test_silence_with_no_base_takes_the_statutory_figures():
    candidate = nl.to_profile(nl.StatedPolicy(), version="new-tenant")
    assert candidate.params.min_rest_hours == 11.0
    assert candidate.params.min_weekly_rest_hours == 35.0


def test_a_stated_shift_catalogue_replaces_the_old_one(base):
    stated = nl.StatedPolicy(
        shift_types=[nl.ShiftTypeIn(label="Late", start_hour=15.5, span_hours=8.0, break_hours=0.5)]
    )
    candidate = nl.to_profile(stated, version="v2", base=base)

    (shift,) = candidate.shift_types
    assert (shift.label, shift.start_hour, shift.span_hours) == ("Late", 15.5, 8.0)


def test_the_weights_the_model_never_sees_come_from_the_shipped_objective():
    candidate = nl.to_profile(nl.StatedPolicy(), version="new-tenant")
    assert candidate.disruption.shortfall_weight == shipped_d2().shortfall_weight


def test_a_stated_notice_rule_becomes_notice_bands(base):
    stated = nl.StatedPolicy(short_notice_hours=12.0, short_notice_multiplier=3)
    candidate = nl.to_profile(stated, version="v2", base=base)

    assert candidate.disruption.notice_bands[0].within_hours == 12.0
    assert candidate.disruption.notice_bands[0].multiplier == 3


def test_notice_bands_are_untouched_when_notice_is_not_mentioned(base):
    candidate = nl.to_profile(nl.StatedPolicy(), version="v2", base=base)
    assert candidate.disruption.notice_bands == base.disruption.notice_bands


def test_a_parse_can_never_enable_an_unencoded_rule(base):
    """The five optional rules are declared and not encoded (`D-099`). A model that could
    turn one on by describing it would promise enforcement that does not happen."""
    enabled = dataclasses.replace(base, enabled_optional_rules=frozenset({"R-SUNDAY"}))

    assert nl.to_profile(nl.StatedPolicy(), version="v2").enabled_optional_rules == frozenset()
    assert nl.to_profile(
        nl.StatedPolicy(), version="v2", base=enabled
    ).enabled_optional_rules == frozenset({"R-SUNDAY"}), "a parse neither adds nor drops them"


# --- Derogations ---------------------------------------------------------------------


def test_a_stated_derogation_satisfies_the_lawfulness_check(base, sample):
    """End to end, and the reason the parameter name is an enum: a shorter rest gap with a
    recorded basis is lawful, and the basis only counts if `validation.py` can find it."""
    stated = nl.StatedPolicy(
        min_rest_hours=9.0,
        derogations=[nl.DerogationIn(parameter="min_rest_hours", basis="CBA 2026/14 art. 7")],
    )
    proposal = nl.propose(
        "nine hours between shifts under CBA 2026/14 art. 7",
        StubClient(stated),
        version="v2",
        sample=sample,
        base=base,
    )

    assert proposal.candidate.params.min_rest_hours == 9.0
    assert proposal.probe is not None
    assert proposal.probe.defects == (), [d.message for d in proposal.probe.defects]


def test_a_shorter_period_with_no_basis_is_refused(base, sample):
    """The prompt says report what the text says and let validation reject it. This is the
    rejection, and it must come from the deterministic layer rather than from the prompt."""
    proposal = nl.propose(
        "nine hours between shifts",
        StubClient(nl.StatedPolicy(min_rest_hours=9.0)),
        version="v2",
        sample=sample,
        base=base,
    )

    assert not proposal.acceptable
    assert any("derogation" in d.message for d in proposal.probe.defects)


# --- The verdict ---------------------------------------------------------------------


def test_a_contradictory_candidate_is_rejected_and_never_probed(base, sample):
    stated = nl.StatedPolicy(min_period_hours=12.0)
    proposal = nl.propose(
        "no shift shorter than twelve hours", StubClient(stated), version="v2",
        sample=sample, base=base,
    )

    assert not proposal.acceptable
    assert proposal.probe is None
    assert proposal.summary().startswith("Rejected")


def test_a_workable_policy_is_accepted_as_a_candidate(base, sample):
    proposal = nl.propose(
        "nobody works more than four days running",
        StubClient(nl.StatedPolicy(max_consecutive_days=4)),
        version="v2",
        sample=sample,
        base=base,
    )

    assert proposal.acceptable
    assert proposal.summary().startswith("Accepted as candidate")


def test_a_shortfall_on_the_sample_week_does_not_reject_the_policy(base, sample):
    """The headline week is a sick call, so the probe finds a shortfall. Refusing on that
    would reject a correct configuration for a shape a real tenant has."""
    proposal = nl.propose(
        "nothing changes", StubClient(nl.StatedPolicy()), version="v2", sample=sample, base=base
    )

    assert proposal.probe.shortfall > 0
    assert proposal.acceptable


def test_what_the_model_could_not_express_is_reported(base):
    stated = nl.StatedPolicy(unclear=["students may not close on school nights"])
    proposal = nl.propose("...", StubClient(stated), version="v2", base=base)

    assert "students may not close" in proposal.summary()


def test_a_proposal_carries_what_produced_it(base):
    """`config.md` wants the model and prompt version to travel with a config change, for the
    reason a solve carries its seed: an output nobody can reproduce cannot be argued with."""
    proposal = nl.propose("...", StubClient(nl.StatedPolicy()), version="v2", base=base)

    assert proposal.model == nl.MODEL
    assert proposal.prompt_version == nl.PROMPT_VERSION


def test_a_proposal_saves_nothing(base):
    """`config.md`: accepting is the caller's. The check is that the base is untouched --
    a model-driven path must not be able to persist a tenant's policy."""
    before = dataclasses.asdict(base)
    nl.propose(
        "eight days running is fine",
        StubClient(nl.StatedPolicy(max_consecutive_days=8)),
        version="v2",
        base=base,
    )

    assert dataclasses.asdict(base) == before
