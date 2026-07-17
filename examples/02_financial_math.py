"""Financial-mathematics examples with small reusable functions."""

from __future__ import annotations

import numpy as np

import abaquant as aq
from _shared.output import print_mapping
from _shared.sample_data import sample_prices


def demonstrate_time_value() -> dict[str, float]:
    """Compute basic accumulation, discounting, and realized return."""
    return {
        "future_value": aq.future_value(1_000.0, 0.06, 5.0),
        "present_value": aq.present_value(1_500.0, 0.06, 5.0),
        "required_periodic_return": aq.rate_of_return(1_000.0, 1_500.0, 5.0),
    }


def demonstrate_rates_and_annuities() -> dict[str, float]:
    """Compare rate conversions and annuity valuations."""
    return {
        "effective_from_nominal": aq.nominal_to_effective_rate(0.06, 12),
        "effective_from_continuous": aq.continuous_to_effective_rate(0.058),
        "semiannual_to_monthly_nominal": aq.convert_nominal_frequency(0.06, 2, 12),
        "ordinary_annuity_pv": aq.effective_annuity_present_value(100.0, 0.01, 24),
        "perpetuity_pv": aq.perpetuity_present_value(10.0, 0.04),
        "geometric_gradient_pv": aq.geometric_gradient_present_value(100.0, 0.05, 0.02, 10),
        "arithmetic_gradient_pv": aq.arithmetic_gradient_present_value(100.0, 5.0, 0.05, 10),
    }


def demonstrate_bonds_and_cashflows() -> dict[str, float]:
    """Price bonds and irregular cash flows."""
    price, coupon, coupon_pv, redemption_pv = aq.bond_price(1_000.0, 0.04, 1_000.0, 0.045, 8)
    _duration, convexity, modified_duration = aq.bond_risk(1_000.0, 0.04, 1_000.0, 0.045, 8, 2)
    return {
        "bond_price": price,
        "periodic_coupon": coupon,
        "coupon_pv": coupon_pv,
        "redemption_pv": redemption_pv,
        "yield_from_price": aq.bond_yield(price, 1_000.0, 0.04, 1_000.0, 8),
        "modified_duration": modified_duration,
        "convexity": convexity,
        "irregular_cashflow_pv": aq.present_value_of_irregular_cashflows(
            [100, 150, 1_200], [0.5, 1.0, 2.0], 0.05
        ),
    }


def demonstrate_corporate_finance() -> dict[str, float]:
    """Run CAPM, WACC, DCF, and simple equity valuation examples."""
    dcf = aq.dcf_valuation(100.0, 0.06, 0.025, 0.09, 5, 250.0, 50.0)
    matrix = aq.dcf_sensitivity_matrix([100, 106, 112], [0.02, 0.025], [0.08, 0.09], 250.0, 50.0)
    return {
        "capm_cost_of_equity": aq.capm_cost_of_equity(0.04, 1.2, 0.09),
        "wacc": aq.weighted_average_cost_of_capital(0.10, 0.7, 0.05, 0.25),
        "dcf_equity_value_per_share": float(dcf["price_per_share"]),
        "dcf_sensitivity_low_discount": float(matrix[0, 0]),
        "gordon_value": aq.gordon_shapiro_valuation(2.0, 0.09, 0.03),
        "multiple_value": aq.multiples_valuation(8.0, 20.0),
    }


def demonstrate_portfolio_primitives() -> dict[str, float]:
    """Compute mean, covariance, Sharpe, and optimized weights from prices."""
    prices = sample_prices()
    returns = aq.simple_returns_from_prices(prices)
    mean_returns = aq.annualized_mean_returns_from_returns(returns)
    covariance = aq.annualized_covariance_from_returns(returns)
    weights = aq.maximum_sharpe_weights(
        mean_returns.to_numpy(), covariance.to_numpy(), risk_free_rate=0.02
    )
    return {
        "equal_weight_alpha": float(aq.equal_weight(3)[0]),
        "max_sharpe_alpha_weight": float(weights[0]),
        "portfolio_volatility": aq.portfolio_volatility(weights, covariance.to_numpy()),
        "portfolio_sharpe": aq.portfolio_sharpe(
            float(np.dot(weights, mean_returns.to_numpy())),
            aq.portfolio_volatility(weights, covariance.to_numpy()),
            risk_free_rate=0.02,
        ),
    }


def demonstrate_risk_and_loans() -> dict[str, float]:
    """Compute loan schedule, parametric VaR diagnostics, and Monte Carlo VaR/CVaR."""
    schedule = aq.amortization_schedule(10_000.0, 0.01, 12)
    var_value, z_score, _, _ = aq.parametric_var(0.08, 0.20, 1_000_000.0, 0.95, 10)
    mc_var, mc_cvar = aq.monte_carlo_var_cvar(0.08, 0.20, 1_000_000.0, 0.95, 10, simulations=5_000)
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
    regression = aq.beta_alpha_from_returns(returns["ALPHA"], returns["BETA"], risk_free_rate=0.02)
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
