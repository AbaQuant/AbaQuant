"""Public financial-mathematics and actuarial interface.

Purpose
-------
This package exports time-value-of-money, rate conversion, annuity, bond, loan, cash-flow, equity, corporate-finance, portfolio, and market-risk helpers.

Conventions
-----------
Functions use decimal rates and explicit period or time arguments. Each callable documents its particular rate and payment-timing convention.

Scope and limitations
---------------------
The package contains deterministic calculations and pure numerical routines; it does not fetch market data.

References
----------
[ 1 ] Kellison, S. G. (2009), The Theory of Interest.
[ 2 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from .annuities import (
    arithmetic_gradient_future_value,
    arithmetic_gradient_present_value,
    continuous_annuity_future_value,
    continuous_annuity_present_value,
    effective_annuity_future_value,
    effective_annuity_present_value,
    geometric_gradient_future_value,
    geometric_gradient_present_value,
    nominal_annuity_future_value,
    nominal_annuity_present_value,
    periods_for_annuity_future_value,
    periods_for_annuity_present_value,
    periods_for_arithmetic_gradient_future_value,
    periods_for_arithmetic_gradient_present_value,
    periods_for_geometric_gradient_future_value,
    periods_for_geometric_gradient_present_value,
    perpetuity_present_value,
)
from .bonds import bond_price, bond_risk, bond_yield
from .cashflows import present_value_of_dividends, present_value_of_irregular_cashflows
from .corporate import (
    beta_alpha_from_returns,
    capm_cost_of_equity,
    dcf_sensitivity_matrix,
    dcf_valuation,
    weighted_average_cost_of_capital,
)
from .equity import gordon_shapiro_valuation, multiples_valuation, required_equity_return
from .loans import amortization_schedule
from .portfolio import (
    annualized_covariance_from_returns,
    annualized_mean_returns_from_returns,
    equal_weight,
    equal_weight_portfolio,
    evaluate_custom_portfolio,
    evaluate_custom_portfolio_from_prices,
    historical_mean_returns,
    log_return_volatility,
    log_returns_from_prices,
    max_sharpe_portfolio,
    maximum_sharpe_weights,
    min_variance_portfolio,
    minimum_variance_weights,
    monte_carlo_portfolio_cloud,
    mvsk_neg_utility,
    mvsk_portfolio,
    optimize_portfolio_strategies,
    portfolio_return,
    portfolio_sharpe,
    portfolio_variance,
    portfolio_volatility,
    risk_parity_objective,
    risk_parity_portfolio,
    sample_covariance,
    simple_returns_from_prices,
)
from .rates import (
    continuous_to_effective_rate,
    continuous_to_nominal_rate,
    convert_nominal_frequency,
    effective_to_nominal_rate,
    nominal_to_continuous_rate,
    nominal_to_effective_rate,
    reinvestment_table,
)
from .risk import monte_carlo_var_cvar, parametric_var
from .tvm import (
    continuous_future_value,
    continuous_present_value,
    decompose_periods,
    future_value,
    number_of_periods,
    present_value,
    rate_of_return,
)

__all__ = [
    "amortization_schedule",
    "annualized_covariance_from_returns",
    "annualized_mean_returns_from_returns",
    "arithmetic_gradient_future_value",
    "arithmetic_gradient_present_value",
    "beta_alpha_from_returns",
    "bond_price",
    "bond_risk",
    "bond_yield",
    "capm_cost_of_equity",
    "continuous_annuity_future_value",
    "continuous_annuity_present_value",
    "continuous_future_value",
    "continuous_present_value",
    "continuous_to_effective_rate",
    "continuous_to_nominal_rate",
    "convert_nominal_frequency",
    "dcf_sensitivity_matrix",
    "dcf_valuation",
    "decompose_periods",
    "effective_annuity_future_value",
    "effective_annuity_present_value",
    "effective_to_nominal_rate",
    "equal_weight",
    "equal_weight_portfolio",
    "evaluate_custom_portfolio",
    "evaluate_custom_portfolio_from_prices",
    "future_value",
    "geometric_gradient_future_value",
    "geometric_gradient_present_value",
    "gordon_shapiro_valuation",
    "historical_mean_returns",
    "log_return_volatility",
    "log_returns_from_prices",
    "max_sharpe_portfolio",
    "maximum_sharpe_weights",
    "min_variance_portfolio",
    "minimum_variance_weights",
    "monte_carlo_portfolio_cloud",
    "monte_carlo_var_cvar",
    "multiples_valuation",
    "mvsk_neg_utility",
    "mvsk_portfolio",
    "nominal_annuity_future_value",
    "nominal_annuity_present_value",
    "nominal_to_continuous_rate",
    "nominal_to_effective_rate",
    "number_of_periods",
    "optimize_portfolio_strategies",
    "parametric_var",
    "periods_for_annuity_future_value",
    "periods_for_annuity_present_value",
    "periods_for_arithmetic_gradient_future_value",
    "periods_for_arithmetic_gradient_present_value",
    "periods_for_geometric_gradient_future_value",
    "periods_for_geometric_gradient_present_value",
    "perpetuity_present_value",
    "portfolio_return",
    "portfolio_sharpe",
    "portfolio_variance",
    "portfolio_volatility",
    "present_value",
    "present_value_of_dividends",
    "present_value_of_irregular_cashflows",
    "rate_of_return",
    "reinvestment_table",
    "required_equity_return",
    "risk_parity_objective",
    "risk_parity_portfolio",
    "sample_covariance",
    "simple_returns_from_prices",
    "weighted_average_cost_of_capital",
]
