"""Carr--Madan fast-Fourier-transform option pricing.

Purpose
-------
The module evaluates damped Fourier transforms of characteristic functions to obtain European option prices.

Conventions
-----------
Characteristic functions must follow the implementation convention. Grid size is normally a power of two; eta controls Fourier-grid spacing.

References
----------
[ 1 ] Carr, P., and D. B. Madan (1999), "Option Valuation Using the Fast Fourier Transform".
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.interpolate import interp1d

from ..validation import validate_option_type


def carr_madan_call_price(
    characteristic_function: Callable[[complex | np.ndarray], complex | np.ndarray],
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    dividend_yield: float = 0.0,
    *,
    alpha: float = 1.5,
    n_grid: int = 4096,
    eta: float = 0.25,
) -> float:
    """Compute a European call price from a characteristic function using Carr--Madan FFT.

    Parameters
    ----------
    characteristic_function : Callable[[complex | np.ndarray], complex | np.ndarray]
        Callable returning the model characteristic function at a Fourier argument.
    spot : float
        Current underlying or asset spot price in currency units.
    strike : float
        Option strike price in the same currency units as the underlying.
    maturity : float
        Time to option expiry in years.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    dividend_yield : float, default=0.0
        Continuous dividend yield in decimal annual units.
    alpha : float, default=1.5
        Model-specific alpha parameter; consult the module convention.
    n_grid : int, default=4096
        Number of points in the Fourier grid, typically a power of two.
    eta : float, default=0.25
        Fourier-grid spacing in the Carr--Madan implementation.

    Returns
    -------
    float
        Computed carr madan call price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    lam = 2 * np.pi / (n_grid * eta)
    b = np.pi / eta
    k_grid = -b + lam * np.arange(n_grid)
    v_grid = eta * np.arange(n_grid)
    cf_vals = characteristic_function(v_grid - (alpha + 1) * 1j)
    denom = alpha**2 + alpha - v_grid**2 + 1j * (2 * alpha + 1) * v_grid
    psi_vals = np.exp(-rate * maturity) * cf_vals / denom
    simpson = (eta / 3) * np.array([3 + (-1) ** j - (1 if j == 0 else 0) for j in range(n_grid)])
    fft_input = np.exp(1j * b * v_grid) * psi_vals * simpson
    prices_raw = np.real(np.fft.fft(fft_input)) * np.exp(-alpha * k_grid) / np.pi
    interpolator = interp1d(k_grid, prices_raw, kind="cubic", fill_value="extrapolate")
    call = float(interpolator(np.log(strike)))
    intrinsic_floor = max(
        spot * np.exp(-dividend_yield * maturity) - strike * np.exp(-rate * maturity), 0.0
    )
    return max(call, intrinsic_floor)


def carr_madan_option_price(
    characteristic_function: Callable[[complex | np.ndarray], complex | np.ndarray],
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    dividend_yield: float = 0.0,
    option_type: str = "call",
    *,
    alpha: float = 1.5,
    n_grid: int = 4096,
    eta: float = 0.25,
) -> float:
    """Compute a European call or put price through the Carr--Madan Fourier routine.

    Parameters
    ----------
    characteristic_function : Callable[[complex | np.ndarray], complex | np.ndarray]
        Callable returning the model characteristic function at a Fourier argument.
    spot : float
        Current underlying or asset spot price in currency units.
    strike : float
        Option strike price in the same currency units as the underlying.
    maturity : float
        Time to option expiry in years.
    rate : float
        Interest rate in decimal units under the stated compounding convention.
    dividend_yield : float, default=0.0
        Continuous dividend yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.
    alpha : float, default=1.5
        Model-specific alpha parameter; consult the module convention.
    n_grid : int, default=4096
        Number of points in the Fourier grid, typically a power of two.
    eta : float, default=0.25
        Fourier-grid spacing in the Carr--Madan implementation.

    Returns
    -------
    float
        Computed carr madan option price as a scalar in the units implied by the input values.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    validate_option_type(option_type)
    call = carr_madan_call_price(
        characteristic_function,
        spot,
        strike,
        maturity,
        rate,
        dividend_yield,
        alpha=alpha,
        n_grid=n_grid,
        eta=eta,
    )
    if option_type == "call":
        return call
    return call - spot * np.exp(-dividend_yield * maturity) + strike * np.exp(-rate * maturity)
