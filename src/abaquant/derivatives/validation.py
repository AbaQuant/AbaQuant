"""Input-validation helpers for advanced derivatives.

Purpose
-------
The module contains small reusable checks for positivity, non-negativity, intervals, integer counts, and option-type labels.

Conventions
-----------
Validation helpers raise ValueError for inputs outside their declared domain.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations


def validate_positive(name: str, value: float) -> None:
    """Require a strictly positive numeric input.

    Parameters
    ----------
    name : str
        Human-readable name of the value being validated.
    value : float
        Numerical value being validated or transformed.

    Returns
    -------
    None
        The function returns ``None`` when the value is valid and raises ``ValueError`` otherwise.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def validate_nonnegative(name: str, value: float) -> None:
    """Require a numeric input greater than or equal to zero.

    Parameters
    ----------
    name : str
        Human-readable name of the value being validated.
    value : float
        Numerical value being validated or transformed.

    Returns
    -------
    None
        The function returns ``None`` when the value is valid and raises ``ValueError`` otherwise.
    """
    if value < 0:
        raise ValueError(f"{name} must be nonnegative.")


def validate_between(name: str, value: float, lower: float, upper: float) -> None:
    """Require a numeric input to lie strictly inside an open interval.

    Parameters
    ----------
    name : str
        Human-readable name of the value being validated.
    value : float
        Numerical value being validated or transformed.
    lower : float
        Lower root-search or interval bound.
    upper : float
        Upper root-search or interval bound.

    Returns
    -------
    None
        The function returns ``None`` when the value is valid and raises ``ValueError`` otherwise.
    """
    if not lower < value < upper:
        raise ValueError(f"{name} must be between {lower} and {upper}.")


def validate_positive_integer(name: str, value: int) -> None:
    """Require a positive integer input.

    Parameters
    ----------
    name : str
        Human-readable name of the value being validated.
    value : int
        Numerical value being validated or transformed.

    Returns
    -------
    None
        The function returns ``None`` when the value is valid and raises ``ValueError`` otherwise.
    """
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def validate_option_type(option_type: str) -> None:
    """Require an option type supported by vanilla call/put routines.

    Parameters
    ----------
    option_type : str
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    None
        The function returns ``None`` when the label is valid and raises ``ValueError`` otherwise.
    """
    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
