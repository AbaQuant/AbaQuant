abaquant.marketdata.errors
==========================

**Import path:** ``abaquant.marketdata.errors``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Exception hierarchy for optional market-data workflows.

When to use it
--------------

Defines domain-specific exceptions that callers may catch explicitly. Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``MarketDataError`` — Base class for failures in the applied market-data layer.
* **class:** ``MarketDataProviderError`` — Raised when a configured provider cannot supply usable data.
* **class:** ``MarketDataValidationError`` — Raised when public market-data inputs violate a domain constraint.
* **class:** ``UniverseValidationError`` — Raised when a ticker-universe request is invalid.
* **class:** ``InsufficientHistoryError`` — Raised when available aligned history is too short for a calculation.
* **class:** ``PortfolioValidationError`` — Raised when an applied portfolio request or allocation is invalid.
* **class:** ``PortfolioOptimizationError`` — Raised when an applied portfolio optimizer cannot produce a valid solution.
* **class:** ``OptionalDependencyError`` — Raised when an optional market-data provider dependency is unavailable.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.errors
   :members:
   :show-inheritance:
   :member-order: bysource
