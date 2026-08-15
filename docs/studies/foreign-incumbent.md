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
the disruption objective cuts changed assignments by **10× to 27×** where the committed set showed
about 5×. Two things came with it that the synthetic set could not have shown: **7 of 13 published
rosters have a past this model calls illegal**, and a defect in the canonical optimum that appeared
within minutes of first contact.

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

With both corrected, **55 genuine hard violations across 6,361 assignments — 0.86%**.

## What is left is Belgium being stricter

| rule | why it fires |
| --- | --- |
| `R-WEEKLY-REST` | 35 uninterrupted hours a week. Their model has no weekly rest rule at all |
| `R-COVER` (hard) | overstaffing. They price it softly; `D-018` makes the ceiling hard |
| `R-MAX-WEEKLY` | one instance exceeds even the 50h absolute ceiling in a single week |

None of these is a defect in their rosters. They are lawful under the rules they were built for, and
this is what it looks like when a roster meets a jurisdiction it was not written for — which is the
situation a real deployment is in.

## The claim, on foreign incumbents

A single absence is injected mid-horizon on a rostered employee, and the four-method comparison runs
unchanged — the foreign scenario is a `generator.Scenario`, so it flows through the same
`methods.run` as every committed case.

| instance | staff | weeks | cold re-solve | warm replan | changed assignments |
| --- | --- | --- | --- | --- | --- |
| 2 | 14 | 2 | 980 | **80** | 74 → **2** |
| 3 | 20 | 2 | 1,800 | **140** | 114 → **8** |
| 6 | 18 | 4 | 2,860 | **280** | 220 → **22** |
| 8 | 30 | 4 | 4,770 | **210** | 375 → **15** |
| 10 | 40 | 4 | 7,560 | **280** | 606 → **22** |

**Between 10× and 27× fewer changed assignments**, against about 5× on the committed set. The margin
is wider because the instances are larger — a cold re-solve of a four-week roster for 40 people
reshuffles 606 assignments to absorb one absence, where a week for twelve reshuffles twelve. The
direction of the effect is the same and its size is a property of the instance.

**This is the headline claim on rosters this project did not produce**, which is the thing every
number in `benchmarks.md` could not say.

## Seven of thirteen have an illegal past

`R-PIN-PAST` fixes everything before `now`, so a hard violation in that region makes the replan
infeasible by construction — "the past itself is illegal", distinct from "no legal future exists".
It has a ladder rung and a differential test, and until now **no natural instance anywhere in this
project**. Foreign data supplies seven of them.

| | instances |
| --- | --- |
| past clean, replan measured | 2, 3, 6, 8, 10 |
| past already illegal | 1, 4, 5, 7, 9, 11, 12, 13 |

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

## What this does not establish

**Nothing about solution quality.** Their objective is a weighted sum of soft preferences — shift-on
and shift-off requests, weekend counts, minimum consecutive days off — and none of it is imported.
Their published objective values are not comparable with anything here, and no claim in this study
depends on them. The rosters are used as incumbents and for nothing else.

**Not a replacement for capture.** These are nurse rosters from published research, not Belgian horeca
rosters from a vendor. `capture.md` still owns the corpus question. What has changed is that the
incumbent is no longer *always* this project's own output, which was the sharpest form of the
objection.

**Five comparisons.** The instances with a clean past are the ones that could be measured, and there
are five of them.
