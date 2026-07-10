abaquant.risk.dashboard
=======================

**Import path:** ``abaquant.risk.dashboard``

**Domain:** Integrated portfolio and credit-risk dashboards.

Purpose
-------

Integrated portfolio and credit risk dashboard.

When to use it
--------------

Use this package to combine backtest, drawdown, contribution, correlation, and credit information into one review surface.

Public objects
--------------

* **class:** ``RiskDashboardSummary`` — Compact summary of an integrated risk dashboard.
  * ``RiskDashboardSummary.as_dict`` — Return a serialization-friendly nested summary mapping.
* **class:** ``RiskDashboard`` — Combine portfolio risk, backtest, correlation, and credit diagnostics.
  * ``RiskDashboard.summary`` — Return nested portfolio, risk-contribution, credit, and correlation summaries.
  * ``RiskDashboard.portfolio_summary`` — Return scalar portfolio performance and drawdown diagnostics.
  * ``RiskDashboard.portfolio_returns`` — Return weighted periodic portfolio returns.
  * ``RiskDashboard.equity_curve`` — Return the dashboard portfolio equity curve.
  * ``RiskDashboard.drawdown`` — Return portfolio drawdowns from the backtest or weighted returns.
  * ``RiskDashboard.correlation`` — Return the asset return correlation matrix.
  * ``RiskDashboard.correlation_summary`` — Return aggregate asset-correlation diagnostics.
  * ``RiskDashboard.risk_contribution`` — Return variance-covariance asset risk contributions.
  * ``RiskDashboard.risk_contribution_summary`` — Return concentration diagnostics from the risk-contribution table.
  * ``RiskDashboard.credit_scores`` — Return a credit-proxy score table for all supplied assessments.
  * ``RiskDashboard.credit_summary`` — Return aggregate diagnostics for supplied credit-proxy assessments.
  * ``RiskDashboard.report`` — Return an exportable report for this integrated risk dashboard.
  * ``RiskDashboard.visual_report`` — Return a dictionary of dashboard figures keyed by chart name.
  * ``RiskDashboard.visualize`` — Return a dashboard figure for risk, drawdown, credit, or correlation.

Detailed reference
------------------

.. automodule:: abaquant.risk.dashboard
   :members:
   :show-inheritance:
   :member-order: bysource
