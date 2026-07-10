abaquant.credit.fundamentals
============================

**Import path:** ``abaquant.credit.fundamentals``

**Domain:** Credit-risk analytics and fundamentals-derived credit proxies.

Purpose
-------

Grouped financial-statement inputs and transparent credit-proxy metrics.

When to use it
--------------

Use this package for transition matrices, spread-based valuation, CDS/CDO building blocks, copula simulation, tail risk, and accounting-based credit diagnostics.

Public objects
--------------

* **class:** ``ReportedValue`` — One reported financial value with statement provenance.
* **class:** ``BalanceSheetInputs`` — Balance-sheet values for one reporting date in a consistent currency.
* **class:** ``IncomeStatementInputs`` — Income-statement values for one reporting period in a consistent currency.
* **class:** ``CashFlowInputs`` — Cash-flow values for one reporting period in a consistent currency.
* **class:** ``PriorPeriodInputs`` — Comparable values from the immediately preceding reporting period.
* **class:** ``MarketEquityObservation`` — Market-capitalization observation with its observation date.
* **class:** ``CreditHistoricalSeries`` — Comparable historical earnings and leverage observations, oldest first.
* **class:** ``CreditAnalysisInputs`` — Grouped, immutable inputs for fundamental credit-proxy calculations.
  * ``CreditAnalysisInputs.total_debt`` — Return current total debt from the balance-sheet input group.
  * ``CreditAnalysisInputs.total_equity`` — Return current total equity from the balance-sheet input group.
  * ``CreditAnalysisInputs.current_assets`` — Return current assets from the balance-sheet input group.
  * ``CreditAnalysisInputs.inventory`` — Return inventory from the balance-sheet input group.
  * ``CreditAnalysisInputs.current_liabilities`` — Return current liabilities from the balance-sheet input group.
  * ``CreditAnalysisInputs.cash_and_cash_equivalents`` — Return cash and cash equivalents from the balance-sheet input group.
  * ``CreditAnalysisInputs.total_assets`` — Return current total assets from the balance-sheet input group.
  * ``CreditAnalysisInputs.total_liabilities`` — Return current total liabilities from the balance-sheet input group.
  * ``CreditAnalysisInputs.retained_earnings`` — Return retained earnings from the balance-sheet input group.
  * ``CreditAnalysisInputs.long_term_debt`` — Return long-term debt from the balance-sheet input group.
  * ``CreditAnalysisInputs.shares_outstanding`` — Return current shares outstanding from the balance-sheet input group.
  * ``CreditAnalysisInputs.ebit`` — Return EBIT from the income-statement input group.
  * ``CreditAnalysisInputs.ebitda`` — Return EBITDA from the income-statement input group.
  * ``CreditAnalysisInputs.interest_expense`` — Return interest expense from the income-statement input group.
  * ``CreditAnalysisInputs.revenue`` — Return current revenue from the income-statement input group.
  * ``CreditAnalysisInputs.net_income`` — Return current net income from the income-statement input group.
  * ``CreditAnalysisInputs.gross_profit`` — Return current gross profit from the income-statement input group.
  * ``CreditAnalysisInputs.operating_cash_flow`` — Return operating cash flow from the cash-flow input group.
  * ``CreditAnalysisInputs.market_value_equity`` — Return observed market equity, or ''None'' when it was not supplied.
  * ``CreditAnalysisInputs.earnings_history`` — Return the normalized historical earnings sequence.
  * ``CreditAnalysisInputs.leverage_history`` — Return the normalized historical leverage sequence.
  * ``CreditAnalysisInputs.previous_total_assets`` — Return prior-period total assets, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_net_income`` — Return prior-period net income, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_long_term_debt`` — Return prior-period long-term debt, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_current_assets`` — Return prior-period current assets, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_current_liabilities`` — Return prior-period current liabilities, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_shares_outstanding`` — Return prior-period shares outstanding, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_gross_profit`` — Return prior-period gross profit, or ''None'' when unavailable.
  * ``CreditAnalysisInputs.previous_revenue`` — Return prior-period revenue, or ''None'' when unavailable.
* **class:** ``CreditScenarioAnalysis`` — Multiplier scenario grid for a fundamental credit-proxy assessment.
  * ``CreditScenarioAnalysis.as_dict`` — Return a serialization-friendly credit scenario mapping.
  * ``CreditScenarioAnalysis.report`` — Return an exportable report for this credit-proxy assessment.
  * ``CreditScenarioAnalysis.visualize`` — Return a figure for this credit multiplier scenario grid.
* **class:** ``CreditProxyAssessment`` — Transparent result of fundamental credit-proxy calculations.
  * ``CreditProxyAssessment.scenario_analysis`` — Recalculate credit-proxy metrics over statement-input multipliers.
  * ``CreditProxyAssessment.as_dict`` — Return a flat, serialization-friendly mapping of assessment outputs.
  * ``CreditProxyAssessment.report`` — Return an exportable report for this credit-proxy assessment.
  * ``CreditProxyAssessment.visualize`` — Return a figure for this credit-proxy assessment.
* **function:** ``calculate_credit_proxy_metrics`` — Calculate manual fundamental credit-proxy metrics.

Detailed reference
------------------

.. automodule:: abaquant.credit.fundamentals
   :members:
   :show-inheritance:
   :member-order: bysource
