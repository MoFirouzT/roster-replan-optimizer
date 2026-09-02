# Foreign incumbents and the cross-week rules

**Status:** Implemented 2026-08-17
**Reconstructed 2026-09-02** from [`benchmarks/foreign.py`](../../benchmarks/foreign.py),
[`studies/foreign-incumbent.md`](../studies/foreign-incumbent.md),
[`studies/cross-week-reach.md`](../studies/cross-week-reach.md),
[`guide/rules-statutory.md`](../guide/rules-statutory.md), the mutant catalogue, and the
commits of 2026-08-15 to 2026-08-17. **It is not the work order this component was built
from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`benchmark-set.md`](benchmark-set.md), whose caveat this exists to
attack.

## Objective

Replan rosters this project did not produce, to test the one claim the committed set
cannot make, and encode whatever their constraints turn out to demand.

## Motivation

The benchmark set solves its own incumbent. Every number in it shows a replan beats a
re-solve **given a roster this model would produce**, not that the model resembles what
real planners publish. That was the largest single gap in the evidence.

Capture and replay was written to close it with a captured corpus and is blocked on an
authorization outside this repository. **This is the half that is not blocked**: published
solutions from the nurse-rostering benchmark set are rosters other people's solvers
produced, optimising an objective this project does not implement.

## Canonical reference

[`guide/rules-statutory.md`](../guide/rules-statutory.md) owns the predicates of the seven
rules this added. [`benchmarks.md`](../benchmarks.md) owns what their use as incumbents
does to the headline claim.

## Governing reference

The nurse-rostering benchmark set, cited in the study. Their constraints are **somebody
else's operational limits**, not a legal instrument, which is why the rules derived from
them carry an operational or CBA provenance rather than a statutory one.

## Parameters and configuration

```bash
uv run python -m benchmarks.foreign --fetch
uv run python -m benchmarks.foreign --study
```

**Fetched and fingerprinted, never redistributed** ([`D-125`](../decisions.md#d-125)).
What is committed is a manifest, not their data.

## Interfaces

```text
foreign.load(number)              their instance, the best published solution, and what is unencoded
foreign.their_violations(...)     one reading, in benchmarks/, with no rule IDs
foreign.compare(...)              their instance, their objective, scored against their optimum
foreign.score_their_objective(...)
```

## Layering

`benchmarks/` sits off the service chain. `their_violations` deliberately lives there
rather than in `checker.py`, because it is a measurement rather than a rule of this
product.

## Build tasks

- [x] Fetch and fingerprint their instances and published solutions.
- [x] Load the **best** published solution by their own objective, not whichever one
      `glob` returns.
- [x] Implement their objective and reproduce every published value.
- [x] Read their seven per-employee constraints as one measurement, before encoding any.
- [x] Use their rosters as incumbents and re-run the headline comparison.
- [x] Encode the ones that earned it, as rules with IDs, predicates and two readings.

## Test contract

| Claim | Layer |
| --- | --- |
| Their objective is scored the way they score it | `test_foreign.py`, three objective mutants |
| Their cover weights and request lists are not transposed | `foreign-cover-weights-are-swapped`, `foreign-objective-reverses-the-request-lists` |
| Max shifts is per type, not a total | `foreign-max-shifts-read-as-a-total` |
| A run at the horizon edge keeps its latitude | `foreign-max-run-gets-the-boundary-latitude-too` |
| Weekends are counted per week, not per day | `foreign-weekends-counted-per-day-not-per-week` |
| Succession has a direction | `foreign-succession-ignores-direction` |
| The incumbent is the best published solution, not whichever was found | `foreign-incumbent-is-whichever-solution-was-found` |

**The measurement checks itself against data this project did not choose.** Their rosters
satisfy their own constraints, so a correct reading reports nothing on all 26. That caught
a misreading on its first run: a minimum block applied at the horizon's edge failed **every
one of the 26**, because a stretch touching either end may continue outside the window.

## Acceptance gate

*Blocks:* nothing. This closes an evidence gap rather than opening a capability.

- [x] **The headline claim reproduces on rosters this project did not produce, by 4.6× to
      37×**, against about 5× on the committed set
      ([`D-125`](../decisions.md#d-125), [`D-137`](../decisions.md#d-137)).
- [x] Both implementations of their objective agree on every case, and it reproduces every
      published value ([`D-133`](../decisions.md#d-133)).
- [x] Their seven constraints bind hard when measured: **every one of the seven is broken**
      by a roster this project produces ([`D-134`](../decisions.md#d-134)).
- [!] **The first reading of the study was measured on a machine-dependent incumbent.** It
      reported 10× to 27× over five instances, on whichever published solution `glob`
      happened to return, which was a **non-best** solution on 8 of the 13 and depended on
      directory order. Re-measured on named incumbents: three instances have a clean past
      instead of five, the direction is unchanged, and **the bottom end is weaker**, one
      instance repairing at 4.6× where the old sample's weakest was 10×
      ([`D-133`](../decisions.md#d-133)).
- [!] **The quality comparison's caveat is larger than its result**
      ([`D-137`](../decisions.md#d-137)). Two of three came back **below** their published
      optimum, and 23 of their 24 solutions are proven optimal under their own objective,
      so a lower number means this comparison granted a freedom their solver did not have.
      It granted two: days off are dropped rather than translated, and the rest rule was
      three hours weaker. Closing the rest gap moved one instance from 1.16× to 1.11× and
      left two unchanged, **so the days-off freedom is carrying the result**. The numbers
      are not a claim that this solver is better, and the unfairness runs the other way
      too without cancelling.

## Measured results

**Foreign data found three things a synthetic set could not.**

**Ten of thirteen published rosters have a past this model calls illegal.** A generator
that builds its own incumbent cannot produce that, because it only ever builds legal ones.

**The first genuinely hard searches this project has seen**, and where the model stops:
about 40 employees over four weeks, **527 s of model construction at 8M variables**, and no
roster ([`D-127`](../decisions.md#d-127)). 7.71 s to prove optimality on another, against a
committed-set maximum of 15.4 ms.

**Their split of hard from soft is not this project's**
([`D-132`](../decisions.md#d-132)). Four items catalogued here as preferences are hard
constraints where those rosters come from, which is a fact about the domain rather than a
disagreement to settle.

**Seven of their constraints became rules of this product**, hard and optional, each with
an ID, a predicate, two readings and a mutant
([`D-135`](../decisions.md#d-135), [`D-136`](../decisions.md#d-136)). One of them can
refuse a roster outright.

## Out of scope

- **Redistributing their data.** Fetched and fingerprinted only.
- **Reporting 0.87× and 0.89× as wins.** They are a red flag, and they are published as
  one.
- **Translating their days-off constraints.** They are dropped, and the study says so and
  says what it costs: 14, 20 and 36 constraints on the three instances, every one of which
  their solver honoured.
- **Claiming this solver is better than theirs.** The comparison exists to test a
  reproduction claim, not a quality one.
- **A Belgian horeca corpus.** That is what capture and replay owns, and it stays blocked.
- **Encoding a constraint before measuring whether it matters.** A rule costs two
  independent readings and a measurement costs one.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Is their data committed?** No, fingerprinted
   ([`D-125`](../decisions.md#d-125)).

2. **Are their constraints encoded first, or measured first?** Measured
   ([`D-134`](../decisions.md#d-134)). The question was not *how do we encode this* but
   *does it matter here*, and the answer decided which of them became rules.

3. **Which published solution is the incumbent?** The best by their own objective
   ([`D-133`](../decisions.md#d-133)). Taking whichever one a directory listing returned
   made the incumbent a property of the machine, and it was that on 8 of 13.

4. **Is their hard-and-soft split adopted?** No
   ([`D-132`](../decisions.md#d-132)). Their instance is imported whole; their
   classification is theirs.

5. **Is the quality comparison withheld until it is fair?** No, published with its caveat
   ([`D-137`](../decisions.md#d-137)). A comparison whose unfairness is named and measured
   is worth more than one that waits.

---

*The ledger: [`README.md`](README.md). The study:
[`studies/foreign-incumbent.md`](../studies/foreign-incumbent.md). The rules it added:
[`guide/rules-statutory.md`](../guide/rules-statutory.md).*
