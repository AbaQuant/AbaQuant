"""Gaussian-copula simulation for credit portfolios.

Purpose
-------
The module maps latent Gaussian factors through rating-transition thresholds and simulates portfolio values.

Conventions
-----------
Correlation matrices must be square and compatible with the issuer order. The seed controls reproducibility.

References
----------
[ 1 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def thresholds_per_bond(rating_idx: int, trans_mat: np.ndarray) -> np.ndarray:
    """Convert one issuer rating-transition row into latent Gaussian thresholds.

    Parameters
    ----------
    rating_idx : int
        Index of the initial credit-rating state.
    trans_mat : np.ndarray
        Credit-rating transition matrix ordered by the package rating states.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
    """
    cum_p = np.cumsum(trans_mat[rating_idx])
    with np.errstate(all="ignore"):
        thresh = norm.ppf(np.clip(cum_p, 1e-15, 1.0 - 1e-15))
    thresh[-1] = np.inf
    return thresh


def gaussian_copula_simulation(
    bonds_data: list,
    trans_mat: np.ndarray,
    corr_mat: np.ndarray,
    n_sims: int = 50_000,
    seed: int = 42,
) -> np.ndarray:
    """Simulate destination ratings and portfolio values under a Gaussian copula.

    Parameters
    ----------
    bonds_data : list
        Issuer or bond input records in the package credit-risk schema.
    trans_mat : np.ndarray
        Credit-rating transition matrix ordered by the package rating states.
    corr_mat : np.ndarray
        Issuer correlation matrix ordered consistently with bonds_data.
    n_sims : int, default=50000
        Number of Gaussian-copula simulations.
    seed : int, default=42
        Optional pseudo-random seed for reproducible simulation.

    Returns
    -------
    np.ndarray
        Result of the gaussian copula simulation calculation.
    """
    rng = np.random.default_rng(seed)
    n = len(bonds_data)

    # Inverse-normal thresholds per bond, centralized to keep one
    # numerical convention shared by the simulation and public function.
    thresholds = [thresholds_per_bond(b["rating_idx"], trans_mat) for b in bonds_data]

    # Cholesky decomposition; use jitter when the matrix is not positive definite.
    C = corr_mat.copy().astype(float)
    np.fill_diagonal(C, 1.0)
    jitter = 0.0
    while True:
        try:
            L = np.linalg.cholesky(C + np.eye(n) * jitter)
            break
        except np.linalg.LinAlgError:
            jitter = jitter * 2 + 1e-8

    # Simular variables normales correlacionadas
    Z = rng.standard_normal((n_sims, n))
    X = Z @ L.T  # (n_sims, n)

    # Map latent values to ratings and calculate portfolio value.
    port_vals = np.zeros(n_sims)
    for b_idx, (b, thresh) in enumerate(zip(bonds_data, thresholds, strict=True)):
        n_vals = len(b["values"])
        r_sim = np.searchsorted(thresh, X[:, b_idx]).clip(0, n_vals - 1)
        port_vals += np.array(b["values"], dtype=float)[r_sim]

    return port_vals


__all__ = ["gaussian_copula_simulation", "thresholds_per_bond"]
