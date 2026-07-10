"""Geometric-Brownian-motion path simulation.

Purpose
-------
The module simulates risk-neutral or drift-specified GBM paths on a uniform time grid.

Conventions
-----------
Spot values use currency units. Rates, yields, and volatility are decimal annual values. T is in years.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np


def simulate_gbm_paths(
    S: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    n_paths: int = 30,
    n_steps: int = 252,
    seed: int | None = 99,
) -> dict[str, np.ndarray]:
    """Simulate geometric-Brownian-motion price paths.

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
    n_paths : int, default=30
        Number of Monte Carlo paths.
    n_steps : int, default=252
        Number of simulation or lattice time steps.
    seed : int | None, default=99
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
    z = rng.standard_normal((n_paths, n_steps))
    increments = (r - q - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    paths = np.empty((n_paths, n_steps + 1), dtype=float)
    paths[:, 0] = S
    paths[:, 1:] = S * np.exp(np.cumsum(increments, axis=1))
    return {
        "times": np.linspace(0.0, T, n_steps + 1),
        "paths": paths,
        "terminal_prices": paths[:, -1].copy(),
    }
