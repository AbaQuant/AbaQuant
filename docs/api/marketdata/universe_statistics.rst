abaquant.marketdata.universe_statistics
=======================================

**Import path:** ``abaquant.marketdata.universe_statistics``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Annualized return and covariance statistics for ticker universes.

When to use it
--------------

Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``UniverseStatistics`` — Annualized moment-estimation namespace for a :class:'MarketUniverse'.
  * ``UniverseStatistics.summary`` — Compute per-asset annualized return and risk summary statistics.
  * ``UniverseStatistics.covariance`` — Compute an annualized covariance matrix from aligned returns.
  * ``UniverseStatistics.expected_returns`` — Compute annualized arithmetic expected returns from aligned returns.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.universe_statistics
   :members:
   :show-inheritance:
   :member-order: bysource
