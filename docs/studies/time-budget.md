# Solution quality against the time budget

**Question.** What does the answer cost if the solver is given 1 s, 5 s or 30 s?
The fallback ladder exists to time-box a solve and report its gap, so the anytime curve is the thing that would justify it.

**Answer.** **There is no curve to draw.**
All **2,268 solver runs** across the three budgets returned `OPTIMAL`, the longest search anywhere was **15.4 ms**, and no answer changed with the budget on any of the 756 (case, method, seed) triples ([`D-107`](../decisions.md#d-107)).
Nothing was ever cut off, so there is no quality to trade for time.

## Why this is a result rather than a missing measurement

**It is a statement about the instance distribution, not about the solver.**
A one-week horizon over 8–25 employees and 21 shift instances is small for CP-SAT.
Reporting it as three identical bars would dress a fact about the benchmark set as a finding about the method, so it is stated instead.

Two things follow, and both are more useful than the curve would have been.

**The ladder's time-boxed rung is unexercised by any committed benchmark.** It is tested by handing the ladder a time-boxed answer rather than by racing a budget ([`D-122`](../decisions.md#d-122)), because a test that tries to induce a timeout on this distribution is testing the clock, not the rung.

**The scheduling concern is the opposite one.** At ~3 ms of search against ~5 ms of model construction, the thing worth optimising is the build, not the search.
That is what redirected the performance work: the compiled-model cache was the obvious candidate and hits **0 of 144** replan solves, while memoising `Instance.window` took 20% off build time ([`model-cache.md`](model-cache.md)).

## Where the regime does change

The committed set never approaches a budget.
Foreign data does: 7.71 s to prove optimality on one imported instance, and no roster at all at ~8M variables, where 527 s went to **model construction** before any search began ([`foreign-incumbent.md`](foreign-incumbent.md), [`D-127`](../decisions.md#d-127)).

So the honest scope is narrow and worth stating: the flat curve is real for the tenants this product targets, and says nothing about instances an order of magnitude larger.
