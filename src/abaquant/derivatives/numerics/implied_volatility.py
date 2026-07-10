"""Implied-volatility inversion routines.

Purpose
-------
The module solves Black--Scholes--Merton and Bachelier inverse-pricing problems from a supplied market option premium.

Conventions
-----------
Returned implied volatilities are annualized decimal values. Inputs must be compatible with the numerical model and no-arbitrage bounds.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
[ 2 ] Bachelier, L. (1900), "Theorie de la Speculation".
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from ..validation import validate_option_type


def _bsm_price(
    S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: str
) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    option_type : str
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed  bsm price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 0:
        return float(max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0))
    if sigma <= 0:
        forward_intrinsic = S * np.exp(-q * T) - K * np.exp(-r * T)
        return float(
            max(forward_intrinsic, 0.0) if option_type == "call" else max(-forward_intrinsic, 0.0)
        )
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return float(S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1))


def implied_volatility_black_scholes(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: str = "call",
    tol: float = 1e-6,
    max_iter: int = 200,
) -> float:
    """Invert a Black--Scholes--Merton premium for implied volatility.

    Parameters
    ----------
    market_price : float
        Observed option premium in the same currency units as spot and strike.
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.
    tol : float, default=1e-06
        Numerical convergence tolerance.
    max_iter : int, default=200
        Maximum numerical-optimizer or root-finder iterations.

    Returns
    -------
    float
        Computed implied volatility black scholes as a dimensionless decimal quantity.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    validate_option_type(option_type)

    def objective(sigma: float) -> float:
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        sigma : float
            Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.

        Returns
        -------
        float
            Computed objective as a scalar in the units implied by the input values.
        """
        return _bsm_price(S, K, T, r, sigma, q, option_type) - market_price

    low = objective(1e-6)
    high = objective(10.0)
    if np.isnan(low) or np.isnan(high) or low * high > 0:
        return float(np.nan)
    return float(brentq(objective, 1e-6, 10.0, xtol=tol, maxiter=max_iter))


def _bachelier_price(
    S: float, K: float, T: float, r: float, sigma_n: float, q: float, option_type: str
) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma_n : float
        Annualized normal volatility in price units per square-root year.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    option_type : str
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed  bachelier price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 0:
        return float(max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0))
    F = S * np.exp((r - q) * T)
    vol = sigma_n * np.sqrt(T)
    if vol <= 0:
        intrinsic = F - K
        return float(
            np.exp(-r * T)
            * (max(intrinsic, 0.0) if option_type == "call" else max(-intrinsic, 0.0))
        )
    d = (F - K) / vol
    if option_type == "call":
        return float(np.exp(-r * T) * ((F - K) * norm.cdf(d) + vol * norm.pdf(d)))
    return float(np.exp(-r * T) * ((K - F) * norm.cdf(-d) + vol * norm.pdf(d)))


def implied_normal_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: str = "call",
    tol: float = 1e-8,
) -> float:
    """Invert a Bachelier premium for normal implied volatility.

    Parameters
    ----------
    market_price : float
        Observed option premium in the same currency units as spot and strike.
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.
    tol : float, default=1e-08
        Numerical convergence tolerance.

    Returns
    -------
    float
        Computed implied normal volatility as a dimensionless decimal quantity.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    validate_option_type(option_type)

    def objective(sigma_n: float) -> float:
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        sigma_n : float
            Annualized normal volatility in price units per square-root year.

        Returns
        -------
        float
            Computed objective as a scalar in the units implied by the input values.
        """
        return _bachelier_price(S, K, T, r, sigma_n, q, option_type) - market_price

    low = objective(1e-6)
    upper = max(abs(S) * 10.0, abs(K) * 10.0, 1.0)
    high = objective(upper)
    if np.isnan(low) or np.isnan(high) or low * high > 0:
        return float(np.nan)
    return float(brentq(objective, 1e-6, upper, xtol=tol))
