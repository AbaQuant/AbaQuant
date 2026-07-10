abaquant.marketdata.sessions
============================

**Import path:** ``abaquant.marketdata.sessions``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Mutable request-local state separated from immutable market-data configuration.

When to use it
--------------

Controls provider/session construction and dependency injection. Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``TickerIdentity`` — Immutable identifier for one normalized ticker and provider.
* **class:** ``TickerConfiguration`` — Immutable cache and request policy for a ticker facade.
* **class:** ``TickerSession`` — Mutable in-memory financial snapshots and request-local diagnostics.
* **class:** ``UniverseSession`` — Mutable in-memory price panels for one universe facade.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.sessions
   :members:
   :show-inheritance:
   :member-order: bysource
