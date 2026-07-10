"""Typed credit-risk input models.

Purpose
-------
The module defines light-weight typed containers used by credit valuation and portfolio routines.

Conventions
-----------
Field meanings, units, and state conventions are documented on the data model.

References
----------
[ 1 ] Merton, R. C. (1974), "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates".
"""

from __future__ import annotations

from typing import TypedDict

import numpy as np


class BondData(TypedDict):
    """Typed input record used by credit-risk valuation routines.

    Attributes
    ----------
    rating_idx : int
        Index of the initial credit-rating state.
    values : np.ndarray
        One-dimensional numerical sample used for distribution diagnostics.

    Notes
    -----
    Behavior and units are defined by the module-level conventions and public method documentation.
    """

    rating_idx: int
    values: np.ndarray


RiskResult = dict[str, float]
RiskResults = dict[float, RiskResult]
Distribution = list[tuple[float, float]]

__all__ = ["BondData", "Distribution", "RiskResult", "RiskResults"]
