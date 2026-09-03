# Importing their coverage rule, and the scale evidence it was hiding

**Status:** Implemented 2026-09-03
**Depends on:** [`gating-cost`](gating-cost.md), whose measurements found this.

## Objective

Find out why three rows of the foreign scale table stopped reproducing, correct them and every
claim resting on them, and specify the import fix behind it.

**Scoped to the correction.** The fix, importing their coverage rule rather than a stricter one
this project imposes by accident, is specified here in full and deliberately not built: see
decision 0.

## Motivation

Three rows of the scale table in [`foreign-incumbent.md`](../studies/foreign-incumbent.md) no
longer reproduce. Instances 8, 10 and 23 return `INFEASIBLE` where the table records `OPTIMAL`
at 7.71 s and 1.91 s and `UNKNOWN` at eight million variables. Four claims rest on those rows,
including *"the first genuinely hard searches this project has seen"*, which is the repository's
answer to the standing objection that nothing here is ever hard.

**The evidence is not stale. It is hidden, and by a defect in this repository.**

Their format states a coverage *requirement* with two weights, one for being under it and one
for being over it. Over-coverage is priced on **every slot of every instance**: 112 slots on
instance 8, 140 on instance 10, 5,824 on instance 23, all with a non-zero weight. Their model
permits overstaffing and charges for it.

This project prohibits it. `R-COVER`'s ceiling is a hard gated `overage == 0`, and the import
never reads their over-weight. So a published roster that legitimately overstaffs is imported as
one this model calls illegal, and when the overstaffing falls in the pinned past the replan is
refused before it starts:

| instance | overstaffed slot | assigned / required |
| --- | --- | --- |
| 8 | day 2, hour 62, pinned | 5 / 4 |
| 10 | day 4, hour 118, pinned | 3 / 1 |
| 23 | day 0, hour 6, pinned | 6 / 3 |

**This is the third mapping error in this import**, after `MaxTotalMinutes` read as a weekly rate
and days off translated as intervals ([`foreign-incumbent.md`](../studies/foreign-incumbent.md)).
Both of those were found the same way and both inflated the same figure.

Each recovery was confirmed by reversing the cause rather than argued. Permitting over-coverage
returns instance 10 to `OPTIMAL` in **2.22 s** against the recorded 1.91 s. Instance 8 needs that
and one more thing, [`D-133`](../decisions.md#d-133): on the published solution the table was
measured against, it returns `OPTIMAL` in **8.43 s** against the recorded 7.71 s. Both on a
slower machine than the original run.

## Canonical reference

[`guide/rules.md`](../guide/rules.md) owns the `R-COVER` predicate, including the ceiling this
component makes conditional. [`internals/model.md`](../internals/model.md) owns the objective the
price would join, and the domination bound that constrains any new weight
([`D-057`](../decisions.md#d-057)). [`foreign-incumbent.md`](../studies/foreign-incumbent.md)
owns the import and its scale table.

[`D-018`](../decisions.md#d-018) decided the soft floor and the hard ceiling together, and
[`D-137`](../decisions.md#d-137) established that a comparison against their published optimum
runs on their constraints. This component sits at the meeting point of those two and does not
overturn either.

## Governing reference

None. Belgian law states a minimum staffing obligation nowhere in this registry, and the ceiling
was never a statutory claim. It is operational, which is what makes it changeable here.

## Parameters and configuration

One parameter, and its default is today's behaviour exactly:

```text
overage_weight: float | None = None
```

`None` keeps `R-COVER`'s hard ceiling: `overage == 0`, gated as now. A number prices the overage
instead, exactly as `shortfall_weight` prices the floor, and removes the gate.

The value the foreign import passes is **not** their number. Their weights sit on their scale and
converting them would answer [`D-057`](../decisions.md#d-057)'s bound question with somebody
else's units, which is the mistake
[`foreign-incumbent.md`](../studies/foreign-incumbent.md) already refuses elsewhere.

## Interfaces

```text
RuleParams(..., overage_weight: float | None = None)
model.build / checker.check                 read it; no signature changes
foreign.load(number)                        sets it, because their format states one
```

No wire schema change. `service/contracts.py` gains the field only if a tenant needs it, and no
tenant has asked.

## Layering

None. The parameter lives in [`domain.py`](../../roster_replan/domain.py), which is the one
module the model and the checker may both import, and it is a rule threshold of the kind that
module already carries.

## Build tasks

**Scope was cut to the correction after the measurements were taken.** The fix changes a shipped
predicate for a benchmark's benefit, and the correction does not depend on it, so the two were
separated and only the correction was built. Everything below records that decision, not a
shortfall against it.

- [!] `overage_weight` on `RuleParams`: **not built.** Deferred with the rest of the fix
- [!] `R-COVER`'s ceiling made conditional in the model and the checker: **not built**
- [!] the predicate updated in [`rules.md`](../guide/rules.md): **not built**
- [!] the domination bound re-derived: **not built**, and it is the reason the fix is a component
  rather than a patch
- [x] the scale table re-run, all nine rows, and corrected in place in
  [`foreign-incumbent.md`](../studies/foreign-incumbent.md)
- [x] the over-coverage mapping error documented there as the third one
- [x] the *10 of 13* figure recounted by `study()`'s own method: **8 of 13** excluding permitted
  over-coverage
- [x] every claim resting on the stale rows corrected: [`time-budget.md`](../studies/time-budget.md),
  [`internals/model.md`](../internals/model.md), [`model.md`](model.md),
  [`cross-week-rules.md`](cross-week-rules.md)
- [x] the records: [`D-155`](../decisions.md#d-155) and [`D-156`](../decisions.md#d-156)
- [x] the five performance nulls collected in
  [`scaling-levers.md`](../studies/scaling-levers.md)
- [!] the mutants: **not built**, because no code changed

## Test contract

- **Differential** (`tests/test_differential.py`): the layer that matters most. A conditional
  ceiling is two readings of one predicate and the harness is what says they agree. Both
  settings must be exercised, because a checker that ignores `overage_weight` agrees with a
  model that ignores it too.
- **Ground truth** (`tests/test_ground_truth.py`): on a micro-instance small enough to
  enumerate, the priced optimum is the enumerated optimum. This is what stops a priced overage
  being bought when it should not be.
- **Golden** (`tests/test_golden.py`): every committed roster is unchanged, since every
  committed instance leaves the parameter `None`. This is the claim that the default is
  genuinely today's behaviour.
- **Foreign** (`tests/test_foreign.py`): instances 8 and 10 reach `OPTIMAL` with the parameter
  set, and the recovered search times are recorded rather than asserted, since they are wall
  clock.
- **Mutants**: one making the ceiling unconditional, caught by the foreign layer, and one making
  the checker ignore the weight while the model honours it, caught by the differential harness.
  The second is the one worth having.

## Acceptance gate

*Blocks:* nothing.

- [x] Instances 8 and 10 reach `OPTIMAL` under their own coverage rule: 8.43 s and 2.22 s, against
  the table's 7.71 s and 1.91 s, each confirmed by reversing one cause alone
- [x] Every committed roster byte-identical: no code changed
- [!] The differential harness with the parameter set and unset: **not run**, the parameter does
  not exist
- [!] The domination bound re-derived: **not done**, deferred with the fix
- [x] The scale table re-run and corrected, and every claim citing it either reproduced or fixed
- [x] Full suite green: 948 passed
- [!] Both mutants caught: **not built**, no code changed

## Measured results

Taken while scoping; the study replaces them.

The re-measurement of the whole table, single worker, 30 s budget. **Six of nine rows reproduce
and three flip**, and the sizes reproduce throughout, to within the injured employee:

| instance | table | today |
| --- | --- | --- |
| 2, 6 | `OPTIMAL` | `OPTIMAL` |
| 8 | `OPTIMAL`, 7.71 s | `INFEASIBLE` |
| 10 | `OPTIMAL`, 1.91 s | `INFEASIBLE` |
| 13, 20, 21, 22 | infeasible past | `INFEASIBLE` |
| 23 | `UNKNOWN`, 16.46 s | `INFEASIBLE`, after a 561 s build |

Recovery, each confirmed by reversing one cause at a time: instance 10 with over-coverage
permitted returns `OPTIMAL` in 2.22 s; instance 8, on the published solution the table was
measured against and with over-coverage permitted, returns `OPTIMAL` in 8.43 s.

**Instance 23 is not expected to recover**, and that is worth stating in advance so the result
is not read as a failure of this component. Beyond its overstaffed slot it carries 141 forced
`R-MAX-WEEKLY` and 57 forced `R-WEEKLY-REST` violations inside the pinned past. Those are
Belgium being stricter, which is the import working as intended.

## Out of scope

- **The pre-build incumbent check.** Specified here first and moved out. It is independent of
  the coverage rule, and this fix removes most of the value it was measured against: an
  incumbent that is legal does not need cheap detection of being illegal. It deserves its own
  spec and its monotone rule set has to include `R-COVER` overage, which the scoping here found
  by getting it wrong.
- **Re-deciding [`D-018`](../decisions.md#d-018).** The hard ceiling stays the default and stays
  the shipped behaviour for every tenant.
- **Importing their weights on their scale.** The parameter takes this project's units.
- **Un-retiring LNS.** If instance 8 comes back at 8.43 s of search, that is the evidence
  [`D-127`](../decisions.md#d-127) leaned on, restored rather than extended.

## Decisions

0. **Fix the import, or correct the record?** **Resolved: correct now, fix later**
   (2026-09-03). The correction stands on its own and the fix does not: making `R-COVER`'s ceiling
   conditional touches a shipped predicate, both readings of it, and
   [`D-057`](../decisions.md#d-057)'s domination bound, for the benefit of a benchmark import. The
   decisions below are kept as the trail for whoever takes the fix.
1. **Price the overage, or give the slot a maximum?** *Proposed:* price it. A maximum would state
   a band their format does not have, so it would be a second invention on top of the one being
   removed. Pricing is also symmetric with the floor, which is already soft and priced, and it
   reuses the machinery and the reasoning of [`D-018`](../decisions.md#d-018) rather than adding
   a parallel one.
2. **Where does the parameter live, `RuleParams` or `Disruption`?** *Proposed:* `RuleParams`. It
   is a property of the rule rather than of the objective, it sits beside the thresholds the rule
   already reads, and `Disruption` is about deviation from the incumbent, which this is not.
3. **Does a priced overage break the domination bound?** *Proposed:* it must be brought inside
   it. [`D-057`](../decisions.md#d-057) requires `shortfall_weight` to dominate everything that
   could buy understaffing, and a priced overage is a new term in that comparison. Re-derive
   rather than assume, and validate at profile load as every other weight is.
4. **Should `scenario()` call `as_rules`?** **Resolved: no** (2026-09-03). Measured: it changes
   nothing here, because `as_rules` touches neither `R-COVER` nor `R-WEEKLY-REST`. The scale path
   imposing Belgian rules is deliberate, and the coverage ceiling was never part of that
   intention.
5. **Is the *10 of 13 illegal pasts* figure wrong?** *Proposed:* inflated rather than wrong, and
   it needs recounting once the import is fixed. It currently counts permitted over-coverage as
   illegality. What survives the recount is the genuine finding, and it is the one the study was
   written to make.
6. **Does this restore [`D-127`](../decisions.md#d-127)'s claim or replace it?** *Proposed:*
   restores the hard-search half and leaves the build ceiling untouched. *"At eight million the
   search finds nothing"* stays unproven either way, because instance 23 is refused for reasons
   this component does not remove.

---

*The ledger: [`README.md`](README.md). The reasoning behind the shape of this file:
[`documentation.md`](documentation.md#specs-for-the-built-components).*
