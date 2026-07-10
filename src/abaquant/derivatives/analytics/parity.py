"""Parity and deterministic option-pricing analytics.

Purpose
-------
The module checks put--call parity, decomposes an option premium into intrinsic and time value, and computes a continuous-carry forward price.

Conventions
-----------
Rates and yields are continuously compounded decimal annual rates; maturity is in years.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np


def parity_check(call, put, S, K, T, r, q=0.0):
    """Evaluate put--call parity and report the residual under continuous carry.

    Parameters
    ----------
    call : float or array-like
        Observed call premium in currency units for the parity calculation.
    put : float or array-like
        Observed put premium in currency units for the parity calculation.
    S : float or array-like
        Current underlying spot price in currency units.
    K : float or array-like
        Option strike price in the same currency units as the underlying.
    T : float or array-like
        Time to maturity in years.
    r : float or array-like
        Continuously compounded risk-free annual rate in decimal units.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    lhs = call - put
    rhs = S * np.exp(-q * T) - K * np.exp(-r * T)
    return {"lhs": lhs, "rhs": rhs, "residual": abs(lhs - rhs)}


def intrinsic_time_value(price, S, K, option_type="call"):
    """Decompose an option premium into intrinsic value and non-negative time value.

    Parameters
    ----------
    price : float or array-like
        Price or option premium in currency units.
    S : float or array-like
        Current underlying spot price in currency units.
    K : float or array-like
        Option strike price in the same currency units as the underlying.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    return {"intrinsic": intrinsic, "time_value": max(price - intrinsic, 0)}


def forward_price_continuous(spot: float, r: float, q: float, T: float) -> float:
    """Compute a continuously compounded cost-of-carry forward price.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price in currency units.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    T : float
        Time to maturity in years.

    Returns
    -------
    float
        Computed forward price continuous as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    return float(spot * np.exp((r - q) * T))
