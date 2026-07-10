"""Time-value-of-money primitives.

Purpose
-------
The module provides future value, present value, implied period-count, implied rate, and period decomposition calculations.

Conventions
-----------
Rates are decimal rates per period and periods are counts of compounding intervals unless a continuous-force parameter is used.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def future_value(principal: float, rate: float, periods: float) -> float:
    """Compute the accumulated value of a present amount.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed future value as a scalar in the units implied by the input values.
    """
    return principal * (1 + rate) ** periods


def continuous_future_value(principal: float, delta: float, periods: float) -> float:
    """Compute accumulated value under a constant force of interest.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    delta : float
        Constant force of interest in decimal annual units.
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed continuous future value as a scalar in the units implied by the input values.
    """
    return principal * np.exp(delta * periods)


def present_value(future_amount: float, rate: float, periods: float) -> float:
    """Compute the discounted value of a future amount.

    Parameters
    ----------
    future_amount : float
        Target future amount in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed present value as a scalar in the units implied by the input values.
    """
    return future_amount / (1 + rate) ** periods


def continuous_present_value(future_amount: float, delta: float, periods: float) -> float:
    """Compute discounted value under a constant force of interest.

    Parameters
    ----------
    future_amount : float
        Target future amount in currency units.
    delta : float
        Constant force of interest in decimal annual units.
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed continuous present value as a scalar in the units implied by the input values.
    """
    return future_amount * np.exp(-delta * periods)


def number_of_periods(principal: float, future_amount: float, rate: float) -> float:
    """Solve for the number of compounding periods needed to reach a target amount.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    future_amount : float
        Target future amount in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.

    Returns
    -------
    float
        Computed number of periods as a scalar in the units implied by the input values.
    """
    if principal == 0 or rate <= 0:
        return 0
    return np.log(future_amount / principal) / np.log(1 + rate)


def rate_of_return(principal: float, future_amount: float, periods: float) -> float:
    """Solve for the effective periodic return implied by two values and a horizon.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    future_amount : float
        Target future amount in currency units.
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed rate of return as a dimensionless decimal quantity.
    """
    if principal == 0 or periods == 0:
        return 0
    return (future_amount / principal) ** (1 / periods) - 1


def decompose_periods(periods: float) -> pd.DataFrame:
    """Decompose a real-valued period count into its implemented representation.

    Parameters
    ----------
    periods : float
        Number of discrete compounding or payment periods.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.
    """
    years = int(periods)
    frac_years = periods - years

    raw_months = frac_years * 12
    months = int(raw_months)
    frac_months = raw_months - months

    raw_days = frac_months * (365 / 12)
    days = int(raw_days)
    frac_days = raw_days - days

    raw_hours = frac_days * 24
    hours = int(raw_hours)
    frac_hours = raw_hours - hours

    raw_minutes = frac_hours * 60
    minutes = int(raw_minutes)
    frac_minutes = raw_minutes - minutes

    raw_seconds = frac_minutes * 60
    seconds = int(raw_seconds)

    return pd.DataFrame(
        [
            {
                "Years": years,
                "Months": months,
                "Days": days,
                "Hours": hours,
                "Minutes": minutes,
                "Seconds": seconds,
            }
        ]
    )


__all__ = [
    "continuous_future_value",
    "continuous_present_value",
    "decompose_periods",
    "future_value",
    "number_of_periods",
    "present_value",
    "rate_of_return",
]
