# Finish declaration

> **Two documents in one file.** Everything under *The declaration* is as it was written on
> 2026-08-13, when T3 was the finish — **including the sentences later work made false**, because a
> record that gets edited whenever the world moves is not a record. That is the rule `decisions.md`
> already runs on: supersede, never rewrite. The bracketed notes inside it are the only additions and
> they point forward — that, and the heading levels, which were demoted one step so the two
> parts nest. No words inside it were changed.
>
> Everything under [*After the declaration*](#after-the-declaration) is what has happened since, held
> to the same standard: what shipped, what it cost, what it got wrong, and what is still not done.
> **For the current state of the project, start there** — the section below is history, and one of
> its claims (*"T4 and T5 were always upside and remain unbuilt"*) stopped being true on 2026-08-14.

## The declaration (2026-08-13)

**T3 is complete. The project is finished in the sense `PLAN.md` defined**: T0 through T3 shipped,
every tier gate passed on evidence rather than on prose, and every spec reconciled with its code.
T4 and T5 were always upside and remain unbuilt.

This document is the declaration `PLAN.md` required, and its job is to be **checkable rather than
celebratory**. What is not done is listed with the same care as what is, because a finish declaration
that only lists achievements is the failure mode this project was built to avoid.

Date: 2026-08-13. Nineteen commits.

### The gates, and what passed them

| Tier | Gate | Passed by |
| --- | --- | --- |
| T0 | something solves, inspectable by eye | the walking skeleton |
| T1 | the repo is trustworthy — a reviewer can see why the model is what the spec says | two independent readings, five test layers, brute-force ground truth |
| T2 | the headline claim is proven against baselines, on a stated instance distribution | four methods over 72 committed cases, both axes, seven studies |
| T3 | production surface | async job service, fallback ladder, telemetry, fairness, model cache |

*(The set is 84 cases since `D-105`. The greedy comparison is re-measured over all of them; the other
T2 analyses are not, and the two added classes sit outside their basis.)*

**None of these could be passed by writing.** T1 needed a checker that disagrees with the model when
one of them is wrong. T2 needed numbers that could have come out the other way, and several did. T3
needed a service that runs.

### What the project measured, including what it got wrong

The headline claim held: **the disruption objective cuts mean disruption from 323 to 66** against a
cold cost re-solve. The rest of the results are more interesting than that, because a majority of the
levers this project expected to matter did not.

| Claim | Outcome |
| --- | --- |
| Disruption objective beats a cold re-solve | **Held** — 323 → 66 |
| Warm starting is a major speedup | **9% of search time**, invisible end to end |
| Greedy repair is a weak baseline | **Ties the optimum on 64 of 72 cases** — 71 of 84 once the coverage axis was sampled in the middle (`D-105`) |
| Presolve is "often the largest single win" | 28% off build — real, not the largest |
| Symmetry breaking helps | **Null** — 3 interchangeable employees in 24 cases |
| The `regular` automaton wins | **Rejected** — 20% slower; one window to replace |
| Pattern/column variables are "dramatically stronger" | **Rejected** — no proof of optimality in 30 s |
| Caching the compiled model is the big latency win | **0 hits in 144 replan solves** |
| — | The real win was memoising one method: **20% off build** |
| CP-SAT is the right solver for this | **Not for speed** — SCIP proves the same optimum faster on 24/24 |

Six of those contradict something a spec or an outline asserted before it was measured, and each is
recorded as a correction with the original reasoning left intact (`D-082`, `D-087`, `D-088`, `D-009`,
`D-093`, `D-001`). That was the point of the rhythm.

**`D-001` was the last one written**, and it is the sharpest: the project's founding solver choice
turns out not to be justified by speed. CP-SAT ships because assumption literals, `violations()` and
non-linear expressiveness are load-bearing for three other commitments — at a measured cost of about
1.3 ms per solve, against a model build costing four times that.

**The D0–D4 study delivered what `replan.md` promised**: the five metrics genuinely disagree, on
23 of 72 cases, at roughly 100% relative regret in both directions — and the divergence found in the
wild reproduces the Ana/Bram example the spec invented to argue it was possible. *(Re-run over the
widened set: 26 of 84, same structure, and `D-060` confirmed on a curve — `D-106`. Then 10 of 84
once `D-119` moved the instances underneath it, which is what that rate turned out to measure; the
structure held and the curve did not — `D-120`.)*

### What is not done

#### Scheduled and not delivered

**Capture and replay** ([`specs/capture.md`](specs/capture.md)) is the one component `PLAN.md`
scheduled inside a completed tier that does not exist. It never gated T2, by design: corpus
population depends on an external authorization this project does not control, and a vendor adapter
built before the payload shape is known yields a round-trip test proving only that the adapter
matches a guess.

It matters more than its status suggests, and the reason is in [`benchmarks.md`](benchmarks.md):
**the incumbent is solved by the system under test**. Every benchmark number here shows that a replan
beats a re-solve *given a roster this model would produce*, not that the model resembles what real
planners publish. Only a captured corpus can carry the second claim. That is the largest single gap
in the evidence, and it is stated here rather than in a footnote.

#### Deferred with reasons, in the specs that own them

- **The cost model is a flat rate** and `cost_weight` ships at `0` (`D-050`). The disruption/cost
  frontier therefore has no cost axis to trace. Needs wage data.
- **Two open decisions** remain in `decisions.md`, both T4 (`D-012`, `D-013`) and both about the LLM
  boundary. Every decision for T1, T2, T3 and capture is written — capture's three were writable
  without the corpus, because the reasoning never depended on it, only the execution does.
  *(Both were written when T4 was built; the Open table is now empty. See the postscript.)*
- **Service `[TODO]`s**: external queue store, metrics backend, interrupting a running solve.
- **`R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`** are registry entries
  marked optional and not encoded — asserted as such by `tests/test_specs.py` so they cannot quietly
  pass as implemented.

#### Never started, by design

T4 (infeasibility explainer, tool surface, NL → profile) and T5 (LNS, generation mode, learned warm
starts, fairness objectives). `PLAN.md`: *T3 is a legitimate finish. T4 and T5 are upside, each
independently shippable.*

*(T4 was built after this declaration and is described in the postscript below. T5 is closed too:
LNS and learned warm starts retired on measurement — `D-104`, `D-105` — with fairness objectives and
generation mode built, `D-108` and `D-109`.)*

### "All specs true", and how far that is checkable

Every spec has been reconciled with its code. Two were corrected during this declaration:
`model.md` still carried a `[TODO]` for a wire format that shipped with T3, and `capture.md` still
claimed its adapter would land in T2.

Prose-level truth is a reading task and was done by reading. What can be mechanised now is, in
`tests/test_specs.py`:

- every rule the registry marks encoded appears in **both** readings, and neither reading invents one;
- every unencoded registry entry is marked optional;
- every decision ID referenced in any document or source file exists;
- **no decision ID is used twice** — `D-089` was assigned twice during T3 and only a human noticed;
- every relative link between documents resolves — which failed on its first run.

### The state of the repo

| | |
| --- | --- |
| Tests | 567 |
| Mutants, each naming the layer that must catch it | 59 |
| Import-linter contracts | 8 |
| Decision records | 94, with 2 still open |
| Studies, including nulls | 8 |
| Python | ~12,000 lines |

The mutation harness is the claim behind the test count: every layer has been shown to fail. It
found four blind spots behind a fully green suite during T1 and T2, and during T3 it found four more
— a ladder rung that reported a timeout as a proof, an absence test passing for the wrong reason, a
dead defensive call, and a fairness property no single response could show.

### Ratifications

`PLAN.md` listed two items to settle here. Both are settled (`D-095`).

1. **Repo name: `roster-replan-optimizer`, ratified unchanged.** Accurate, and it matches the package
   name, the remote and every link in the docs. Nothing the project learned contradicts it.
2. **Public/private fork: deliberately deferred, not executed.** `PLAN.md`'s recommended default was
   *public on completion*, and the IP-hygiene test it set itself is satisfied — the project is
   synthetic throughout, with no tenant data, no vendor payloads and no wage data, so it would pass
   "would I be fine if this went public tomorrow?" today. The owner has chosen to keep it private for
   now, which changes nothing about the code. Publication is irreversible in practice — whatever is
   published can be cached and indexed after any revert — so leaving a reversible decision reversible
   is the cheaper order to do these in.

**This declaration is therefore complete.**

## After the declaration

Date: 2026-08-14. The declaration above is left as written. This section is the same exercise applied
to everything since — and there is more of it than the word *postscript* implied, because **T4 and T5
both closed**. `PLAN.md` is now built out in full; what remains is listed at the end and every item of
it is blocked on something this project does not control.

### T4, built in full

| Piece | Where | The decision it turned on |
| --- | --- | --- |
| Shortfall and infeasibility explainer | [`explain.py`](../roster_replan/explain.py), [`prose.py`](../roster_replan/prose.py) | `D-097` — explain shortfalls first, and answer from the checker |
| Minimal cores | [`core.py`](../roster_replan/core.py) | `D-100` — the objective inflates the core; deletion is a null on top |
| Tool surface and hypotheticals | [`service/tools.py`](../roster_replan/service/tools.py), [`whatif.py`](../roster_replan/whatif.py) | `D-098` — unlawful hypotheticals are refused, not answered |
| Profile review | [`profile.py`](../roster_replan/profile.py) | `D-099` — deterministic, and enabling an unencoded rule is a defect |
| NL → profile | [`nl.py`](../roster_replan/nl.py) | `D-101` — the schema is the confinement, and an open mapping is not a schema |
| Parse eval | [`nl_eval.py`](../benchmarks/nl_eval.py) | `D-102` — score what was invented, not only what was found |

**The two open decisions are written.** `D-012` and `D-013` were the only entries left in the Open
table, and both were writable once the boundary they describe existed. The table is now empty.

**What T4 got wrong.** `D-100` deferred core minimisation on the grounds that a sufficient core names
unnecessary rules; measured, the cause was not what the deferred work was aimed at — dropping the
objective cuts a 160-gate core to two, and the deletion loop meant to do the work removes nothing on
top. `D-101` is sharper because it is a defect rather than a null: the derogation field the prompt
asked the model to fill compiled to an object that **could hold nothing**, and every behavioural test
passed over it, because a stub returns what the test hands it. The layer now reads the compiled schema.

**The parse is measured**: **18/18 on three consecutive runs**, after 16/18 on the first
([`studies/nl-parse.md`](studies/nl-parse.md)). It found one real defect — `unclear` specified in a
way that invited an assumptions log (`D-103`) — and one of the eval's own, where it scored its
author's capitalisation as the correct answer. Extraction was right in every case on the first run,
Dutch and adversarial cases included.

What that does **not** establish belongs here as much as in the study: fifteen cases written by the
same person who wrote the parser and the prompt. It is the incumbent problem from
[`benchmarks.md`](benchmarks.md) one layer up — **the text is text this system imagined**, not what a
Belgian horeca operator would send.

### T5, closed: two built, two retired on measurement

| Item | Outcome |
| --- | --- |
| LNS | **Retired** (`D-104`, `D-105`) — improves a solution the solver cannot prove optimal in time, and neither half is true here |
| Learned warm starts | **Retired** (`D-104`) — would optimise the 9% of search time `D-082` measured, on a search taking milliseconds |
| Fairness objectives | **Shipped** (`D-108`) — rolling balance of unpopular shifts |
| Generation mode | **Shipped** (`D-109`) — the cold-start case, made testable rather than argued |

**The retirements rest on a swept range, not on one sample of it.** 2,268 solves returned `OPTIMAL`,
longest search 15.4 ms, and solver-free greedy ties the optimum on 71 of 84 cases. `D-105` then swept
the generator's whole parameter space — demand at 105% of capacity, minimum slot slack of −7, 40
employees, every pressure at once — and every configuration returned `OPTIMAL` in 3 to 11 ms, with the
structurally short cases running *faster* than the baseline. What would reopen LNS is a longer horizon
or a tenant an order of magnitude larger, and neither exists here.

**Fairness is a third meaning of the word in this repo**, and gets its own type for that reason: not
`D-091`'s round-robin between tenants in the queue, and not D4's spreading of the changes a replan
makes, but who works the shifts nobody wants, across weeks. Unpopularity is declared by the profile
rather than derived from the clock, and the domination bound grew a term because an unstaffed
unpopular shift is one nobody's count went up for.

**Generation needed no formulation.** It is a replan from an empty incumbent, so what shipped is the
claim made testable at the solver, the ladder and the service. Testing it corrected `replan.md`: cold
disruption is flat at zero rather than the positive constant the spec derived, so the shortfall caveat
it carried describes a risk the implementation cannot have, and what actually ranks a cold roster is
the peak-workload tie-breaker.

### The set widened, and what that re-measured

The committed set held 60 of its 72 cases at ~0.70 demand with nothing between 0.73 and 0.89 — one
tightness level and two deliberate outliers, which is what varying one axis at a time from a slack
baseline produces. Two classes fill the gap and the set is **84 cases** (`D-105`).

It moved a headline claim and left the rest standing. **Greedy ties on 71 of 84** where it tied on 64
of 72, and the 13 losses are the original 8 reproduced case for case plus 5 in the new band: the tie
rate was substantially a statement about where the set sampled. Conjunction — piling demand, scarcity
and thin availability together — was tried first and **rejected**, because structurally short weeks
make both methods leave the same unfillable holes and the benchmark goes blind rather than sharp.

Everything else re-ran and reproduced (`D-106`, `D-107`): D0–D4 divergence at 26 of 84 with `D-060`
confirmed on a curve for the first time, presolve, symmetry, the automaton, patterns, the rest-gap
encoding. The one real find was not a lever but a **sampling bug**: `studies.py` selected its cold
instances positionally, so adding two classes silently swapped two others out, and two results moved
in ways that read exactly like findings. The sample is named now.

*(That divergence rate is now **10 of 84**, and the curve is withdrawn — `D-120`. Canonicalising the
optimum replaced every instance in the set, and the rate fell by a factor of two and a half without
the method changing at all. The structure held: the same D0/D1/D2 against D3/D4 split, the same
symmetric regret, and a worked example reproducing to the point on another seed of the same class.
**26 of 84 was never a robust figure, and nothing said so**, because nothing had moved the instances
underneath it before.)*

### What is still not done

Three of these four are blocked on something outside this repository, which is the honest reason
they are not done. The fourth is not blocked at all — it is deployment work with no findings in it,
and saying so is more useful than filing it beside the ones that need an external input.

| Gap | Blocked on |
| --- | --- |
| **Capture and replay** — was the largest gap, now half of one (`D-125`) | External authorization and real vendor payloads. Foreign published rosters answered the sharpest form of the objection; a Belgian horeca corpus is still what this owns |
| The cost axis (`cost_weight` ships at 0, `D-050`) | Wage data |
| `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` | A named legal source each — every one is still `[CITE]`, and `rules.md` refuses a legality claim without provenance |
| Service `[TODO]`s: external queue store, metrics backend, interrupting a running solve | Nothing — these are deployment choices, and `service.md` states each as the tier's honest limit |
| **Whether the reference-period budget is a lossy approximation** — reopened by `D-116` | Nothing. It needs a pooled `max_hours_this_period` field, which `D-111` deferred and the horizon study is the argument for reinstating |

The capture gap outranks the rest and the reason is unchanged: **the incumbent is solved by the system
under test**. Every benchmark number here shows a replan beats a re-solve *given a roster this model
would produce*, not that the model resembles what real planners publish.

### The horizon, and a rule that was right for the wrong reason

The project's rules were written for a one-week horizon, and one week is what every number above was
measured on. Auditing that assumption cost four decisions and found one real defect, one latent one,
and a hole in the harness that is supposed to find defects.

**Two rules were named for a week and measured over a horizon.** `R-MAX-WEEKLY` summed an employee's
whole instance against one budget, and `R-WEEKLY-REST` asked for one 35-hour window anywhere in the
payload — in *both* readings. At seven days those are the same span, which is why the encodings were
right and why nothing could see they were right by coincidence. Past seven they separate in the weak
direction: 35 hours of rest inside four weeks satisfies a rule that means 35 inside each of them.

**The differential harness could not have caught it**, because both readings were wrong in the same
direction, and brute force enumerates against the same predicates. It is the shared-*assumption* form
of what the independence rule forbids for shared thresholds, in the one place the discipline does not
reach: seven days appears as a number in neither reading. Validation refused the payload first
(`D-110`), the rules were scoped to the week (`D-111`), and four mutants now restore the defect one
reading at a time — caught by the layer that an hour earlier could not have seen it.

**Then the guard came off** (`D-113`), and working through its three stated reasons found only one
defect among them. The profile probe's hard-coded week was already right and merely misnamed. The
generator's seven days gates the evidence, not the request path. What was left is the stub week: a
ten-day horizon ends three days into a week no roster can rest inside, so it is refused as a request
rather than answered with an infeasibility about a week that is mostly not in the payload.

**And the last unmeasured rejection in the repo is measured** (`D-116`,
[`studies/horizon.md`](studies/horizon.md)). `rules.md` had rejected a reference-period horizon
because it *"multiplies instance size by an order of magnitude and destroys the interactive latency"*.
Both halves are wrong — size grows **linearly**, and four weeks answers in about 112 ms. The
rejection stands for the reason it never gave: a longer horizon **buys nothing**, reaching identical
coverage to four chained weekly solves on every case at both ends of the tightness axis, while being
two to six times slower under pressure.

That study also **scoped a premise this repo reasons from everywhere**. `D-081` separates the two
clocks because build costs more than search; the crossover sits between one week and two, so every
performance conclusion here is a statement about a one-week horizon rather than about this model.

A latent defect fell out of the generator on the way (`D-115`): `_load` weighted demand toward the
back of the week with `day >= 4`, a weekly pattern for exactly as long as the horizon is a week.
Nothing would have failed. The study would have measured a different world.

### The harness that finds defects had one

`CLAUDE.md` tells a reader to ask `jq .verdict` first and treat `leaked` as void. A run reported
`verdict: clean`, `trustworthy: true`, `leaked: []` — with a mutated `checker.py` in the working tree,
and the reason named three fields lower in the same object. The clean-tree check subtracts files that
were already modified, so it was blind to precisely the two files the run was mutating, and
`trustworthy` was derived from that check alone.

`D-112` adds a fourth verdict. Every mutant caught plus a tree the run cannot vouch for is
`unverifiable` rather than `clean`, whether the cause was a file already modified or an editor writing
back after the restore verified. A survivor still outranks it. **A field a reader is told to trust
must not be the one field that cannot see the failure.**

### CI, and the first thing it found

There was none, and four documents said the independence rule was *"enforced in CI"* (`D-114`). There
is now: the suite on every push with and without the optional parse extra, plus the ten import
contracts. The suite also could not be run the obvious way — without the repo root on pytest's path
`uv run pytest` failed at conftest import while `uv run python -m pytest` passed.

What CI found first was its own limit. Two timing guards are calibrated against the machine that
recorded `timings.json`, and a shared runner is slower at Python and at CP-SAT by different factors,
so both the milliseconds and the ratio between them move. Widening the band is what `D-096` already
refused one level up, so they are deselected. **CI checks 762 of 766 tests, and the four it does not check
are the four it cannot.**

Its second finding was larger and is a defect in the product rather than in the tests (`D-118`). On a
linux runner six tests failed for a reason unrelated to any of them: the optimum is **degenerate**, so
which of the equally good rosters CP-SAT returns is a property of the binary, and every committed
scenario diverges from its regeneration on a different one. The incumbent is solved, the disruption
event picks whom to injure out of *that* roster, and the whole case follows. What that falsifies is a
README sentence — a roster could not be reproduced from its input, seed and profile version alone,
only its objective value could. CI ran macOS for a while, matching the platform the artifacts were
recorded on, which bought a green tick at the price of a CI that **could no longer tell anyone the
project was portable**.

**That is fixed rather than filed** (`D-119`, `D-121`). Every proved optimum is now pinned at its
optimal value and a canonical criterion picks a single point on the optimal face, so the roster is a
function of the model rather than of the search: degeneracy across the committed set went from 24
replans and 84 cold weeks to nought and nought. CI is back on linux — a different ortools build from
the one every artifact here was recorded with — and green, which is the only evidence that claim could
have. It cost 61% of search time and `D-081`'s premise, and the README sentence is now true without a
qualifier.

### The optimum was degenerate, and that falsified a claim

The objective is **flat across many rosters**. On the committed set, four solver seeds return the
same objective value every time and a *different roster* on 24 of the 84 replans and on all 84 cold
weeks. So which optimum came back was decided by the search, and therefore by the ortools binary
rather than by anything in the specification — which made `README.md`'s promise that a roster
reproduces from its input, seed and profile version **false** (`D-118`).

Nothing in the suite could see it. Every objective value, every benchmark number and every test
stayed green, because none of them looked at *which* optimum. **CI found it, by being the first
machine that had never run this code**, and it took two wrong inferences and a local reproduction
before the cause was established rather than guessed.

The fix is a second phase on every proved optimum: pin the optimal value, minimise a canonical
criterion over the optimal face, so nothing about what is optimal changes and the roster becomes a
function of the model (`D-119`). Degeneracy went to zero on both counts, and CI proves it on a
different build from the one every committed artifact was recorded with (`D-121`).

**Its price is on the invoice, and one line of it was found later.** It costs 61% of search time and
`D-081`'s premise — build no longer outruns search at one week, so every performance conclusion here
is scoped rather than general. Then the first full mutation run afterwards came back with
**survivors**: two mutants that had been caught for months now pass, because both break the *search
path* and both tests detected that by watching the answer change. `D-119` made the answer independent
of the search path on purpose (`D-124`). **Reproducibility and observability were trading against
each other and only one side was priced.**

### What a roster from outside this project does to it

`benchmarks.md` has said since T2 that the incumbent is solved by the system under test, and this
declaration called it the largest single gap in the evidence. Half of it is now closed (`D-125`,
[`studies/foreign-incumbent.md`](studies/foreign-incumbent.md)). Published solutions from the
nurse-rostering benchmark set are rosters built by other people's solvers for an objective this
project does not implement, and used as incumbents they reproduce the headline claim by **10× to
27×** where the committed set shows about 5×.

Three things came back that a synthetic set could not have produced.

**The importer was wrong twice before it was right, and both errors were this project's own
conventions misapplied.** A weekly rate derived from their horizon total forbids exactly the uneven
spending a pool permits — `D-123`'s finding arriving from outside, hours after it was recorded — and
translating days off into intervals flagged every night shift the evening before one, which is the
start-day attribution convention `rules.md` fixes. Corrected: 55 hard violations across 6,361
assignments, all of them Belgium being stricter than the rules those rosters were built for.

**Seven of thirteen published rosters have a past this model calls illegal.** `R-PIN-PAST` pins it,
so the replan is correctly infeasible — the "the past itself is illegal" case, which had a ladder
rung, a test, and no natural instance anywhere in this project until now.

**It found a defect in a fix made the same day.** `D-119`'s canonicalising phase asserted it could
not fail; a 40-employee four-week instance raised that assertion on first contact, and behind it was
a second defect nobody had noticed — phase two was handed a fresh time budget rather than the
remainder, so a 30-second request could take 60 (`D-126`). The committed set could not have found
either, because every instance in it canonicalises in milliseconds.

**And it found where the model stops** (`D-127`). Every performance number here is measured on 8-25
employees over one week, and `D-105` swept the generator's whole range without finding anything hard —
which measured that *the generator cannot produce a hard instance*, a different claim. Foreign
instances do: **7.71 seconds of search to prove optimality**, against a committed-set maximum of 15.4
ms across 2,268 runs, and at 8 million variables no roster at all. `D-104` retired LNS because every
solve returned `OPTIMAL` in milliseconds; that reasoning is now narrowed from *this never happens* to
*this does not happen in the regime we serve*.

The binding constraint at every size turns out to be **model construction rather than search** — 527
seconds to build the 8-million-variable model the solver then fails to crack. `D-081` separated the
two clocks because build dominated at one week for twelve people, and it still dominates at 52 weeks
for a hundred. The usable envelope is now a number: **up to about 40 employees over four weeks**,
proved optimal and canonical within seconds.

### The state of the repo

| | At the declaration | Now |
| --- | --- | --- |
| Tests | 567 | 848, of which 28 skip without fetched benchmark data |
| Mutants, each naming the layer that must catch it | 59 | 111 |
| Import-linter contracts | 8 | 11 |
| Decision records | 94, 2 open | 132, none open |
| Studies, including nulls | 8 | 13 |
| Python | ~12,000 lines | ~22,000 lines |

The mutation harness has been run in full three times since the declaration: 95 mutants all caught on
a clean tree, `verdict: clean` and `trustworthy: true`; then 103 of 103 caught but `unverifiable` for
a late write, closed by re-running the one affected layer (`D-130`); and most recently **108 of 108
caught, `clean` and `trustworthy`, in 574 seconds** on the tree `D-131` was committed to. `D-132`'s
three are proven at their own layer and were added after that run, which is the weaker result and is
what the next full run settles. The first clean run was the first whose verdict meant what it says,
because the harness had to be hardened a third time
first (`D-112`): it had been reporting `clean` while a mutated file sat in the working tree, since its
clean-tree check skips files that were already modified and `trustworthy` was derived from that check
alone.

The two earlier hardenings were the same failure in cruder forms — an editor's format-on-save watcher
wrote mutated text back under it three times, once *minutes after* a run had finished, and the verdict
lives in a file rather than in stdout because reading it through a pipe destroyed two runs. Three
hardenings in, the pattern is worth naming: **every one of them was the harness being confidently
wrong rather than merely failing**, which is exactly the failure mode it exists to catch in everything
else.

## Archived

`PLAN.md` is archived to [`archive/PLAN.md`](archive/PLAN.md) and is not maintained. Anything in it
that is still true has moved into a spec; anything that has not is sequencing, which has been spent.
