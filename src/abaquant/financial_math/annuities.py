"""Annuity, perpetuity, and gradient cash-flow valuation.

Purpose
-------
The module values level, continuous, geometric-gradient, and arithmetic-gradient cash-flow streams and solves selected period-count equations.

Conventions
-----------
Rates are decimal rates per stated period. Payments are assumed to occur at period end unless the due flag or function definition states otherwise.

Scope and limitations
---------------------
The formulas assume deterministic rates and cash flows.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import root_scalar

from .rates import convert_nominal_frequency


def effective_annuity_future_value(
    payment: float, period_rate: float, periods: float, due: bool = False
) -> float:
    """Compute accumulated value of a level annuity under an effective period rate.

    Parameters
    ----------
    payment : float
        Level payment amount in currency units per payment period.
    period_rate : float
        Effective interest rate per payment period in decimal units.
    periods : float
        Number of discrete compounding or payment periods.
    due : bool, default=False
        Whether annuity payments occur at the beginning rather than end of each period.

    Returns
    -------
    float
        Computed effective annuity future value as a scalar in the units implied by the input values.
    """
    R = payment
    i_m = period_rate
    n_m = periods
    anticipada = due
    if i_m == 0:
        return R * n_m
    factor = ((1 + i_m) ** n_m - 1) / i_m
    if anticipada:
        factor *= 1 + i_m
    return R * factor


def nominal_annuity_future_value(
    payment: float,
    nominal_rate: float,
    compounding_frequency: int | float,
    payment_frequency: int | float,
    years: float,
) -> float:
    """Compute accumulated value of a level annuity under nominal compounding.

    Parameters
    ----------
    payment : float
        Level payment amount in currency units per payment period.
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    compounding_frequency : int | float
        Positive number of nominal compounding periods per year.
    payment_frequency : int | float
        Positive number of payments per year.
    years : float
        Time horizon in years.

    Returns
    -------
    float
        Computed nominal annuity future value as a scalar in the units implied by the input values.
    """
    i_p = convert_nominal_frequency(nominal_rate, compounding_frequency, payment_frequency)
    R = payment
    p = payment_frequency
    n = years
    n_p = n * p
    return effective_annuity_future_value(R, i_p, n_p, due=False)


def continuous_annuity_future_value(annual_flow: float, delta: float, years: float) -> float:
    """Compute accumulated value of a continuous cash-flow annuity.

    Parameters
    ----------
    annual_flow : float
        Continuous cash-flow rate in currency units per year.
    delta : float
        Constant force of interest in decimal annual units.
    years : float
        Time horizon in years.

    Returns
    -------
    float
        Computed continuous annuity future value as a scalar in the units implied by the input values.
    """
    R_anual = annual_flow
    n = years
    if delta == 0:
        return R_anual * n
    return R_anual * (np.exp(delta * n) - 1) / delta


def effective_annuity_present_value(
    payment: float, period_rate: float, periods: float, due: bool = False
) -> float:
    """Compute present value of a level annuity under an effective period rate.

    Parameters
    ----------
    payment : float
        Level payment amount in currency units per payment period.
    period_rate : float
        Effective interest rate per payment period in decimal units.
    periods : float
        Number of discrete compounding or payment periods.
    due : bool, default=False
        Whether annuity payments occur at the beginning rather than end of each period.

    Returns
    -------
    float
        Computed effective annuity present value as a scalar in the units implied by the input values.
    """
    R = payment
    i_m = period_rate
    n_m = periods
    anticipada = due
    if i_m == 0:
        return R * n_m
    factor = (1 - (1 + i_m) ** (-n_m)) / i_m
    if anticipada:
        factor *= 1 + i_m
    return R * factor


def nominal_annuity_present_value(
    payment: float,
    nominal_rate: float,
    compounding_frequency: int | float,
    payment_frequency: int | float,
    years: float,
) -> float:
    """Compute present value of a level annuity under nominal compounding.

    Parameters
    ----------
    payment : float
        Level payment amount in currency units per payment period.
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    compounding_frequency : int | float
        Positive number of nominal compounding periods per year.
    payment_frequency : int | float
        Positive number of payments per year.
    years : float
        Time horizon in years.

    Returns
    -------
    float
        Computed nominal annuity present value as a scalar in the units implied by the input values.
    """
    i_p = convert_nominal_frequency(nominal_rate, compounding_frequency, payment_frequency)
    n_p = years * payment_frequency
    return effective_annuity_present_value(payment, i_p, n_p, due=False)


def continuous_annuity_present_value(annual_flow: float, delta: float, years: float) -> float:
    """Compute present value of a continuous cash-flow annuity.

    Parameters
    ----------
    annual_flow : float
        Continuous cash-flow rate in currency units per year.
    delta : float
        Constant force of interest in decimal annual units.
    years : float
        Time horizon in years.

    Returns
    -------
    float
        Computed continuous annuity present value as a scalar in the units implied by the input values.
    """
    R_anual = annual_flow
    n = years
    if delta == 0:
        return R_anual * n
    return R_anual * (1 - np.exp(-delta * n)) / delta


def perpetuity_present_value(payment: float, rate: float) -> float:
    """Compute the present value of a level perpetuity.

    Parameters
    ----------
    payment : float
        Level payment amount in currency units per payment period.
    rate : float
        Interest rate in decimal units under the stated compounding convention.

    Returns
    -------
    float
        Computed perpetuity present value as a scalar in the units implied by the input values.
    """
    if rate == 0:
        return 0
    return payment / rate


def geometric_gradient_future_value(R1: float, i_m: float, q_m: float, n_m: float) -> float:
    """Compute accumulated value of a geometric-gradient payment stream.

    Parameters
    ----------
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.
    q_m : float
        Growth rate of payments per gradient period in decimal units.
    n_m : float
        Number of gradient-payment periods.

    Returns
    -------
    float
        Computed geometric gradient future value as a scalar in the units implied by the input values.
    """
    if i_m == q_m:
        return n_m * R1 * ((1 + i_m) ** (n_m - 1))
    numerador = ((1 + i_m) ** n_m) - ((1 + q_m) ** n_m)
    denominador = i_m - q_m
    return R1 * (numerador / denominador)


def geometric_gradient_present_value(R1: float, i: float, q: float, n: float) -> float:
    """Compute present value of a geometric-gradient payment stream.

    Parameters
    ----------
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    i : float
        Effective interest rate per period in decimal units.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    n : float
        Number of discrete periods, assets, or observations as determined by the callable.

    Returns
    -------
    float
        Computed geometric gradient present value as a scalar in the units implied by the input values.
    """
    if i == q:
        return R1 * n / (1 + i)
    return R1 * (1 - ((1 + q) / (1 + i)) ** n) / (i - q)


def periods_for_annuity_future_value(
    future_value: float, payment: float, period_rate: float
) -> float:
    """Solve the period count for a level-annuity accumulated-value target.

    Parameters
    ----------
    future_value : float
        Target accumulated amount in currency units.
    payment : float
        Level payment amount in currency units per payment period.
    period_rate : float
        Effective interest rate per payment period in decimal units.

    Returns
    -------
    float
        Computed periods for annuity future value as a scalar in the units implied by the input values.
    """
    VF = future_value
    R = payment
    i_m = period_rate
    if i_m == 0:
        return VF / R
    val = (VF * i_m / R) + 1
    if val <= 0:
        return np.nan
    return np.log(val) / np.log(1 + i_m)


def periods_for_annuity_present_value(
    present_value: float, payment: float, period_rate: float
) -> float:
    """Solve the period count for a level-annuity present-value target.

    Parameters
    ----------
    present_value : float
        Target present amount in currency units.
    payment : float
        Level payment amount in currency units per payment period.
    period_rate : float
        Effective interest rate per payment period in decimal units.

    Returns
    -------
    float
        Computed periods for annuity present value as a scalar in the units implied by the input values.
    """
    VP = present_value
    R = payment
    i_m = period_rate
    if i_m == 0:
        return VP / R
    val = 1 - (VP * i_m / R)
    if val <= 0:
        return np.nan
    return -np.log(val) / np.log(1 + i_m)


def periods_for_geometric_gradient_future_value(
    future_value: float, R1: float, i_m: float, q_m: float
) -> float:
    """Solve the period count for a geometric-gradient accumulated-value target.

    Parameters
    ----------
    future_value : float
        Target accumulated amount in currency units.
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.
    q_m : float
        Growth rate of payments per gradient period in decimal units.

    Returns
    -------
    float
        Computed periods for geometric gradient future value as a scalar in the units implied by the input values.
    """
    VF = future_value

    def objective(n: float) -> float:
        if i_m == q_m:
            return n * R1 * ((1 + i_m) ** (n - 1)) - VF
        return R1 * (((1 + i_m) ** n - (1 + q_m) ** n) / (i_m - q_m)) - VF

    try:
        res = root_scalar(objective, bracket=[0.0001, 2000], method="brentq")
        return res.root
    except Exception:
        return np.nan


def periods_for_geometric_gradient_present_value(
    present_value: float, R1: float, i_m: float, q_m: float
) -> float:
    """Solve the period count for a geometric-gradient present-value target.

    Parameters
    ----------
    present_value : float
        Target present amount in currency units.
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.
    q_m : float
        Growth rate of payments per gradient period in decimal units.

    Returns
    -------
    float
        Computed periods for geometric gradient present value as a scalar in the units implied by the input values.
    """
    VP = present_value
    if i_m == q_m:
        return VP * (1 + i_m) / R1

    def objective(n: float) -> float:
        return R1 * (1 - ((1 + q_m) / (1 + i_m)) ** n) / (i_m - q_m) - VP

    try:
        res = root_scalar(objective, bracket=[0.0001, 2000], method="brentq")
        return res.root
    except Exception:
        return np.nan


def arithmetic_gradient_present_value(R1: float, G: float, i_m: float, n_m: float) -> float:
    """Compute present value of an arithmetic-gradient payment stream.

    Parameters
    ----------
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    G : float
        Arithmetic increment added to each successive payment, in currency units per period.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.
    n_m : float
        Number of gradient-payment periods.

    Returns
    -------
    float
        Computed arithmetic gradient present value as a scalar in the units implied by the input values.
    """
    if i_m == 0:
        return R1 * n_m + G * n_m * (n_m - 1) / 2
    an = (1 - (1 + i_m) ** (-n_m)) / i_m
    return R1 * an + (G / i_m) * (an - n_m * (1 + i_m) ** (-n_m))


def arithmetic_gradient_future_value(R1: float, G: float, i_m: float, n_m: float) -> float:
    """Compute accumulated value of an arithmetic-gradient payment stream.

    Parameters
    ----------
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    G : float
        Arithmetic increment added to each successive payment, in currency units per period.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.
    n_m : float
        Number of gradient-payment periods.

    Returns
    -------
    float
        Computed arithmetic gradient future value as a scalar in the units implied by the input values.
    """
    if i_m == 0:
        return R1 * n_m + G * n_m * (n_m - 1) / 2
    sn = ((1 + i_m) ** n_m - 1) / i_m
    return R1 * sn + (G / i_m) * (sn - n_m)


def periods_for_arithmetic_gradient_future_value(
    future_value: float, R1: float, G: float, i_m: float
) -> float:
    """Solve the period count for an arithmetic-gradient accumulated-value target.

    Parameters
    ----------
    future_value : float
        Target accumulated amount in currency units.
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    G : float
        Arithmetic increment added to each successive payment, in currency units per period.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.

    Returns
    -------
    float
        Computed periods for arithmetic gradient future value as a scalar in the units implied by the input values.
    """
    VF = future_value

    def objective(n: float) -> float:
        return arithmetic_gradient_future_value(R1, G, i_m, n) - VF

    try:
        res = root_scalar(objective, bracket=[0.0001, 2000], method="brentq")
        return res.root
    except Exception:
        return np.nan


def periods_for_arithmetic_gradient_present_value(
    present_value: float, R1: float, G: float, i_m: float
) -> float:
    """Solve the period count for an arithmetic-gradient present-value target.

    Parameters
    ----------
    present_value : float
        Target present amount in currency units.
    R1 : float
        First payment in a gradient cash-flow stream, in currency units.
    G : float
        Arithmetic increment added to each successive payment, in currency units per period.
    i_m : float
        Effective interest rate per gradient-payment period in decimal units.

    Returns
    -------
    float
        Computed periods for arithmetic gradient present value as a scalar in the units implied by the input values.
    """
    VP = present_value

    def objective(n: float) -> float:
        return arithmetic_gradient_present_value(R1, G, i_m, n) - VP

    try:
        res = root_scalar(objective, bracket=[0.0001, 2000], method="brentq")
        return res.root
    except Exception:
        return np.nan


__all__ = [
    "arithmetic_gradient_future_value",
    "arithmetic_gradient_present_value",
    "continuous_annuity_future_value",
    "continuous_annuity_present_value",
    "effective_annuity_future_value",
    "effective_annuity_present_value",
    "geometric_gradient_future_value",
    "geometric_gradient_present_value",
    "nominal_annuity_future_value",
    "nominal_annuity_present_value",
    "periods_for_annuity_future_value",
    "periods_for_annuity_present_value",
    "periods_for_arithmetic_gradient_future_value",
    "periods_for_arithmetic_gradient_present_value",
    "periods_for_geometric_gradient_future_value",
    "periods_for_geometric_gradient_present_value",
    "perpetuity_present_value",
]
