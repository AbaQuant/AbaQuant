abaquant.marketdata.financials.models
=====================================

**Import path:** ``abaquant.marketdata.financials.models``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Immutable financial-statement snapshot and line-item models.

When to use it
--------------

Defines structured inputs or model-facing data containers. Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``FinancialLineItem`` — Resolved canonical line item with provider provenance.
* **class:** ``FinancialStatementSnapshot`` — Immutable metadata wrapper around three normalized statement tables.
  * ``FinancialStatementSnapshot.income_statement`` — Return a defensive copy of the normalized income statement.
  * ``FinancialStatementSnapshot.balance_sheet`` — Return a defensive copy of the normalized balance sheet.
  * ``FinancialStatementSnapshot.cash_flow_statement`` — Return a defensive copy of the normalized cash-flow statement.
  * ``FinancialStatementSnapshot.canonical_line_items`` — Return a read-only canonical item mapping.
  * ``FinancialStatementSnapshot.raw_tables`` — Return defensive copies of income, balance-sheet, and cash-flow tables.
  * ``FinancialStatementSnapshot.visualize`` — Return a figure for the latest numeric column of one statement table.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.models
   :members:
   :show-inheritance:
   :member-order: bysource
