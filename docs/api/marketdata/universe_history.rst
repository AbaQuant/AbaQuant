abaquant.marketdata.universe_history
====================================

**Import path:** ``abaquant.marketdata.universe_history``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Normalized historical price and return panels for ticker universes.

When to use it
--------------

Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``UniverseHistory`` — Lazy historical-price and return retrieval namespace for a universe.
  * ``UniverseHistory.prices`` — Return the normalized price data required by this interface.
  * ``UniverseHistory.returns`` — Compute periodic returns from the normalized price panel.
* **function:** ``normalize_price_panel`` — Compute the result defined by ''normalize_price_panel'' under this module's documented convention.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.universe_history
   :members:
   :show-inheritance:
   :member-order: bysource
