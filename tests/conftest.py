"""Fixtures for the checker suite.

Instances are built explicitly rather than by a factory with sensible defaults: the
whole point of the independence rule is that no rule threshold has a default anywhere
near the two readings, and a test helper that supplies 11 hours for you is that default
wearing a different hat.
"""

from __future__ import annotations

import pytest

from roster_replan.domain import (
    Employee,
    Instance,
    Interval,
    OpenShift,
    RuleParams,
    ShiftType,
    shipped_d2,
)

MORNING, EVENING, NIGHT = 0, 1, 2


@pytest.fixture
def shift_types() -> tuple[ShiftType, ...]:
    """8h spans with a 30-minute break, so span and work_hours differ and any rule
    reading the wrong one is visible rather than coincidentally right."""
    return (
        ShiftType(label="M", start_hour=7.0, span_hours=8.0, break_hours=0.5),
        ShiftType(label="E", start_hour=15.0, span_hours=8.0, break_hours=0.5),
        ShiftType(label="N", start_hour=23.0, span_hours=8.0, break_hours=0.5),
    )


@pytest.fixture
def params() -> RuleParams:
    return RuleParams(
        min_rest_hours=11.0,
        min_weekly_rest_hours=35.0,
        min_period_hours=3.0,
        max_consecutive_days=6,
    )


@pytest.fixture
def person() -> Employee:
    return Employee(
        name="Ana",
        contract="salaried",
        skills=frozenset({"bar"}),
        max_hours_this_week=38.0,
        max_daily_hours=8.0,
    )


@pytest.fixture
def make_instance(shift_types, params):
    def build(employees, open_shifts, days=7, **kwargs) -> Instance:
        return Instance(
            days=days,
            shift_types=shift_types,
            employees=tuple(employees),
            open_shifts=tuple(open_shifts),
            params=params,
            disruption=kwargs.pop("disruption", shipped_d2()),
            **kwargs,
        )

    return build


@pytest.fixture
def one_shift() -> OpenShift:
    return OpenShift(day=0, shift=MORNING, required=1)


def hours(day: float, clock: float) -> float:
    """Hours from the horizon start, for readable interval fixtures."""
    return day * 24.0 + clock


def unavailable(day: float, start: float, end: float) -> Interval:
    return Interval(hours(day, start), hours(day, end))
