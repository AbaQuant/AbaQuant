"""One-factor Gaussian-copula CDO tranche valuation.

Purpose
-------
The module evaluates conditional default probabilities and expected tranche survival under a one-factor Gaussian copula.

Conventions
-----------
Hazard rates and risk-free rates are decimal annual rates. Attachment and detachment are fractional portfolio-loss points. Recovery is a fraction in [0, 1].

References
----------
[ 1 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
[ 2 ] Jarrow, R. A., and S. M. Turnbull (1995), "Pricing Derivatives on Financial Securities Subject to Credit Risk".
"""

from __future__ import annotations

import numpy as np
from scipy.special import gammaln
from scipy.stats import norm


def gauss_hermite_normal(nodes: int) -> tuple[np.ndarray, np.ndarray]:
    """Transform Gauss--Hermite nodes to standard-normal factor nodes.

    Parameters
    ----------
    nodes : int
        Quadrature nodes or numerical nodes accepted by the routine.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
    """
    x_nodes, raw_weights = np.polynomial.hermite.hermgauss(nodes)
    factor_nodes = x_nodes * np.sqrt(2)
    weights = raw_weights / np.sqrt(np.pi)
    return factor_nodes, weights


def log_binomial_coefficient(n: int, k: int) -> float:
    """Compute the logarithm of a binomial coefficient.

    Parameters
    ----------
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    k : int
        Integer count used in the binomial coefficient.

    Returns
    -------
    float
        Computed log binomial coefficient as a scalar in the units implied by the input values.
    """
    return float(gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1))


def conditional_default_probability(
    t: float, hazard_rate: float, rho: float, factor: np.ndarray
) -> np.ndarray:
    """Compute conditional default probability given the common Gaussian factor.

    Parameters
    ----------
    t : float
        Time in years at which a credit-model quantity is evaluated.
    hazard_rate : float
        Constant default intensity in decimal annual units.
    rho : float
        Correlation parameter constrained to the interval [-1, 1].
    factor : np.ndarray
        Common-factor realization in the one-factor Gaussian copula.

    Returns
    -------
    np.ndarray
        Result of the conditional default probability calculation.
    """
    unconditional = 1.0 - np.exp(-hazard_rate * t)
    inv_q = norm.ppf(unconditional)
    arg = (inv_q - np.sqrt(rho) * factor) / np.sqrt(1.0 - rho)
    return norm.cdf(arg)


def binomial_probabilities_log(n: int, q: np.ndarray, k_max: int) -> np.ndarray:
    """Compute binomial probabilities in log-stable form.

    Parameters
    ----------
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    q : np.ndarray
        Continuous dividend or carry yield in decimal annual units.
    k_max : int
        Largest event-count index retained in the binomial probability vector.

    Returns
    -------
    numpy.ndarray
        Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
    """
    eps = 1e-300
    log_q = np.log(np.clip(q, eps, 1 - eps))
    log_1q = np.log(np.clip(1.0 - q, eps, 1 - eps))
    probs = np.zeros((k_max, len(q)))
    for k in range(k_max):
        log_p = log_binomial_coefficient(n, k) + k * log_q + (n - k) * log_1q
        probs[k] = np.exp(log_p)
    return probs


def expected_tranche_survival_given_factor(
    t: float,
    hazard_rate: float,
    rho: float,
    n: int,
    recovery_rate: float,
    attachment: float,
    detachment: float,
    factor_nodes: np.ndarray,
) -> np.ndarray:
    """Compute conditional expected tranche survival for one factor realization.

    Parameters
    ----------
    t : float
        Time in years at which a credit-model quantity is evaluated.
    hazard_rate : float
        Constant default intensity in decimal annual units.
    rho : float
        Correlation parameter constrained to the interval [-1, 1].
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    recovery_rate : float
        Recovery fraction expressed as a decimal in [0, 1].
    attachment : float
        Tranche attachment point as a fractional portfolio loss.
    detachment : float
        Tranche detachment point as a fractional portfolio loss.
    factor_nodes : np.ndarray
        Quadrature nodes representing the common Gaussian factor.

    Returns
    -------
    np.ndarray
        Result of the expected tranche survival given factor calculation.
    """
    q = conditional_default_probability(t, hazard_rate, rho, factor_nodes)
    lgd = 1.0 - recovery_rate
    n_l = attachment * n / lgd
    n_h = detachment * n / lgd
    m_l = int(np.ceil(n_l))
    m_h = int(np.ceil(n_h))
    probs = binomial_probabilities_log(n, q, m_h)
    expected = probs[:m_l].sum(axis=0)
    for k in range(m_l, m_h):
        fraction = np.clip((detachment - k * lgd / n) / (detachment - attachment), 0.0, 1.0)
        expected += probs[k] * fraction
    return expected


def value_tranche(
    hazard_rate: float,
    rho: float,
    n: int,
    recovery_rate: float,
    attachment: float,
    detachment: float,
    risk_free_rate: float,
    periods: list[float] | tuple[float, ...] | np.ndarray,
    factor_nodes: np.ndarray,
    weights: np.ndarray,
) -> dict[str, float | np.ndarray]:
    """Value the tranche cash-flow structure under the one-factor Gaussian-copula model.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    rho : float
        Correlation parameter constrained to the interval [-1, 1].
    n : int
        Number of discrete periods, assets, or observations as determined by the callable.
    recovery_rate : float
        Recovery fraction expressed as a decimal in [0, 1].
    attachment : float
        Tranche attachment point as a fractional portfolio loss.
    detachment : float
        Tranche detachment point as a fractional portfolio loss.
    risk_free_rate : float
        Annual risk-free rate in decimal units.
    periods : list[float] | tuple[float, ...] | np.ndarray
        Number of discrete compounding or payment periods.
    factor_nodes : np.ndarray
        Quadrature nodes representing the common Gaussian factor.
    weights : np.ndarray
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.

    Returns
    -------
    dict[str, float | np.ndarray]
        Named outputs of the value tranche calculation.
    """
    taus = [0.0, *periods]
    n_nodes = len(factor_nodes)
    expected_survival = np.zeros((len(taus), n_nodes))
    expected_survival[0] = 1.0

    for j, t in enumerate(periods):
        expected_survival[j + 1] = expected_tranche_survival_given_factor(
            t, hazard_rate, rho, n, recovery_rate, attachment, detachment, factor_nodes
        )

    fee_current = np.zeros(n_nodes)
    fee_accrued = np.zeros(n_nodes)
    protection = np.zeros(n_nodes)

    for j in range(1, len(taus)):
        tau_j = taus[j]
        tau_prev = taus[j - 1]
        delta = tau_j - tau_prev
        tau_mid = 0.5 * (tau_j + tau_prev)
        discount_j = np.exp(-risk_free_rate * tau_j)
        discount_mid = np.exp(-risk_free_rate * tau_mid)
        surv_j = expected_survival[j]
        surv_prev = expected_survival[j - 1]
        loss_increment = surv_prev - surv_j

        fee_current += delta * surv_j * discount_j
        fee_accrued += 0.5 * delta * loss_increment * discount_mid
        protection += loss_increment * discount_mid

    a = float((weights * fee_current).sum())
    b = float((weights * fee_accrued).sum())
    c = float((weights * protection).sum())
    spread = c / (a + b) if (a + b) > 1e-15 else np.nan
    terminal_survival = float((weights * expected_survival[-1]).sum())

    return {
        "A": a,
        "B": b,
        "C": c,
        "spread": float(spread),
        "spread_bps": float(spread * 10_000),
        "E_T": terminal_survival,
        "E_all": expected_survival,
    }


__all__ = [
    "binomial_probabilities_log",
    "conditional_default_probability",
    "expected_tranche_survival_given_factor",
    "gauss_hermite_normal",
    "log_binomial_coefficient",
    "value_tranche",
]
