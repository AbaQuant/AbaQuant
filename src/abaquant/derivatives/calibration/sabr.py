"""SABR smile calibration.

Purpose
-------
The module fits SABR alpha, rho, and nu parameters with beta held fixed to a supplied implied-volatility smile.

Conventions
-----------
Forward and strikes share units; maturity is in years; all volatilities are decimal annual quantities.

References
----------
[ 1 ] Hagan, P. S., D. Kumar, A. S. Lesniewski, and D. E. Woodward (2002), "Managing Smile Risk".
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from ..models.sabr import SABRVolatilityModel


def calibrate_sabr(
    forward: float,
    maturity: float,
    strikes: np.ndarray,
    market_ivs: np.ndarray,
    *,
    beta: float,
    initial_alpha: float = 0.2,
    initial_rho: float = -0.3,
    initial_nu: float = 0.4,
    tol: float = 1e-8,
    max_iter: int = 500,
) -> dict[str, float]:
    """Calibrate SABR smile parameters with beta fixed.

    Parameters
    ----------
    forward : float
        Forward price or rate in the same units as the relevant strike.
    maturity : float
        Time to option expiry in years.
    strikes : np.ndarray
        Strike-price grid in the same currency units as the underlying or forward.
    market_ivs : np.ndarray
        Observed market implied volatilities, expressed as annualized decimals.
    beta : float
        Model-specific beta parameter; consult the module convention.
    initial_alpha : float, default=0.2
        Initial calibration guess for SABR alpha.
    initial_rho : float, default=-0.3
        Initial calibration guess for SABR rho.
    initial_nu : float, default=0.4
        Initial calibration guess for SABR nu.
    tol : float, default=1e-08
        Numerical convergence tolerance.
    max_iter : int, default=500
        Maximum numerical-optimizer or root-finder iterations.

    Returns
    -------
    dict[str, float]
        Named outputs of the calibrate sabr calculation.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """

    def objective(params: np.ndarray) -> float:
        """Compute the result defined by ``objective`` under this module's documented convention.

        Parameters
        ----------
        params : np.ndarray
            Instrument-specific payoff parameters.

        Returns
        -------
        float
            Computed objective as a scalar in the units implied by the input values.
        """
        alpha, rho, nu = params
        if alpha <= 0 or nu <= 0 or abs(rho) >= 1:
            return 1e6
        total = 0.0
        for strike, market_iv in zip(strikes, market_ivs, strict=True):
            if np.isnan(market_iv):
                continue
            model_iv = SABRVolatilityModel(
                forward, strike, maturity, alpha, beta, rho, nu
            ).implied_vol()
            total += (model_iv - market_iv) ** 2
        return float(total)

    res = minimize(
        objective,
        [initial_alpha, initial_rho, initial_nu],
        method="L-BFGS-B",
        bounds=[(1e-4, 5.0), (-0.999, 0.999), (1e-4, 5.0)],
        options={"ftol": tol, "maxiter": max_iter},
    )
    alpha_cal, rho_cal, nu_cal = res.x
    rmse = np.sqrt(res.fun / max(len(strikes), 1))
    return {
        "alpha": float(alpha_cal),
        "beta": float(beta),
        "rho": float(rho_cal),
        "nu": float(nu_cal),
        "rmse": float(rmse),
        "success": bool(res.success),
    }
