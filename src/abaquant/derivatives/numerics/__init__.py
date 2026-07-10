"""Numerical routines for advanced derivatives.

Purpose
-------
The package provides Fourier-inversion and implied-volatility algorithms used by the advanced pricing models.

Conventions
-----------
Numerical grids, tolerances, and iteration limits are explicit function parameters.

References
----------
[ 1 ] Carr, P., and D. B. Madan (1999), "Option Valuation Using the Fast Fourier Transform".
[ 2 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from .carr_madan_fft import carr_madan_call_price, carr_madan_option_price
from .implied_volatility import implied_normal_volatility, implied_volatility_black_scholes

__all__ = [
    "carr_madan_call_price",
    "carr_madan_option_price",
    "implied_normal_volatility",
    "implied_volatility_black_scholes",
]
