"""Equity valuation primitives.

Purpose
-------
The module implements Gordon--Shapiro dividend-growth valuation, implied required return, and multiple-based valuation helpers.

Conventions
-----------
Dividends and prices use common currency units; growth and required returns are decimal annual rates.

Scope and limitations
---------------------
The Gordon--Shapiro model requires a required return greater than the perpetual growth rate.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations


def gordon_shapiro_valuation(
    next_dividend: float, required_return: float, growth_rate: float
) -> float:
    """Value equity under the constant-growth Gordon--Shapiro dividend model.

    Parameters
    ----------
    next_dividend : float
        Dividend expected in the next period, in currency units.
    required_return : float
        Required equity return in decimal annual units.
    growth_rate : float
        Constant growth rate in decimal annual units.

    Returns
    -------
    float
        Computed gordon shapiro valuation as a scalar in the units implied by the input values.
    """
    if required_return <= growth_rate:
        return None
    return next_dividend / (required_return - growth_rate)


def required_equity_return(next_dividend: float, current_price: float, growth_rate: float) -> float:
    """Infer the constant-growth required equity return from dividend and price inputs.

    Parameters
    ----------
    next_dividend : float
        Dividend expected in the next period, in currency units.
    current_price : float
        Current equity price in currency units.
    growth_rate : float
        Constant growth rate in decimal annual units.

    Returns
    -------
    float
        Computed required equity return as a dimensionless decimal quantity.
    """
    if current_price <= 0:
        return None
    return (next_dividend / current_price) + growth_rate


def multiples_valuation(value_metric: float, target_multiple: float) -> float:
    """Estimate value by applying a selected valuation multiple.

    Parameters
    ----------
    value_metric : float
        Fundamental metric to which a valuation multiple is applied.
    target_multiple : float
        Comparable-company valuation multiple applied to the selected metric.

    Returns
    -------
    float
        Computed multiples valuation as a scalar in the units implied by the input values.
    """
    return value_metric * target_multiple


__all__ = ["gordon_shapiro_valuation", "multiples_valuation", "required_equity_return"]
