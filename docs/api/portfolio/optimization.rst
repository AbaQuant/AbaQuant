abaquant.portfolio.optimization
===============================

**Import path:** ``abaquant.portfolio.optimization``

**Domain:** Portfolio construction, optimization, backtesting, risk metrics, and stress testing.

Purpose
-------

Static portfolio allocation strategies.

When to use it
--------------

Use this package to transform return histories and covariance estimates into weights, then evaluate those weights out of sample and under explicit scenarios.

Public objects
--------------

* **class:** ``PortfolioScenarioAnalysis`` — One-period portfolio shock scenario analysis.
  * ``PortfolioScenarioAnalysis.as_frame`` — Return asset-level shock, weight, and contribution rows.
  * ``PortfolioScenarioAnalysis.as_dict`` — Return a serialization-friendly portfolio scenario mapping.
  * ``PortfolioScenarioAnalysis.scenario_analysis`` — Evaluate a one-period asset-shock scenario for a portfolio.
  * ``PortfolioScenarioAnalysis.backtest`` — Run a deterministic periodically rebalanced portfolio backtest.
  * ``PortfolioScenarioAnalysis.visualize`` — Return a figure for this portfolio scenario analysis.
* **class:** ``PortfolioComputation`` — Static in-sample allocation model for a panel of periodic asset returns.
  * ``PortfolioComputation.equal_weight`` — Construct or evaluate an equally weighted fully invested portfolio.
  * ``PortfolioComputation.max_sharpe`` — Construct a bounded maximum-Sharpe-ratio portfolio.
  * ``PortfolioComputation.min_variance`` — Compute the result defined by ''min_variance'' under this module's documented convention.
  * ``PortfolioComputation.risk_parity`` — Compute an equal-risk-contribution portfolio allocation.
  * ``PortfolioComputation.inverse_volatility`` — Compute weights inversely proportional to asset volatility.
  * ``PortfolioComputation.inverse_variance`` — Compute weights inversely proportional to asset variance.
  * ``PortfolioComputation.max_diversification`` — Optimize the diversification ratio under the configured constraints.
  * ``PortfolioComputation.min_cvar`` — Optimize a portfolio for minimum historical conditional value at risk.
  * ``PortfolioComputation.max_sortino`` — Optimize a portfolio for maximum Sortino ratio.
  * ``PortfolioComputation.max_calmar`` — Optimize a portfolio for maximum Calmar ratio.
  * ``PortfolioComputation.hrp`` — Compute Hierarchical Risk Parity weights from the optimizer return data.
  * ``PortfolioComputation.max_decorrelation`` — Optimize an allocation that minimizes average portfolio correlation.
  * ``PortfolioComputation.min_cdar`` — Optimize a portfolio for minimum conditional drawdown at risk.
  * ``PortfolioComputation.target_volatility`` — Find an allocation whose volatility is close to the requested target.
  * ``PortfolioComputation.max_return`` — Maximize estimated portfolio return under configured constraints.
  * ``PortfolioComputation.min_neg_skewness`` — Optimize a portfolio to reduce negative skewness exposure.
  * ``PortfolioComputation.kelly_fraction`` — Optimize the implemented expected-log-growth Kelly criterion.
  * ``PortfolioComputation.black_litterman`` — Compute the implemented equilibrium-prior Black--Litterman allocation without investor views.
  * ``PortfolioComputation.min_tail_kurtosis`` — Optimize a portfolio to reduce downside-tail kurtosis.
  * ``PortfolioComputation.max_omega`` — Optimize the Omega ratio relative to the supplied periodic threshold.
  * ``PortfolioComputation.max_entropy`` — Optimize diversified weights using the implemented entropy--variance objective.
  * ``PortfolioComputation.optimize`` — Run the named portfolio-allocation strategy.
  * ``PortfolioComputation.available_strategies`` — Return the allocation strategy names accepted by optimize.
  * ``PortfolioComputation.weights_to_series`` — Return a weight vector indexed by the optimizer asset labels.
* **class:** ``PortfolioEstimationContext`` — Validated in-sample returns, moments, and constraints for allocation methods.
* **class:** ``MeanVarianceAllocator`` — Mean--variance and full-investment allocation methods.
  * ``MeanVarianceAllocator.equal_weight`` — Return equal fully invested asset weights.
  * ``MeanVarianceAllocator.maximum_sharpe`` — Return the in-sample maximum-Sharpe allocation.
  * ``MeanVarianceAllocator.minimum_variance`` — Return the constrained global minimum-variance allocation.
  * ``MeanVarianceAllocator.maximum_return`` — Return the constrained maximum-return allocation.
* **class:** ``RiskBasedAllocator`` — Risk-budget, diversification, hierarchy, and concentration allocation methods.
  * ``RiskBasedAllocator.risk_parity`` — Return equal-risk-contribution weights.
  * ``RiskBasedAllocator.inverse_volatility`` — Return weights inversely proportional to asset volatility.
  * ``RiskBasedAllocator.inverse_variance`` — Return weights inversely proportional to asset variance.
  * ``RiskBasedAllocator.maximum_diversification`` — Return the maximum-diversification allocation.
  * ``RiskBasedAllocator.maximum_decorrelation`` — Return the maximum-decorrelation allocation.
  * ``RiskBasedAllocator.hierarchical_risk_parity`` — Return hierarchical risk-parity weights.
  * ``RiskBasedAllocator.maximum_entropy`` — Return the maximum-entropy allocation.
* **class:** ``DownsideRiskAllocator`` — Tail-loss and downside-performance allocation methods.
  * ``DownsideRiskAllocator.minimum_cvar`` — Return the allocation minimizing conditional value at risk.
  * ``DownsideRiskAllocator.minimum_cdar`` — Return the allocation minimizing conditional drawdown at risk.
  * ``DownsideRiskAllocator.maximum_sortino`` — Return the in-sample maximum-Sortino allocation.
  * ``DownsideRiskAllocator.maximum_calmar`` — Return the in-sample maximum-Calmar allocation.
  * ``DownsideRiskAllocator.minimum_tail_kurtosis`` — Return the allocation minimizing tail kurtosis.
  * ``DownsideRiskAllocator.maximum_omega`` — Return the allocation maximizing the Omega ratio.
* **class:** ``PortfolioAllocator`` — Facade that composes specialized static portfolio allocation families.
  * ``PortfolioAllocator.allocate`` — Run one explicitly selected allocation-family method.
  * ``PortfolioAllocator.weights_to_series`` — Index an allocation vector by the context asset order.
  * ``PortfolioAllocator.scenario_analysis`` — Evaluate a one-period asset-shock scenario for a portfolio.
  * ``PortfolioAllocator.backtest`` — Run a deterministic periodically rebalanced portfolio backtest.
  * ``PortfolioAllocator.report`` — Return an exportable report for this portfolio allocator.
  * ``PortfolioAllocator.visualize`` — Return a figure for weights, cumulative return, or correlation.

Detailed reference
------------------

.. automodule:: abaquant.portfolio.optimization
   :members:
   :show-inheritance:
   :member-order: bysource
