# Decisions

What was chosen, what was rejected, and why.

**Each record states its decision, not its analysis.**
Method, tables, sweeps and per-instance figures belong to the study, which every record links and every `D-0NN` reaches in one click.
The record says what was chosen, what was rejected, why, and what it forces elsewhere.
A record that restates its own study is how this file reached 49,000 words.

**The budget is 300 words, and the cap is 340.**
The cap is asserted in `tests/test_specs.py`, because the mean walked to 343 without one.
The figure is not arbitrary: editing thirty of the longest records down to their decision put every one
of them between 259 and 332 words, so that is what a record costs when it states its decision and links
its analysis.

**These records are curated.**
A record says what governs the code today.
One whose wording has gone stale is corrected in place; one that no longer earns a reader's attention is merged into the record carrying its argument, or retired.
Reasoning lives here rather than in a live document, where present tense squeezes it out.

What a record may not do is quietly change what it decided.
A record that supersedes another **names what it replaced and why the old reading was wrong**, and nothing is kept in a state known to be false.
An ID is never reused and never vanishes: what leaves this file leaves its anchor behind in [Merged and retired](#merged-and-retired), so every reference to it still resolves.

*Assumes: the terms of art in [`CLAUDE.md`](../CLAUDE.md); what each component found, in the [ledger](specs/README.md).*

---

# Index

Two ways in.
**Lookup** is the whole set in ID order; the titles carry the finding, so scanning them is usually enough to find the record you want.
**By theme** groups the records that make one argument together, which the ID order hides because IDs are chronological.
A record can sit under more than one theme: the grouping is not a partition.

**`T0`–`T5` are the tiers the original plan sequenced the work in**, and records use them because that
is what was decided at the time.
They appear nowhere else now: every other document says what it means instead.
Neither the plan that set the tiers nor the declaration that closed them is in the repository any more.

## Lookup

| ID | Record |
| --- | --- |
| [`D-001`](#d-001) | CP-SAT over MILP: measured, and not for speed |
| [`D-002`](#d-002) | Hard constraints structural rather than penalised |
| [`D-003`](#d-003) | Model and checker as independent implementations sharing no rule logic |
| [`D-004`](#d-004) | Brute-force enumeration as ground truth rather than trusting the solver |
| [`D-005`](#d-005) | Deviation-from-published as the objective, not cost-from-scratch |
| [`D-006`](#d-006) | D2 as the shipped disruption metric; D3 and D4 configurable |
| [`D-009`](#d-009) | Assignment booleans over pattern/column variables, measured |
| [`D-010`](#d-010) | Async job queue over synchronous HTTP |
| [`D-011`](#d-011) | Stateless solver, and an in-process queue that is not |
| [`D-012`](#d-012) | The LLM renders a finding it cannot alter, and a validator bounds what it may say |
| [`D-013`](#d-013) | Minimal core from the solver, prose from the LLM: never the reverse |
| [`D-014`](#d-014) | Horizon-boundary state supplied by the caller, not solved over a longer horizon |
| [`D-015`](#d-015) | Incumbent comparison on observables only, never on objective values |
| [`D-016`](#d-016) | Pseudonymisation at capture, and absence reasons never written |
| [`D-017`](#d-017) | The acceptance bar is fixed before the first replay |
| [`D-018`](#d-018) | `R-COVER` split into a hard ceiling and a soft floor |
| [`D-019`](#d-019) | Availability as interval intersection rather than whole-day blocking |
| [`D-020`](#d-020) | Absences non-relaxable, declared unavailability relaxable: one rule, two provenances |
| [`D-021`](#d-021) | Pins as assumption-literal equalities rather than build-time constant substitution |
| [`D-022`](#d-022) | Historical coverage shortfall excluded from the objective, reported separately |
| [`D-023`](#d-023) | `R-CONSEC-DAYS` reclassified operational/CBA: no statutory basis for adult workers |
| [`D-024`](#d-024) | Belgian rule implemented wherever it is stricter than the WTD |
| [`D-025`](#d-025) | `R-SKILL-MIX` class declared per entry, not per rule |
| [`D-026`](#d-026) | `R-SKILL-MIX` kept separate from `R-SKILL` to preserve presolve elimination |
| [`D-027`](#d-027) | Shift hours attributed wholly to the start day, never split at midnight |
| [`D-028`](#d-028) | Weekly rest as anchored candidate windows rather than time discretisation |
| [`D-029`](#d-029) | Weekly rest required inside the horizon: conservatism accepted over a heavier caller contract |
| [`D-031`](#d-031) | `R-MIN-SHIFT` reclassified input validation: not roster-violable under fixed shift instances |
| [`D-032`](#d-032) | Flexi eligibility and Dimona state resolved upstream, indexed per employee **per day** |
| [`D-033`](#d-033) | Flexi income ceiling folded into `max_hours_this_week`, not a parallel euro budget |
| [`D-034`](#d-034) | `R-FLEXI-ELIG` and `R-DIMONA-FLX` kept as separate IDs: different operator actions |
| [`D-035`](#d-035) | Conservative Dimona reading for same-day replan: only filed `OK` counts |
| [`D-036`](#d-036) | Per-contract administrative disruption deferred, and the D0–D4 study raised its value |
| [`D-037`](#d-037) | `span` and `work_hours` as separate symbols: no single `hours(d, s)` |
| [`D-038`](#d-038) | Independence scoped to rule logic; payload schema and stated conventions shared |
| [`D-039`](#d-039) | Rule thresholds never defaulted in shared code: payload carries every parameter |
| [`D-040`](#d-040) | Input validation and roster checking as separate layers with separate result types |
| [`D-041`](#d-041) | Differential harness compares violation sets, not feasibility bits |
| [`D-043`](#d-043) | `R-COVER` ceiling gated as `o == 0` so overstaffing is reportable, not merely rejected |
| [`D-044`](#d-044) | Model violations enumerated by maximising gate literals, not by iterating cores |
| [`D-045`](#d-045) | Presolve retains exclusion reasons; unrepresentable rosters compared on eligibility only |
| [`D-047`](#d-047) | Soft coverage floor collapses the infeasibility surface to pins and impossible parameters |
| [`D-049`](#d-049) | Weighted sum, not lexicographic ordering |
| [`D-050`](#d-050) | Exchange rate swept to trace the frontier rather than fixed by assertion |
| [`D-051`](#d-051) | Publication state as a single `published_through` cutoff, not a per-slot set |
| [`D-052`](#d-052) | `draft_weight` non-zero, for stable output and warm starts that resemble their hint |
| [`D-053`](#d-053) | D3 pairs drops with adds per (employee, day) so a move is one event |
| [`D-054`](#d-054) | D3 weights read from the day's anchor slot: solution-independent by necessity |
| [`D-055`](#d-055) | D4 as convex lower bounds rather than a max-term or a piecewise construction |
| [`D-057`](#d-057) | Shortfall-weight domination bound derived and validated, not chosen |
| [`D-058`](#d-058) | Variables exist for every incumbent pair, so deviations are always countable |
| [`D-059`](#d-059) | Eligibility fixings gated, so an ineligible assignment is reportable |
| [`D-060`](#d-060) | Metric divergence requires slack: the mechanism holds, the stated instrument does not |
| [`D-061`](#d-061) | Day-permutation invariance holds only on a day-decoupled cold instance |
| [`D-062`](#d-062) | Relaxation monotonicity excludes coverage, which changes the objective rather than the feasible set |
| [`D-063`](#d-063) | Suite-wide invariant realised as a shared helper, opt-out by construction |
| [`D-064`](#d-064) | Committed instances as Python constructors, not serialised: a schema is T2's problem |
| [`D-065`](#d-065) | Seven-day horizon throughout the micro set, rather than derogating weekly rest |
| [`D-066`](#d-066) | Threshold-bracketing instances for every rule limit, after mutation testing found the set blind |
| [`D-067`](#d-067) | Golden rosters recorded only where enumeration proves the optimum unique |
| [`D-068`](#d-068) | A benchmark case is a scenario: a published week and a disruption to it |
| [`D-069`](#d-069) | The incumbent is solved cold, not hand-built |
| [`D-070`](#d-070) | Tightness measured against presolved eligibility, not asserted by the parameter |
| [`D-071`](#d-071) | Low demand expressed by closing slots, not by thinning a full grid |
| [`D-072`](#d-072) | Student contracts omitted from the generator until `R-STUDENT-QUOTA` is encoded |
| [`D-073`](#d-073) | The benchmark set is defined by its seeds, not by serialised instances |
| [`D-074`](#d-074) | Two fingerprints per case, so a stale manifest says which layer moved |
| [`D-075`](#d-075) | Nothing filtered out of the committed set |
| [`D-076`](#d-076) | Classes differing only in the event share a base week |
| [`D-077`](#d-077) | Mutation testing as a committed harness, each mutant naming the layer that should catch it |
| [`D-078`](#d-078) | The greedy baseline is solver-free by contract, and its tie-break is stated |
| [`D-079`](#d-079) | Every method is scored on one yardstick, whatever it optimised |
| [`D-080`](#d-080) | The cost baseline keeps the incumbent attached and zeroes the change weights |
| [`D-081`](#d-081) | Search time is reported separately from end-to-end time |
| [`D-082`](#d-082) | The warm start helps, and only where the right clock can see it |
| [`D-083`](#d-083) | The committed set is not widened to manufacture a gap against greedy |
| [`D-084`](#d-084) | Benchmark results are not committed; the analysis is |
| [`D-085`](#d-085) | Metric divergence is measured as regret by lexicographic solve, not by comparing rosters |
| [`D-086`](#d-086) | D4 is unexercised by the committed set, and this is recorded rather than inferred |
| [`D-087`](#d-087) | Symmetry breaking measured and not shipped, because the distribution has no symmetry |
| [`D-088`](#d-088) | The `regular` automaton rejected at a one-week horizon, on speed and on reporting |
| [`D-089`](#d-089) | `R-REST-GAP` keeps pairwise inequalities at a one-week horizon |
| [`D-090`](#d-090) | The wire schema is its own schema, not a serialisation of the domain |
| [`D-091`](#d-091) | Round-robin fairness across tenants, not weighted |
| [`D-092`](#d-092) | `Instance.window` memoised: the largest single win in the solve path |
| [`D-094`](#d-094) | A timeout and an infeasibility are different answers, and `solve` now says which |
| [`D-095`](#d-095) | Finish declaration: name ratified, publication deferred |
| [`D-096`](#d-096) | The timing balance is committed and asserted; absolute milliseconds are not |
| [`D-097`](#d-097) | The explainer starts with shortfalls, and answers from the checker |
| [`D-098`](#d-098) | `what_if` refuses unlawful hypotheticals rather than answering them |
| [`D-099`](#d-099) | Profile review is deterministic, and enabling an unencoded rule is a defect |
| [`D-100`](#d-100) | The objective inflates the infeasibility core; minimisation is a null on top |
| [`D-101`](#d-101) | The parse is confined by the schema, and an open mapping is not a schema |
| [`D-102`](#d-102) | The parse eval scores what was invented, not only what was found |
| [`D-103`](#d-103) | `unclear` is for what could not be said, not for what was assumed |
| [`D-104`](#d-104) | Two of T5's four items are retired on measurements already taken |
| [`D-105`](#d-105) | The coverage axis is sampled where the answer changes, and every T2 analysis is re-measured over 84 |
| [`D-108`](#d-108) | Fairness is a third thing, and it pays for understaffing like everything else |
| [`D-109`](#d-109) | Generation ships as the cold-start case, and the spec's derivation of it was wrong |
| [`D-111`](#d-111) | The week rules are measured over a week, and the blind spot that hid it |
| [`D-112`](#d-112) | The mutation harness says `unverifiable` where it used to say `clean` |
| [`D-113`](#d-113) | The guard comes off for whole weeks, and stays on for part of one |
| [`D-114`](#d-114) | The timing guards are calibrated, so CI deselects them rather than widening them |
| [`D-115`](#d-115) | The generator takes a horizon, and its weekly pattern was a weekly pattern only by accident |
| [`D-116`](#d-116) | A longer horizon is rejected because it buys nothing, not because it costs too much |
| [`D-119`](#d-119) | The optimum is canonical, because the model should decide the roster and the search should not |
| [`D-120`](#d-120) | The D0–D4 divergence rate is 10 of 84, and the number it replaces was never robust |
| [`D-121`](#d-121) | CI goes back to linux, because the canonical optimum is a claim that needs a foreign binary to test |
| [`D-122`](#d-122) | The time-boxed rung is tested by handing the ladder a time-boxed answer, not by racing a budget |
| [`D-123`](#d-123) | The reference period gets its own rule, and the approximation it tests turns out to be free |
| [`D-124`](#d-124) | Canonicalising the optimum blinded two test layers, and the harness is what noticed |
| [`D-125`](#d-125) | Foreign rosters are fetched and fingerprinted, never redistributed |
| [`D-126`](#d-126) | The canonicalising phase can run out of budget, and says so instead of raising |
| [`D-127`](#d-127) | Where the model stops is a number now, and it bounds two earlier records |
| [`D-128`](#d-128) | Priced hard rules are measured, and the easy distribution gives the wrong answer |
| [`D-129`](#d-129) | Learning the soft weights is retired: the rosters carry no signal to learn from |
| [`D-130`](#d-130) | The mutation report records what a run cost, and a late write costs one layer |
| [`D-131`](#d-131) | The one cross-week term shipped without a way to reach it |
| [`D-132`](#d-132) | Their whole instance is imported, and their split of hard from soft is not ours |
| [`D-133`](#d-133) | Their objective is scored, it reproduces every published value, and the incumbent it exposed was machine-dependent |
| [`D-134`](#d-134) | Their constraints are read before they are encoded, and they bind hard |
| [`D-135`](#d-135) | Two of their constraints become rules of this product, hard and optional |
| [`D-136`](#d-136) | The rest of their constraint set, and the one rule that can refuse a roster |
| [`D-137`](#d-137) | The quality comparison exists, and its caveat is larger than its result |
| [`D-138`](#d-138) | The reachability defect repeated, and the harness caught it by refusing to start |
| [`D-139`](#d-139) | The harness reported a hole it did not have, and that is a fourth hardening |
| [`D-140`](#d-140) | A rule whose test could not have failed, and the two runs that proved it |
| [`D-141`](#d-141) | Fourteen mutants were never tested, because CPython could not see the edit |
| [`D-142`](#d-142) | A day off is not an interval, and that is a rule rather than a workaround |
| [`D-143`](#d-143) | A catch against a red catcher is not a catch, and CI found it before the harness did |
| [`D-144`](#d-144) | Two overrides of different provenance are not one ranking, and the sweep was paying twice |
| [`D-145`](#d-145) | Every statutory rule names an instrument, and two of the searches found no rule at all |
| [`D-146`](#d-146) | Four documents trimmed to what they carry, and the spec table made true |
| [`D-148`](#d-148) | The README draws the claim it used to only tabulate |
| [`D-149`](#d-149) | The model cache is deleted, because its key was a claim that went stale |
| [`D-150`](#d-150) | The guarantee starts at the payload, and the clock in front of it is the caller's |
| [`D-151`](#d-151) | The documentation becomes two doors, and the reconciled specs move into them |
| [`D-152`](#d-152) | `docs/specs/` holds work orders again, and the twelve are reconstructions |
| [`D-153`](#d-153) | The gates carry search, and a faster builder is not what would lift the ceiling |
| [`D-154`](#d-154) | The canonical optimum is not canonical, and the criterion is why |
| [`D-155`](#d-155) | Their coverage rule is a band and ours is a ceiling, and three rows of the scale table said so |
| [`D-156`](#d-156) | The performance work is closed on five nulls, and the reason is the regime |

## By theme

| Theme | Records |
| --- | --- |
| The objective: what disruption is, and what it trades against | [`D-005`](#d-005), [`D-006`](#d-006), [`D-015`](#d-015), [`D-018`](#d-018), [`D-022`](#d-022), [`D-036`](#d-036), [`D-049`](#d-049), [`D-050`](#d-050), [`D-051`](#d-051), [`D-052`](#d-052), [`D-053`](#d-053), [`D-054`](#d-054), [`D-055`](#d-055), [`D-057`](#d-057), [`D-060`](#d-060), [`D-085`](#d-085), [`D-086`](#d-086), [`D-120`](#d-120), [`D-129`](#d-129) |
| Formulation and solver choice | [`D-153`](#d-153), [`D-156`](#d-156), [`D-001`](#d-001), [`D-002`](#d-002), [`D-009`](#d-009), [`D-021`](#d-021), [`D-028`](#d-028), [`D-037`](#d-037), [`D-043`](#d-043), [`D-044`](#d-044), [`D-047`](#d-047), [`D-058`](#d-058), [`D-059`](#d-059), [`D-087`](#d-087), [`D-088`](#d-088), [`D-089`](#d-089), [`D-092`](#d-092), [`D-100`](#d-100), [`D-119`](#d-119), [`D-126`](#d-126), [`D-149`](#d-149) |
| Independence: two readings of one registry | [`D-003`](#d-003), [`D-038`](#d-038), [`D-039`](#d-039), [`D-040`](#d-040), [`D-041`](#d-041), [`D-045`](#d-045), [`D-063`](#d-063), [`D-078`](#d-078), [`D-128`](#d-128) |
| Ground truth, test layers, and the mutation harness | [`D-004`](#d-004), [`D-061`](#d-061), [`D-062`](#d-062), [`D-064`](#d-064), [`D-065`](#d-065), [`D-066`](#d-066), [`D-067`](#d-067), [`D-077`](#d-077), [`D-112`](#d-112), [`D-122`](#d-122), [`D-124`](#d-124), [`D-130`](#d-130), [`D-138`](#d-138), [`D-139`](#d-139), [`D-140`](#d-140), [`D-141`](#d-141), [`D-143`](#d-143) |
| Rules, legal encoding and provenance | [`D-018`](#d-018), [`D-019`](#d-019), [`D-020`](#d-020), [`D-023`](#d-023), [`D-024`](#d-024), [`D-025`](#d-025), [`D-026`](#d-026), [`D-027`](#d-027), [`D-029`](#d-029), [`D-031`](#d-031), [`D-032`](#d-032), [`D-033`](#d-033), [`D-034`](#d-034), [`D-035`](#d-035), [`D-111`](#d-111), [`D-123`](#d-123), [`D-135`](#d-135), [`D-136`](#d-136), [`D-142`](#d-142), [`D-145`](#d-145) |
| The benchmark set and its method | [`D-068`](#d-068), [`D-069`](#d-069), [`D-070`](#d-070), [`D-071`](#d-071), [`D-072`](#d-072), [`D-073`](#d-073), [`D-074`](#d-074), [`D-075`](#d-075), [`D-076`](#d-076), [`D-079`](#d-079), [`D-080`](#d-080), [`D-081`](#d-081), [`D-082`](#d-082), [`D-083`](#d-083), [`D-084`](#d-084), [`D-096`](#d-096), [`D-105`](#d-105) |
| Reproducibility and CI | [`D-154`](#d-154), [`D-096`](#d-096), [`D-114`](#d-114), [`D-119`](#d-119), [`D-121`](#d-121), [`D-124`](#d-124) |
| Explaining an answer: shortfalls, cores, hypotheticals | [`D-012`](#d-012), [`D-013`](#d-013), [`D-097`](#d-097), [`D-098`](#d-098), [`D-100`](#d-100), [`D-144`](#d-144) |
| The LLM boundary and profile configuration | [`D-012`](#d-012), [`D-013`](#d-013), [`D-099`](#d-099), [`D-101`](#d-101), [`D-102`](#d-102), [`D-103`](#d-103) |
| Service, runtime and the fallback ladder | [`D-010`](#d-010), [`D-011`](#d-011), [`D-090`](#d-090), [`D-091`](#d-091), [`D-094`](#d-094), [`D-122`](#d-122), [`D-149`](#d-149) |
| Horizon and cross-week reach | [`D-014`](#d-014), [`D-029`](#d-029), [`D-081`](#d-081), [`D-108`](#d-108), [`D-109`](#d-109), [`D-113`](#d-113), [`D-115`](#d-115), [`D-116`](#d-116), [`D-131`](#d-131), [`D-150`](#d-150) |
| The foreign instance | [`D-155`](#d-155), [`D-125`](#d-125), [`D-127`](#d-127), [`D-128`](#d-128), [`D-132`](#d-132), [`D-133`](#d-133), [`D-134`](#d-134), [`D-135`](#d-135), [`D-136`](#d-136), [`D-137`](#d-137) |
| Capture and replay (specified, not built) | [`D-015`](#d-015), [`D-016`](#d-016), [`D-017`](#d-017) |
| Scope, declarations, and the documentation itself | [`D-095`](#d-095), [`D-104`](#d-104), [`D-146`](#d-146), [`D-148`](#d-148), [`D-151`](#d-151), [`D-152`](#d-152) |

---

## Template

### D-000. Title

- **Decision.** What was chosen.
- **Alternatives.** What was considered and rejected.
- **Reason.** Why, in terms that survive without context.
- **Consequences.** What this forces elsewhere.
- **Study.** `docs/studies/...` if one exists.
- **Date.**

---

## Merged and retired

An ID is never reused and never vanishes.
A record **merged** had its argument moved into the record that carries it; one **retired** decides nothing any more, because what it decided is gone or a later record replaced it.
Every anchor stays here, so a link or a docstring citing one of these still resolves.

| ID | Where it went |
| --- | --- |
| D-007 | <a id="d-007"></a> Merged into [`D-049`](#d-049). The ID reserved the weighted-sum question, which was answered at T1. It carried a pointer and never a decision of its own |
| D-008 | <a id="d-008"></a> Merged into [`D-018`](#d-018). It ratified `D-018`'s provisional marking on measurement. The split and what measured it are one decision |
| D-030 | <a id="d-030"></a> Merged into [`D-040`](#d-040). `D-040`'s dividing question, stated a second time about one parameter |
| D-042 | <a id="d-042"></a> Merged into [`D-004`](#d-004). The two stages of the ground-truth layer belong to the record that owns the layer. The tier ordering that forced the split is spent |
| D-046 | <a id="d-046"></a> Merged into [`D-045`](#d-045). The smaller of the two comparison narrowings, by its own account. Both now sit in one record, and neither may be widened without a new one |
| D-048 | <a id="d-048"></a> Retired by [`D-100`](#d-100). It deferred core minimisation and named the wrong cause. The objective inflates the core; deletion on top of that drops zero gates |
| D-056 | <a id="d-056"></a> Merged into [`D-053`](#d-053). What D3 counts, including the change type fixed shift instances cannot express |
| D-093 | <a id="d-093"></a> Retired by [`D-149`](#d-149). The compiled-model cache it shipped enabled is deleted. The measurement that justified deleting it is in [`model-cache.md`](studies/model-cache.md), which is durable |
| D-106 | <a id="d-106"></a> Retired by [`D-120`](#d-120). Its coverage-axis curve is withdrawn: the divergence rate fell from 26 of 84 to 10 when the canonical optimum replaced every instance |
| D-107 | <a id="d-107"></a> Merged into [`D-105`](#d-105). One widening of the coverage axis and the re-measurement it owed |
| D-110 | <a id="d-110"></a> Merged into [`D-111`](#d-111). The horizon guard and the blind spot behind it. The finding survives in the record that closed it |
| D-117 | <a id="d-117"></a> Retired by [`D-121`](#d-121). The `machine` mark it put on the solved half of the manifest is gone, and [`D-119`](#d-119) removed the degeneracy it was written about |
| D-118 | <a id="d-118"></a> Retired by [`D-121`](#d-121). Both halves are spent. CI is on linux and `README.md` carries no *on the same solver build* qualifier |
| D-147 | <a id="d-147"></a> Merged into [`D-127`](#d-127). A scoping clause on a number belongs with the number |

---

## Open: to be written as they are made

Records leave this table as they are written.
What remains here is what is still owed.

| ID | Decision | Tier |
| --- | --- | --- |
| n/a | A `whatif.Change` kind for the hard rules that are **lawfully relaxable** and have none: `R-DAY-OFF`, `R-MAX-WEEKENDS`, `R-MIN-DAYS-OFF`, `R-MAX-SHIFT-TYPE`, `R-CONSEC-DAYS`: all operational/CBA, all carried on an employee's own data. `whatif.recommend()` already ranks people blocked by them and would test them as it tests R-SKILL, R-MAX-DAILY and R-MAX-WEEKLY today, but cannot build a `Change` for them. **Deliberately excluded, not merely unbuilt:** a declared absence under `R-AVAIL`, which `rules.md` splits by provenance precisely because an absence is never relaxable, and `R-REST-GAP`, where the lawful move is a recorded derogation rather than an override a solver may offer | T4 |
| n/a | **Policy-change analysis: what a tenant's new policy does before they adopt it.** `compare()` already answers it for one instance, and that is the trap: a verdict from a single week is a verdict about that week. The analysis owed is the aggregate: run the old and new profile over a **corpus** of weeks and report which rules newly bind and how often, how coverage and shortfall move, who carries the change (the fairness machinery from [`D-108`](#d-108) already measures this), and how many absences a week still absorbs before going short. `whatif.recommend()` contributes the finding no single what-if can: the rule a tenant keeps having to override, which is an argument about their skill matrix rather than a solver setting. **Blocked on `capture.md`**, specified and unbuilt: without real weeks this measures the generator. No cost axis either, while the rate is flat ([`D-050`](#d-050)) | T5 |

---

# Records

Written in batches, one batch per spec, and ordered here by ID so a reader can look one up directly.

<a id="d-001"></a>
## D-001. CP-SAT over MILP: measured, and not for speed

- **Decision.** CP-SAT. The MILP alternative is fully built in `benchmarks/milp.py` and reaches the
  same optimum on every committed case, so this record rests on a comparison rather than on a
  preference.
- **Alternatives.** Branch-and-cut MILP. Both SCIP 10 and CBC ship inside `ortools`, so the comparison
  needed no new dependency, and is therefore against **open-source** MILP, not Gurobi.
- **Reason.** **Not speed. Measured, CP-SAT loses**: SCIP proves the same optimum faster on 24 of 24
  cases. What CP-SAT provides instead is three capabilities this project already depends on and MILP
  cannot supply:

  1. **Assumption literals, and therefore infeasibility cores**: the object the explainer consumes.
     MILP has no assumption mechanism; an IIS is a different guarantee and `pywraplp` does not expose
     one.
  2. **`violations()`**: fixing every assignment and maximising true gate literals leaves exactly the
     violated constraints false, so one solve enumerates them all. Without it the model can only
     refuse a roster.
  3. **Non-linear expressiveness**: D3 and D4 pair changes through `min(drops, adds)`, which MILP
     needs auxiliary binaries and big-M for. `milp.py` refuses D3 and D4 rather than comparing a
     linearised approximation.

  The price is quantified rather than waved away: about **1.3 ms per solve**, against a model build
  costing ~5 ms regardless of backend.
- **Consequences.** The gating that buys capabilities 1 and 2 costs **21% of CP-SAT's search time** and
  half of its variables: 534 gate literals against 183 assignment variables on `headline/0`. That is
  the real price of the explainer, and it is a number rather than an intuition.

  One finding travels beyond this record: **MILP's default relative MIP gap is unsafe at this
  objective's scale and fails silently.** `pywraplp` defaults it to `1e-4`, and `shortfall_weight` is
  100,000 so that coverage dominates, so `1e-4` of a roster one shift short is about ten changed
  shifts, reported as optimal.
- **Study.** [`docs/studies/cp-sat-vs-milp.md`](studies/cp-sat-vs-milp.md)
- **Date.** 2026-08-12.

<a id="d-002"></a>
## D-002. Hard constraints structural rather than penalised

- **Decision.** Hard rules are encoded as constraints, not as large penalties in the objective.
  Infeasibility is a legitimate return value.
- **Alternatives.** Penalise every rule with a weight big enough that the solver avoids it: the
  formulation that never has to answer "no".
- **Reason.** A penalised legal rule produces a roster that is *cheaply illegal*, and cheaply illegal
  is not a state this service may return. It also destroys the differential harness: if nothing is
  hard, `checker_feasible` is universally true and the comparison is vacuous. And it moves every
  semantic claim into a weight nobody can falsify: a rule you can buy your way out of is a price,
  not a rule.
- **Consequences.** The service must be able to answer "nothing, and an explanation", which forces
  the assumption-literal machinery ([`D-044`](#d-044), [`D-100`](#d-100)) and the T4 explainer. It also forces the
  classification test to be applied honestly rule by rule, because "make it soft" is no longer a free
  escape from a hard modelling question. The one deliberate exception is `R-COVER`'s floor ([`D-018`](#d-018)),
  and what that costs is recorded in [`D-047`](#d-047).
- **Date.** 2026-08-12.

<a id="d-003"></a>
## D-003. Model and checker as independent implementations sharing no rule logic

- **Decision.** The rules are implemented twice: once as a CP-SAT encoding, once as plain Python
  over a returned roster, and the two are compared automatically on every run.
- **Alternatives.** One implementation, tested directly against expected outputs. A checker that
  reuses the model's predicates so the two cannot drift.
- **Reason.** Structurally required, not a nice-to-have. Under any formulation without
  hard-constraint guarantees: penalties inside a local search, or a time-boxed solve accepting a gap:
  feasibility is not guaranteed by construction, and independent verification is the only thing
  that makes a legality claim true rather than assumed. A checker that reuses the model's predicates
  verifies that the model agrees with itself, which is the one thing never in doubt.
- **Consequences.** The duplication is deliberate and has to be defended against well-meaning
  refactoring, so an import-linter contract enforces it in CI. Exactly where the line falls is
  [`D-038`](#d-038); what may never be shared is [`D-039`](#d-039). The checker is also what every other test layer
  asserts against ([`D-063`](#d-063)), so its independence is load-bearing for the whole suite rather than for
  the differential layer alone.
- **Date.** 2026-08-12.

<a id="d-004"></a>
## D-004. Brute-force enumeration as ground truth rather than trusting the solver

- **Decision.** On instances small enough to enumerate exhaustively, every roster is generated and
  scored by the independent readings, and the solver is required to agree.
- **Alternatives.** Trust CP-SAT's `OPTIMAL` status. Test the model against hand-computed expected
  answers.
- **Reason.** `OPTIMAL` means optimal *for the model as encoded*, which is precisely the thing under
  test: it certifies the search, not the formulation. A wrong threshold, an inverted inequality or a
  forgotten horizon boundary all produce a confidently optimal answer to the wrong question.
  Hand-computed expectations do not scale past a handful, and they encode the author's reading of the
  spec, which is the same reading that produced the bug.
- **Consequences.** Enumeration costs `2 ** (employees × open_shifts)`, so instances stay tiny and
  the bound is asserted by a test rather than left to review: an oversized instance would not fail,
  it would only make the suite slow, which is how enumeration layers quietly get deleted instead of
  fixed. It is blind to anything both readings take as data, which is what the golden layer exists
  for ([`D-067`](#d-067)). And it only covers the structures its instances contain, which is how a
  live objective bug survived it ([`D-058`](#d-058)).
- **The layer is two stages.** **(a)** the enumerated hard-feasible set equals the model's feasible
  set; **(b)** the solver's objective equals the enumerated optimum. (a) needs only the checker and
  catches the large majority of encoding errors: a wrong threshold, an inverted inequality, a
  forgotten horizon boundary. It is not a weaker version of the gate, it is the half that does not
  need preference to be defined. (b) needs a second independent reading of the **objective** for
  exactly the reason (a) needs one of the rules, so `scoring.py` evaluates the metric directly and is
  forbidden by contract from importing the model's encoding.
- **Absorbs `D-042`, 2026-09-02**, which split the layer when T1 scheduled this gate before the
  objective it needed.
- **Date.** 2026-08-13.

<a id="d-005"></a>
## D-005. Deviation-from-published as the objective, not cost-from-scratch

- **Decision.** The objective minimises how far the new roster departs from the published one. Cost
  is a second term traded against it, not the thing being minimised.
- **Alternatives.** Re-solve the week from scratch on a cost objective, which is what a scheduler
  normally does after a disruption.
- **Reason.** After a sick call the planner does not want the cheapest week, they want the cheapest
  *change*. A cost-optimal re-solve is free to rearrange people who were never affected, because cost
  cannot see that they had already been told. The product claim of this whole project is that the
  second-best roster nobody has to be re-told about beats the best roster everybody does.
- **Consequences.** The objective needs three inputs a cost objective does not: the incumbent, the
  publication state ([`D-051`](#d-051)) and `now`. It gives cold solves a degenerate case rather than a separate
  formulation: with an empty incumbent every change weighs the same and the objective falls back to
  cost. And it fixes the T2 comparison, since "cold re-solve on cost" is precisely the baseline this
  is measured against.
- **Date.** 2026-08-12.

<a id="d-006"></a>
## D-006. D2 as the shipped disruption metric; D3 and D4 configurable

- **Decision.** Five metrics D0–D4 are defined and encoded. **D2**: changed slots weighted by
  publication state and by notice: is the shipped default. D3 and D4 are configurable.
- **Alternatives.** Ship one metric and define no others. Ship the most detailed one, D4.
- **Reason.** All five are defensible, and the fact that they produce different rosters is the
  deliverable rather than a problem to settle: the T2 study exists to show it. D2 is the shipped
  choice because it is the simplest metric that prices the two things a planner actually reacts to:
  whether people were told, and how much warning they get. D3 and D4 add claims about human
  preference that are hypotheses rather than measurements, and a hypothesis is better shipped as an
  option than baked into the default.
- **Consequences.** Each metric contains the one before it: D1 with equal weights *is* D0, D2 with a
  flat multiplier *is* D1, which is what makes the study a clean comparison rather than five
  unrelated ideas. Every metric has to be scored independently, so `scoring.py` implements all
  five and not only the shipped one ([`D-004`](#d-004)). D2 reads `now`, so a golden test must pin `now` and
  not only the instance. And the metrics only diverge where there is slack, which is what makes
  coverage tightness T2's decisive generator knob ([`D-060`](#d-060)).
- **Date.** 2026-08-12.

<a id="d-009"></a>
## D-009. Assignment booleans over pattern/column variables, measured

- **Decision.** Assignment booleans `x[e, d, s]`. The pattern formulation is fully built in
  `benchmarks/patterns.py` so the comparison is against a real second formulation rather than an
  estimate, and it is not shipped.
- **Alternatives.** One boolean per (employee, legal weekly pattern), with coverage summing the
  chosen patterns, which makes every per-employee rule vanish from the model, because a pattern
  breaking one is never enumerated.
- **Reason.** It is competitive on a replan and **fails on a cold week**. On replans the two are within
  noise, and the reason is not the formulation: `now` sits on day 5, so five of seven days are pinned
  and there are only 36 to 122 legal patterns for a whole tenant. Solved cold, with the horizon open,
  the catalogue grows to 5,000–19,500 patterns, enumeration alone costs 0.4–6.7 seconds against a 20 ms
  assignment solve, and the pattern model **fails to prove optimality within 30 seconds on 5 of 6
  cases**. The second failure is the one that matters, because caching removes the first and not the
  second.
- **Consequences.** The mechanism is worth naming, because it ties two of these studies together: with
  no incumbent the objective is nearly indifferent, and thousands of near-identical columns give
  CP-SAT an enormous symmetric search space. **The pattern encoding creates the symmetry that [`D-087`](#d-087)
  found the assignment model does not have.** This is a result about *explicit enumeration*, not about
  column-based formulations in general: the standard answer is column generation, which needs an LP
  relaxation CP-SAT does not expose and would be a separate project. It also does not improve with a
  longer horizon: at a four-week reference period the enumeration is `4^28` rather than `4^7`.
- **Study.** `docs/studies/pattern-encoding.md`.
- **Date.** 2026-08-13.

<a id="d-010"></a>
## D-010. Async job queue over synchronous HTTP

- **Decision.** `POST /v1/replans` enqueues and returns `202` with a job id; `GET` polls; `DELETE`
  cancels. No endpoint solves inside the request.
- **Alternatives.** Synchronous HTTP, which is simpler and needs no job state. An event-driven design
  reacting continuously to roster changes.
- **Reason.** Synchronous works only for sub-second solves. At 30 s it produces timeouts, retries that
  re-trigger an expensive solve, request pile-up, no progress feedback and no way to cancel, and the
  retry storm is the dangerous one, because it multiplies exactly the load that caused it.
  Event-driven suits continuous replanning but makes *"why did my roster change?"* hard to answer,
  which is the question this project exists to answer well.
- **Consequences.** Measured, the premise is weaker than it looked: **nothing in the committed set
  takes more than 12.4 ms**, so at present sizes a synchronous endpoint would have been adequate and
  this is insurance against instance sizes the project does not yet serve. The insurance is cheap and
  the shape is hard to retrofit: a caller written against a synchronous API cannot be moved to
  polling without a version bump, so it stays. It is also what makes the fallback ladder's budget
  meaningful: a request that may take 30 s needs somewhere to put a partial answer.

  Cancelling a *running* solve marks the job and discards its result but does not stop the CPU work,
  which needs a solution callback wired through `model.solve`. Stated in `service.md` rather than left
  to be discovered under load.
- **Date.** 2026-08-13.

<a id="d-011"></a>
## D-011. Stateless solver, and an in-process queue that is not

- **Decision.** `run_job` takes a payload and returns a payload. No database reads anywhere in the
  solve path. The job store holds requests in memory, keyed by tenant.
- **Alternatives.** Let the solver read tenant profiles and rosters from a database directly, which
  removes a serialisation layer and a class of contract bugs.
- **Reason.** A solve that reads from a database cannot be replayed, and optimisation is close to
  undebuggable without replay: the input is large, the output is sensitive to every field, and "it
  returned something odd last Tuesday" is unanswerable unless last Tuesday's exact input is
  reconstructible. Every job therefore keeps its request, seed and profile version after completion:
  a job that has discarded its input cannot be replayed however good its telemetry is.
- **Consequences.** The distinction that matters is between the *solver* and the *queue*. The solver
  is stateless as specified. The queue is in-process, so replicas do not share it and a restart loses
  it: the honest limit of this tier, and a contained change: swapping the store for Redis or SQS
  touches nothing below `service/`, precisely because the solver reads nothing.

  Statelessness is also what makes the T2 benchmark machinery and the production path the same code.
  `benchmarks/methods.py` and `run_job` call the same solver with the same payloads, so a benchmark
  number is a claim about the deployed system rather than about a laboratory copy of it.
- **Date.** 2026-08-13.

<a id="d-012"></a>
## D-012. The LLM renders a finding it cannot alter, and a validator bounds what it may say

- **Decision.** The deterministic layer computes the finding (`explain.py`) *and* renders it
  (`prose.py`). An LLM is optional and may only rephrase. `prose.unsupported_terms` bounds what any
  rendering may contain: every employee name, rule ID and number must appear in the finding it came
  from, and the deterministic renderer is held to the same bound it would judge a model by.
- **Alternatives.** Hand the LLM the structured finding and let it write the sentence, checking the
  result by reading. Let it choose which blocked employees are worth mentioning.
- **Reason.** `PLAN.md` requires the LLM be confined to artifacts a deterministic layer can reject, and
  **"can reject" is the load-bearing half**: a rejection rule that cannot be executed is a review
  policy. Meaning is what a deterministic layer cannot judge; **vocabulary is what it can**. So the
  check is not whether the sentence is true but whether it mentions anything the finding does not
  support, which is decidable and catches an invented employee, rule or count.

  Building the renderer first is what makes the LLM optional rather than load-bearing: the feature
  degrades to "slightly better English" when no model is available, rather than to "no explanation".
- **Consequences.** The validator's first version flagged a token only if it was already a **real**
  employee name, which let a wholly invented `E99` through: the worse failure, since a fabricated
  person is less checkable than a real one named wrongly. It now treats anything identifier-shaped as a
  claim about the instance.

  Three things the renderer refuses to invent are [`D-013`](#d-013)'s rule applied to itself.
  **Weekdays**: there is no calendar by design, so `day 5` becomes `Sat` only when the caller supplies
  `weekday_of_day_zero`. **Shift names**: `label` is printed verbatim, because expanding `E` to
  `Evening` is right for this generator and wrong for a tenant whose `E` means something else.
  **Employee identity**: names come from the payload.
- **Date.** 2026-08-13.

<a id="d-013"></a>
## D-013. Minimal core from the solver, prose from the LLM: never the reverse

- **Decision.** The conflict is always identified by deterministic code. The LLM never decides *what*
  is wrong, only how to say it. Enforced by [`D-012`](#d-012)'s validator rather than by instruction.
- **Alternatives.** Let the model read the instance and diagnose the shortfall directly, which is
  what a general-purpose assistant would do and needs no explainer at all.
- **Reason.** A diagnosis is a claim about the world that a planner will act on: moving someone's
  Saturday, calling somebody in. A model that produces one is producing a claim nothing checked, and
  the failure mode is not obvious nonsense but a plausible, specific, wrong reason: *Ana is
  unavailable* when Ana is merely over hours. That is worse than no explanation, because it is
  actionable and wrong.

  The inversion this record forbids is the tempting one, because it is less work: the model is good
  at reading a payload and producing a fluent account of it, and the account is usually right. Usually
  right is the problem.
- **Consequences.** The rule now has machinery behind it rather than a paragraph. `explain.py`
  answers from the checker ([`D-097`](#d-097)), so the finding is independently derived; `prose.py` renders it;
  `unsupported_terms` rejects any rendering that adds a name, a rule or a number. A model that
  hallucinates fails the check rather than reaching a planner.

  It also constrains the tool surface T4 builds next: `explain_infeasibility` returns the structured
  finding alongside the prose, so a caller that does not trust the sentence can read the fields. The
  minimal-core reduction landed in [`D-100`](#d-100) and belongs to the *rare* case
  ([`D-047`](#d-047)); this record's machinery is what it renders through.
- **Date.** 2026-08-13.

<a id="d-014"></a>
## D-014. Horizon-boundary state supplied by the caller, not solved over a longer horizon

- **Decision.** Every rule whose true legal scope exceeds the one-week horizon takes its
  cross-boundary state as caller-supplied data: `max_hours_this_week[e]`,
  `last_shift_end_before_horizon[e]`, `consecutive_days_worked_before_horizon[e]`,
  `flexi_eligible[e, d]`, `dimona_ok[e, d]`. The solver and the checker see only those numbers.
- **Alternatives.** Extend the solve horizon to the legal reference period: a quarter, or a year.
  Reconstruct the history inside the service from its own store.
- **Reason.** Average weekly hours in Belgian law are measured over a rolling reference period
  (Arbeidswet art. 26bis §1), not per calendar week. A per-week ceiling is therefore not the rule but
  an approximation of it, and one that is wrong in both directions: it forbids a legal heavy week that
  a light week would compensate, and it permits thirteen consecutive weeks at the ceiling. Extending
  the horizon fixes that and multiplies instance size by an order of magnitude, destroying the
  interactive latency the whole service is built around.
- **Consequences.** Correctness now depends on a computation this service does not perform, and that
  cost is stated rather than hidden. The checker verifies assignments against the *supplied* budget
  and must never recompute it: a checker that reaches for the reference period is testing the caller,
  not the roster. Missing boundary state is a malformed payload and never a defaulted one, because the
  safe-looking fallback is precisely the wrong model this decision exists to avoid. `model.md` owns the
  input contract and names the caller as its owner. The same architecture is reused, there by necessity
  rather than by preference, in [`D-032`](#d-032).
- **Date.** 2026-08-12.

<a id="d-015"></a>
## D-015. Incumbent comparison on observables only, never on objective values

- **Decision.** A replayed record compares only externally observable outcomes: coverage shortfall,
  violations by rule ID, cost, disruption, solve time. The two systems' objective values are never
  compared. Both solutions are scored by **this project's** checker and metrics.
- **Alternatives.** Compare objective values directly. Fit a mapping from the incumbent's objective
  onto this one so the two become comparable.
- **Reason.** The incumbent's objective is unknown, differently scaled and differently weighted, so a
  table comparing the two numbers is measuring nothing while looking rigorous. Fitting a mapping is
  worse: it invents the very thing under test, and any conclusion then depends on a translation
  nobody can check.

  This is the same rule `methods.py` already applies inside the repo: every method scored on the
  shipped D2 yardstick whatever it optimised, because scoring each method under its own objective
  makes every comparison a tautology. [`D-015`](#d-015) is that discipline applied across an organisational
  boundary instead of within one, where it matters more because the other side's objective is not
  merely different but unavailable.
- **Consequences.** Scoring the incumbent with this project's checker means **the incumbent can fail
  it**. That is a finding to report, not a bug in the harness, and it is the most valuable thing an
  independent legality layer can produce, so the harness must not be built in a way that suppresses
  it or treats a violating incumbent as bad input.

  Results are paired per-instance deltas with win/loss/tie counts, never aggregate means. A mean
  hides the distribution that decides this: a substitute tying on ninety instances and losing badly
  on ten is not a substitute, and an average will not say so.

  Solve time is the one confounded metric and is marked as such rather than quietly compared, because
  the vendor's figure may include queueing and network time.
- **Date.** 2026-08-13.

<a id="d-016"></a>
## D-016. Pseudonymisation at capture, and absence reasons never written

- **Decision.** Employee identifiers become stable per-tenant surrogate keys at the moment of
  capture. Names, contact details and national registry numbers are never written. **Absence reasons
  are discarded**, retaining only the availability bit.
- **Alternatives.** Capture verbatim and pseudonymise at analysis or export time. Retain absence
  reasons under access control, on the grounds that they might inform a future model.
- **Reason.** Data that is never written cannot leak, and the timing is the whole decision: a
  pseudonymisation step at analysis time protects nothing about the window between capture and
  analysis, which is when a roster store is most exposed. And a roster store is an unusually rich
  target: it locates named individuals at specific places and times.

  Dropping absence reasons is the load-bearing half. A sick call is health data under GDPR Article 9,
  which carries obligations a benchmark corpus has no business taking on, and the optimiser never
  needed it: `R-AVAIL` reads an interval, not a cause. The cheapest privacy decision available, and
  only cheap because the domain model was already built without it.
- **Consequences.** **The "raw" layer is not verbatim, and `capture.md` said it was.** The two-layer
  scheme exists so the normalization can be shown faithful, and it describes the raw layer as
  "verbatim and immutable", which cannot hold once identifiers are replaced before anything is
  written. The spec is corrected: raw means *as received, after pseudonymisation and with nothing else
  altered*, with pseudonymisation named as the first of the documented losses.

  A stable per-tenant surrogate key is deliberately stable: an employee must be recognisable across
  records or a replay cannot measure disruption against them. The residual exposure: a stable key
  plus a shift pattern is re-identifying in a small tenant: is accepted rather than hidden.
- **Date.** 2026-08-13.

<a id="d-017"></a>
## D-017. The acceptance bar is fixed before the first replay

- **Decision.** The bar in `capture.md` is
  fixed in advance of the first replay: two absolute gates, then bars on the paired distribution. It
  changes only through a `decisions.md` entry, and never in response to a result.
- **Alternatives.** Set the bar once the distribution is known, which is what usually happens.
- **Reason.** A success criterion written after the numbers arrive is not a criterion: it is a
  description of the numbers. This project spends its credibility on measurements that could have
  come out the other way, and a movable bar retracts that at the one moment it matters most, on the
  only corpus that can test the headline claim against reality rather than against instances this
  project invented for itself.
- **Consequences.** Each clause exists to close a specific route, and the structure is the decision
  rather than the numbers:

  - **Two absolute gates**: zero checker violations, and no instance with worse coverage. Both are
    outcomes no distributional argument can compensate for: one violation breaks the legality claim
    the product is built on, and understaffing is what a planner notices within the hour.
  - **Parity and thesis are separate numbers**: no worse on ≥ 90%, strictly better on ≥ 50%. One
    figure cannot carry both, and T2 already produced the method that proves it: greedy repair ties
    the optimum on 64 of 72 cases, so it would clear a 90% parity bar while demonstrating nothing.
    The ≥ 50% clause is what that finding argues for.
  - **A cap on the losses**: worse by no more than 25% on the instances where it is worse. Without
    it the 10% allowance is unbounded and ten catastrophic losses pass a bar designed to exclude
    exactly that.
  - **Two time bounds**: p95 ≤ 1.5x the incumbent *and* ≤ 5 s. The relative bound alone is gamed by
    a slow incumbent; the absolute one is what the planner waiting for the answer experiences.
- **Date.** 2026-08-13.

<a id="d-018"></a>
## D-018. `R-COVER` split into a hard ceiling and a soft floor

- **Decision.** Coverage is one equality per shift instance, `Σ_e x[e, d, s] + u[d, s] = req[d, s]`
  with `u ∈ [0, req]` priced in the objective. Overstaffing is rejected outright; understaffing is
  permitted and priced.
- **Alternatives.** A hard equality, which is what the walking skeleton did. Both directions soft. Two
  inequalities rather than one equality with an explicit slack.
- **Reason.** The classification test asks what the service should return when the only
  otherwise-legal roster breaks the rule. For a coverage shortfall, "nothing, and an explanation" is
  the wrong answer: a disruption often has no legal repair, and *one short on Saturday, here is what
  it costs* is what a planner can act on. The ceiling can be hard for free: the all-zero roster
  satisfies it, so a hard upper bound can never be the sole cause of infeasibility.
  **Everything soft** makes `checker_feasible` universally true, so the
  differential harness asserts `true ⟺ true`. **Everything hard** leaves no shortfall representable,
  so there is no cost axis to trade disruption against.
- **Measured, not only argued.** Forcing every non-historical shortfall to zero, **a hard floor cannot
  answer 16 of the 72 committed cases**, and 18 of 84 once the coverage axis was widened
  ([`D-105`](#d-105)). The composition of the 16 is what settles it: **eight are weeks that could
  already be fully staffed before the event**, ordinary disruptions on healthy tenants. The other
  eight are the chronically short tenants a hard floor was never going to serve.
- **Consequences.** A fifth of this distribution would receive no answer at all. The equality with an
  explicit slack gives CP-SAT a tighter linear relaxation than two inequalities, and `u` is directly
  the coordinate the explainer reports. The shortfall weight must dominate every other soft term by
  the bound derived in [`D-057`](#d-057), and `validation.py` checks it. Leads to
  [`D-047`](#d-047).
- **Absorbs `D-008`, 2026-09-02**, which ratified this record's provisional T1 marking on the
  measurement above.
- **Date.** 2026-08-12, measured 2026-08-13.

<a id="d-019"></a>
## D-019. Availability as interval intersection rather than whole-day blocking

- **Decision.** `R-AVAIL` blocks `(e, d, s)` when the shift's half-open interval intersects a blocked
  interval: not when the absence falls on the same calendar day.
- **Alternatives.** Day-granular blocking, which is what `t0.py` does.
- **Reason.** Day equality is wrong in both directions. An unavailability of `Sat 09:00–12:00` must
  not block `Sat Evening`, and a `23:00–07:00` shift belongs partly to the next day.
- **Consequences.** Shift windows are computed from timestamps on both sides, and the checker
  recomputes them from the raw interval lists rather than consuming an eligibility mask from the model:
  the mask is the thing under test. Half-open overlap is a shared convention under [`D-038`](#d-038), so an
  unavailability ending exactly at a shift's start is not a conflict. This is the substantive
  correction to `t0.py`, which the rules spec supersedes rather than extends.
- **Date.** 2026-08-12.

<a id="d-020"></a>
## D-020. Absences non-relaxable, declared unavailability relaxable: one rule, two provenances

- **Decision.** `R-AVAIL` takes two caller-supplied interval sets, `absences[e]` and
  `unavailability[e]`. One rule ID, one predicate, two provenances carried through to what a human is
  shown: the checker's `Violation` records `absent` or `unavailable` in its `observed` field.
  `unavailability` becomes tenant-configurable to soft in T2; `absences` never does.
- **Alternatives.** Two rule IDs. A single `blocked` set that discards the provenance at parse time.
- **Reason.** The distinction is invisible to the solved model and matters only to what a human is
  told. A report blaming a declared preference is actionable: that person can be asked. One blaming an
  illness is noise. Two IDs would duplicate an identical predicate to buy a reporting difference.
- **Consequences.** Provenance has to survive into the reporting surface, so the two sets cannot be
  merged when the payload is parsed. An absent key means the empty set, and never means "unknown".
- **Superseded in part by [`D-059`](#d-059), 2026-08-13.** This record originally held that `absences` carry no
  assumption literal, "because there is no meaningful core containing *Ana is ill*". [`D-059`](#d-059) gates every
  eligibility fixing uniformly, absences included, so a pair that exists only to carry an incumbent
  assignment is gated either way. The original clause was written when both provenances presolved away
  and neither had a literal at all; it describes a distinction that only bites for pairs where a
  variable exists anyway. That case is reachable exactly when the incumbent's already-started past
  assigns an absent person: *the past itself is illegal*, which is a diagnostic worth having rather
  than permission to relax, and which is the framing the structural legal rules already use for their
  own literals. What is left in practice: the model's `Gate` descriptor does not distinguish the two
  provenances; only the checker's `Violation` does. Carrying provenance into the gate is a **T4
  explainer obligation**, recorded here so it is a known cost rather than a discovery.
- **Date.** 2026-08-12, amended 2026-08-13.

<a id="d-021"></a>
## D-021. Pins as assumption-literal equalities rather than build-time constant substitution

- **Decision.** `R-PIN-PAST` fixes `x[e, d, s] = x̄[e, d, s]` as a gated equality for every shift
  instance with `start(d, s) < now`, rather than substituting constants when the model is built.
- **Alternatives.** Substitute the constant at build time and never create the variable.
- **Reason.** Substitution is cheaper and makes *pinning is not exemption* automatic, but it destroys
  the ability to name the past as the source of a conflict. Because pins are equalities, an incumbent
  that already violates a rule makes the entire solve infeasible with no repair available: a real
  production scenario, reached whenever rules changed or a roster was hand-edited. The literals let the
  service distinguish **"the past itself is illegal"** from **"no legal future exists"**: two different
  messages, two different operator responses, and the first is invisible without them.
- **Consequences.** Pinned assignments are ordinary variables, so they stay inside every other rule's
  sums by construction: pinned hours consume the `R-MAX-WEEKLY` budget, pinned days count toward
  `R-CONSEC-DAYS`, and a pinned night shift ending at 07:00 constrains the following morning through
  `R-REST-GAP`. Treating the past as though it did not happen is the classic bug in this rule, and it
  produces rosters that are illegal precisely at the boundary nobody inspects. The cut-off is
  `start(d, s) < now` strictly: a shift in progress is past, because three hours of a night shift
  already worked cannot be un-worked. `now` and `x̄` are both caller-supplied and neither is derived; a
  replan carrying one without the other is a malformed payload. The encoding cost is expected to be
  small because CP-SAT presolve folds equalities well: **measured in the T2 presolve study, not
  assumed here.**
- **Date.** 2026-08-12.

<a id="d-022"></a>
## D-022. Historical coverage shortfall excluded from the objective, reported separately

- **Decision.** Shortfall on shift instances that started before `now` is excluded from the objective
  and reported separately as historical. The same applies to `R-SKILL-MIX` shortfall.
- **Alternatives.** Include it in the objective. Forbid it, by requiring the incumbent's past to be
  fully staffed.
- **Reason.** A past shift that was understaffed stays understaffed, and nothing in the horizon can
  fix it. Leaving it in the objective adds a constant that cannot be optimised away, and it makes two
  runs with different `now` values incomparable, which is exactly the comparison a replan study needs
  to make.
- **Consequences.** Both the objective encoding and the independent scorer need the `now` boundary,
  and each implements the exclusion separately. The shortfall is still reported, so it does not vanish
  from a planner's view along with its cost.
- **Date.** 2026-08-12.

<a id="d-023"></a>
## D-023. `R-CONSEC-DAYS` reclassified operational/CBA: no statutory basis for adult workers

- **Decision.** The rule stays in the registry; its legality claim does not. Provenance is operational
  and sectoral-CBA, and a tenant may switch the rule off entirely rather than only loosen it: the one
  rule among the structural legal set that may legitimately be disabled.
- **Alternatives.** Keep it as statutory with a citation attached. Drop the rule.
- **Reason.** The citation search surfaced that Belgian law sets **no general cap on consecutive
  working days for adult workers**. The commonly quoted figure of six derives from Arbeidswet art. 16,
  which requires compensatory rest for Sunday work *within the six days following that Sunday*: a rule
  about where compensatory rest lands, not a ceiling on consecutive days. The binding legal guarantee
  is `R-WEEKLY-REST` (art. 38ter §3), and it belongs there. Planners want the cap and sectoral
  agreements impose it, so the rule is worth encoding; the legality claim is not.
- **Consequences.** Tenant-configurable including *off*, unlike everything else in that section. Youth
  workers under 18 do have explicit statutory limits: out of scope for T1, and not this rule. This is
  the clearest case for requiring provenance before T1 closes: the rule was carried as
  `labour law [CITE]`, and only the search for the citation found that there wasn't one. A legality
  claim without provenance is a guess, and the checker is the component whose whole value is that it is
  not one.
- **Date.** 2026-08-12.

<a id="d-024"></a>
## D-024. Belgian rule implemented wherever it is stricter than the WTD

- **Decision.** Where the Arbeidswet and Directive 2003/88/EC differ, this project implements the
  Belgian rule. Each affected rule records where the divergence falls.
- **Alternatives.** Implement the WTD as a portable European baseline. Implement both and check the
  pair against each other.
- **Reason.** The Belgian rule is the binding one for the target tenants, and the stricter of the two
  cannot produce a WTD violation, so one implementation satisfies both, and the converse does not
  hold. The clearest instance is `R-WEEKLY-REST`: WTD art. 5 requires 24 uninterrupted hours plus
  art. 3's eleven, and art. 16(a) permits averaging that over a 14-day reference period; Belgium
  requires 35 *consecutive* hours and does not average. Implementing the WTD rule would leave rosters
  that are unlawful in Belgium.
- **Consequences.** Each rule records which of its parameters are national rather than European, so a
  future non-Belgian tenant knows exactly what has to move. Article numbers were checked against the
  consolidated statute rather than third-party restatements, which are frequently wrong: the FPS
  Employment summary attributes the three-hour minimum work period to art. 19 where the statute puts it
  in art. 21.
- **Date.** 2026-08-12.

<a id="d-025"></a>
## D-025. `R-SKILL-MIX` class declared per entry, not per rule

- **Decision.** Each `skill_mix` entry declares its own class, and a hard entry carries its own legal
  provenance string, validated non-empty at profile load.
- **Alternatives.** One class for the whole rule, as every other rule has.
- **Reason.** The classification test gives *different answers* for two entries of identical shape.
  "At least one first-aider" is operational and soft: a covered shift where nobody can do first aid is
  a real, priced operational state, and a planner must be shown it rather than handed an infeasibility.
  "At least one licensed nurse" is legal and hard: running the ward without one is not an expensive
  option, it is a prohibited one. Applying the test rule-by-rule forces one answer for both; applying
  it entry-by-entry is the only way it comes out right.
- **Consequences.** Soft entries get a slack variable and hard entries none, so the encoding branches
  on payload data rather than on the rule ID. Weights for soft entries sit at or above the `R-COVER`
  shortfall weight: an unqualified shift is at least as bad as a short one. Validation owns checking
  that a hard entry names its source, since the class travels in the payload rather than in the code.
- **Date.** 2026-08-12.

<a id="d-026"></a>
## D-026. `R-SKILL-MIX` kept separate from `R-SKILL` to preserve presolve elimination

- **Decision.** Two rule IDs and two encodings, even though `R-SKILL` is formally the special case
  `m = req[d, s]` of `R-SKILL-MIX`.
- **Alternatives.** Unify them under one counting constraint, since one is a special case of the other.
- **Reason.** `R-SKILL` is per-assignee and is enforced by *deleting* variables in presolve: the
  cheapest constraint in the model, and together with `R-AVAIL` it eliminates most of the grid.
  `R-SKILL-MIX` constrains a shift's *composition*, needs a counting constraint over the surviving
  variables, and cannot presolve away. Unifying them would trade the cheapest encoding in the model for
  the more expensive one and buy nothing but a shorter registry.
- **Consequences.** Two IDs, two encodings, one vocabulary. The checker implements the two counts
  independently even though both read `skills[e]`. In practice `R-SKILL` reaches a planner through
  `R-COVER` (scarcity surfaces as a priced shortfall) so the explainer reports skill scarcity
  alongside the shortfall rather than as a separate finding.
- **Date.** 2026-08-12.

<a id="d-027"></a>
## D-027. Shift hours attributed wholly to the start day, never split at midnight

- **Decision.** A shift instance's hours belong entirely to its start day. A `23:00–07:00` night shift
  is eight hours on `d` and zero on `d + 1`, for `R-MAX-DAILY`, `R-MAX-WEEKLY` and `R-CONSEC-DAYS`
  alike.
- **Alternatives.** Split the hours at midnight, in proportion to the time falling either side.
- **Reason.** It follows from shift instances being indexed by start day, and it has to be *stated*
  because a checker that split at midnight would disagree with the model on every night shift while
  both looked entirely correct in isolation.
- **Consequences.** `d` is a worked day for `R-CONSEC-DAYS` and `d + 1` is not, which is the intended
  reading: the night worker's Tuesday is mostly rest, and it is `R-REST-GAP` that protects it, not a
  fractional day count. The convention is shared between model and checker under [`D-038`](#d-038): it is a
  definition this project fixes, not a reading of the law, so two independent implementations of it
  would add no signal.
- **Date.** 2026-08-12.

<a id="d-028"></a>
## D-028. Weekly rest as anchored candidate windows rather than time discretisation

- **Decision.** Introduce `r[e, j]` for each candidate window `j`, require `Σ_j r[e, j] ≥ 1`, and for
  each shift instance overlapping window `j` add `r[e, j] ⟹ x[e, instance] = 0`. Candidates are
  anchored at `end(d, s)` for each shift instance, plus the horizon start.
- **Alternatives.** Discretise time and test a window at every tick. A `regular` automaton over the
  worked/not-worked sequence.
- **Reason.** Anchoring is sufficient, not merely convenient: any feasible rest window can be slid
  later until its left edge meets the end of some shift without shrinking below the threshold, so an
  anchored candidate exists whenever any window does. The candidate count is therefore `|O| + 1` and
  **not a function of time granularity**: no minute resolution has to be chosen, and no correctness
  claim depends on one.
- **Consequences.** `R-WEEKLY-REST` is the only T1 rule that is existential rather than a sum over
  assignments. The checker *measures* where the model *searches*, sort the assigned intervals, prepend
  `last_shift_end_before_horizon[e]`, take the maximum gap, which is what keeps the two readings
  independent for the one rule where sharing the construction would be most tempting. The automaton
  alternative expresses this rule and `R-CONSEC-DAYS` in a single propagator and is deferred to the T2
  encoding study, which should confirm that it beats the naive form at seven-day horizons rather than
  assume it.
- **Date.** 2026-08-12.

<a id="d-029"></a>
## D-029. Weekly rest required inside the horizon: conservatism accepted over a heavier caller contract

- **Decision.** The 35-hour rest block must lie **within** the horizon. A lawful roster whose block
  straddles the horizon's end is therefore rejected.
- **Alternatives.** A caller-supplied forward-looking commitment, symmetric with
  `last_shift_end_before_horizon`.
- **Reason.** On a seven-day horizon the conservatism is nearly harmless, since one such block must
  exist inside any week. The alternative obliges the caller to promise something about a week it has
  not planned yet: a heavier contract than the conservatism costs, and one that could not be honestly
  honoured at the moment a replan is requested.
- **Consequences.** It bites on shorter horizons, so short horizons are not a supported use case until
  that commitment lands. Recorded as known conservatism rather than left to be rediscovered as a bug
  report. The committed micro-instance set keeps a seven-day horizon throughout for this reason, rather
  than derogating the rule: see [`D-065`](#d-065).
- **Date.** 2026-08-12.

<a id="d-031"></a>
## D-031. `R-MIN-SHIFT` reclassified input validation: not roster-violable under fixed shift instances

- **Decision.** The minimum work period is checked over the tenant's shift catalogue at profile load
  and on every profile change, not over rosters. The roster checker does not implement it: the one
  intended exception to *every rule gets a checker encoding*.
- **Alternatives.** Keep it as the hard constraint the registry originally carried.
- **Reason.** With fixed shift instances it cannot be one. Shift types have durations defined by the
  tenant profile, and `x[e, d, s]` assigns a whole instance or none of it, so no roster the model can
  express contains a work period the catalogue does not already contain. A too-short shift is a
  **defect in the profile, not in the roster**, and a constraint that no reachable solution can violate
  is not a constraint, it is validation wearing one.
- **Consequences.** It becomes structural again in **T5 generation mode**, where shift boundaries turn
  into decision variables rather than data, at which point it needs a real encoding and a checker entry.
  Recorded so that transition is a known cost rather than a discovery. It reads gross `span` rather than
  net working time (see [`D-037`](#d-037)) because art. 21 governs the work period, and a "prestatie" containing
  a coffee break is still one period. There is no explainer case: a profile is rejected at load, before
  any solve exists to explain.
- **Date.** 2026-08-12.

<a id="d-032"></a>
## D-032. Flexi eligibility and Dimona state resolved upstream, indexed per employee **per day**

- **Decision.** `flexi_eligible[e, d]` and `dimona_ok[e, d]` are caller-supplied booleans indexed by
  day, mandatory for any employee on a flexi contract. Model and checker read the boolean and never
  derive it.
- **Alternatives.** Derive eligibility inside the service. Index the flag per employee rather than per
  day.
- **Reason.** Two separate arguments, and both are forcing. **Upstream, by necessity**: between them
  these rules depend on employment with *other* employers in quarter T-3 against a sectoral full-time
  reference, on a reduction from 100% in T-4 to 80% in T-3, on year-to-date earnings across employers,
  on sectoral opt-outs, and on a response the NSSO returns from its own records. A one-week payload
  contains none of it, and no amount of solver cleverness recovers it. **Per day, because quarters cut
  through horizons**: eligibility is retested each quarter and a Dimona may never cross a quarter
  boundary, so in the week containing 30 June and 1 July one employee can be eligible on Tuesday and
  ineligible on Wednesday inside a single solve. An employee-level flag gets exactly that week wrong,
  and it is the week nobody tests.
- **Consequences.** Correctness depends on a computation this service does not perform, stated the same
  way as the reference period in [`D-014`](#d-014). A missing flag for a flexi employee is a malformed payload,
  never a default of `true`. Both rules are enforced by presolve elimination into the same eligibility
  filter, which is what makes [`D-034`](#d-034)'s separation a deliberate choice rather than a side effect.
- **Date.** 2026-08-12.

<a id="d-033"></a>
## D-033. Flexi income ceiling folded into `max_hours_this_week`, not a parallel euro budget

- **Decision.** The annual flexi income ceiling enters as a fourth term in the `min()` the caller
  already computes for `max_hours_this_week[e]`.
- **Alternatives.** A parallel euro-denominated budget, with its own constraint in the model.
- **Reason.** The caller already converts a reference period into weekly hours; converting a remaining
  income allowance into remaining hours is the same kind of arithmetic against a known wage. It keeps
  one budget concept in the model instead of two, and the second would be another thing to keep
  consistent for no modelling gain.
- **Consequences.** The model never sees money, which keeps wage rules cleanly outside it: the horeca
  flexi hourly cap is recorded in the spec precisely so nobody mistakes it for a rostering constraint.
  The conversion's correctness sits with the caller, alongside everything else [`D-014`](#d-014) moved there.
- **Date.** 2026-08-12.

<a id="d-034"></a>
## D-034. `R-FLEXI-ELIG` and `R-DIMONA-FLX` kept as separate IDs: different operator actions

- **Decision.** Two rule IDs, even though both are presolve eliminations folded into a single
  eligibility filter and both consume a caller-supplied per-day boolean.
- **Alternatives.** One combined flexi-eligibility gate, since the encodings are identical.
- **Reason.** They fail for different reasons and produce different operator actions: *this person
  cannot hold a flexi job* versus *the paperwork is not in*. The second is fixable this morning; the
  first is not fixable at all. An explainer that conflates them sends the planner somewhere useless.
- **Consequences.** The presolve exclusion table records both reasons when a pair is excluded by both,
  so neither is lost behind the other. Identical encoding is not an argument for identical identity:
  the ID exists for the vocabulary, not for the constraint.
- **Date.** 2026-08-12.

<a id="d-035"></a>
## D-035. Conservative Dimona reading for same-day replan: only filed `OK` counts

- **Decision.** `dimona_ok[e, d]` is true only where a type-`FLX` declaration is filed and the NSSO
  returned `OK`. A filing that could still be completed in time does not count in T1.
- **Alternatives.** An optimistic reading, admitting substitutes whose filing could plausibly complete
  before the shift starts.
- **Reason.** The optimistic reading requires a judgement about NSSO turnaround that this service
  cannot make. The gate is real and it binds precisely where this project's headline scenario lives:
  under the verbal regime the filing names the day's start and end times, so replacing an absent flexi
  worker with another flexi worker requires a fresh `OK` before the substitute starts. For a Saturday
  sick call that materially narrows which substitutes are reachable, in a way that has nothing to do
  with availability or skill. A replan that ignores it proposes repairs that cannot legally be executed
  that morning.
- **Consequences.** `dimona_ok[e, d]` is not static within a horizon, and for a same-day replan the
  caller must distinguish *already filed* from *can still be filed in time*. The conservative reading may
  therefore reject repairs a human would make; whether that costs real repairs is answerable only
  against real incumbent decisions, and is deferred to the T2 capture and replay work. The filing
  deadline itself is unresolved: vendor guidance states 24 hours before start, the general statutory
  obligation is filing before work begins, and the two are not the same claim.
- **Related.** The asymmetry this creates: moving a flexi worker's shift requires re-filing, moving a
  salaried worker's requires nothing: is the externally grounded argument that a contract-weighted
  disruption metric is not arbitrary. That is [`D-036`](#d-036) and D3/D4 territory, and it is deliberately *not*
  a reason to change the shipped D2.
- **Date.** 2026-08-12.

<a id="d-036"></a>
## D-036. Per-contract administrative disruption deferred, and the D0–D4 study raised its value

- **Decision.** Not added to the metric. Changing a flexi worker's shift carries administrative cost a
  salaried change does not (same-day Dimona filing (`R-DIMONA-FLX`) is the clearest case) and this
  ID reserved the question of pricing that asymmetry. It stays out of D0–D4 and out of the shipped
  profile.
- **Alternatives.** Add a per-contract multiplier to the slot weight and include it in the D0–D4
  comparison as a sixth variant.
- **Reason.** It is not one of D0–D4 and adding it would have changed what that study measured. D0–D4
  nest (D1 with equal weights is D0, D2 with a flat multiplier is D1) which is what makes their
  comparison clean ([`D-085`](#d-085)). A contract multiplier is orthogonal to that ladder rather than another
  rung on it, so it belongs in its own study. More importantly the weight itself is unknown: how much
  administrative cost a same-day Dimona actually imposes is a fact about a tenant's back office, and
  inventing a number would make it look measured.
- **Consequences.** The D0–D4 study makes this **more** interesting rather than less, and the reason is
  worth recording because it is not obvious. D0, D1 and D2 turn out never to diverge on the committed
  set, because a disruption damages a *given* slot, so the publication and notice weights multiply
  every candidate repair by the same constant and a constant factor reorders nothing. A per-contract
  weight would not behave that way: it varies with **which employee** is chosen, and candidates differ
  precisely in that. So it is the one weight in this family that would genuinely change the answer on
  this distribution: unlike the two that ship.

  It needs the same evidence D3's `W_callin > W_cancel > W_move` ordering needs, which is
  capture-and-replay. Revisit with that corpus, not before.
- **Date.** 2026-08-13.

<a id="d-037"></a>
## D-037. `span` and `work_hours` as separate symbols: no single `hours(d, s)`

- **Decision.** A shift instance carries gross `span` and net `work_hours` as distinct symbols.
  `R-MIN-SHIFT` reads `span`; `R-MAX-WEEKLY` and `R-MAX-DAILY` read `work_hours`.
- **Alternatives.** One `hours(d, s)` symbol, as most rostering models have.
- **Reason.** Art. 38quater entitles a worker exceeding six hours to a break, and a break is not
  working time, so the two quantities genuinely differ, and the rules disagree about which one they
  want. Art. 21 governs the *work period*, and a "prestatie" may contain short meal or coffee breaks
  without becoming two periods, so the minimum-length rule wants gross span. The other two are
  working-time ceilings and want net.
- **Consequences.** One symbol would make one of those rules wrong by about a break per shift, some
  fifteen minutes, in a direction no test would notice until a checker and a model disagreed over it.
  `work_hours = span − break_hours` is a stated convention shared between the two readings under
  [`D-038`](#d-038).
- **Date.** 2026-08-12.

<a id="d-038"></a>
## D-038. Independence scoped to rule logic; payload schema and stated conventions shared

- **Decision.** The model and the checker share the payload schema and the stated conventions:
  half-open interval overlap, start-day attribution, `work_hours = span − break_hours`. They share no
  rule predicate and no rule parameter. Enforced by import-linter contracts in CI.
- **Alternatives.** The original phrasing, "they share no code".
- **Reason.** The original cannot be implemented as written: the differential harness must feed *the
  identical instance* to both readings, so both must be able to parse an instance, so something is
  shared. The line is drawn by what a shared item could hide. A **schema** bug corrupts both readings
  identically and the harness cannot see it, but neither can a schema hide a *rule* bug, which is what
  the harness exists to catch, and sharing is the only way the two readings are comparable at all. A
  **convention** is a definition this project fixes rather than a reading of the law; two independent
  implementations of the same convention add no signal, and a disagreement between them would be a bug
  in neither model nor checker.
- **Consequences.** Six import-linter contracts covering the checker, the model, input validation and
  the objective scorer, each asserting a direction of non-dependence. The parameter half of the rule is
  **not** linted (see [`D-039`](#d-039)) because no linter can tell a shared constant from a coincidentally
  equal one.
- **Date.** 2026-08-12.

<a id="d-039"></a>
## D-039. Rule thresholds never defaulted in shared code: payload carries every parameter

- **Decision.** Every numeric rule parameter (11 hours, 35 hours, 3 hours, 6 days) travels in the
  payload. No default for any of them lives in code that either reading can reach.
- **Alternatives.** A shared constants module holding the statutory defaults, which is where they would
  naturally go.
- **Reason.** A shared threshold is precisely the bug the brute-force and differential layers **cannot**
  detect, because both readings would be wrong in the same direction and agree perfectly while doing it.
  Every other class of rule bug shows up as a disagreement; this one shows up as silence.
- **Consequences.** Payloads are more verbose, and a missing parameter is a malformed payload rather
  than a silent statutory default. Because no linter can distinguish a shared constant from a
  coincidentally equal one, this is a standing **review obligation**: the one part of [`D-038`](#d-038) that CI
  does not enforce, and therefore the one most likely to decay.
- **Date.** 2026-08-12.

<a id="d-040"></a>
## D-040. Input validation and roster checking as separate layers with separate result types

- **Decision.** `validate_instance()` returns `InputDefect`; `check()` returns `Violation`. The two
  are never mixed in one list.
- **Alternatives.** One validation pass returning one list of problems, which is what most systems
  do.
- **Reason.** The dividing question is whether a different roster could fix the fault. If none could,
  it is input validation. Conflating the two is how a caller's arithmetic error gets reported as a
  solver defect. They also have different audiences: a caller fixes a defect, a planner reads a
  violation, and a single list forces both to filter it.
- **Consequences.** A non-empty defect list rejects the request outright and never degrades into a
  best-effort solve, because a request that is not well-formed has no meaningful optimum. Several
  rules land wholly or partly in the validation layer as a result: `R-MIN-SHIFT` entirely
  ([`D-031`](#d-031)) and `R-MAX-WEEKLY`'s budget bound, and the registry has to say so explicitly, or
  a reader looking for a checker encoding finds nothing and reads it as an omission.
- **The budget bound is the worked case.** That the supplied `max_hours_this_week[e]` does not exceed
  the absolute weekly ceiling is worth verifying, because a 60-hour weekly budget is a bad payload
  whatever the roster says. It is never reported as an `R-MAX-WEEKLY` violation: that would blame the
  solver for the caller's arithmetic while describing a roster perfectly legal against the budget it
  was given. This is the single place a well-meaning checker most reliably goes wrong. One that
  reaches for the reference period is testing the caller, and it will disagree with the model for
  reasons that are defects in neither.
- **Absorbs `D-030`, 2026-09-02**, which stated this record's dividing question a second time about
  one parameter.
- **Date.** 2026-08-12.

<a id="d-041"></a>
## D-041. Differential harness compares violation sets, not feasibility bits

- **Decision.** The harness asserts `checker_violations(r)` equals `model_violations(r)` as sets of
  `(rule, coordinates)`, and prints the rule ID on mismatch.
- **Alternatives.** Assert `model_feasible(r) ⟺ checker_feasible(r)`, which is what `PLAN.md`
  originally specified.
- **Reason.** Once a coverage shortfall is representable the feasibility comparison is vacuous: the
  empty roster satisfies every hard rule, so `checker_feasible` is nearly always true and the
  assertion collapses to `true ⟺ true`. Comparing violation sets also localises a disagreement to the
  rule that caused it, instead of reporting that two systems disagree about a whole roster and
  leaving someone to find out where.
- **Consequences.** The model must be able to *report* violations rather than merely refuse rosters,
  which is [`D-044`](#d-044), and which is the second independent reason the assumption literals are not
  optional. Two places where the readings genuinely differ in granularity had to be stated rather
  than papered over ([`D-045`](#d-045)) and neither narrowing may be widened without a record
  here.
- **Date.** 2026-08-12.

<a id="d-043"></a>
## D-043. `R-COVER` ceiling gated as `o == 0` so overstaffing is reportable, not merely rejected

- **Decision.** Overage gets its own variable `o[d, s]` under a gated `o == 0`, rather than being
  excluded by bounding the assignment sum inside the slack's domain.
- **Alternatives.** Fold the ceiling into `u`'s domain, which makes an overstaffed roster
  unrepresentable and costs nothing.
- **Reason.** An unrepresentable roster cannot be reported. The differential harness fixes a roster
  and asks the model what is wrong with it, so an overstaffed roster has to produce a *finding with
  coordinates* rather than an infeasibility with none. Same argument as [`D-059`](#d-059), one layer up.
- **Consequences.** One extra variable and one extra gate per shift instance. The checker
  independently recounts assignees and emits a violation for any instance over `req`, and must not
  read `u` from the solver: a checker that trusts the solver's own slack is verifying arithmetic,
  not coverage.
- **Date.** 2026-08-12.

<a id="d-044"></a>
## D-044. Model violations enumerated by maximising gate literals, not by iterating cores

- **Decision.** `violations(roster, instance)` fixes every assignment variable to the roster, then
  maximises the number of true gate literals. The literals left false are exactly the violated
  constraints.
- **Alternatives.** Read the infeasibility core. Iterate cores (drop each and re-solve) to
  enumerate all conflicts.
- **Reason.** With every assignment fixed, each gate can be true exactly when its own constraint
  holds, so one maximisation enumerates every violation at once. A core explains one conflict and
  hides the rest, which is precisely wrong for a harness whose job is comparing *complete* violation
  sets.
- **Consequences.** One solve per comparison instead of a loop of them. The function asserts that a
  fully fixed roster leaves the model feasible, which is a live check that every hard constraint
  carries a literal: an ungated constraint makes the model infeasible there, and the assertion says
  why. Presolved-away pairs never become variables and so can only be reported from the exclusion
  table, which is [`D-045`](#d-045) and is why that table is retained.
- **Date.** 2026-08-12.

<a id="d-045"></a>
## D-045. Presolve retains exclusion reasons; unrepresentable rosters compared on eligibility only

- **Decision.** Presolve keeps a map from each excluded pair to the rule IDs that excluded it.
  Rosters that assign such a pair are compared between the readings on **eligibility findings only**.
- **Alternatives.** Discard the reasons, since the variable is gone anyway. Compare those rosters in
  full and make the model account for the assignment somehow.
- **Reason.** A removed pair can never be reported by a constraint that does not exist, so without
  the map an assignment to an ineligible person is invisible rather than rejected. The comparison
  narrowing is larger than it first looks, and it took a failing test to state correctly: because the
  pair is not representable, the model cannot count that body toward **anything**: headcount, weekly
  or daily hours, a consecutive-day streak, a rest gap. Every aggregating rule is affected, not just
  coverage. The only thing the model has an opinion about is *why the pair was excluded*.
- **Consequences.** Nothing aggregate is compared on those rosters. The loss is bought back by
  comparing the two eligibility derivations directly: pair by pair, over every instance variant, for
  `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX`. That is a stronger test than the headcount
  comparison would have been, because it localises a disagreement to the eligibility rule that caused
  it rather than surfacing it as a coverage mismatch three rules away.
- **The second narrowing is `R-CONSEC-DAYS`, compared at `(rule, employee)`.** Both readings are
  right and report different things: the checker names the first breaching day of a run, the model
  gates every sliding window that breaches. Forcing agreement would mean rewriting one reading to
  imitate the other, which is the one thing independence forbids. Stated cost: a day-coordinate
  error in that rule is not caught. **Neither narrowing may be widened without a new record**, and
  together they are the whole of what the harness does not compare.
- **Absorbs `D-046`, 2026-09-02**, which called itself the smaller of the two.
- **Date.** 2026-08-12.

<a id="d-047"></a>
## D-047. Soft coverage floor collapses the infeasibility surface to pins and impossible parameters

- **Decision.** Recorded as a consequence of [`D-018`](#d-018) rather than as a separate choice: with the
  coverage floor soft, a cold solve is essentially never infeasible.
- **Alternatives.** None. This is a finding, and the alternative was not noticing it until T4.
- **Reason.** Once the floor is soft, the empty roster satisfies every hard rule, so a shift nobody can
  staff comes back as a priced shortfall rather than as a refusal. What remains able to produce
  infeasibility is narrow, and both causes are structural rather than combinatorial: an incumbent whose
  past already breaks a rule (`R-PIN-PAST`), and a parameter that no roster can satisfy at all, such as
  a weekly rest window wider than the horizon.
- **Consequences.** **This re-scopes T4.** The explainer's ordinary job is explaining *shortfalls and
  their cost*, not explaining infeasibility; infeasibility is the rare case, and an explainer built for
  the rare case first would be built for the wrong one. It also constrains the ground-truth layer: a
  micro-instance intended to be infeasible has to reach infeasibility through one of those two doors,
  because nothing else leads there.
- **Date.** 2026-08-12.

<a id="d-049"></a>
## D-049. Weighted sum, not lexicographic ordering

- **Decision.** Hard rules are constraints; shortfall, disruption and cost are summed with weights.
  Not a lexicographic ordering.
- **Alternatives.** Lexicographic (feasibility, then disruption, then cost) which guarantees
  disruption is never traded away.
- **Reason.** That guarantee is the problem. Under a lexicographic ordering no cost saving, however
  large, buys a single unit of disruption. This collapses the disruption/cost Pareto frontier to one
  point, and that frontier is the headline chart in [`benchmarks.md`](benchmarks.md). An objective
  that makes the money chart trivial is the wrong objective.
- **Consequences.** The weights have to sit on one scale, which forces the shortfall term to dominate
  by a derived bound rather than by a number that merely looks large ([`D-057`](#d-057)). The exchange rate
  becomes a parameter to sweep rather than a constant to defend ([`D-050`](#d-050)). Four levels result, and
  only two of them trade: hard rules are not in the objective at all, shortfall is priced and must
  dominate, and disruption and cost trade against each other.
- **Absorbs `D-007`, 2026-09-02.** That ID reserved this same question for T2 and was answered here
  at T1, so it carried a pointer and no decision of its own.
- **Date.** 2026-08-12.

<a id="d-050"></a>
## D-050. Exchange rate swept to trace the frontier rather than fixed by assertion

- **Decision.** `cost_weight` is swept across a range to trace the frontier. The shipped default is
  stated as a hypothesis with its reasoning attached, not presented as correct.
- **Alternatives.** Pick one exchange rate and defend it. Tune it until the output looks reasonable.
- **Reason.** The rate is a tenant's business judgement, not a fact about rostering. The honest claim
  is not "here is the correct exchange rate" but *"we cannot know yours; here is the frontier, and
  here is our default and why"*. Tuning until the output looks reasonable is the same act with the
  reasoning taken out, and it produces a number nobody can argue with because nobody knows where it
  came from.
- **Consequences.** The default: one published change at short notice is worth about two hours of
  overtime premium: is written down so it can be argued with. Calibrating it needs the T2 corpus:
  real planners choosing between paying overtime and moving someone reveal their own rate. Until
  then `cost_weight` ships at **0**, so the shipped objective is pure disruption and the cost axis
  only comes alive when a tenant sets it.
- **Date.** 2026-08-12.

<a id="d-051"></a>
## D-051. Publication state as a single `published_through` cutoff, not a per-slot set

- **Decision.** The caller supplies one number, `published_through`. A slot is published iff its start
  falls before it. Exactly parallel to `now`.
- **Alternatives.** A general set `published ⊆ O`, naming exactly which slots are out.
- **Reason.** One number is easy for a caller to get right, and it matches the pattern that actually
  dominates: *"the schedule is out through Sunday the 14th."* A per-slot set is more expressive and
  correspondingly easier to supply wrongly, and a wrong publication state silently misprices every
  change in the horizon.
- **Consequences.** Stated limit: a wave-published roster, some shifts in a horizon announced,
  others held back: cannot be represented. `published_through` is a special case of the general set,
  so the generalisation is additive when a tenant needs it. Publication state attaches to **slots
  rather than to assignments**, which is what makes an add cost anything at all: a published roster
  communicates rest as well as work, and being called in on a day off is among the most disruptive
  things a replan can do.
- **Date.** 2026-08-12.

<a id="d-052"></a>
## D-052. `draft_weight` non-zero, for stable output and warm starts that resemble their hint

- **Decision.** Changes to unpublished slots carry a small weight rather than zero.
- **Alternatives.** Zero, which is what "an unpublished draft can be reshuffled freely" literally
  implies.
- **Reason.** Zero leaves the optimiser indifferent among draft rosters, and indifference costs two
  things worth keeping: stable output across runs, and a warm start that resembles its hint. A small
  weight buys both and distorts nothing, because the number of assignments is pinned by coverage
  rather than chosen freely.
- **Consequences.** A cold solve is not indifferent either, which is what makes *generation is a
  replan from an empty incumbent* produce a stable roster rather than an arbitrary one. Ships at 1
  against a `published_weight` of 10.
- **Date.** 2026-08-12.

<a id="d-053"></a>
## D-053. D3 pairs drops with adds per (employee, day) so a move is one event

- **Decision.** Within an `(employee, day)`, `moves = min(drops, adds)`, and what is left over is
  priced as cancellations and call-ins.
- **Alternatives.** Count every changed slot on its own, as D0–D2 do.
- **Reason.** D0–D2 count a moved shift twice, once as a drop and once as an add. To the person it
  happened to it is one event: *"your Saturday moved from the morning to the evening."* D3 is the
  definition that notices.
- **Consequences.** Pairing needs a common granularity for the drop and the add, which is what forces
  the per-day weight in [`D-054`](#d-054). It also produces the worked divergence that makes the D0–D4 study
  real: where D2 calls a third person in for a morning (two changes), D3 prefers to move two people
  who were already working (four slots, but two *moves*). Both are defensible answers to the same
  disruption. The default ordering `W_callin > W_cancel > W_move` is a hypothesis about human
  preference, not a measurement, and it is the most falsifiable claim in the objective spec: T2's
  replay work tests it directly against what real planners chose.
- **`extend` is not a change type.** With fixed shift instances a shift's boundaries are data, so no
  roster the model can express extends one, and a change type no solution can exhibit is not a change
  type. It becomes representable in T5's generation mode and is a change type only there. Same shape
  as [`D-031`](#d-031): fixed shift instances remove a whole class of things the model can talk
  about, and both the rules and the objective have to notice.
- **Absorbs `D-056`, 2026-09-02.**
- **Date.** 2026-08-12.

<a id="d-054"></a>
## D-054. D3 weights read from the day's anchor slot: solution-independent by necessity

- **Decision.** In D3, `P` and `N` are evaluated per day, read from the day's earliest **open** shift.
- **Alternatives.** The day's earliest **affected** shift, which is the more intuitive reading.
- **Reason.** The intuitive choice is wrong twice over. The weight would depend on which slots the
  solution changed, which makes the objective non-linear. And it would be impossible to match between the
  model and an independent scorer, because one iterates variables and the other iterates changes.
  Solution-independence is not a nice-to-have here: it is what makes the two readings comparable, and
  without it stage (b) of ground truth cannot exist at all ([`D-004`](#d-004)).
- **Consequences.** Stated cost: a move from an early shift to a late one inside a long day is priced
  by the day's earliest notice rather than by the affected shift's. The anchor lives in `domain.py`
  as a shared convention for the same reason half-open overlap does: it is a definition this project
  fixes, not a reading of the rules ([`D-038`](#d-038)).
- **Date.** 2026-08-12.

<a id="d-055"></a>
## D-055. D4 as convex lower bounds rather than a max-term or a piecewise construction

- **Decision.** Introduce `t_e` and lower-bound it by every segment's line:
  `t_e ≥ k·events_e − k(k−1)/2` for `k = 1 … concentration_tiers`: then minimise `Σ_e t_e`.
- **Alternatives.** A max-term over the tiers. A general piecewise-linear construction with auxiliary
  booleans.
- **Reason.** A convex function of an integer variable needs no piecewise machinery when it is being
  minimised. Because `f` is convex and the objective pushes `t_e` down, `t_e` settles at exactly
  `f(events_e)`. Linear, no products, no auxiliary booleans. The max-term is the
  `concentration_tiers = 1` special case, and it is insensitive to everything below the maximum,
  which is the opposite of what a concentration penalty is for.
- **Consequences.** `f` is the triangular numbers, so the *n*-th change to one person costs *n*. The
  tier count is a parameter, so how far the escalation runs is configurable without touching the
  encoding. This is the answer to *five changes to one person is worse than one change to five*,
  which any plain sum over changes is blind to.
- **Date.** 2026-08-12.

<a id="d-057"></a>
## D-057. Shortfall-weight domination bound derived and validated, not chosen

- **Decision.** `shortfall_weight > max_{(d,s)} req[d, s] × max_change_weight`, computed from the
  instance and checked at profile load.
- **Alternatives.** Pick a large round number and assume it is large enough.
- **Reason.** Understaffing *reduces* disruption: an unstaffed shift is a shift nobody was moved
  onto. So a shortfall weight that is too low lets the optimiser buy stability by leaving shifts
  empty: a failure that looks like a tuning problem and is really an ordering error. The bound is
  computable, which is why it does not have to be guessed. Leaving one shift instance unstaffed
  avoids at most `req[d, s]` changed assignments, each worth at most the largest per-change weight
  the metric can produce.
- **Consequences.** Because it is derived it is checkable, so it is checked: a weight scale that
  violates it is a malformed request rather than a preference, and it lands in the input-validation
  layer ([`D-040`](#d-040)). `max_change_weight` is computed by the scorer and read by validation, which is why
  validation depends on `scoring.py` and not on the model. The same bound is what makes
  generation-as-cold-start safe: disruption is constant across rosters with equal coverage, and a
  shortfall is the only thing that could break that constancy.
- **Date.** 2026-08-12.

<a id="d-058"></a>
## D-058. Variables exist for every incumbent pair, so deviations are always countable

- **Decision.** A variable is created for every eligible pair, and additionally for any pair the
  incumbent assigned, eligible or not.
- **Alternatives.** Create variables only for eligible pairs, which is what presolve would otherwise
  dictate.
- **Reason.** Two separate things need the second case. An already-illegal past must be
  representable, or *the past itself is illegal* is indistinguishable from a clean solve. And a
  deviation from the incumbent must be **countable**: an employee who became unavailable has to be
  dropped, and that drop is disruption: without a variable the objective never sees it, and the
  model silently understates the cost of exactly the change the replan exists to make.
- **Consequences.** This was a live bug behind a green suite. Every micro-instance happened to have a
  clean incumbent, so the ground-truth layer passed while the objective was wrong; the regression
  instance is now committed. The general lesson is [`D-004`](#d-004)'s standing limit: a ground-truth layer
  only covers the structures its instances contain. A pair that exists only to carry a pin or a
  deviation is still ineligible, which is [`D-059`](#d-059).
- **Date.** 2026-08-12.

<a id="d-059"></a>
## D-059. Eligibility fixings gated, so an ineligible assignment is reportable

- **Decision.** Where a variable exists for an ineligible pair ([`D-058`](#d-058)), the exclusion is a gated
  `x == 0` rather than an outright fixing.
- **Alternatives.** Fix the variable to zero unconditionally, which is what "ineligible" plainly
  means.
- **Reason.** An outright fixing makes a roster that assigns the pair *infeasible* rather than
  *reported*, and the differential harness needs a finding with coordinates. Same argument as
  [`D-043`](#d-043).
- **Consequences.** The gate is reachable only through an incumbent pin, so a core naming an absence
  means *the past itself is illegal*: a diagnostic worth having. It partially supersedes [`D-020`](#d-020)'s
  claim that absences carry no assumption literal, and the amendment is recorded there. The model's
  gate descriptor still does not carry the absence-versus-unavailability provenance, which is a T4
  explainer obligation.
- **Date.** 2026-08-12.

<a id="d-060"></a>
## D-060. Metric divergence requires slack: the mechanism holds, the stated instrument does not

- **Decision.** Divergence needs room to choose, and coverage tightness is a real generator knob for
  it. But the quantity this record originally proposed to test it against: the instance set's
  week-level `min_slot_slack`: does not predict divergence and is not used for the claim.
- **Alternatives.** Report the week-level correlation as the confirmation. Drop the claim.
- **Reason.** The mechanism is confirmed where it is cleanest: `tight` diverges on 0 of 6 cases,
  because a fully constrained week has one legal repair and every metric returns it. But the
  week-level minimum is a minimum over 21 slots, and the repair happens at the one the event damaged:
  a week can hold one impossible slot and abundant room everywhere else. Measured that way the
  relationship is non-monotone and the most constrained bucket has the highest conflict rate, which
  is an artifact of the instrument. Measured at the damaged slot (`metrics.repair_slack`) it improves
  to 16/40 at high slack against near-zero below, and still is not a law.
- **Consequences.** **Slack is necessary and nowhere near sufficient.** The missing condition is
  structural: D3 diverges from D2 only when a *move* is available: another open shift on the same
  day that a rostered person could be shifted to, which is a property of the damaged day rather than
  of the week or the slot. The committed set does not vary it, so the study reports a correlation and
  not a law, and a generator axis over same-day shift availability is the honest way to close it.
  `demand-spike` diverging on 0 of 6 is the same point from the other side: an added headcount is a
  pure call-in with nothing to pair against, so no move exists to be preferred.
- **Supersedes.** The forward-declared version of this record, which assumed the week-level measure
  would serve.
- **Date.** 2026-08-13.

<a id="d-061"></a>
## D-061. Day-permutation invariance holds only on a day-decoupled cold instance

- **Decision.** The metamorphic day-permutation test asserts objective invariance only under stated
  preconditions: one shift type per day separated by more than `min_rest_hours`, no consecutive-day
  limit, weekly rest loose enough not to bind, and a **cold** solve.
- **Alternatives.** The original unqualified claim that day permutation "stays structure-consistent".
- **Reason.** The unqualified claim is false, and three separate couplings make it so. `R-REST-GAP`
  and `R-WEEKLY-REST` constrain adjacent and consecutive days. `R-CONSEC-DAYS` counts runs, and
  `{0,1,2}` is one run of three where `{0,2,4}` is three runs of one. D1 and D2 read publication state
  and notice from absolute start times, so permuting days reprices every change.
- **Consequences.** The preconditions are load-bearing and look like boilerplate, so the negative
  case is committed alongside: one employee and two *adjacent* days with `max_consecutive_days = 1`
  must leave a shift unstaffed, while the same two shifts moved apart can both be covered. That test
  exists so the preconditions cannot later be dropped as decoration. Employee relabelling, by
  contrast, is invariant unconditionally, and the difference between the two is the point of having
  both.
- **Date.** 2026-08-12.

<a id="d-062"></a>
## D-062. Relaxation monotonicity excludes coverage, which changes the objective rather than the feasible set

- **Decision.** The *monotone objective under relaxation* property test relaxes rules but never
  coverage.
- **Alternatives.** Include coverage among the relaxable rules, since it is one.
- **Reason.** Relaxing a rule expands the feasible set without touching the objective function, so
  the optimum can only improve or hold. Relaxing coverage changes the objective itself, through the
  shortfall term: it is not a relaxation in this sense, and comparing optima across it is
  meaningless rather than merely noisy.
- **Consequences.** A monotonicity suite in which every relaxation happened to be inert would pass
  vacuously, so one test asserts that at least one relaxation actually moves the objective. The
  property depends on relaxation being expressible at all, which is what the assumption literals buy
  under [`D-002`](#d-002).
- **Date.** 2026-08-12.

<a id="d-063"></a>
## D-063. Suite-wide invariant realised as a shared helper, opt-out by construction

- **Decision.** Every test that produces a solution goes through a `solved()` helper asserting zero
  **hard** checker violations and an `OPTIMAL` status. Soft violations are recorded, not asserted
  away.
- **Alternatives.** A pytest fixture or hook applying the assertion automatically to every test.
- **Reason.** Automatic enforcement cannot be opted out of, and some tests legitimately call the
  solver directly. A helper puts the opt-out in the test body, so bypassing the invariant is a choice
  someone can see in review rather than an absence nobody notices.
- **Consequences.** The `OPTIMAL` half matters more than it looks: a test comparing objectives across
  relaxations or against enumeration is meaningless on a time-limited `FEASIBLE`, and the failure
  would read as a wrong objective rather than as a truncated search. The invariant is why the
  checker's independence ([`D-003`](#d-003)) is load-bearing for the whole suite and not only for the
  differential layer.
- **Date.** 2026-08-12.

<a id="d-064"></a>
## D-064. Committed instances as Python constructors, not serialised: a schema is T2's problem

- **Decision.** The micro-instance set lives in `tests/micro_instances.py` as Python constructors.
  No JSON, no loader.
- **Alternatives.** Serialise the set, which is what "committed and versioned" usually implies.
- **Reason.** "Committed" here means fixed, and producing a readable diff, which a module already does. A schema and a
  loader are T2's problem, and they arrive there anyway alongside the versioned *benchmark* set that
  actually needs them. Building them now would be building a T2 artifact early and filing it under
  T1.
- **Consequences.** Instances are constructed with the domain types, so a schema change breaks them
  at import rather than at parse: the better failure, and an earlier one. The golden *record* is
  serialised, because it is data rather than construction, so the two choices are not in tension.
- **The prediction was wrong, 2026-08-13.** The benchmark set did not need a schema or a loader
  either. Generation is deterministic, so [`D-073`](#d-073) defines the set by its seeds and commits
  fingerprints rather than payloads, for the same readability reason this record gives. Serialisation
  is now owed to T3's API boundary, which needs it for its own reasons, and no earlier. The decision
  recorded above stands; only its guess about when the bill would arrive was wrong, and it is left in
  place because a prediction that failed is worth more visible than deleted.
- **Date.** 2026-08-13.

<a id="d-065"></a>
## D-065. Seven-day horizon throughout the micro set, rather than derogating weekly rest

- **Decision.** Every micro-instance runs a seven-day horizon, including those with only two open
  shifts.
- **Alternatives.** Use a three-day horizon matching the instance's real content, and lower
  `min_weekly_rest_hours` to suit.
- **Reason.** `R-WEEKLY-REST` requires its 35-hour window inside the horizon ([`D-029`](#d-029)), so on a
  three-day instance the rule binds everywhere for a reason belonging to the horizon rather than to
  the roster: the instance would be testing its own scaffolding. Lowering the parameter instead
  would demand a `derogation_basis`, and inventing a legal citation to quiet the validator is
  precisely the dishonesty the rule registry exists to prevent.
- **Consequences.** Free, because enumeration cost is `2 ** (employees × open_shifts)` and does not
  depend on the number of days. A convention that costs nothing and removes a whole class of
  misleading failure is worth stating rather than leaving to per-instance judgement.
- **Date.** 2026-08-13.

<a id="d-066"></a>
## D-066. Threshold-bracketing instances for every rule limit, after mutation testing found the set blind

- **Decision.** Five instances bracket their rule thresholds from both sides, added after
  deliberately breaking the model to see what the suite caught.
- **Alternatives.** Trust that an instance exercising a rule proves the rule is enforced.
- **Reason.** It does not. The three main shift types sit on an eight-hour grid, so every gap they
  can produce is 0, 8 or 16 hours, and a rest threshold of 9 hours is indistinguishable from 11.
  Lowering `min_rest_hours` in the model passed all 82 ground-truth tests. Probing each threshold in
  turn found the same blindness in the weekly budget and the daily maximum, whose limits sat far from
  any shift-count boundary, and in the gross-versus-net distinction, which only shows up for a budget
  in `[15.0, 16.0)`.
- **Consequences.** The generalisable lesson, and the reason this is a record rather than a commit
  message: **a fixture set proves a rule exists; only a fixture at the boundary proves it is enforced
  at the right number.** It also establishes the practice: a test layer is not done until it has
  been shown to fail on a deliberate break.
- **Date.** 2026-08-13.

<a id="d-067"></a>
## D-067. Golden rosters recorded only where enumeration proves the optimum unique

- **Decision.** The golden record commits objective values for every scenario, and the roster itself
  only where enumeration shows the optimum is unique.
- **Alternatives.** Commit every roster, which is what a golden layer normally means.
- **Reason.** Interchangeable employees create ties, and a tied optimum's *roster* is a function of
  solver version and search order rather than of the specification. Committing one would produce
  failures that are not defects, and would train everyone to regenerate without reading the diff,
  which destroys the only value the layer has.
- **Consequences.** Uniqueness is settled by enumeration at generation time, so the distinction is
  measured rather than guessed. The layer exists because stage (b) of ground truth is blind to
  anything *both* readings take as data: changing `published_weight` from 10 to 12 leaves both
  readings agreeing perfectly about a different optimum, and all 82 ground-truth tests pass. That is
  the class the golden record catches, verified by mutation rather than assumed: the weight change
  fails the golden layer and nothing else. Regeneration is a documented command rather than folklore,
  so the friction sits where it belongs.
- **Date.** 2026-08-13.

<a id="d-068"></a>
## D-068. A benchmark case is a scenario: a published week and a disruption to it

- **Decision.** The generator emits a `Scenario`: a base week, the incumbent solved from
  it, and the instance carrying a disruption event: rather than a bare `Instance`.
- **Alternatives.** Generate instances, and let the benchmark runner inject the events.
- **Reason.** A replan is a function of a published roster and something that went wrong with it
  ([`D-005`](#d-005)). An instance on its own cannot pose the question this project answers. Injecting events
  in the runner would also let the disruption vary independently of the week it lands on, so two
  methods could be compared on differently damaged weeks with nothing to show it had happened.
- **Consequences.** Generation runs in two phases and costs a solve per scenario, which puts a floor
  under how large the committed set can be. The scenario carries the base week as well as the replan
  instance, so the cold baselines have something to solve that never saw the incumbent, which is
  what makes "cold re-solve" a fair comparison rather than a straw man.
- **Date.** 2026-08-13.

<a id="d-069"></a>
## D-069. The incumbent is solved cold, not hand-built

- **Decision.** The base week is solved with the shipped profile and the resulting roster becomes
  `x̄`.
- **Alternatives.** Hand-construct incumbents. Build them with a greedy heuristic.
- **Reason.** A hand-built incumbent is easy or hard for reasons nobody chose, and it encodes the
  author's idea of what a published roster looks like: the same idea that produced the model.
  Solving it makes the incumbent legal and coverage-satisfying by construction, which is what a real
  published week is.
- **Consequences.** Stated cost, because it is the weak point of the whole benchmark: **the
  incumbent comes from the system under test.** It cannot be evidence that this model matches
  practice, only that a replan beats a re-solve *given* a roster this model would produce. Replacing
  it with captured rosters is exactly what `capture.md` exists to do, and this is
  the strongest argument for that work being scheduled rather than optional. The base solve can leave
  shortfall at high demand, so `base_shortfall` is recorded on the scenario rather than assumed zero.
- **Date.** 2026-08-13.

<a id="d-070"></a>
## D-070. Tightness measured against presolved eligibility, not asserted by the parameter

- **Decision.** `demand_ratio` is a generation *target*. What a scenario reports is measured after
  the fact (realised demand ratio, minimum slot slack, tight slots, and slots no roster can staff)
  computed over the pairs that survive `model.exclusions()`.
- **Alternatives.** Report the requested parameter. Measure slack against headcount.
- **Reason.** [`D-060`](#d-060) makes coverage tightness the knob that decides whether the D0–D4 study can see
  anything at all, so a nominal figure would quietly decide the study's answer. Availability density
  and skill scarcity both change how tight a week actually is, and neither is visible in the demand
  parameter. Headcount has the same fault one level down: two weeks with identical demand and
  identical staff are not equally tight if one of them cannot staff its evenings.
- **Consequences.** The measure imports the model's presolve. That is deliberate and is not an
  independence breach: tightness *describes* an instance rather than claiming what is legal, and the
  description that matters is the one the solver is working from. Requested and measured ratios
  differ by the rounding that turning hours into whole shift instances forces, so `benchmarks.md`
  reports the measured figure and the instance set records both.
- **Date.** 2026-08-13.

<a id="d-071"></a>
## D-071. Low demand expressed by closing slots, not by thinning a full grid

- **Decision.** When target demand falls below one person per shift instance, the generator opens
  fewer shift instances rather than keeping the whole grid open.
- **Alternatives.** Always open every `(day, shift)` pair and vary the required headcount.
- **Reason.** `O` is the set of pairs with `req > 0` ([`model.md`](internals/model.md)), so closing a
  slot is how low demand is actually expressed, and a small tenant genuinely does not run a night
  shift every day. The full grid also puts a floor under the achievable demand ratio: with 21
  instances at one body each, no scenario can be looser than that floor, which silently caps how
  loose the study is able to look.
- **Consequences.** Instance size now varies with tightness, so a solve-time comparison across
  tightness is partly a comparison across instance size, and the benchmark has to report both rather
  than attribute the difference to tightness alone. Guarded by a test asserting that measured
  tightness tracks the requested value across the range, which is what fails if the grid is forced
  open again.
- **Date.** 2026-08-13.

<a id="d-072"></a>
## D-072. Student contracts omitted from the generator until `R-STUDENT-QUOTA` is encoded

- **Decision.** The generated contract mix is flexi and salaried. No student share.
- **Alternatives.** Generate students now, as `benchmarks.md`'s parameter list implies.
- **Reason.** `R-STUDENT-QUOTA` is a profile-gated T2 rule and is not yet encoded, so a student share
  would move no constraint. A knob that does nothing makes the instance distribution look richer than
  it is, and a study run over it would report a null that is a property of the generator rather than
  of the problem.
- **Consequences.** The contract-mix axis is narrower than `benchmarks.md` originally described until
  the rule lands, and the spec now says so rather than leaving the gap to be found in the results.
  Adding students is additive once the rule is encoded: the flexi path already proves the per-employee,
  per-day eligibility shape the quota will need.
- **Date.** 2026-08-13.

<a id="d-073"></a>
## D-073. The benchmark set is defined by its seeds, not by serialised instances

- **Decision.** What is committed is a manifest of class names, seeds and fingerprints.
  Instances are regenerated on demand from `benchmarks/suite.py`.
- **Alternatives.** Serialise all 72 instances, which is what "committed and versioned" normally
  means.
- **Reason.** Generation is deterministic, so a class name plus a seed names an instance exactly.
  What that buys is a readable diff, and readability decides whether anyone looks: the same
  argument [`D-067`](#d-067) makes about golden rosters. Seventy-two serialised payloads produce a diff nobody
  reads, and a diff nobody reads is not review, it is a checkbox.
- **Consequences.** The set's stability now rests on the generator staying put, which is what the
  fingerprints and `GENERATOR_VERSION` are for ([`D-074`](#d-074)). No schema and no loader are needed, which
  contradicts the expectation recorded in [`D-064`](#d-064); that record is amended rather than rewritten.
- **Date.** 2026-08-13.

<a id="d-074"></a>
## D-074. Two fingerprints per case, so a stale manifest says which layer moved

- **Decision.** Each case records a `week` digest over the generated payload and an `incumbent`
  digest over the solved base roster.
- **Alternatives.** One combined digest per case.
- **Reason.** The two move for different reasons. `week` moves when the generator moves. `incumbent`
  moves when the generator moves *or* when the solver does: a CP-SAT upgrade, or a change to the
  objective encoding. A single digest says "something changed" and leaves the reader to work out
  what, which [`D-067`](#d-067) already names as the failure that trains everyone to regenerate without
  reading.
- **Amended by [`D-123`](#d-123): there is a third case, and this record calls it impossible.** A `week` hash
  moving while every `incumbent` holds (84 of 84 against 0 of 84) is what a **payload schema**
  change looks like: an optional field added to `Employee` alters the digest of every generated week
  while every solved roster, tightness figure and damage count stays identical. The reasoning below
  assumed the incumbent is solved *from* the week and therefore cannot hold while the week moves. It
  can, when what moved is the shape rather than the content, and that reading is worth having because
  it is the one case where regenerating changes nothing anybody measured.
- **Consequences.** A `week` hash holding while incumbents move is a solver change, and the
  instances stay comparable across it. Both moving is a generator change, and they do not.
  `GENERATOR_VERSION` carries the second case explicitly, and the manifest test fails when it is not
  bumped. The independence of the two is verified by moving each input on its own: counting distinct
  hashes across the set cannot show it, because the incumbent is a deterministic function of the week
  and the seed, so the two counts match whether or not one field is a copy of the other.
- **Date.** 2026-08-13.

<a id="d-075"></a>
## D-075. Nothing filtered out of the committed set

- **Decision.** Scenarios that guarantee a coverage shortfall, or whose base week is already short,
  stay in the set with that fact recorded per case.
- **Alternatives.** Drop them at generation time so that every committed case is a clean repair
  question.
- **Reason.** Filtering at generation prunes the distribution to the cases that flatter the thesis,
  and it does it invisibly: the resulting p95 is a p95 over a set somebody curated, and the stated
  distribution no longer describes what was measured. Which cases to exclude is an analysis
  decision, and it belongs in `benchmarks.md` where it can be argued with, not in the generator where
  it cannot be seen.
- **Consequences.** `base_shortfall`, `short_slots` and `damage` are recorded per case so the
  analysis can segment rather than pool. One class, `scarce-skill`, is chronically short by design,
  and results over it are reported separately: pooling a capacity question with a repair question
  averages two different things into a number that answers neither. The one property that *is*
  asserted is that every case poses a question at all: a scenario whose event damaged nothing scores
  as a flawless repair for all four methods and measures none of them.
- **Date.** 2026-08-13.

<a id="d-076"></a>
## D-076. Classes differing only in the event share a base week

- **Decision.** Classes that vary only the disruption event generate the identical published week at
  a given seed, and the set asserts it rather than relying on it.
- **Alternatives.** Let every class generate its own week.
- **Reason.** The property falls out of the event parameters not being read until the base week
  already exists, and leaving it accidental is the whole risk: if the base week ever came to depend
  on the event, a difference in results across events would be a difference in *instances* and
  nothing in the benchmark would say so. The event axis measures the event only if the week is held.
- **Consequences.** The same holds one axis over: `early-notice` is the headline week at a
  different hour, so the notice axis varies notice and nothing else. Both are asserted by test, and
  a mutant that seeds generation from the event name is caught by them.
- **Date.** 2026-08-13.

<a id="d-077"></a>
## D-077. Mutation testing as a committed harness, each mutant naming the layer that should catch it

- **Decision.** `tests/mutation.py` holds every deliberate defect this project has used to check a test
  layer. Each mutant names the layer expected to object, and one caught only by some *other* layer is
  reported as a miss rather than a pass.
- **Alternatives.** Keep it a habit. Point an off-the-shelf mutation tool at the whole codebase.
- **Reason.** **A habit is not evidence.** This repo already claimed every layer had been checked this
  way, and the claim was the only thing committed: the checks themselves were thrown away after each
  use, so nothing could be re-run and nothing could be reviewed.

  **Naming the expected catcher is what makes a result mean anything.** Run the whole suite against any
  mutant and something fails, which says nothing about whether the ground-truth layer can see a wrong
  threshold or whether the golden record can see a reweighted objective. Those are separate claims and
  they need separate answers. A general mutation tool buries the handful of mutants that encode a real
  hypothesis under thousands that encode none.
- **Consequences.** **Adding a test layer now means adding a mutant for it**: the harness is where a
  layer earns being trusted. It is deliberately outside the normal suite: it rewrites source files and
  takes minutes, so it runs when a layer is added or is about to be relied on.

  Its first full run found two holes behind a green suite: the differential harness could not see a
  wrong `min_rest_hours`, and [`D-057`](#d-057)'s bound had no test asserting it fires.
- **The restore has to be verified, not assumed.** A format-on-save watcher's delayed write can land
  *after* the restore, and did. The harness now verifies every touched path against git before exiting.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-13.

<a id="d-078"></a>
## D-078. The greedy baseline is solver-free by contract, and its tie-break is stated

- **Decision.** `benchmarks/greedy.py` is its own module, forbidden by an import-linter contract from
  reaching `model`, `disruption`, `scoring` or `ortools`. Its legality oracle is the checker. Its
  candidate order is written down: hours already rostered this week, then employee index.
- **Alternatives.** A function inside `methods.py`. Eligibility read from `model.exclusions()`.
  Whatever candidate order iteration happens to produce.
- **Reason.** The baseline's whole claim is that it is not the thing it is a baseline for. A baseline
  that consults the model inherits the model's bugs and stops being independent evidence, and a
  docstring saying "solver-free" is not a check. It cannot live in `methods.py`, which runs the three
  solver methods, so the contract needs a module boundary to attach to. The tie-break is stated for a
  different reason: "nearest-eligible" names an ordering that does not exist until somebody writes it
  down, and an undefined choice among equally eligible people makes the baseline's number
  irreproducible: a change to it would be indistinguishable from a change to the method.
- **Consequences.** `_legal` asks the checker only about the candidate's own assignments. Adding one
  person to one shift can break a rule about that person or overstaff the slot, and the slot is never
  filled past `required`, so the narrow question is the whole question: at a fraction of the cost of
  re-checking the full roster, which matters because this method's time is one of the reported
  numbers. The greedy loop's `is_past` skip turned out **not** to be a defence: `_legal` refuses a
  past slot anyway, because adding one is a `R-PIN-PAST` violation the checker names. The mutation
  harness established that by surviving, and the comment now says so, so that nobody later reads the
  skip as the thing protecting the past.
- **Date.** 2026-08-13.

<a id="d-079"></a>
## D-079. Every method is scored on one yardstick, whatever it optimised

- **Decision.** All four methods are scored with `scoring.score` under the scenario's own shipped D2
  profile. A method's own objective decides what it searches for and never how it is measured.
- **Alternatives.** Score each method under the objective it optimised.
- **Reason.** Scoring under its own objective makes the comparison a tautology: each method wins the
  axis it was pointed at, the cold cost solve reports zero disruption because its profile prices none,
  and the table says nothing. There is one comparison worth making and it requires one scale.
- **Consequences.** `cold-cost` optimises a profile with every change weight zeroed and is then
  measured on a profile that prices them at full weight, which is exactly the point: that is what
  "the status quo is disruptive" means. The invariant that makes the whole table checkable follows
  from the shared scale: the disruption solve is optimal, so no method may score below it on
  `Score.total`, and `test_optimum_dominates` asserts it per case. Comparing on total rather than on
  disruption alone is deliberate: greedy reaches a lower disruption on eight cases by leaving a shift
  unstaffed, and that is a different point on the frontier rather than a better answer.
- **Date.** 2026-08-13.

<a id="d-080"></a>
## D-080. The cost baseline keeps the incumbent attached and zeroes the change weights

- **Decision.** `cold-cost` solves the same instance, with `now` and the incumbent still attached,
  under a profile whose publication, move, cancel, call-in and concentration weights are all zero and
  whose `cost_weight` is 1.
- **Alternatives.** Solve with `incumbent=None` and `now=None`, which is the literal reading of "cold".
- **Reason.** Dropping the incumbent unpins the past. A baseline free to reassign shifts that have
  already started is not a legal roster and is not a baseline for anything, and dropping `now` also
  changes which shortfall counts as historical, so the two scores would no longer be on one scale.
  Zeroing the weights reaches the same place legitimately: the model, the coverage priority and the
  pinned past are identical, and exactly one thing differs, which is that deviation is free.
- **Consequences.** The baseline is **indifferent**, and that is the finding rather than a defect.
  The cost model is a flat rate ([`D-050`](#d-050)), coverage is an equality with a hard ceiling, so every fully
  staffed roster costs the same and CP-SAT returns whichever it reaches first. Measured across three
  solver seeds, its disruption moves by a median of 80 points and by as much as 260 on the same case,
  on 45 of the 72, so a single seed's number would have been an accident reported as a result. The
  disruption methods move by zero across the same seeds. Both figures are in `benchmarks.md`, and the
  seed sweep exists because of this record.
- **Date.** 2026-08-13.

<a id="d-081"></a>
## D-081. Search time is reported separately from end-to-end time

- **Decision.** `Solution` carries CP-SAT's own wall time, and every benchmark row reports it
  alongside the end-to-end measurement taken around the whole call.
- **Alternatives.** One stopwatch around `solve`.
- **Reason.** At T2 sizes a search is about 3 ms and building the model in Python is about 7 ms
  (**since reduced to about 5 ms by [`D-092`](#d-092); the figure is left as measured, and the conclusion is
  unaffected because build still dominates**), so
  an end-to-end number is mostly measuring model construction, which is identical for all four
  methods. The first version of this harness reported exactly that, and the four methods came out
  equally fast for a reason that has nothing to do with any of them. The warm start's effect is
  invisible on that clock and clear on the other.
- **Consequences.** Two columns, and they answer different questions. End-to-end is the latency T3's
  service owes a caller, and it is the number that says model construction is the bottleneck at this
  size, which is what the per-tenant compiled-model cache in T3 is for. Search time is the only one
  that compares one search against another.
- **The premise died and the decision did not, 2026-08-14.** [`D-119`](#d-119)'s canonicalising phase
  moved the committed `build/search` balance from 1.52 to **0.985**, so build no longer dominates at
  seven days, and [`D-127`](#d-127) bounds it by size: at 28 days search costs nearly three times
  build. Two clocks are still the right instrument, and the figures above are what they were when
  they were measured.
- **Date.** 2026-08-13.

<a id="d-082"></a>
## D-082. The warm start helps, and only where the right clock can see it

- **Decision.** `replan.md` asked for this result to be filed either way. It is not a null: the hint
  reduces search time on 201 of 216 paired runs, with a median paired ratio of 0.907. It is
  invisible end to end, and it never changes the answer.
- **Alternatives.** Report the end-to-end number, which shows nothing, or drop the hint as not worth
  its complexity.
- **Reason.** The claim `replan.md` warned against is a warm-start speedup that is really an objective
  effect. The cold *disruption* baseline separates them, and it is the comparison used here: same
  objective, same instance, same solver seed, hint or no hint. What is left is the hint, and it is
  worth about 9% of a 3 ms search.
- **Consequences.** A 9% saving on 3 ms is not the headline the phrase "warm-started replan" suggests,
  and `benchmarks.md` says so in those words. The effect that carries the results is the **objective**:
  the disruption profile cuts mean disruption from 323 to 66 against the cost baseline, and the hint
  is a rounding error beside it. The finding also has a T5 consequence: learned warm starts are
  chasing 9% of the smaller half of the latency budget, and that is worth knowing before building
  them. Whether the hint matters at sizes where search dominates construction is unanswered here and
  needs instances this set does not contain.
- **Date.** 2026-08-13.

<a id="d-083"></a>
## D-083. The committed set is not widened to manufacture a gap against greedy

- **Decision.** Greedy ties the optimal replan exactly on 64 of the 72 committed cases. That is
  reported as the result, and no harder scenario class is added in response to it.
- **Alternatives.** Extend the distribution with a high-damage class until the optimiser's advantage
  is visible in the headline average.
- **Reason.** The cases were committed before these numbers existed ([`D-073`](#d-073), [`D-075`](#d-075)), and adding a
  class *because* the existing ones do not flatter the thesis is the same act [`D-075`](#d-075) refuses at
  generation time, moved one step later where it is even harder to see. The honest statement is
  available and is more useful: on a one-week horizon where a disruption damages one to three
  assignments, calling the nearest eligible person is usually optimal, and the optimiser earns its
  place on the eight cases where the repair needs a chain the planner would not find: all of them in
  the tight, thin-availability, flexi-heavy or multi-absence classes, where greedy leaves a shift
  unstaffed that a chain would have covered.
- **Consequences.** The damage axis is now named as the one the distribution does not vary: median
  damage is 1 assignment and the maximum over all 72 cases is 3. A class that varies it is a
  legitimate future addition, and if it is added it is added as an axis with a stated range like every
  other, not as a repair to a disappointing table. The result also sharpens what the optimiser is
  *for* at this scale: not beating the planner on the common case, but never being the one to leave a
  shift uncovered, and being right on the case the planner cannot see.
- **The figure is superseded by [`D-105`](#d-105), 2026-08-14.** Greedy ties on **71 of 84** once the
  coverage axis is sampled where methods separate. What this record decides is the refusal to widen
  the set in answer to a disappointing table, and that stands.
- **Date.** 2026-08-13.

<a id="d-084"></a>
## D-084. Benchmark results are not committed; the analysis is

- **Decision.** `benchmarks/results.json` is generated and gitignored. What the repository carries is
  the analysis in `benchmarks.md`, the hardware and versions it was measured on, and the command that
  regenerates it.
- **Alternatives.** Commit the raw rows the way `benchmarks/manifest.json` is committed. Commit the
  summary table instead of the rows.
- **Reason.** The manifest is committed because a fingerprint is exact: it changes only when the
  instances change, so a diff to it is a signal. A results row carries wall-clock milliseconds, so it
  changes on every run and on every machine. A 750 KB file that always shows a diff is a file whose
  diff nobody reads, and [`D-067`](#d-067) is this repo's standing record of what that trains people to do.
  Committing the summary instead has the opposite fault: the summary embeds the segmentation choices
  `benchmarks.md` argues for, and a reader has to be able to redo them differently.
- **Consequences.** The numbers in `benchmarks.md` are backed by a stated command, a stated seed set
  and stated hardware rather than by a checked-in artifact, which is the honest position given they
  are timings. The comparisons meant to survive a change of machine are the paired ones: warm against
  cold, seed against seed, and they are reported as ratios for that reason. Anything that must be
  exact and produce a readable diff belongs in the manifest, which is where [`D-073`](#d-073) and [`D-074`](#d-074) put it.
- **Date.** 2026-08-13.

<a id="d-085"></a>
## D-085. Metric divergence is measured as regret by lexicographic solve, not by comparing rosters

- **Decision.** Two metrics are said to disagree on a case when holding one at its optimum makes the
  other strictly worse than its own optimum. The second solve minimises `b` subject to `a`'s
  objective equalling `V_a`, which selects the best `b`-roster among **all** of `a`'s optima.
- **Alternatives.** Solve under each metric and compare the returned rosters. Compare objective
  values.
- **Reason.** A metric usually has many optimal rosters, and which one is returned is the solver's
  search order. Comparing returned rosters reports 47 of 72 cases as divergent where only 23 are:
  D0's tie set is large enough that it would "disagree" with itself at another seed. The
  lexicographic form removes the ambiguity entirely: a positive regret means *no* optimum of `a` is
  an optimum of `b`, which is a fact about the metrics rather than about the search. This is the same
  failure [`D-080`](#d-080) records for the cost baseline, and it is worth having been caught twice.
- **Consequences.** Raw regrets are **not comparable across directions**, because D3 multiplies by
  change-type weights of 6 to 14 and D2 does not: the apparent 420-against-50 asymmetry in the matrix
  is units, and normalised against the paying metric's own optimum the disagreement is about even
  both ways. The study reports the normalised figure and says so. Every regret must be non-negative,
  which is asserted inline and independently in the test layer: a negative one means a solve is wrong,
  not that a metric is surprising.
- **Date.** 2026-08-13.

<a id="d-086"></a>
## D-086. D4 is unexercised by the committed set, and this is recorded rather than inferred

- **Decision.** D3 and D4 never conflict on any of the 72 cases, in either direction. The
  concentration penalty is reported as **unexercised** rather than as validated or as equivalent.
- **Alternatives.** Report the zero as evidence that D4 adds nothing. Drop D4.
- **Reason.** The penalty only becomes non-linear when two events land on the same person
  (`f(1)=1, f(2)=3`), and median damage across this set is one assignment. Even `multi-absence`, which
  removes three people, gives each of them one event. A zero here is therefore a fact about the
  distribution and says nothing about the metric: reading it as "D4 adds nothing" would be inferring
  a null from an experiment that could not have produced anything else.
- **Consequences.** Any claim that D4 behaves correctly rests on the micro-instances and the golden
  record, not on the benchmark set. The same damage axis [`D-083`](#d-083) names as missing is what would
  exercise it, which is the second independent reason to add one. Until then the study says so in
  those words.
- **Date.** 2026-08-13.

<a id="d-087"></a>
## D-087. Symmetry breaking measured and not shipped, because the distribution has no symmetry

- **Decision.** No symmetry breaking in the model. `model.md` said this was deliberate pending
  measurement; the measurement is now in [`studies/symmetry-breaking.md`](studies/symmetry-breaking.md).
- **Alternatives.** Ship lexicographic ordering over interchangeable employees.
- **Reason.** There is almost nothing to break. Across 24 committed cases there are **3**
  interchangeable employees in total, in one case. Lexicographic ordering therefore costs about 4% of
  build time and returns a coin flip on search. But the null had to be separated from "the lever does
  not work", so it was also run on a workforce built to be interchangeable, where it is worth **20% of
  total time**: 27% off the search, paid for with a 79% larger model. The lever works; this
  distribution does not present the structure it needs.
- **Consequences.** The spec's stated reason was **partly wrong and is corrected**. It attributes the
  suppression to the disruption objective, and the objective is the smaller half: the incumbent
  roughly halves what symmetry remains (7 interchangeable employees across six cold weeks, 3 across
  24 replans), but the larger effect is the generator giving every employee an independently sampled
  budget and availability, so two employees are rarely identical before any incumbent exists. That
  also bounds how far this null travels: a real tenant with eight part-timers on identical contracts
  and open availability would have genuine orbits, and this distribution does not model that tenant.
  Revisit when a tenant profile shows a substantial group identical in contract, skills, budget and
  availability.
- **Study.** `docs/studies/symmetry-breaking.md`.
- **Date.** 2026-08-13.

<a id="d-088"></a>
## D-088. The `regular` automaton rejected at a one-week horizon, on speed and on reporting

- **Decision.** `R-CONSEC-DAYS` keeps the sliding-window encoding. The automaton is implemented behind
  `build(sequence="automaton")` for the study and is not the shipped path.
- **Alternatives.** Adopt the automaton, which is the textbook encoding for a sequence rule.
- **Reason.** It loses on both axes. **Speed:** 20% slower to search on 24 of 24 cases, with an
  identical variable and constraint count, because at a seven-day horizon with a six-day limit the
  sliding-window encoding builds exactly **one** window per employee, so the automaton is competing
  against a single linear inequality over seven booleans. `model.md` suspected the window count would
  be small; it is one. **Reporting:** an automaton can carry an assumption literal: checked rather
  than assumed, since the API accepts calls it might not honour, but only one per employee for the
  whole week, where the window encoding names the *day* the streak breached. `violations()` compares
  gates to checker violations on the `(rule, employee, day, shift)` key, so adopting it would mean
  carving an exception into the harness that proves the two readings agree.
- **Consequences.** Revisit at a horizon longer than about two weeks, where the window count grows
  with the horizon and the automaton stays one constraint. That is not hypothetical for this domain:
  reference-period arithmetic is a multi-week rule ([`D-014`](#d-014), [`D-033`](#d-033)), but it is not the model that
  ships. `R-WEEKLY-REST` is not a candidate in either direction: it governs a continuous 35-hour free
  run measured in hours, which a day-level automaton cannot express.
- **Study.** `docs/studies/regular-constraint.md`.
- **Date.** 2026-08-13.

<a id="d-089"></a>
## D-089. `R-REST-GAP` keeps pairwise inequalities at a one-week horizon

- **Decision.** The pairwise encoding stays. The `no_overlap` alternative is implemented behind
  `build(rest="intervals")` for the study and is not the shipped path.
- **Alternatives.** One optional interval per (employee, shift instance), inflated by
  `min_rest_hours`, under a single `add_no_overlap` per employee: the alternative `rules.md` named
  and deferred to a T2 study.
- **Reason.** It trades search time for build time and the trade does not come out ahead. The interval
  form is 23% smaller and builds 12% faster, and searches 16% slower on 24 of 24 cases; the total is
  2% better on the committed set: the threshold the measurement harness itself calls not worth the
  complexity, and **11% worse** on the larger cold instances. A lever whose sign
  depends on which half of the latency dominates is not a lever. It also coarsens the gate: a
  `no_overlap` covers an employee's whole week, where the pairwise encoding names the second slot of
  the offending pair: the coordinate the checker reports and `violations()` matches on.
- **Consequences.** **The claim behind the alternative is untested, and the study says so rather than
  claiming a null.** `rules.md` justifies it by the pair set growing quadratically *as the horizon
  grows*, and this project's horizon is fixed at one week. The larger family varies employees, and
  employees are the wrong axis: conflicting pairs are computed over slots, so adding people
  multiplies both encodings equally. Revisit with a longer horizon, not with tenant size.

  Worth recording once across three studies: [`D-088`](#d-088), [`D-009`](#d-009) and this one all failed partly because
  **global constraints aggregate, and this model's gates are per rule instance**. Any encoding that
  replaces many local constraints with one global one coarsens what a failure can be attributed to,
  and that is a standing cost in a project whose T4 deliverable is an explainer.
- **Study.** `docs/studies/rest-gap-encoding.md`.
- **Date.** 2026-08-13.

<a id="d-090"></a>
## D-090. The wire schema is its own schema, not a serialisation of the domain

- **Decision.** `service/contracts.py` defines a parallel set of Pydantic models with explicit
  conversion in both directions. The domain dataclasses are never exposed at the boundary. A request
  Pydantic accepts but `validation.py` refuses becomes a job in state `rejected`, returned with `422`
  and readable at the same URL a result would have occupied.
- **Alternatives.** Serialise `domain.Instance` directly, or make the domain types Pydantic models.
- **Reason.** `service.md` asks for versioned contracts "so a model change never breaks a caller",
  and reusing the dataclasses defeats that in one step: every internal field becomes public API, and
  renaming an attribute becomes a breaking change for every caller. The cost is a parallel file and
  two conversion functions; the benefit is that `domain.py` stays free to change and the thing that
  must not change lives in a file whose only job is to not change.
- **Consequences.** Two things JSON cannot carry had to be decided rather than discovered. An
  unbounded notice band is `null`, because `NoticeBand.within_hours` is `inf` on the last band and
  `Infinity` is not valid JSON: a strict parser at a caller would have rejected our own output. A
  `Roster` is a list of triples in sort order, so two identical rosters serialise identically and a
  response body does not depend on set iteration order.

  **The round trip is the identity, and is tested as one over four committed instances and through
  the real serialiser.** This is not tidiness: `PLAN.md` requires every solve's input, seed and
  profile version to be persisted for replay, and a wire format that cannot express something the
  solver can breaks that guarantee *silently*: the payload still parses, it just describes a
  slightly different problem. A mutant that drops `unavailability` from the round trip is caught by
  that test and by nothing else.
- **Date.** 2026-08-13.

<a id="d-091"></a>
## D-091. Round-robin fairness across tenants, not weighted

- **Decision.** One queue per tenant and a rotation between them. Each scheduling turn takes one job
  from the next tenant that has one, so a tenant with 500 queued jobs gets one slot per rotation,
  exactly like a tenant with one.
- **Alternatives.** A single FIFO. Weighted scheduling by plan tier, contract value or queue age.
- **Reason.** `service.md` requires that "one large customer cannot starve two thousand small ones",
  and a FIFO fails it precisely when it matters: a tenant submitting 500 replans at 09:00 takes the
  next 500 slots. Weighting was rejected for now because a per-tenant weight needs a priority nothing
  in this project can justify: plan tier, contract value and queue age are all defensible and none
  is derivable from a payload. Equal shares is the honest default, and inventing a weighting to look
  sophisticated would encode a business decision nobody made.
- **Consequences.** `next_batch` is where a weight goes when there is a reason for one, and the
  rotation is the only thing that would change. Fairness is a claim about *scheduling* and cannot be
  observed in any single response, so it is asserted directly against the rotation rather than
  through the API: a FIFO passes every other test in `test_service.py` and fails only that one. The
  mutation harness carries a mutant that turns the rotation back into a FIFO.
- **Date.** 2026-08-13.

<a id="d-092"></a>
## D-092. `Instance.window` memoised: the largest single win in the solve path

- **Decision.** `Instance.window` caches its results per `(day, shift)` in a field excluded from
  `init`, equality and `repr`.
- **Alternatives.** Leave it pure and pursue the compiled-model cache `service.md` asks for. Hoist the
  computation into each caller.
- **Reason.** Profiling `build` put **60% of its time in this one method**: about 3,474 calls per
  build to compute the 21 distinct values a one-week horizon with three shift types has. Since build
  (~5 ms) costs more than search (~3 ms) at these sizes ([`D-081`](#d-081)), that made it the largest single
  cost in the whole solve path. It takes about **20% off build time**, measured on a cold cache per
  build: the saving is collapsing 3,474 calls to 21 *within* one build, not reuse across requests, so
  it is a production win rather than a benchmark artifact. That is larger than presolve, larger than
  the warm start, and larger than every level-1 lever in T2: all of which compared *encodings*, which
  is why none of them could see it.
- **Consequences.** Safe without invalidation: `window` is a pure function of `(day, shift)` and
  immutable shift types, and `Interval` is frozen, so a shared instance is indistinguishable from a
  fresh one. This is the only thing in `domain.py` that is neither a data container nor a stated
  convention, and it earns the exception by being the largest measured cost in the project.

  **It broke the benchmark manifest immediately, and that is the guard working.** `suite.py`
  fingerprints instances by walking `dataclasses.fields`, so the cache leaked into every committed
  hash and made it depend on which methods had been called first. `_canonical` now walks only fields
  with `compare=True`: a field excluded from `__eq__` must be excluded from a fingerprint, or two
  equal objects hash differently. The manifest then reproduced byte-for-byte, which is also the
  cleanest evidence that memoisation changed no instance.
- **Study.** `docs/studies/model-cache.md`.
- **Date.** 2026-08-13.

<a id="d-094"></a>
## D-094. A timeout and an infeasibility are different answers, and `solve` now says which

- **Decision.** `solve` returns three things, not two: a `Solution`, a `list[Gate]` meaning **proved
  infeasible**, or an `Unproven` meaning the search stopped with no solution and no proof. Previously
  the last two shared a type.
- **Alternatives.** Keep the two-way split and let callers infer exhaustion from an empty core. Raise
  on a timeout.
- **Reason.** An empty `list[Gate]` is type-identical to "proved infeasible, with an empty core", so
  no caller could tell a proof from a stopwatch. Three consumers turn that into a real failure. The
  fallback ladder reported *no legal roster exists* when the truth was *we did not look for long
  enough*. `methods.py` recorded a timeout as `INFEASIBLE`, which would have put a stopwatch reading
  into a benchmark as a proof. And T4's explainer is specified to consume a core and phrase it, so it
  would have narrated a conflict nobody demonstrated: the exact failure [`D-013`](#d-013) exists to prevent,
  arriving through the data rather than through the LLM.
- **Consequences.** The ladder's cold branch reads `Unproven` and never a core, which is not merely
  defensive: **a cold solve cannot be infeasible at all**, because the coverage floor is soft and the
  empty roster satisfies every hard constraint ([`D-018`](#d-018)). So exhaustion is the only cold failure, and
  the branch that would report a cold core is unreachable by construction. That reasoning is asserted
  by test rather than left in a comment, because it silently stops holding if the floor ever hardens.
- **How it was found.** Not by review. The ladder was given a 1 ms budget to force its lower rungs,
  and it answered "no legal roster exists" for an instance that solves in 10 ms. Nothing in the
  committed set takes more than 12.4 ms, so no benchmark, test or production payload would have
  reached this path: it needed a deliberately absurd budget, which is the same technique the whole
  rung-forcing exercise rests on.
- **Date.** 2026-08-13.

<a id="d-095"></a>
## D-095. Finish declaration: name ratified, publication deferred

- **Decision.** T3 is declared finished. The repo keeps the name `roster-replan-optimizer`. The
  public/private fork is **deferred rather than executed**: the project stays private for now.
  The plan the project ran on is retired and is no longer maintained.
- **Alternatives.** Rename to something shorter, such as `roster-replan`. Publish now, which was
  the plan's own recommended default for completion.
- **Reason.** The name is accurate and is load-bearing in three places: the package, the remote and
  every cross-reference in the docs, so renaming costs a sweep and buys a shorter URL. On
  publication, the project passes the IP-hygiene test it set itself: it is synthetic throughout, with
  no tenant data, no vendor payloads and no wage data, so "would I be fine if this went public
  tomorrow?" is already yes. The reason to wait is asymmetry rather than doubt. Publishing is
  irreversible in practice (what is published is cached and indexed regardless of a later revert)
  and staying private is not. Between two acceptable options where one can be undone, the reversible
  one is the cheaper order to take them in.
- **Consequences.** Finishing is recorded as a state of the repo rather than as an announcement, which
  is the correct separation: the work is done whether or not anyone is shown it. The declaration
  listed what did **not** ship with the same care as what did: capture and replay,
  [`D-001`](#d-001), the flat cost model, and T4/T5 as designed upside.

  One thing it added that the plan did not ask for: `tests/test_specs.py`, which mechanises the
  checkable half of "all specs true". It found a broken documentation link on its first run, and it
  encodes the duplicate-ID check that would have caught [`D-089`](#d-089) being assigned twice.
- **Where those documents are, 2026-09-02.** Neither the plan nor the declaration is in the
  repository. What the declaration got wrong is in the [ledger](specs/README.md) as findings against
  the components that found them, and where the project stands is [`STATE.md`](STATE.md).
- **Date.** 2026-08-13.

<a id="d-096"></a>
## D-096. The timing balance is committed and asserted; absolute milliseconds are not

- **Decision.** `tests/timings.json` records build p50, search p50 and their ratio. The test asserts
  the **ratio** within 20%, and the milliseconds only within a loose sanity band.
- **Alternatives.** Assert a band around the absolute figures, which is the obvious guard. Assert
  nothing and re-read the documents by hand after a performance change.
- **Reason.** [`D-092`](#d-092) cut build time from about 7 ms to about 5 ms and **six documents went on quoting
  7 ms**: two specs, two studies, `benchmarks.md` and a decision record. Nothing caught it: the suite
  was green, the mutation harness was green, and `test_specs.py` checks rule IDs, decision IDs and
  links but has no opinion about numbers.

  The incident taught something narrower than *measurements rot*, and it is what shapes this guard.
  **Paired ratios did not rot.** Re-running every level-1 study after [`D-092`](#d-092) moved the ratios by
  about a point and changed no verdict, because a ratio divides out whatever the shared baseline does.
  **The absolute figure did**, because it is a statement about the baseline itself.

  The first version of this file asserted a 40% band on the milliseconds, and it would **not** have
  caught [`D-092`](#d-092), whose shift was 26%. A band loose enough to survive a slower laptop is too
  loose to detect what it exists for. `build / search` is the right quantity: a faster machine shrinks
  both sides of it, and [`D-092`](#d-092) moved it 44% against a 20% band.
- **Consequences.** The studies are left alone, which is the point: they were already robust and
  adding provenance stamps to all eight would have been friction against a failure mode they do not
  have. One quantity is guarded, and it is the one that broke.

  `test_build_still_dominates_search` asserts the *ordering* separately, because two records reasoned
  from it rather than merely quoting it ([`D-081`](#d-081), [`D-093`](#d-093)). A silent reversal is exactly
  what happened last time. *(Retired by [`D-119`](#d-119), which reversed it.)*
- **Date.** 2026-08-13.

<a id="d-097"></a>
## D-097. The explainer starts with shortfalls, and answers from the checker

- **Decision.** T4's first component explains **why a shift is short**, not why a solve was infeasible.
  `roster_replan/explain.py` imports the checker and nothing else; an import-linter contract forbids it
  `model`, `disruption` and `ortools`.
- **Alternatives.** Start with the infeasibility explainer `PLAN.md` names first. Derive the reasons
  from `model.exclusions()`, which already retains them and would need no recomputation.
- **Reason.** [`D-047`](#d-047) re-scoped this before T4 opened and the measurement confirms it: with a
  soft coverage floor **a cold solve is essentially never infeasible**. Across the committed set, 16 of
  72 cases return an optimal roster that still leaves a shift short (24 unstaffed positions) and none
  is infeasible. An explainer built for infeasibility first would be built for a case that does not
  occur.

  **Answering from the checker rather than from presolve is the other half.** An explanation derived
  from the model's own exclusion table is the solver's account of itself: a wrong exclusion produces a
  wrong explanation that agrees with it, and nothing shows. Asking the independent reading makes a
  wrong exclusion **contradict** the roster, which is a finding rather than a consistent lie.
- **Consequences.** The design yields an invariant worth more than the feature. Because
  `shortfall_weight` dominates, an optimal solver adds anyone it legally can, so every person off an
  under-staffed slot must be blocked by something. An employee the checker says could have been added
  is a **defect report** rather than a gap. `Shortfall.unexplained` carries them and is asserted empty
  across all 72 cases, which makes this a fifth reading of the rules rather than a presentation layer,
  because it can fail on a roster every other layer accepts.

  A person blocked by two rules is counted under both: naming one "primary" would imply that relaxing
  it frees them, and it does not.
- **Date.** 2026-08-13.

<a id="d-098"></a>
## D-098. `what_if` refuses unlawful hypotheticals rather than answering them

- **Decision.** A `what_if` variant is validated before it is solved. If the change makes the instance
  unlawful (most importantly, relaxing a statutory parameter with no recorded derogation basis) the
  tool returns the refusal and its defects as the answer, and no roster.
- **Alternatives.** Solve it anyway and let the caller notice. Refuse rule relaxations outright.
- **Reason.** *Yes, hire nobody, just shorten the rest gap* is the most dangerous sentence this
  project could emit: specific, actionable, and illegal. A hypothetical tool is exactly where that
  answer would be produced innocently, because the machinery is perfectly capable of solving an
  instance whose parameters break the law: `validation.py` is what knows better, and it was already
  written.

  Refusing relaxations outright was rejected for the opposite reason: a derogation is lawful, and a
  planner exploring one is the case this tool exists to serve. The rule is *recorded basis*, not
  *never*, so the same relaxation is answered when a basis is supplied.
- **Consequences.** The change set is closed and typed rather than a free-form patch. A tool an LLM
  can call will be called with something unexpected, and a patch endpoint over `Instance` is an
  arbitrary-edit hole wearing a schema: each `Change` kind is one whose interaction with the rule
  registry was understood before it was allowed.

  A hypothetical hire is eligible on every day, which is the optimistic reading and is stated rather
  than hidden: the answer is an **upper bound** on what hiring would buy.

  `Outcome` carries the resulting roster, not only the summary numbers. That began as a testability
  fix and is the better design anyway: two tied optima under D2 share an objective *and* a change
  count, so a baseline accidentally solved at the wrong seed is invisible in every scalar and visible
  only in the roster: the mutation harness caught exactly that, twice, before the field existed.
- **Date.** 2026-08-13.

<a id="d-099"></a>
## D-099. Profile review is deterministic, and enabling an unencoded rule is a defect

- **Decision.** Stages 2 to 4 of `config.md`: structural lawfulness, contradiction and subsumption,
  feasibility probe: are built in `roster_replan/profile.py` and run with no model available. A profile
  that enables one of the five registry-declared, unencoded optional rules is **rejected**.
- **Alternatives.** Build the natural-language parse first, since it is the visible feature. Accept
  enabled optional rules as a forward declaration of intent.
- **Reason.** `config.md` states the constraint and it decides the order: *"deterministic profile
  editing works fully with no LLM; the NL layer is an accelerator, never a dependency."* An accelerator
  built before the thing it accelerates has nothing to fall back to.

  **Accepting an enabled-but-unencoded rule would be worse than ignoring it.** The tenant would hold a
  profile stating that Sunday work is restricted, the solver would restrict nothing, and no test
  anywhere would fail: the registry describing intent rather than code, reaching production through
  configuration instead of through documentation.
- **Consequences.** Two categories, deliberately not merged. A **contradiction** is a property of the
  profile alone and is rejected, and needs no solver to see. **Subsumption** is reported and not
  rejected: a rule that forbids nothing is valid and the tenant may have meant it, but nothing else in
  the system would ever tell them the protection is inert.

  The probe is skipped when a contradiction was found, because solving parameters that cannot all hold
  yields an infeasibility whose cause is the profile and whose explanation would be about the week. It
  uses the **caller's** sample, which also keeps `benchmarks` out of the runtime.
- **Date.** 2026-08-13.

<a id="d-100"></a>
## D-100. The objective inflates the infeasibility core; minimisation is a null on top

- **Decision.** `roster_replan/core.py` reduces a core by deletion, and asks the feasibility question
  **with no objective set**. `explain_infeasibility` reports the minimal core and how large the
  sufficient one was.
- **Alternatives.** Report CP-SAT's core as it comes, which is what T1 did. Minimise the core produced
  by `solve`, which is what [`D-048`](#d-048) specified.
- **Reason.** [`D-048`](#d-048) deferred minimisation because a sufficient core "can name rule instances
  that are not actually necessary". Measured, that understates it badly: on five constructed infeasible
  instances `solve` returns **159 to 219 gates naming eight rules**, where the real conflict is two.

  But **deletion is not the lever**. Asking the same question as pure feasibility, with no objective,
  returns **2 to 3 gates**: an ~80× reduction from one line rather than from a loop of solves. Running
  deletion afterwards then drops **zero** gates on all five cases. The deferred work was aimed at the
  wrong cause.
- **Consequences.** The deletion loop is kept even though it is currently a null, for a reason worth
  separating from its measured effect: it **guarantees** minimality where dropping the objective merely
  achieves it.

  The two changes compose, and only in one order: minimising a 160-gate core would be 160 solves,
  where on a 2-gate core it is three. **Dropping the objective is what makes the guarantee affordable.**

  **Minimal is not smallest.** A different deletion order reaches a different minimal core, so the order
  is fixed to keep the result reproducible.
- **Retires `D-048`, 2026-09-02.** That record deferred minimisation to T4 and named the wrong cause:
  it read the sufficient core as merely naming unnecessary rule instances, where the measurement is
  159 to 219 gates against a real conflict of two, and deletion is not what fixes it. The deferral
  was right; its diagnosis was not.
- **Date.** 2026-08-13.

<a id="d-101"></a>
## D-101. The parse is confined by the schema, and an open mapping is not a schema

- **Decision.** Stage 1 of `config.md` ships as `roster_replan/nl.py`: a narrow `StatedPolicy` schema,
  structured outputs, an injected client, and a `Proposal` that ends in a verdict rather than a save.
  Every field is designed against the schema the API **compiles**, not against the Python type that
  looks right, so derogations are a list of `(parameter, basis)` pairs with the parameter an enum,
  not the `dict[str, str]` the domain uses.
- **Alternatives.** Mirror `RuleParams.derogation_basis` as a mapping, which is what the first version
  did. Take the parameter name as free text. Confine the model by instruction.
- **Reason.** Measured, not reasoned: a `dict[str, str]` field compiles to **an object that can hold
  nothing**: described in the prompt and unreachable in the response. A tenant citing a CBA article
  for a nine-hour rest gap would have the citation dropped and their lawful policy reported back as
  unlawful, with nothing saying why.

  **No test of the surrounding logic could see it**, because the tests drive a stub client, and a stub
  returns whatever the test hands it. So the layer reads the **compiled** schema, and the first schema
  mutant restores this bug.

  The confinement is structural rather than instructed: there is no field for `shortfall_weight` and
  none for `enabled_optional_rules`. **A rule the model cannot state is a rule it cannot break**, and
  that holds against a bad parse, a bad prompt and a prompt injection alike.
- **Consequences.** `to_profile` translates the pairs into the mapping the domain carries; the domain
  type does not change to suit the parse.

  **Unset is not a default.** A silence carries the base profile's value forward. `to_profile` is
  tested against a base that deliberately disagrees with the shipped defaults: against one that
  agrees, inheriting and falling back are indistinguishable, and the mutant survives. It did.

  *The NL layer is an accelerator, never a dependency* is now an import-linter contract.
- **Date.** 2026-08-14.

<a id="d-102"></a>
## D-102. The parse eval scores what was invented, not only what was found

- **Decision.** `benchmarks/nl_eval.py` scores every case against a **complete** expected payload: a
  field the text did not mention must come back unset, and a parse that fills one is reported as
  `invented` rather than as a near miss. The round trip `config.md` asked for is built as well and
  reported separately rather than folded into one number.
- **Alternatives.** Score recall on the fields each case mentions, which is what an extraction eval
  usually does. Ship only the round trip. Ship only the free-form half.
- **Reason.** **Recall measures the wrong failure.** A parse that misses a stated rule produces a
  profile the tenant can see is incomplete; a parse that supplies eleven hours nobody mentioned
  produces one that looks exactly like a policy they wrote, and the rule is enforced against real
  people until somebody reads the document closely.

  Keeping the round trip is a smaller point with the same shape. It cannot prove comprehension: same
  author both sides, but it does prove **coverage**: a field `describe` forgets does not come home.

  Four cases state no policy at all. They ask for a weight [`D-057`](#d-057) bounds and for a rule
  [`D-099`](#d-099) leaves unencoded, and the only correct answer to each is to report it as something
  the schema cannot say. Those are the cases that test the claim worth testing.
- **Consequences.** The eval needs a key and is not in the suite, so its scoring is what breaks
  silently. `tests/test_nl.py` therefore tests the scorer. **An eval that cannot fail measures
  nothing**, and this one is only ever read when it disagrees with a model.

  Two things it does not prove: it does not measure Dutch beyond two cases, and every expected payload
  is one reading of an ambiguous sentence: a disagreement is a finding to argue with, not
  automatically a defect in the parse.
- **Study.** [`docs/studies/nl-parse.md`](studies/nl-parse.md)
- **Date.** 2026-08-14.

<a id="d-103"></a>
## D-103. `unclear` is for what could not be said, not for what was assumed

- **Decision.** `StatedPolicy.unclear` carries only what the schema cannot express or what the text
  leaves unresolved. An assumption the parse **resolved** belongs in the field it resolved to, and a
  silence is not unclear: an unset field already reports that the text did not mention it.
  `PROMPT_VERSION` moved to `nl-2026.2`.
- **Alternatives.** Leave the description as it was and relax the eval, since both failing cases had
  extracted every figure correctly. Score `unclear` only where something unsayable is asked for.
- **Reason.** Measured. The first run scored 16 of 18, and **both failures were this field**: the
  figures were right in every case. *"Less than a day's warning"* parsed to 24 hours and then filed a
  note saying a day had been read as 24 hours; a shift catalogue parsed correctly and then filed the
  text's silences.

  The old wording invited it, so this is a defect in the schema rather than in the model, which is why
  it is fixed there.

  It matters because of what the field is **for**. A planner reads `unclear` to find the one thing the
  system could not take on, and a profile that comes back with five caveats about what the text did
  not say trains them to skim it.
- **Consequences.** The eval scores `unclear` present-or-absent on every case, including the ones that
  should report nothing. That strictness is what turned a pair of passes into a finding, and both cases
  passed on re-run with the extraction unchanged.

  One failure in that run was **the eval's fault and is recorded as such**: shift labels came back
  `early` where the eval expected `Early`, and the schema calls that field the tenant's own name for
  the shift. [`D-102`](#d-102) said in advance that a disagreement is a finding to argue with rather
  than a defect; this is that clause being used, and it went both ways in the same run.
- **Study.** [`docs/studies/nl-parse.md`](studies/nl-parse.md)
- **Date.** 2026-08-14.

<a id="d-104"></a>
## D-104. Two of T5's four items are retired on measurements already taken

- **Decision.** **LNS and learned warm starts are retired**, not deferred: the reason is measurement
  rather than scope. **Generation mode and fairness objectives stay open**: nothing here has measured
  them, and they are product capabilities rather than solver improvements.
- **Alternatives.** Retire T5 whole. Leave all four open, since upside costs nothing to list.
- **Reason.** **Large-neighbourhood search improves a solution the solver cannot prove optimal in the
  time available. Neither half of that sentence is true here.** Every one of 2,160 solves at three
  budgets returned `OPTIMAL`, and solver-free greedy already ties the optimum on most committed cases
  ([`D-083`](#d-083)): the same thing said from the other end.

  **Learned warm starts are the weaker of the two.** Warm starting is worth 9% of a search that runs in
  milliseconds, so learning a better one optimises nine per cent of twelve. The machinery to train it
  would exceed the thing it optimises by orders of magnitude.

  Keeping the other two is not hedging: generation mode lacks only a product surface, and fairness
  across *people* is untouched by anything measured here.
- **Consequences.** What would reopen LNS is stated, so the retirement is falsifiable: **a distribution
  where the solver stops proving optimality.** It also removes the last reason to treat the benchmark
  set as fixed: a distribution that never produces a hard instance is a finding about the generator.
- **Amended by [`D-105`](#d-105).** The generator's whole range was swept and no setting it can express
  makes the search hard, so the retirement rests on a swept range rather than one sample of it. The
  conclusion is firmer; only the citation moved.
- **Narrowed by [`D-127`](#d-127).** Foreign instances do search for seconds, so *this never happens*
  became *this does not happen in the regime we serve*.
- **Study.** [`docs/studies/time-budget.md`](studies/time-budget.md)
- **Date.** 2026-08-14.

<a id="d-105"></a>
## D-105. The coverage axis is sampled where the answer changes, and every T2 analysis is re-measured over 84

- **Decision.** Two classes added (`busy` at 0.80 and `overloaded` at 0.95) taking the committed set
  from 72 cases to 84. Existing instances are untouched and `GENERATOR_VERSION` stays at 1: the
  sampling moved, not the generator. **Every T2 analysis is re-measured over the 84**, not only the
  greedy comparison.
- **Alternatives.** Leave the set alone. Add **conjunction** classes: high demand together with
  scarce skills and thin availability.
- **Reason.** The set held 60 of its 72 cases at a demand ratio of ~0.70, with nothing between 0.73
  and 0.89: the one-axis-at-a-time design, right for attribution and blind where methods separate.
  Measured along the axis, greedy ties **6 of 6 seeds at 0.70 and 3 of 6 at 0.95**, so **"greedy ties
  64 of 72" was substantially a statement about where the set looks.** Over 84 it is 71.

  **The conjunction idea was measured and rejected**, the more useful half: the three pressures
  together produce *structurally* short weeks where greedy ties 6 of 6 at every setting, because both
  methods leave the same unavoidable holes. That makes the benchmark blind rather than sharper, and
  no configuration searches harder: all return `OPTIMAL` in 3 to 11 ms.
- **The re-measurement reproduced, and found what the levers could not.** Every T2 lever holds. One
  code change came out of it: `studies.py` selected its cold instances **positionally**, so inserting
  two classes pushed two others out of the sample without touching a line of study code, and the
  symmetry study's cold count fell from 7 to 0: a sampling artifact arriving in the one place
  fingerprints do not reach.
- **Consequences.** Two figures moved, both upward: the longest search 12.4 ms → **15.4 ms**, and a
  hard coverage floor cannot answer **18 of 84** where it could not answer 16 of 72.
  [`D-104`](#d-104) records what this firmed up.
- **Absorbs `D-107`, 2026-09-02**, which carried the re-measurement this widening owed.
- **Study.** [`docs/studies/time-budget.md`](studies/time-budget.md)
- **Date.** 2026-08-14.

<a id="d-108"></a>
## D-108. Fairness is a third thing, and it pays for understaffing like everything else

- **Decision.** T5's fairness objective ships: a rolling balance of unpopular shifts, in its own
  `Fairness` dataclass rather than inside `Disruption`, encoded by `disruption.fairness_terms` and read
  back independently by `scoring.fairness_of`. Which shifts are unpopular is **declared by the
  profile**, and each employee carries `unpopular_shifts_before_horizon` so the balance is struck over
  a window wider than the horizon. [`D-057`](#d-057)'s domination bound grows a term.
- **Alternatives.** Add the weights to `Disruption`. Derive unpopularity from the shift times. Balance
  with a `max − min` range term instead of a convex penalty.
- **Reason.** **This repo already had two things called fairness and this is neither**, which is why it
  gets its own type. [`D-091`](#d-091)'s round-robin is fairness between *tenants in the queue*; D4's
  concentration spreads *the changes a replan makes*. This one is about the roster, and a tenant can
  want any one of the three without the others.

  **Unpopularity cannot be derived.** A late shift is a burden in one restaurant and the shift people
  compete for in another. Computing it from the clock would encode one tenant's culture as arithmetic,
  in the part of this system that is supposed to be policy-as-data.

  **Convex, not a range**, on the argument `replan.md` already makes for D4: a range term equalises the
  two ends and ignores everyone in the middle.
- **Consequences.** **Fairness gives the optimiser a second reason to leave a shift empty**: an
  unstaffed unpopular shift is one nobody's count went up for, so the bound grows and a weight scale
  that breaks it is a malformed request.

  **The escalation flattens past `fairness_tiers`**: a window long enough to push the whole workforce
  past it switches fairness off while still looking configured.

  **The committed set cannot exercise this term**, because its evenings require a scarce skill, so the
  behavioural tests run over `identical_workforce`: [`D-087`](#d-087)'s argument for symmetry.
- **Date.** 2026-08-14.

<a id="d-109"></a>
## D-109. Generation ships as the cold-start case, and the spec's derivation of it was wrong

- **Decision.** Generation mode needs no formulation, no mode flag and no second route: a caller omits
  `incumbent` and `now`, and validation already accepts that as a cold solve. What ships is the claim
  made **testable** (at the solver, the ladder and the service) plus a correction to the derivation
  `replan.md` had been carrying.
- **Alternatives.** Add a `/v1/rosters` endpoint, or a `mode: "generate"` field, so the capability is
  visible in the API rather than implied by two omitted fields.
- **Reason.** A second route over the same solve would contradict what this design is *for*.
  `replan.md`'s argument is that generation is not a special case, and the honest way to ship that is
  to prove the existing surface carries it. The service test is load-bearing: "no second formulation"
  would be true of `solve` and false of the product if a cold payload could not get through the queue,
  and nothing had ever checked.

  **Testing it found the spec wrong about why it works.** The derivation said cold disruption is a
  positive constant that a shortfall would reduce. Measured, `scoring.disruption_of` short-circuits to
  **0** with no incumbent, so the disruption axis is flat at every coverage level. Both readings rank
  equal-coverage rosters the same way, which is why nobody noticed, but the caveat was describing a
  risk the implementation cannot have.
- **Consequences.** With disruption flat and `cost_weight` at `0`, the objective a cold solve minimises
  is **entirely the peak-workload tie-breaker**. `replan.md` said generation "reduces to cost", which
  is true only once wage data exists.

  Generation reaches the `exact` rung and needs no fallback: a cold solve cannot be infeasible, because
  the empty roster satisfies every hard rule once the coverage floor is soft.

  **T5 is now closed.**
- **Date.** 2026-08-14.

<a id="d-111"></a>
## D-111. The week rules are measured over a week, and the blind spot that hid it

- **Decision.** `R-MAX-WEEKLY` and `R-WEEKLY-REST` are enforced **per week** in both readings, over
  seven-day weeks from the horizon start; a rest window counts for a week only if it lies
  inside it. `domain.py` gains the week as a shared convention.
- **Alternatives.** A per-week budget field. A rolling reading: 35 free hours in every seven-day
  window rather than in every aligned week. Leaving both scoped to the horizon.
- **What was wrong, and why nothing could see it.** Both readings scoped these week rules to the
  **horizon**. At seven days the two spans coincide and the encodings are right; past seven they
  separate in the weak direction: 35 hours of rest inside four weeks satisfies a rule meaning 35
  inside each. **Nothing in the suite could have caught it**: the differential
  harness compares two readings that are wrong in the same direction, so it reports agreement, and
  brute-force ground truth enumerates against the same predicates. This is the shared-*assumption*
  form of what `domain.py` forbids for shared thresholds: seven days was never named as a threshold,
  because it is not a number in either reading. A `days > 7` guard stood in front of it until
  [`D-113`](#d-113).
- **Reason.** The generalisation is free at one week: **895 variables and 1,205
  constraints before and after**. At two weeks it is a different model. The **rolling reading** was
  rejected on reporting: it has no week to name, so a violation could not say *when*. The cost is
  stated rather than hidden: a 40-hour rest straddling a boundary counts for neither week, which is
  [`D-029`](#d-029)'s conservatism at every internal boundary.
- **Consequences.** Both rules now report a day coordinate, so the differential harness compares
  *which week* rather than only *whether*, and four mutants restoring the old scoping are caught by
  the layer that could not have seen the defect an hour earlier.
- **Absorbs `D-110`, 2026-09-02**, which refused a horizon past seven days.
- **Date.** 2026-08-14.

<a id="d-112"></a>
## D-112. The mutation harness says `unverifiable` where it used to say `clean`

- **Decision.** A run that cannot vouch for the tree it ran in reports `verdict: unverifiable` and
  `trustworthy: false`. Two conditions trigger it: a target file already modified when the run
  started, and a late write reinstated after the per-mutant restore verified. A survivor outranks both.
- **Alternatives.** Refuse to start on a dirty tree, which forbids the workflow that found this. Leave
  it, since the report already named the skipped files. Check the tree by content rather than by
  `git status`.
- **Reason.** **The harness knew and said nothing that mattered.** The report read `verdict: clean`,
  `trustworthy: true`, `leaked: []` (with a mutated `checker.py` in the working tree) and named the
  reason three fields lower. The clean-tree check subtracts files that were already modified, so it was
  blind to precisely the two files the run was mutating, and `trustworthy` was computed as
  `verdict != "leaked"`, a tautology when the leak check cannot see.

  **A field a reader is told to trust must not be the one field that cannot see the failure.**

  Refusing to start was rejected because of *when* the harness is used: when a layer is added or is
  about to be trusted, which is mid-change by definition. Checking by content was rejected as
  insufficient rather than wrong: no in-process check reaches a watcher writing back **after the
  process exited**. What the harness can do is decline to certify a tree it will not be around to watch.
- **Consequences.** `summarise` computes `unvouched_for` from its input, so the field the verdict
  derives from is in the report rather than left to be reconstructed from two others. Four tests pin the ordering:
  leak, survivor, unverifiable, clean.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-14.

<a id="d-113"></a>
## D-113. The guard comes off for whole weeks, and stays on for part of one

- **Decision.** A horizon longer than a week is accepted when it is a **whole number of weeks**. One
  ending part-way through a week is refused as a request. [`D-110`](#d-110)'s flat refusal is retired.
- **Alternatives.** Keep the guard until the committed set contains multi-week instances. Accept a
  part-week horizon and let the model report what it finds. Require whole weeks always, which would
  refuse the three-day horizons the service answers today.
- **Reason.** [`D-111`](#d-111) gave three reasons for keeping the guard, and they did not survive contact
  in the same way.

  The **profile probe** was not a defect. Its hard-coded `7 * 24.0` was right for a reason its name
  denied: after [`D-111`](#d-111) the rest window must fit inside a *week*, so the constant is the rule's
  own span rather than the payload's.

  The **stub week** is real and is what the guard becomes. A ten-day horizon ends in a three-day week
  that cannot hold 35 hours under any roster. The model reports that honestly and it is a useless truth:
  no roster fixes it, so it is an `InputDefect` naming the stub.

  The **generator** is unfixed and does not gate this: it is evidence tooling, not the request path.
  What its seven-day hard-coding costs is that **no committed benchmark case runs at more than a week**,
  so this ships a supported configuration with no measurement behind it.
- **Consequences.** Generation mode ([`D-109`](#d-109)) inherits the lift. Two things the generator needs
  before it can supply evidence, neither fixed here: `DAYS = 7` has to become a scenario parameter, and
  `_load` treats `day >= 4` as the weekend, which past day six makes every remaining day a Saturday.
- **Study.** [`docs/studies/horizon.md`](studies/horizon.md)
- **Date.** 2026-08-14.

<a id="d-114"></a>
## D-114. The timing guards are calibrated, so CI deselects them rather than widening them

- **Decision.** The two calibrated timing guards are marked `machine` and deselected in CI with
  `-m "not machine"`. They still run by default everywhere else.
  `test_build_still_dominates_search` is not marked and runs in CI.
- **Alternatives.** Widen the bands until a shared runner passes. Regenerate `timings.json` on the
  runner, making CI the calibration machine. Delete the guards, since CI cannot check them.
- **Reason.** `timings.json` holds figures measured on the machine in `benchmarks.md`'s hardware line,
  and a shared two-core runner is routinely two to four times slower at single-threaded Python. The
  guard is not detecting a regression; **it is detecting the runner**.

  **Widening is the option [`D-096`](#d-096) already refused**, one level up: a band loose enough to
  survive a slower laptop is too loose to detect what it exists for, and one loose enough for a CI
  runner is looser still.

  **Regenerating on the runner** moves the calibration to hardware nobody reads the documents on.

  The ratio is the subtler half. [`D-096`](#d-096) chose `build / search` because a faster machine
  shrinks both sides, but that holds between comparable machines, not between a laptop and a runner
  where the Python half and the C++ half slow by different factors. The ratio is portable against
  *speed*, not against a change in the mix.
- **Consequences.** CI cannot check these guards, and that is the honest shape of the hole: they guard
  *this* repo's documents against drifting from *this* machine.

  This is also **the first thing CI found, and it found it by failing on a green repo**: the tests pass
  on every machine that has ever run them and fail on the one machine that had never run them.
- **Date.** 2026-08-14.

<a id="d-115"></a>
## D-115. The generator takes a horizon, and its weekly pattern was a weekly pattern only by accident

- **Decision.** `ScenarioParams` gains `days`, defaulting to seven, and the generator refuses a horizon
  `validation.py` would refuse. `_load`'s demand weighting keys on `day % DAYS_PER_WEEK` rather than on
  `day`.
- **Alternatives.** Generate multi-week instances by tiling a week, which is what the scoping probe did.
  Leave the generator at one week and study horizons with hand-built instances.
- **Reason.** The tiled probe was fine for measuring model *size* and knowingly wrong about everything
  else: it repeated one week's demand exactly and scaled the budget to keep the model feasible, so it
  could not support any claim about coverage.

  **`_load` is the defect this turned up.** It weights demand toward the back of the week with
  `1.6 if day >= 4`, which is a weekly pattern for exactly as long as the horizon is a week. At fourteen
  days it makes every day from the first Thursday onward a Saturday, so a fortnight would have been
  generated with ten weekend days out of fourteen. **Nothing would have failed; the study would simply
  have measured a different world.**

  It is the same shape as [`D-111`](#d-111) one layer out: a constant that is right only because two
  things coincide. The generator had three of them and they were mechanical; this one was arithmetic,
  and it is the one that would have been believed.
- **Consequences.** Capacity is now the weekly budget times the number of weeks, because
  `max_hours_this_week` binds per week while demand is stated over the horizon.

  **Nothing moved at seven days.** The committed fingerprints are unchanged, which is the guard
  [`D-074`](#d-074) exists to be: every edit is inert at the default, and the fingerprints say so rather
  than a reading of the diff.
- **Study.** [`docs/studies/horizon.md`](studies/horizon.md)
- **Date.** 2026-08-14.

<a id="d-116"></a>
## D-116. A longer horizon is rejected because it buys nothing, not because it costs too much

- **Decision.** The one-week horizon stands. `rules.md`'s rejection of a reference-period horizon is
  kept and **its stated reasons are replaced with the measured ones**.
- **Alternatives.** Ship a multi-week horizon now that validation accepts one. Keep the rejection and
  leave its reasoning as written.
- **Reason.** The sentence being tested claimed a longer horizon *"multiplies instance size by an order
  of magnitude and destroys the interactive latency."* Measured over 7, 14 and 28 days: four times the
  days gives **3.9× the variables**, and four weeks answers in about **112 ms end to end**. Size is
  linear because nothing in this model aggregates across the horizon. **Both halves are wrong.**

  What justifies the rejection is the half the sentence never mentions. Four weeks solved at once and
  four weeks solved one at a time reach **identical coverage on every case tried**, and under pressure
  the single solve is two to six times slower. **The longer horizon is slower and finds nothing.**

  That follows from the structure once [`D-111`](#d-111) is in place: `R-MAX-WEEKLY` binds inside a week
  and `R-WEEKLY-REST` is measured inside one, so what couples the weeks is only what
  `last_shift_end_before_horizon` and `consecutive_days_worked_before_horizon` already carry.
- **Consequences.** [`D-081`](#d-081)'s premise is now **scoped rather than general**: build costs more
  than search at seven days, and at twenty-eight search costs nearly three times as much. Every
  performance conclusion in this repo is a statement about a one-week horizon.

  **The measurement cannot reach the question `rules.md` is actually about**, which is why this
  reopens [`D-111`](#d-111)'s deferral rather than closing it. Both arms carry the same per-week ceiling,
  so what was compared is horizon *length*. What a collapsed reference period loses is the freedom to
  spend it unevenly, and no arm of this study can express it because the field does not exist.
- **Study.** [`docs/studies/horizon.md`](studies/horizon.md)
- **Date.** 2026-08-14.

<a id="d-119"></a>
## D-119. The optimum is canonical, because the model should decide the roster and the search should not

- **Decision.** `model.solve` runs a second phase on every proved optimum: the optimal objective value
  is pinned as a constraint and a canonical criterion is minimised over the optimal set. The roster
  returned is therefore a function of the model, not of the search. Nothing about *what is optimal*
  changes, so every committed objective value is untouched by construction.
- **Alternatives.** Canonicalise cold solves only. A dominated tie-break folded into the primary
  objective, which would need the objective scale to grow. Leave it, and keep
  [`D-118`](#d-118)'s scoped claim.
- **Reason.** The claim being repaired is `README.md`'s reproducibility promise.
  **The degeneracy is not marginal**: the objective value is identical
  every time, and the roster differs on **24 of the 84 replans and on all 84 cold weeks**. The choice
  among equal optima was determined by nothing anybody wrote down. Canonicalising cold solves only was
  the recommendation until that measurement: [`D-105`](#d-105)'s lesson landing again.

  **The criterion is `Σ ordinal² · x`, and the exponent was measured rather than chosen.** A linear one
  left a cold week with four rosters; squaring collapsed it to one *and* ran three times faster.
- **Consequences.** **Search time rises 61%, and [`D-081`](#d-081)'s premise dies at one week**: the
  committed `build/search` balance moves from 1.52 to 0.985, and
  `test_build_still_dominates_search` is retired: a test pinning a claim the code no longer makes is
  worse than no test.

  Every committed artifact derived from a solve is regenerated, and **the demo scenario moved to
  `headline/3`**: under the canonical incumbent the old one's sick call lands on somebody who can be
  covered, so it stopped showing a shortfall at all.
- **Study.** [`docs/studies/reproducibility.md`](studies/reproducibility.md)
- **Date.** 2026-08-14.

<a id="d-120"></a>
## D-120. The D0–D4 divergence rate is 10 of 84, and the number it replaces was never robust

- **Decision.** [`studies/disruption-metrics.md`](studies/disruption-metrics.md) is re-measured on the
  set as [`D-119`](#d-119) leaves it. Divergence falls from **26 of 84 to 10 of 84**, the worked example
  moves, and the coverage-axis curve the study drew is withdrawn. [`D-085`](#d-085) and
  [`D-086`](#d-086) keep their figures as recorded; this supersedes them, and **retires
  [`D-106`](#d-106)**, which drew the curve.
- **Alternatives.** Keep the old numbers with a note. Re-run and report the new rate without
  revisiting the conclusions drawn from the old one.
- **Reason.** **The method did not change and could not have.** `metrics.py` builds its own models, so
  the canonical optimum never touches it, and the regret measurement was tie-proof before and after.

  **The instances changed.** A canonical incumbent is a different published roster, so the disruption
  event lands on a different person and every replan is a new instance. The divergence rate is a
  property of the instances, and this measures how little that property travels: same generator, same
  classes, same seeds, and a rate that fell by a factor of two and a half.

  What held is the part worth having: the split is still **entirely** D0/D1/D2 against D3/D4, the
  regret is still symmetric, and the hand-derived worked example reproduces **to the point** on a
  different seed. **A structure that survives its instances being replaced is a finding; a rate that
  does not is a measurement.**
- **Consequences.** [`D-060`](#d-060)'s mechanism comes out *stronger*: measured at the slot the event
  damaged, **all ten divergences sit in the top slack bucket and every other bucket is a clean zero**.
  As a necessary condition that is now exact on this set; as a sufficient one it remains nowhere close.

  The rate is quoted in `README.md`, which is corrected. What should not be corrected is the
  impression the old number gave: **26 of 84 was never a robust figure**, and nothing said so,
  because nothing had moved the instances underneath it.
- **Study.** [`docs/studies/disruption-metrics.md`](studies/disruption-metrics.md)
- **Date.** 2026-08-14.

<a id="d-121"></a>
## D-121. CI goes back to linux, because the canonical optimum is a claim that needs a foreign binary to test

- **Decision.** CI returns to `ubuntu-latest`, and the solved half of the benchmark manifest loses its
  `machine` mark. The timing guards keep theirs. [`D-118`](#d-118)'s move to macOS is retired;
  [`D-117`](#d-117)'s mark on the manifest is retired with it.
- **Alternatives.** Stay on macOS, where everything is known to pass. Flip the runner but leave the
  manifest marked, so a failure could only come from the six scenario tests.
- **Reason.** [`D-118`](#d-118) was a workaround with a stated expiry, and [`D-119`](#d-119) is the expiry:
  the roster is now a function of the model rather than of the search, so an artifact should no longer
  carry the binary that made it.

  Should is not does, and **this is the experiment rather than the conclusion**. A linux x86-64 runner is
  a different ortools build from every machine these artifacts were recorded on, which is exactly the
  property under test.

  **Leaving the manifest marked was rejected for making the experiment weaker on purpose.** If the
  digests still carry the build the test should fail and say so; if they do not, the mark is a lie the
  suite tells about itself.
- **Consequences.** The failure mode is legible in advance, which is the point of writing this before
  the run. **Green** means the canonical optimum travels between builds. **Red** means
  [`D-119`](#d-119) bought reproducibility on one machine only, and the honest response is macOS plus a
  qualifier that stays.
- **Outcome.** **Green**, on a linux x86-64 runner against artifacts recorded on macOS arm64.
  `README.md` drops the *on the same solver build* qualifier, [`D-118`](#d-118) is retired, and CI is
  testing portability again rather than assuming it.
- **Study.** [`docs/studies/reproducibility.md`](studies/reproducibility.md)
- **Date.** 2026-08-14.

<a id="d-122"></a>
## D-122. The time-boxed rung is tested by handing the ladder a time-boxed answer, not by racing a budget

- **Decision.** `test_time_boxed_rung_reports_a_gap_rather_than_hiding_it` stubs `ladder.solve` to
  return a feasible-but-unproven `Solution` rather than trying to provoke one with a small budget. The
  other three rungs keep their constructed conditions.
- **Alternatives.** Widen the budget window. Use a harder instance so optimality cannot be proven. Mark
  the test `machine`, as [`D-114`](#d-114) did for the timing guards.
- **Reason.** The test asked for a budget that finds a roster and cannot prove it optimal. On the
  machine it was written on that window is roughly 50 ms to 87 ms. CI fell below its lower edge, and it
  failed in **one of the two jobs of the same commit on the same hardware**: the signature of a race
  rather than a defect.

  **Widening the window is not available, and that was measured before concluding it.** This instance
  family is proved optimal in about 90 ms at every size tried, so making it bigger moves the *lower*
  edge up without moving the upper one.

  **None of that window is the ladder's behaviour.** What the test asserts lives entirely in
  `_from_solve`: given a solution the solver could not prove optimal, the rung is `TIME_BOXED`, the gap
  is positive, `degraded` is set, and `trustworthy` stays true because the roster is still legal.
  Handing it exactly such a solution tests exactly that, deterministically, on any machine.

  Marking it `machine` was rejected because it is not a machine-calibrated claim: `timings.json`
  asserts a measured quantity, and this asserts a branch.
- **Consequences.** The stub is the *solver's own output shape*, taken from a real proved solve and
  relabelled, so the roster is genuine and legal rather than mocked away. What is no longer covered is
  the solver actually producing a feasible-but-unproven answer under a budget, and that was never
  covered reliably, since **no committed case has ever reached a time budget**.
- **Study.** [`docs/studies/time-budget.md`](studies/time-budget.md)
- **Date.** 2026-08-14.

<a id="d-123"></a>
## D-123. The reference period gets its own rule, and the approximation it tests turns out to be free

- **Decision.** `R-MAX-PERIOD` ships: an **optional** per-employee ceiling on hours across the whole
  horizon, carrying what is left of the rolling reference period. Both readings enforce it. This closes
  the deferral [`D-111`](#d-111) made and [`D-116`](#d-116) reopened.
- **Alternatives.** Leave it deferred. Fold it into `R-MAX-WEEKLY` as a second parameter. Make it
  mandatory.
- **Reason.** [`D-116`](#d-116) measured a longer horizon and found it buys nothing, then said what it
  could not reach: **both arms held the same weekly ceiling, so what was compared was horizon length.**
  The approximation `rules.md` actually makes is different: the weekly budget derives from an *average
  over a reference period*, and an average is a pool. A caller with 140 hours left in the quarter and a
  38-hour weekly ceiling is stating two facts, and one number cannot hold both.

  Neither rule implies the other, which is why this is a second rule rather than a second parameter: the
  ceiling is a **rate**, the pool is a **budget**, and a test holds a witness for each direction.

  **Optional is deliberate.** Every other caller-supplied quantity is mandatory because a missing one has
  a dangerous default. This one does not: absent means the caller has nothing to add beyond the weekly
  ceiling.
- **Consequences.** **The approximation is free, measured**: given the same total hours as a pool rather
  than a flat weekly rate, four to nine employees per case work unequal weeks and coverage is identical
  on every case. It is a null with a stated edge: a pool *tighter* than the weeks it spans would bind
  where no weekly ceiling would, and the generator produces no such case.

  **The manifest found a case [`D-074`](#d-074) has no name for**: 84 of 84 `week` digests moved and 0 of
  84 `incumbent` digests did. The third thing that can move is the **payload schema**.
- **Study.** [`docs/studies/horizon.md`](studies/horizon.md)
- **Date.** 2026-08-14.

<a id="d-124"></a>
## D-124. Canonicalising the optimum blinded two test layers, and the harness is what noticed

- **Decision.** `test_a_hint_does_not_survive_into_the_next_solve` and
  `test_the_baseline_is_the_instance_as_it_stands` stop inferring a search-path defect from the answer
  and assert it where it happens: the cached model carries no leftover hint, and every measurement in a
  hypothetical is taken at the seed the caller asked for.
- **Alternatives.** Accept the loss and delete the two mutants. Re-introduce tie-dependence somewhere so
  the old proxies keep working.
- **Reason.** The first full mutation run after [`D-119`](#d-119) came back `survivors`, 95 of 97, on a
  clean tree and a green suite of 766 tests. Both survivors break the **search path** rather than the
  answer, and both detected that by observing that the *roster changed*.
  **[`D-119`](#d-119) made the roster independent of the search path on purpose**, so the detector stopped
  working: measured rather than inferred: with canonicalisation disabled both mutants are caught, and
  with it enabled both survive.

  That is a real cost of [`D-119`](#d-119) and nobody predicted it.
  **Reproducibility and observability were trading against each other, and only one side of the trade
  was on the invoice.**
- **Consequences.** Three tests have now been converted from *inferring a defect through the answer* to
  *asserting it where it lives*. The pattern is worth naming because it will recur: **a test that
  detects a search-path defect by watching the output is only as good as the output's sensitivity to the
  search**, and this project has just spent real effort removing that sensitivity.

  The mutation harness is the only layer that could have found this, and it is the first time a blind
  spot was **created by a deliberate improvement** rather than missed when the layer was written.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-14.

<a id="d-125"></a>
## D-125. Foreign rosters are fetched and fingerprinted, never redistributed

- **Decision.** `benchmarks/foreign.py` imports the nurse-rostering benchmark instances and their
  published solutions from schedulingbenchmarks.org. `benchmarks/foreign.json` commits the URLs and a
  SHA-256 per archive; the data is fetched on demand into a gitignored cache and verified against
  those digests, and a mismatch deletes the file rather than proceeding.
- **Alternatives.** Commit the instances, and rewrite `README.md`'s claim that all committed data is
  synthetic. Commit nothing and skip the study. Vendor a derived form.
- **Reason.** The source **states no licence, no copyright and no terms of use**, which is not public
  domain: absent a grant, default copyright applies. Fetching for use is ordinary; republishing is
  not.

  The fingerprint pattern is already this project's, which is why it fits without inventing anything:
  [`D-073`](#d-073) commits the benchmark set as seeds and hashes rather than 84 payloads, for a different
  reason and with the same shape. A verified fetch is reproducible in the way that matters: the study
  either runs against the bytes it was written against or refuses, and `README.md` keeps a sentence
  that `finish.md`'s publication reasoning leans on.

  **Vendoring a derived form was the tempting middle**, rejected as the worst of both: still their
  data, reduced enough to be hard to check and not enough to stop being theirs.
- **Consequences.** The foreign study needs one command before it runs and says so. CI does not run
  it (the data is absent there by design) so this is a study a reader reproduces deliberately,
  which is the same footing as `benchmarks/nl_eval.py` and for a better reason: that one costs money,
  this one costs someone else's bandwidth.

  If the upstream archives change, the digests stop matching and the study refuses to run rather than
  quietly measuring something else. That is the failure mode worth designing for, because a benchmark
  that silently changes its inputs is [`D-074`](#d-074)'s problem arriving from outside the repository.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-14.

<a id="d-126"></a>
## D-126. The canonicalising phase can run out of budget, and says so instead of raising

- **Decision.** `_canonicalise` receives the **remaining** budget rather than a fresh one, and returns
  `(roster, canonical)`. When phase two cannot prove its criterion optimal in the time left, phase one's
  roster stands and `Solution.canonical` is `False`. The assertion that this could not happen is gone.
- **Alternatives.** Give phase two its own full budget and keep raising. Return the feasible-but-unproven
  phase-two roster. Skip canonicalisation above some instance size.
- **Reason.** [`D-119`](#d-119) added the phase and asserted it unreachable. That is true about
  **feasibility** and says nothing about **optimality**: phase two minimises a criterion over a set
  that can hold millions of points, and proving a minimum there is a real search.

  Two defects were behind it and only one was visible. The other is that phase two was handed a fresh
  `max_time_in_seconds`, so a caller asking for 30 seconds could wait 60: a budget contract the service
  and the ladder both reason from.

  **Returning the unproven phase-two roster was rejected as the worst option**: it is reproducible by
  accident, which is the failure [`D-119`](#d-119) exists to remove, wearing a disguise.
- **Consequences.** `Solution` carries `canonical`, and it is the difference between a roster that
  reproduces on any machine and one that reproduces on this build. The unqualified claim in `README.md`
  is therefore true **with a stated boundary**.

  **The committed set could not have found this**: it is the argument for foreign data, made by foreign
  data, on its first day.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-14.

<a id="d-127"></a>
## D-127. Where the model stops is a number now, and it bounds two earlier records

- **Decision.** Scale limits are measured on foreign instances. [`D-104`](#d-104)'s
  retirement of LNS and [`D-081`](#d-081)'s two-clock premise are both **bounded to the distribution they
  were measured on** rather than left general.
- **Alternatives.** Leave the scale question open, as [`D-105`](#d-105) did. Generate larger synthetic
  instances instead.
- **Reason.** [`D-105`](#d-105) swept every knob the generator has and found every solve returning
  `OPTIMAL` in 3 to 11 ms, and read that as nothing here being hard. What it measured is that **the
  generator cannot produce a hard instance**: a different claim, and the one this project could not
  tell apart from the inside.

  Foreign instances do produce them. **One takes 7.71 seconds of search to prove optimality**, against
  a committed-set maximum of 15.4 ms across 2,268 runs: a factor of 500. Another, at 8 million
  variables, returns `UNKNOWN`.

  LNS is not un-retired: the instances where it would help are 100 employees over a year, which is
  not the tenant this service is for. The reasoning narrows from "this never happens" to "this does
  not happen in the regime we serve".
- **Consequences.** **The binding constraint at every size is model construction, not search**: 9
  seconds at 910k variables and **527 at 8M**, to build a model the solver then fails to crack. That
  makes [`D-092`](#d-092) correctly aimed at both ends of the scale.

  The usable envelope is stated rather than implied: **up to about 40 employees over four weeks**.
  Nothing between that and the ceiling is measured, because these instances do not sample it.
- **The ceiling is this implementation's, not the formulation's.** 527 seconds is a Python loop
  emitting constraints one at a time, so it bounds what this service answers today and says nothing
  about whether the encoding is right at that size. Whether batching construction moves it is **not**
  measured. [`model.md`](internals/model.md) and [`docs/README.md`](README.md) say so where they
  quote the figure.
- **Absorbs `D-147`, 2026-09-02.**
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-14.

<a id="d-128"></a>
## D-128. Priced hard rules are measured, and the easy distribution gives the wrong answer

- **Decision.** [`D-002`](#d-002)'s refusal of penalised hard constraints and [`D-003`](#d-003)'s
  justification of the independent checker are **confirmed on measurement**, and both are scoped to the
  reason that survived: a penalty formulation escapes an expensive hard rule through `R-COVER`'s soft
  floor, so raising the price buys legality by refusing to staff. The rival lives at
  [`benchmarks/anneal.py`](../benchmarks/anneal.py) and is **not** registered in `methods.METHODS`.
- **Alternatives.** Leave the claim as prose. Register the search as a fifth method.
- **Reason.** Three records asserted that penalising a hard rule yields a cheaply illegal roster and
  none had measured it. Measured, at weight 1 **every case returns an illegal roster and 13 of 14
  outscore the proven optimum** on the shared yardstick: a results table showing only the objective
  column ranks the unsafe method first. The characteristic failure is quieter than the claim supposed:
  ten of the fourteen returned the damaged incumbent untouched, because declining to repair is the
  cheapest way out of a priced rule.

  **The committed set alone would have falsified the strong claim**, reporting a tuned penalty engine as
  safe and near-optimal. On the one hard instance no weight works at all.

  The mechanism is the transferable part: `R-COVER`'s floor is the one deliberate soft exception, so a
  search that must pay for legality finds the cheapest lawful way to be lawful, and that is to staff
  nothing.
- **Consequences.** **[`D-003`](#d-003)'s independence has a number behind it now.** Nothing inside such a
  search can report its own illegality, which is the checker's job stated as a measurement rather than
  as a structural argument. The budget axis is evaluations rather than seconds, stated as a limitation.
- **Study.** [`docs/studies/penalty-search.md`](studies/penalty-search.md)
- **Date.** 2026-08-15.

<a id="d-129"></a>
## D-129. Learning the soft weights is retired: the rosters carry no signal to learn from

- **Decision.** **Weight recovery from (generated, published) roster pairs is retired, not deferred**,
  on this instance distribution. The identifiability probe ships at
  [`benchmarks/weights.py`](../benchmarks/weights.py) because the measurement *is* the result; no
  estimator is built. What would reopen it is stated below, so the retirement is falsifiable.
- **Alternatives.** Build the estimator anyway and report its accuracy. Start crude and escalate to
  inverse optimization. Sweep the foreign rosters first.
- **Reason.** An estimator scored against parameters the data cannot identify reports its own prior and
  looks like a result, so identifiability was measured before anything was fitted. **Not one of the five
  D2-active weights moves the roster on any of the fourteen classes**, across three orders of magnitude.

  The objective is **priced but not pivotal**: the weight enters the objective and cannot reach the
  argmin. **Two existing records already said this**: D0/D1/D2 never disagree
  ([`D-085`](#d-085), [`D-120`](#d-120)), and a solver-free greedy with no objective at all ties the optimum
  on 71 of 84 ([`D-083`](#d-083), [`D-105`](#d-105)).

  **The null is about the distribution, and that is demonstrated rather than argued.** Where
  `weights.forced_choice` builds a case the weights alone decide, the roster follows them.
- **Consequences.** **Where signal exists, recovery returns an interval on a ratio and never a weight**:
  scaling every weight leaves every argmin unchanged, so more data narrows the interval and never
  collapses it. Any estimator reporting a point estimate is reporting its prior.

  **What would reopen this**: a distribution where the objective picks the roster. The sharper reopening
  is one this project cannot do alone: the premise was that *published* rosters encode preferences, and
  what is measured here is rosters **this model produces**.
- **Study.** [`docs/studies/weight-recovery.md`](studies/weight-recovery.md)
- **Date.** 2026-08-15.

<a id="d-130"></a>
## D-130. The mutation report records what a run cost, and a late write costs one layer

- **Decision.** Every run writes `started_at` and `duration_seconds` into
  `tests/mutation-report.json`. The remedy for `unverifiable` is to re-run **only the layer whose paths
  are named in `unvouched_for`**, with `--report` pointed somewhere else. [`D-112`](#d-112) stands
  unchanged: it defines what the verdict means; this defines what the report carries.
- **Alternatives.** Leave the runtime to prose. Time each mutant. Keep telling readers to commit and
  re-run, which is correct and roughly ten times the cost of what is needed.
- **Reason.** **How long a run takes was folklore, and every copy of it was wrong.** The module docstring
  and `CLAUDE.md` both said *tens of minutes*; a working session put it near a hundred, and nothing in
  the repo could contradict that because **the one durable record kept no clock**.

  The gap matters more than the number: an hour-long job gets scheduled around while a ten-minute one
  gets run, so a wrong cost estimate quietly discourages the exact use the harness exists for.

  `duration_seconds` comes from `time.monotonic()`: subtracting wall-clock stamps would measure a
  laptop that sleeps mid-run as much as the run.

  **The layer-sized remedy is what one `unverifiable` run taught.** Re-running the one affected layer
  settled it in seconds where a full re-run would have re-proved a hundred mutants nobody doubted, and
  sending it to a different report matters, because a five-mutant report written over a hundred-mutant
  one is how a previous session's record was lost.
- **Consequences.** `CLAUDE.md` and the docstring carry the measured figure and say to quote the report
  once the two disagree. The report is gitignored, so a second machine's number is a new measurement
  rather than a contradiction.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.

<a id="d-131"></a>
## D-131. The one cross-week term shipped without a way to reach it

- **Decision.** `Fairness`, `Employee.unpopular_shifts_before_horizon` and `max_hours_this_period` join
  the wire contract, and `Profile` gains the `fairness` field the specs already said it had, carried
  onto the week by `applied_to`. The priors limit `replan.md` attributed to `validation.py` is
  implemented in `profile.remarks`, which gains an optional `sample`.
- **Alternatives.** Correct the specs instead, leaving T5's objective unreachable by the product. Put
  the priors check in `validation.py`, as the spec said, which would reject a lawful request.
- **Reason.** **A term the service cannot express is not shipped.** [`D-108`](#d-108) records fairness as
  built, tested and measured against the domination bound, and it is all three. What no test asked is
  whether a caller could switch it on. None could: `Strict` forbids unknown fields, so the one
  cross-week term in the objective and the one cross-week hard rule ([`D-123`](#d-123)) were callable
  only from Python.

  **The round-trip test could not see it**, because it runs over committed cases and no case sets these
  fields: the identity held over the fields the set happens to use. An instance distribution that does
  not contain a field cannot test whether the boundary carries it.

  The priors warning was a claim about code that did not exist, and it belongs in `remarks`: a fairness
  window longer than the tier count is lawful, and every `validation` finding rejects a request.
- **Consequences.** The three fields are additive and default to absent, so no fingerprint moves.
  `applied_to` overwrites `instance.fairness` including with `None`: policy is the profile's.

  **A third defect surfaced in the NL layer**: `nl.to_profile` builds a `Profile` by construction, so a
  parse silent about fairness would have **deleted a tenant's declaration**. Any future `Profile` field
  inherits that obligation.
- **Date.** 2026-08-17.

<a id="d-132"></a>
## D-132. Their whole instance is imported, and their split of hard from soft is not ours

- **Decision.** `benchmarks/foreign.py` parses every section and every column of the nurse-rostering
  instance format. What this model has no field for is carried on an `Unencoded` object rather than
  discarded: per-employee limits, both request lists with their weights, per-slot cover weights, the
  "cannot follow" relation, and their own stated rest rule. Nothing is encoded and nothing is scored.
- **Alternatives.** Import and encode in one go. Import only the objective terms, leaving their
  constraints unread. Keep dropping what does not fit, which is the state this replaces.
- **Reason.** **The parse is the half that decides nothing.** Reading a parameter is reversible;
  encoding one is a rule in the model, the same rule in the checker, a differential case and a mutant.
  Splitting them let the data be looked at before anything was committed to, and looking at it moved a
  belief. **Their split of hard from soft is not the one this project would have guessed:** every
  per-employee limit carries no weight and is hard, so the items `preferences.md` calls *preferences*
  are constraints where they come from.
- **Consequences.** `load`'s third member is an `Unencoded` superset, so every existing caller is
  untouched. The parse is tested in CI against a **synthetic sample written in their format**, so the
  mutants do not report survivors on a machine that has not fetched the archives ([`D-112`](#d-112)'s
  failure mode). Still not established: **nothing about solution quality.**
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-133"></a>
## D-133. Their objective is scored, it reproduces every published value, and the incumbent it exposed was machine-dependent

- **Decision.** `foreign.score_their_objective` implements the nurse-rostering benchmark's own
  objective and is checked against the value each archive states in its solution's file name. All **26
  published values across 13 instances reproduce exactly**. Which published solution `load` returns is
  now named: `foreign.solutions(n)` orders them by objective and `load` takes the best.
- **Alternatives.** Score their objective without checking it against their values. Convert their
  weights onto this project's scale. Leave `load`'s pick alone.
- **Reason.** **The check is the point, not the scorer.** Implementing somebody else's objective is
  guesswork until a number confirms it, and their archives state one in the solution file's name:
  external, fixed, and not something this project can quietly adjust.

  **It also settles [`D-132`](#d-132)'s finding numerically.** Reproducing every published value without
  weekend or consecutive-day terms proves their objective excludes them: a missing term would show up
  as a shortfall on at least one of the 26, and none does.

  **The incumbent was being chosen by the filesystem.** `next(glob(...))` returned a **non-best**
  solution on 8 of 13 instances, and glob order is directory order, so which roster the study
  replanned was a property of the machine it ran on. That is [`D-118`](#d-118)'s defect in a second place,
  found this time by asking a different question of the same data.
- **Consequences.** **The study's replan table is re-measured**, because 8 of 13 incumbents changed;
  the claim is unaffected in direction and the numbers move.

  Scoring this project's own rosters under their objective is one call and is **not done here**: it
  needs their constraints encoded first, or the comparison comes back flattering.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-134"></a>
## D-134. Their constraints are read before they are encoded, and they bind hard

- **Decision.** Their seven per-employee constraints are implemented as `foreign.their_violations`:
  **one reading, in `benchmarks/`, with no rule IDs**: to answer whether they would bind on a roster
  this project produces before any of them is encoded. They do, on every case tried.
- **Alternatives.** Encode them first, in both readings with rule IDs and mutants, and find out
  afterwards whether they change anything. Skip the question and run the quality comparison now. Add
  them to `checker.py`, which is where a rule this product enforces belongs.
- **Reason.** **A rule costs two independent readings, and a measurement costs one.** None of these is
  such a rule yet: they are somebody else's operational limits, and the question is not *how do we
  encode this* but *does it matter here*.

  **The measurement is checkable against data this project did not choose.** Their rosters satisfy
  their own constraints, so a correct reading reports nothing on all 26. That caught a misreading on
  its first run: a minimum block applied at the horizon's edge failed **every one of the 26**, because
  a stretch touching either end may continue outside the window.

  **The result is not close.** Cold generation breaks **every one of the seven**, and the two the
  preference survey ranks highest are the worst: on one instance **all ten employees work all four
  weekends**, against a cap of two their own solver met exactly.
- **Consequences.** **The quality comparison stays blocked, now on evidence rather than on caution**:
  a roster breaking 154 rest-block constraints buys cover with a schedule their solver was never
  permitted to return.

  **It is also the strongest evidence `docs/preferences.md` has**: the same claim with a number on it,
  produced by somebody else's constraint set rather than by introspection.

  `their_violations` returns rule-name strings rather than `Violation` objects, deliberately: an ID
  would put them in a registry that states what this product enforces.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-135"></a>
## D-135. Two of their constraints become rules of this product, hard and optional

- **Decision.** `R-MAX-WEEKENDS` and `R-MIN-DAYS-OFF` enter the registry as **hard, optional**
  operational rules, encoded in both readings. Parameters are per employee, plus a caller-supplied
  `RuleParams.weekend_days` that is empty by default. Absent parameters mean the caller is not asking
  for the rule. The other five constraints [`D-134`](#d-134) measured are not encoded here.
- **Alternatives.** Benchmark-only encoding. Soft, priced in the objective, which is what
  `preferences.md` assumed these were. All seven at once. Derive the weekend from the clock.
- **Reason.** Building them benchmark-only would build them twice: [`D-134`](#d-134) measured this model
  breaking both on every case tried, and `preferences.md` ranks them among the things employees
  actually want. **Hard rather than soft on evidence rather than taste**: the only formulation
  measured against real data states both as constraints carrying no weight ([`D-132`](#d-132)). Hard does
  not mean unrelaxable: every hard constraint is gated, so a planner who must breach one gets a core
  naming it. **The weekend is asked for, never derived**: a week here is a position in the horizon and
  never a Monday. **Two, not seven**, because these carry both encoding shapes the rest reuse.
- **Consequences.** **The quality comparison stays blocked until all seven are encoded**, and saying
  so is the point of recording it. `R-MIN-DAYS-OFF` inherits [`D-134`](#d-134)'s boundary latitude as a
  specified rule rather than an implementation detail. Every `week` fingerprint moved and nothing else
  did: a schema change, not a generator or solver one, checkable in a minute because of
  [`D-074`](#d-074)'s split.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-136"></a>
## D-136. The rest of their constraint set, and the one rule that can refuse a roster

- **Decision.** `R-MIN-BLOCK`, `R-MAX-SHIFT-TYPE`, `R-MIN-HOURS` and `R-SUCCESSION` join the registry
  on [`D-135`](#d-135)'s terms. `R-CONSEC-DAYS` gains a **per-employee limit** rather than a second
  rule. All seven constraints [`D-134`](#d-134) measured are now encoded.
- **Alternatives.** Leave `MinTotalMinutes` out, since [`D-134`](#d-134) measured zero breaches. Give
  `MaxConsecutiveShifts` its own ID. Share one predicate between `R-MIN-BLOCK` and `R-MIN-DAYS-OFF`.
  An automaton for `R-SUCCESSION`.
- **Reason.** **`R-MIN-HOURS` earns its place by being different.** Every other rule here is satisfied
  by an empty roster; this is the only one a roster breaks by doing too *little*, so it is the only one
  that can conflict with `R-COVER`'s soft floor and produce a legitimate infeasibility. Gating it means
  the core names the rule rather than leaving a planner to infer it from a shortfall.
  **`MaxConsecutiveShifts` should not have got an ID**: `R-CONSEC-DAYS` already states it, and two IDs
  on one predicate is the failure the registry exists to prevent. **No shared predicate** between the
  two mirror-image rules: one predicate serving two rules breaks both readings of both at once.
- **Consequences.** A cap of zero in `R-MAX-SHIFT-TYPE` is a rule, not an impossibility, so it stays
  out of presolve's exclusions. **[`D-134`](#d-134)'s measurement is the gate, and it passes**: 31, 77
  and 198 breaches become zero. It cost **45–55% more variables**, and one instance turned a proof into
  a gap. So [`D-127`](#d-127)'s narrowing narrows again: a tenant enabling all seven over a month should
  expect a gap rather than a proof.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-137"></a>
## D-137. The quality comparison exists, and its caveat is larger than its result

- **Decision.** `foreign.compare` solves their instances with their constraints as this project's
  rules, their objective as the model's objective, and the coverage ceiling relaxed through its
  assumption literals: then scores the result against their published optimum. It runs, both
  implementations of their objective agree on every case, and **its numbers are not a claim that this
  solver is better.**
- **Alternatives.** Score a roster this model produced for its own objective, which measures nothing.
  Report 0.87× and 0.89× as wins. Withhold it until it is fair.
- **Reason.** **Two of three came back below the published optimum, and that is a red flag rather than
  a result.** 23 of their 24 solutions are proven optimal under their own objective, so a lower number
  means this comparison granted a freedom their solver did not have. It granted two.

  **Days off are dropped, not translated** ([`D-125`](#d-125)): 14, 20 and 36 constraints on the three
  instances, every one of which their solver honoured. **The rest rule was three hours weaker**, and
  closing it moved one instance from 1.16× to 1.11× and left two unchanged, so the days-off freedom
  is carrying the result.

  **The unfairness runs the other way too, and it does not cancel.** Their values are proved optima
  and all three of these solves returned `FEASIBLE` at a 300-second budget, so this side is a best
  effort against a proof.
- **Consequences.** What the comparison **does** establish: this project's stack can express their
  problem and solve it to a feasible roster, and two independent readings of their objective agree on
  every case: the independence rule applied to somebody else's objective.

  **Relaxing the coverage ceiling used the assumption literals for their stated purpose**, dropping
  exactly one gate and nothing else.

  **What would make it fair is a day-based availability rule.** Until one exists this stays as
  reported: a number with a bias of known direction and unknown size.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-138"></a>
## D-138. The reachability defect repeated, and the harness caught it by refusing to start

- **Decision.** The five wave-2 rule parameters join the wire contract alongside wave 1's two, and a
  round-trip test builds an instance using **all seven** rather than reaching for a committed scenario.
- **Alternatives.** Notice it later, which is what would have happened. Add a schema-completeness test
  that walks `domain` fields and asserts each has a wire counterpart: the general fix, and a bigger
  change than this one.
- **Reason.** **[`D-131`](#d-131) recorded exactly this defect and it happened again seven rules later.**
  Wave 2 encoded five parameters in both readings and added them to `domain.py`, and stopped there.
  `Strict` forbids unknown fields, so every one of them was rejected at the boundary: encoded, tested,
  specified, and unreachable by any caller.

  **The existing round-trip test could not see it**, for the reason [`D-131`](#d-131) already gave: it
  runs over committed cases, and none of them sets these fields. **A recorded lesson is not a control.**

  **What did catch it was the mutation harness refusing to start.** Three mutants could not find their
  anchors, stale precisely because the fields around them had changed. Its self-protection found a
  product defect while protecting itself from a stale catalogue.
- **Consequences.** Two of the three stale anchors were **ambiguous rather than missing**, for a reason
  [`D-136`](#d-136) chose on purpose: two mirror-image predicates are written twice so one cannot break
  both readings at once, which makes single-line anchors match twice. Both are re-anchored on the rule
  name: a small ongoing cost of the independence rule, paid here for the first time.

  **The general fix is not made here.** A test walking every `domain` field would catch the next
  instance without depending on anybody remembering; this record names it rather than pretending the
  round-trip test now covers the class.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.

<a id="d-139"></a>
## D-139. The harness reported a hole it did not have, and that is a fourth hardening

- **Decision.** `run` checks the mutation is **still in the file when the tests finish**. A mutant whose
  defect was reverted inside the test window is `voided` (neither caught nor survived) and its path
  joins `unvouched_for`, so the verdict is `unverifiable` rather than `survivors`.
- **Alternatives.** Treat it as a survivor and re-run by hand, which is what happened this time. Re-read
  the file before the tests as well, which narrows the window and does not close it.
- **Reason.** **The first three hardenings were the harness withholding a failure; this one is the
  harness inventing one.** It reported a survivor on a mutant that is caught decisively: applied by
  hand it raises `KeyError: -1` and fails twelve tests. The defect had been written away inside the test
  window, so pytest found nothing wrong because nothing was wrong. That reads as **a hole in a test
  layer**, which is the most expensive wrong answer this harness can give: it points at the layer rather
  than at itself, and the natural response is to write a test for ground already covered.

  **It falsified a sentence in `summarise`'s own docstring**: *"a mutant that survived, survived"* is
  not true when the mutation was gone before the tests ran. The docstring is corrected in place, because
  it is the reasoning the verdict rests on.
- **Consequences.** stdout gains `VOID` beside `CAUGHT` and `SURVIVED`. Two tests hold the pair that
  matters: a reverted mutant is not a survivor, and a genuine survivor is still one on a tree the run
  cannot vouch for: a fix turning real holes into shrugs would be worse than the defect.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.

<a id="d-140"></a>
## D-140. A rule whose test could not have failed, and the two runs that proved it

- **Decision.** The `R-MIN-HOURS` micro-instance sets a floor of 7.5 hours against three 7.5-hour
  shifts, where it used to set 15 against exactly 15. `run` records the catcher's output for any mutant
  it scores as a survivor, so the next one is diagnosable from the report.
- **Alternatives.** Read the survivor as harness flakiness, which two of the three survivors in these
  runs genuinely were and this one was not. Add a second instance rather than fixing the first.
- **Reason.** **The floor was set at exactly the hours on offer, so it could not be told from a
  ceiling.** Fifteen hours of open shifts and a 15-hour minimum: the only roster satisfying `≥ 15` is
  the full one, and `≤ 15` accepts that roster too. A reading that enforced the wrong comparison
  returned the same optimum, so the mutant survived: correctly, because nothing tested the direction.

  This is [`D-066`](#d-066)'s finding in a new rule: *a fixture set proves a rule exists; only a fixture
  at the boundary proves it is enforced at the right number*.

  **It took two trustworthy runs to see, and neither would have been trustworthy a day earlier.**
  [`D-139`](#d-139) stopped the harness inventing a survivor, and closing the editor stopped an
  auto-saved buffer reverting mutations mid-run.
- **Consequences.** **Two mutants remain intermittent and are recorded as open rather than explained.**
  Applied by hand they fail 12 and 9 tests; run through the harness alone, one was caught six times out
  of six. They are deterministic in isolation and intermittent inside a 132-mutant run, and that is the
  whole of what is known. *(Explained afterwards by [`D-141`](#d-141): CPython could not see the edit.)*

  **A correction belongs here.** The flakiness was attributed to autosave writing stale buffers back.
  That was real and was not the whole cause, because the survivor set still moved between two runs on a
  quiet tree.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.

<a id="d-141"></a>
## D-141. Fourteen mutants were never tested, because CPython could not see the edit

- **Decision.** The harness deletes the cached bytecode for any file it rewrites, after the mutation and
  after the restore, via a `_invalidate` helper.
- **Alternatives.** Touch the mtime forward after writing, which works until two writes land in one
  second again: the exact condition that caused this. Run each catcher with a fresh
  `PYTHONPYCACHEPREFIX`, which recompiles the world once per mutant. Keep treating the intermittent
  survivors as flakiness.
- **Reason.** **CPython validates a `.pyc` against the source's size and its mtime in whole seconds.** A
  mutation that changes neither is invisible to that check, so the interpreter loads the cached bytecode
  and runs the **original** code. The mutant then survives without ever having been tested, and the
  report says so in the language of a hole in a test layer.

  Proved rather than inferred: with the mutation on disk and the mtime left alone, a probe runs clean;
  with the same bytes and the mtime bumped two seconds, it raises the `KeyError` the mutation causes.

  **Fourteen of the 132 mutants are size-neutral**: swapping two identifiers, `>=` for `<=`, a range's
  bounds, and every survivor across four full runs was one of them.

  **This is worse than the four hardenings before it.** Those made the verdict untrustworthy in ways the
  report could state; this made a *`clean` verdict partly hollow*, and nothing anywhere said which
  mutants it applied to. Every earlier `clean` on this catalogue should be read with that caveat.
- **Consequences.** The three mutants that had been coming and going are caught on every run now, and
  **two causes wore the same costume**: one of them was a genuine hole [`D-140`](#d-140) fixed
  independently.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.

<a id="d-142"></a>
## D-142. A day off is not an interval, and that is a rule rather than a workaround

- **Decision.** `R-DAY-OFF` joins the registry as a hard, optional operational rule: an employee is not
  assigned any shift that **starts** on a day granted off. `Employee.days_off` is a set of day indices,
  both readings enforce it, and the importer stops dropping its source's days off.
- **Alternatives.** Translate a day off into an unavailability interval, which is the obvious mapping
  and is wrong. Leave them dropped. Widen `R-AVAIL` to take a day set as well as intervals.
- **Reason.** **The obvious translation is wrong at exactly one boundary, and that boundary is common.**
  A shift starting at 22:00 the evening before a granted day runs six hours into it and overlaps any
  interval covering that day, so an interval reading refuses a night shift the grant never meant to
  touch. Start-day attribution is what makes a day-indexed set exact where an interval is not.

  This was not reasoned from first principles: [`D-125`](#d-125) recorded it as a defect found from
  outside, when the first import flagged *every* night shift before a day off.

  **It is a third kind of unavailability**, not a variant of the two `R-AVAIL` has. That rule splits by
  provenance: an absence is never relaxable, a declared unavailability is. A granted day off is
  something the employer *gave*, which a planner may need to ask back.
- **Consequences.** **The external oracle confirms the reading**: their published rosters honour all 70
  granted days off across the three compared instances, where an interval translation reported a
  violation for every night shift before one.

  **This closes the freedom [`D-137`](#d-137) named.** What remains of that comparison's unfairness is
  the half running the other way.

  **A mutant found the layer this rule cannot be tested in.** The generator grants nobody a day off, so
  both readings agree perfectly about an instance where the rule never applies: [`D-108`](#d-108)'s note
  arriving in a second place.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Date.** 2026-08-17.

<a id="d-143"></a>
## D-143. A catch against a red catcher is not a catch, and CI found it before the harness did

- **Decision.** The harness checks **every distinct catcher passes before anything is mutated** and
  refuses to start if one does not, alongside the anchor pre-flight it already had. Checked once per
  catcher (25 runs rather than 132) because the question is about the tree, not about a mutation.
- **Alternatives.** Re-run each catcher per mutant, doubling a fourteen-minute run to answer the same
  question 132 times. Trust the suite to be green, which is what was being done and is exactly what
  failed.
- **Reason.** **A mutant is scored caught when its catcher fails.** A catcher that was *already* failing
  therefore scores every mutant it guards as caught without testing one of them, and the run reports
  that as a clean verdict.

  It happened here. [`D-140`](#d-140) rewrote a micro-instance and the golden record was not regenerated
  with it, so `tests/test_golden.py` was red from that commit onward. The full run that followed reported
  **132 of 132 caught, `clean`, `trustworthy: true`**: with one mutant scored on a test that could not
  have passed whatever the code did. What was wrong was the verdict's basis, not its answer.

  **CI found it, and that is the second time CI has caught something the local discipline could not**
  ([`D-118`](#d-118) was the first).
- **Consequences.** **The `clean` verdict for that run stands for 131 of its 132 mutants**: a smaller
  correction than [`D-141`](#d-141)'s and the same species: a verdict resting on something nobody checked.
  The refusal message names the failing tests, so the fix is visible without a second run, and the cost
  is under a minute against fourteen.
- **Study.** [`docs/studies/mutation-harness.md`](studies/mutation-harness.md)
- **Date.** 2026-08-17.


<a id="d-144"></a>
## D-144. Two overrides of different provenance are not one ranking, and the sweep was paying twice

- **Decision.** `whatif.recommend()` carries the `rule` it would relax and that rule's `provenance`,
  and sorts **within** a provenance rather than across one: operational asks first, then statutory,
  cheapest-first inside each group. It solves the unchanged instance **once** for the sweep rather
  than once per candidate, and tests at most five people by default.
- **Alternatives.** The flat cheapest-first list that shipped, whose demo output put a statutory
  relaxation on the top line, tied on points with two operational ones. Dropping statutory candidates,
  which hides a lawful option a planner may weigh. An order over rule kinds, which this project cannot
  derive from disruption.
- **Reason.** **Disruption cannot order two asks of different kinds.** Ignoring a skill requirement is
  a judgement the planner already owns; asking somebody to work further into a budget a statute caps
  is a different question at any price. A single sorted list says otherwise by its shape: the top
  line reads as the recommendation.

  **Nothing unlawful ever reached the list**: `validate_instance` refuses a cap above the absolute
  ceiling and `compare` returns that refusal, dropping the candidate. The defect was presenting
  lawful-but-different asks as comparable.

  **The cost was avoidable.** The baseline does not depend on which override is tested, yet `compare`
  re-solved it per candidate: 2N solves where N+1 does. Five candidates fell from 78 ms to 49 ms,
  output unchanged. Uncapped, the sweep is a solve per blocked person.
- **Consequences.** Two gaps remain, and are why the Open table's second row retires here rather than
  being answered: a candidate whose rule has no `Change` kind cannot be placed against one that has,
  and inside the statutory group disruption is still the only order, though `R-MAX-WEEKLY` and
  `R-MAX-DAILY` are not equally easy things to ask of a person. `compare` gains an optional `baseline`
  and an obligation with it: one from another instance or seed breaks the pairing.
- **Date.** 2026-08-20.

<a id="d-145"></a>
## D-145. Every statutory rule names an instrument, and two of the searches found no rule at all

- **Decision.** The five profile-gated rules and the three open items inside T1 rules now carry a
  named instrument, recorded in `rules.md` with the parameter each sets. Two searches returned a
  negative and the negative is recorded as the finding: **there is no 24-hour Dimona deadline** and
  **no horeca 3h48 minimum**. `R-SKILL-MIX` keeps its `[CITE]` permanently, because its provenance is
  declared per entry by the tenant, so no one instrument can be named.
- **Alternatives.** Deleting the five unsourced rows. Encoding them off the citations, which confuses
  naming a source with passing two independent readings. Leaving the two negatives open, which
  invites the same search a third time.
- **Reason.** **A citation search is worth running for what it refuses.** The NSSO defines a timely
  `FLX` filing as *"vóór de aanvang van de prestaties"*; the vendor 24-hour figure is tooling lead
  time with nothing behind it, narrowing what [`D-035`](#d-035) is conservative about: the bar is a filing that
  returns `OK` before the shift starts, not a day of notice. The horeca 3h48 claim traces to the
  Wet van 18 mei 2026 lowering the *general* part-time floor to a tenth of a full week; it does not
  reach PC 302, and art. 21 still carries `<W 1989-12-22/31>` as its last marker. This repeats what
  [`D-023`](#d-023) found for `R-CONSEC-DAYS`: the widely quoted rule did not exist.
- **Consequences.** A citation is not an encoded rule and the five stay outlines, held to *optional*
  by `tests/test_specs.py`. Two provenance lines are weaker and say so: `R-SUNDAY`'s art. 66 could not
  be read off the consolidated statute, every ejustice endpoint truncating before Chapter VI, and the
  flexi income ceiling is carried by three figures. `R-BREAK` arrives with a
  demand this registry cannot yet meet: its floor applies only where no CAO does, and no profile
  field says. `R-FLEXI-ELIG`'s T-3 test is unchanged; a pensioner branch is missing rather than wrong.
- **Date.** 2026-08-20.

<a id="d-146"></a>
## D-146. Four documents trimmed to what they carry, and the spec table made true

- **Decision.** A review pass removes material that no longer earns its place, as one change with one
  record. The T0 walking skeleton (`roster_replan/t0.py`) is deleted. `preferences.md` loses its
  twenty-three-item catalogue and its cost taxonomy, keeping what was measured. `finish.md` leads
  with the current state and carries the 2026-08-13 declaration below it, unedited. `capture.md`
  leaves the spec table in [`docs/README.md`](README.md).
- **Alternatives.** A record each, which is four records for one argument. Deleting `capture.md` and
  `preferences.md` outright, which loses the acceptance bar fixed before measuring and [`D-134`](#d-134)'s breach
  ranking. Rewriting the declaration so it reads true, which supersede-never-rewrite forbids.
- **Reason.** Each item failed one test: does a reader's attention buy anything here it does not buy
  elsewhere? `t0.py` sat in the shipped package only to be contradicted by `rules.md`. The catalogue
  was a roadmap, and a roadmap of unbuilt things is not evidence on a project that has declared
  itself finished. The declaration's first stretch is knowingly false in places: right for a record,
  wrong for the page a reader lands on. And a spec table promising *reconciled against the code*
  could not hold a row reading *specified, not built* and stay true.
- **Consequences.** 115 lines leave `preferences.md` and 184 leave the package. The declaration's body
  is byte-identical, checked by diff rather than by eye; its heading moved and one directional
  reference had to follow. `preferences.md` keeps the survey item IDs, because
  [`foreign-incumbent.md`](studies/foreign-incumbent.md) cites them. One planned trim was dropped on
  inspection: a scoping note here duplicated a limit [`horizon.md`](studies/horizon.md) already states better, so it was
  cut rather than moved.
- **Where those documents are now, 2026-09-02.** None of the four is in the repository under the name
  used above. What was measured in `preferences.md` is
  [`cross-week-reach.md`](studies/cross-week-reach.md); the declaration, the capture plan and the
  proposal catalogue are Tier 0. **This record is not the two-doors split**, which is
  [`D-151`](#d-151): it is the trim that preceded it by hours.
- **Date.** 2026-08-20.

<a id="d-148"></a>
## D-148. The README draws the claim it used to only tabulate

- **Decision.** `README.md` opens with a generated figure: one week of a 12-person roster drawn
  twice, a cold cost re-solve against the shipped replan. It is produced by
  [`benchmarks/figure.py`](../benchmarks/figure.py) from a committed case, never drawn by hand, and the SVG is committed
  beside the manifest it depends on.
- **Alternatives.** Drawing the demo scenario, which cannot carry it. A hand-made image, which
  cannot be checked against anything. No image, which is where this sat.
- **Reason.** A roster is a grid of people against days, and every reader of the results table has
  been rebuilding that grid in their head. The picture also shows the mechanism in a way a mean
  cannot: the cold solve moves three people nobody asked about, and a reader can count them.
  `scenarios/saturday_sick_call.json` had to be rejected as the source: at `now = 129` the week is
  pinned back to Saturday morning, so the cost baseline has nothing left to reshuffle and returns
  **the same single change** the replan does. That is true about late notice and useless about the
  objective, so the figure is `headline/1`, where Sunday is still movable.
- **Consequences.** A committed artifact can go stale and a caption can lie, so
  `tests/test_figure.py` asserts the file is what the generator still produces and counts the marks
  drawn against what `methods.run` reports; two mutants cover both failures. The figure inherits the
  reproducibility [`D-119`](#d-119) bought: against a degenerate optimum it would have flickered with the ortools
  build. It shows one case and says so on the page: six changes against two, where the set-wide
  means are 12.4 and 2.4.
- **Date.** 2026-08-20.

<a id="d-149"></a>
## D-149. The model cache is deleted, because its key was a claim that went stale

- **Decision.** `roster_replan/compiled.py` and `tests/test_cache.py` are deleted, with the
  thread-local store in `service/jobs.py`, the `built` argument on `ladder.answer`, and six mutants.
  `model.solve(built=...)` stays, because `benchmarks/` passes a model directly and owns the
  consequence. Nothing memoises a built model any more. **Retires [`D-093`](#d-093)**, which shipped
  the cache enabled on the argument that a miss is cheap and the repeating workloads are real: true,
  and beside the point once the key is a claim that goes stale without anything noticing.
- **Alternatives.** Adding the eight missing fields, which repairs today and not tomorrow. Adding
  them plus a structural test that every `Employee` field is fingerprinted or declared
  objective-only: correct, and still paying for a component measured at zero benefit.
- **Reason.** The fingerprint covered 12 of `Employee`'s 21 fields. Eight of the nine it missed
  carry hard rules and arrived *after* it was written ([`D-123`](#d-123), [`D-135`](#d-135), [`D-136`](#d-136), [`D-142`](#d-142)) and none
  revisited it. So two instances differing only in a granted day off share a key: warm the cache with
  one, ask for the other, and the service answers `OPTIMAL` with a roster breaking eight `R-DAY-OFF`
  instances where an honest solve returns INFEASIBLE. Only the independent checker caught it, which
  is [`D-003`](#d-003) earning its place. [`D-093`](#d-093) already measured the cache at **0 hits in 144 solves**, so this
  is a hazard attached to nothing, and removing it is cheaper than repairing it.
- **Consequences.** `service.md` asked for this component and now records that it was built and
  removed; the study stays, because the measurement is what justified deleting. The recurrence this
  closes is the general one: a key that must be updated whenever a field is added is a key that will
  be wrong. **The blind spot is the one [`D-131`](#d-131) already named**: a field the committed set does not
  supply is a field no test exercises, and `test_optional_rules.py` says as much in its own
  docstring. Two boundaries have now failed that way.
- **Date.** 2026-08-20.

<a id="d-150"></a>
## D-150. The guarantee starts at the payload, and the clock in front of it is the caller's

- **Decision.** No calendar or timezone handling enters this service. Instead two live documents say
  where the guarantee begins: [`api.md`](guide/api.md#time-is-hours-from-the-horizon-start) states how an offset is produced: by subtracting two
  zone-aware instants, never as `day * 24 + hour`, and [`limits.md`](guide/limits.md#what-it-guarantees) states that model/checker
  independence does not reach behind the payload.
- **Alternatives.** Accepting civil timestamps plus an IANA zone at the wire boundary and converting
  here, which reverses [`D-135`](#d-135) and moves the boundary without removing it, since the caller owns the
  system of record either way. Shipping a tested reference converter beside `demo.py`: the only
  option that makes the conversion testable, and the only one that costs a dependency and a second
  contract. Leaving it, which is where this sat.
- **Reason.** A local day is not always 24 hours. In `Europe/Brussels` the last Sunday of March is 23
  and the last Sunday of October 25, so on two weeks a year a caller multiplying days by 24 puts every
  offset after the change an hour out, and `R-REST-GAP` reads those offsets to the hour. `api.md` gave
  the unit and never the method. The deeper point is that [`D-003`](#d-003)'s independence buys nothing here:
  the model and the checker are independent of each other and read the *same* input, so a week
  described wrong is planned against and then certified against, and both agree. `limits.md` claimed
  every guarantee and scoped none of them: it did not contain the word *caller*.
- **Consequences.** The strongest claim this project makes is now bounded in the document that makes
  it. The same boundary already carries [`D-014`](#d-014)'s four quantities, so this scopes those too rather than
  naming only the clock. A tested converter stays **open, not rejected**: it is the one fix that turns
  an untested part into a tested part, and it waits for a second caller to say what shape it needs.
- **Date.** 2026-08-21.

<a id="d-151"></a>
## D-151. The documentation becomes two doors, and the reconciled specs move into them

- **Decision.** `docs/specs/` stops holding work orders. [`guide/`](guide/rules.md) is for people
  using the service and [`internals/`](internals/model.md) for people changing it, and each
  reconciled spec moves into the door its readers use: `rules.md` to the guide, `model.md` and
  `replan.md` into `internals/model.md`, `validation.md` into `internals/testing.md`, `service.md`
  into `guide/api.md`, `config.md` into `guide/configuring.md`.
- **Alternatives.** Keep the specs as specs and cross-link them from a guide. One door, sectioned.
  Keep both and let the specs be the source the guide summarises.
- **Reason.** **A spec that has been reconciled with its code is a description of the system**, so it
  belongs where people read about the system. Keeping both would leave two documents owning one
  claim, and the one nobody reads is the one that goes stale. Two audiences ask different questions
  of the same facts, and a single door serves whichever of them wrote it.

  `capture.md` is the exception that fixes the sorting test: it was specified and never built, so
  there is nothing to reconcile and it goes to Tier 0. The test is whether a document describes the
  system, not how old it is.
- **Consequences.** Nothing is left to say what each component found, which is what the
  [ledger](specs/README.md) answers, written in the restructure of 2026-09-02
  ([`documentation-restructure.md`](specs/documentation-restructure.md)) and reconstructed from
  evidence because the work orders were gone by then. A reader looking for the spec that owned a
  capability finds the row and the document it became. Rule IDs, numbers and claims moved unchanged.
- **Recorded late, 2026-09-02.** The split shipped without a record, and [`STATE.md`](STATE.md) and
  the ledger both cited [`D-146`](#d-146) for it: the trim that preceded it, which decides something
  else. Both citations now point here. A decision this size leaving no record is what the curation
  pass was for.
- **Superseded in part by [`D-152`](#d-152).** The move stands; the clause that `docs/specs/` stops
  holding work orders does not, because the build record went with the specs.
- **Date.** 2026-08-20.

<a id="d-152"></a>
## D-152. `docs/specs/` holds work orders again, and the twelve are reconstructions

- **Decision.** Every built component gets a spec file here, holding what a live document does not:
  the scope, the interfaces, the test contract, the gate it passed, what it ruled out, and the
  decision trail. Predicates, formulation and contract stay in [`guide/`](guide/rules.md) and
  [`internals/`](internals/model.md) and are cited, never restated. The twelve written on 2026-09-02
  are **reconstructions** and say so on their Status line.
- **Alternatives.** Leave the directory a ledger, as [`D-151`](#d-151) left it. Restore the seven
  deleted files. Move the predicates back into specs and make the live documents summaries.
- **Reason.** [`D-151`](#d-151)'s first half stands and its second does not. A reconciled spec is a
  description of the system, so moving it into the two doors was right. **What went with it was the
  build record**, and no live document carries that, because a live document says what is so now for
  a reader who was not there.

  Checked rather than assumed: the seven files deleted in `48e86d3` have no Status line, no build
  tasks, no gate, no out-of-scope and no decisions section. **This project never had a build record
  in this directory**, so the change creates a tier rather than restoring one, and restoring the
  seven verbatim would put a second owner on every predicate.
- **Consequences.** A reconstruction may not present itself as a work order, so three rules bind: the
  Status line names it one and its sources; a gate box is ticked only against evidence that exists
  now, cited on the line; the Decisions section cites records rather than inventing a trail.

  The sweep also found **88 citations in `roster_replan/`, `tests/` and `benchmarks/` naming a spec
  file deleted on 2026-08-20**, behind a green suite and a green linter, because the anchor check
  reads only Markdown links inside the doc set. Repointing them is a separate unit.
- **Spec.** [`docs/specs/spec-reconstruction.md`](specs/spec-reconstruction.md)
- **Date.** 2026-09-02.

<a id="d-153"></a>
## D-153. The gates carry search, and a faster builder is not what would lift the ceiling

- **Decision.** [`D-127`](#d-127)'s open question is answered and closed: **batching construction
  does not move the ceiling.** `build(gated=False)` ships as a **study switch** and is rejected as a
  mode. [`D-002`](#d-002)'s gates are confirmed on a reason they were not chosen for: they carry
  search, not only reporting.
- **Alternatives.** Write the `CpModelProto` directly. Ship the ungated build, rebuilding gated when
  a core is needed. Leave the question open, as [`D-127`](#d-127) left it.
- **Reason.** Both alternatives were built and measured, and both are nulls.

  **Writing the proto by hand is slower than the wrapper it bypasses**: 5.01 µs against 3.75 µs per
  gated two-term constraint, with `protobuf` already resolving to its C implementation.

  **Removing the gates halves the model and costs the proof of optimality.** On the committed set it
  takes 15% off build and 52% off search, helping on 28 of 28 paired cases. On a tight week it fails
  on three of eight, holding a roster scoring 480 for 30 s while the bound sits at −7980. Eight
  workers close it in 19 ms, so it is the single-worker search that depends on the literals, and
  that is how [`benchmarks.md`](benchmarks.md) measures.

  Why they help is measured and not explained: a bare model and one shared literal fixed true are
  both slow, so it is not enforcement propagating weakly.
- **Consequences.** The sentence *"that ceiling is a Python build loop, not a limit of the
  formulation"* is corrected wherever it appears. The bound is unchanged at about 40 employees over
  four weeks.

  [`cp-sat-vs-milp.md`](studies/cp-sat-vs-milp.md)'s **21% of search is bounded to the committed
  distribution**, and its *CP-SAT, ungated* row gains the code it never had.

  At the top of the range they are 89% of the model and presolve substitutes them away, never having
  been measured earning that cost at size.

  **The committed set could not have found this**, for the third time
  ([`D-105`](#d-105), [`D-127`](#d-127), [`penalty-search.md`](studies/penalty-search.md)).
- **Study.** [`docs/studies/gate-cost.md`](studies/gate-cost.md)
- **Spec.** [`docs/specs/gating-cost.md`](specs/gating-cost.md)
- **Date.** 2026-09-03.

<a id="d-154"></a>
## D-154. The canonical optimum is not canonical, and the criterion is why

- **Decision.** [`D-119`](#d-119)'s promise is **recorded as not held**. `Σ ordinal² · x` is not a
  total order over rosters, so pinning the optimal value and minimising it does not determine which
  optimum comes back. The claim in [`limits.md`](guide/limits.md) that a roster is reproducible from
  its input, seed and profile version is true on every committed case and is not true in general.
  Nothing is changed in the model yet.
- **Alternatives.** Fix it now with heavier weights. Say nothing, since no committed case is
  affected. Withdraw the reproducibility claim outright.
- **Reason.** Sums of squares collide. On `flexi-heavy/2` the gated and ungated builds each return a
  proved optimum, each report `canonical`, and they differ by six assignments at the identical
  criterion value 299,796: `6² + 85² + 161²` and `7² + 83² + 162²` are both 33,182.

  The committed manifest was stable because seed 7 on the shipped model landed on the same tied
  roster every time. That is the search deciding, which is exactly what [`D-119`](#d-119) exists to
  prevent, and it was hidden because nothing perturbed the search until something did.

  It is not fixed in the same change that found it. A criterion that cannot tie needs weights no two
  subsets can share, and a superincreasing sequence overflows int64 long before 60,000 variables, so
  this is a design question rather than a patch. Writing the record now is what keeps the promise in
  [`limits.md`](guide/limits.md) from standing unqualified while the question is open.
- **Consequences.** [`limits.md`](guide/limits.md) qualifies the reproducibility guarantee, and
  `test_suite.py`'s manifest test is understood as evidence that the *current* configuration is
  stable rather than that the roster is determined.

  This is [`reproducibility.md`](studies/reproducibility.md) one level in. That study removed the
  degeneracy the search could see and left a smaller set the criterion cannot separate, so
  *degeneracy measures zero* means *no tie was reached*, not *no tie exists*.
- **Study.** [`docs/studies/gate-cost.md`](studies/gate-cost.md), which found it
- **Date.** 2026-09-03.

<a id="d-155"></a>
## D-155. Their coverage rule is a band and ours is a ceiling, and three rows of the scale table said so

- **Decision.** The scale table in [`foreign-incumbent.md`](studies/foreign-incumbent.md) is corrected
  in place: instances 8, 10 and 23 no longer reproduce, and the cause is a **third mapping error in
  this project's importer**, not decay in the model. The hardness finding stands, re-measured. The
  claim that *the search finds nothing at eight million variables* is withdrawn. The fix to the
  importer is specified and **not built**.
- **Alternatives.** Retire the table. Fix `R-COVER`'s ceiling now and re-run. Leave the rows and note
  that they are old.
- **Reason.** Their format prices over-coverage on every slot of every instance; this project
  prohibits it with a hard gated `overage == 0` ([`D-018`](#d-018)) and the importer never reads their
  weight. A roster that overstaffs legally under their rules therefore imports as illegal, and where
  that falls in the pinned past the replan is refused before any search.

  Each row was recovered by reversing one cause at a time: instance 10 returns `OPTIMAL` in 2.22 s
  against 1.91 s recorded, and instance 8, on the solution the table used before
  [`D-133`](#d-133), in **8.43 s** against 7.71 s.

  **Instance 23 is the claim that falls.** It returns `INFEASIBLE` after a 561 s build, having never
  searched. Nothing is known about search at that size.
- **Consequences.** *"The first genuinely hard searches this project has seen"* survives and is now
  reproduced twice. *"At eight million the search finds nothing"* is withdrawn wherever it appears.

  **The illegality figure is inflated**: 10 of 13 published rosters have an illegal past, but **8 of
  13** excluding permitted over-coverage, and instances 1 and 10 become clean. What survives is
  `R-WEEKLY-REST`, the stricter-jurisdiction finding the study was written to make, so the correction
  narrows the claim without removing it.

  The fix changes a shipped predicate for a benchmark's benefit, so it is scoped in
  [`scale-evidence.md`](specs/scale-evidence.md) rather than taken here.
- **Study.** [`docs/studies/foreign-incumbent.md`](studies/foreign-incumbent.md)
- **Spec.** [`docs/specs/scale-evidence.md`](specs/scale-evidence.md)
- **Date.** 2026-09-03.

<a id="d-156"></a>
## D-156. The performance work is closed on five nulls, and the reason is the regime

- **Decision.** The effort to make this solver faster is **closed without shipping a speedup**. Five
  levers were measured and all five were rejected. No further performance work is scheduled, and
  [`scaling-levers.md`](studies/scaling-levers.md) is where the next person is sent before starting
  any.
- **Alternatives.** Build the disruption-radius restriction. Promote the rolling horizon out of
  [`horizon.md`](studies/horizon.md). Write the model builder in a compiled language. Leave the
  question open.
- **Reason.** Nothing measured helps in the regime this service serves. A committed case is 8 to 25
  employees over one week and answers in about 3 ms of search, so there is no latency to recover.

  The five: a hand-written proto builder is **slower** than the wrapper; removing the gate literals
  loses the proof of optimality ([`D-153`](#d-153)); the interval rest-gap encoding cuts variables by
  7.1× on a large instance and is **slower to search** at every size tried; parallel workers change a
  replan not at all; and the generator cannot reach the sizes where any of it would matter.

  The remaining levers are large and none of them is aimed at a measured problem. Building one would
  be answering a question nobody has asked of this service.
- **Consequences.** [`limits.md`](guide/limits.md) keeps its envelope and gains nothing, which is the
  honest outcome. **A performance claim in this repository now needs a regime attached**, because the
  one thing every null shares is that it was decided by the distribution rather than by the lever.

  It also bounds [`D-105`](#d-105) from the other side: the generator *can* produce an instance the
  solver fails to prove optimal, at 100 employees over 8 weeks, which is far outside the envelope this
  service claims and is why it was never seen.
- **Study.** [`docs/studies/scaling-levers.md`](studies/scaling-levers.md)
- **Date.** 2026-09-03.
