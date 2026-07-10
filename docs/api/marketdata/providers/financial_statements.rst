abaquant.marketdata.providers.financial_statements
==================================================

**Import path:** ``abaquant.marketdata.providers.financial_statements``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Financial-statement provider protocol.

When to use it
--------------

This module belongs to the provider layer. Most users reach it through the market-data facades; custom integrations can implement or instantiate the documented contracts directly.

Public objects
--------------

* **class:** ``FinancialStatementProvider`` — Provider capability for annual or quarterly financial statements.
  * ``FinancialStatementProvider.sec_facts`` — Return raw SEC Company Facts JSON when the provider supports it.
  * ``FinancialStatementProvider.income_statement`` — Return the requested income statement table.
  * ``FinancialStatementProvider.balance_sheet`` — Return the requested balance-sheet table.
  * ``FinancialStatementProvider.cash_flow_statement`` — Return the requested cash-flow statement table.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.providers.financial_statements
   :members:
   :show-inheritance:
   :member-order: bysource
