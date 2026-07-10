"""Binomial-lattice option pricing.

Purpose
-------
This module constructs recombining Cox--Ross--Rubinstein-style trees for vanilla options and can include early exercise by backward induction.

Conventions
-----------
Maturity is in years, the number of steps is a positive integer, and rates, yields, and volatility are decimal annual quantities.

Scope and limitations
---------------------
Tree values are numerical approximations whose accuracy depends on the number of time steps.

References
----------
[ 1 ] Cox, J. C., S. A. Ross, and M. Rubinstein (1979), "Option Pricing: A Simplified Approach".
"""

from __future__ import annotations

import numpy as np


def binomial_tree(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    n: int,
    q: float = 0.0,
    option_type: str = "call",
    american: bool = False,
) -> tuple[float, tuple[np.ndarray, np.ndarray] | None]:
    """Price a vanilla option by backward induction on a binomial lattice.

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
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    option_type : str, default='call'
        Option type label, normally ``"call"`` or ``"put"``.
    american : bool, default=False
        Whether early exercise is allowed in the lattice valuation.

    Returns
    -------
    tuple[float, tuple[np.ndarray, np.ndarray] | None]
        Positional outputs produced by the binomial tree calculation.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    option_type = option_type.lower().strip()
    dt = T / n
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)

    if p < 0 or p > 1:
        return None, None

    S_tree = [np.zeros(i + 1) for i in range(n + 1)]
    V_tree = [np.zeros(i + 1) for i in range(n + 1)]

    for i in range(n + 1):
        for j in range(i + 1):
            S_tree[i][j] = S * (u ** (i - j)) * (d**j)

    for j in range(n + 1):
        if option_type == "call":
            V_tree[n][j] = max(0, S_tree[n][j] - K)
        else:
            V_tree[n][j] = max(0, K - S_tree[n][j])

    df = np.exp(-r * dt)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            val_hold = df * (p * V_tree[i + 1][j] + (1 - p) * V_tree[i + 1][j + 1])
            if american:
                if option_type == "call":
                    val_exercise = max(0, S_tree[i][j] - K)
                else:
                    val_exercise = max(0, K - S_tree[i][j])
                V_tree[i][j] = max(val_hold, val_exercise)
            else:
                V_tree[i][j] = val_hold

    return V_tree[0][0], (S_tree, V_tree)


def crr_binomial_tree(
    S: float,
    K: float,
    r: float,
    sigma: float,
    T: float,
    n: int,
    is_call: bool = True,
    american: bool = False,
    q: float = 0.0,
) -> tuple[float, np.ndarray | None, np.ndarray | None]:
    """Price a vanilla option with the Cox--Ross--Rubinstein lattice convention.

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
    T : float
        Time to maturity in years.
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    is_call : bool, default=True
        Whether the instrument is a call; false selects a put.
    american : bool, default=False
        Whether early exercise is allowed in the lattice valuation.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    tuple[float, np.ndarray | None, np.ndarray | None]
        Positional outputs produced by the crr binomial tree calculation.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    option_type = "call" if is_call else "put"
    price, trees = binomial_tree(S, K, T, r, sigma, n, q, option_type, american)
    if trees is None:
        return price, None, None
    stock_tree, value_tree = trees
    return price, stock_tree, value_tree


__all__ = ["binomial_tree", "crr_binomial_tree"]
