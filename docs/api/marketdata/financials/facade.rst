abaquant.marketdata.financials.facade
=====================================

**Import path:** ``abaquant.marketdata.financials.facade``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Small public facade for cached financial statement retrieval.

When to use it
--------------

This module participates in the financial-statement pipeline: provider response, normalization, cache/repository coordination, canonical line-item resolution, and analytical input construction.

Public objects
--------------

* **class:** ``FinancialStatements`` — Public financial-statement facade with source-aware repositories.
  * ``FinancialStatements.snapshot`` — Return one repository-managed statement snapshot.
  * ``FinancialStatements.refresh`` — Refresh a period when forced or when its cache is stale.
  * ``FinancialStatements.cache_status`` — Describe cache availability without a provider request.
  * ``FinancialStatements.clear_cache`` — Remove selected cache entries from memory and disk.
  * ``FinancialStatements.sec_company_facts`` — Return raw SEC Company Facts with attached provenance metadata.
  * ``FinancialStatements.sec_facts`` — Return raw SEC Company Facts JSON for the configured SEC source.
  * ``FinancialStatements.sec_cache_status`` — Describe SEC raw-data cache availability without a provider request.
  * ``FinancialStatements.clear_sec_cache`` — Clear SEC raw Company Facts cache entries for this ticker when supported.
  * ``FinancialStatements.income_statement`` — Return a defensive copy of the normalized income statement.
  * ``FinancialStatements.balance_sheet`` — Return a defensive copy of the normalized balance sheet.
  * ``FinancialStatements.cash_flow_statement`` — Return a defensive copy of the normalized cash-flow statement.
  * ``FinancialStatements.get_line_item_details`` — Return a resolved line item with provider-label provenance.
  * ``FinancialStatements.get_line_item`` — Return a resolved scalar value or ''None'' when unavailable.
  * ``FinancialStatements.credit_inputs`` — Build grouped credit-analysis inputs from one snapshot.
  * ``FinancialStatements.visualize`` — Return a figure for the latest column of one cached statement table.
  * ``FinancialStatements.total_debt`` — Return the latest resolved 'total_debt' statement value.
  * ``FinancialStatements.total_equity`` — Return the latest resolved 'total_equity' statement value.
  * ``FinancialStatements.current_assets`` — Return the latest resolved 'current_assets' statement value.
  * ``FinancialStatements.inventory`` — Return the latest resolved 'inventory' statement value.
  * ``FinancialStatements.current_liabilities`` — Return the latest resolved 'current_liabilities' statement value.
  * ``FinancialStatements.cash_and_cash_equivalents`` — Return the latest resolved 'cash_and_cash_equivalents' statement value.
  * ``FinancialStatements.ebit`` — Return the latest resolved 'ebit' statement value.
  * ``FinancialStatements.ebitda`` — Return the latest resolved 'ebitda' statement value.
  * ``FinancialStatements.interest_expense`` — Return the latest resolved 'interest_expense' statement value.
  * ``FinancialStatements.operating_cash_flow`` — Return the latest resolved 'operating_cash_flow' statement value.
  * ``FinancialStatements.total_assets`` — Return the latest resolved 'total_assets' statement value.
  * ``FinancialStatements.total_liabilities`` — Return the latest resolved 'total_liabilities' statement value.
  * ``FinancialStatements.retained_earnings`` — Return the latest resolved 'retained_earnings' statement value.
  * ``FinancialStatements.revenue`` — Return the latest resolved 'revenue' statement value.
  * ``FinancialStatements.net_income`` — Return the latest resolved 'net_income' statement value.
  * ``FinancialStatements.long_term_debt`` — Return the latest resolved 'long_term_debt' statement value.
  * ``FinancialStatements.shares_outstanding`` — Return the latest resolved 'shares_outstanding' statement value.
  * ``FinancialStatements.gross_profit`` — Return the latest resolved 'gross_profit' statement value.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.facade
   :members:
   :show-inheritance:
   :member-order: bysource
