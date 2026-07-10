"""Shared constrained numerical solvers for portfolio weights.

Purpose
-------
The module contains feasibility normalization and SLSQP wrappers used by higher-level allocation routines.

Conventions
-----------
Weight vectors follow the package convention of summing to one. Bounds are decimal allocation limits.

Scope and limitations
---------------------
The historical failure behavior of the solver wrapper is documented at the callable level.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from scipy.optimize import minimize


def normalize_weights(weights: np.ndarray, min_weight: float, max_weight: float) -> np.ndarray:
    """Clip weights to bounds and normalize them to sum to one.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    min_weight : float
        Lower allocation bound applied to each asset weight.
    max_weight : float
        Upper allocation bound applied to each asset weight.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
    """
    clipped = np.clip(np.asarray(weights, dtype=float), min_weight, max_weight)
    total = clipped.sum()
    if total != 0:
        return clipped / total
    return clipped


def solve_slsqp_weights(
    objective: Callable[[np.ndarray], float],
    n_assets: int,
    min_weight: float,
    max_weight: float,
    bounds: Sequence[tuple[float, float]] | None = None,
    constraints: Sequence[dict] | tuple[dict, ...] | None = None,
    x0: np.ndarray | None = None,
) -> np.ndarray:
    """Solve a constrained portfolio-weight problem using SciPy SLSQP.

    Parameters
    ----------
    objective : Callable[[np.ndarray], float]
        Objective function passed to the numerical optimizer.
    n_assets : int
        Number of assets in the allocation problem.
    min_weight : float
        Lower allocation bound applied to each asset weight.
    max_weight : float
        Upper allocation bound applied to each asset weight.
    bounds : Sequence[tuple[float, float]] | None, default=None
        Allocation bounds in the format accepted by the underlying optimizer.
    constraints : Sequence[dict] | tuple[dict, ...] | None, default=None
        Constraint specification passed to the numerical optimizer.
    x0 : np.ndarray | None, default=None
        Optional initial point for numerical optimization.

    Returns
    -------
    np.ndarray
        Result of the solve slsqp weights calculation.
    """
    if n_assets == 1:
        return np.array([1.0])
    if x0 is None:
        x0 = np.repeat(1.0 / n_assets, n_assets)
    if bounds is None:
        bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    if constraints is None:
        constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12, "disp": False},
    )
    weights = result.x if result.success else x0
    return normalize_weights(weights, min_weight, max_weight)


__all__ = ["normalize_weights", "solve_slsqp_weights"]
