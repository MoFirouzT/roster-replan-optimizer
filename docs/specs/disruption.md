# Disruption: the objective

**Status:** Implemented 2026-08-14
**Reconstructed 2026-09-02** from [`disruption.py`](../../roster_replan/disruption.py),
[`scoring.py`](../../roster_replan/scoring.py),
[`internals/model.md`](../internals/model.md),
[`studies/disruption-metrics.md`](../studies/disruption-metrics.md), the records cited
below, and the commits of 2026-08-12 to 2026-08-14. **It is not the work order this
component was built from.** No such document existed: the seven files in this directory
before 2026-08-20 were design statements with no gate and no build tasks
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** the model, which owns the variables this prices.

## Objective

Price a replan by how far it departs from the published roster rather than by what it
costs, and give that price five definitions so the choice between them is a decision
somebody makes rather than one nobody notices.

## Motivation

A scheduler re-solving after a sick call gets the cheapest week. A planner wants the
cheapest *change*: cost cannot see that people have already been told, so it is free to
rearrange staff the disruption never touched. The claim this whole project rests on is
that the second-best roster nobody has to be re-told about beats the best roster
everybody does ([`D-005`](../decisions.md#d-005)).

Saying that is easy and it does not settle anything, because "how far it departs" has
more than one honest meaning. Counting changed assignments, weighting them by whether
people knew, weighting them by how much notice they get, counting a move as one event
rather than two, and penalising five changes landing on one person: all five are
defensible and they do not agree. The component exists to define all five, ship one, and
measure whether the disagreement is real.

## Canonical reference

[`internals/model.md`](../internals/model.md) owns the statement:

- **Objective**, the weighted sum and the derived weight ordering
- **What disruption is a function of**, the incumbent, the publication state and `now`
- **The five disruption metrics**, D0 through D4 and the concentration encoding
- **Fairness**, which shares the objective and is a different quantity

The shipped parameters are in [`guide/configuring.md`](../guide/configuring.md); the
frontier this objective trades on is in [`guide/limits.md`](../guide/limits.md).
Nothing in this file restates a formula from those documents.

## Governing reference

None. Deviation from an incumbent is not a statutory quantity and no source names one.
Every rule this objective trades against has provenance; the objective itself has none
and does not claim any.

## Parameters and configuration

All on `Disruption` in [`domain.py`](../../roster_replan/domain.py), set per profile:

| Parameter | Shipped | Note |
| --- | --- | --- |
| `metric` | `"D2"` | `"D0"` to `"D4"` |
| `published_weight`, `draft_weight` | 10, 1 | `draft_weight` is deliberately not zero |
| notice bands | under 24 h ×4, else ×1 | a step, not a decay |
| `W_move`, `W_cancel`, `W_callin` | D3 and D4 only | the ordering is a hypothesis |
| `concentration_weight`, `concentration_tiers` | D4 only | triangular |
| `shortfall_weight`, `mix_shortfall_weight` | must dominate | checked at load |
| `cost_weight` | 0 | inert on every instance this project has |

`cost_weight` shipping at zero is a fact about the data, not a preference: no instance
carries a wage, so all rates are 1.0 and the term is fixed once coverage is. It stays
because switching it on is how the cost baseline is defined.

## Interfaces

```text
disruption.objective_terms(model, instance, x, params) -> list      the model's reading
disruption.fairness_terms(model, instance, x, params)  -> list
scoring.score(roster, instance) -> Score                            the independent reading
scoring.disruption_of(roster, instance) -> int
scoring.max_change_weight(instance) -> int                          used by validation
```

`Score` reports the terms separately rather than only as a total, because the
coverage-against-disruption frontier needs both axes and one number cannot be put on a
chart.

## Layering

Two contracts in `pyproject.toml`, and they are the component's central claim rather
than housekeeping:

- *The objective scorer is an independent reading: no solver, no model encoding.*
  `scoring` may not import `disruption`, `model`, `checker` or `ortools`.
- *The objective encoding never reaches the scorer.*

Brute force compares the optimum `disruption` encodes against the minimum `scoring`
measures, so a shared helper would turn that comparison into an identity
([`D-004`](../decisions.md#d-004)).

## Build tasks

- [x] Define D0 through D4 so that each nests the one before it.
- [x] Encode all five in `disruption.py`, and score all five in `scoring.py`.
- [x] Encode concentration without piecewise machinery.
- [x] Derive the weight ordering that stops understaffing being bought, and check it at
      profile load rather than trusting it ([`D-057`](../decisions.md#d-057)).
- [x] Measure whether the five actually choose different rosters.

## Test contract

| Claim | Layer |
| --- | --- |
| D1 with equal weights is D0; D2 with a flat band is D1 | `test_replan.py`, the three nesting tests |
| Each metric prices what it says it prices | `test_replan.py`, D0 through D4 and the triangular penalty |
| The encoding and the scorer agree on the chosen roster | `test_replan.py::test_scorer_agrees_with_the_model_on_the_chosen_roster`, all five |
| The encoded optimum is the true optimum | brute force, three cases including one where the incumbent became ineligible |
| The metrics genuinely disagree | `test_replan.py::test_d2_and_d3_choose_different_rosters`, and the regret matrix in `test_metrics.py` |
| Understaffing is never bought | `test_replan.py::test_understaffing_is_never_bought`, plus the bound tests |

Five mutants name a layer here: `model-publication-weights-swapped`,
`model-notice-multiplier-dropped`, `scorer-notice-multiplier-dropped`,
`validation-domination-bound-never-fires`, and `both-readings-reweighted`.

The last one is the point. Reweighting *both* readings the same way is invisible to the
differential comparison, because the two readings still agree; only a committed number
catches it ([`D-067`](../decisions.md#d-067)). Two independent readings do not protect
against a shared premise, and this component is where that limit was first written down.

## Acceptance gate

*Blocks:* nothing now. It blocked the benchmark set, which scores every method with
`scoring.py`.

- [x] All five metrics encoded and independently scored. `scoring.py` implements five,
      not only the shipped one ([`D-006`](../decisions.md#d-006)).
- [x] Brute force agrees with the solver on every metric, on cold, replan, and
      ineligible-incumbent instances.
- [x] The domination bound is derived rather than tuned, and is rejected at load when a
      profile breaks it. `test_replan.py::test_domination_bound_is_validated`.
- [x] The shipped default satisfies its own bound.
- [x] The five are shown to choose different rosters. **10 of 84 committed cases**
      ([`disruption-metrics.md`](../studies/disruption-metrics.md)).
- [!] **The divergence rate is not a durable number.** It was 26 of 84 when this gate
      was first met and is 10 of 84 now. Nothing about the method changed: the canonical
      optimum ([`D-119`](../decisions.md#d-119)) changed the incumbents, so every replan
      in the set became a different instance ([`D-120`](../decisions.md#d-120)). The
      structure held and the rate did not.
- [!] **D4 is not exercised by the committed set.** Concentration needs two events on
      one person and the median damage is one assignment, so D4 agrees with D3 on all 84
      cases. It is encoded, unit-tested and unmeasured in the aggregate, and that is
      recorded rather than inferred.

## Measured results

**They disagree, and where they disagree they disagree badly.** Regret is roughly 100%
in both directions: each metric scores the other's answer at about twice its own
optimum. The split is entirely D0/D1/D2 on one side and D3/D4 on the other, with zero
conflict in all six ordered pairs within the first group.

That zero is structural rather than lucky. The whole week is published
([`D-051`](../decisions.md#d-051)) and a disruption damages a specific slot, so every
candidate repair changes that same slot and `P × N` multiplies every option equally. A
constant factor cannot reorder anything. D1 and D2 earn their weights when a repair can
choose *which* slot to disturb, and no scenario in this set poses that question.

**Divergence needs slack, and slack is nowhere near sufficient**
([`D-060`](../decisions.md#d-060)). Measured at the damaged slot, all ten divergences sit
in the top slack bucket and every other bucket is a clean zero. Measured at the week
level, the relationship is not monotone and the most constrained bucket has the highest
conflict rate, which is the instrument and not the world. The missing condition is
structural: D3 leaves D2 only when a *move* is available, and the committed set does not
vary that axis.

**One measurement here was withdrawn rather than corrected.** The coverage-axis curve
this study drew was retired outright when the instances moved ([`D-120`](../decisions.md#d-120)).

## Out of scope

- **Choosing between D3 and D4 on evidence.** The `W_callin > W_cancel > W_move`
  ordering is a claim about what people prefer, not a measurement, and this project has
  no data that could settle it. It ships as an option for that reason.
- **Wave publication.** `published_through` is one number, so a roster with some shifts
  announced and others held back inside the same horizon cannot be expressed. The
  general form is a set, the current form is a special case of it, and the change is
  additive when a tenant needs it.
- **`extend` as a change type.** Shift boundaries are data, so no roster extends one.
- **A real cost model.** Overtime premiums, weekend rates and wage data are absent, and
  the placeholder says so where it is written.
- **Affected-slot weighting in D3.** It would make the objective non-linear and
  impossible to match between the two readings, and matching them is the whole design.

## Decisions

Reconstructed. Each of these was decided while the component was built and the reasoning
is in the record, which is the citation. Where no record exists, this section says so.

1. **Deviate from the incumbent, or re-solve on cost?** Deviate.
   [`D-005`](../decisions.md#d-005). The consequence is that the objective needs three
   inputs a cost objective does not, and that a cold solve becomes the degenerate case
   rather than a second formulation.

2. **Ship one metric, or define five and ship one?** Five.
   [`D-006`](../decisions.md#d-006). D2 is the simplest metric that prices the two things
   a planner reacts to, whether people were told and how much warning they get. D3 and
   D4 add claims about human preference, and a hypothesis is better shipped as an option
   than baked into a default.

3. **Is `draft_weight` zero?** No, and this was decided in the definition rather than in
   a record. Zero leaves the solver indifferent among draft rosters, and indifference
   costs stable output across runs and a warm start that resembles its hint. The same
   failure is named from the other side in the cost baseline: an indifferent objective
   produces arbitrary output that looks like a finding.

4. **Notice as a step or a decay?** A step. Statutory and contractual notice periods are
   themselves steps, and a step is easy to explain where a decay curve invites argument
   about its shape. No record: it was settled in the definition and has not been
   revisited.

5. **Is the weight ordering tuned?** No, derived, and checked rather than trusted
   ([`D-057`](../decisions.md#d-057)). Understaffing reduces disruption and fairness both,
   so the shortfall weight has to dominate both, and a weight scale that breaks the bound
   is a malformed request rather than a bad answer.

6. **Where is `P × N` evaluated in D3?** At the day's anchor slot, its earliest *open*
   shift, deliberately not its earliest *affected* one. Solution-independence is what
   makes the two readings comparable, and affected-slot weighting would destroy it. The
   cost is that a move inside a long day is priced by the day's earliest notice.

---

*The ledger: [`README.md`](README.md). The reasoning: [`decisions.md`](../decisions.md).
The measurement: [`disruption-metrics.md`](../studies/disruption-metrics.md).*
