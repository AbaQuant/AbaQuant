abaquant.marketdata.financials.repository
=========================================

**Import path:** ``abaquant.marketdata.financials.repository``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Retrieval repository coordinating provider access and snapshot persistence.

When to use it
--------------

This module participates in the financial-statement pipeline: provider response, normalization, cache/repository coordination, canonical line-item resolution, and analytical input construction.

Public objects
--------------

* **class:** ``FinancialStatementRepository`` — Retrieve bundled statements and manage memory/disk snapshot lifecycles.
  * ``FinancialStatementRepository.get`` — Return a cached or freshly retrieved bundled snapshot.
  * ``FinancialStatementRepository.is_stale`` — Return whether retrieval age exceeds the configured threshold.
  * ``FinancialStatementRepository.status`` — Describe local snapshot availability without provider access.
  * ``FinancialStatementRepository.clear`` — Remove selected memory and disk snapshots.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.repository
   :members:
   :show-inheritance:
   :member-order: bysource
