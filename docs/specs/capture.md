# Capture and replay

> **Status: outline.** Adapter and replay harness land in T2, alongside the scoring machinery they
> share with `benchmarks.md`. Population depends on an external authorization this project does not
> control — see *Sequencing*.

## What this exists to prove

The incumbent path is a third-party solver API (Solvice, as consumed by Protime and Strobbo).
Replacing it requires a falsifiable claim that the substitute is at least as good, on the traffic
that actually occurs rather than on instances this project invented for itself.

Capture is what makes that claim measurable:
production requests and responses are recorded, replayed through this solver, and both outputs are
scored by the same independent checker and the same metrics.

It also supplies the only calibration target the synthetic generator will ever have.
A generator whose realism is asserted by its author is not validated;
one whose parameters are fitted to captured instances can be.

## Two-layer records

Every captured interaction is stored twice.

- **Raw.** The vendor request and response, verbatim and immutable.
- **Normalized.** The same interaction expressed in this project's own instance and solution schema.

Neither layer is sufficient alone.
Without the raw layer there is no way to demonstrate the normalization was faithful;
without the normalized layer there is nothing to replay.
The adapter between them is a component like any other and is round-trip tested:
`normalize(raw)` followed by `denormalize` must reproduce the raw payload up to documented,
enumerated losses.

`[TODO]` Record schema. At minimum: record ID, pseudonymous tenant ID, capture timestamp, vendor and
endpoint, raw request, raw response, normalized instance, normalized vendor solution, adapter
version, profile version.

## Pseudonymisation happens at capture

Not at analysis time, not at export.
Data that is never written cannot leak, and a roster store is an unusually rich target:
it locates named individuals at specific places and times.

- Employee identifiers are replaced by stable per-tenant surrogate keys at the moment of capture.
- Names, contact details and national registry numbers are never written.
- **Absence reasons are dropped.** Only the availability bit is retained.

The last one is the load-bearing one. A sick call is health data under GDPR Article 9, carrying
obligations that a benchmark corpus has no business incurring. The optimiser never needed the
reason — it needs to know the person is unavailable — so discarding it costs nothing and removes
the entire category from scope.

`[TODO]` Retention period, and whether raw payloads are retained after adapter round-trip passes.

## Replay and scoring

For each record, the normalized instance is solved by this service and the two solutions are scored
side by side.

**Both solutions are scored by this project's checker.** The incumbent's output is not assumed
legal. If it violates a rule in the registry, that is a finding to be reported, not a bug in the
harness — and it is precisely the kind of finding an independent legality layer exists to produce.

## Comparison is on observables, never on objectives

The incumbent's objective function is unknown, differently scaled, and differently weighted.
Comparing objective values across the two systems is meaningless, and any table that does it is
measuring nothing. Only externally observable outcomes are compared:

| Metric | Source |
|---|---|
| Coverage shortfall | this project's checker |
| Violations, by rule ID | this project's checker |
| Cost | this project's cost model, applied to both solutions |
| Disruption (D2) | `replan.md`, applied to both solutions |
| Solve wall-time | measured for this service, read from the vendor response for the incumbent |

Results are reported as **paired per-instance deltas with win/loss/tie counts**, not as aggregate
means. A mean conceals the distribution that matters here: a substitute that ties on ninety
instances and loses catastrophically on ten is not a substitute, and an average will not say so.

## The bar, stated before measuring

A success criterion written after the numbers arrive is not a criterion.
The following is fixed in advance of the first replay and is changed only through a `decisions.md`
entry, never in response to a result.

**Absolute gates.** Failing either means the substitute is not viable, whatever the distribution
says.

- Zero checker violations across the corpus. The independent legality layer is the product;
  a single violation retracts the claim it exists to make.
- No instance with worse coverage than the incumbent. Understaffing is the outcome a planner
  notices within the hour, and no disruption improvement compensates for it.

**Distributional bars.** Reported as paired per-instance comparisons.

- Disruption (D2) **no worse on ≥ 90%** of instances, and **strictly better on ≥ 50%**.
  The first number is the parity claim, the second is the thesis.
  One figure cannot carry both: a method can tie everywhere and satisfy a 90% bar while
  demonstrating nothing.
- On the instances where disruption is worse, **worse by no more than 25%** of that instance's
  incumbent score. Without this cap the 10% allowance is unbounded, and ten catastrophic losses
  would pass a bar designed to exclude exactly that.
- **p95 solve time ≤ 1.5× the incumbent's, and ≤ 5s in absolute terms.**
  The relative bound alone is gameable by a slow incumbent; the absolute bound is what the planner
  waiting for the answer actually experiences.

Solve time is the one metric whose comparison is confounded: this service is measured locally,
while the incumbent's figure is read from a vendor response that may include queueing and network
time. Where the vendor reports solver time separately, that is the number used, and the corpus
records which of the two was available per record.

## Shadow mode

Capture runs beside production and serves nothing.
No captured replay result reaches a planner, and this service returns no answer to a real request
until the bar above is met on a stated corpus.

## Sequencing

The adapter, the replay harness and the scoring code are built in **T2**, where the multi-method
comparison machinery already exists and this is one more instance source feeding it.

Population is gated on authorization to capture Protime and Strobbo traffic, which is a contractual
question with lead time and is not this project's to grant.
That conversation starts early because it is the long pole;
**T2 does not block on it.** The harness is testable against synthetic instances passed through the
adapter, and the corpus fills in as access arrives.

## Relationship to committed data

Nothing captured is committed to this repository.
`benchmarks/instances/` remains synthetic and seeded so that every published result is reproducible
by anyone; replayed results are reported as a separate corpus, identified by version and size, and
are reproducible only by someone holding the same access.
