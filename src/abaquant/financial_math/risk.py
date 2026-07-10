"""Parametric and simulation-based market-risk measures.

Purpose
-------
The module estimates value at risk and conditional value at risk from annual return and volatility assumptions.

Conventions
-----------
Returns and volatility are annualized decimal quantities unless a horizon conversion is applied. Portfolio value is expressed in currency units.

Scope and limitations
---------------------
The parametric method relies on its stated distributional assumptions; simulated estimates depend on the random seed and number of paths.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Rockafellar, R. T., and S. Uryasev (2000), "Optimization of Conditional Value-at-Risk".
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def parametric_var(
    annual_return: float,
    annual_volatility: float,
    portfolio_value: float,
    confidence_level: float,
    horizon_days: int | float,
) -> tuple[float, float, float, float]:
    """Estimate parametric value at risk under the implemented return distribution.

    Parameters
    ----------
    annual_return : float
        Annual expected return in decimal units.
    annual_volatility : float
        Annual volatility in decimal units.
    portfolio_value : float
        Current portfolio value in currency units.
    confidence_level : float
        Confidence probability for a tail-risk measure.
    horizon_days : int | float
        Risk-measure horizon in trading days.

    Returns
    -------
    tuple[float, float, float, float]
        ``(var_amount, z_score, period_return, period_volatility)``. The second
        value is the normal quantile used in the VaR calculation; it is not CVaR.
    """
    t = horizon_days / 252.0
    period_return = annual_return * t
    period_volatility = annual_volatility * np.sqrt(t)
    z_score = norm.ppf(confidence_level)
    var_amount = portfolio_value * (z_score * period_volatility - period_return)
    return max(var_amount, 0), z_score, period_return, period_volatility


def monte_carlo_var_cvar(
    annual_return: float,
    annual_volatility: float,
    portfolio_value: float,
    confidence_level: float,
    horizon_days: int | float,
    simulations: int = 10000,
    seed: int = 42,
) -> tuple[float, float]:
    """Estimate value at risk and conditional value at risk by simulation.

    Parameters
    ----------
    annual_return : float
        Annual expected return in decimal units.
    annual_volatility : float
        Annual volatility in decimal units.
    portfolio_value : float
        Current portfolio value in currency units.
    confidence_level : float
        Confidence probability for a tail-risk measure.
    horizon_days : int | float
        Risk-measure horizon in trading days.
    simulations : int, default=10000
        Number of Monte Carlo simulations.
    seed : int, default=42
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    tuple[float, float]
        Positional outputs produced by the monte carlo var cvar calculation.
    """
    t = horizon_days / 252.0
    period_return = annual_return * t
    period_volatility = annual_volatility * np.sqrt(t)

    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal(simulations)
    simulated_returns = period_return + period_volatility * shocks

    alpha = 1.0 - confidence_level
    q_alpha = np.percentile(simulated_returns, alpha * 100)

    tail = simulated_returns[simulated_returns <= q_alpha]
    cvar_alpha = tail.mean() if len(tail) > 0 else q_alpha

    return max(-q_alpha * portfolio_value, 0), max(-cvar_alpha * portfolio_value, 0)


__all__ = ["monte_carlo_var_cvar", "parametric_var"]
