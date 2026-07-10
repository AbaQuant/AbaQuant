abaquant.marketdata.providers.history
=====================================

**Import path:** ``abaquant.marketdata.providers.history``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Historical-price provider protocol.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``PriceHistoryProvider`` — Provider capability for single-asset and batched price history.
  * ``PriceHistoryProvider.history`` — Return one symbol's historical market data.
  * ``PriceHistoryProvider.history_many`` — Return a batched historical price panel.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.history
   :members:
   :show-inheritance:
   :member-order: bysource
