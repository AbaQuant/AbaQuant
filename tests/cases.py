from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

import abaquant as quact


def sample_bonds() -> list[dict[str, Any]]:
    return [
        {
            "name": "A",
            "rating_idx": 0,
            "values": np.linspace(100.0, 80.0, 18),
        },
        {
            "name": "B",
            "rating_idx": 8,
            "values": np.linspace(90.0, 50.0, 18),
        },
    ]


def sample_distribution() -> list[tuple[float, float]]:
    return quact.independent_distribution(sample_bonds(), quact.DEFAULT_TM)


def sample_simulations() -> np.ndarray:
    return quact.gaussian_copula_simulation(
        [{"rating_idx": 0, "values": np.arange(18, dtype=float)}],
        quact.DEFAULT_TM,
        np.eye(1),
        n_sims=5,
        seed=11,
    )


def sample_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "A": [100.0, 101.0, 102.5, 101.8],
            "B": [50.0, 50.5, 51.0, 52.0],
        }
    )


def simple_expected_returns(prices: pd.DataFrame) -> pd.Series:
    return pd.Series({"A": 0.08, "B": 0.12})


def simple_covariance(prices: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([[0.04, 0.01], [0.01, 0.09]], index=prices.columns, columns=prices.columns)


def optima_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 105.0, 106.0, 106.5, 107.0],
            "BBB": [50.0, 50.2, 50.6, 50.4, 50.9, 51.4, 51.1, 51.8, 52.0, 52.5],
            "CCC": [80.0, 79.5, 80.2, 80.8, 81.0, 81.4, 81.9, 82.3, 82.0, 82.6],
        },
        index=pd.date_range("2024-01-02", periods=10, freq="B"),
    )


def optima_returns() -> pd.DataFrame:
    return quact.get_returns(optima_prices())


def optima_weights() -> np.ndarray:
    return np.array([0.5, 0.3, 0.2])


def optima_return_series() -> pd.Series:
    return quact.portfolio_returns(optima_returns(), optima_weights())


def optima_backtest_prices() -> pd.DataFrame:
    idx = pd.date_range("2023-01-02", periods=90, freq="B")
    steps = np.arange(len(idx), dtype=float)
    return pd.DataFrame(
        {
            "AAA": 100.0 * (1.001 + 0.004 * np.sin(steps / 5.0)).cumprod(),
            "BBB": 80.0 * (1.0005 + 0.003 * np.cos(steps / 7.0)).cumprod(),
            "CCC": 60.0 * (1.0008 + 0.002 * np.sin(steps / 9.0)).cumprod(),
        },
        index=idx,
    )


def optima_stress_prices() -> pd.DataFrame:
    idx = pd.date_range("2020-02-19", periods=55, freq="B")
    steps = np.arange(len(idx), dtype=float)
    shock = np.where(steps < 16, 1 - 0.015 * steps, 0.76 + 0.006 * (steps - 16))
    return pd.DataFrame(
        {
            "AAA": 100.0 * shock,
            "BBB": 75.0 * (shock * 0.9 + 0.1),
            "CCC": 120.0 * (shock * 0.8 + 0.2),
        },
        index=idx,
    )


CASES: dict[str, Callable[[], Any]] = {
    "crr_binomial_tree": lambda: quact.crr_binomial_tree(100, 100, 0.05, 0.2, 1, 3, True, False, 0),
    "down_and_out_barrier_option": lambda: quact.down_and_out_barrier_option(
        100, 95, 80, 1, 0.05, 0.2, 0.01, "call"
    ),
    "binomial_tree": lambda: quact.binomial_tree(100, 100, 1, 0.05, 0.2, 3, 0, "call", False),
    "black_76": lambda: quact.black_76(100, 100, 0.05, 0.2, 1, True),
    "black_scholes": lambda: quact.black_scholes(100, 100, 0.05, 0.2, 1, True, 0),
    "vanilla_intrinsic_value": lambda: quact.vanilla_intrinsic_value(110.0, 100.0, True),
    "vanilla_extrinsic_value": lambda: quact.vanilla_extrinsic_value(14.0, 110.0, 100.0, True),
    "bond_values_per_rating": lambda: quact.bond_values_per_rating(
        1000, 0.05, 3, 1, 0.4, quact.DEFAULT_SPREADS
    ),
    "beta_alpha_from_returns": lambda: quact.beta_alpha_from_returns(
        pd.Series([0.01, -0.005, 0.012, 0.004]),
        pd.Series([0.008, -0.003, 0.01, 0.002]),
        0.04,
    ),
    "binomial_probabilities_log": lambda: quact.binomial_probabilities_log(
        3, np.array([0.1, 0.2]), 3
    ),
    "build_transition_matrix": lambda: quact.build_transition_matrix(nr_treatment="redistribute"),
    "bsm_d1_d2": lambda: quact.bsm_d1_d2(100, 100, 0.05, 0.01, 0.2, 1),
    "annualized_return": lambda: quact.annualized_return(optima_return_series()),
    "annualized_volatility": lambda: quact.annualized_volatility(optima_return_series()),
    "calculate_greeks": lambda: quact.calculate_greeks(100, 100, 0.05, 0.2, 1, True, 0),
    "option_payoff_leg": lambda: quact.option_payoff_leg(
        "call", 1, np.array([90, 100, 110]), 100, 2
    ),
    "monte_carlo_var_cvar": lambda: quact.monte_carlo_var_cvar(
        0.1, 0.2, 1000, 0.95, 10, simulations=1000, seed=7
    ),
    "parametric_var": lambda: quact.parametric_var(0.1, 0.2, 1000, 0.95, 10),
    "present_value_of_dividends": lambda: quact.present_value_of_dividends(
        10, 4, 0.08, 1, "Continuous"
    ),
    "present_value_of_irregular_cashflows": lambda: quact.present_value_of_irregular_cashflows(
        [100, 200, 300], [0.5, 1, 2], 0.08, "Continuous"
    ),
    "calmar_ratio": lambda: quact.calmar_ratio(optima_return_series()),
    "calibrate_heston": lambda: quact.calibrate_heston(
        100,
        1,
        0.05,
        0.0,
        np.array([90.0, 100.0, 110.0]),
        np.array([0.24, 0.20, 0.22]),
        max_iter=2,
    ),
    "calibrate_sabr": lambda: quact.calibrate_sabr(
        100.0,
        1.0,
        np.array([90.0, 100.0, 110.0]),
        np.array([0.24, 0.20, 0.22]),
        beta=0.5,
        max_iter=2,
    ),
    "capm_cost_of_equity": lambda: quact.capm_cost_of_equity(0.04, 1.2, 0.1),
    "calculate_credit_proxy_metrics": lambda: quact.calculate_credit_proxy_metrics(
        quact.CreditAnalysisInputs(
            balance_sheet=quact.BalanceSheetInputs(
                total_debt=100.0,
                total_equity=250.0,
                current_assets=180.0,
                current_liabilities=75.0,
            ),
            income_statement=quact.IncomeStatementInputs(
                ebit=60.0,
                ebitda=75.0,
                interest_expense=8.0,
                net_income=42.0,
            ),
            cash_flow_statement=quact.CashFlowInputs(operating_cash_flow=50.0),
        )
    ).as_dict(),
    "compute_all_metrics": lambda: quact.compute_all_metrics(optima_return_series(), rf=0.03),
    "compare_all_models": lambda: quact.compare_all_models(
        100,
        100,
        1,
        0.05,
        0.2,
        heston_params={"v0": 0.04, "kappa": 2.0, "theta": 0.04, "xi": 0.3, "rho": -0.5},
        merton_params={"lam": 0.5, "mu_j": -0.1, "sigma_j": 0.2},
        crr_N=5,
    ),
    "conditional_default_probability": lambda: quact.conditional_default_probability(
        1, 0.02, 0.3, np.array([-1.0, 0.0, 1.0])
    ),
    "conditional_drawdown_at_risk": lambda: quact.conditional_drawdown_at_risk(
        optima_return_series()
    ),
    "cumulative_returns": lambda: quact.cumulative_returns(optima_return_series()),
    "cvar_historical": lambda: quact.cvar_historical(optima_return_series()),
    "dcf_sensitivity_matrix": lambda: quact.dcf_sensitivity_matrix(
        [100, 110, 121], [0.02, 0.03], [0.08, 0.09], 50, 10
    ),
    "dcf_valuation": lambda: quact.dcf_valuation(100, 0.1, 0.03, 0.08, 3, 50, 10),
    "decompose_periods": lambda: quact.decompose_periods(2.345),
    "downside_deviation": lambda: quact.downside_deviation(optima_return_series()),
    "drawdown_series": lambda: quact.drawdown_series(optima_return_series()),
    "equal_weight_portfolio": lambda: quact.equal_weight_portfolio(
        ["A", "B"], np.array([0.08, 0.12]), np.array([[0.04, 0.01], [0.01, 0.09]]), 0.03
    ),
    "evaluate_custom_portfolio": lambda: quact.evaluate_custom_portfolio(
        sample_prices(), {"A": 0.6, "B": 0.4}, simple_expected_returns, simple_covariance
    ),
    "expected_tranche_survival_given_factor": lambda: quact.expected_tranche_survival_given_factor(
        1, 0.02, 0.3, 10, 0.4, 0.03, 0.06, np.array([-1.0, 0.0, 1.0])
    ),
    "expected_value_and_sigma": lambda: quact.expected_value_and_sigma(
        sample_bonds(), quact.DEFAULT_TM
    ),
    "evaluate_custom_portfolio_from_prices": lambda: quact.evaluate_custom_portfolio_from_prices(
        optima_prices(),
        {"AAA": 0.5, "BBB": 0.3, "CCC": 0.2},
    ),
    "forward_price_with_yield": lambda: quact.forward_price_with_yield(
        100, 0.05, 0.02, 1, "Continuous"
    ),
    "forward_price": lambda: quact.forward_price(100, 0.05, 1, 0.02),
    "fra": lambda: quact.fra(0.04, 0.05, 1, 2, 1_000_000, 0.055),
    "gauss_hermite_normal": lambda: quact.gauss_hermite_normal(3),
    "gaussian_copula_simulation": sample_simulations,
    "reinvestment_table": lambda: quact.reinvestment_table(1000, 0.12, 2),
    "get_rate_curve": lambda: quact.get_rate_curve(
        provider=quact.ManualRateProvider({1.0: 0.04, 2.0: 0.05})
    ).zero_rate(1.5),
    "get_returns": optima_returns,
    "bsm_greeks": lambda: quact.bsm_greeks("Yield", 100, 100, 1, 0.05, 0.2, 0.01),
    "second_order_greeks": lambda: quact.second_order_greeks(100, 100, 0.05, 0.01, 0.2, 1, True),
    "implied_volatility_bsm": lambda: quact.implied_volatility_bsm(
        quact.black_scholes(100, 100, 0.05, 0.2, 1), 100, 100, 0.05, 1
    ),
    "independent_distribution": sample_distribution,
    "intrinsic_time_value": lambda: quact.intrinsic_time_value(12.0, 100.0, 95.0, "call"),
    "bsm_d1_d2_summary": lambda: quact.bsm_d1_d2_summary(100.0, 100.0, 1.0, 0.05, 0.2, 0.01),
    "crr_tree_parameters": lambda: quact.crr_tree_parameters(1.0, 0.05, 0.2, 0.01, 200),
    "distribution_moments": lambda: quact.distribution_moments(
        np.array([-0.02, 0.01, 0.03, -0.01])
    ),
    "excess_kurtosis": lambda: quact.excess_kurtosis(np.array([-0.02, 0.01, 0.03, -0.01])),
    "forward_price_continuous": lambda: quact.forward_price_continuous(100.0, 0.05, 0.01, 1.0),
    "historical_mean_returns": lambda: quact.historical_mean_returns(optima_prices()),
    "hierarchical_risk_parity": lambda: quact.hierarchical_risk_parity(
        optima_returns().cov(),
        optima_returns().corr(),
        ["AAA", "BBB", "CCC"],
    ),
    "simple_returns_from_prices": lambda: quact.simple_returns_from_prices(optima_prices()),
    "log_returns_from_prices": lambda: quact.log_returns_from_prices(optima_prices()),
    "annualized_mean_returns_from_returns": lambda: quact.annualized_mean_returns_from_returns(
        optima_returns()
    ),
    "annualized_covariance_from_returns": lambda: quact.annualized_covariance_from_returns(
        optima_returns()
    ),
    "iv_rv_spread": lambda: quact.iv_rv_spread(
        np.array([0.22, 0.24, 0.21]), np.array([0.18, 0.20, 0.19])
    ),
    "log_return_volatility": lambda: quact.log_return_volatility(optima_prices()["AAA"]),
    "log_binomial_coefficient": lambda: quact.log_binomial_coefficient(10, 3),
    "markowitz_frontier": lambda: quact.markowitz_frontier(
        optima_returns().mean() * 252,
        optima_returns().cov() * 252,
        n_points=5,
    ),
    "max_sharpe_portfolio": lambda: quact.max_sharpe_portfolio(
        ["AAA", "BBB", "CCC"],
        quact.historical_mean_returns(optima_prices()).values,
        quact.sample_covariance(optima_prices()).values,
        0.03,
    ),
    "max_drawdown": lambda: quact.max_drawdown(optima_return_series()),
    "merton_jump_statistics": lambda: quact.merton_jump_statistics(1.2, -0.1, 0.2, 0.15),
    "min_variance_portfolio": lambda: quact.min_variance_portfolio(
        ["AAA", "BBB", "CCC"],
        quact.historical_mean_returns(optima_prices()).values,
        quact.sample_covariance(optima_prices()).values,
        0.03,
    ),
    "monte_carlo_portfolio_cloud": lambda: quact.monte_carlo_portfolio_cloud(
        np.array([0.08, 0.12]),
        np.array([[0.04, 0.01], [0.01, 0.09]]),
        0.03,
        n_simulations=5,
        seed=11,
    ),
    "monte_carlo_portfolios": lambda: quact.monte_carlo_portfolios(
        optima_returns().mean() * 252,
        optima_returns().cov() * 252,
        n_portfolios=6,
        rf=0.03,
        seed=11,
    ),
    "monte_carlo_bsm": lambda: quact.monte_carlo_bsm(
        100,
        100,
        1,
        0.05,
        0.2,
        n_paths=1000,
        seed=11,
    ),
    "mvsk_neg_utility": lambda: quact.mvsk_neg_utility(
        np.array([0.6, 0.4]), sample_prices().pct_change().dropna().values
    ),
    "mvsk_portfolio": lambda: quact.mvsk_portfolio(
        ["A", "B"],
        np.array([0.08, 0.12]),
        np.array([[0.04, 0.01], [0.01, 0.09]]),
        sample_prices().pct_change().dropna().values,
        0.03,
    ),
    "periods_for_annuity_future_value": lambda: quact.periods_for_annuity_future_value(
        1268.2503013196977, 100, 0.01
    ),
    "periods_for_annuity_present_value": lambda: quact.periods_for_annuity_present_value(
        1125.5077473484641, 100, 0.01
    ),
    "periods_for_arithmetic_gradient_future_value": lambda: (
        quact.periods_for_arithmetic_gradient_future_value(660, 100, 5, 0.01)
    ),
    "periods_for_arithmetic_gradient_present_value": lambda: (
        quact.periods_for_arithmetic_gradient_present_value(560, 100, 5, 0.01)
    ),
    "periods_for_geometric_gradient_future_value": lambda: (
        quact.periods_for_geometric_gradient_future_value(700, 100, 0.02, 0.01)
    ),
    "periods_for_geometric_gradient_present_value": lambda: (
        quact.periods_for_geometric_gradient_present_value(560, 100, 0.02, 0.01)
    ),
    "number_of_periods": lambda: quact.number_of_periods(1000, 1469.3280768, 0.08),
    "simple_chooser_option": lambda: quact.simple_chooser_option(100, 100, 0.5, 1, 0.05, 0.2, 0.01),
    "perpetual_option": lambda: quact.perpetual_option(120, 100, 0.05, 0.2, True),
    "arithmetic_asian_options": lambda: quact.arithmetic_asian_options(
        100, 100, 1, 0.05, 0.2, 0, "call"
    ),
    "geometric_asian_options": lambda: quact.geometric_asian_options(
        100, 100, 1, 0.05, 0.2, 0, "call"
    ),
    "asset_or_nothing_options": lambda: quact.asset_or_nothing_options(
        100, 100, 1, 0.05, 0.2, 0, "call"
    ),
    "bsm_option_prices": lambda: quact.bsm_option_prices("Yield", 100, 100, 1, 0.05, 0.2, 0.01),
    "cash_or_nothing_options": lambda: quact.cash_or_nothing_options(
        100, 100, 10, 1, 0.05, 0.2, 0, "call"
    ),
    "compound_options": lambda: quact.compound_options(
        100, 5, 100, 0.5, 1, 0.05, 0.2, 0.01, "call_on_call"
    ),
    "gap_options": lambda: quact.gap_options(100, 95, 100, 1, 0.05, 0.2, 0.01, "call"),
    "exchange_options": lambda: quact.exchange_options(95, 100, 0.01, 0.02, 0.2, 0.25, 0.3, 1),
    "floating_lookback_options": lambda: quact.floating_lookback_options(
        100, 90, 1, 0.05, 0.2, 0.01, "call"
    ),
    "optimize_portfolio_strategies": lambda: quact.optimize_portfolio_strategies(
        optima_prices(),
        risk_free_rate=0.03,
        n_simulations=5,
        seed=11,
    ),
    "exotic_payoff_leg": lambda: quact.exotic_payoff_leg(
        "gap_call", 1, np.array([90, 100, 110]), {"K1": 100, "K2": 95}, 2
    ),
    "strategy_profile": lambda: quact.strategy_profile(
        100,
        [{"option_type": "call", "position": 1, "strike": 100, "premium": 2}],
        points=5,
    ),
    "bond_price": lambda: quact.bond_price(1000, 0.08, 40, 0.09, 10),
    "simple_forward_price": lambda: quact.simple_forward_price(100, 0.05, 1),
    "commodity_forward_price": lambda: quact.commodity_forward_price(100, 0.05, 0.01, 1),
    "forward_price_with_continuous_dividend": lambda: quact.forward_price_with_continuous_dividend(
        100, 0.05, 0.02, 1
    ),
    "forward_price_with_discrete_dividends": lambda: quact.forward_price_with_discrete_dividends(
        100, 0.05, 1, 3
    ),
    "fx_forward_price": lambda: quact.fx_forward_price(20, 0.08, 0.04, 1),
    "portfolio_return": lambda: quact.portfolio_return(
        np.array([0.6, 0.4]), np.array([0.08, 0.12])
    ),
    "portfolio_variance": lambda: quact.portfolio_variance(
        np.array([0.6, 0.4]), np.array([[0.04, 0.01], [0.01, 0.09]])
    ),
    "equal_weight": lambda: quact.equal_weight(3),
    "minimum_variance_weights": lambda: quact.minimum_variance_weights(
        np.array([[0.04, 0.01], [0.01, 0.09]])
    ),
    "maximum_sharpe_weights": lambda: quact.maximum_sharpe_weights(
        np.array([0.08, 0.12]), np.array([[0.04, 0.01], [0.01, 0.09]]), 0.03
    ),
    "portfolio_returns": lambda: quact.portfolio_returns(optima_returns(), optima_weights()),
    "portfolio_sharpe": lambda: quact.portfolio_sharpe(0.1, 0.2, 0.03),
    "portfolio_volatility": lambda: quact.portfolio_volatility(
        np.array([0.6, 0.4]), np.array([[0.04, 0.01], [0.01, 0.09]])
    ),
    "parity_check": lambda: quact.parity_check(
        10.450583572185565, 5.573526022256971, 100, 100, 1, 0.05
    ),
    "cds_fair_spread": lambda: quact.cds_fair_spread(4.0, 0.2, 0.35),
    "required_equity_return": lambda: quact.required_equity_return(5, 100, 0.03),
    "bond_risk": lambda: quact.bond_risk(1000, 0.08, 40, 0.09, 10, 2),
    "realized_vol": lambda: quact.realized_vol(
        np.array([100.0, 101.0, 100.5, 102.0, 103.0, 102.5]), window=3
    ),
    "risk_parity_objective": lambda: quact.risk_parity_objective(
        np.array([0.5, 0.5]), np.array([[0.04, 0.01], [0.01, 0.09]])
    ),
    "risk_parity_portfolio": lambda: quact.risk_parity_portfolio(
        ["A", "B"], np.array([0.08, 0.12]), np.array([[0.04, 0.01], [0.01, 0.09]]), 0.03
    ),
    "run_all_scenarios": lambda: quact.run_all_scenarios(
        optima_stress_prices(),
        pd.Series(optima_weights(), index=["AAA", "BBB", "CCC"]),
    ),
    "run_backtest": lambda: quact.run_backtest(
        optima_backtest_prices(),
        "Equal Weight (1/N)",
        rebalance_freq="monthly",
        lookback_days=21,
        initial_capital=1000.0,
    ),
    "run_rebalanced_backtest": lambda: quact.run_rebalanced_backtest(
        optima_returns(),
        weights="equal_weight",
        rebalance="monthly",
        transaction_cost_bps=5.0,
        initial_capital=1000.0,
    ).summary(),
    "run_stress_test": lambda: quact.run_stress_test(
        optima_stress_prices(),
        pd.Series(optima_weights(), index=["AAA", "BBB", "CCC"]),
        "COVID-19 (2020)",
        min_coverage=0.1,
    ),
    "scale_var_cvar": lambda: quact.scale_var_cvar(
        quact.var_cvar_parametric(1000, 25, (0.95,)), (0.95,)
    ),
    "sample_covariance": lambda: quact.sample_covariance(optima_prices()),
    "sharpe_ratio": lambda: quact.sharpe_ratio(optima_return_series(), rf=0.03),
    "simulate_gbm_paths": lambda: quact.simulate_gbm_paths(
        100.0, 1.0, 0.05, 0.2, 0.01, n_paths=2, n_steps=3, seed=11
    ),
    "simulate_merton_paths": lambda: quact.simulate_merton_paths(
        100.0, 1.0, 0.05, 0.15, 0.01, 1.2, -0.1, 0.2, n_paths=2, n_steps=3, seed=11
    ),
    "simulate_vg_nig_returns": lambda: quact.simulate_vg_nig_returns(
        1.0, 0.2, -0.05, 0.2, 15.0, -5.0, 1.5, 0.2, n_sim=5, seed=11
    ),
    "sortino_ratio": lambda: quact.sortino_ratio(optima_return_series(), rf=0.03),
    "solve_slsqp_weights": lambda: quact.solve_slsqp_weights(
        lambda weights: float(np.sum((weights - np.array([0.2, 0.3, 0.5])) ** 2)),
        3,
        0.0,
        1.0,
    ),
    "cds_probability_table": lambda: quact.cds_probability_table(0.02, 3),
    "cds_premium_leg_table": lambda: quact.cds_premium_leg_table(0.02, 0.05, 3),
    "cds_accrued_premium_table": lambda: quact.cds_accrued_premium_table(0.02, 0.05, 3),
    "cds_contingent_leg_table": lambda: quact.cds_contingent_leg_table(0.02, 0.05, 3, 0.4),
    "amortization_schedule": lambda: quact.amortization_schedule(1000, 0.01, 3),
    "effective_to_nominal_rate": lambda: quact.effective_to_nominal_rate(0.12682503013196977, 12),
    "continuous_to_effective_rate": lambda: quact.continuous_to_effective_rate(0.12),
    "continuous_to_nominal_rate": lambda: quact.continuous_to_nominal_rate(0.12, 12),
    "nominal_to_effective_rate": lambda: quact.nominal_to_effective_rate(0.12, 12),
    "nominal_to_continuous_rate": lambda: quact.nominal_to_continuous_rate(0.12, 12),
    "convert_nominal_frequency": lambda: quact.convert_nominal_frequency(0.12, 12, 4),
    "rate_of_return": lambda: quact.rate_of_return(1000, 1469.3280768, 5),
    "bond_yield": lambda: quact.bond_yield(950, 1000, 0.08, 40, 10),
    "thresholds_per_bond": lambda: quact.thresholds_per_bond(0, quact.DEFAULT_TM),
    "theoretical_mc_error": lambda: quact.theoretical_mc_error(
        10.0, 0.2, 1.0, np.array([1000, 4000])
    ),
    "validate_tickers": lambda: quact.validate_tickers([" aapl ", "MSFT", "AAPL", "", "btc-usd"]),
    "forward_contract_value": lambda: quact.forward_contract_value(
        100, 102, 0.05, 0.02, 0.5, "Long", "Continuous"
    ),
    "live_forward_value": lambda: quact.live_forward_value(100, 102, 0.05, 0.02, 0.5),
    "future_value": lambda: quact.future_value(1000, 0.08, 5),
    "continuous_future_value": lambda: quact.continuous_future_value(1000, 0.08, 5),
    "present_value": lambda: quact.present_value(1469.3280768, 0.08, 5),
    "continuous_present_value": lambda: quact.continuous_present_value(1500, 0.08, 5),
    "gordon_shapiro_valuation": lambda: quact.gordon_shapiro_valuation(5, 0.12, 0.03),
    "multiples_valuation": lambda: quact.multiples_valuation(12, 8),
    "var_cvar_from_distribution": lambda: quact.var_cvar_from_distribution(
        sample_distribution(), (0.95,)
    ),
    "var_cvar_from_simulations": lambda: quact.var_cvar_from_simulations(
        sample_simulations(), (0.95,)
    ),
    "var_cvar_parametric": lambda: quact.var_cvar_parametric(1000, 25, (0.95,)),
    "var_historical": lambda: quact.var_historical(optima_return_series()),
    "value_cds": lambda: quact.value_cds(0.02, 0.05, 3, 0.4),
    "value_tranche": lambda: quact.value_tranche(
        0.02, 0.3, 10, 0.4, 0.03, 0.06, 0.05, [1, 2], *quact.gauss_hermite_normal(5)
    ),
    "weighted_average_cost_of_capital": lambda: quact.weighted_average_cost_of_capital(
        0.12, 0.6, 0.06, 0.3
    ),
    "continuous_annuity_future_value": lambda: quact.continuous_annuity_future_value(1200, 0.08, 3),
    "effective_annuity_future_value": lambda: quact.effective_annuity_future_value(100, 0.01, 12),
    "nominal_annuity_future_value": lambda: quact.nominal_annuity_future_value(
        100, 0.12, 12, 12, 1
    ),
    "arithmetic_gradient_future_value": lambda: quact.arithmetic_gradient_future_value(
        100, 5, 0.01, 6
    ),
    "geometric_gradient_future_value": lambda: quact.geometric_gradient_future_value(
        100, 0.02, 0.01, 6
    ),
    "continuous_annuity_present_value": lambda: quact.continuous_annuity_present_value(
        1200, 0.08, 3
    ),
    "effective_annuity_present_value": lambda: quact.effective_annuity_present_value(100, 0.01, 12),
    "nominal_annuity_present_value": lambda: quact.nominal_annuity_present_value(
        100, 0.12, 12, 12, 1
    ),
    "arithmetic_gradient_present_value": lambda: quact.arithmetic_gradient_present_value(
        100, 5, 0.01, 6
    ),
    "geometric_gradient_present_value": lambda: quact.geometric_gradient_present_value(
        100, 0.02, 0.01, 6
    ),
    "perpetuity_present_value": lambda: quact.perpetuity_present_value(100, 0.05),
}

CASES.update(
    {
        "amortization_schedule": lambda: quact.amortization_schedule(1000, 0.01, 3),
        "arithmetic_asian_options": CASES["arithmetic_asian_options"],
        "arithmetic_gradient_future_value": lambda: quact.arithmetic_gradient_future_value(
            100, 5, 0.01, 6
        ),
        "arithmetic_gradient_present_value": lambda: quact.arithmetic_gradient_present_value(
            100, 5, 0.01, 6
        ),
        "asset_or_nothing_options": CASES["asset_or_nothing_options"],
        "bond_price": lambda: quact.bond_price(1000, 0.08, 40, 0.09, 10),
        "bond_risk": lambda: quact.bond_risk(1000, 0.08, 40, 0.09, 10, 2),
        "bond_yield": lambda: quact.bond_yield(950, 1000, 0.08, 40, 10),
        "bsm_greeks": CASES["bsm_greeks"],
        "bsm_option_prices": CASES["bsm_option_prices"],
        "calculate_greeks": lambda: quact.calculate_greeks(100, 100, 0.05, 0.2, 1, True, 0.01),
        "cash_or_nothing_options": CASES["cash_or_nothing_options"],
        "cds_accrued_premium_table": lambda: quact.cds_accrued_premium_table(0.02, 0.05, 3),
        "cds_contingent_leg_table": lambda: quact.cds_contingent_leg_table(0.02, 0.05, 3, 0.4),
        "cds_fair_spread": lambda: quact.cds_fair_spread(4.0, 0.2, 0.35),
        "cds_premium_leg_table": lambda: quact.cds_premium_leg_table(0.02, 0.05, 3),
        "cds_probability_table": lambda: quact.cds_probability_table(0.02, 3),
        "commodity_forward_price": lambda: quact.commodity_forward_price(100, 0.05, 0.01, 1),
        "compound_options": CASES["compound_options"],
        "continuous_annuity_future_value": lambda: quact.continuous_annuity_future_value(
            1200, 0.08, 3
        ),
        "continuous_annuity_present_value": lambda: quact.continuous_annuity_present_value(
            1200, 0.08, 3
        ),
        "continuous_future_value": lambda: quact.continuous_future_value(1000, 0.08, 5),
        "continuous_present_value": lambda: quact.continuous_present_value(1500, 0.08, 5),
        "continuous_to_effective_rate": lambda: quact.continuous_to_effective_rate(0.12),
        "continuous_to_nominal_rate": lambda: quact.continuous_to_nominal_rate(0.12, 12),
        "convert_nominal_frequency": lambda: quact.convert_nominal_frequency(0.12, 12, 4),
        "crr_binomial_tree": lambda: quact.crr_binomial_tree(100, 100, 0.05, 0.2, 1, 3),
        "decompose_periods": lambda: quact.decompose_periods(2.345),
        "down_and_out_barrier_option": CASES["down_and_out_barrier_option"],
        "effective_annuity_future_value": lambda: quact.effective_annuity_future_value(
            100, 0.01, 12
        ),
        "effective_annuity_present_value": lambda: quact.effective_annuity_present_value(
            100, 0.01, 12
        ),
        "effective_to_nominal_rate": lambda: quact.effective_to_nominal_rate(
            0.12682503013196977, 12
        ),
        "exchange_options": CASES["exchange_options"],
        "exotic_payoff_leg": CASES["exotic_payoff_leg"],
        "floating_lookback_options": CASES["floating_lookback_options"],
        "forward_contract_value": lambda: quact.forward_contract_value(100, 102, 0.05, 0.02, 0.5),
        "forward_price_with_continuous_dividend": lambda: (
            quact.forward_price_with_continuous_dividend(100, 0.05, 0.02, 1)
        ),
        "forward_price_with_discrete_dividends": lambda: (
            quact.forward_price_with_discrete_dividends(100, 0.05, 1, 3)
        ),
        "forward_price_with_yield": lambda: quact.forward_price_with_yield(100, 0.05, 0.02, 1),
        "future_value": lambda: quact.future_value(1000, 0.08, 5),
        "fx_forward_price": lambda: quact.fx_forward_price(20, 0.08, 0.04, 1),
        "gap_options": CASES["gap_options"],
        "geometric_asian_options": CASES["geometric_asian_options"],
        "geometric_gradient_future_value": lambda: quact.geometric_gradient_future_value(
            100, 0.02, 0.01, 6
        ),
        "geometric_gradient_present_value": lambda: quact.geometric_gradient_present_value(
            100, 0.02, 0.01, 6
        ),
        "gordon_shapiro_valuation": lambda: quact.gordon_shapiro_valuation(5, 0.12, 0.03),
        "live_forward_value": lambda: quact.live_forward_value(100, 102, 0.05, 0.02, 0.5),
        "monte_carlo_var_cvar": lambda: quact.monte_carlo_var_cvar(
            0.1, 0.2, 1000, 0.95, 10, simulations=1000, seed=7
        ),
        "multiples_valuation": lambda: quact.multiples_valuation(12, 8),
        "nominal_annuity_future_value": lambda: quact.nominal_annuity_future_value(
            100, 0.12, 12, 12, 1
        ),
        "nominal_annuity_present_value": lambda: quact.nominal_annuity_present_value(
            100, 0.12, 12, 12, 1
        ),
        "nominal_to_continuous_rate": lambda: quact.nominal_to_continuous_rate(0.12, 12),
        "nominal_to_effective_rate": lambda: quact.nominal_to_effective_rate(0.12, 12),
        "number_of_periods": lambda: quact.number_of_periods(1000, 1469.3280768, 0.08),
        "option_payoff_leg": lambda: quact.option_payoff_leg(
            "call", 1, np.array([90, 100, 110]), 100, 2
        ),
        "parametric_var": lambda: quact.parametric_var(0.1, 0.2, 1000, 0.95, 10),
        "periods_for_annuity_future_value": lambda: quact.periods_for_annuity_future_value(
            1268.2503013196977, 100, 0.01
        ),
        "periods_for_annuity_present_value": lambda: quact.periods_for_annuity_present_value(
            1125.5077473484641, 100, 0.01
        ),
        "periods_for_arithmetic_gradient_future_value": lambda: (
            quact.periods_for_arithmetic_gradient_future_value(660, 100, 5, 0.01)
        ),
        "periods_for_arithmetic_gradient_present_value": lambda: (
            quact.periods_for_arithmetic_gradient_present_value(560, 100, 5, 0.01)
        ),
        "periods_for_geometric_gradient_future_value": lambda: (
            quact.periods_for_geometric_gradient_future_value(700, 100, 0.02, 0.01)
        ),
        "periods_for_geometric_gradient_present_value": lambda: (
            quact.periods_for_geometric_gradient_present_value(560, 100, 0.02, 0.01)
        ),
        "perpetual_option": CASES["perpetual_option"],
        "perpetuity_present_value": lambda: quact.perpetuity_present_value(100, 0.05),
        "present_value": lambda: quact.present_value(1469.3280768, 0.08, 5),
        "present_value_of_dividends": lambda: quact.present_value_of_dividends(10, 4, 0.08, 1),
        "present_value_of_irregular_cashflows": lambda: quact.present_value_of_irregular_cashflows(
            [100, 200, 300], [0.5, 1, 2], 0.08
        ),
        "rate_of_return": lambda: quact.rate_of_return(1000, 1469.3280768, 5),
        "reinvestment_table": lambda: quact.reinvestment_table(1000, 0.12, 2),
        "required_equity_return": lambda: quact.required_equity_return(5, 100, 0.03),
        "second_order_greeks": lambda: quact.second_order_greeks(
            100, 100, 0.05, 0.01, 0.2, 1, True
        ),
        "simple_chooser_option": CASES["simple_chooser_option"],
        "simple_forward_price": lambda: quact.simple_forward_price(100, 0.05, 1),
        "strategy_profile": lambda: quact.strategy_profile(
            100,
            [{"option_type": "call", "position": 1, "strike": 100, "premium": 2}],
            points=5,
        ),
        "value_cds": lambda: quact.value_cds(0.02, 0.05, 3, 0.4),
        "value_tranche": lambda: quact.value_tranche(
            0.02, 0.3, 10, 0.4, 0.03, 0.06, 0.05, [1, 2], *quact.gauss_hermite_normal(5)
        ),
    }
)
