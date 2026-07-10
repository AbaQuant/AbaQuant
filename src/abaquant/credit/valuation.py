"""CreditMetrics-style bond valuation by destination rating.

Purpose
-------
The module evaluates a coupon bond under each future rating state using spreads, recovery, and rating-dependent discounting inputs.

Conventions
-----------
Face value is currency, coupon and recovery are fractions, maturity is in years, and spread inputs are decimal annual rates.

References
----------
[ 1 ] Merton, R. C. (1974), "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates".
[ 2 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
"""

from __future__ import annotations

import numpy as np


def bond_values_per_rating(
    face_value: float,
    coupon_rate: float,
    T: int,
    payments_per_year: int,
    recovery_pct: float,
    spreads: np.ndarray,
    include_d: bool = True,
    spread_times: np.ndarray | None = None,
) -> np.ndarray:
    """Compute future bond values for each destination credit-rating state.

    Parameters
    ----------
    face_value : float
        Bond nominal or face value in currency units.
    coupon_rate : float
        Coupon rate as a decimal fraction of face value.
    T : int
        Time to maturity in years.
    payments_per_year : int
        Coupon payments per year.
    recovery_pct : float
        Recovery fraction expressed as a decimal in [0, 1].
    spreads : np.ndarray
        Rating- and maturity-specific credit-spread inputs in decimal annual units.
    include_d : bool, default=True
        Whether the default state is included in the requested output.
    spread_times : np.ndarray | None, default=None
        Times in years corresponding to the supplied spread term structure.

    Returns
    -------
    np.ndarray
        Result of the bond values per rating calculation.
    """
    n_rated = 17
    n_cols = spreads.shape[1]

    # Construct time grid for the yield curve columns
    if spread_times is None:
        times = np.arange(1, n_cols + 1, dtype=float)  # [1,2,…,n_cols]
    else:
        times = np.asarray(spread_times, dtype=float)

    vals = np.zeros(n_rated + (1 if include_d else 0))
    coupon_payment = face_value * coupon_rate / payments_per_year
    # Cash flow times
    cf_times = np.array([(t + 1) / payments_per_year for t in range(T * payments_per_year)])

    for r_idx in range(n_rated):
        y_row = spreads[r_idx]
        pv = 0.0
        for t_yr in cf_times:
            # Find the yield for this cash-flow time via nearest available tenor
            idx = int(np.argmin(np.abs(times - t_yr)))
            # If the exact time is beyond the last available, use the last
            if t_yr > times[-1]:
                idx = len(times) - 1
            y = y_row[idx]
            pv += coupon_payment / (1.0 + y) ** t_yr
        # Principal discount at maturity T
        idx_T = int(np.argmin(np.abs(times - T)))
        if times[-1] < T:
            idx_T = len(times) - 1
        pv += face_value / (1.0 + y_row[idx_T]) ** T
        vals[r_idx] = pv

    if include_d:
        vals[17] = recovery_pct * face_value

    return vals


__all__ = ["bond_values_per_rating"]
