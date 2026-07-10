"""Model-calibration workflows.

Purpose
-------
The package exposes both legacy functional calibration helpers and structured
calibration classes that return reusable result objects with model-versus-market
fit diagnostics.

Conventions
-----------
Market implied volatilities are decimal annual volatilities and optimisation
tolerances are numerical convergence thresholds.

References
----------
[ 1 ] Heston, S. L. (1993), "A Closed-Form Solution for Options with Stochastic Volatility".
[ 2 ] Hagan, P. S., D. Kumar, A. S. Lesniewski, and D. E. Woodward (2002), "Managing Smile Risk".
"""

from .core import (
    BSMFlatVolCalibration,
    CalibrationError,
    CalibrationResult,
    HestonCalibration,
    SABRSmileCalibration,
)
from .heston import calibrate_heston
from .sabr import calibrate_sabr

__all__ = [
    "BSMFlatVolCalibration",
    "CalibrationError",
    "CalibrationResult",
    "HestonCalibration",
    "SABRSmileCalibration",
    "calibrate_heston",
    "calibrate_sabr",
]
