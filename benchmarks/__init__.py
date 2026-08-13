"""T2 benchmark machinery: the seeded scenario generator and the committed set.

Kept out of `roster_replan` deliberately. This is an *instance source*, not a reading of
the specification, so the independence contracts in `pyproject.toml` do not reach it and
should not: the generator is allowed to import the model, and does, because measured
tightness has to be measured against the eligibility the solver will actually see.
"""
