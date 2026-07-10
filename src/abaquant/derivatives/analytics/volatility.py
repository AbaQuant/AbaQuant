"""Historical and implied-volatility analytics.

Purpose
-------
The module computes rolling realized volatility from price data and aligns implied-versus-realized volatility spreads.

Conventions
-----------
Annualization defaults and rolling-window units are documented by each callable. Volatilities are decimal quantities.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np


def realized_vol(prices, window=21, annualize=252):
    """Compute rolling realized volatility from a price series.

    Parameters
    ----------
    prices : pandas.DataFrame or array-like
        Price observations with dates on the index and assets on columns where applicable.
    window : int, default=21
        Rolling observation window length used for realized volatility.
    annualize : int, default=252
        Annualization factor or flag accepted by the volatility routine.

    Returns
    -------
    object
        Result of the realized vol workflow.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    prices = np.array(prices, dtype=float)
    log_ret = np.log(prices[1:] / prices[:-1])
    rv = np.full(len(prices), np.nan)
    for i in range(window, len(log_ret) + 1):
        rv[i] = np.std(log_ret[i - window : i], ddof=1) * np.sqrt(annualize)
    return rv


def iv_rv_spread(iv_series, rv_series):
    """Align implied and realized volatility series and compute their spread.

    Parameters
    ----------
    iv_series : float or array-like
        Implied-volatility series in decimal annual units.
    rv_series : float or array-like
        Realized-volatility series in decimal annual units.

    Returns
    -------
    float
        Computed iv rv spread in the units implied by the documented inputs.
    """
    iv = np.array(iv_series, dtype=float)
    rv = np.array(rv_series, dtype=float)
    spread = iv - rv
    return {
        "spread": spread,
        "mean_spread": np.nanmean(spread),
        "std_spread": np.nanstd(spread),
        "pct_positive": np.nanmean(spread > 0) * 100,
    }
