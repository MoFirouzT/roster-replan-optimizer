# Rules

Every rule a roster is checked against: what it says, what parameters it takes, and where its authority comes from.

**One vocabulary end to end.** A rule's ID is the same string in this registry, in the CP-SAT model, in the independent checker, in the `Violation` objects you get back, and in the explainer's prose. When a shortfall says `R-SKILL`, that is the entry in the registry, and the column beside it says which file specifies the rule.

Each rule is specified in eight bullets. Five are for anyone using the service (**Statement**, **Class**, **Parameters**, **Explainer text**, **Provenance**) and three are for anyone changing it: **Predicate**, **Model encoding**, **Checker encoding**. The last two are documented side by side deliberately, because the model and the checker are two independent readings of this registry and keeping both visible is what makes the independence checkable.

*Assumes: the symbols and the formulation they sit in, [`model.md`](../internals/model.md); the payload each rule reads its parameters from, [`api.md`](api.md).*

**The rules themselves are in three files**, and the registry's last column says which:

| | |
| --- | --- |
| [`rules-operational.md`](rules-operational.md) | the five this product imposes because a roster has to work |
| [`rules-statutory.md`](rules-statutory.md) | the fourteen that carry a named legal instrument |
| [`rules-eligibility.md`](rules-eligibility.md) | the two resolved upstream and supplied as data |

## Registry

| ID | Rule | Class | Parameters | Provenance | Specified in |
| --- | --- | --- | --- | --- | --- |
| `R-COVER` | Each open shift is staffed to its requirement | hard ceiling, soft floor | per shift | operational | [operational](rules-operational.md#rule-r-cover) |
| `R-AVAIL` | No assignment overlapping a declared absence or unavailability | hard | per employee, interval | operational | [operational](rules-operational.md#rule-r-avail) |
| `R-SKILL` | Assigned employee holds the shift's required skill | hard | per shift/employee | operational | [operational](rules-operational.md#rule-r-skill) |
| `R-SKILL-MIX` | A shift's roster holds at least *m* people with a given skill | hard or soft, **per entry** | per shift/skill | operational, or legal per entry `[CITE]` | [operational](rules-operational.md#rule-r-skill-mix) |
| `R-PIN-PAST` | Shifts starting before `now` are immutable | pinned | `now` | operational | [operational](rules-operational.md#rule-r-pin-past) |
| `R-MIN-SHIFT` | Minimum shift length: 2h horeca, 3h general | **input validation**: not roster-violable | hours, per tenant | Arbeidswet art. 21; KB 18 June 1990; PC 302 CAO nr. 7 of 25 June 1997 art. 10 | [statutory](rules-statutory.md#rule-r-min-shift) |
| `R-REST-GAP` | Minimum rest between consecutive shifts | hard | hours | Arbeidswet art. 38ter §1; WTD art. 3 | [statutory](rules-statutory.md#rule-r-rest-gap) |
| `R-MAX-WEEKLY` | Maximum hours this week, as a supplied per-employee budget | hard | hours, per employee | Arbeidswet art. 19, 26bis; WTD art. 6, 16(b) | [statutory](rules-statutory.md#rule-r-max-weekly) |
| `R-MAX-PERIOD` | Hours left in the rolling reference period, over the whole horizon | hard, **optional** | hours, per employee | Arbeidswet art. 26bis §1; WTD art. 16(b), 19 | [statutory](rules-statutory.md#rule-r-max-period) |
| `R-MAX-DAILY` | Maximum hours per day | hard | hours, per contract | Arbeidswet art. 19, 20, 20bis, 22 | [statutory](rules-statutory.md#rule-r-max-daily) |
| `R-CONSEC-DAYS` | Maximum consecutive working days | hard | days | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-consec-days) |
| `R-MAX-WEEKENDS` | Maximum weekends worked across the horizon | hard, **optional** | weekends, per employee | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-max-weekends) |
| `R-MIN-DAYS-OFF` | Minimum length of a stretch of days off | hard, **optional** | days, per employee | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-min-days-off) |
| `R-MIN-BLOCK` | Minimum length of a block of working days | hard, **optional** | days, per employee | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-min-block) |
| `R-MAX-SHIFT-TYPE` | Maximum assignments of one shift type | hard, **optional** | count, per employee and shift type | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-max-shift-type) |
| `R-MIN-HOURS` | Minimum assigned hours over the horizon | hard, **optional** | hours, per employee | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-min-hours) |
| `R-SUCCESSION` | A shift type that may not follow another | hard, **optional** | pairs of shift types | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-succession) |
| `R-DAY-OFF` | A day granted off, by day rather than by interval | hard, **optional** | day set, per employee | **not statutory**: operational/CBA | [statutory](rules-statutory.md#rule-r-day-off) |
| `R-WEEKLY-REST` | Minimum uninterrupted weekly rest | hard | hours | Arbeidswet art. 38ter §3; WTD art. 5 | [statutory](rules-statutory.md#rule-r-weekly-rest) |
| `R-FLEXI-ELIG` | Flexi-job eligibility conditions | hard, **resolved upstream** | per employee, per day | Wet 16 Nov 2015 art. 4 §1, as amended by Wet 28 June 2026 | [eligibility](rules-eligibility.md#rule-r-flexi-elig) |
| `R-DIMONA-FLX` | `FLX` Dimona filing as an eligibility gate | hard, **resolved upstream** | filing state, per employee/day | NSSO Dimona instructions; Wet 16 Nov 2015 | [eligibility](rules-eligibility.md#rule-r-dimona-flx) |
| `R-STUDENT-QUOTA` | Student-worker hour quota | hard, optional | hours/year | KB 28 November 1969 art. 17bis | *not yet specified* |
| `R-SUNDAY` | Sunday and public-holiday work restriction | hard, optional | derogation set | Arbeidswet art. 11, 16, 66; Feestdagenwet art. 4, 6, 11 | *not yet specified* |
| `R-BREAK` | In-shift break entitlement | hard, optional | minutes per hours worked | Arbeidswet art. 38quater; art. 34 under 18 | *not yet specified* |
| `R-PT-MIN` | Part-time minimum shift length and weekly hours | hard, optional | hours | Arbeidswet art. 21; Wet 3 July 1978 art. 11bis | *not yet specified* |
| `R-PUB-NOTICE` | Variable-schedule publication notice | soft, optional | days | Wet 8 April 1965 art. 6 §1, 1°, third para., d) | *not yet specified* |

The *Specified in* column names the file holding each rule's predicate. The five with no file
(`R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`) are declared and sourced but not yet specified;
each still needs an exact predicate (the conditions it imposes, written out), its parameters and their per-tenant configurability, a
hard/soft classification, and the failure message the explainer renders.
Every rule marked *optional* is profile-gated: a tenant that does not enable it never pays for it.

`[CITE]`: every legal rule needs a named source. A legality claim without
provenance is a guess, and the checker is the component whose whole value is that it is not one.

**Every rule that names a statute names one.** The five unspecified rules are sourced above, and so
are the three items that were once open inside the specified ones. Two of those searches came back
negative, and the negative is the finding: there is **no 24-hour Dimona deadline** and **no horeca
3h48 minimum**. Both are recorded where the rule that would have carried them lives.

`R-SKILL-MIX` keeps its `[CITE]` and always will. Its provenance is declared **per entry** by the
tenant, so there is no one instrument to name: a first-aider requirement and a food-hygiene
requirement come from different places, and which applies is a fact about the tenant. That marker is
a property of the rule's shape rather than work left undone.

A citation is not the same as an encoded rule. Those five stay outlines until each has a predicate,
parameters, a hard/soft classification and a failure message, and `tests/test_specs.py` holds them to
*optional* until then.

### What the sources say, for rules not yet encoded

Recorded here so the search does not have to be repeated when one of these is built. **None of these
numbers is enforced by anything**, and none has been through the two independent readings that a
shipped rule gets.

| Rule | What the instrument sets |
| --- | --- |
| `R-STUDENT-QUOTA` | 650 hours a calendar year, permanent since 1 January 2025: 475 before, 600 through 2023–24. Counted in hours, filed under Dimona worker type `STU`; ordinary contributions from the 651st hour | *not yet specified* |
| `R-SUNDAY` | Sunday work permitted for horeca under Arbeidswet art. 66 for workers 18 or over. Compensatory rest under art. 16: a full day where Sunday work passed four hours, half a day otherwise, inside the six days following. Public holidays are the Feestdagenwet's own entitlement and the two must not be made to coincide | *not yet specified* |
| `R-BREAK` | Two limbs. No more than six hours worked without interruption; and where working time passes six hours a break is owed, its length and timing set by CAO or the work rules. Only where no CAO applies does the statute's own floor bite: fifteen minutes, at the latest on reaching six hours. Under-18 workers take art. 34 instead. The statute does not say whether the break is paid | *not yet specified* |
| `R-PT-MIN` | Three hours per work period (Arbeidswet art. 21, general, **not** part-time-specific). Weekly floor one tenth of a comparable full-timer's week since 1 June 2026, a third before. PC 302 sets its own: ten hours a week, two hours a period | *not yet specified* |
| `R-PUB-NOTICE` | Seven working days, which a generally binding CAO may shorten to no fewer than three. **PC 302 sits at three**: it registered no CAO of its own by 31 December 2022, so the amending law's own floor took effect for it on 1 January 2023 | *not yet specified* |

Two of these carry a question that would have to be answered before encoding. `R-BREAK`'s second limb
is conditional on the tenant having no CAO, which is a profile fact this registry has no field for.
And `R-PUB-NOTICE` may not be alone: art. 159 of the Programmawet van 22 december 1989 states an
overlapping publication duty, and whether it is a second obligation or the same one seen twice was
not settled.

**Two provenance lines are weaker than the rest and say so.** `R-SUNDAY`'s art. 66 could not be read
off the consolidated statute (every ejustice endpoint truncates before Chapter VI) so its sector
list rests on agreeing secondary renderings. And the flexi income ceiling is carried by three
different figures in circulation. It is resolved upstream, so the number in [`rules-eligibility.md`](rules-eligibility.md#rule-r-flexi-elig) is documentation
rather than a model input.

## Legal sources

Cited in short form throughout. Every instrument below is consolidated and publicly available.

| Short form | Instrument |
| --- | --- |
| **Arbeidswet** | Arbeidswet van 16 maart 1971 / Loi du 16 mars 1971 sur le travail (BS 30 March 1971), as amended |
| **WTD** | Directive 2003/88/EC of 4 November 2003 concerning certain aspects of the organisation of working time |
| **Feestdagenwet** | Wet van 4 januari 1974 betreffende de feestdagen: the public-holiday regime, separate from the Arbeidswet's Sunday regime |
| **Arbeidsreglementenwet** | Wet van 8 april 1965 tot instelling van de arbeidsreglementen, as amended by the Wet van 3 oktober 2022 (BS 10 November 2022) |
| **Arbeidsovereenkomstenwet** | Wet van 3 juli 1978 betreffende de arbeidsovereenkomsten, as amended by the Wet van 18 mei 2026 (BS 1 June 2026) |
| **RSZ-uitvoeringsbesluit** | KB van 28 november 1969 uitvoering wet 27 juni 1969: art. 17bis carries the student quota |
| **PC 302 CAO nr. 7** | CAO nr. 7 van 25 juni 1997, Paritair Comité voor het Hotelbedrijf, generally binding by KB of 25 May 1999 |

Belgium transposes the WTD, and in several places transposes it *more strictly*. **Where the two
differ, this project implements the Belgian rule**: it is the binding one for the target tenants, and
the stricter of the two cannot produce a WTD violation. Each rule records where that happens, in the file the registry sends you to.

The relevant provisions are widely restated by third parties and often restated incorrectly; article
numbers here were checked against the consolidated statute rather than against summaries. One
concrete instance: the FPS Employment summary page attributes the three-hour minimum work period to
art. 19, and the statute puts it in art. 21.

## The reference period, and why `R-MAX-WEEKLY` is a budget

Average weekly hours in Belgian labour law are measured over a **rolling reference period** (a quarter or a year) not per calendar week. A per-week ceiling is not the rule; it is an approximation of it, and one that is wrong in both directions. It forbids a legal heavy week that a light week would compensate, and it permits thirteen consecutive weeks at the ceiling.

**So the reference period is resolved upstream and enters the solve as data.** You compute, per employee, the hours already worked in the period and the working time left in it, and supply a single `max_hours_this_week` budget. The solver and the checker see only that number. The horizon stays one week, the rule stays local, and the semantics stay correct.

The alternative (extending the solve horizon to cover the whole reference period) was built and measured, and it buys nothing: four weeks solved at once and four weeks solved one at a time reach identical coverage on every case tried, and under pressure the single solve is two to six times slower for it. See [`horizon.md`](../studies/horizon.md).

**The budget is a week's hours, and it binds in every week of the horizon.** At a one-week horizon that is the same sum either way. What a single number cannot express is a *different* ceiling in week two from week one; supplying that is a payload change and it is not built.

A horizon of **whole weeks** is a precondition of the request. A week or less is answered; two, three or four whole weeks are answered; ten days is refused, because it ends in a stub week no roster can fit a weekly rest inside.

The cost is stated rather than hidden: **correctness depends on a computation this service does not perform.** The checker verifies assignments against the budget you supplied and never recomputes it: a checker that invents its own budget from a period it cannot see is testing you, not the roster.
