# Components and the ledger

The unit of work in this project is the **component**: one capability, specified before it
was built and reconciled against its code afterwards. This file indexes the components and
records what each one found.

*Assumes: the design argument in [`design.md`](../internals/design.md), and the working
contract in [`CLAUDE.md`](../../CLAUDE.md).*

---

## The ledger is reconstructed, and the specs are still here

The components were built from spec files in this directory, one per component, written
before the code and reconciled against it after. Those files are not here now, and nothing
was lost: on 2026-08-20 they were rewritten as the two live doors a reader actually uses
([`D-151`](../decisions.md#d-151)), because a spec that has been reconciled with its code
is a description of the system and belongs where people read about the system.

| The spec that owned it | Where it is now |
| --- | --- |
| `rules.md` | [`guide/rules.md`](../guide/rules.md) |
| `model.md`, `replan.md` | [`internals/model.md`](../internals/model.md) |
| `validation.md` | [`internals/testing.md`](../internals/testing.md) |
| `service.md` | [`guide/api.md`](../guide/api.md) |
| `capture.md` | Tier 0: specified and never built, so there is nothing to reconcile |

So the rows below are **reconstructed from evidence rather than copied from work orders**:
the tier scoping the plan set, the tables the finish declaration left, the studies, the
decision records, and the implementing commits the dates come from. A row is a claim about
what happened, and every claim in one links to the thing that holds it.

## In flight

A component here has no ledger row. A row records what was found, and an unbuilt component
has found nothing.

| Spec | Status | What it proposes |
| --- | --- | --- |
| *(none)* | | |

---

## The ledger

One row per component, oldest first. **Dates are the implementing commit's**; a range means
the component was revisited, and the second date is the last change that moved a finding.

The **finding** column is the point of the row: what the component established, including
where the answer was no, and including the six places a claim in this repository turned out
to be false.

| Component | Date | Where it lives | What it found |
| --- | --- | --- | --- |
| **Walking skeleton** | 2026-08-11 → 2026-08-20 | Deleted ([`D-146`](../decisions.md#d-146)) | Something solved inside the one-week cap on three rules and eight employees, which is all the gate asked. It then sat in the shipped package with nothing to do but be contradicted by [`rules.md`](../guide/rules.md), so it was deleted rather than kept as an example |
| **Rule registry** | 2026-08-12 → 2026-08-20 | [`guide/rules.md`](../guide/rules.md) | 26 rules with stable IDs, each carrying a provenance: a statute, a CBA, or nothing. Provenance is what the registry enforces: [`D-145`](../decisions.md#d-145) made every statutory rule name an instrument, and **two of the searches found no rule at all**, so those entries lost their legality claim rather than keeping an unsourced one. A granted day off turned out to be a rule rather than an interval ([`D-142`](../decisions.md#d-142)) |
| **The model** | 2026-08-12 → 2026-08-20 | [`model.py`](../../roster_replan/model.py), [`internals/model.md`](../internals/model.md) | Assignment booleans beat pattern variables ([`D-009`](../decisions.md#d-009)), and presolve removed a quarter of the model for 28% off build and 14% off search on 28 of 28 cases ([`presolve.md`](../studies/presolve.md)). Four levers measured and rejected: the `regular` automaton, pattern encoding, `no_overlap` rest gaps, symmetry breaking. **The optimum was degenerate**, so the reproducibility promise in `README.md` was false and no test could see it, because none looked at *which* optimum ([`reproducibility.md`](../studies/reproducibility.md), [`D-119`](../decisions.md#d-119)). **The last unmeasured rejection in the repo was measured and both its reasons were wrong**: size grows linearly and a longer horizon buys nothing ([`horizon.md`](../studies/horizon.md), [`D-116`](../decisions.md#d-116)). Where it stops is a number: about 40 employees over four weeks, 527 s of construction at 8M variables ([`D-127`](../decisions.md#d-127)) |
| **Checker, validation, and the correctness harnesses** | 2026-08-12 → 2026-08-14 | [`checker.py`](../../roster_replan/checker.py), [`validation.py`](../../roster_replan/validation.py), [`internals/testing.md`](../internals/testing.md) | Two readings of one registry, sharing a payload schema and never a threshold ([`D-003`](../decisions.md#d-003), [`D-038`](../decisions.md#d-038), [`D-039`](../decisions.md#d-039)), with the boundary enforced by an import contract. The differential harness compares violation *sets*, because comparing feasibility bits is vacuous once shortfall is representable ([`D-041`](../decisions.md#d-041)). Its limit is measured: **two rules were named for a week and measured over a horizon, and the harness could not have caught it**, because both readings were wrong in the same direction ([`D-111`](../decisions.md#d-111)) |
| **Disruption metric** | 2026-08-12 → 2026-08-14 | [`disruption.py`](../../roster_replan/disruption.py), [`scoring.py`](../../roster_replan/scoring.py) | Deviation from the incumbent rather than cost from scratch ([`D-005`](../decisions.md#d-005)), D0–D4 defined and D2 shipped ([`D-006`](../decisions.md#d-006)). The five definitions genuinely disagree, **on 10 of 84 cases and only D0–D2 against D3–D4** ([`disruption-metrics.md`](../studies/disruption-metrics.md), [`D-120`](../decisions.md#d-120)); within each side nothing separates them. Divergence needs slack, and is not monotone in it ([`D-060`](../decisions.md#d-060)) |
| **Mutation harness** | 2026-08-13 → 2026-08-17 | [`tests/mutation.py`](../../tests/mutation.py), [`mutation-harness.md`](../studies/mutation-harness.md) | Every mutant names the layer that must object, and one caught elsewhere is a miss ([`D-077`](../decisions.md#d-077)). **Four blind spots found behind fully green suites.** Five hardenings, each one the harness having been confidently wrong about itself: **canonicalising the optimum blinded two test layers and the harness is what noticed** ([`D-124`](../decisions.md#d-124)); **it reported `clean` with a mutated file in the tree** ([`D-112`](../decisions.md#d-112)), a survivor it did not have ([`D-139`](../decisions.md#d-139)), and **fourteen mutants it had never tested**, because CPython could not see the edit ([`D-141`](../decisions.md#d-141)) |
| **Benchmark: generator, committed set, four methods** | 2026-08-13 → 2026-08-14 | [`benchmarks/`](../../benchmarks), [`repair.py`](../../roster_replan/repair.py), [`benchmarks.md`](../benchmarks.md) | The set is defined by seeds and fingerprints, never by serialised payloads ([`D-073`](../decisions.md#d-073)), and nothing was filtered out of it ([`D-075`](../decisions.md#d-075)). The objective does the work: **the warm start is 9% of search time and invisible end to end** ([`warm-start.md`](../studies/warm-start.md)). **Greedy repair ties the optimum on 71 of 84**, which is the honest reading of a baseline that was expected to be weak ([`D-105`](../decisions.md#d-105)). There is no quality curve to draw: all 2,268 runs returned `OPTIMAL` ([`time-budget.md`](../studies/time-budget.md)). The distribution itself is a finding: **sampling the coverage axis only at its ends would have given the wrong answer** about pricing a hard rule ([`penalty-search.md`](../studies/penalty-search.md), [`D-128`](../decisions.md#d-128)) |
| **Capture and replay** | 2026-08-13 | Tier 0: **specified, never built** | The acceptance bar was fixed in advance of the first replay and there has been no replay ([`D-017`](../decisions.md#d-017)). Comparison is on observables, never on objective values ([`D-015`](../decisions.md#d-015)); pseudonymisation happens at capture and absence reasons are never written ([`D-016`](../decisions.md#d-016)). Blocked on an authorization outside this repository. It is still the largest single gap in the evidence (**the incumbent is solved by the system under test**) and [`foreign-incumbent.md`](../studies/foreign-incumbent.md) closed the half that was not blocked |
| **Job service** | 2026-08-13 → 2026-08-20 | [`service/`](../../roster_replan/service), [`guide/api.md`](../guide/api.md) | An async job queue over synchronous HTTP ([`D-010`](../decisions.md#d-010)), a stateless solver behind an in-process queue that is not ([`D-011`](../decisions.md#d-011)), round-robin fairness so one large tenant cannot starve the small ones ([`D-091`](../decisions.md#d-091)), and a fallback ladder where a timeout and an infeasibility are different answers ([`D-094`](../decisions.md#d-094)). The per-tenant compiled-model cache the spec asked for **got 0 hits in 144 solves** and was deleted, because a replan changes the model's own inputs ([`model-cache.md`](../studies/model-cache.md), [`D-149`](../decisions.md#d-149)) |
| **Explanation and minimal cores** | 2026-08-13 → 2026-08-18 | [`explain.py`](../../roster_replan/explain.py), [`prose.py`](../../roster_replan/prose.py), [`core.py`](../../roster_replan/core.py) | The explainer starts with shortfalls and answers from the checker ([`D-097`](../decisions.md#d-097)); the LLM phrases a proven finding and never identifies one ([`D-012`](../decisions.md#d-012), [`D-013`](../decisions.md#d-013)). **[`D-100`](../decisions.md#d-100) deferred core minimisation for a cause that was not the one that mattered**: the objective inflates the core, and deletion on top of that is a null |
| **Tool surface, hypotheticals, profile review** | 2026-08-13 → 2026-08-20 | [`service/tools.py`](../../roster_replan/service/tools.py), [`whatif.py`](../../roster_replan/whatif.py), [`profile.py`](../../roster_replan/profile.py) | `what_if` refuses unlawful hypotheticals rather than answering them ([`D-098`](../decisions.md#d-098)). Profile review is deterministic, and enabling a rule the model does not encode is a defect rather than a warning ([`D-099`](../decisions.md#d-099)). Two overrides of different provenance are not one ranking, and the sweep behind them was paying for the baseline twice ([`D-144`](../decisions.md#d-144)) |
| **NL → profile** | 2026-08-14 | [`nl.py`](../../roster_replan/nl.py), [`benchmarks/nl_eval.py`](../../benchmarks/nl_eval.py) | The schema is the confinement, and an open mapping is not a schema ([`D-101`](../decisions.md#d-101)); the eval scores what was invented, not only what was found ([`D-102`](../decisions.md#d-102)). **18/18 on three consecutive runs**, Dutch and adversarial cases included ([`nl-parse.md`](../studies/nl-parse.md)). **[`D-101`](../decisions.md#d-101)'s derogation field compiled to an object that could hold nothing**, and the reachability defect then repeated ([`D-131`](../decisions.md#d-131), [`D-138`](../decisions.md#d-138)) |
| **T5: fairness, generation, and two retirements** | 2026-08-14 → 2026-08-15 | [`disruption.py`](../../roster_replan/disruption.py), [`model.py`](../../roster_replan/model.py) | Two built, two retired on measurements already taken ([`D-104`](../decisions.md#d-104)). Fairness is a third meaning of the word here (a rolling balance of unpopular shifts, the one objective term with memory ([`D-108`](../decisions.md#d-108))) and generation ships as the cold-start case, with the spec's derivation of it wrong ([`D-109`](../decisions.md#d-109)). LNS is retired because it improves a solution the solver cannot prove optimal in time and neither half holds here. Learned warm starts are retired twice over: they would chase 9% of search time, and **the published rosters carry no signal to learn from at all** ([`weight-recovery.md`](../studies/weight-recovery.md), [`D-129`](../decisions.md#d-129)) |
| **Foreign incumbents and the cross-week rules** | 2026-08-15 → 2026-08-17 | [`benchmarks/foreign.py`](../../benchmarks/foreign.py), [`foreign-incumbent.md`](../studies/foreign-incumbent.md) | The headline claim reproduces on rosters this project did not produce, **by 4.6× to 37×** against about 5× on the committed set ([`D-125`](../decisions.md#d-125), [`D-137`](../decisions.md#d-137)). Foreign data found what a synthetic set could not: ten of thirteen published rosters have a past this model calls illegal, the first genuinely hard searches, and where the model stops. Their split of hard from soft is not this project's ([`D-132`](../decisions.md#d-132)) (four items catalogued here as preferences are hard constraints where those rosters come from) and their constraints bind hard when measured, breaking **every one of the seven** ([`D-134`](../decisions.md#d-134)). Seven became rules of this product ([`D-135`](../decisions.md#d-135), [`D-136`](../decisions.md#d-136)) |
| **Documentation restructure** | 2026-09-02 | [`documentation-restructure.md`](documentation-restructure.md), [`lint_docs.py`](../../scripts/lint_docs.py) | The documentation moves onto the shared discipline contract: no archive tier, this ledger, curated records, durable measurements, and a linter in CI. The disagreements between two projects that grew the same discipline separately were already settled in the plugin's own records, so nothing here was re-argued. **What the sweep found was worse than what it was called for**: eight dead `docs/specs/` links, a record count wrong by one, a status document four days stale, `CLAUDE.md` quoting a mutation run that had been superseded, a registry claiming 31 rules against 26, and a bare anchor the linter cannot see. Every one of them had sat behind a green suite. No claim, number or rule ID moved with the restructure itself, checked line by line |
| **Curating the decision records** | 2026-09-02 | [`decision-curation.md`](decision-curation.md), [`decisions.md`](../decisions.md) | 150 records read against a stated test for what earns one, and **137 kept**: 5 retired, 9 merged, 1 written. The estimate said 110 to 125 and **the pool it predicted was not a pool**: the records no live document cites are the T1 rule batch, each fixing a distinct predicate, uncited because the rules documents cite rule IDs rather than record links. **No record only restated a ledger row**, the criterion the unit was framed around, because the rows were reconstructed from the records. What was removable was records a later one had replaced, at the opposite end of the file. The read also found **a decision with no record at all**: the two-door split that two live documents were citing [`D-146`](../decisions.md#d-146) for, now [`D-151`](../decisions.md#d-151). No anchor was removed, so 324 inbound links and 558 internal ones still resolve |

---

## Where the detail lives

Each row is one line on purpose. The method and the numbers behind a finding are in the
study it links to; what was decided about it, and what was ruled out, is in the record.

---

*Every record: [`decisions.md`](../decisions.md), by [ID](../decisions.md#lookup) or [by theme](../decisions.md#by-theme). Every measurement, including the nulls: [`studies/`](../studies/README.md).*
