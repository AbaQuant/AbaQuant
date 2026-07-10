"""Financial-mathematics examples with small reusable functions."""

from __future__ import annotations

import numpy as np

from _shared.output import print_mapping
from _shared.package_bootstrap import ensure_package_importable
from _shared.sample_data import sample_prices

ensure_package_importable()

from abaquant.financial_math.annuities import (
    arithmetic_gradient_present_value,
    effective_annuity_present_value,
    geometric_gradient_present_value,
    perpetuity_present_value,
)
from abaquant.financial_math.bonds import bond_price, bond_risk, bond_yield
from abaquant.financial_math.cashflows import present_value_of_irregular_cashflows
from abaquant.financial_math.corporate import (
    beta_alpha_from_returns,
    capm_cost_of_equity,
    dcf_sensitivity_matrix,
    dcf_valuation,
    weighted_average_cost_of_capital,
)
from abaquant.financial_math.equity import gordon_shapiro_valuation, multiples_valuation
from abaquant.financial_math.loans import amortization_schedule
from abaquant.financial_math.portfolio import (
    annualized_covariance_from_returns,
    annualized_mean_returns_from_returns,
    equal_weight,
    maximum_sharpe_weights,
    portfolio_sharpe,
    portfolio_volatility,
    simple_returns_from_prices,
)
from abaquant.financial_math.rates import (
    continuous_to_effective_rate,
    convert_nominal_frequency,
    nominal_to_effective_rate,
)
from abaquant.financial_math.risk import monte_carlo_var_cvar, parametric_var
from abaquant.financial_math.tvm import future_value, present_value, rate_of_return


def demonstrate_time_value() -> dict[str, float]:
    """Compute basic accumulation, discounting, and realized return."""
    return {
        "future_value": future_value(1_000.0, 0.06, 5.0),
        "present_value": present_value(1_500.0, 0.06, 5.0),
        "required_periodic_return": rate_of_return(1_000.0, 1_500.0, 5.0),
    }


def demonstrate_rates_and_annuities() -> dict[str, float]:
    """Compare rate conversions and annuity valuations."""
    return {
        "effective_from_nominal": nominal_to_effective_rate(0.06, 12),
        "effective_from_continuous": continuous_to_effective_rate(0.058),
        "semiannual_to_monthly_nominal": convert_nominal_frequency(0.06, 2, 12),
        "ordinary_annuity_pv": effective_annuity_present_value(100.0, 0.01, 24),
        "perpetuity_pv": perpetuity_present_value(10.0, 0.04),
        "geometric_gradient_pv": geometric_gradient_present_value(100.0, 0.05, 0.02, 10),
        "arithmetic_gradient_pv": arithmetic_gradient_present_value(100.0, 5.0, 0.05, 10),
    }


def demonstrate_bonds_and_cashflows() -> dict[str, float]:
    """Price bonds and irregular cash flows."""
    price, coupon, coupon_pv, redemption_pv = bond_price(1_000.0, 0.04, 1_000.0, 0.045, 8)
    _duration, convexity, modified_duration = bond_risk(1_000.0, 0.04, 1_000.0, 0.045, 8, 2)
    return {
        "bond_price": price,
        "periodic_coupon": coupon,
        "coupon_pv": coupon_pv,
        "redemption_pv": redemption_pv,
        "yield_from_price": bond_yield(price, 1_000.0, 0.04, 1_000.0, 8),
        "modified_duration": modified_duration,
        "convexity": convexity,
        "irregular_cashflow_pv": present_value_of_irregular_cashflows(
            [100, 150, 1_200], [0.5, 1.0, 2.0], 0.05
        ),
    }


def demonstrate_corporate_finance() -> dict[str, float]:
    """Run CAPM, WACC, DCF, and simple equity valuation examples."""
    dcf = dcf_valuation(100.0, 0.06, 0.025, 0.09, 5, 250.0, 50.0)
    matrix = dcf_sensitivity_matrix([100, 106, 112], [0.02, 0.025], [0.08, 0.09], 250.0, 50.0)
    return {
        "capm_cost_of_equity": capm_cost_of_equity(0.04, 1.2, 0.09),
        "wacc": weighted_average_cost_of_capital(0.10, 0.7, 0.05, 0.25),
        "dcf_equity_value_per_share": float(dcf["price_per_share"]),
        "dcf_sensitivity_low_discount": float(matrix[0, 0]),
        "gordon_value": gordon_shapiro_valuation(2.0, 0.09, 0.03),
        "multiple_value": multiples_valuation(8.0, 20.0),
    }


def demonstrate_portfolio_primitives() -> dict[str, float]:
    """Compute mean, covariance, Sharpe, and optimized weights from prices."""
    prices = sample_prices()
    returns = simple_returns_from_prices(prices)
    mean_returns = annualized_mean_returns_from_returns(returns)
    covariance = annualized_covariance_from_returns(returns)
    weights = maximum_sharpe_weights(
        mean_returns.to_numpy(), covariance.to_numpy(), risk_free_rate=0.02
    )
    return {
        "equal_weight_alpha": float(equal_weight(3)[0]),
        "max_sharpe_alpha_weight": float(weights[0]),
        "portfolio_volatility": portfolio_volatility(weights, covariance.to_numpy()),
        "portfolio_sharpe": portfolio_sharpe(
            float(np.dot(weights, mean_returns.to_numpy())),
            portfolio_volatility(weights, covariance.to_numpy()),
            risk_free_rate=0.02,
        ),
    }


def demonstrate_risk_and_loans() -> dict[str, float]:
    """Compute loan schedule, parametric VaR diagnostics, and Monte Carlo VaR/CVaR."""
    schedule = amortization_schedule(10_000.0, 0.01, 12)
    var_value, z_score, _, _ = parametric_var(0.08, 0.20, 1_000_000.0, 0.95, 10)
    mc_var, mc_cvar = monte_carlo_var_cvar(0.08, 0.20, 1_000_000.0, 0.95, 10, simulations=5_000)
    return {
        "first_payment": float(schedule.iloc[0]["Interest"] + schedule.iloc[0]["Amortization"]),
        "parametric_var": var_value,
        "parametric_z_score": z_score,
        "monte_carlo_var": mc_var,
        "monte_carlo_cvar": mc_cvar,
    }


def demonstrate_beta_alpha() -> dict[str, float]:
    """Estimate beta and alpha from synthetic returns."""
    prices = sample_prices()
    returns = prices.pct_change().dropna()
    regression = beta_alpha_from_returns(returns["ALPHA"], returns["BETA"], risk_free_rate=0.02)
    return {"beta": float(regression["beta"]), "alpha": float(regression["alpha"])}


def run() -> None:
    """Run all financial-mathematics demonstrations."""
    print_mapping("Time value of money", demonstrate_time_value())
    print_mapping("Rates and annuities", demonstrate_rates_and_annuities())
    print_mapping("Bonds and cash flows", demonstrate_bonds_and_cashflows())
    print_mapping("Corporate finance", demonstrate_corporate_finance())
    print_mapping("Portfolio primitives", demonstrate_portfolio_primitives())
    print_mapping("Risk and loans", demonstrate_risk_and_loans())
    print_mapping("Beta and alpha", demonstrate_beta_alpha())


if __name__ == "__main__":
    run()
