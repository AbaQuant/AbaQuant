"""Level-payment loan amortization schedules.

Purpose
-------
The module produces deterministic amortization schedules for fixed-rate installment loans.

Conventions
-----------
Principal is a currency amount; period rate is a decimal rate per payment period; periods is the number of payments.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import pandas as pd


def amortization_schedule(principal: float, period_rate: float, periods: int) -> pd.DataFrame:
    """Construct the deterministic payment, interest, principal, and balance schedule of a level-payment loan.

    Parameters
    ----------
    principal : float
        Initial invested amount or loan principal in currency units.
    period_rate : float
        Effective interest rate per payment period in decimal units.
    periods : int
        Number of discrete compounding or payment periods.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    if period_rate < 0:
        raise ValueError("period_rate must be >= 0")
    period_count = periods

    if period_rate == 0:
        payment = principal / period_count
    else:
        payment = principal * (period_rate / (1 - (1 + period_rate) ** (-period_count)))

    balance = principal
    rows = []

    for period in range(1, period_count + 1):
        opening_balance = balance
        interest = opening_balance * period_rate
        amortization = payment - interest

        if period == period_count:
            amortization = opening_balance
            balance = 0.0
        else:
            balance -= amortization
            if abs(balance) < 0.01:
                balance = 0.0

        rows.append(
            {
                "Period": period,
                "Opening balance": opening_balance,
                "Interest": interest,
                "Amortization": amortization,
                "Outstanding balance": balance,
            }
        )

    return pd.DataFrame(rows)


__all__ = ["amortization_schedule"]
