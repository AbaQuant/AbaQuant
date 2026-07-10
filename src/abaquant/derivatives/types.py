"""Shared advanced-derivatives type aliases.

Purpose
-------
The module centralizes typing aliases used by model, numerical, and simulation interfaces.

Conventions
-----------
Aliases constrain public argument choices but do not alter runtime pricing behavior.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeAlias

import numpy as np

ArrayLike: TypeAlias = Sequence[float] | np.ndarray
CharacteristicFunction: TypeAlias = Callable[[complex | np.ndarray], complex | np.ndarray]
