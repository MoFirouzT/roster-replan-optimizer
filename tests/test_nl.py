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
from roster_replan.domain import Fairness, shipped_d2
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
    return suite.build("headline/3").instance


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


def test_a_silence_is_not_reported_as_unclear():
    """`D-103`, measured: the old wording invited an assumptions log, so a profile that
    parsed perfectly came back with caveats about what the text did not say.

    Asserted against the prompt and the schema rather than against a parse, because the only
    thing that can quietly undo it is someone rewriting either one — and the eval that would
    notice costs money and is not in this suite.
    """
    assert "do not also describe" in nl.SYSTEM
    described = nl.StatedPolicy.model_fields["unclear"].description
    assert "not an assumptions log" in described.casefold()
    assert "silence" in described.casefold()


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
        # Policy no parse may set and none may delete either (`D-131`). A model must not
        # infer which shifts nobody wants, and a silence about them is not a withdrawal.
        fairness=Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=4),
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
    assert candidate.fairness == strict.fairness


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


# --- The renderer, and the half of the round trip that needs no API -------------------


@pytest.fixture
def distinctive(base):
    """A profile whose every figure is unique and unlike the shipped defaults.

    Both properties are load-bearing. Unique, so a rendered figure cannot be satisfied by
    some other number that happens to appear; unlike the defaults, so a value the renderer
    drops does not come home anyway on the fallback path.
    """
    return dataclasses.replace(
        base,
        params=dataclasses.replace(
            base.params,
            min_rest_hours=13.0,
            min_weekly_rest_hours=41.0,
            min_period_hours=6.0,
            max_consecutive_days=5,
            derogation_basis={"min_rest_hours": "CAO 302 article 12"},
        ),
        disruption=dataclasses.replace(
            base.disruption, notice_bands=(nl.NoticeBand(18.0, 9), nl.NoticeBand(float("inf"), 1))
        ),
    )


def test_the_rendering_states_every_figure_the_schema_can_carry(distinctive):
    """The coverage claim `config.md` says the round trip is worth — asserted here without
    an API, so the live eval only has to add *can the model read it back*."""
    text = nl.describe(distinctive)

    for figure in ("13", "41", "6", "5", "18", "9"):
        assert figure in text, f"{figure} is in the profile and not in the rendering"
    assert "CAO 302 article 12" in text


def test_the_rendering_omits_a_rule_the_profile_does_not_set(distinctive):
    """A silence has to render as a silence. A renderer that writes 'nobody works more than
    None days' teaches the parse to read a rule out of a profile that has none."""
    without = dataclasses.replace(
        distinctive, params=dataclasses.replace(distinctive.params, max_consecutive_days=None)
    )
    assert "days in a row" not in nl.describe(without)
    assert "None" not in nl.describe(without)


def test_the_rendering_puts_shift_starts_on_a_clock(distinctive):
    assert "07:00" in nl.describe(distinctive) or "15:00" in nl.describe(distinctive)


def test_a_rendering_survives_its_own_parse(distinctive):
    """The round trip with the model taken out: what `describe` says is fed back as the
    payload a perfect parse would have produced, and the profile must come home unchanged.

    This is a tautology twice over and still worth running — it is the only test that
    exercises `describe → StatedPolicy → to_profile` as one path, which is where a field
    renders correctly, parses correctly, and is then dropped on the way into the profile.
    """
    stated = nl.StatedPolicy(
        shift_types=[
            nl.ShiftTypeIn(
                label=s.label,
                start_hour=s.start_hour,
                span_hours=s.span_hours,
                break_hours=s.break_hours,
            )
            for s in distinctive.shift_types
        ],
        min_rest_hours=13.0,
        min_weekly_rest_hours=41.0,
        min_period_hours=6.0,
        max_consecutive_days=5,
        derogations=[nl.DerogationIn(parameter="min_rest_hours", basis="CAO 302 article 12")],
        short_notice_hours=18.0,
        short_notice_multiplier=9,
    )
    back = nl.to_profile(stated, version=distinctive.version)

    assert back == distinctive


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


# --- The eval harness ------------------------------------------------------------------
# `benchmarks/nl_eval.py` costs API calls, so it is a script and runs deliberately. Its
# *scoring* is deterministic and is tested here: an eval that cannot fail measures nothing,
# and this one is only ever read when it disagrees with a model.


def test_the_env_file_is_read(tmp_path):
    from benchmarks import nl_eval

    path = tmp_path / ".env"
    path.write_text("ANTHROPIC_API_KEY=sk-ant-not-a-real-key\n")
    environ: dict[str, str] = {}

    assert nl_eval.load_env(path, environ) == {"ANTHROPIC_API_KEY": "sk-ant-not-a-real-key"}
    assert environ["ANTHROPIC_API_KEY"] == "sk-ant-not-a-real-key"


def test_a_real_environment_variable_wins_over_the_file(tmp_path):
    """A file in the working directory must never quietly replace an exported key: that is
    how the wrong account gets billed, and how a key you rotated keeps being used."""
    from benchmarks import nl_eval

    path = tmp_path / ".env"
    path.write_text("ANTHROPIC_API_KEY=from-the-file\n")
    environ = {"ANTHROPIC_API_KEY": "from-the-shell"}

    assert nl_eval.load_env(path, environ) == {}
    assert environ["ANTHROPIC_API_KEY"] == "from-the-shell"


def test_the_shipped_placeholder_does_not_count_as_a_key(tmp_path):
    """`.env.example` ships `ANTHROPIC_API_KEY=` with nothing after it. Reading that as a
    value turns a clear 'no key' message into a 401 from the API."""
    from benchmarks import nl_eval

    path = tmp_path / ".env"
    path.write_text("# a comment\n\nANTHROPIC_API_KEY=\n")
    environ: dict[str, str] = {}

    assert nl_eval.load_env(path, environ) == {}
    assert environ == {}


def test_the_loader_survives_the_shapes_people_write(tmp_path):
    from benchmarks import nl_eval

    path = tmp_path / ".env"
    path.write_text(
        "# comment\n"
        "\n"
        "export ANTHROPIC_API_KEY=exported\n"
        'ANTHROPIC_MODEL="claude-opus-5"\n'
        "QUOTED='single'\n"
        "NOT_A_PAIR\n"
    )
    environ: dict[str, str] = {}
    loaded = nl_eval.load_env(path, environ)

    assert loaded == {
        "ANTHROPIC_API_KEY": "exported",
        "ANTHROPIC_MODEL": "claude-opus-5",
        "QUOTED": "single",
    }


def test_a_missing_env_file_is_not_an_error(tmp_path):
    from benchmarks import nl_eval

    assert nl_eval.load_env(tmp_path / "nothing-here", {}) == {}


def test_the_eval_scores_a_perfect_parse_clean():
    from benchmarks import nl_eval

    case = nl_eval.Case("x", "...", nl.StatedPolicy(min_rest_hours=11.0), why="")
    assert nl_eval._diff(case, nl.StatedPolicy(min_rest_hours=11.0)) == []


def test_the_eval_reports_an_invented_field_as_invented():
    """The assertion the whole free-form half exists for. A parse that supplies a weekly
    rest nobody mentioned has invented a rule, and 'missed' would be the wrong word for it:
    one is a parse that read carelessly, the other is a policy the tenant never agreed to."""
    from benchmarks import nl_eval

    case = nl_eval.Case("x", "...", nl.StatedPolicy(min_rest_hours=11.0), why="")
    diffs = nl_eval._diff(case, nl.StatedPolicy(min_rest_hours=11.0, min_weekly_rest_hours=35.0))

    assert diffs == ["invented min_weekly_rest_hours: 35.0"]


def test_the_eval_reports_a_missed_field_as_missed():
    from benchmarks import nl_eval

    case = nl_eval.Case("x", "...", nl.StatedPolicy(max_consecutive_days=6), why="")
    (diff,) = nl_eval._diff(case, nl.StatedPolicy())

    assert diff.startswith("missed max_consecutive_days")


def test_the_eval_scores_the_unsayable_as_present_or_absent():
    """`unclear` is the model's own wording, so it cannot be compared for equality — but a
    case that asks for something the schema cannot hold must still fail when nothing is
    reported, or the confinement cases would all pass vacuously."""
    from benchmarks import nl_eval

    asked = nl_eval.Case("x", "...", nl.StatedPolicy(unclear=["..."]), why="")
    assert nl_eval._diff(asked, nl.StatedPolicy()) == [
        "nothing reported as unclear, but the text asked for something unsayable"
    ]
    assert nl_eval._diff(asked, nl.StatedPolicy(unclear=["weights are not mine to set"])) == []


def test_the_round_trip_reports_a_field_that_did_not_survive():
    """The round trip has to be able to fail. A stub that answers every rendering with the
    same empty payload stands in for a parse that read nothing."""
    from benchmarks import nl_eval

    results = nl_eval.round_trip(StubClient(nl.StatedPolicy()))

    assert results, "no profiles were round-tripped"
    assert all(not ok for _, ok, _ in results)
    assert any("params.min_rest_hours" in line for _, _, diffs in results for line in diffs)


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
