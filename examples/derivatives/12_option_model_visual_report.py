"""Build a compact option-model visual report with reusable functions."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import configure_example_visuals, print_mapping, reset_example_visuals


def build_report_models() -> dict[str, object]:
    """Create the models used by the visual report."""
    return {
        "black_scholes": aq.BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.22),
        "lattice": aq.CoxRossRubinsteinModel(100.0, 105.0, 1.0, 0.05, 0.22, number_of_steps=8),
        "sabr": aq.SABRVolatilityModel(100.0, 105.0, 1.0, 0.20, 0.7, -0.25, 0.45),
    }


def price_report_models(models: dict[str, object]) -> dict[str, float]:
    """Compute numerical values that correspond to the visual report."""
    return {
        "bsm_call_price": models["black_scholes"].call_price(),
        "bsm_put_price": models["black_scholes"].put_price(),
        "bsm_call_extrinsic_value": models["black_scholes"].extrinsic_value("call"),
        "bsm_call_moneyness": models["black_scholes"].moneyness(),
        "bsm_call_forward_moneyness": models["black_scholes"].forward_moneyness(),
        "bsm_call_break_even_price": models["black_scholes"].break_even_price("call"),
        "lattice_put_price": models["lattice"].put_price(),
        "sabr_atm_iv": models["sabr"].implied_vol(),
    }


def create_report_figures(models: dict[str, object]) -> dict[str, str]:
    """Save payoff, value-profile, tree, and smile charts."""
    output_directory = configure_example_visuals(subdirectory="option_model_report")
    figures = {
        "call_payoff": models["black_scholes"].visualize(
            chart="payoff", option_type="call", filename="01_call_payoff"
        ),
        "put_payoff": models["black_scholes"].visualize(
            chart="payoff", option_type="put", filename="02_put_payoff"
        ),
        "call_value_profile": models["black_scholes"].visualize(
            chart="price_profile", option_type="call", filename="03_call_value_profile"
        ),
        "call_extrinsic_profile": models["black_scholes"].visualize(
            chart="extrinsic_value", option_type="call", filename="04_call_extrinsic_profile"
        ),
        "call_greeks": models["black_scholes"].visualize(
            chart="greeks",
            option_type="call",
            greek_scale="standardized",
            filename="05_call_greeks",
        ),
        "call_price_surface": models["black_scholes"].visualize(
            chart="price_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="06_call_price_surface",
        ),
        "call_extrinsic_surface": models["black_scholes"].visualize(
            chart="extrinsic_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="07_call_extrinsic_surface",
        ),
        "call_delta_surface": models["black_scholes"].visualize(
            chart="delta_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="08_call_delta_surface",
        ),
        "put_lattice": models["lattice"].visualize(
            chart="tree", option_type="put", filename="09_put_lattice"
        ),
        "sabr_smile": models["sabr"].visualize(chart="volatility_smile", filename="10_sabr_smile"),
        "strategy_payoff": aq.OptionStrategy.bull_call_spread(
            lower_strike=100.0,
            upper_strike=115.0,
            lower_premium=6.0,
            upper_premium=2.0,
        ).visualize(chart="payoff", filename="11_strategy_payoff"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the option-model report."""
    try:
        models = build_report_models()
        print_mapping("Option report values", price_report_models(models))
        print_mapping("Option report figures", create_report_figures(models))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
