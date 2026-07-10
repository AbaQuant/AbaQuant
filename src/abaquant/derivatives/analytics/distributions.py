"""Distribution diagnostics and Monte Carlo error analytics.

Purpose
-------
The module computes sample moments and a theoretical standard-error proxy for Monte Carlo valuation.

Conventions
-----------
Sample arrays are interpreted as numerical observations; time is in years and volatility is annualized decimal volatility.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def distribution_moments(values: Sequence[float] | np.ndarray) -> dict[str, float]:
    """Compute sample distribution moments used for diagnostics.

    Parameters
    ----------
    values : Sequence[float] | np.ndarray
        One-dimensional numerical sample used for distribution diagnostics.

    Returns
    -------
    dict[str, float]
        Named outputs of the distribution moments calculation.
    """
    x = np.asarray(values, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std == 0:
        skew = 0.0
        kurt = 0.0
    else:
        centered = x - mean
        skew = np.mean(centered**3) / std**3
        kurt = np.mean(centered**4) / std**4 - 3.0
    return {"mean": float(mean), "std": float(std), "skew": float(skew), "kurt": float(kurt)}


def excess_kurtosis(values: Sequence[float] | np.ndarray) -> float:
    """Compute sample excess kurtosis.

    Parameters
    ----------
    values : Sequence[float] | np.ndarray
        One-dimensional numerical sample used for distribution diagnostics.

    Returns
    -------
    float
        Computed excess kurtosis as a scalar in the units implied by the input values.
    """
    return distribution_moments(values)["kurt"]


def theoretical_mc_error(
    reference_price: float,
    sigma: float,
    T: float,
    n_paths: Sequence[int] | np.ndarray,
) -> np.ndarray:
    """Compute the theoretical Monte Carlo standard-error proxy used by the module.

    Parameters
    ----------
    reference_price : float
        Reference option price used by the Monte Carlo error formula.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.
    n_paths : Sequence[int] | np.ndarray
        Number of Monte Carlo paths.

    Returns
    -------
    np.ndarray
        Result of the theoretical mc error calculation.
    """
    n = np.asarray(n_paths, dtype=float)
    return reference_price * sigma * np.sqrt(T) / np.sqrt(n)
