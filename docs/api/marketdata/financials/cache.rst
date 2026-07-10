abaquant.marketdata.financials.cache
====================================

**Import path:** ``abaquant.marketdata.financials.cache``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Atomic, versioned disk cache for financial-statement snapshots.

When to use it
--------------

This module participates in the financial-statement pipeline: provider response, normalization, cache/repository coordination, canonical line-item resolution, and analytical input construction.

Public objects
--------------

* **class:** ``FinancialStatementCacheStore`` — Read and write snapshots atomically; invalid or corrupt files are cache misses.
  * ``FinancialStatementCacheStore.path`` — Return the deterministic cache path for one symbol, source, and period.
  * ``FinancialStatementCacheStore.load`` — Load and checksum-validate one cache entry.
  * ``FinancialStatementCacheStore.save`` — Write a cache entry through a temporary file and atomic replacement.
  * ``FinancialStatementCacheStore.remove`` — Remove one cache entry if it exists.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.cache
   :members:
   :show-inheritance:
   :member-order: bysource
