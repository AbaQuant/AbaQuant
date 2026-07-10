"""Present-value calculations for dividends and irregular cash flows.

Purpose
-------
The module discounts deterministic dividend streams and cash-flow schedules under stated compounding conventions.

Conventions
-----------
Amounts are currency values, times are years, and rates are decimal annual rates interpreted according to the compounding argument.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np


def present_value_of_dividends(
    dividend_amount: float,
    payments_per_year: int,
    rate: float,
    total_years: float,
    compounding: str = "Continuous",
) -> float:
    """Discount a level dividend stream to present value.

    Parameters
    ----------
    dividend_amount : float
        Level dividend payment in currency units.
    payments_per_year : int
        Coupon or payment frequency per year.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    total_years : float
        Number of years over which the dividend stream is paid.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed present value of dividends as a scalar in the units implied by the input values.
    """
    present_value_total = 0
    dt = 1 / payments_per_year
    payment_count = int(total_years * payments_per_year)

    for k in range(1, payment_count + 1):
        payment_time = k * dt
        if compounding == "Continuous":
            present_value_total += dividend_amount * np.exp(-rate * payment_time)
        else:
            present_value_total += dividend_amount / ((1 + rate) ** payment_time)
    return present_value_total


def present_value_of_irregular_cashflows(
    amounts: list[float] | np.ndarray,
    times_years: list[float] | np.ndarray,
    rate: float,
    compounding: str = "Continuous",
) -> float:
    """Discount irregular dated cash flows to present value.

    Parameters
    ----------
    amounts : list[float] | np.ndarray
        Cash-flow amounts in currency units, ordered consistently with ``times_years``.
    times_years : list[float] | np.ndarray
        Cash-flow times in years, ordered consistently with ``amounts``.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed present value of irregular cashflows as a scalar in the units implied by the input values.
    """
    present_value_total = 0.0
    for amount, t in zip(amounts, times_years, strict=False):
        if compounding == "Continuous":
            present_value_total += amount * np.exp(-rate * t)
        else:
            present_value_total += amount / ((1 + rate) ** t)
    return present_value_total


__all__ = ["present_value_of_dividends", "present_value_of_irregular_cashflows"]
