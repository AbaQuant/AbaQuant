"""Merton jump-diffusion path simulation.

Purpose
-------
The module simulates price paths with a diffusive component and compound-Poisson log jumps.

Conventions
-----------
Jump intensity is per year; all rates and volatilities are annualized decimal quantities; the seed controls reproducibility.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Merton, R. C. (1976), "Option Pricing When Underlying Stock Returns Are Discontinuous".
"""

from __future__ import annotations

import numpy as np

from ..models.merton import merton_jump_statistics


def simulate_merton_paths(
    S: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    lam: float = 1.0,
    mu_j: float = 0.0,
    sigma_j: float = 0.2,
    n_paths: int = 30,
    n_steps: int = 252,
    seed: int | None = 42,
) -> dict[str, np.ndarray]:
    """Simulate Merton jump-diffusion price paths.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    lam : float, default=1.0
        Jump intensity in expected jumps per year.
    mu_j : float, default=0.0
        Mean log jump size in the Merton jump-diffusion model.
    sigma_j : float, default=0.2
        Standard deviation of log jump size in decimal units.
    n_paths : int, default=30
        Number of Monte Carlo paths.
    n_steps : int, default=252
        Number of simulation or lattice time steps.
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
    if n_paths <= 0 or n_steps <= 0:
        raise ValueError("n_paths and n_steps must be positive.")
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    kappa_j = merton_jump_statistics(lam, mu_j, sigma_j, sigma)["kappa_j"]
    paths = np.empty((n_paths, n_steps + 1), dtype=float)
    paths[:, 0] = S

    for path_idx in range(n_paths):
        for step in range(1, n_steps + 1):
            diffusion = (r - q - lam * kappa_j - 0.5 * sigma**2) * dt + sigma * np.sqrt(
                dt
            ) * rng.standard_normal()
            n_jumps = rng.poisson(lam * dt)
            jump = rng.normal(mu_j, sigma_j, n_jumps).sum() if n_jumps > 0 else 0.0
            paths[path_idx, step] = paths[path_idx, step - 1] * np.exp(diffusion + jump)

    return {
        "times": np.linspace(0.0, T, n_steps + 1),
        "paths": paths,
        "terminal_prices": paths[:, -1].copy(),
    }
