"""Exception hierarchy for optional market-data workflows.

Purpose
-------
The module defines domain-specific errors that distinguish provider, validation, history, portfolio, and optional-dependency failures.

Conventions
-----------
Exceptions carry human-readable messages and are raised instead of leaking provider-specific implementation exceptions from the public layer.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations


class MarketDataError(RuntimeError):
    """Base class for failures in the applied market-data layer."""


class MarketDataProviderError(MarketDataError):
    """Raised when a configured provider cannot supply usable data."""


class MarketDataValidationError(MarketDataError, ValueError):
    """Raised when public market-data inputs violate a domain constraint."""


class UniverseValidationError(MarketDataValidationError):
    """Raised when a ticker-universe request is invalid."""


class InsufficientHistoryError(MarketDataError):
    """Raised when available aligned history is too short for a calculation."""


class PortfolioValidationError(MarketDataValidationError):
    """Raised when an applied portfolio request or allocation is invalid."""


class PortfolioOptimizationError(MarketDataError):
    """Raised when an applied portfolio optimizer cannot produce a valid solution."""


class OptionalDependencyError(ImportError, MarketDataError):
    """Raised when an optional market-data provider dependency is unavailable."""
