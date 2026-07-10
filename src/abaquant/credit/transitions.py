"""Credit-rating transition matrix construction.

Purpose
-------
The module turns raw migration-frequency data into a transition matrix with selectable treatment of the not-rated state.

Conventions
-----------
Rows follow the package rating-state order. The default state is absorbing when included by the selected convention.

References
----------
[ 1 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
"""

from __future__ import annotations

import numpy as np

from .data import ISSUER_RATINGS, _TM_RAW_17x19


def build_transition_matrix(
    raw_17x19: np.ndarray | None = None, nr_treatment: str = "redistribute"
) -> np.ndarray:
    """Build a credit-rating transition matrix under the selected not-rated treatment.

    Parameters
    ----------
    raw_17x19 : np.ndarray | None, default=None
        Raw credit-transition table in the documented 17-by-19 source layout.
    nr_treatment : str, default='redistribute'
        Rule governing treatment of the not-rated transition state.

    Returns
    -------
    np.ndarray
        Result of the build transition matrix calculation.
    """
    if raw_17x19 is None:
        raw_17x19 = _TM_RAW_17x19.copy()

    raw = raw_17x19.astype(float).copy()  # (17, 19)

    # Split columns: 0..16=AAA..CCC/C, 17=D, 18=NR
    rated_probs = raw[:, :17]  # AAA..CCC/C  (17 cols)
    d_probs = raw[:, 17]  # D
    nr_probs = raw[:, 18]  # NR

    if nr_treatment == "raw_with_d":
        # Raw S&P probabilities, columns AAA..D (18 destination states), excluding NR.
        # Rows do not sum to one because NR is excluded without redistribution (the spreadsheet convention).
        # This is the traditional convention used in CreditMetrics textbook exercises.
        # Returns (18, 18): rows 0..16 sum to less than one; D is absorbing.
        raw18 = np.column_stack([rated_probs, d_probs])  # (17, 18)
        d_row = np.zeros(18)
        d_row[-1] = 1.0
        return np.vstack([raw18, d_row])  # (18, 18)

    elif nr_treatment == "redistribute":
        # Redistribute NR proportionally across the 18 states (AAA..CCC/C + D)
        rated_plus_d = np.column_stack([rated_probs, d_probs])  # (17, 18)
        sums_rated_d = rated_plus_d.sum(axis=1, keepdims=True)
        sums_rated_d[sums_rated_d == 0] = 1.0
        adjusted = rated_plus_d + nr_probs[:, None] * (rated_plus_d / sums_rated_d)
        # Normalize to sum exactly 1
        rs = adjusted.sum(axis=1, keepdims=True)
        rs[rs == 0] = 1.0
        adjusted = adjusted / rs  # (17, 18)
        d_row = np.zeros(18)
        d_row[-1] = 1.0
        return np.vstack([adjusted, d_row])  # (18, 18)

    elif nr_treatment == "simple_normalize":
        # Drop NR and renormalize AAA..D to one using simple scaling
        rated_plus_d = np.column_stack([rated_probs, d_probs])  # (17, 18)
        sums = rated_plus_d.sum(axis=1, keepdims=True)
        sums[sums == 0] = 1.0
        adjusted = rated_plus_d / sums  # (17, 18)
        d_row = np.zeros(18)
        d_row[-1] = 1.0
        return np.vstack([adjusted, d_row])  # (18, 18)

    else:  # 'raw_no_d_nr'
        # Use AAA..CCC/C as provided, without D, without NR, and without normalization
        # Returns (17, 17), consistent with the teaching-exercise convention.
        # Rows sum to less than one because NR and D are excluded.
        # This mode assumes the residual probability disappears: no default and no NR transition.
        return rated_probs.copy()  # (17, 17)


DEFAULT_TM = build_transition_matrix()
_TM_SIZE_BY_MODE = {"raw_with_d": 18, "redistribute": 18, "simple_normalize": 18, "raw_no_d_nr": 17}
RATINGS_NO_D = ISSUER_RATINGS[:17]

__all__ = [
    "DEFAULT_TM",
    "RATINGS_NO_D",
    "_TM_SIZE_BY_MODE",
    "build_transition_matrix",
]
