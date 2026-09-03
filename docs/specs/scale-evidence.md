# The scale evidence, re-measured, and the check that comes before the build

**Status:** Draft
**Depends on:** [`gating-cost`](gating-cost.md), whose measurements found this.

## Objective

Correct the foreign scale table to what reproduces today, and stop spending a full model
build to learn something a solver-free function knows in two seconds.

## Motivation

[`foreign-incumbent.md`](../studies/foreign-incumbent.md) carries the table that
[`D-127`](../decisions.md#d-127) rests on, and four claims are drawn from it across the
repository. Three of them no longer reproduce.

The table records instance 8 proving optimality in **7.71 s of search**, called *"the first
genuinely hard searches this project has seen"* and used as the answer to the standing
objection that nothing here is ever hard. It records instance 23 returning `UNKNOWN` at
8M variables, quoted as *"at eight million the search finds nothing"*.

**Today instances 8, 10 and 23 all return `INFEASIBLE`**, decided in presolve, because their
incumbents have illegal pasts. Instance 23 returns it after a 606 s build. The likely cause is
[`D-133`](../decisions.md#d-133), which changed `load` to take the best published solution by
their objective and so changed which pasts are legal.

The sizes in the table do reproduce, to within the injured employee: 8,049,159 variables
against the recorded 8,049,059. **What has rotted is the solve column, not the size column**,
and the distinction matters because the build ceiling survives and the search evidence does not.

Underneath sits a second finding. **No published solution rescues any large instance.** The
minimum hard violations across every published solution are 17, 388, 625, 942 and 1,709 for
instances 13, 20, 21, 22 and 23. This benchmark set cannot supply a large valid replan, so the
project has no evidence at all about what one costs.

## Canonical reference

[`internals/model.md`](../internals/model.md) owns *where it stops*.
[`guide/rules.md`](../guide/rules.md) owns the predicates, and this component adds a property
to them: whether a rule is **monotone**, in the sense that adding assignments can only create
or worsen a violation of it. That property is what makes the pre-build check sound, so
`rules.md` owns it and this spec cites it rather than listing it.

[`guide/limits.md`](../guide/limits.md) owns what the service guarantees, including the
fallback ladder's promise to always answer.

## Governing reference

None. No statutory parameter moves.

## Parameters and configuration

No profile or payload parameter. One function, and it is not a caller knob:

```text
checker.forced_violations(instance) -> list[Violation]
```

The hard violations of monotone rules committed entirely inside the pinned past. Non-empty
means no legal roster exists, whatever is chosen for the future.

## Interfaces

```text
checker.forced_violations(instance)   -> list[Violation]
ladder.answer(instance, ...)          -> unchanged signature and unchanged rungs
```

`ladder.answer` consults `forced_violations` before building. A non-empty result takes the
`incumbent` rung directly, which already returns the published roster with its violations named
and already marks the answer as the floor rather than a repair. **No new rung and no new
promise**: this reaches an existing outcome without paying for the model first.

`model.solve` is untouched. A caller solving directly still builds and still gets a core, which
is the minimal explanation the pre-build check does not produce.

## Layering

None. `checker.py` keeps its position and imports no solver, which is what lets this run before
a model exists.

## Build tasks

- [ ] the monotone property in [`rules.md`](../guide/rules.md), one bullet per rule with its reason
- [ ] `checker.forced_violations`
- [ ] `ladder.answer` consults it before building
- [ ] re-run the scale table and correct [`foreign-incumbent.md`](../studies/foreign-incumbent.md)
- [ ] correct every claim resting on the stale rows: [`D-127`](../decisions.md#d-127),
  [`design.md`](../internals/design.md), [`model.md`](model.md),
  [`time-budget.md`](../studies/time-budget.md), the [ledger](README.md) and the
  [studies index](../studies/README.md)
- [ ] record that no published solution gives a legal past, and what that costs the evidence
- [ ] the record in [`decisions.md`](../decisions.md)
- [ ] the mutant, named to its catching layer

## Test contract

- **Unit** (`tests/test_checker.py`): `forced_violations` is empty on a legal past, non-empty on
  a past breaking a monotone rule, and **empty on a past breaking only a non-monotone one**. The
  third is the one that matters: a `R-MIN-HOURS` shortfall in the past is repairable in the
  future, and reporting it as forced would refuse a week that has a legal answer.
- **Ladder** (`tests/test_ladder.py`): an instance with a forced violation reaches the
  `incumbent` rung with the same roster, violations and rung it reaches today without the
  short-circuit. This is the claim that the change is a speedup and not a behaviour change.
- **Differential** (`tests/test_differential.py`): unchanged. The model never sees this
  function, so a disagreement here would mean the monotone classification is wrong rather than
  the checker.
- **Mutant**: `forced_violations` returning a non-monotone rule's violation, so a repairable
  week is refused. Named catcher: `tests/test_checker.py`.

## Acceptance gate

*Blocks:* nothing.

- [ ] Every claim citing the scale table either reproduces or is corrected, with the run that
  settled it recorded
- [ ] `forced_violations` agrees with the solver on all five large foreign instances: forced
  violations found exactly where the model proves infeasible
- [ ] The ladder returns the same answer with and without the short-circuit on every committed
  case
- [ ] Full suite green
- [ ] Mutant caught by its named layer

## Measured results

Taken while scoping, and the study replaces them.

**The pre-build check is 300× cheaper than learning the same thing from the model.** Forced
monotone violations inside the pinned past, against the build that discovers the same
infeasibility:

| instance | staff × weeks | build | `forced_violations` | forced | full hard |
| --- | --- | --- | --- | --- | --- |
| 13 | 120 × 4 | 9.7 s | 25 ms | 9 | 18 |
| 20 | 50 × 26 | 10.0 s | 155 ms | 28 | 393 |
| 21 | 100 × 26 | 45 s | 347 ms | 53 | 626 |
| 22 | 50 × 52 | 67 s | 869 ms | 50 | 943 |
| 23 | 100 × 52 | **606 s** | **2,020 ms** | 198 | 1,710 |

Only `R-MAX-WEEKLY` and `R-WEEKLY-REST` fire, on every instance. Both are monotone by
inspection: a week's hours only grow as assignments are added, and a rest window only shrinks.

**The saving is real and its demonstrated value is narrow, which is worth stating.** Every
instance it helps is one this service cannot answer anyway, and on the committed set the build
it skips costs about 5 ms. It converts a 606 s route to a refusal into a 2 s one, and it does
not make a single answerable week faster.

## Out of scope

- **Making a large valid replan available.** The benchmark set cannot supply one and this
  component does not go looking. It records the gap.
- **A minimal core from the pre-build check.** It names forced violations, not the minimal
  conflict set `solve` returns. A caller wanting the core still pays for the model.
- **Re-deciding [`D-133`](../decisions.md#d-133).** Taking the best published solution stays;
  what changes is the table measured under it.
- **Un-retiring LNS.** [`D-127`](../decisions.md#d-127) bounded
  [`D-104`](../decisions.md#d-104) on evidence that has now gone, which weakens the bound and
  does not restore the lever.

## Decisions

1. **Correct the table in place, or retire it?** *Proposed:* correct in place and say what
   moved. A measurement is durable ([`CLAUDE.md`](../../CLAUDE.md)), so the rows stay with the
   conditions they were taken under, and the run that contradicts them is recorded beside them
   rather than replacing them silently.
2. **Does this supersede [`D-127`](../decisions.md#d-127) or bound it?** *Proposed:* bounds it.
   Its build ceiling reproduces and is untouched. What falls is the search half, which was
   never the decision, only the evidence quoted around it.
3. **Should the short-circuit be in `ladder` or in `solve`?** *Proposed:* `ladder`. `solve`
   promises a core on infeasibility and this function cannot produce one, so putting it there
   would weaken a documented return. The ladder already owns the incumbent rung and the
   never-return-nothing promise.
4. **Where does the monotone property live?** *Proposed:* [`rules.md`](../guide/rules.md), one
   bullet per rule beside the existing *Model encoding* bullet. It is a property of the
   predicate, and putting it in `checker.py` alone would make the model and the checker disagree
   about what a rule means with nothing to catch it.
5. **Is `historical` on `Violation` the same property?** **Resolved: no** (2026-09-03). It is
   set on `R-COVER`, `R-SKILL-MIX` and `R-PIN-PAST` only, and it marks where a violation sits
   rather than whether the future could repair it. Reusing it would have been wrong on both
   counts.

---

*The ledger: [`README.md`](README.md). The reasoning behind the shape of this file:
[`spec-reconstruction.md`](spec-reconstruction.md).*
