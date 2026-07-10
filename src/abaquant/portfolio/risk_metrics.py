"""Portfolio performance and downside-risk metrics.

Purpose
-------
The module computes return, volatility, drawdown, Sharpe, Sortino, historical VaR, historical CVaR, and related summary statistics from periodic return series.

Conventions
-----------
Returns are simple periodic returns. The default annualization factor is 252 trading days. Historical VaR and CVaR retain the implementation sign convention in which negative values denote losses.

References
----------
[ 1 ] Sharpe, W. F. (1966), "Mutual Fund Performance".
[ 2 ] Rockafellar, R. T., and S. Uryasev (2000), "Optimization of Conditional Value-at-Risk".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Basic helper functions.
# ---------------------------------------------------------------------------
def portfolio_returns(returns: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Compute the weighted portfolio return series.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    weights = np.asarray(weights, dtype=float)
    return returns.dot(weights)


def cumulative_returns(returns: pd.Series) -> pd.Series:
    """Convert periodic returns into a cumulative wealth index starting at one.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    return (1 + returns).cumprod()


# ---------------------------------------------------------------------------
# Return and volatility metrics.
# ---------------------------------------------------------------------------
def annualized_return(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Annualize the implemented periodic return statistic.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed annualized return as a dimensionless decimal quantity.
    """
    if len(returns) == 0:
        return 0.0
    total_return = (1 + returns).prod()
    n_years = len(returns) / periods
    if n_years <= 0:
        return 0.0
    return total_return ** (1 / n_years) - 1


def annualized_volatility(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Annualize sample volatility from periodic returns.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed annualized volatility as a dimensionless decimal quantity.
    """
    if len(returns) < 2:
        return 0.0
    return returns.std(ddof=1) * np.sqrt(periods)


# ---------------------------------------------------------------------------
# Risk-adjusted ratios
# ---------------------------------------------------------------------------
def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Compute the annualized Sharpe ratio from periodic returns.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    rf : float, default=0.0
        Risk-free rate under the function annualization convention.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed sharpe ratio as a dimensionless decimal quantity.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    vol = annualized_volatility(returns, periods)
    if vol == 0:
        return 0.0
    ret = annualized_return(returns, periods)
    return (ret - rf) / vol


def downside_deviation(
    returns: pd.Series, rf_daily: float = 0.0, periods: int = TRADING_DAYS
) -> float:
    """Compute annualized downside deviation relative to the supplied threshold.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    rf_daily : float, default=0.0
        Daily risk-free or target return threshold in decimal units.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed downside deviation as a scalar in the units implied by the input values.
    """
    downside = returns[returns < rf_daily] - rf_daily
    if len(downside) == 0:
        return 0.0
    return np.sqrt((downside**2).mean()) * np.sqrt(periods)


def sortino_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Compute the annualized Sortino ratio from periodic returns.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    rf : float, default=0.0
        Risk-free rate under the function annualization convention.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed sortino ratio as a dimensionless decimal quantity.
    """
    rf_daily = (1 + rf) ** (1 / periods) - 1
    dd = downside_deviation(returns, rf_daily, periods)
    if dd == 0:
        return 0.0
    ret = annualized_return(returns, periods)
    return (ret - rf) / dd


# ---------------------------------------------------------------------------
# Drawdown y Calmar
# ---------------------------------------------------------------------------
def drawdown_series(returns: pd.Series) -> pd.Series:
    """Compute the drawdown series of a return stream.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.
    """
    cum = cumulative_returns(returns)
    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    return dd


def max_drawdown(returns: pd.Series) -> float:
    """Return the most negative observed drawdown.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.

    Returns
    -------
    float
        Computed max drawdown as a scalar in the units implied by the input values.
    """
    if len(returns) == 0:
        return 0.0
    dd = drawdown_series(returns)
    return dd.min()  # negative value


def calmar_ratio(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Compute annualized return divided by absolute maximum drawdown.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed calmar ratio as a dimensionless decimal quantity.
    """
    mdd = max_drawdown(returns)
    if mdd == 0:
        return 0.0
    ret = annualized_return(returns, periods)
    return ret / abs(mdd)


def conditional_drawdown_at_risk(returns: pd.Series, alpha: float = 0.05) -> float:
    """Compute the mean of the worst observed drawdowns at the selected tail level.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    alpha : float, default=0.05
        Model-specific alpha parameter; consult the module convention.

    Returns
    -------
    float
        Computed conditional drawdown at risk as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    dd = drawdown_series(returns)
    if len(dd) == 0:
        return 0.0
    losses = -dd  # convertir a positivo
    var_dd = np.quantile(losses, 1 - alpha)
    tail = losses[losses >= var_dd]
    if len(tail) == 0:
        return var_dd
    return tail.mean()


# ---------------------------------------------------------------------------
# Value at Risk / Conditional VaR
# ---------------------------------------------------------------------------
def var_historical(returns: pd.Series, alpha: float = 0.05) -> float:
    """Compute historical value at risk under the module sign convention.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    alpha : float, default=0.05
        Model-specific alpha parameter; consult the module convention.

    Returns
    -------
    float
        Computed var historical as a scalar in the units implied by the input values.
    """
    if len(returns) == 0:
        return 0.0
    return np.quantile(returns, alpha)


def cvar_historical(returns: pd.Series, alpha: float = 0.05) -> float:
    """Compute historical conditional value at risk under the module sign convention.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    alpha : float, default=0.05
        Model-specific alpha parameter; consult the module convention.

    Returns
    -------
    float
        Computed cvar historical as a scalar in the units implied by the input values.
    """
    if len(returns) == 0:
        return 0.0
    var = var_historical(returns, alpha)
    tail = returns[returns <= var]
    if len(tail) == 0:
        return var
    return tail.mean()


# ---------------------------------------------------------------------------
# Complete metric summary.
# ---------------------------------------------------------------------------
def compute_all_metrics(
    returns: pd.Series,
    rf: float = 0.0,
    periods: int = TRADING_DAYS,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Compute the module portfolio-performance metric summary.

    Parameters
    ----------
    returns : pd.Series
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    rf : float, default=0.0
        Risk-free rate under the function annualization convention.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.
    alpha : float, default=0.05
        Model-specific alpha parameter; consult the module convention.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    return {
        "Annualized Return": annualized_return(returns, periods),
        "Annualized Volatility": annualized_volatility(returns, periods),
        "Sharpe Ratio": sharpe_ratio(returns, rf, periods),
        "Sortino Ratio": sortino_ratio(returns, rf, periods),
        "Max Drawdown": max_drawdown(returns),
        "Calmar Ratio": calmar_ratio(returns, periods),
        f"VaR {int((1 - alpha) * 100)}% (daily)": var_historical(returns, alpha),
        f"CVaR {int((1 - alpha) * 100)}% (daily)": cvar_historical(returns, alpha),
    }
