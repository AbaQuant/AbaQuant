abaquant.marketdata.universe_portfolio
======================================

**Import path:** ``abaquant.marketdata.universe_portfolio``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Applied static portfolio construction for ticker universes.

When to use it
--------------

Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``UniversePortfolioAnalytics`` — Static portfolio-analysis namespace for a :class:'MarketUniverse'.
  * ``UniversePortfolioAnalytics.equal_weight`` — Construct or evaluate an equally weighted fully invested portfolio.
  * ``UniversePortfolioAnalytics.minimum_variance`` — Construct a bounded global minimum-variance portfolio.
  * ``UniversePortfolioAnalytics.max_sharpe`` — Construct a bounded maximum-Sharpe-ratio portfolio.
  * ``UniversePortfolioAnalytics.evaluate`` — Evaluate a user-supplied portfolio allocation against historical inputs.
  * ``UniversePortfolioAnalytics.backtest`` — Backtest a deterministic rebalanced allocation for this universe.
  * ``UniversePortfolioAnalytics.scenario_analysis`` — Evaluate a one-period shock scenario for this universe.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.universe_portfolio
   :members:
   :show-inheritance:
   :member-order: bysource
