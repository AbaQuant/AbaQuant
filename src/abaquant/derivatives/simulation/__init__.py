"""Path and return simulation routines.

Purpose
-------
The package exposes geometric-Brownian-motion, Merton jump-diffusion, and Levy-style simulation helpers.

Conventions
-----------
Times are years, rates and volatilities are decimal annual quantities, and seed arguments control pseudo-random reproducibility.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Merton, R. C. (1976), "Option Pricing When Underlying Stock Returns Are Discontinuous".
"""

from .gbm import simulate_gbm_paths
from .levy import simulate_vg_nig_returns
from .merton import simulate_merton_paths

__all__ = ["simulate_gbm_paths", "simulate_merton_paths", "simulate_vg_nig_returns"]
