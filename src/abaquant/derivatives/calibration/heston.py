"""Heston implied-volatility calibration.

Purpose
-------
The module fits Heston model parameters to a supplied cross-section of market implied volatilities by constrained numerical minimisation.

Conventions
-----------
Strikes and spot share units; maturity is in years; rates and dividends are decimal annual rates; implied volatilities are decimal annual quantities.

References
----------
[ 1 ] Heston, S. L. (1993), "A Closed-Form Solution for Options with Stochastic Volatility".
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from ..models.heston import HestonStochasticVolatilityModel
from ..numerics.implied_volatility import implied_volatility_black_scholes


def calibrate_heston(
    S,
    T,
    r,
    q,
    strikes,
    market_ivs,
    kappa0=2.0,
    theta0=0.04,
    xi0=0.3,
    rho0=-0.5,
    v00=0.04,
    method="L-BFGS-B",
    tol=1e-8,
    max_iter=300,
):
    """Calibrate Heston parameters to a cross-section of market implied volatilities.

    Parameters
    ----------
    S : float or array-like
        Current underlying spot price in currency units.
    T : float or array-like
        Time to maturity in years.
    r : float or array-like
        Continuously compounded risk-free annual rate in decimal units.
    q : float or array-like
        Continuous dividend or carry yield in decimal annual units.
    strikes : float or array-like
        Strike-price grid in the same currency units as the underlying or forward.
    market_ivs : float or array-like
        Observed market implied volatilities, expressed as annualized decimals.
    kappa0 : float, default=2.0
        Initial calibration guess for Heston kappa.
    theta0 : float, default=0.04
        Initial calibration guess for Heston theta.
    xi0 : float, default=0.3
        Initial calibration guess for Heston xi.
    rho0 : float, default=-0.5
        Initial calibration guess for Heston rho.
    v00 : float, default=0.04
        Initial calibration guess for Heston initial variance.
    method : str, default='L-BFGS-B'
        Optimization method name accepted by the underlying solver.
    tol : float, default=1e-08
        Numerical convergence tolerance.
    max_iter : int, default=300
        Maximum numerical-optimizer or root-finder iterations.

    Returns
    -------
    float
        Computed calibrate heston in the units implied by the documented inputs.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """

    def objective(params):
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        params : float or array-like
            Instrument-specific payoff parameters.

        Returns
        -------
        object
            Result of the objective workflow.
        """
        kappa, theta, xi, rho, v0 = params
        # Parameter constraints
        if (
            kappa <= 0
            or theta <= 0
            or xi <= 0
            or abs(rho) >= 1
            or v0 <= 0
            or 2 * kappa * theta <= xi**2 * 0.1
        ):  # soft Feller
            return 1e8
        total = 0.0
        for K, miv in zip(strikes, market_ivs, strict=True):
            if np.isnan(miv) or miv <= 0:
                continue
            h = HestonStochasticVolatilityModel(S, K, T, r, q, v0, kappa, theta, xi, rho)
            price = h.call_price()
            model_iv = implied_volatility_black_scholes(price, S, K, T, r, q, "call")
            if np.isnan(model_iv):
                total += 1.0
            else:
                total += (model_iv - miv) ** 2
        return total

    x0 = [kappa0, theta0, xi0, rho0, v00]
    bounds = [(0.01, 15.0), (0.001, 1.0), (0.01, 2.0), (-0.999, 0.999), (0.0001, 1.0)]

    res = minimize(
        objective, x0, method=method, bounds=bounds, options={"maxiter": max_iter, "ftol": tol}
    )

    kappa_c, theta_c, xi_c, rho_c, v0_c = res.x
    n_valid = sum(1 for iv in market_ivs if not np.isnan(iv) and iv > 0)
    rmse = np.sqrt(res.fun / max(n_valid, 1))

    return {
        "kappa": kappa_c,
        "theta": theta_c,
        "xi": xi_c,
        "rho": rho_c,
        "v0": v0_c,
        "rmse": rmse,
        "success": res.success,
        "message": str(res.message).upper(),
    }
