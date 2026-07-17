"""Credit-risk examples with grouped inputs and visual diagnostics."""

from __future__ import annotations

import numpy as np

import abaquant as aq
from _shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)
from _shared.sample_data import sample_credit_input_values


def build_credit_inputs() -> aq.CreditAnalysisInputs:
    """Build one complete grouped credit-analysis input object."""
    values = sample_credit_input_values()
    return aq.CreditAnalysisInputs(
        balance_sheet=aq.BalanceSheetInputs(
            total_debt=values["total_debt"],
            total_equity=values["total_equity"],
            current_assets=values["current_assets"],
            inventory=values["inventory"],
            current_liabilities=values["current_liabilities"],
            cash_and_cash_equivalents=values["cash_and_cash_equivalents"],
            total_assets=values["total_assets"],
            total_liabilities=values["total_liabilities"],
            retained_earnings=values["retained_earnings"],
            long_term_debt=values["long_term_debt"],
        ),
        income_statement=aq.IncomeStatementInputs(
            revenue=values["revenue"],
            gross_profit=values["gross_profit"],
            ebit=values["ebit"],
            ebitda=values["ebitda"],
            interest_expense=values["interest_expense"],
            net_income=values["net_income"],
        ),
        cash_flow_statement=aq.CashFlowInputs(operating_cash_flow=values["operating_cash_flow"]),
        prior_period=aq.PriorPeriodInputs(
            total_assets=values["previous_total_assets"],
            net_income=values["previous_net_income"],
            long_term_debt=values["previous_long_term_debt"],
            current_assets=values["previous_current_assets"],
            current_liabilities=values["previous_current_liabilities"],
            shares_outstanding=values["previous_shares_outstanding"],
            gross_profit=values["previous_gross_profit"],
            revenue=values["previous_revenue"],
        ),
        market_equity=aq.MarketEquityObservation(market_value_equity=600.0),
        historical_series=aq.CreditHistoricalSeries(
            earnings_history=(40.0, 46.0, 55.0, 60.0),
            leverage_history=(0.55, 0.49, 0.43, 0.40),
        ),
        reporting_currency="USD",
        reporting_period="FY2025",
    )


def compute_credit_proxy_summary() -> tuple[object, dict[str, object]]:
    """Calculate fundamental proxy metrics and select dashboard values."""
    assessment = aq.calculate_credit_proxy_metrics(build_credit_inputs())
    summary = {
        "synthetic_score": assessment.synthetic_credit_proxy_score,
        "synthetic_band": assessment.synthetic_credit_proxy_band,
        "debt_to_equity": assessment.metrics["debt_to_equity"],
        "current_ratio": assessment.metrics["current_ratio"],
        "altman_z_score": assessment.metrics["altman_z_score"],
        "piotroski_f_score": assessment.metrics["piotroski_f_score"],
    }
    return assessment, summary


def run_transition_and_valuation_examples() -> dict[str, object]:
    """Build transition, bond-valuation, and distribution examples."""
    transition_matrix = aq.build_transition_matrix()
    spreads = np.tile(np.linspace(0.01, 0.08, 5), (17, 1))
    values_by_rating = aq.bond_values_per_rating(100.0, 0.05, 5, 1, 0.40, spreads)
    bonds_data = [
        {"name": "Bond A", "rating_idx": 0, "values": values_by_rating},
        {"name": "Bond B", "rating_idx": 2, "values": values_by_rating * 0.95},
    ]
    distribution = aq.independent_distribution(bonds_data, transition_matrix)
    expected_values, moments = aq.expected_value_and_sigma(bonds_data, transition_matrix)
    return {
        "transition_shape": transition_matrix.shape,
        "aaa_bond_value": float(values_by_rating[0]),
        "distribution_states": len(distribution),
        "expected_value": moments["EV_port"],
        "sigma": moments["sigma_port"],
        "first_expected_value_record": expected_values[0],
    }


def run_cds_cdo_and_var_examples() -> dict[str, object]:
    """Value simple CDS/CDO cases and compute VaR/CVaR summaries."""
    cds = aq.value_cds(hazard_rate=0.03, discount_rate=0.04, maturity=5, recovery_rate=0.40)
    nodes, weights = aq.gauss_hermite_normal(10)
    tranche = aq.value_tranche(
        hazard_rate=0.03,
        rho=0.25,
        n=20,
        recovery_rate=0.40,
        attachment=0.03,
        detachment=0.07,
        risk_free_rate=0.04,
        periods=np.arange(1.0, 6.0),
        factor_nodes=nodes,
        weights=weights,
    )
    simulations = np.array([95.0, 97.0, 100.0, 102.0, 105.0, 90.0, 88.0])
    return {
        "cds_fair_spread": cds["spread"],
        "tranche_protection_leg": tranche["A"],
        "parametric_var_95": aq.var_cvar_parametric(100.0, 5.0)[0.95]["VaR"],
        "simulation_cvar_95": aq.var_cvar_from_simulations(simulations)[0.95]["CVaR"],
        "distribution_var_levels": sorted(
            aq.var_cvar_from_distribution(
                [(1.0, 0.25), (2.0, 0.25), (3.0, 0.25), (4.0, 0.25)]
            ).keys()
        ),
    }


def run_copula_example() -> dict[str, object]:
    """Simulate correlated rating transitions with a small portfolio."""
    transition_matrix = aq.build_transition_matrix()
    corr = np.array([[1.0, 0.25], [0.25, 1.0]])
    values = np.linspace(90.0, 105.0, transition_matrix.shape[1])
    bonds = [
        {"rating_idx": 0, "values": values},
        {"rating_idx": 1, "values": values * 0.96},
    ]
    simulation = aq.gaussian_copula_simulation(bonds, transition_matrix, corr, n_sims=500, seed=7)
    return {"simulation_shape": simulation.shape, "first_row_sum": float(simulation[0].sum())}


def create_credit_visualizations(assessment: object) -> dict[str, str]:
    """Create and save credit-assessment metric and score charts."""
    output_directory = configure_example_visuals(subdirectory="credit_risk")
    figures = {
        "credit_metrics": assessment.visualize(chart="metrics", filename="credit_metrics"),
        "credit_score": assessment.visualize(chart="score", filename="credit_score"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run credit-risk calculations and visualizations."""
    assessment, summary = compute_credit_proxy_summary()
    print_mapping("Fundamental credit proxy summary", summary)
    print_section("Transition and valuation examples")
    for key, value in run_transition_and_valuation_examples().items():
        print(f"{key}: {value}")
    print_section("CDS, CDO, and VaR examples")
    for key, value in run_cds_cdo_and_var_examples().items():
        print(f"{key}: {value}")
    print_mapping("Copula simulation", run_copula_example())
    try:
        print_mapping("Created credit figures", create_credit_visualizations(assessment))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
