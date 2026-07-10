"""Credit-default-swap valuation primitives.

Purpose
-------
The module constructs probability, premium-leg, contingent-leg, and accrued-premium tables and computes a fair CDS spread.

Conventions
-----------
Hazard and discount rates are decimal annual rates; maturity is in years; recovery is a fraction in [0, 1].

References
----------
[ 1 ] Jarrow, R. A., and S. M. Turnbull (1995), "Pricing Derivatives on Financial Securities Subject to Credit Risk".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def cds_probability_table(hazard_rate: float, maturity: int) -> pd.DataFrame:
    """Build the default and survival probability table used for CDS valuation.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    maturity : int
        Time to option expiry in years.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    rows = []
    for t in range(1, maturity + 1):
        survival_t = float(np.exp(-hazard_rate * t))
        survival_prev = float(np.exp(-hazard_rate * (t - 1)))
        rows.append(
            {
                "time_years": t,
                "survival_probability": survival_t,
                "cumulative_default_probability": 1.0 - survival_t,
                "marginal_default_probability": survival_prev - survival_t,
            }
        )
    return pd.DataFrame(rows)


def cds_premium_leg_table(hazard_rate: float, discount_rate: float, maturity: int) -> pd.DataFrame:
    """Build the discounted premium-leg cash-flow table for a CDS.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    discount_rate : float
        Annual discount rate in decimal units.
    maturity : int
        Time to option expiry in years.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    rows = []
    for t in range(1, maturity + 1):
        survival_t = float(np.exp(-hazard_rate * t))
        discount = float(np.exp(-discount_rate * t))
        rows.append(
            {
                "time_years": t,
                "survival_probability": survival_t,
                "expected_premium_payment": survival_t,
                "discount_factor": discount,
                "present_value_expected_premium": survival_t * discount,
            }
        )
    df = pd.DataFrame(rows)
    df.loc["Total"] = df[["present_value_expected_premium"]].sum()
    return df


def cds_contingent_leg_table(
    hazard_rate: float, discount_rate: float, maturity: int, recovery_rate: float
) -> pd.DataFrame:
    """Build the discounted contingent-protection-leg cash-flow table for a CDS.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    discount_rate : float
        Annual discount rate in decimal units.
    maturity : int
        Time to option expiry in years.
    recovery_rate : float
        Recovery fraction expressed as a decimal in [0, 1].

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    lgd = 1.0 - recovery_rate
    rows = []
    for t in range(1, maturity + 1):
        t_mid = t - 0.5
        survival_prev = float(np.exp(-hazard_rate * (t - 1)))
        survival_t = float(np.exp(-hazard_rate * t))
        default_prob = survival_prev - survival_t
        expected_payment = lgd * default_prob
        discount = float(np.exp(-discount_rate * t_mid))
        rows.append(
            {
                "time_years": t_mid,
                "marginal_default_probability": default_prob,
                "recovery_rate": recovery_rate,
                "LGD (1-RR)": lgd,
                "expected_protection_payment": expected_payment,
                "midpoint_discount_factor": discount,
                "present_value_expected_protection": expected_payment * discount,
            }
        )
    df = pd.DataFrame(rows)
    df.loc["Total"] = df[["present_value_expected_protection"]].sum()
    return df


def cds_accrued_premium_table(
    hazard_rate: float, discount_rate: float, maturity: int
) -> pd.DataFrame:
    """Build the accrued-premium approximation table for a CDS.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    discount_rate : float
        Annual discount rate in decimal units.
    maturity : int
        Time to option expiry in years.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    rows = []
    for t in range(1, maturity + 1):
        t_mid = t - 0.5
        survival_prev = float(np.exp(-hazard_rate * (t - 1)))
        survival_t = float(np.exp(-hazard_rate * t))
        default_prob = survival_prev - survival_t
        expected_accrual = 0.5 * default_prob
        discount = float(np.exp(-discount_rate * t_mid))
        rows.append(
            {
                "time_years": t_mid,
                "marginal_default_probability": default_prob,
                "accrual_fraction": 0.5,
                "expected_accrued_premium": expected_accrual,
                "midpoint_discount_factor": discount,
                "present_value_expected_accrued_premium": expected_accrual * discount,
            }
        )
    df = pd.DataFrame(rows)
    df.loc["Total"] = df[["present_value_expected_accrued_premium"]].sum()
    return df


def cds_fair_spread(vpc_total: float, vppp_total: float, vpv_total: float) -> float:
    """Compute the fair annual CDS premium rate from leg present values.

    Parameters
    ----------
    vpc_total : float
        Total present value of the CDS contingent leg.
    vppp_total : float
        Total present value of the CDS premium-payment leg.
    vpv_total : float
        Total present value of accrued CDS premium.

    Returns
    -------
    float
        Computed cds fair spread as a dimensionless decimal quantity.
    """
    denominator = vpc_total + vppp_total
    if denominator == 0:
        return 0.0
    return float(vpv_total / denominator)


def value_cds(
    hazard_rate: float, discount_rate: float, maturity: int, recovery_rate: float
) -> dict[str, float | pd.DataFrame]:
    """Value the CDS premium and protection legs and compute the fair spread.

    Parameters
    ----------
    hazard_rate : float
        Constant default intensity in decimal annual units.
    discount_rate : float
        Annual discount rate in decimal units.
    maturity : int
        Time to option expiry in years.
    recovery_rate : float
        Recovery fraction expressed as a decimal in [0, 1].

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    probabilities = cds_probability_table(hazard_rate, maturity)
    fixed_leg = cds_premium_leg_table(hazard_rate, discount_rate, maturity)
    contingent_leg = cds_contingent_leg_table(hazard_rate, discount_rate, maturity, recovery_rate)
    accrued_premium = cds_accrued_premium_table(hazard_rate, discount_rate, maturity)

    vpc_total = float(fixed_leg.loc["Total", "present_value_expected_premium"])
    vpv_total = float(contingent_leg.loc["Total", "present_value_expected_protection"])
    vppp_total = float(accrued_premium.loc["Total", "present_value_expected_accrued_premium"])
    spread = cds_fair_spread(vpc_total, vppp_total, vpv_total)

    return {
        "probabilities": probabilities,
        "premium_leg": fixed_leg,
        "contingent_leg": contingent_leg,
        "accrued_premium": accrued_premium,
        "premium_leg_total": vpc_total,
        "contingent_leg_total": vpv_total,
        "accrued_premium_total": vppp_total,
        "spread": spread,
    }


__all__ = [
    "cds_accrued_premium_table",
    "cds_contingent_leg_table",
    "cds_fair_spread",
    "cds_premium_leg_table",
    "cds_probability_table",
    "value_cds",
]
