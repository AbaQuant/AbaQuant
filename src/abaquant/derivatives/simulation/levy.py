"""Levy-style return simulation helpers.

Purpose
-------
The module generates Variance-Gamma and NIG-inspired return samples for comparative diagnostics.

Conventions
-----------
Model parameters use the implementation convention. T is in years and n_sim is the number of simulated observations.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Madan, D. B., P. P. Carr, and E. C. Chang (1998), "The Variance Gamma Process and Option Pricing".
[ 3 ] Barndorff-Nielsen, O. E. (1997), "Normal Inverse Gaussian Distributions and Stochastic Volatility Modelling".
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..analytics.distributions import distribution_moments


def simulate_vg_nig_returns(
    T: float,
    vg_sigma: float,
    vg_theta: float,
    vg_nu: float,
    nig_alpha: float,
    nig_beta: float,
    nig_delta: float,
    sigma_bsm: float,
    n_sim: int = 50_000,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Simulate return samples for the implemented Variance-Gamma and NIG parameterizations.

    Parameters
    ----------
    T : float
        Time to maturity in years.
    vg_sigma : float
        Variance-Gamma diffusion-scale parameter used by the simulation.
    vg_theta : float
        Variance-Gamma asymmetry parameter used by the simulation.
    vg_nu : float
        Variance-Gamma activity parameter used by the simulation.
    nig_alpha : float
        NIG alpha shape parameter under the implemented simulation parameterization.
    nig_beta : float
        NIG beta skew parameter under the implemented simulation parameterization.
    nig_delta : float
        NIG delta scale parameter under the implemented simulation parameterization.
    sigma_bsm : float
        Annualized Black--Scholes volatility used by the comparison simulation.
    n_sim : int, default=50000
        Number of simulated observations.
    seed : int | None, default=42
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if n_sim <= 0:
        raise ValueError("n_sim must be positive.")
    if vg_nu <= 0:
        raise ValueError("vg_nu must be positive.")
    if nig_alpha <= abs(nig_beta):
        raise ValueError("nig_alpha must be greater than abs(nig_beta).")

    rng = np.random.default_rng(seed)
    gamma_times = rng.gamma(T / vg_nu, vg_nu, n_sim)
    vg_returns = vg_theta * gamma_times + vg_sigma * np.sqrt(gamma_times) * rng.standard_normal(
        n_sim
    )

    ig_mean = nig_delta * T / np.sqrt(nig_alpha**2 - nig_beta**2)
    ig_shape = (nig_delta * T) ** 2
    v_ig = rng.standard_normal(n_sim) ** 2
    x_ig = (
        ig_mean
        + ig_mean**2 * v_ig / (2 * ig_shape)
        - ig_mean / (2 * ig_shape) * np.sqrt(4 * ig_mean * ig_shape * v_ig + ig_mean**2 * v_ig**2)
    )
    u_ig = rng.random(n_sim)
    ig_times = np.where(u_ig <= ig_mean / (ig_mean + x_ig), x_ig, ig_mean**2 / x_ig)
    nig_returns = nig_beta * ig_times + np.sqrt(ig_times) * rng.standard_normal(n_sim)

    gbm_returns = rng.normal(0.0, sigma_bsm * np.sqrt(T), n_sim)
    return {
        "vg_returns": vg_returns,
        "nig_returns": nig_returns,
        "gbm_returns": gbm_returns,
        "moments": {
            "VG": distribution_moments(vg_returns),
            "NIG": distribution_moments(nig_returns),
            "GBM": distribution_moments(gbm_returns),
        },
    }
