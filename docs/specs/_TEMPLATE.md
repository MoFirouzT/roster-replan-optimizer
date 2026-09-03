# &lt;Title&gt;

**Status:** Draft | Approved | Implemented &lt;YYYY-MM-DD&gt;
**Depends on:** &lt;the components this one needs first, by spec filename, or none&gt;

&lt;For a spec written after the code, add one line here saying so and naming what it was
built from. A reconstruction is a useful document and a dishonest one if it presents
itself as a work order that was reviewed before implementation.&gt;

## Objective

&lt;One sentence: what capability this component delivers.&gt;

## Motivation

&lt;Optional. Include it when the component is not obviously needed, or when it closes
something an earlier one left open. State the question, not the solution.&gt;

## Canonical reference

&lt;Which sections of which canonical document this implements, and where they are:
`guide/rules.md` and its three companions for the predicates, `internals/model.md` for
the formulation, `guide/api.md` for the contract. Or "none, no new predicate and no new
formulation".

The canonical document owns the statement. This spec cites it and never restates it: a
predicate written in two places is two documents to keep true, and `grep`ping a
parameter name across the repository is how the shared-parameter review in `D-039` is
actually done.&gt;

## Governing reference

&lt;Optional. The statute, the CBA article, or the published source this component's
authority rests on. A rule with no source has none, and saying that plainly beats
inventing one: two searches in the rule registry found no rule at all, and those entries
lost their legality claim rather than keeping an unsourced one. Never cite from memory:
check the instrument and the article first.&gt;

## Parameters and configuration

&lt;The concrete values this component introduces and where they are set: the profile, the
payload, a constant in the module. Name each one exactly as the code spells it.&gt;

## Interfaces

&lt;Function signatures, request and response schema, payload fields. Whatever applies;
omit the section if the component adds none.&gt;

## Layering

&lt;Optional. Which `[tool.importlinter]` contracts this component touches, and what they
forbid. The enforced copy in `pyproject.toml` is the only one that cannot rot, so cite
it by contract name rather than restating the layer order.&gt;

## Build tasks

- [ ] &lt;task&gt;

## Test contract

&lt;Which layer proves which claim, named so a reader can run it:

- the **unit and golden** cases, by test file
- the **differential harness**, when the claim is that the checker and the model agree,
  and what it cannot see here
- the **brute force** stage, when the instance is small enough to enumerate
- the **property** invariants
- the **mutant** that must fail, and the layer named to catch it

`internals/testing.md` describes the layers. A layer that has never been shown to fail
is not known to work, so a new layer arrives with its mutant.&gt;

## Acceptance gate

*Blocks:* &lt;what may not start until this is green, or "nothing"&gt;.

- [ ] &lt;condition, with the measured value beside it once it is run&gt;

Record a box only against evidence. `- [x]` ran and passed, `- [!]` ran and did not,
with the result written on the line, `- [ ]` no record either way. A spec whose
**Status** is `Implemented` may carry no `- [ ]`, and `scripts/lint_docs.py` enforces
that: "we meant to tick it" and "it passed" are indistinguishable six weeks later.

## Measured results

&lt;Optional. What the component actually found, when the finding is the deliverable. This
is the builder's record; the reader-facing write-up is a study in `docs/studies/`, and a
measurement is kept even when the thing it measured has been deleted.&gt;

## Out of scope

- &lt;item. This section is binding.&gt;

## Decisions

&lt;Component-local decisions about formulation, interface and build. Roadmap and
positioning questions stay in the gitignored `planning/`, never here.

Pose each with a proposed answer, then resolve it in place at review, keeping the
proposal so the section becomes the decision trail rather than a list of questions
answered somewhere else. This is where a later reader is sent for *why*, so it is the
one section that is not trimmed on the way to green.

Promote a decision to a record in `decisions.md` only when it is cross-cutting and
expensive to reverse, and leave the `D-nnn` pointer here.&gt;

1. &lt;question&gt; *Proposed:* &lt;recommendation&gt;.
2. &lt;question&gt; **Resolved:** &lt;decision and reason&gt; (YYYY-MM-DD).

---

*The ledger: [`README.md`](README.md). The reasoning behind the shape of this file:
[`documentation.md`](documentation.md#specs-for-the-built-components).*
