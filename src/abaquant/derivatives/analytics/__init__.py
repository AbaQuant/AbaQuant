"""Analytics helpers for advanced derivatives.

Purpose
-------
The package contains distribution diagnostics, parity checks, and historical/implied-volatility analytics used alongside pricing models.

Conventions
-----------
Inputs follow the conventions documented by each function.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from .distributions import distribution_moments, excess_kurtosis, theoretical_mc_error
from .parity import forward_price_continuous, intrinsic_time_value, parity_check
from .volatility import iv_rv_spread, realized_vol

__all__ = [
    "distribution_moments",
    "excess_kurtosis",
    "forward_price_continuous",
    "intrinsic_time_value",
    "iv_rv_spread",
    "parity_check",
    "realized_vol",
    "theoretical_mc_error",
]
