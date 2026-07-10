abaquant.portfolio.risk_metrics
===============================

**Import path:** ``abaquant.portfolio.risk_metrics``

**Domain:** Portfolio construction, optimization, backtesting, risk metrics, and stress testing.

Purpose
-------

Portfolio performance and downside-risk metrics.

When to use it
--------------

Use this package to transform return histories and covariance estimates into weights, then evaluate those weights out of sample and under explicit scenarios.

Public objects
--------------

* **function:** ``portfolio_returns`` — Compute the weighted portfolio return series.
* **function:** ``cumulative_returns`` — Convert periodic returns into a cumulative wealth index starting at one.
* **function:** ``annualized_return`` — Annualize the implemented periodic return statistic.
* **function:** ``annualized_volatility`` — Annualize sample volatility from periodic returns.
* **function:** ``sharpe_ratio`` — Compute the annualized Sharpe ratio from periodic returns.
* **function:** ``downside_deviation`` — Compute annualized downside deviation relative to the supplied threshold.
* **function:** ``sortino_ratio`` — Compute the annualized Sortino ratio from periodic returns.
* **function:** ``drawdown_series`` — Compute the drawdown series of a return stream.
* **function:** ``max_drawdown`` — Return the most negative observed drawdown.
* **function:** ``calmar_ratio`` — Compute annualized return divided by absolute maximum drawdown.
* **function:** ``conditional_drawdown_at_risk`` — Compute the mean of the worst observed drawdowns at the selected tail level.
* **function:** ``var_historical`` — Compute historical value at risk under the module sign convention.
* **function:** ``cvar_historical`` — Compute historical conditional value at risk under the module sign convention.
* **function:** ``compute_all_metrics`` — Compute the module portfolio-performance metric summary.

Detailed reference
------------------

.. automodule:: abaquant.portfolio.risk_metrics
   :members:
   :show-inheritance:
   :member-order: bysource
