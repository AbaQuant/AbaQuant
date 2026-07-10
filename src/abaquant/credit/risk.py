"""Credit portfolio VaR, CVaR, and scaling metrics.

Purpose
-------
The module extracts tail measures from exact or simulated portfolio-value distributions and computes parametric normal approximations.

Conventions
-----------
The implementation documents whether values denote portfolio value or loss. Confidence levels are probabilities in [0, 1].

References
----------
[ 1 ] Rockafellar, R. T., and S. Uryasev (2000), "Optimization of Conditional Value-at-Risk".
[ 2 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .data import TRADING_DAYS


def var_cvar_from_distribution(
    sorted_dist: list,
    conf_levels: tuple[float, ...] = (0.90, 0.95, 0.99, 0.999),
    normalize: bool = True,
) -> dict:
    """Compute value at risk and conditional value at risk from an exact distribution.

    Parameters
    ----------
    sorted_dist : list
        Sorted exact portfolio-value distribution with corresponding probabilities.
    conf_levels : tuple[float, ...], default=(0.9, 0.95, 0.99, 0.999)
        Sequence of confidence probabilities for tail-risk outputs.
    normalize : bool, default=True
        Whether the probability masses are normalized to sum to one before tail
        metrics are computed.

    Returns
    -------
    dict
        Named outputs of the var cvar from distribution calculation.
    """
    vals = np.array([d[0] for d in sorted_dist], dtype=float)
    probs = np.array([d[1] for d in sorted_dist], dtype=float)
    sum_p = float(probs.sum())

    probs_n = (probs / sum_p if sum_p > 0 else probs) if normalize else probs

    ev = float(np.dot(vals, probs_n))
    var2 = float(np.dot((vals - ev) ** 2, probs_n))
    sigma = float(var2**0.5)
    cum = np.cumsum(probs_n)

    out = {}
    for conf in conf_levels:
        alpha = 1.0 - conf

        # searchsorted returns the first i for which cum[i] is at least alpha.
        # This is the correct lower quantile; do not subtract one.
        idx = int(np.searchsorted(cum, alpha, side="left"))
        idx = min(idx, len(vals) - 1)  # defensive upper-bound clamp
        q_val = float(vals[idx])

        var_v = max(ev - q_val, 0.0)

        # CVaR = E[V | V <= q], the expected value in the adverse tail.
        tail_mask = vals <= q_val
        tail_sum = probs_n[tail_mask].sum()
        if tail_sum > 1e-15:
            cvar_v = max(
                ev - float(np.dot(vals[tail_mask], probs_n[tail_mask]) / tail_sum),
                0.0,
            )
        else:
            cvar_v = var_v

        out[conf] = {
            "EV": ev,
            "sigma": sigma,
            "VaR": var_v,
            "CVaR": cvar_v,
            "q": q_val,
            "sum_probs": sum_p,
        }

    return out


def scale_var_cvar(
    results: dict, conf_levels: tuple[float, ...] = (0.90, 0.95, 0.99, 0.999)
) -> dict:
    """Scale documented risk results across confidence levels or horizons.

    Parameters
    ----------
    results : dict
        Existing risk-measure mapping to rescale or transform.
    conf_levels : tuple[float, ...], default=(0.9, 0.95, 0.99, 0.999)
        Sequence of confidence probabilities for tail-risk outputs.

    Returns
    -------
    dict
        Named outputs of the scale var cvar calculation.
    """
    _k1d = 1.0 / np.sqrt(TRADING_DAYS)  # / sqrt252
    _k10d = np.sqrt(10.0 / TRADING_DAYS)  # * sqrt(10/252)
    CAPITAL_MULTIPLIER = 3.0  # Basel II/III

    out = {}
    for conf in conf_levels:
        if conf not in results:
            continue
        r = results[conf]
        var_1y = r["VaR"]
        cvar_1y = r["CVaR"]

        var_1d = var_1y * _k1d
        cvar_1d = cvar_1y * _k1d
        var_10d = var_1y * _k10d
        cvar_10d = cvar_1y * _k10d
        capital = CAPITAL_MULTIPLIER * var_10d

        out[conf] = {
            "EV": r["EV"],
            "sigma": r["sigma"],
            "VaR_1y": var_1y,
            "CVaR_1y": cvar_1y,
            "VaR_1d": var_1d,
            "CVaR_1d": cvar_1d,
            "VaR_10d": var_10d,
            "CVaR_10d": cvar_10d,
            "Capital": capital,
            # optional fields
            "q": r.get("q"),
            "sum_probs": r.get("sum_probs"),
        }
    return out


def var_cvar_from_simulations(
    sim_vals: np.ndarray, conf_levels: tuple[float, ...] = (0.90, 0.95, 0.99, 0.999)
) -> dict:
    """Compute value at risk and conditional value at risk from simulated values.

    Parameters
    ----------
    sim_vals : np.ndarray
        Simulated portfolio-value samples.
    conf_levels : tuple[float, ...], default=(0.9, 0.95, 0.99, 0.999)
        Sequence of confidence probabilities for tail-risk outputs.

    Returns
    -------
    dict
        Named outputs of the var cvar from simulations calculation.
    """
    ev = float(np.mean(sim_vals))
    sigma = float(np.std(sim_vals))
    out = {}
    for conf in conf_levels:
        q = float(np.quantile(sim_vals, 1.0 - conf))
        var = max(ev - q, 0.0)
        tail = sim_vals[sim_vals <= q]
        cvar = max(ev - float(tail.mean()), 0.0) if len(tail) > 0 else var
        out[conf] = {"EV": ev, "sigma": sigma, "VaR": var, "CVaR": cvar, "q": q}
    return out


def var_cvar_parametric(
    ev: float, sigma: float, conf_levels: tuple[float, ...] = (0.90, 0.95, 0.99, 0.999)
) -> dict:
    """Compute normal-approximation value at risk and conditional value at risk.

    Parameters
    ----------
    ev : float
        Expected portfolio value used by the parametric credit-risk approximation.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    conf_levels : tuple[float, ...], default=(0.9, 0.95, 0.99, 0.999)
        Sequence of confidence probabilities for tail-risk outputs.

    Returns
    -------
    dict
        Named outputs of the var cvar parametric calculation.
    """
    out = {}
    for conf in conf_levels:
        z = float(norm.ppf(conf))
        var = max(z * sigma, 0.0)
        cvar = max(float(norm.pdf(z)) / (1.0 - conf) * sigma, var)
        out[conf] = {
            "EV": ev,
            "sigma": sigma,
            "VaR": var,
            "CVaR": cvar,
        }
    return out


__all__ = [
    "scale_var_cvar",
    "var_cvar_from_distribution",
    "var_cvar_from_simulations",
    "var_cvar_parametric",
]
