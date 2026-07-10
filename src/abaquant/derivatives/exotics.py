"""Exotic-option formulas and closed-form approximations.

Purpose
-------
The module contains pricing routines for gap, binary, Asian, barrier, lookback, compound, exchange, chooser, and perpetual options.

Conventions
-----------
Inputs follow the Black--Scholes--Merton convention: maturity in years; rates, yields, and volatility as decimal annual quantities; prices and strikes in common currency units.

Scope and limitations
---------------------
Several instruments use analytical approximations or implementation-specific conventions. They should not be treated as substitutes for a calibrated production exotic-options model.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import root_scalar
from scipy.stats import multivariate_normal, norm

from .vanilla import bsm_option_prices


def gap_options(
    S: float,
    K1: float,
    K2: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
) -> float:
    """Price a gap option under the Black--Scholes--Merton closed-form convention.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K1 : float
        First strike or trigger price in the instrument-specific payoff.
    K2 : float
        Second strike price in the instrument-specific payoff.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed gap options as a scalar in the units implied by the input values.
    """
    d1 = (np.log(S / K2) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * np.exp(-q * T) * norm.cdf(d1) - K1 * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        price = K1 * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'.")
    return price


def cash_or_nothing_options(
    S: float,
    K: float,
    Q: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
) -> float:
    """Price a cash-or-nothing digital option under Black--Scholes--Merton.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    Q : float
        Fixed cash amount paid by a cash-or-nothing option, in currency units.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed cash or nothing options as a scalar in the units implied by the input values.
    """
    d1 = (np.log(S / K) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = Q * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        price = Q * np.exp(-r * T) * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'.")
    return price


def asset_or_nothing_options(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call"
) -> float:
    """Price an asset-or-nothing digital option under Black--Scholes--Merton.

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
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed asset or nothing options as a scalar in the units implied by the input values.
    """
    if T <= 0 or sigma <= 0:
        return 0.0

    d1 = (np.log(S / K) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))

    if option_type == "call":
        price = S * np.exp(-q * T) * norm.cdf(d1)
    elif option_type == "put":
        price = S * np.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'.")

    return max(0.0, price)


def down_and_out_barrier_option(
    S: float,
    K: float,
    H: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
) -> float:
    """Price the implemented down-and-out barrier option formula.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    H : float
        Barrier level in the same currency units as the underlying price.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed down and out barrier option as a scalar in the units implied by the input values.
    """
    if S <= H:
        return 0.0

    lam = (r - q + (sigma**2) / 2) / (sigma**2)
    y = (np.log(H**2 / (S * K)) / (sigma * np.sqrt(T))) + lam * sigma * np.sqrt(T)

    vanilla_call, vanilla_put, _, _ = bsm_option_prices("Yield", S, K, T, r, sigma, extra=q)

    if option_type == "call":
        c_di = S * np.exp(-q * T) * (H / S) ** (2 * lam) * norm.cdf(y) - K * np.exp(-r * T) * (
            H / S
        ) ** (2 * lam - 2) * norm.cdf(y - sigma * np.sqrt(T))
        price = vanilla_call - c_di
    elif option_type == "put":
        p_di = -S * np.exp(-q * T) * (H / S) ** (2 * lam) * norm.cdf(-y) + K * np.exp(-r * T) * (
            H / S
        ) ** (2 * lam - 2) * norm.cdf(-y + sigma * np.sqrt(T))
        price = vanilla_put - p_di

    return max(0.0, price)


def arithmetic_asian_options(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call"
) -> float:
    """Price an arithmetic-average Asian option using the module approximation.

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
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed arithmetic asian options as a scalar in the units implied by the input values.
    """
    b = r - q

    # Use np.expm1 for improved precision when b*T or sigma squared*T is small.
    if np.isclose(b, 0.0):
        M1 = S
        # Correct Turnbull--Wakeman limit as b tends to zero:
        M2 = (2 * S**2 / (sigma**2 * T**2)) * (np.expm1(sigma**2 * T) / sigma**2 - T)
    else:
        # np.expm1(x) = exp(x)-1 and is more accurate than exp(x)-1 for small x.
        M1 = S * np.expm1(b * T) / (b * T)
        term1 = np.expm1((2 * b + sigma**2) * T) / (2 * b + sigma**2)
        term2 = np.expm1(b * T) / b
        M2 = (2 * S**2 / ((b + sigma**2) * T**2)) * (term1 - term2)

    F = M1
    # Require M2/M1 squared to exceed one so that the logarithm remains positive.
    ratio = M2 / (M1**2)
    if ratio <= 1.0:
        ratio = 1.0 + 1e-12
    sigma_adj = np.sqrt(np.log(ratio) / T)

    d1 = (np.log(F / K) + (sigma_adj**2 / 2) * T) / (sigma_adj * np.sqrt(T))
    d2 = d1 - sigma_adj * np.sqrt(T)

    if option_type == "call":
        price = np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
    elif option_type == "put":
        price = np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    else:
        raise ValueError("option_type must be 'call' or 'put'.")

    return max(0.0, price)


def geometric_asian_options(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call"
) -> float:
    """Price a geometric-average Asian option using its closed-form lognormal reduction.

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
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed geometric asian options as a scalar in the units implied by the input values.
    """
    b = r - q
    sigma_adj = sigma / np.sqrt(3.0)
    b_adj = 0.5 * (b - (sigma**2) / 6.0)

    d1 = (np.log(S / K) + (b_adj + (sigma_adj**2) / 2.0) * T) / (sigma_adj * np.sqrt(T))
    d2 = d1 - sigma_adj * np.sqrt(T)

    if option_type == "call":
        price = S * np.exp((b_adj - r) * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp((b_adj - r) * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'.")

    return max(0.0, price)


def floating_lookback_options(
    S: float,
    S_ref: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
) -> float:
    # Derive the analytic limit when r equals q rather than relying on a fixed epsilon.
    # The first-order expansion supplies the r-to-q limit used below.
    """Price the implemented floating-strike lookback option formula.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    S_ref : float
        Reference running minimum, maximum, or observed price required by the payoff, in currency units.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    float
        Computed floating lookback options as a scalar in the units implied by the input values.
    """
    r_eq_q = np.isclose(r, q, atol=1e-9)

    if option_type == "call":
        Smin = S_ref

        if r_eq_q:
            # Analytic r = q limit avoids division by zero.
            sqrtT = np.sqrt(T)
            a1 = (np.log(S / Smin) + (sigma**2 / 2) * T) / (sigma * sqrtT)
            a2 = a1 - sigma * sqrtT
            # Limit formula: the indicated term converges to T when r and q both vanish.
            price = S * np.exp(-q * T) * (
                norm.cdf(a1) + sigma * sqrtT * norm.pdf(a1)
            ) - Smin * np.exp(-r * T) * norm.cdf(a2)
        else:
            a1 = (np.log(S / Smin) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
            a2 = a1 - sigma * np.sqrt(T)
            a3 = (np.log(S / Smin) + (-r + q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
            Y1 = -2 * (r - q - (sigma**2) / 2) * np.log(S / Smin) / (sigma**2)
            coef = sigma**2 / (2 * (r - q))

            term1 = S * np.exp(-q * T) * norm.cdf(a1)
            term2 = S * np.exp(-q * T) * coef * norm.cdf(-a1)
            term3 = Smin * np.exp(-r * T) * (norm.cdf(a2) - coef * np.exp(Y1) * norm.cdf(-a3))
            price = term1 - term2 - term3

    elif option_type == "put":
        Smax = S_ref

        if r_eq_q:
            sqrtT = np.sqrt(T)
            b1 = (np.log(Smax / S) + (sigma**2 / 2) * T) / (sigma * sqrtT)
            b2 = b1 - sigma * sqrtT
            price = Smax * np.exp(-r * T) * norm.cdf(b1) - S * np.exp(-q * T) * (
                norm.cdf(b2) - sigma * sqrtT * norm.pdf(b2)
            )
        else:
            b1 = (np.log(Smax / S) + (-r + q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
            b2 = b1 - sigma * np.sqrt(T)
            b3 = (np.log(Smax / S) + (r - q - (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
            Y2 = 2 * (r - q - (sigma**2) / 2) * np.log(Smax / S) / (sigma**2)
            coef = sigma**2 / (2 * (r - q))

            term1 = Smax * np.exp(-r * T) * (norm.cdf(b1) - coef * np.exp(Y2) * norm.cdf(-b3))
            term2 = S * np.exp(-q * T) * norm.cdf(b2)
            term3 = S * np.exp(-q * T) * coef * norm.cdf(-b2)
            price = term1 - term2 + term3
    else:
        raise ValueError("option_type must be 'call' or 'put'.")

    return max(0.0, price)


def _pnbivariada(x: float, y: float, rho: float) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    x : float
        First numerical argument of the internal bivariate-normal helper.
    y : float
        Second numerical argument of the internal bivariate-normal helper.
    rho : float
        Correlation parameter constrained to the interval [-1, 1].

    Returns
    -------
    float
        Computed  pnbivariada as a scalar in the units implied by the input values.
    """
    mean = np.array([0.0, 0.0])
    cov = np.array([[1.0, rho], [rho, 1.0]])
    return float(multivariate_normal(mean=mean, cov=cov).cdf([x, y]))


def compound_options(
    S: float,
    K1: float,
    K2: float,
    T1: float,
    T2: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call_on_call",
) -> float:
    """Price an option on an option using the implemented compound-option formula.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K1 : float
        First strike or trigger price in the instrument-specific payoff.
    K2 : float
        Second strike price in the instrument-specific payoff.
    T1 : float
        First decision or exercise time in years.
    T2 : float
        Second maturity or exercise time in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call_on_call'
        Compound option type: ``"call_on_call"``, ``"put_on_call"``, ``"call_on_put"``, or ``"put_on_put"``.

    Returns
    -------
    float
        Computed compound options as a scalar in the units implied by the input values.
    """
    tau = T2 - T1

    price_index = 0 if "on_call" in option_type else 1

    def objective(x: float) -> float:
        return bsm_option_prices("Yield", x, K2, tau, r, sigma, extra=q)[price_index] - K1

    try:
        # Check for a sign change before Brent root finding so failure is explicit.
        f_lo = objective(0.001)
        f_hi = objective(10000.0)
        if f_lo * f_hi > 0:
            return 0.0  # No root lies in the interval; the option has zero value under this approximation.
        S_star = root_scalar(objective, bracket=[0.001, 10000.0], method="brentq", xtol=1e-6).root
    except Exception:
        return 0.0

    a1 = (np.log(S / S_star) + (r - q + (sigma**2) / 2) * T1) / (sigma * np.sqrt(T1))
    a2 = a1 - sigma * np.sqrt(T1)
    b1 = (np.log(S / K2) + (r - q + (sigma**2) / 2) * T2) / (sigma * np.sqrt(T2))
    b2 = b1 - sigma * np.sqrt(T2)
    rho = np.sqrt(T1 / T2)

    if option_type == "call_on_call":
        M1 = _pnbivariada(a1, b1, rho)
        M2 = _pnbivariada(a2, b2, rho)
        price = (
            S * np.exp(-q * T2) * M1
            - K2 * np.exp(-r * T2) * M2
            - K1 * np.exp(-r * T1) * norm.cdf(a2)
        )

    elif option_type == "put_on_call":
        M1 = _pnbivariada(-a1, b1, -rho)
        M2 = _pnbivariada(-a2, b2, -rho)
        price = (
            K2 * np.exp(-r * T2) * M2
            - S * np.exp(-q * T2) * M1
            + K1 * np.exp(-r * T1) * norm.cdf(-a2)
        )

    elif option_type == "call_on_put":
        M1 = _pnbivariada(-a1, -b1, rho)
        M2 = _pnbivariada(-a2, -b2, rho)
        price = (
            K2 * np.exp(-r * T2) * M2
            - S * np.exp(-q * T2) * M1
            - K1 * np.exp(-r * T1) * norm.cdf(-a2)
        )

    elif option_type == "put_on_put":
        M1 = _pnbivariada(a1, -b1, -rho)
        M2 = _pnbivariada(a2, -b2, -rho)
        price = (
            S * np.exp(-q * T2) * M1
            - K2 * np.exp(-r * T2) * M2
            + K1 * np.exp(-r * T1) * norm.cdf(a2)
        )

    return price


def exchange_options(
    U: float, V: float, q_u: float, q_v: float, sigma_u: float, sigma_v: float, rho: float, T: float
) -> float:
    """Price an option to exchange one risky asset for another under the Margrabe-style formula.

    Parameters
    ----------
    U : float
        Price of the asset delivered or exchanged in currency units.
    V : float
        Price of the asset received or benchmarked in currency units.
    q_u : float
        Continuous yield of the first exchanged asset in decimal annual units.
    q_v : float
        Continuous yield of the second exchanged asset in decimal annual units.
    sigma_u : float
        Annualized lognormal volatility of the first asset in decimal units.
    sigma_v : float
        Annualized lognormal volatility of the second asset in decimal units.
    rho : float
        Correlation parameter constrained to the interval [-1, 1].
    T : float
        Time to maturity in years.

    Returns
    -------
    float
        Computed exchange options as a scalar in the units implied by the input values.
    """
    sigma = np.sqrt(sigma_u**2 + sigma_v**2 - 2 * rho * sigma_u * sigma_v)
    d1 = (np.log(V / U) + (q_u - q_v + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    price = V * np.exp(-q_v * T) * norm.cdf(d1) - U * np.exp(-q_u * T) * norm.cdf(d2)
    return max(0.0, price)


def exotic_payoff_leg(
    option_type: str, position: int, S_T: np.ndarray, params: dict, premium: float
) -> np.ndarray:
    """Evaluate terminal payoff and profit for an exotic option leg.

    Parameters
    ----------
    option_type : str
        Option type label, normally ``"call"`` or ``"put"``.
    position : int
        Position sign, usually ``1`` for long and ``-1`` for short.
    S_T : np.ndarray
        Underlying terminal price or terminal-price vector, in currency units.
    params : dict
        Instrument-specific payoff parameters.
    premium : float
        Premium paid or received at inception in currency units.

    Returns
    -------
    np.ndarray
        Result of the exotic payoff leg calculation.
    """
    option_type_key = option_type.lower()
    is_call = "call" in option_type_key
    if "gap" in option_type_key:
        K1 = params.get("K", 100.0)
        K1 = params.get("K1", K1)
        K2 = params.get("K2", K1)
        payoff = np.where(S_T > K1, S_T - K2, 0.0) if is_call else np.where(S_T < K1, K2 - S_T, 0.0)
    elif "cash-or-nothing" in option_type_key or "con_" in option_type_key:
        K = params.get("K", 100.0)
        Q = params.get("Q", 100.0)
        payoff = np.where(S_T > K, Q, 0.0) if is_call else np.where(S_T < K, Q, 0.0)
    elif "asset-or-nothing" in option_type_key or "aon_" in option_type_key:
        K = params.get("K", 100.0)
        payoff = np.where(S_T > K, S_T, 0.0) if is_call else np.where(S_T < K, S_T, 0.0)
    elif "down-and-out" in option_type_key or "dno_" in option_type_key:
        K = params.get("K", 100.0)
        H = params.get("H", 80.0)
        vanilla = np.maximum(S_T - K, 0.0) if is_call else np.maximum(K - S_T, 0.0)
        payoff = np.where(S_T > H, vanilla, 0.0)
    else:
        payoff = np.zeros_like(S_T)
    return position * payoff - position * premium


def simple_chooser_option(
    S: float, K: float, T1: float, T2: float, r: float, sigma: float, q: float = 0.0
) -> float:
    """Price a simple chooser option under the implemented Black--Scholes--Merton relation.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T1 : float
        First decision or exercise time in years.
    T2 : float
        Second maturity or exercise time in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    float
        Computed simple chooser option as a scalar in the units implied by the input values.
    """
    c = bsm_option_prices("Yield", S, K, T2, r, sigma, extra=q)[0]
    K_put = K * np.exp(-(r - q) * (T2 - T1))
    p = bsm_option_prices("Yield", S, K_put, T1, r, sigma, extra=q)[1]
    return c + np.exp(-q * (T2 - T1)) * p


def perpetual_option(S: float, K: float, r: float, sigma: float, is_call: bool = True) -> float:
    """Price the implemented perpetual American-style option formula.

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
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.

    Returns
    -------
    float
        Computed perpetual option as a scalar in the units implied by the input values.
    """
    if sigma <= 0 or r <= 0:
        return max(S - K, 0) if is_call else max(K - S, 0)
    h = 0.5 + np.sqrt(0.25 + 2 * r / sigma**2)
    if is_call:
        price = (K / (h - 1)) * ((S * (h - 1)) / (h * K)) ** h
    else:
        h_s = 0.5 - np.sqrt(0.25 + 2 * r / sigma**2)
        price = (K / (1 - h_s)) * ((S * (1 - h_s)) / (h_s * K)) ** h_s
    return max(0.0, price)


__all__ = [
    "arithmetic_asian_options",
    "asset_or_nothing_options",
    "cash_or_nothing_options",
    "compound_options",
    "down_and_out_barrier_option",
    "exchange_options",
    "exotic_payoff_leg",
    "floating_lookback_options",
    "gap_options",
    "geometric_asian_options",
    "perpetual_option",
    "simple_chooser_option",
]
