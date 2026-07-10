abaquant.financial_math.portfolio
=================================

**Import path:** ``abaquant.financial_math.portfolio``

**Domain:** Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.

Purpose
-------

Pure portfolio return, covariance, and allocation mathematics.

When to use it
--------------

Use these functions for deterministic calculations where explicit cash-flow, rate, compounding, sign, and annualization conventions matter.

Public objects
--------------

* **function:** ``simple_returns_from_prices`` — Compute simple returns independently for each price series.
* **function:** ``log_returns_from_prices`` — Compute logarithmic returns independently for each price series.
* **function:** ``annualized_mean_returns_from_returns`` — Annualize arithmetic mean returns from periodic observations.
* **function:** ``annualized_covariance_from_returns`` — Annualize the sample covariance matrix of periodic returns.
* **function:** ``equal_weight`` — Construct or evaluate an equally weighted fully invested portfolio.
* **function:** ``portfolio_variance`` — Compute portfolio variance from a weight vector and covariance matrix.
* **function:** ``minimum_variance_weights`` — Solve the constrained global minimum-variance allocation problem.
* **function:** ``maximum_sharpe_weights`` — Solve the constrained maximum-Sharpe portfolio allocation problem.
* **function:** ``historical_mean_returns`` — Estimate annualized arithmetic expected returns from historical prices.
* **function:** ``sample_covariance`` — Estimate an annualized covariance matrix from historical prices.
* **function:** ``log_return_volatility`` — Estimate annualized volatility from historical log returns.
* **function:** ``portfolio_return`` — Compute the weighted expected return of a portfolio.
* **function:** ``portfolio_volatility`` — Compute portfolio volatility from a weight vector and covariance matrix.
* **function:** ``portfolio_sharpe`` — Compute the annualized excess-return-to-volatility ratio.
* **function:** ``equal_weight_portfolio`` — Compute the result defined by ''equal_weight_portfolio'' under this module's documented convention.
* **function:** ``max_sharpe_portfolio`` — Compute the result defined by ''max_sharpe_portfolio'' under this module's documented convention.
* **function:** ``min_variance_portfolio`` — Compute the result defined by ''min_variance_portfolio'' under this module's documented convention.
* **function:** ``risk_parity_objective`` — Compute the result defined by ''risk_parity_objective'' under this module's documented convention.
* **function:** ``risk_parity_portfolio`` — Compute the result defined by ''risk_parity_portfolio'' under this module's documented convention.
* **function:** ``mvsk_neg_utility`` — Compute the result defined by ''mvsk_neg_utility'' under this module's documented convention.
* **function:** ``mvsk_portfolio`` — Compute the result defined by ''mvsk_portfolio'' under this module's documented convention.
* **function:** ``monte_carlo_portfolio_cloud`` — Compute the result defined by ''monte_carlo_portfolio_cloud'' under this module's documented convention.
* **function:** ``evaluate_custom_portfolio`` — Compute the result defined by ''evaluate_custom_portfolio'' under this module's documented convention.
* **function:** ``evaluate_custom_portfolio_from_prices`` — Compute the result defined by ''evaluate_custom_portfolio_from_prices'' under this module's documented convention.
* **function:** ``optimize_portfolio_strategies`` — Compute the result defined by ''optimize_portfolio_strategies'' under this module's documented convention.

Detailed reference
------------------

.. automodule:: abaquant.financial_math.portfolio
   :members:
   :show-inheritance:
   :member-order: bysource
