"""Interest-rate conversion and reinvestment calculations.

Purpose
-------
The module converts nominal, effective, and continuously compounded rates and constructs deterministic reinvestment tables.

Conventions
-----------
Rates are decimal annual rates. Compounding frequencies are positive counts per year.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def nominal_to_effective_rate(nominal_rate: float, compounds_per_year: int | float) -> float:
    """Convert a nominal annual rate to an effective annual rate.

    Parameters
    ----------
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    compounds_per_year : int | float
        Positive number of nominal compounding periods per year.

    Returns
    -------
    float
        Computed nominal to effective rate as a dimensionless decimal quantity.
    """
    if compounds_per_year <= 0:
        raise ValueError(f"`compounds_per_year` must be positive; received {compounds_per_year}.")
    return (1 + nominal_rate / compounds_per_year) ** compounds_per_year - 1


def effective_to_nominal_rate(effective_rate: float, compounds_per_year: int | float) -> float:
    """Convert an effective annual rate to a nominal annual rate.

    Parameters
    ----------
    effective_rate : float
        Effective annual interest rate in decimal units.
    compounds_per_year : int | float
        Positive number of nominal compounding periods per year.

    Returns
    -------
    float
        Computed effective to nominal rate as a dimensionless decimal quantity.
    """
    if compounds_per_year <= 0:
        raise ValueError(f"`compounds_per_year` must be positive; received {compounds_per_year}.")
    return compounds_per_year * ((1 + effective_rate) ** (1 / compounds_per_year) - 1)


def nominal_to_continuous_rate(nominal_rate: float, compounds_per_year: int | float) -> float:
    """Convert a nominal annual rate to a constant force of interest.

    Parameters
    ----------
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    compounds_per_year : int | float
        Positive number of nominal compounding periods per year.

    Returns
    -------
    float
        Computed nominal to continuous rate as a dimensionless decimal quantity.
    """
    if compounds_per_year <= 0:
        raise ValueError(f"`compounds_per_year` must be positive; received {compounds_per_year}.")
    return compounds_per_year * np.log(1 + nominal_rate / compounds_per_year)


def continuous_to_effective_rate(delta: float) -> float:
    """Convert a constant force of interest to an effective annual rate.

    Parameters
    ----------
    delta : float
        Constant force of interest in decimal annual units.

    Returns
    -------
    float
        Computed continuous to effective rate as a dimensionless decimal quantity.
    """
    return np.exp(delta) - 1


def continuous_to_nominal_rate(delta: float, compounds_per_year: int | float) -> float:
    """Convert a constant force of interest to a nominal annual rate.

    Parameters
    ----------
    delta : float
        Constant force of interest in decimal annual units.
    compounds_per_year : int | float
        Positive number of nominal compounding periods per year.

    Returns
    -------
    float
        Computed continuous to nominal rate as a dimensionless decimal quantity.
    """
    if compounds_per_year <= 0:
        raise ValueError(f"`compounds_per_year` must be positive; received {compounds_per_year}.")
    return compounds_per_year * (np.exp(delta / compounds_per_year) - 1)


def convert_nominal_frequency(
    nominal_rate: float, from_frequency: int | float, to_frequency: int | float
) -> float:
    """Convert a nominal annual rate between compounding frequencies.

    Parameters
    ----------
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    from_frequency : int | float
        Original nominal compounding frequency per year.
    to_frequency : int | float
        Target nominal compounding frequency per year.

    Returns
    -------
    float
        Computed convert nominal frequency as a scalar in the units implied by the input values.
    """
    if from_frequency <= 0 or to_frequency <= 0:
        raise ValueError(
            "`from_frequency` and `to_frequency` must be positive; "
            f"received from_frequency={from_frequency}, to_frequency={to_frequency}."
        )
    period_effective_rate = (
        (1 + nominal_rate / from_frequency) ** (from_frequency / to_frequency)
    ) - 1
    return period_effective_rate * to_frequency


def reinvestment_table(principal: float, nominal_rate: float, years: float) -> pd.DataFrame:
    """Build the deterministic year-by-year reinvestment table.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    nominal_rate : float
        Nominal annual interest rate in decimal units.
    years : float
        Time horizon in years.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    periods = [
        ("Every 4 years", 0.25),
        ("Every 2 years", 0.5),
        ("Annual", 1),
        ("Semiannual", 2),
        ("Quarterly", 4),
        ("Monthly", 12),
        ("Weekly", 52),
        ("Daily", 365),
        ("Hourly", 8760),
        ("Every minute", 525600),
        ("Every second", 31536000),
    ]

    rows = []
    for name, frequency in periods:
        accumulated_amount = principal * ((1 + nominal_rate / frequency) ** (frequency * years))
        cumulative_return = (accumulated_amount / principal) - 1
        rows.append(
            {
                "Reinvestment period": name,
                "m = Times per year": str(frequency),
                "Accumulated amount": accumulated_amount,
                "Cumulative return": cumulative_return,
            }
        )

    continuous_amount = principal * np.exp(nominal_rate * years)
    continuous_return = (continuous_amount / principal) - 1
    rows.append(
        {
            "Reinvestment period": "Continuous",
            "m = Times per year": "infinity",
            "Accumulated amount": continuous_amount,
            "Cumulative return": continuous_return,
        }
    )

    return pd.DataFrame(rows)


__all__ = [
    "continuous_to_effective_rate",
    "continuous_to_nominal_rate",
    "convert_nominal_frequency",
    "effective_to_nominal_rate",
    "nominal_to_continuous_rate",
    "nominal_to_effective_rate",
    "reinvestment_table",
]
