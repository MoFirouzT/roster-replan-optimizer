# Natural language to profile

**Status:** Implemented 2026-08-14
**Reconstructed 2026-09-02** from [`nl.py`](../../roster_replan/nl.py),
[`benchmarks/nl_eval.py`](../../benchmarks/nl_eval.py),
[`guide/configuring.md`](../guide/configuring.md),
[`studies/nl-parse.md`](../studies/nl-parse.md), the mutant catalogue, and the commits of
2026-08-14, and **it is not the work order this component was built from**: this project had
none ([`documentation.md`](documentation.md#specs-for-the-built-components)).
**Depends on:** [`tools.md`](tools.md), whose deterministic review this accelerates.

## Objective

Turn a policy written in plain English into a candidate tenant profile, where what the
model may say is bounded by a schema rather than by a prompt, and where the deterministic
review that follows is the thing that decides.

## Motivation

Configuring a tenant means setting rule parameters, and a planner describing their own
policy in a sentence is faster and less error-prone than filling a form. That is worth
having, and it is also the point in this system where a language model is closest to the
rules.

So the design question is not *how good is the parse*. It is *what is the model
structurally unable to do*, and the answer has to survive the model being asked something
unexpected.

## Canonical reference

[`guide/configuring.md`](../guide/configuring.md) owns the four stages, what `StatedPolicy`
carries, what *unset* means, and how to run the parse.

## Governing reference

None. The confinement is a local design choice rather than a published method.

## Parameters and configuration

An optional dependency and a key:

```bash
uv sync --extra nl
```

Everything else works without it. The client is injected, so the module imports and tests
with no API key. Model, prompt version and the parsed payload are carried on every
proposal so a config change can be audited; storing them is the caller's job, as accepting
a candidate is.

## Interfaces

```text
nl.parse(text, client)         English -> StatedPolicy, the one call a model makes
nl.to_profile(stated, base)    StatedPolicy -> Profile, silence carried forward
nl.describe(profile)           Profile -> canonical English, the other half of the round trip
nl.propose(text, base_profile) all four stages, ending in a verdict rather than a save
```

`describe` exists so the mapping can be checked in both directions. What that check is
worth is stated rather than assumed: it is **a tautology by construction, proving coverage
and not comprehension**, because the same author wrote both halves
([`nl-parse.md`](../studies/nl-parse.md)). It still catches a field one side forgot.

**Nothing is saved.** `propose` returns a candidate; accepting it is the caller's act.

`StatedPolicy` carries only what a tenant would actually say: a rest gap, a shortest
shift, how much worse a change at short notice is. It has **no field** for
`shortfall_weight` and none for `enabled_optional_rules`. *Unset* means the text did not
say so, which is not the same claim as a default: a silence carries the base profile's
value forward and never invents a rule.

## Layering

*The natural-language layer is an accelerator: nothing deterministic reaches it.* No
deterministic module may import `roster_replan.nl` or `anthropic`.

That contract is the whole safety argument. Deterministic profile editing works fully with
no model, so the model is never a dependency of anything that has to be right.

## Build tasks

- [x] Define `StatedPolicy` as the confinement, omitting every field a tenant would not
      state.
- [x] Carry silence forward from the base profile rather than defaulting.
- [x] Run stages 2 to 4 on every candidate, deterministically.
- [x] Render a profile back to canonical English, so the mapping is checkable both ways.
- [x] Commit eighteen cases, each with the policy it must produce, including Dutch and
      adversarial ones.
- [x] Score what was invented, not only what was found.

## Test contract

| Claim | Layer |
| --- | --- |
| Derogations are a closed schema, not an open mapping | `test_nl.py::nl-derogations-as-an-open-mapping` |
| A derogation parameter is not free text | `nl-derogation-parameter-is-free-text` |
| Silence does not overwrite the base profile | `nl-silence-overwrites-the-base-profile` |
| Silence does not delete a fairness declaration | `nl-silence-deletes-the-fairness-declaration` |
| A candidate with defects is not accepted | `nl-accepts-a-candidate-with-defects` |
| Rendering drops no rule | `nl-rendering-drops-a-rule` |
| The eval fails an invented rule | `nl-eval-passes-an-invented-rule` |
| The eval's environment cannot be overridden by a file | `nl-eval-env-file-overrides-the-shell` |

Eight mutants, and half of them are about **silence and invention** rather than about
extraction, which is where the risk actually is.

## Acceptance gate

*Blocks:* nothing. This is the accelerator.

- [x] **18 of 18, repeated three times**, after 16 of 18 on the first run
      ([`nl-parse.md`](../studies/nl-parse.md)). The extraction itself was right in every
      case on the first run, including both Dutch and both adversarial ones. Both
      first-run failures were in the `unclear` field, and only one was the parse's fault.
- [x] The module imports and tests with no API key.
- [x] No deterministic module can reach the model, enforced by contract.
- [!] **[`D-101`](../decisions.md#d-101)'s derogation field compiled to an object that
      could hold nothing.** The schema was specified, encoded and tested, and the wire
      contract had no counterpart, so the field was reachable only from Python
      ([`D-131`](../decisions.md#d-131)). The round-trip test could not see it, because it
      runs over committed cases and no case sets the field: **an instance distribution
      that does not contain a field cannot test whether the boundary carries it.**
- [!] **The same defect then repeated seven rules later**
      ([`D-138`](../decisions.md#d-138)). What caught the repeat was the mutation harness
      refusing to start on stale anchors. **A recorded lesson is not a control**, and the
      general fix, a test walking every `domain` field and asserting a wire counterpart,
      is named rather than made.

## Measured results

**The parse is measured on two halves, reported separately because they are worth
different things** ([`D-102`](../decisions.md#d-102)). Getting the stated fields right is
the easy half. The half that matters is leaving alone the fields the text says nothing
about, and the eval scores **what was invented**, not only what was found.

Eighteen calls per run, about $0.35, model `claude-opus-5` at low effort, prompt
`nl-2026.1` on the first run and `nl-2026.2` after.

**`unclear` is for what could not be said, not for what was assumed**
([`D-103`](../decisions.md#d-103)). Both first-run failures were there, which is the field
where the distinction is hardest to hold.

## Out of scope

- **Letting the model set a weight.** `StatedPolicy` has no field for `shortfall_weight`.
  A rule the model cannot state is a rule it cannot break.
- **Letting the model enable an optional rule.** No field for it, and profile review would
  reject one anyway ([`D-099`](../decisions.md#d-099)).
- **Saving anything.** `propose` returns a candidate and the verdict on it.
- **Confining by prompt.** A prompt is a request; a schema is a boundary.
- **A free-form derogation mapping.** An open mapping is not a schema
  ([`D-101`](../decisions.md#d-101)).
- **Making the parse a dependency of deterministic editing.** It is an accelerator, and
  the import contract keeps it one.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **What confines the model, the prompt or the schema?** The schema
   ([`D-101`](../decisions.md#d-101)). A prompt asks; a type refuses.

2. **Does the eval score only extraction?** No, invention too
   ([`D-102`](../decisions.md#d-102)). A parse that fills in a plausible rest gap nobody
   mentioned is the failure worth catching, and an extraction-only score rewards it.

3. **What does silence mean?** The base profile's value carries forward. Not a default,
   and never a new rule. That is the amendment case and it is the common one.

4. **What is `unclear` for?** What could not be said
   ([`D-103`](../decisions.md#d-103)). Using it for what was assumed makes it a place to
   hide a guess.

5. **Is the parse built before deterministic review?** No
   ([`D-099`](../decisions.md#d-099)). An accelerator built first has nothing to fall back
   to.

---

*The ledger: [`README.md`](README.md). The stages:
[`guide/configuring.md`](../guide/configuring.md). How it was measured:
[`studies/nl-parse.md`](../studies/nl-parse.md).*
