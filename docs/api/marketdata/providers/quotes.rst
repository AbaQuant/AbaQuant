abaquant.marketdata.providers.quotes
====================================

**Import path:** ``abaquant.marketdata.providers.quotes``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Quote-provider protocol.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``QuoteProvider`` — Provider capability for lightweight quote and issuer metadata.
  * ``QuoteProvider.fast_info`` — Return lightweight quote metadata for one normalized symbol.
  * ``QuoteProvider.info`` — Return issuer metadata for one normalized symbol.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.quotes
   :members:
   :show-inheritance:
   :member-order: bysource
