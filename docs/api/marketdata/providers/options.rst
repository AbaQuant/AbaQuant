abaquant.marketdata.providers.options
=====================================

**Import path:** ``abaquant.marketdata.providers.options``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Listed-option-chain provider protocol.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``OptionChainProvider`` — Provider capability for expirations and raw call/put option tables.
  * ``OptionChainProvider.option_expirations`` — Return listed expiration dates for one normalized symbol.
  * ``OptionChainProvider.option_chain`` — Return raw call and put tables for one expiration date.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.options
   :members:
   :show-inheritance:
   :member-order: bysource
