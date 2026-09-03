# The tool surface, hypotheticals, and profile review

**Status:** Implemented 2026-08-20
**Reconstructed 2026-09-02** from
[`service/tools.py`](../../roster_replan/service/tools.py),
[`whatif.py`](../../roster_replan/whatif.py),
[`profile.py`](../../roster_replan/profile.py), [`guide/api.md`](../guide/api.md),
[`guide/configuring.md`](../guide/configuring.md), the mutant catalogue, and the commits of
2026-08-13 to 2026-08-20, and **it is not the work order this component was built from**:
this project had none
([`documentation.md`](documentation.md#specs-for-the-built-components)).
**Depends on:** [`service.md`](service.md) and [`explanation.md`](explanation.md).

## Objective

Five read-only tools a planner or a model can call, a hypothetical that refuses unlawful
questions rather than answering them, and a deterministic review of a tenant profile that
runs with no solver and no language model.

## Motivation

The dangerous output of this project is not a wrong roster. It is a specific, actionable,
illegal suggestion: *hire nobody, just shorten the rest gap*. A hypothetical tool is
exactly where that gets produced innocently, because the machinery is perfectly capable of
solving an instance whose parameters break the law.

Profile review has the same shape from the other side. A tenant who switches on a rule the
model does not encode holds a profile stating that Sunday work is restricted while the
solver restricts nothing, and **no test anywhere fails**.

## Canonical reference

[`guide/api.md`](../guide/api.md) owns the five tools, their three shared properties, and
the recommendation surface. [`guide/configuring.md`](../guide/configuring.md) owns the
profile and its four stages.

## Governing reference

None of its own. The lawfulness the tools enforce comes from
[`rules.md`](rules.md).

## Parameters and configuration

`MAX_CANDIDATES` is five by default. Uncapped, the recommendation sweep is a solve per
blocked person for a list nobody reads far into.

## Interfaces

`solve`, `replan`, `explain_infeasibility`, `what_if`, `validate_profile`: enumerable at
`GET /v1/tools`, invoked at `POST /v1/tools/{name}`.

```text
whatif.compare(instance, changes)   a typed, closed change set, never a free-form patch
whatif.recommend(...)               -> tuple[Recommendation, ...]
profile.review(profile)             -> defects and remarks, deterministic, no solver
```

Each `Recommendation` carries the employee, the action in planner language, the
`disruption_delta` it was measured at, the `rule` it would relax, and that rule's
`provenance`.

Three properties hold across all five tools: structured fields **and** prose together;
nothing decides anything; all five are read-only.

## Layering

The service may not import the language-model layer, so nothing here can reach one.
`recommend` is a library function rather than a sixth tool, on purpose: **a ranked list of
ways to override labour rules, handed to a model, reads as an instruction however it is
grouped.**

## Build tasks

- [x] Five read-only tools with schemas, listed at one route and called at another.
- [x] A closed, typed change set for `what_if`, never a patch endpoint over `Instance`.
- [x] Validate a hypothetical before solving it, and return the refusal as the answer.
- [x] Build profile review stages 2 to 4 with no model available: structural lawfulness,
      contradiction and subsumption, feasibility probe.
- [x] Reject a profile that enables one of the five declared but unencoded rules.
- [x] Carry provenance on every recommendation and sort within it, never across it.

## Test contract

| Claim | Layer |
| --- | --- |
| An unlawful hypothetical is refused | `test_whatif.py::whatif-answers-unlawful-hypotheticals` |
| The baseline is one solve, not one per candidate | `recommend-resolves-the-baseline-per-candidate` |
| The candidate cap holds | `recommend-ignores-the-candidate-cap` |
| Provenance groups the list; it is not one ranking | `recommend-ranks-statutory-against-operational` |
| A hypothetical hire lands with the skill it was given | `whatif-hire-lands-without-the-skill` |
| An unencoded optional rule is a defect, not a warning | `test_profile.py::profile-accepts-unencoded-optional-rules` |
| A contradictory profile is not probed | `profile-probes-a-contradictory-profile-anyway` |
| An inert rule is a remark, not a defect | `profile-inert-rule-reported-as-a-defect` |
| Priors past the tiers are noticed | `profile-misses-priors-past-the-tiers` |
| The remark text is what review actually returns | `test_specs.py::profile-remark-text-reworded` |

## Acceptance gate

*Blocks:* nothing downstream.

- [x] `what_if` refuses an unlawful variant and returns the defects as the answer, with no
      roster ([`D-098`](../decisions.md#d-098)).
- [x] The same relaxation **is** answered when a derogation basis is supplied. The rule is
      *recorded basis*, not *never*: a derogation is lawful and a planner exploring one is
      the case the tool exists to serve.
- [x] Profile review runs with no model and no language model available.
- [x] A profile enabling an unencoded rule is rejected rather than accepted as a forward
      declaration of intent ([`D-099`](../decisions.md#d-099)).
- [!] **The shipped recommendation list was a flat cheapest-first ranking, and its own demo
      output showed why that is wrong**: a statutory relaxation on the top line, tied on
      points with two operational ones ([`D-144`](../decisions.md#d-144)). Nothing unlawful
      ever reached the list; the defect was presenting lawful-but-different asks as
      comparable.
- [!] **The sweep was paying for the baseline twice.** It does not depend on which
      override is tested, and `compare` re-solved it per candidate: 2N solves where N+1
      does. Five candidates fell from 78 ms to 49 ms.

## Measured results

**Disruption cannot order two asks of different kinds.** Ignoring a skill requirement is a
judgement the planner already owns; asking somebody to work further into a budget a
statute caps is a different question at any price. A single sorted list says otherwise by
its shape, because the top line reads as the recommendation. **Lawful is not the same as
equivalent**, and the grouping is what carries that.

**Two categories in profile review are deliberately not merged.** A contradiction is a
property of the profile alone, needs no solver to see, and is rejected. **Subsumption is
reported and not rejected**: a rule that forbids nothing is valid, the tenant may have
meant it, and nothing else in the system would ever tell them the protection is inert.

**One blocker is a hint, not a guarantee.** Each recommendation candidate is re-solved on
a disposable copy of the instance and kept only if the shift actually closes.

**Nothing is applied.** Every candidate is a fresh, disposable instance, so the incumbent
and every employee's real record are exactly as they were. Ignoring a rule for one solve is
not the same as changing somebody's record, and publishing an override is the caller's
later act.

## Out of scope

- **A patch endpoint over `Instance`.** An arbitrary-edit hole wearing a schema. Each
  `Change` kind is one whose interaction with the rule registry was understood before it
  was allowed.
- **Refusing rule relaxations outright.** That would hide the lawful case the tool exists
  for.
- **Dropping statutory candidates from the recommendation list.** It hides a lawful option
  a planner may weigh.
- **An order over rule kinds.** This project cannot derive one from disruption, and
  inventing one would be the same error the flat list made.
- **Any tool that writes.** `validate_profile` checks and reports; the save is the
  caller's.
- **Testing people blocked by more than one rule.** Only single-blocker candidates are
  swept, and only where the rule has an override kind: `R-SKILL`, `R-MAX-DAILY` and
  `R-MAX-WEEKLY` today.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Is an unlawful hypothetical solved and flagged, or refused?** Refused
   ([`D-098`](../decisions.md#d-098)). `validation.py` already knew better and was already
   written.

2. **Is the natural-language parse built before deterministic review?** No
   ([`D-099`](../decisions.md#d-099)). An accelerator built before the thing it
   accelerates has nothing to fall back to.

3. **Is an enabled-but-unencoded rule a warning?** No, a defect
   ([`D-099`](../decisions.md#d-099)). Accepting it would put the registry's description
   of intent into production through configuration instead of through documentation.

4. **Is the recommendation list one ranking?** No, grouped by provenance
   ([`D-144`](../decisions.md#d-144)).

5. **Is a hypothetical hire eligible everywhere?** Yes, and that optimistic reading is
   stated rather than hidden ([`D-098`](../decisions.md#d-098)).

6. **Where does the priors warning live?** In `profile.remarks`, not in `validation.py`
   ([`D-131`](../decisions.md#d-131)). A fairness window longer than the tier count is
   lawful, and every validation finding rejects a request.

---

*The ledger: [`README.md`](README.md). The tools:
[`guide/api.md`](../guide/api.md). The profile:
[`guide/configuring.md`](../guide/configuring.md).*
