"""The T3 production surface: contracts, jobs, endpoints.

Deliberately separate from the solver core. `roster_replan.ladder` and everything below it
import nothing from here, which an import-linter contract enforces -- the solver has to stay
runnable, testable and replayable with no web layer present.
"""
