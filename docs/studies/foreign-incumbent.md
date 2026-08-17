# Replanning a roster this project did not produce

**Question.** [`benchmarks.md`](../benchmarks.md) has carried the same caveat since T2, and
[`finish.md`](../finish.md) calls it the largest single gap in the evidence:

> **The incumbent is solved by the system under test.** Every benchmark number here shows that a
> replan beats a re-solve *given a roster this model would produce*, not that the model resembles
> what real planners publish.

[`capture.md`](../specs/capture.md) was written to close that with a captured corpus, and is blocked
on an authorization this project does not control. This is the half that is not blocked.

**Answer. The claim reproduces on foreign incumbents, and by a wider margin than on the committed
set.** Against a cold cost re-solve on published rosters from the nurse-rostering benchmark set,
the disruption objective cuts changed assignments by **5× to 37×** where the committed set showed
about 5×. Two things came with it that the synthetic set could not have shown: **10 of 13 published
rosters have a past this model calls illegal**, and a defect in the canonical optimum that appeared
within minutes of first contact.

> **Re-measured on named incumbents** (`D-133`). This study originally reported 10× to 27× over five
> instances, on whichever published solution `glob` happened to return — which was a **non-best**
> solution on 8 of the 13 and depended on directory order, so the incumbent was a property of the
> machine. `load` now takes the best published solution by their own objective. Three instances have
> a clean past instead of five, the direction of the claim is unchanged, and its bottom end is
> weaker: one instance repairs at 4.6× where the old sample's weakest was 10×.

    uv run python -m benchmarks.foreign --fetch
    uv run python -m benchmarks.foreign --study

## Where the rosters come from, and what is committed

The [nurse rostering benchmark instances](https://www.schedulingbenchmarks.org/nrp/) ship 24
instances with published solutions, 23 of which are proven optimal under *their* objective. Those
solutions are what makes them useful here: a roster produced by another solver optimising a goal this
project does not implement is exactly what the generator cannot make.

**The site states no licence, no copyright and no terms**, which means default copyright rather than
public domain. So nothing is redistributed: `benchmarks/foreign.json` commits the URLs and their
SHA-256, the data is fetched on demand and verified against them, and a mismatch deletes the file
rather than proceeding (`D-125`). It is `D-073`'s pattern — the benchmark manifest already commits
fingerprints instead of payloads — and it keeps `README.md`'s *all data committed here is synthetic*
true.

## The mapping, and the two versions of it that were wrong

Their model is day-based with a "cannot follow" relation between shifts; this one is clock-based. The
clock exists in the XML form of each instance, so rest gaps are computed from their own start times.
Everything else that maps, maps: cover requirements, maximum consecutive shifts, shift lengths.

The first import reported **0 of 24 rosters legal**, and both reasons were mine.

**A weekly rate they never stated.** Their staff records carry `MaxTotalMinutes` over the horizon and
no weekly figure, so the first version derived one by division. That flat average forbids precisely
the uneven spending a pool permits, and it accounted for 60-80% of every reported violation. It is
`D-123`'s finding arriving from outside: their rosters spend a quarter unevenly because they may, and
a rate invented from a pool calls that illegal. `MaxTotalMinutes` is `max_hours_this_period` and
nothing else.

**Days off translated into intervals.** Theirs forbids an assignment *on* a day; ours is interval
overlap, and a night shift starting at 22:00 the evening before spills six hours into it. Every
`R-AVAIL` violation reported was a night shift the day before a day off — the start-day attribution
convention `rules.md` fixes, colliding with a naive translation. Days off are now dropped rather than
approximated.

With both corrected, **70 genuine hard violations across 6,363 assignments — 1.10%** on the best
published solution of each instance.

That figure was 55 across 6,361 when the incumbent was whichever `glob` returned (`D-133`). Almost
the same number of assignments, 27% more violations — but **there is no consistent direction**
between a better and a worse published roster: the same count over each instance's *worst* published
solution is 73, and per instance it moves both ways. What the old number measured was a particular
arbitrary sample, and what replaces it is a named one.

## What is left is Belgium being stricter

| rule | why it fires |
| --- | --- |
| `R-WEEKLY-REST` | 35 uninterrupted hours a week. Their model has no weekly rest rule at all |
| `R-COVER` (hard) | overstaffing. They price it softly; `D-018` makes the ceiling hard |
| `R-MAX-WEEKLY` | one instance exceeds even the 50h absolute ceiling in a single week |

None of these is a defect in their rosters. They are lawful under the rules they were built for, and
this is what it looks like when a roster meets a jurisdiction it was not written for — which is the
situation a real deployment is in.

Two of those rows are no longer read off the rosters alone (`D-132`). *"They price it softly"* is now
their own number: the imported cover weights are **100 for one position short and 1 for one over**, on
every slot of every instance, so overstaffing is the cheapest thing their objective can buy and
`D-018`'s hard ceiling is what turns it into a violation. And the rule that is **not** in the table is
the informative one — `R-REST-GAP` fires nowhere, because their own `MinRestTime` of 14 hours is
stricter than the 11 imposed on them. An empty column that is explained is worth more than a full one
that is not.

## The claim, on foreign incumbents

A single absence is injected mid-horizon on a rostered employee, and the four-method comparison runs
unchanged — the foreign scenario is a `generator.Scenario`, so it flows through the same
`methods.run` as every committed case.

| instance | staff | weeks | cold re-solve | warm replan | changed assignments |
| --- | --- | --- | --- | --- | --- |
| 2 | 14 | 2 | 980 | **80** | 74 → **2** |
| 4 | 10 | 4 | 1,820 | **380** | 146 → **32** |
| 6 | 18 | 4 | 2,860 | **280** | 220 → **22** |

**Between 4.6× and 37× fewer changed assignments**, against about 5× on the committed set. The margin
is wider on the larger instances because a cold re-solve of a four-week roster reshuffles hundreds of
assignments to absorb one absence, where a week for twelve reshuffles twelve. The direction of the
effect is the same on every case and its size is a property of the instance.

**The spread is much wider than the old sample suggested**, and that is the substance of `D-133`'s
re-measurement rather than a detail of it. Instance 4 repairs at 4.6× — below the committed set's
average, and below anything the previous five-instance table contained. A claim quoted as a range is
only as good as the sample the range came from, and this one's sample was chosen by directory order.

**This is the headline claim on rosters this project did not produce**, which is the thing every
number in `benchmarks.md` could not say.

## Ten of thirteen have an illegal past

`R-PIN-PAST` fixes everything before `now`, so a hard violation in that region makes the replan
infeasible by construction — "the past itself is illegal", distinct from "no legal future exists".
It has a ladder rung and a differential test, and until now **no natural instance anywhere in this
project**. Foreign data supplies ten of them.

| | instances |
| --- | --- |
| past clean, replan measured | 2, 4, 6 |
| past already illegal | 1, 3, 5, 7, 8, 9, 10, 11, 12, 13 |

That is not a mapping artifact — it is what a published roster looks like when a stricter rule set
arrives after it was written, and any deployment importing historical rosters will meet it on day one.
The ladder's `incumbent` rung exists for exactly this and now has evidence rather than a code review.

## The defect this found in a fix made the same day

Canonicalising the optimum (`D-119`) added a second solve phase and asserted that it could not fail:
*the phase-one solution satisfies every constraint here, including the pin*. True of feasibility, and
silent about proving a criterion optimal over a face with millions of points. Instance 10 — 40
employees, four weeks — raised that assertion on first contact (`D-126`).

Two defects, not one. Phase two could exceed the caller's budget, because it was given a fresh copy
of `max_time_in_seconds` rather than what remained; and when it could not finish, the answer was an
exception rather than a roster. Both are fixed, and `Solution.canonical` now says which kind of
optimum came back.

**The committed set could not have found this.** Every instance in it is small enough that phase two
finishes in milliseconds. That is the argument for foreign data in one sentence.

## How far the model goes

Every performance number in this repo is measured on 8-25 employees over one week, and `D-104`
retired LNS on the grounds that nothing ever fails to prove optimality. Both are statements about a
distribution this project generated for itself. These instances run to 150 employees over 52 weeks
and were built by other people for other purposes, which is the only way to find where the model
stops. The **replan** is measured, not a cold solve: the published roster pins the past, which is the
regime the service is actually for.

| instance | staff | weeks | variables | constraints | build s | search s | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 14 | 2 | 1,944 | 2,140 | 0.01 | 0.03 | OPTIMAL |
| 6 | 18 | 4 | 7,231 | 9,522 | 0.06 | 0.48 | OPTIMAL |
| 8 | 30 | 4 | 18,855 | 29,805 | 0.17 | **7.71** | OPTIMAL |
| 10 | 40 | 4 | 32,392 | 51,243 | 0.30 | 1.91 | OPTIMAL |
| 13 | 120 | 4 | 910,498 | 1,604,811 | **9.32** | — | infeasible past |
| 20 | 50 | 26 | 308,301 | 413,805 | 9.38 | — | infeasible past |
| 21 | 100 | 26 | 1,060,803 | 1,752,026 | **45.07** | — | infeasible past |
| 22 | 50 | 52 | 1,546,273 | 2,228,062 | **67.16** | — | infeasible past |
| 23 | 100 | 52 | 8,049,059 | 14,786,635 | **527.45** | 16.46 | **UNKNOWN** |

**The search is genuinely hard here, for the first time in this project.** Instance 8 takes **7.71
seconds** of search to prove optimality, against a committed-set maximum of **15.4 ms** across all
2,268 runs. That is a factor of 500, and it is the answer to the standing objection that nothing in
this repo is ever hard. `D-104` retired LNS because every solve returned `OPTIMAL` in milliseconds;
that reasoning is now bounded by a distribution rather than general, and instance 23 is a case where
the search returns nothing at all.

**The binding constraint is model construction, not search.** At every size, building the CP-SAT model
in Python costs more than searching it — 9 seconds at 910k variables, 45 at 1.1M, 67 at 1.5M, and
**527 seconds at 8M**. Instance 23 spends nearly nine minutes constructing a model the solver then
fails to crack in its budget. `D-081` separated the two clocks because build dominated at one week
for 12 people; it still dominates at 52 weeks for 100, by a wider margin and for the same reason.
That makes `D-092`'s memoisation — the largest single win in the solve path, found by profiling the
builder rather than the solver — the correctly aimed piece of work at both ends of the scale.

**Instance 24 was abandoned.** 150 employees, 52 weeks, 32 shift types — after roughly forty
minutes it had still not finished *building* the model, and it was stopped rather than waited out.
That is reported as what happened rather than as a measurement: the run does not know whether it
would have completed in an hour or never, only that nine minutes of build at instance 23's size was
not the ceiling.

**Where it stops is now a number rather than a guess.** Up to about 40 employees over four weeks, the
service proves optimality and canonicalises inside a few seconds. Past roughly a million variables the
build alone leaves interactive latency behind, and at eight million the search finds nothing. Nothing
between those points has been measured, because these instances do not sample it.

## Their objective, reproduced to the digit

The archives state each published solution's objective value **in its file name** —
`Instance1.Solution.607.roster`. That makes it an external number: fixed before this project existed,
and not one this project can quietly adjust to make an implementation look right.

`foreign.score_their_objective` implements their objective and reproduces **all 26 published values
across all 13 instances, exactly** (`D-133`). Their whole objective is:

```
Σ_slots  under_weight × max(0, required − assigned)  +  over_weight × max(0, assigned − required)
  + Σ_on_requests   weight  where the shift was not assigned
  + Σ_off_requests  weight  where it was
```

**The brevity is the finding.** Twenty-six exact matches with no weekend term, no consecutive-days
term and no sequence term is proof that those are constraints in their formulation rather than
objective components — the same conclusion `D-132` drew from reading which elements carry a `weight`
attribute, now settled arithmetically. A missing term would have to show up as a shortfall on at
least one of the 26, and none does.

This is the strongest external check any component in this repo has. Every other correctness claim
here rests on two readings this project wrote agreeing with each other; this one rests on numbers
somebody else published.

## Their constraints, and what this model does without them

Their objective can now score any roster, including this project's. Running that comparison today
would flatter this side, and `foreign.their_violations` measures by how much rather than leaving it
as a caution (`D-134`).

It is **one reading, in `benchmarks/`, with no rule IDs** — a rule this product enforces costs two
independent readings, and the question in front of these is not how to encode them but whether they
matter here. It carries the same external check the objective does: their published rosters satisfy
their own constraints, so a correct reading reports nothing on all 26, and it does.

*(That check earned its place immediately. A minimum block length applied at the horizon's edge
failed every one of the 26, because a stretch touching either end may continue outside the window.
Read as 26 wrong rosters it is absurd; read as one rule applied too strictly it is the boundary
latitude `R-WEEKLY-REST` already gets. A maximum needs none and gets none.)*

Cold generation under this project's objective, on the three instances with a clean past, checked
against their constraints:

| constraint | survey item | breaches |
| --- | --- | --- |
| `MinConsecutiveDaysOff` | E7 — days off in blocks | 154 |
| `MinConsecutiveShifts` | E1 — block length | 67 |
| `Succession` | E8 — quick returns | 38 |
| `MaxWeekends` | E4 — weekend load | 34 |
| `MaxShifts` per type | — | 18 |
| `MaxConsecutiveShifts` | — | 3 |
| `MinTotalMinutes` | E3 — hours floor | 0 |

**Every constraint but one is broken, and the two the preference survey ranks highest are the worst.**
Counted per person rather than per breach, the weekend result is the one to quote:

| instance | staff | over their weekend cap | their cap | worst here | worst theirs |
| --- | --- | --- | --- | --- | --- |
| 2 | 14 | 7 of 14 | 1 | 2 | 1 |
| 4 | 10 | **10 of 10** | 2 | 4 | 2 |
| 6 | 18 | 17 of 18 | 2 | 4 | 2 |

On instance 4 **every employee works every weekend of the month** — four out of four, against a cap of
two that their own solver met exactly. Nothing here is a defect: the rosters are optimal for the
objective this project states, and that objective is silent on all of it. This model has no opinion
about weekends, block lengths or shift successions, and this is what having no opinion produces.

That makes this the strongest evidence [`../preferences.md`](../preferences.md) has. The survey
argued from first principles that the objective says nothing about structure across weeks; this is
the same claim with a number on it, produced by somebody else's constraint set rather than by
introspection, and it ranks the survey's items by how badly each is currently ignored rather than by
how plausible each sounded.

**All seven are now rules of this product** (`D-135`, `D-136`), hard and optional, encoded in the
model and the checker and carried into brute-force ground truth by nine micro-instances.
`MaxConsecutiveShifts` is the exception that proves the shape: it got no rule ID, because
`R-CONSEC-DAYS` already states that predicate and only needed a per-employee limit.

**The measurement that motivated the work is the check that it worked.** Asked to hold their
constraints, this model now produces rosters that satisfy all seven where it previously broke six:

| instance | staff | breaches before | breaches after |
| --- | --- | --- | --- |
| 2 | 14 | 31 | **0** |
| 4 | 10 | 77 | **0** |
| 6 | 18 | 198 | **0** |

**The rules are not free, and the honest version of the price is narrower than the first one written
here.** Measured against the same instances solved without them, at a 120-second budget:

| instance | staff | weeks | without the rules | with them | variables | added |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 14 | 2 | `OPTIMAL`, 58 s | **`FEASIBLE`, hit the budget** | 1,750 | +786 |
| 4 | 10 | 4 | `OPTIMAL`, at the budget | `FEASIBLE`, at the budget | 2,598 | +1,430 |
| 6 | 18 | 4 | `OPTIMAL`, at the budget | `FEASIBLE`, at the budget | 6,493 | +3,527 |

**Instance 2 is the only clean before-and-after**, and it is a real degradation: optimality proved in
58 seconds becomes a feasible roster with a gap. Instances 4 and 6 were already consuming the whole
budget *without* the rules — reported `OPTIMAL` because the proof lands in phase one and `D-119`'s
canonicalising phase spends what is left — so they cannot carry a claim about the rules' cost either
way. The first draft of this paragraph said these instances proved optimality "in single-digit
seconds", which is `D-127`'s figure for a different instance under a different measurement, and the
numbers above contradict it.

What the variable counts do support on all three is the size: **45% to 55% more variables**, which is
the seven rules' encoding rather than an interaction with anything.

So the claim `D-104` and `D-127` have been narrowing narrows once more, and only by as much as one
instance carries: `OPTIMAL` in milliseconds was a statement about the regime this project serves *with
the objective it shipped*, and switching on rules a tenant may legitimately want is enough to leave
it (`D-136`).

## The quality comparison, and why its number is not a win

    uv run python -m benchmarks.foreign --compare

Their constraints as this project's rules, their objective as the model's objective, their coverage
semantics — the ceiling relaxed through its own assumption literal, because their formulation prices
overstaffing at 1 where `D-018` forbids it. Scored against their published optimum, at a 300-second
budget:

| instance | staff | weeks | published optimum | this project | ratio | status |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 14 | 2 | 828 | 719 | 0.87× | `FEASIBLE` |
| 4 | 10 | 4 | 1,716 | 1,524 | 0.89× | `FEASIBLE` |
| 6 | 18 | 4 | 1,950 | 2,167 | 1.11× | `FEASIBLE` |

**Two of three are below a proved optimum, which is a red flag and not a result** (`D-137`). Their
solutions are proven optimal under their own objective; a lower number means this comparison handed
this project a freedom their solver did not have. It handed over two.

**Days off are dropped, not translated**, which this study has recorded since `D-125` as an import
decision and which turns out to be a quality-claim problem: **14, 20 and 36 constraints** on these
three instances, every one honoured by their solver and ignored here.

**The rest rule was three hours weaker, and that one is closed.** `as_rules` now takes their stated
`MinRestTime` of 14 hours rather than imposing Belgium's 11. It moved instance 6 from 1.16× to 1.11×
and left the other two unchanged — a small freedom, which is what leaves the dropped days off carrying
the result.

**The bias runs both ways and does not cancel.** Their values are proofs; all three of these are
best efforts at a budget. That cuts against this project while the dropped days off cut for it, and
two unmeasured biases in opposite directions are not a fair comparison.

What the run *does* establish: this project's stack can express their problem and solve it, and the
two implementations of their objective — one as CP-SAT terms, one as a scorer — agree on every case,
asserted in the study rather than assumed.

**What would make it fair is a day-based availability rule.** `R-AVAIL` is interval overlap by design
and cannot say "no shift starting on this day" without the start-day collision `D-125` describes. Until
one exists, this table is a number with a bias of known direction and unknown size.

## What this does not establish

**Not a fair quality comparison.** The table above is a comparison and it is not yet a fair one: the
dropped days off hand this project a freedom their solver did not have, and the missing proof of
optimality takes one back. Both are named and only one is sized.

This limit has moved three times and is worth reading as a sequence. It began as *"nothing about
solution quality — none of their objective is imported"*. Their instances are now **imported in full**
(`D-132`), their objective is **implemented and checked against 26 published values** (`D-133`), their
constraints are **encoded as rules in both readings** (`D-135`, `D-136`), and the comparison **runs**
(`D-137`). What is left is one import decision — days off — rather than a missing component.

The import along the way also corrected the sentence this paragraph used to carry, which described
their objective as
"a weighted sum of soft preferences — shift-on and shift-off requests, weekend counts, minimum
consecutive days off". **Only the first of those is in their objective.** Weekend counts and
consecutive days off carry no weight in the `.ros` form and are hard constraints; their objective is
the two request lists plus per-slot under- and over-cover weights. The distinction matters for
anything built on top: the items [`../preferences.md`](../preferences.md) catalogues as preferences
are rules where these rosters come from.

**Their rest rule is stricter than the one imposed on them**, which turns an empty column into
evidence. The `.txt` form states no rest gap — the reason this importer applies Belgian parameters —
but the `.ros` form states `MinRestTime` 840 minutes, 14 hours, on all thirteen instances against the
11 imposed here. `R-REST-GAP` cannot fire on a published roster and never does. A mistranslated start
time would put shifts closer together than either rule allows, so the empty column is a check on the
importer's clock rather than an absence of one.

**Not a replacement for capture.** These are nurse rosters from published research, not Belgian horeca
rosters from a vendor. `capture.md` still owns the corpus question. What has changed is that the
incumbent is no longer *always* this project's own output, which was the sharpest form of the
objection.

**Three comparisons.** The instances with a clean past are the ones that could be measured, and on
named incumbents there are three of them rather than five (`D-133`). A range quoted from three cases
is a range with three points in it, and the honest reading of 4.6× to 37× is that the effect is
large and its size is not characterised.
