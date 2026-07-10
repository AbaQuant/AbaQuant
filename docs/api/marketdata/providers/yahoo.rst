abaquant.marketdata.providers.yahoo
===================================

**Import path:** ``abaquant.marketdata.providers.yahoo``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Yahoo Finance adapter backed by the optional yfinance dependency.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``YahooFinanceProvider`` — Yahoo Finance provider adapter backed by optional yfinance.
  * ``YahooFinanceProvider.fast_info`` — Retrieve a lightweight quote metadata mapping from the provider.
  * ``YahooFinanceProvider.info`` — Return provider metadata normalized to a plain Python dictionary.
  * ``YahooFinanceProvider.history`` — Retrieve historical market data through the configured provider.
  * ``YahooFinanceProvider.history_many`` — Retrieve batched historical market data through the configured provider.
  * ``YahooFinanceProvider.option_expirations`` — Retrieve listed option expiration dates from the provider.
  * ``YahooFinanceProvider.option_chain`` — Retrieve raw call and put option-chain tables from the provider.
  * ``YahooFinanceProvider.income_statement`` — Retrieve a structured annual or quarterly income statement from yfinance.
  * ``YahooFinanceProvider.balance_sheet`` — Retrieve a structured annual or quarterly balance sheet from yfinance.
  * ``YahooFinanceProvider.cash_flow_statement`` — Retrieve a structured annual or quarterly cash-flow statement from yfinance.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.yahoo
   :members:
   :show-inheritance:
   :member-order: bysource
