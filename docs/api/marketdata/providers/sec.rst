abaquant.marketdata.providers.sec
=================================

**Import path:** ``abaquant.marketdata.providers.sec``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

SEC EDGAR/XBRL financial-statement provider with persistent JSON caching.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``SecCompanyFacts`` — Raw SEC Company Facts payload with resolved CIK provenance.
* **class:** ``SecJsonCacheStore`` — Versioned, checksum-validated disk cache for SEC JSON payloads.
  * ``SecJsonCacheStore.ticker_mapping_path`` — Return the cache path for the SEC ticker-to-CIK mapping.
  * ``SecJsonCacheStore.company_facts_path`` — Return the cache path for one ticker's Company Facts payload.
  * ``SecJsonCacheStore.load_ticker_mapping`` — Load the cached ticker-to-CIK mapping when present and fresh.
  * ``SecJsonCacheStore.save_ticker_mapping`` — Persist a normalized ticker-to-CIK mapping atomically.
  * ``SecJsonCacheStore.load_company_facts`` — Load a cached Company Facts payload when present and fresh.
  * ``SecJsonCacheStore.save_company_facts`` — Persist one Company Facts payload atomically.
  * ``SecJsonCacheStore.ticker_mapping_status`` — Return local ticker-mapping cache availability without network access.
  * ``SecJsonCacheStore.company_facts_status`` — Return local Company Facts cache availability without network access.
  * ``SecJsonCacheStore.remove_company_facts`` — Remove cached Company Facts payloads for one symbol.
* **class:** ``SecXbrlProvider`` — Financial-statement provider backed by SEC EDGAR Company Facts.
  * ``SecXbrlProvider.company_facts`` — Return the SEC Company Facts payload for one ticker symbol.
  * ``SecXbrlProvider.sec_facts`` — Return the raw SEC Company Facts JSON payload for one symbol.
  * ``SecXbrlProvider.cik_for_symbol`` — Resolve a ticker symbol to a ten-digit SEC CIK using cache when possible.
  * ``SecXbrlProvider.income_statement`` — Return a normalized SEC-derived income-statement table.
  * ``SecXbrlProvider.balance_sheet`` — Return a normalized SEC-derived balance-sheet table.
  * ``SecXbrlProvider.cash_flow_statement`` — Return a normalized SEC-derived cash-flow statement table.
  * ``SecXbrlProvider.cache_status`` — Describe SEC raw-data cache availability without provider access.
  * ``SecXbrlProvider.clear_cache`` — Clear memory and disk Company Facts cache entries for one or all symbols.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.sec
   :members:
   :show-inheritance:
   :member-order: bysource
