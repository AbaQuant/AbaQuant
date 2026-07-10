"""Vanilla option pricing and Greeks under Black--Scholes--Merton and Black--76.

Purpose
-------
The module prices European calls and puts, computes first- and selected second-order Greeks, and inverts a Black--Scholes--Merton premium for implied volatility.

Conventions
-----------
Spot, strike, and option value share currency units. Maturity is in years. Rates and continuous yields are continuously compounded decimal annual rates; volatility is annualized decimal volatility.

Scope and limitations
---------------------
The analytical formulas assume lognormal diffusion with constant model inputs and European exercise.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


def bsm_option_prices(
    model_type: str, S: float, K: float, T: float, r: float, sigma: float, extra: float = 0.0
) -> tuple[float, float, float, float]:
    """Compute Black--Scholes-style call and put prices and the intermediate d statistics.

    Parameters
    ----------
    model_type : str
        Legacy model selector controlling the Black--Scholes-style carry convention.
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
    extra : float, default=0.0
        Model-specific carry, income, cost, or yield adjustment.

    Returns
    -------
    tuple[float, float, float, float]
        ``(call, put, d1, d2)`` in positional order. Prices use the same currency units as the underlying and strike.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 0 or sigma <= 0:
        return 0.0, 0.0, 0.0, 0.0

    d1 = 0.0
    d2 = 0.0
    call = 0.0
    put = 0.0

    if model_type == "Simple":
        d1 = (np.log(S / K) + (r + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    elif model_type == "Income":
        S_adj = S - extra
        if S_adj <= 0:
            S_adj = 0.0001
        d1 = (np.log(S_adj / K) + (r + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call = S_adj * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put = K * np.exp(-r * T) * norm.cdf(-d2) - S_adj * norm.cdf(-d1)

    elif model_type in ("Yield", "Currency"):
        d1 = (np.log(S / K) + (r - extra + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call = S * np.exp(-extra * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-extra * T) * norm.cdf(-d1)

    elif model_type == "Futures":
        d1 = (np.log(S / K) + ((sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call = np.exp(-r * T) * (S * norm.cdf(d1) - K * norm.cdf(d2))
        put = np.exp(-r * T) * (K * norm.cdf(-d2) - S * norm.cdf(-d1))

    elif model_type == "Costs":
        S_adj = S + extra
        d1 = (np.log(S_adj / K) + (r + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call = S_adj * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put = K * np.exp(-r * T) * norm.cdf(-d2) - S_adj * norm.cdf(-d1)

    return call, put, d1, d2


def bsm_greeks(
    model_type: str, S: float, K: float, T: float, r: float, sigma: float, extra: float = 0.0
) -> tuple[float, float, float, float, float, float, float, float]:
    """Compute first-order Black--Scholes-style Greeks for calls and puts.

    Parameters
    ----------
    model_type : str
        Legacy model selector controlling the Black--Scholes-style carry convention.
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
    extra : float, default=0.0
        Model-specific carry, income, cost, or yield adjustment.

    Returns
    -------
    tuple[float, float, float, float, float, float, float, float]
        ``(delta_call, delta_put, gamma, vega, theta_call, theta_put, rho_call, rho_put)`` under the module scaling convention.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 0 or sigma <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    q_yield = 0.0
    S_adj = S

    if model_type == "Income":
        S_adj = S - extra
        if S_adj <= 0:
            S_adj = 0.0001
    elif model_type == "Costs":
        S_adj = S + extra
    elif model_type in ("Yield", "Currency"):
        q_yield = extra
    elif model_type == "Futures":
        q_yield = r

    d1 = (np.log(S_adj / K) + (r - q_yield + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    N_neg_d1 = norm.cdf(-d1)
    N_neg_d2 = norm.cdf(-d2)
    nd1 = norm.pdf(d1)

    delta_call = np.exp(-q_yield * T) * Nd1
    delta_put = np.exp(-q_yield * T) * (Nd1 - 1)
    gamma = np.exp(-q_yield * T) * nd1 / (S_adj * sigma * np.sqrt(T))
    vega = S_adj * np.exp(-q_yield * T) * nd1 * np.sqrt(T) / 100

    common_term = -(S_adj * np.exp(-q_yield * T) * nd1 * sigma) / (2 * np.sqrt(T))
    theta_call = (
        common_term - r * K * np.exp(-r * T) * Nd2 + q_yield * S_adj * np.exp(-q_yield * T) * Nd1
    ) / 365
    theta_put = (
        common_term
        + r * K * np.exp(-r * T) * N_neg_d2
        - q_yield * S_adj * np.exp(-q_yield * T) * N_neg_d1
    ) / 365

    rho_call = K * T * np.exp(-r * T) * Nd2 / 100
    rho_put = -K * T * np.exp(-r * T) * N_neg_d2 / 100

    return delta_call, delta_put, gamma, vega, theta_call, theta_put, rho_call, rho_put


def black_scholes(
    S: float, K: float, r: float, sigma: float, T: float, is_call: bool = True, q: float = 0.0
) -> float:
    """Price a European option under the Black--Scholes--Merton model.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    float
        Computed black scholes as a scalar in the units implied by the input values.
    """
    call, put, _, _ = bsm_option_prices("Yield", S, K, T, r, sigma, extra=q)
    return call if is_call else put


def vanilla_intrinsic_value(S: float, K: float, is_call: bool = True) -> float:
    """Return the immediate-exercise value of a vanilla option.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.

    Returns
    -------
    float
        ``max(S-K, 0)`` for a call and ``max(K-S, 0)`` for a put.
    """
    return float(max(S - K, 0.0) if is_call else max(K - S, 0.0))


def vanilla_extrinsic_value(option_price: float, S: float, K: float, is_call: bool = True) -> float:
    """Return option value in excess of immediate-exercise value.

    Parameters
    ----------
    option_price : float
        Model or market option premium in currency units.
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.

    Returns
    -------
    float
        Option premium minus intrinsic value. Negative values are preserved to
        expose inconsistent inputs rather than silently truncating the result.
    """
    return float(option_price - vanilla_intrinsic_value(S, K, is_call=is_call))


def black_76(F0: float, K: float, r: float, sigma: float, T: float, is_call: bool = True) -> float:
    """Price a European option on a forward or futures price under Black--76.

    Parameters
    ----------
    F0 : float
        Current futures or forward price, in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.

    Returns
    -------
    float
        Computed black 76 as a scalar in the units implied by the input values.
    """
    call, put, _, _ = bsm_option_prices("Futures", F0, K, T, r, sigma)
    return call if is_call else put


def bsm_d1_d2(
    S: float, K: float, r: float, q: float, sigma: float, T: float
) -> tuple[float, float]:
    """Compute the Black--Scholes--Merton d1 and d2 statistics.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.

    Returns
    -------
    tuple[float, float]
        ``(d1, d2)`` for the stated Black--Scholes--Merton inputs.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return float(d1), float(d1 - sigma * np.sqrt(T))


def calculate_greeks(
    S: float, K: float, r: float, sigma: float, T: float, is_call: bool = True, q: float = 0.0
) -> dict[str, float]:
    """Return the standard Black--Scholes--Merton Greeks for one option type.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    dc, dp, gamma, vega, tc, tp, rc, rp = bsm_greeks("Yield", S, K, T, r, sigma, extra=q)
    delta = dc if is_call else dp
    theta = tc if is_call else tp
    rho = rc if is_call else rp
    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega, "rho": rho}


def second_order_greeks(
    S: float, K: float, r: float, q: float, sigma: float, T: float, is_call: bool = True
) -> dict[str, float]:
    """Compute selected second-order Black--Scholes--Merton sensitivity measures.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    q : float
        Continuous dividend or carry yield in decimal annual units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    T : float
        Time to maturity in years.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 1e-6 or sigma <= 1e-6:
        return {"vanna": 0.0, "vomma": 0.0, "charm": 0.0, "speed": 0.0, "color_val": 0.0}
    d1, d2 = bsm_d1_d2(S, K, r, q, sigma, T)
    pdf_d1 = norm.pdf(d1)
    sqrt_t = np.sqrt(T)
    discount_yield = np.exp(-q * T)
    vanna = -discount_yield * pdf_d1 * d2 / sigma
    vega_raw = S * discount_yield * pdf_d1 * sqrt_t
    vomma = vega_raw * d1 * d2 / sigma * 0.01
    if is_call:
        charm = q * discount_yield * norm.cdf(d1) - discount_yield * pdf_d1 * (
            2 * (r - q) * T - d2 * sigma * sqrt_t
        ) / (2 * T * sigma * sqrt_t)
    else:
        charm = -q * discount_yield * norm.cdf(-d1) - discount_yield * pdf_d1 * (
            2 * (r - q) * T - d2 * sigma * sqrt_t
        ) / (2 * T * sigma * sqrt_t)
    charm = charm / 365.0
    gamma = discount_yield * pdf_d1 / (S * sigma * sqrt_t)
    speed = -gamma / S * (d1 / (sigma * sqrt_t) + 1)
    color = (
        -discount_yield
        * pdf_d1
        / (2 * S * T * sigma * sqrt_t)
        * (2 * q * T + 1 + (2 * (r - q) * T - d2 * sigma * sqrt_t) * d1 / (sigma * sqrt_t))
        / 365.0
    )
    return {
        "vanna": float(vanna),
        "vomma": float(vomma),
        "charm": float(charm),
        "speed": float(speed),
        "color_val": float(color),
    }


def implied_volatility_bsm(
    market_price: float,
    S: float,
    K: float,
    r: float,
    T: float,
    is_call: bool = True,
    q: float = 0.0,
    lower: float = 1e-6,
    upper: float = 10.0,
) -> float:
    """Solve for Black--Scholes--Merton implied volatility with Brent root finding.

    Parameters
    ----------
    market_price : float
        Observed option premium in the same currency units as spot and strike.
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    T : float
        Time to maturity in years.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    lower : float, default=1e-06
        Lower root-search or interval bound.
    upper : float, default=10.0
        Upper root-search or interval bound.

    Returns
    -------
    float
        Computed implied volatility bsm as a dimensionless decimal quantity.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """

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
        return black_scholes(S, K, r, sigma, T, is_call, q) - market_price

    return float(brentq(objective, lower, upper, xtol=1e-8, maxiter=200))


__all__ = [
    "black_76",
    "black_scholes",
    "bsm_d1_d2",
    "bsm_greeks",
    "bsm_option_prices",
    "calculate_greeks",
    "implied_volatility_bsm",
    "second_order_greeks",
    "vanilla_extrinsic_value",
    "vanilla_intrinsic_value",
]
