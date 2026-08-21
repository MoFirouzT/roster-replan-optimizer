# Reproducibility: does the same input return the same roster?

**Question.** `README.md` promises a roster can be reproduced offline from its input, seed and profile version.
Nothing had tested it, because everything ran on one machine.

**Answer.** **No — the optimum was degenerate, and the promise was false.**
Four solver seeds returned the same objective value every time and **a different roster on 24 of the 84 replans and on all 84 cold weeks**.
The value was fully determined by the model; the choice among equal optima was determined by nothing anybody had written down.
Fixed by pinning the optimal value and minimising a canonical criterion over the optimal set, at a cost of **61% of search time** ([`D-119`](../decisions.md#d-119)).
It now holds across solver builds, which is the part that needed a foreign binary to test ([`D-121`](../decisions.md#d-121)).

## How it was found

Not by a test. **CI found it, on a machine that had never run the code.**

Six tests failed on a linux x86-64 runner that passed on a macOS arm64 laptop: the demo scenario, two metric-divergence results, MILP agreement on `tight/0`, the sample week's shortfall, and the profile probe's blocking rules.
CP-SAT is deterministic for a given build and promises nothing across builds, so a committed artifact derived from a solve carries the binary that produced it.

The diagnosis took two wrong turns worth recording.
[`D-117`](../decisions.md#d-117) blamed the benchmark manifest and marked its solved half `machine`; the blast radius was wider — *every* committed case is downstream of a solve, because the incumbent is solved and the disruption event picks whom to injure out of that roster.
[`D-118`](../decisions.md#d-118) then moved CI to macOS to match the artifacts, and said plainly what that cost: **CI could no longer tell anyone the project was portable, because it only ran where the project was known to work.**

Underneath both was a product defect rather than a test problem, and naming it that way is what produced the real fix.

## The degeneracy, measured

| | Rosters identical across 4 seeds | Rosters differing |
| --- | --- | --- |
| Replans, 84 cases | 60 | **24** |
| Cold weeks, 84 cases | 0 | **84** |

The objective value was identical on every case, every seed, both before and after the fix.
A cold week has no incumbent to pin it, so nothing in the model preferred one roster over another at all.

## The fix

`model.solve` runs a second phase on every proved optimum: the optimal objective value is pinned as a constraint, and a canonical criterion is minimised over the optimal set.
The roster is therefore a function of the model rather than of the search, and **nothing about what is optimal changes** — every committed objective value is untouched by construction.

**The criterion is `Σ ordinal² · x`, and the exponent was measured rather than chosen.**
A linear criterion still left a cold week with four rosters across four seeds.
Squaring collapsed it to one *and* ran three times faster, because a steeper gradient prunes harder.
No preference about rosters is encoded by it; any total order would serve and this one is cheap.

## What it cost

**61% of search time**, and one of the project's stated premises.
The committed `build/search` balance moved from 1.52 to 0.985 — build 4.87 ms against search 3.21 ms became 5.08 against 5.16.
Building the model no longer costs more than searching it, which is the premise [`D-081`](../decisions.md#d-081) separates the two clocks for.
`test_build_still_dominates_search` was retired rather than adjusted: a test pinning a claim the code no longer makes is worse than no test.
[`D-116`](../decisions.md#d-116) had already located that crossover between one week and two; this brought it forward to one.

**It blinded two test layers, and nobody predicted that** ([`D-124`](../decisions.md#d-124)).
The first full mutation run afterwards came back `survivors`, 95 of 97, on a clean tree and a green suite of 766 tests.
Both survivors detected a **search-path** defect by observing that the roster changed — a stale hint on a cached model, and a hypothetical measured at the wrong seed.
Canonicalisation removed exactly that sensitivity on purpose, so the detector stopped working.
Confirmed rather than assumed: with canonicalisation disabled in a scratch copy both mutants are caught, and with it enabled both survive.

> **Reproducibility and observability were trading against each other, and only one side of the trade was on the invoice.**

Both tests now assert the defect where it lives rather than inferring it from the answer.
This is the fifth blind spot the mutation harness has found behind a fully green suite, and the first one *created by a deliberate improvement*.

## Does it travel between builds?

That is the claim [`D-119`](../decisions.md#d-119) could not make from one machine, so CI went back to `ubuntu-latest` to test it — deliberately, as an experiment with its failure mode written down in advance.

**Green.** The six scenario tests and the manifest's solved half all pass on a linux x86-64 runner, against artifacts recorded on macOS arm64.
`README.md`'s reproducibility claim dropped the *on the same solver build* qualifier, [`D-118`](../decisions.md#d-118) was retired, and CI tests portability again rather than assuming it.

## The boundary, stated

Phase two is a real search — it minimises a criterion over a set that can hold millions of points — so it can run out of budget.
It receives the **remaining** budget rather than a fresh one, and when it cannot prove its criterion optimal in the time left, phase one's roster stands and `Solution.canonical` is `False` ([`D-126`](../decisions.md#d-126)).

So the unqualified claim is true with a stated boundary: every instance in the committed set canonicalises in milliseconds, and an instance large enough to exhaust the budget returns an optimum that is not canonical **and says so**.

**The committed set could not have found this.** It took a foreign instance of 40 employees over four weeks, on the importer's first working day — the argument for foreign data, made by foreign data.
