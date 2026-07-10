"""Forward, futures-style carry, foreign-exchange forward, and FRA valuation.

Purpose
-------
The module implements deterministic cost-of-carry identities and the value of existing forward-style contracts under several rate-compounding conventions.

Conventions
-----------
Rates are decimal rates. The compounding argument determines whether a rate is interpreted as continuously compounded or periodically compounded. Times are measured in years.

Scope and limitations
---------------------
It assumes deterministic financing and carry inputs and does not model stochastic interest rates or default risk.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np


def _is_continuous(compounding: str) -> bool:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    compounding : str
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    bool
        Whether the input satisfies the documented condition.
    """
    return compounding.strip().lower().startswith("continuous")


def _growth_factor(rate: float, maturity: float, compounding: str) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    maturity : float
        Time to option expiry in years.
    compounding : str
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed  growth factor as a scalar in the units implied by the input values.
    """
    if _is_continuous(compounding):
        return float(np.exp(rate * maturity))
    return float((1 + rate) ** maturity)


def _discount_factor(rate: float, maturity: float, compounding: str) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    maturity : float
        Time to option expiry in years.
    compounding : str
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed  discount factor as a scalar in the units implied by the input values.
    """
    return 1.0 / _growth_factor(rate, maturity, compounding)


def forward_price(
    spot: float,
    rate: float,
    maturity: float,
    carry: float = 0.0,
    compounding: str = "Continuous",
) -> float:
    """Compute the no-arbitrage forward price under the stated carry convention.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    maturity : float
        Time to option expiry in years.
    carry : float, default=0.0
        Net annual carry rate in decimal units.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed forward price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if _is_continuous(compounding):
        return float(spot * np.exp((rate - carry) * maturity))
    return float(
        spot
        * _growth_factor(rate, maturity, compounding)
        / _growth_factor(carry, maturity, compounding)
    )


def forward_price_with_yield(
    spot: float, rate: float, yield_rate: float, maturity: float, compounding: str = "Continuous"
) -> float:
    """Compute a forward price with continuous or periodic yield carry.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    yield_rate : float
        Dividend, income, or carry yield in decimal annual units.
    maturity : float
        Time to option expiry in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed forward price with yield as a dimensionless decimal quantity.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return forward_price(spot, rate, maturity, carry=yield_rate, compounding=compounding)


def forward_contract_value(
    spot: float,
    delivery_price: float,
    rate: float,
    yield_rate: float,
    time_to_maturity: float,
    position: str = "Long",
    compounding: str = "Continuous",
) -> float:
    """Compute the value of an existing long or short forward contract.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    delivery_price : float
        Forward delivery price fixed at trade inception, in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    yield_rate : float
        Dividend, income, or carry yield in decimal annual units.
    time_to_maturity : float
        Remaining time to contract maturity in years.
    position : str, default='Long'
        Position side, such as long or short, under the function convention.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed forward contract value as a scalar in the units implied by the input values.
    """
    long_value = live_forward_value(
        spot, delivery_price, rate, yield_rate, time_to_maturity, compounding=compounding
    )
    return long_value if position == "Long" else -long_value


def simple_forward_price(
    spot: float, rate: float, maturity: float, compounding: str = "Continuous"
) -> float:
    """Compute the forward price with financing carry only.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    maturity : float
        Time to option expiry in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed simple forward price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return forward_price(spot, rate, maturity, compounding=compounding)


def forward_price_with_continuous_dividend(
    spot: float,
    rate: float,
    dividend_yield: float,
    maturity: float,
    compounding: str = "Continuous",
) -> float:
    """Compute an equity forward price with continuous dividend yield.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    dividend_yield : float
        Continuous dividend yield in decimal annual units.
    maturity : float
        Time to option expiry in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed forward price with continuous dividend as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return forward_price(spot, rate, maturity, carry=dividend_yield, compounding=compounding)


def forward_price_with_discrete_dividends(
    spot: float,
    rate: float,
    maturity: float,
    present_value_dividends: float,
    compounding: str = "Continuous",
) -> float:
    """Compute an equity forward price after subtracting present-value discrete dividends.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    maturity : float
        Time to option expiry in years.
    present_value_dividends : float
        Present value of known discrete dividends in currency units.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed forward price with discrete dividends as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return float((spot - present_value_dividends) * _growth_factor(rate, maturity, compounding))


def commodity_forward_price(
    spot: float, rate: float, storage_cost: float, maturity: float, compounding: str = "Continuous"
) -> float:
    """Compute a commodity forward price with deterministic storage cost.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    storage_cost : float
        Annual deterministic storage-cost rate or amount under the function convention.
    maturity : float
        Time to option expiry in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed commodity forward price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if _is_continuous(compounding):
        return float(spot * np.exp((rate + storage_cost) * maturity))
    return float(
        spot
        * _growth_factor(rate, maturity, compounding)
        * _growth_factor(storage_cost, maturity, compounding)
    )


def fx_forward_price(
    spot: float,
    domestic_rate: float,
    foreign_rate: float,
    maturity: float,
    compounding: str = "Continuous",
) -> float:
    """Compute a foreign-exchange forward price from domestic and foreign rates.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    domestic_rate : float
        Domestic annual interest rate in decimal units.
    foreign_rate : float
        Foreign annual interest rate in decimal units.
    maturity : float
        Time to option expiry in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed fx forward price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return forward_price(spot, domestic_rate, maturity, carry=foreign_rate, compounding=compounding)


def live_forward_value(
    spot: float,
    delivery_price: float,
    rate: float,
    yield_rate: float,
    time_to_maturity: float,
    compounding: str = "Continuous",
) -> float:
    """Compute the current value of a forward with a fixed delivery price.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    delivery_price : float
        Forward delivery price fixed at trade inception, in currency units.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    yield_rate : float
        Dividend, income, or carry yield in decimal annual units.
    time_to_maturity : float
        Remaining time to contract maturity in years.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    float
        Computed live forward value as a scalar in the units implied by the input values.
    """
    return float(
        spot * _discount_factor(yield_rate, time_to_maturity, compounding)
        - delivery_price * _discount_factor(rate, time_to_maturity, compounding)
    )


def fra(
    r1: float,
    r2: float,
    t1: float,
    t2: float,
    notional: float,
    fixed_rate: float,
    compounding: str = "Continuous",
) -> tuple[float, float]:
    """Value the forward-rate-agreement cash-flow relationship implemented by this routine.

    Parameters
    ----------
    r1 : float
        First interest-rate input in decimal units.
    r2 : float
        Second interest-rate input in decimal units.
    t1 : float
        First accrual or settlement time in years.
    t2 : float
        Second accrual or settlement time in years.
    notional : float
        Forward-rate-agreement notional amount in currency units.
    fixed_rate : float
        Contractual fixed rate in decimal units.
    compounding : str, default='Continuous'
        Compounding convention or frequency accepted by the implementation.

    Returns
    -------
    tuple[float, float]
        Positional outputs produced by the fra calculation.
    """
    tau = t2 - t1
    if _is_continuous(compounding):
        forward_rate = (r2 * t2 - r1 * t1) / tau
    else:
        forward_rate = (
            _growth_factor(r2, t2, compounding) / _growth_factor(r1, t1, compounding)
        ) ** (1 / tau) - 1
    value = notional * (forward_rate - fixed_rate) * tau * _discount_factor(r2, t2, compounding)
    return float(forward_rate), float(value)


__all__ = [
    "commodity_forward_price",
    "forward_contract_value",
    "forward_price",
    "forward_price_with_continuous_dividend",
    "forward_price_with_discrete_dividends",
    "forward_price_with_yield",
    "fra",
    "fx_forward_price",
    "live_forward_value",
    "simple_forward_price",
]
