"""Pure portfolio return, covariance, and allocation mathematics.

Purpose
-------
The module transforms price panels into returns, annualizes moments, evaluates portfolios, and solves selected static allocation problems.

Conventions
-----------
Returns are simple or log returns as stated. The default annualization factor is 252 observations per year. Weight vectors are ordered consistently with the input expected-return vector or covariance matrix.

Scope and limitations
---------------------
Optimisation outputs are in-sample mathematical solutions; they do not include transaction costs, taxes, rebalancing, or investment advice.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
[ 2 ] Sharpe, W. F. (1966), "Mutual Fund Performance".
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import scipy.optimize as opt

TRADING_DAYS = 252


def simple_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute simple returns independently for each price series.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    return prices.astype(float).pct_change(fill_method=None).iloc[1:]


def log_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute logarithmic returns independently for each price series.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    price_frame = prices.astype(float)
    returns = np.log(price_frame / price_frame.shift(1)).iloc[1:]
    return returns.replace([np.inf, -np.inf], np.nan)


def annualized_mean_returns_from_returns(
    returns: pd.DataFrame, periods: int = TRADING_DAYS
) -> pd.Series:
    """Annualize arithmetic mean returns from periodic observations.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if periods <= 0:
        raise ValueError("periods must be positive.")
    return returns.astype(float).mean(skipna=True) * periods


def annualized_covariance_from_returns(
    returns: pd.DataFrame, periods: int = TRADING_DAYS
) -> pd.DataFrame:
    """Annualize the sample covariance matrix of periodic returns.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic simple return observations; rows are observation dates and columns are assets when two-dimensional.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if periods <= 0:
        raise ValueError("periods must be positive.")
    return returns.astype(float).cov() * periods


def equal_weight(n_assets: int) -> np.ndarray:
    """Construct or evaluate an equally weighted fully invested portfolio.

    Parameters
    ----------
    n_assets : int
        Number of assets in the allocation problem.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
    """
    if n_assets <= 0:
        raise ValueError("n_assets must be positive.")
    return np.full(n_assets, 1.0 / n_assets, dtype=float)


def portfolio_variance(weights: np.ndarray, covariance: np.ndarray) -> float:
    """Compute portfolio variance from a weight vector and covariance matrix.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    float
        Computed portfolio variance as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    _validate_portfolio_arrays(w, cov)
    return float(w @ cov @ w)


def minimum_variance_weights(
    covariance_matrix: np.ndarray,
    bounds: tuple[float, float] = (0.0, 1.0),
) -> np.ndarray:
    """Solve the constrained global minimum-variance allocation problem.

    Parameters
    ----------
    covariance_matrix : np.ndarray
        Square covariance matrix ordered consistently with the asset order.
    bounds : tuple[float, float], default=(0.0, 1.0)
        Allocation bounds in the format accepted by the underlying optimizer.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    cov = np.asarray(covariance_matrix, dtype=float)
    n_assets = _validate_covariance_matrix(cov)
    clean_bounds = _validate_bounds(bounds, n_assets)
    w0 = equal_weight(n_assets)

    result = opt.minimize(
        lambda w: portfolio_variance(w, cov),
        w0,
        method="SLSQP",
        bounds=[clean_bounds] * n_assets,
        constraints={"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    return _validated_optimizer_weights(result, n_assets)


def maximum_sharpe_weights(
    mean_returns: np.ndarray,
    covariance_matrix: np.ndarray,
    risk_free_rate: float,
    bounds: tuple[float, float] = (0.0, 1.0),
) -> np.ndarray:
    """Solve the constrained maximum-Sharpe portfolio allocation problem.

    Parameters
    ----------
    mean_returns : np.ndarray
        Expected-return vector ordered consistently with the covariance matrix.
    covariance_matrix : np.ndarray
        Square covariance matrix ordered consistently with the asset order.
    risk_free_rate : float
        Annual risk-free rate in decimal units.
    bounds : tuple[float, float], default=(0.0, 1.0)
        Allocation bounds in the format accepted by the underlying optimizer.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    expected = np.asarray(mean_returns, dtype=float)
    cov = np.asarray(covariance_matrix, dtype=float)
    n_assets = _validate_mean_covariance(expected, cov)
    clean_bounds = _validate_bounds(bounds, n_assets)
    rf = float(risk_free_rate)
    if not np.isfinite(rf):
        raise ValueError("risk_free_rate must be finite.")
    w0 = equal_weight(n_assets)

    def objective(weights: np.ndarray) -> float:
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        weights : np.ndarray
            Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.

        Returns
        -------
        float
            Computed objective as a scalar in the units implied by the input values.
        """
        ret = portfolio_return(weights, expected)
        variance = max(portfolio_variance(weights, cov), 1e-24)
        vol = float(np.sqrt(variance))
        return -portfolio_sharpe(ret, vol, rf)

    result = opt.minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=[clean_bounds] * n_assets,
        constraints={"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    return _validated_optimizer_weights(result, n_assets)


def historical_mean_returns(prices: pd.DataFrame, periods: int = TRADING_DAYS) -> pd.Series:
    """Estimate annualized arithmetic expected returns from historical prices.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    returns = simple_returns_from_prices(prices).dropna()
    return returns.mean() * periods


def sample_covariance(prices: pd.DataFrame, periods: int = TRADING_DAYS) -> pd.DataFrame:
    """Estimate an annualized covariance matrix from historical prices.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    returns = simple_returns_from_prices(prices).dropna()
    return returns.cov() * periods


def log_return_volatility(prices: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Estimate annualized volatility from historical log returns.

    Parameters
    ----------
    prices : pd.Series
        Price observations with dates on the index and assets on columns where applicable.
    periods : int, default=TRADING_DAYS
        Number of discrete compounding or payment periods.

    Returns
    -------
    float
        Computed log return volatility as a dimensionless decimal quantity.
    """
    log_returns = np.log(prices / prices.shift(1))
    log_returns = log_returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(log_returns) < 2:
        return 0.0
    return float(log_returns.std(ddof=1) * np.sqrt(periods))


def portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
    """Compute the weighted expected return of a portfolio.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.

    Returns
    -------
    float
        Computed portfolio return as a dimensionless decimal quantity.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    return float(np.asarray(weights, dtype=float) @ np.asarray(expected_returns, dtype=float))


def portfolio_volatility(weights: np.ndarray, covariance: np.ndarray) -> float:
    """Compute portfolio volatility from a weight vector and covariance matrix.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    float
        Computed portfolio volatility as a dimensionless decimal quantity.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    return float(np.sqrt(max(portfolio_variance(weights, covariance), 0.0)))


def portfolio_sharpe(return_: float, volatility: float, risk_free_rate: float = 0.0) -> float:
    """Compute the annualized excess-return-to-volatility ratio.

    Parameters
    ----------
    return_ : float
        Expected portfolio return in decimal annual units.
    volatility : float
        Volatility input: a positive annualized decimal number, ``"realized"``, or ``"market"`` as documented by the applied interface.
    risk_free_rate : float, default=0.0
        Annual risk-free rate in decimal units.

    Returns
    -------
    float
        Computed portfolio sharpe as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if volatility == 0:
        return 0.0
    return float((return_ - risk_free_rate) / volatility)


def equal_weight_portfolio(
    asset_names: list[str],
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_free_rate: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Compute the result defined by ``equal_weight_portfolio`` under this module's documented convention.

    Parameters
    ----------
    asset_names : list[str]
        Asset labels ordered consistently with expected returns and covariance.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    risk_free_rate : float
        Annual risk-free rate in decimal units.

    Returns
    -------
    tuple[float, float, float, dict[str, float]]
        Positional outputs produced by the equal weight portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    n_assets = len(asset_names)
    weights = np.ones(n_assets) / n_assets
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, covariance)
    sharpe = portfolio_sharpe(ret, vol, risk_free_rate)
    return (
        ret,
        vol,
        sharpe,
        {name: float(weight) for name, weight in zip(asset_names, weights, strict=True)},
    )


def max_sharpe_portfolio(
    asset_names: list[str],
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_free_rate: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Compute the result defined by ``max_sharpe_portfolio`` under this module's documented convention.

    Parameters
    ----------
    asset_names : list[str]
        Asset labels ordered consistently with expected returns and covariance.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    risk_free_rate : float
        Annual risk-free rate in decimal units.

    Returns
    -------
    tuple[float, float, float, dict[str, float]]
        Positional outputs produced by the max sharpe portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    n_assets = len(asset_names)
    expected = np.asarray(expected_returns, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    w0 = np.ones(n_assets) / n_assets

    def objective(weights: np.ndarray) -> float:
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        weights : np.ndarray
            Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.

        Returns
        -------
        float
            Computed objective as a scalar in the units implied by the input values.
        """
        ret = portfolio_return(weights, expected)
        vol = max(portfolio_volatility(weights, cov), 1e-12)
        return -portfolio_sharpe(ret, vol, risk_free_rate)

    result = opt.minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    weights = result.x if result.success else w0
    weights = np.clip(weights, 0.0, 1.0)
    weights = weights / weights.sum()
    ret = portfolio_return(weights, expected)
    vol = portfolio_volatility(weights, cov)
    sharpe = portfolio_sharpe(ret, vol, risk_free_rate)
    return (
        ret,
        vol,
        sharpe,
        {name: float(weight) for name, weight in zip(asset_names, weights, strict=True)},
    )


def min_variance_portfolio(
    asset_names: list[str],
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_free_rate: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Compute the result defined by ``min_variance_portfolio`` under this module's documented convention.

    Parameters
    ----------
    asset_names : list[str]
        Asset labels ordered consistently with expected returns and covariance.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    risk_free_rate : float
        Annual risk-free rate in decimal units.

    Returns
    -------
    tuple[float, float, float, dict[str, float]]
        Positional outputs produced by the min variance portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    n_assets = len(asset_names)
    expected = np.asarray(expected_returns, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    w0 = np.ones(n_assets) / n_assets

    result = opt.minimize(
        lambda w: w @ cov @ w,
        w0,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    weights = result.x if result.success else w0
    weights = np.clip(weights, 0.0, 1.0)
    weights = weights / weights.sum()
    ret = portfolio_return(weights, expected)
    vol = portfolio_volatility(weights, cov)
    sharpe = portfolio_sharpe(ret, vol, risk_free_rate)
    return (
        ret,
        vol,
        sharpe,
        {name: float(weight) for name, weight in zip(asset_names, weights, strict=True)},
    )


def risk_parity_objective(weights: np.ndarray, covariance: np.ndarray) -> float:
    """Compute the result defined by ``risk_parity_objective`` under this module's documented convention.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    float
        Computed risk parity objective as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    sigma = portfolio_volatility(w, cov)
    if sigma == 0:
        return 0.0
    marginal = cov @ w / sigma
    contribution = w * marginal
    target = sigma / len(w)
    return float(np.sum((contribution - target) ** 2))


def risk_parity_portfolio(
    asset_names: list[str],
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_free_rate: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Compute the result defined by ``risk_parity_portfolio`` under this module's documented convention.

    Parameters
    ----------
    asset_names : list[str]
        Asset labels ordered consistently with expected returns and covariance.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    risk_free_rate : float
        Annual risk-free rate in decimal units.

    Returns
    -------
    tuple[float, float, float, dict[str, float]]
        Positional outputs produced by the risk parity portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    n_assets = len(asset_names)
    w0 = np.ones(n_assets) / n_assets
    result = opt.minimize(
        risk_parity_objective,
        w0,
        args=(np.asarray(covariance, dtype=float),),
        method="SLSQP",
        bounds=[(1e-4, 1.0)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    weights = np.abs(result.x) / np.sum(np.abs(result.x))
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, covariance)
    sharpe = portfolio_sharpe(ret, vol, risk_free_rate)
    return (
        ret,
        vol,
        sharpe,
        {name: float(weight) for name, weight in zip(asset_names, weights, strict=True)},
    )


def mvsk_neg_utility(
    weights: np.ndarray,
    daily_returns: np.ndarray,
    lambda2: float = 1.0,
    lambda3: float = 0.5,
    lambda4: float = 0.5,
) -> float:
    """Compute the result defined by ``mvsk_neg_utility`` under this module's documented convention.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    daily_returns : np.ndarray
        Daily simple-return matrix used by higher-moment portfolio objectives.
    lambda2 : float, default=1.0
        Second-moment penalty coefficient in the MVSK utility.
    lambda3 : float, default=0.5
        Third-moment reward or penalty coefficient in the MVSK utility.
    lambda4 : float, default=0.5
        Fourth-moment penalty coefficient in the MVSK utility.

    Returns
    -------
    float
        Computed mvsk neg utility as a scalar in the units implied by the input values.
    """
    w = np.asarray(weights, dtype=float)
    port_returns = np.asarray(daily_returns, dtype=float) @ w
    mean = float(np.mean(port_returns))
    variance = float(np.var(port_returns))
    std = float(np.std(port_returns)) + 1e-10
    skewness = float(np.mean(((port_returns - mean) / std) ** 3))
    kurtosis = float(np.mean(((port_returns - mean) / std) ** 4))
    utility = mean - lambda2 * variance + lambda3 * skewness - lambda4 * kurtosis
    return float(-utility)


def mvsk_portfolio(
    asset_names: list[str],
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    daily_returns: np.ndarray,
    risk_free_rate: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Compute the result defined by ``mvsk_portfolio`` under this module's documented convention.

    Parameters
    ----------
    asset_names : list[str]
        Asset labels ordered consistently with expected returns and covariance.
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    daily_returns : np.ndarray
        Daily simple-return matrix used by higher-moment portfolio objectives.
    risk_free_rate : float
        Annual risk-free rate in decimal units.

    Returns
    -------
    tuple[float, float, float, dict[str, float]]
        Positional outputs produced by the mvsk portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    n_assets = len(asset_names)
    w0 = np.ones(n_assets) / n_assets
    result = opt.minimize(
        mvsk_neg_utility,
        w0,
        args=(np.asarray(daily_returns, dtype=float),),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        options={"ftol": 1e-12, "maxiter": 2000},
    )
    weights = np.abs(result.x) / np.sum(np.abs(result.x))
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, covariance)
    sharpe = portfolio_sharpe(ret, vol, risk_free_rate)
    return (
        ret,
        vol,
        sharpe,
        {name: float(weight) for name, weight in zip(asset_names, weights, strict=True)},
    )


def monte_carlo_portfolio_cloud(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_free_rate: float,
    n_simulations: int = 2500,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute the result defined by ``monte_carlo_portfolio_cloud`` under this module's documented convention.

    Parameters
    ----------
    expected_returns : np.ndarray
        Expected-return vector ordered consistently with portfolio weights and covariance.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.
    risk_free_rate : float
        Annual risk-free rate in decimal units.
    n_simulations : int, default=2500
        Number of simulated portfolio allocations.
    seed : int | None, default=None
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        Positional outputs produced by the monte carlo portfolio cloud calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    rng = np.random.default_rng(seed)
    expected = np.asarray(expected_returns, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    weights = rng.dirichlet(np.ones(len(expected)), size=n_simulations)
    returns = weights @ expected
    volatilities = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    sharpes = (returns - risk_free_rate) / volatilities
    return weights, returns, volatilities, sharpes


def evaluate_custom_portfolio(
    prices: pd.DataFrame,
    weights_by_asset: dict[str, float],
    expected_return_fn: Callable[[pd.DataFrame], pd.Series],
    covariance_fn: Callable[[pd.DataFrame], pd.DataFrame],
) -> tuple[float, float, np.ndarray, list[str]]:
    """Compute the result defined by ``evaluate_custom_portfolio`` under this module's documented convention.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.
    weights_by_asset : dict[str, float]
        Mapping from asset label to portfolio weight.
    expected_return_fn : Callable[[pd.DataFrame], pd.Series]
        Callable that estimates expected returns from a price panel.
    covariance_fn : Callable[[pd.DataFrame], pd.DataFrame]
        Callable that estimates a covariance matrix from a price panel.

    Returns
    -------
    tuple[float, float, np.ndarray, list[str]]
        Positional outputs produced by the evaluate custom portfolio calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    mu = expected_return_fn(prices)
    covariance = covariance_fn(prices)
    weights = np.array([weights_by_asset.get(column, 0.0) for column in prices.columns])
    total_weight = weights.sum()
    if total_weight > 0:
        weights = weights / total_weight
    ret = portfolio_return(weights, mu.values)
    vol = portfolio_volatility(weights, covariance.values)
    return ret, vol, weights, list(prices.columns)


def evaluate_custom_portfolio_from_prices(
    prices: pd.DataFrame,
    weights_by_asset: dict[str, float],
) -> tuple[float, float, np.ndarray, list[str]]:
    """Compute the result defined by ``evaluate_custom_portfolio_from_prices`` under this module's documented convention.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.
    weights_by_asset : dict[str, float]
        Mapping from asset label to portfolio weight.

    Returns
    -------
    tuple[float, float, np.ndarray, list[str]]
        Positional outputs produced by the evaluate custom portfolio from prices calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    return evaluate_custom_portfolio(
        prices,
        weights_by_asset,
        historical_mean_returns,
        sample_covariance,
    )


def optimize_portfolio_strategies(
    prices: pd.DataFrame,
    risk_free_rate: float = 0.05,
    n_simulations: int = 2500,
    seed: int | None = None,
) -> tuple[
    pd.Series,
    pd.DataFrame,
    dict[str, tuple[float, float, float, dict[str, float]]],
    tuple[np.ndarray, np.ndarray, np.ndarray],
]:
    """Compute the result defined by ``optimize_portfolio_strategies`` under this module's documented convention.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.
    risk_free_rate : float, default=0.05
        Annual risk-free rate in decimal units.
    n_simulations : int, default=2500
        Number of simulated portfolio allocations.
    seed : int | None, default=None
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    tuple[pd.Series, pd.DataFrame, dict[str, tuple[float, float, float, dict[str, float]]], tuple[np.ndarray, np.ndarray, np.ndarray]]
        Positional outputs produced by the optimize portfolio strategies calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    mu = historical_mean_returns(prices)
    covariance = sample_covariance(prices)
    daily_returns = prices.pct_change().dropna()
    assets = list(prices.columns)

    ret_s, vol_s, sharpe_s, weights_sharpe = max_sharpe_portfolio(
        assets, mu.values, covariance.values, risk_free_rate
    )
    ret_m, vol_m, sharpe_m, weights_min = min_variance_portfolio(
        assets, mu.values, covariance.values, risk_free_rate
    )
    ret_eq, vol_eq, sharpe_eq, weights_equal = equal_weight_portfolio(
        assets, mu.values, covariance.values, risk_free_rate
    )
    ret_rp, vol_rp, sharpe_rp, weights_risk_parity = risk_parity_portfolio(
        assets, mu.values, covariance.values, risk_free_rate
    )
    ret_mv, vol_mv, sharpe_mv, weights_mvsk = mvsk_portfolio(
        assets, mu.values, covariance.values, daily_returns.values, risk_free_rate
    )

    _, ret_sim, vol_sim, sharpe_sim = monte_carlo_portfolio_cloud(
        mu.values,
        covariance.values,
        risk_free_rate,
        n_simulations=n_simulations,
        seed=seed,
    )
    results = {
        "Max Sharpe": (ret_s, vol_s, sharpe_s, weights_sharpe),
        "Min Variance": (ret_m, vol_m, sharpe_m, weights_min),
        "Equal Weight 1/N": (ret_eq, vol_eq, sharpe_eq, weights_equal),
        "Risk Parity": (ret_rp, vol_rp, sharpe_rp, weights_risk_parity),
        "MVSK": (ret_mv, vol_mv, sharpe_mv, weights_mvsk),
    }
    return mu, covariance, results, (ret_sim, vol_sim, sharpe_sim)


def _validate_portfolio_arrays(weights: np.ndarray, covariance: np.ndarray) -> None:
    """Validate an internal input invariant used by the surrounding calculation.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    None
        Result of the  validate portfolio arrays calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if weights.ndim != 1:
        raise ValueError("weights must be a one-dimensional array.")
    n_assets = _validate_covariance_matrix(covariance)
    if len(weights) != n_assets:
        raise ValueError("weights length must match covariance dimensions.")
    if not np.all(np.isfinite(weights)):
        raise ValueError("weights must be finite.")


def _validate_covariance_matrix(covariance: np.ndarray) -> int:
    """Validate an internal input invariant used by the surrounding calculation.

    Parameters
    ----------
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    int
        Computed  validate covariance matrix as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]:
        raise ValueError("covariance_matrix must be square.")
    if covariance.shape[0] == 0:
        raise ValueError("covariance_matrix must contain at least one asset.")
    if not np.all(np.isfinite(covariance)):
        raise ValueError("covariance_matrix must be finite.")
    return int(covariance.shape[0])


def _validate_mean_covariance(mean_returns: np.ndarray, covariance: np.ndarray) -> int:
    """Validate an internal input invariant used by the surrounding calculation.

    Parameters
    ----------
    mean_returns : np.ndarray
        Expected-return vector ordered consistently with the covariance matrix.
    covariance : np.ndarray
        Square covariance matrix ordered consistently with the weight vector.

    Returns
    -------
    int
        Computed  validate mean covariance as a scalar in the units implied by the input values.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if mean_returns.ndim != 1:
        raise ValueError("mean_returns must be one-dimensional.")
    if not np.all(np.isfinite(mean_returns)):
        raise ValueError("mean_returns must be finite.")
    n_assets = _validate_covariance_matrix(covariance)
    if len(mean_returns) != n_assets:
        raise ValueError("mean_returns length must match covariance dimensions.")
    return n_assets


def _validate_bounds(bounds: tuple[float, float], n_assets: int) -> tuple[float, float]:
    """Validate an internal input invariant used by the surrounding calculation.

    Parameters
    ----------
    bounds : tuple[float, float]
        Allocation bounds in the format accepted by the underlying optimizer.
    n_assets : int
        Number of assets in the allocation problem.

    Returns
    -------
    tuple[float, float]
        Positional outputs produced by the  validate bounds calculation.
    """
    lower, upper = (float(bounds[0]), float(bounds[1]))
    if not np.isfinite(lower) or not np.isfinite(upper):
        raise ValueError("bounds must be finite.")
    if lower > upper:
        raise ValueError("lower bound must be less than or equal to upper bound.")
    if n_assets * lower > 1.0 + 1e-12 or n_assets * upper < 1.0 - 1e-12:
        raise ValueError("bounds are infeasible for a fully invested portfolio.")
    return lower, upper


def _validated_optimizer_weights(result: opt.OptimizeResult, n_assets: int) -> np.ndarray:
    """Validate an internal input invariant used by the surrounding calculation.

    Parameters
    ----------
    result : opt.OptimizeResult
        Optimizer result object validated by the internal helper.
    n_assets : int
        Number of assets in the allocation problem.

    Returns
    -------
    np.ndarray
        Result of the  validated optimizer weights calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if not result.success:
        message = str(getattr(result, "message", "optimization failed"))
        raise ValueError(f"portfolio optimization failed: {message}")
    weights = np.asarray(result.x, dtype=float)
    if weights.shape != (n_assets,) or not np.all(np.isfinite(weights)):
        raise ValueError("portfolio optimization returned invalid weights.")
    total = float(weights.sum())
    if not np.isfinite(total) or abs(total) < 1e-12:
        raise ValueError("portfolio optimization returned zero total weight.")
    weights = weights / total
    if not np.isclose(weights.sum(), 1.0, atol=1e-8):
        raise ValueError("portfolio optimization weights do not sum to 1.")
    return weights


__all__ = [
    "annualized_covariance_from_returns",
    "annualized_mean_returns_from_returns",
    "equal_weight",
    "equal_weight_portfolio",
    "evaluate_custom_portfolio",
    "evaluate_custom_portfolio_from_prices",
    "historical_mean_returns",
    "log_return_volatility",
    "log_returns_from_prices",
    "max_sharpe_portfolio",
    "maximum_sharpe_weights",
    "min_variance_portfolio",
    "minimum_variance_weights",
    "monte_carlo_portfolio_cloud",
    "mvsk_neg_utility",
    "mvsk_portfolio",
    "optimize_portfolio_strategies",
    "portfolio_return",
    "portfolio_sharpe",
    "portfolio_variance",
    "portfolio_volatility",
    "risk_parity_objective",
    "risk_parity_portfolio",
    "sample_covariance",
    "simple_returns_from_prices",
]
