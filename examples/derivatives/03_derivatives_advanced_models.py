"""Advanced derivative models with structured calculations and figures."""

from __future__ import annotations

import numpy as np

import abaquant as aq
from examples._shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)


def build_pricing_models() -> dict[str, object]:
    """Create one deterministic instance of each advanced pricing model."""
    return {
        "black_scholes": aq.BlackScholesMertonModel(100.0, 100.0, 1.0, 0.05, 0.20),
        "crr": aq.CoxRossRubinsteinModel(100.0, 100.0, 1.0, 0.05, 0.20, number_of_steps=50),
        "bachelier": aq.NormalBachelierModel(100.0, 100.0, 1.0, 0.05, 20.0),
        "heston": aq.HestonStochasticVolatilityModel(
            100.0, 100.0, 1.0, 0.05, 0.0, 0.04, 2.0, 0.04, 0.3, -0.5
        ),
        "merton": aq.MertonJumpDiffusionModel(
            100.0, 100.0, 1.0, 0.05, 0.20, poisson_series_terms=8
        ),
        "nig": aq.NormalInverseGaussianModel(100.0, 100.0, 1.0, 0.05, 5.0, 0.0, 0.2),
        "sabr": aq.SABRVolatilityModel(100.0, 100.0, 1.0, 0.20, 0.5, -0.3, 0.4),
        "variance_gamma": aq.VarianceGammaProcessModel(100.0, 100.0, 1.0, 0.05, 0.20, -0.1, 0.2),
    }


def price_all_models(models: dict[str, object]) -> dict[str, float]:
    """Evaluate call prices or implied volatility for the model set."""
    return {
        "black_scholes_call": models["black_scholes"].call_price(),
        "crr_put": models["crr"].put_price(),
        "bachelier_call": models["bachelier"].call_price(),
        "heston_call": models["heston"].call_price(),
        "merton_call": models["merton"].call_price(),
        "nig_call": models["nig"].call_price(),
        "sabr_implied_volatility": models["sabr"].implied_vol(),
        "variance_gamma_call": models["variance_gamma"].call_price(),
    }


def run_model_diagnostics(models: dict[str, object]) -> dict[str, object]:
    """Compute analytical and numerical diagnostics for pricing models."""
    bsm_price = models["black_scholes"].call_price()
    prices = np.array([100.0, 101.0, 99.0, 102.0, 103.0])
    return {
        "bsm_d1_d2": aq.bsm_d1_d2_summary(100.0, 100.0, 1.0, 0.05, 0.20),
        "bsm_call_diagnostics": models["black_scholes"].diagnostics("call").as_dict(),
        "bsm_put_diagnostics": models["black_scholes"].diagnostics("put").as_dict(),
        "crr_tree_parameters": aq.crr_tree_parameters(1.0, 0.05, 0.20, N=50),
        "merton_jump_statistics": aq.merton_jump_statistics(1.0, -0.05, 0.20, 0.20),
        "distribution_moments": aq.derivatives.analytics.distributions.distribution_moments(prices),
        "parity_check": aq.derivatives.analytics.parity.parity_check(
            10.0, 7.0, 100.0, 100.0, 1.0, 0.05
        ),
        "realized_volatility_last": float(
            aq.derivatives.analytics.volatility.realized_vol(prices, window=2)[-1]
        ),
        "solved_bsm_iv": aq.derivatives.numerics.implied_volatility.implied_volatility_black_scholes(
            bsm_price, 100.0, 100.0, 1.0, 0.05
        ),
    }


def run_simulations() -> dict[str, object]:
    """Run compact Monte Carlo and path-simulation examples."""
    return {
        "monte_carlo_bsm": aq.monte_carlo_bsm(100.0, 100.0, 1.0, 0.05, 0.20, n_paths=2_000),
        "gbm_shape": aq.simulate_gbm_paths(100.0, 1.0, 0.05, 0.20, n_paths=8, n_steps=20)[
            "paths"
        ].shape,
        "merton_shape": aq.simulate_merton_paths(100.0, 1.0, 0.05, 0.20, n_paths=8, n_steps=20)[
            "paths"
        ].shape,
        "levy_keys": sorted(
            aq.simulate_vg_nig_returns(1.0, 0.20, -0.1, 0.2, 5.0, 0.0, 0.2, 0.2, n_sim=500).keys()
        ),
    }


def create_model_visualizations(models: dict[str, object]) -> dict[str, str]:
    """Create and save option-model visualizations."""
    output_directory = configure_example_visuals(subdirectory="derivatives_advanced_models")
    figures = {
        "bsm_call_payoff": models["black_scholes"].visualize(
            chart="payoff", option_type="call", filename="bsm_call_payoff"
        ),
        "bsm_put_profile": models["black_scholes"].visualize(
            chart="price_profile", option_type="put", filename="bsm_put_profile"
        ),
        "bsm_call_extrinsic": models["black_scholes"].visualize(
            chart="extrinsic_value", option_type="call", filename="bsm_call_extrinsic"
        ),
        "bsm_call_greeks": models["black_scholes"].visualize(
            chart="greeks",
            option_type="call",
            greek_scale="standardized",
            filename="bsm_call_greeks",
        ),
        "bsm_call_price_surface": models["black_scholes"].visualize(
            chart="price_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="bsm_call_price_surface",
        ),
        "bsm_call_delta_surface": models["black_scholes"].visualize(
            chart="delta_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="bsm_call_delta_surface",
        ),
        "bsm_call_extrinsic_surface": models["black_scholes"].visualize(
            chart="extrinsic_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="bsm_call_extrinsic_surface",
        ),
        "crr_lattice": aq.CoxRossRubinsteinModel(
            100.0, 100.0, 1.0, 0.05, 0.20, number_of_steps=6
        ).visualize(chart="tree", option_type="put", filename="crr_put_lattice"),
        "sabr_smile": models["sabr"].visualize(chart="volatility_smile", filename="sabr_smile"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run advanced-derivatives calculations and visualization examples."""
    models = build_pricing_models()
    print_mapping("Advanced model values", price_all_models(models))
    print_section("Model diagnostics")
    for key, value in run_model_diagnostics(models).items():
        print(f"{key}: {value}")
    print_section("Simulation diagnostics")
    for key, value in run_simulations().items():
        print(f"{key}: {value}")
    try:
        print_mapping("Created advanced-derivative figures", create_model_visualizations(models))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
