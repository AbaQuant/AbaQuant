"""Markowitz efficient-frontier and random-portfolio calculations.

Purpose
-------
The module traces constrained minimum-variance portfolios across a target-return grid and generates random fully invested portfolio clouds.

Conventions
-----------
Expected returns and covariance are annualized inputs. The allow_short flag controls whether the optimizer enforces non-negative weights.

Scope and limitations
---------------------
Numerical solutions depend on the supplied covariance matrix and SciPy optimizer convergence.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

TRADING_DAYS = 252


def _portfolio_perf(w: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> tuple[float, float]:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    w : np.ndarray
        Numeric portfolio-weight vector in the established asset order.
    mu : np.ndarray
        Expected-return vector ordered consistently with the covariance matrix.
    cov : np.ndarray
        Covariance matrix ordered consistently with the associated asset vectors.

    Returns
    -------
    tuple[float, float]
        Positional outputs produced by the  portfolio perf calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    ret = float(w @ mu)
    vol = float(np.sqrt(max(w @ cov @ w, 0)))
    return ret, vol


def markowitz_frontier(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    n_points: int = 50,
    allow_short: bool = False,
) -> pd.DataFrame:
    """Trace the constrained Markowitz efficient frontier over target returns.

    Parameters
    ----------
    mean_returns : pd.Series
        Expected-return vector ordered consistently with the covariance matrix.
    cov_matrix : pd.DataFrame
        Square covariance matrix ordered consistently with the asset order.
    n_points : int, default=50
        Number of target-return points used to trace the frontier.
    allow_short : bool, default=False
        Whether negative portfolio weights are allowed by the optimizer.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    mu = mean_returns.values
    cov = cov_matrix.values
    n = len(mu)
    tickers = list(mean_returns.index)

    bounds = tuple((-1.0, 1.0) if allow_short else (0.0, 1.0) for _ in range(n))
    x0 = np.repeat(1.0 / n, n)

    # Grid of target expected returns.
    ret_min = mu.min()
    ret_max = mu.max()
    target_returns = np.linspace(ret_min, ret_max, n_points)

    rows = []
    for target in target_returns:
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t},
        )

        def variance(w):
            """Compute the result defined by ``variance`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            float
                Computed variance in the units implied by the documented inputs.

            Notes
            -----
            This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
            """
            return w @ cov @ w

        result = minimize(
            variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-12},
        )
        if not result.success:
            continue

        w = result.x
        ret, vol = _portfolio_perf(w, mu, cov)
        row = {"Return": ret, "Volatility": vol}
        row.update({t: wi for t, wi in zip(tickers, w, strict=True)})
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["Sharpe"] = df["Return"] / df["Volatility"].replace(0, np.nan)
    return df.sort_values("Volatility").reset_index(drop=True)


def monte_carlo_portfolios(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    n_portfolios: int = 3000,
    rf: float = 0.0,
    allow_short: bool = False,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Generate a random fully invested portfolio cloud.

    Parameters
    ----------
    mean_returns : pd.Series
        Expected-return vector ordered consistently with the covariance matrix.
    cov_matrix : pd.DataFrame
        Square covariance matrix ordered consistently with the asset order.
    n_portfolios : int, default=3000
        Number of random portfolios to generate.
    rf : float, default=0.0
        Risk-free rate under the function annualization convention.
    allow_short : bool, default=False
        Whether negative portfolio weights are allowed by the optimizer.
    seed : int | None, default=42
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    rng = np.random.default_rng(seed)
    mu = mean_returns.values
    cov = cov_matrix.values
    n = len(mu)
    tickers = list(mean_returns.index)

    if allow_short:
        raw = rng.normal(size=(n_portfolios, n))
        weights = raw / np.abs(raw).sum(axis=1, keepdims=True)
    else:
        # A Dirichlet draw produces non-negative weights that sum to one.
        weights = rng.dirichlet(np.ones(n), size=n_portfolios)

    rets = weights @ mu
    vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    vols = np.clip(vols, 1e-12, None)
    sharpes = (rets - rf) / vols

    df = pd.DataFrame(weights, columns=tickers)
    df.insert(0, "Sharpe", sharpes)
    df.insert(0, "Volatility", vols)
    df.insert(0, "Return", rets)
    return df
