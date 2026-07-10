abaquant.marketdata.universe
============================

**Import path:** ``abaquant.marketdata.universe``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Lazy multi-ticker market-data universe.

When to use it
--------------

Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **function:** ``get_tickers`` — Create a lazy applied universe for normalized ticker symbols.
* **class:** ``MarketUniverse`` — Lazy multi-ticker facade with immutable symbols and a separate session.
  * ``MarketUniverse.visualize`` — Return a normalized multi-ticker price-history figure.
* **function:** ``normalize_symbols`` — Normalize, validate, and de-duplicate ticker symbols.
* **function:** ``resolve_provider`` — Resolve a provider name or provider instance to the market-data protocol.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.universe
   :members:
   :show-inheritance:
   :member-order: bysource
