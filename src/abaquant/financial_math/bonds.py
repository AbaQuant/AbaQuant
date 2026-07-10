"""Deterministic coupon-bond valuation and interest-rate risk measures.

Purpose
-------
The module computes coupon-bond prices, solves yield to maturity numerically, and reports duration and convexity measures.

Conventions
-----------
Coupon and yield rates are per coupon period. Redemption and face values use currency units. Payment frequency converts period measures to annual measures.

Scope and limitations
---------------------
The risk metrics assume parallel yield shifts and deterministic promised cash flows.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import root_scalar


def bond_price(
    face_value: float,
    coupon_rate_per_period: float,
    redemption_value: float,
    yield_per_period: float,
    periods: int,
) -> tuple[float, float, float, float]:
    """Value a coupon bond from deterministic promised cash flows.

    Parameters
    ----------
    face_value : float
        Bond face or par value in currency units.
    coupon_rate_per_period : float
        Coupon rate per payment period in decimal units.
    redemption_value : float
        Bond redemption value paid at maturity in currency units.
    yield_per_period : float
        Yield rate per coupon period in decimal units.
    periods : int
        Number of discrete compounding or payment periods.

    Returns
    -------
    tuple[float, float, float, float]
        ``(price, coupon_per_period, coupon_present_value, redemption_present_value)`` in positional order.
    """
    F = face_value
    r_m = coupon_rate_per_period
    C = redemption_value
    i_m = yield_per_period
    n = periods
    coupon_payment = F * r_m

    if i_m == 0:
        coupon_present_value = coupon_payment * n
    else:
        coupon_present_value = coupon_payment * ((1 - (1 + i_m) ** (-n)) / i_m)

    redemption_present_value = C * (1 + i_m) ** (-n)
    total_price = coupon_present_value + redemption_present_value
    return total_price, coupon_payment, coupon_present_value, redemption_present_value


def bond_yield(
    price: float,
    face_value: float,
    coupon_rate_per_period: float,
    redemption_value: float,
    periods: int,
) -> float:
    """Solve the yield per coupon period consistent with an observed bond price.

    Parameters
    ----------
    price : float
        Price or option premium in currency units.
    face_value : float
        Bond face or par value in currency units.
    coupon_rate_per_period : float
        Coupon rate per payment period in decimal units.
    redemption_value : float
        Bond redemption value paid at maturity in currency units.
    periods : int
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed bond yield as a dimensionless decimal quantity.
    """
    P = price
    F = face_value
    r_m = coupon_rate_per_period
    C = redemption_value
    n = periods

    def f(i):
        """Compute the result defined by ``f`` under this module's documented convention.

        Parameters
        ----------
        i : float or array-like
            Effective interest rate per period in decimal units.

        Returns
        -------
        object
            Result of the f workflow.
        """
        calculated_price = F * r_m * n + C if i == 0 else bond_price(F, r_m, C, i, n)[0]
        return calculated_price - P

    try:
        res = root_scalar(f, bracket=[-0.99, 10.0], method="brentq")
        return res.root
    except Exception:
        return np.nan


def bond_risk(
    face_value: float,
    coupon_rate_per_period: float,
    redemption_value: float,
    yield_per_period: float,
    periods: int,
    payments_per_year: int | float,
) -> tuple[float, float, float]:
    """Compute price, duration, and convexity measures for a coupon bond.

    Parameters
    ----------
    face_value : float
        Bond face or par value in currency units.
    coupon_rate_per_period : float
        Coupon rate per payment period in decimal units.
    redemption_value : float
        Bond redemption value paid at maturity in currency units.
    yield_per_period : float
        Yield rate per coupon period in decimal units.
    periods : int
        Number of discrete compounding or payment periods.
    payments_per_year : int | float
        Coupon or payment frequency per year.

    Returns
    -------
    tuple[float, float, float]
        ``(price, Macaulay_duration_years, convexity_years_squared)`` under the implemented coupon-bond convention.
    """
    F = face_value
    coupon_rate = coupon_rate_per_period
    C = redemption_value
    periodic_rate = yield_per_period
    period_count = periods
    m = payments_per_year
    coupon_payment = F * coupon_rate
    price = 0.0
    sum_mac = 0.0
    sum_conv = 0.0

    for t in range(1, int(period_count) + 1):
        cf = coupon_payment if t < period_count else coupon_payment + C
        pv_cashflow = cf / ((1 + periodic_rate) ** t)
        price += pv_cashflow
        sum_mac += t * pv_cashflow
        sum_conv += t * (t + 1) * pv_cashflow

    mac_duration_periods = sum_mac / price
    mac_duration_years = mac_duration_periods / m
    mod_duration_years = mac_duration_years / (1 + periodic_rate)
    convexity_years = sum_conv / (price * (m**2) * ((1 + periodic_rate) ** 2))

    return mac_duration_years, mod_duration_years, convexity_years


__all__ = ["bond_price", "bond_risk", "bond_yield"]
