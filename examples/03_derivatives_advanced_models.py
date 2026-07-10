"""Advanced derivative models with structured calculations and figures."""

from __future__ import annotations

import numpy as np

from _shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.derivatives.analytics import distributions, parity, volatility
from abaquant.derivatives.models import (
    BlackScholesMertonModel,
    CoxRossRubinsteinModel,
    HestonStochasticVolatilityModel,
    MertonJumpDiffusionModel,
    NormalBachelierModel,
    NormalInverseGaussianModel,
    SABRVolatilityModel,
    VarianceGammaProcessModel,
)
from abaquant.derivatives.models.binomial import crr_tree_parameters
from abaquant.derivatives.models.black_scholes import bsm_d1_d2_summary
from abaquant.derivatives.models.merton import merton_jump_statistics
from abaquant.derivatives.monte_carlo import monte_carlo_bsm
from abaquant.derivatives.numerics.implied_volatility import (
    implied_volatility_black_scholes,
)
from abaquant.derivatives.simulation.gbm import simulate_gbm_paths
from abaquant.derivatives.simulation.levy import simulate_vg_nig_returns
from abaquant.derivatives.simulation.merton import simulate_merton_paths
from abaquant.visualization import VisualizationError


def build_pricing_models() -> dict[str, object]:
    """Create one deterministic instance of each advanced pricing model."""
    return {
        "black_scholes": BlackScholesMertonModel(100.0, 100.0, 1.0, 0.05, 0.20),
        "crr": CoxRossRubinsteinModel(100.0, 100.0, 1.0, 0.05, 0.20, number_of_steps=50),
        "bachelier": NormalBachelierModel(100.0, 100.0, 1.0, 0.05, 20.0),
        "heston": HestonStochasticVolatilityModel(
            100.0, 100.0, 1.0, 0.05, 0.0, 0.04, 2.0, 0.04, 0.3, -0.5
        ),
        "merton": MertonJumpDiffusionModel(100.0, 100.0, 1.0, 0.05, 0.20, poisson_series_terms=8),
        "nig": NormalInverseGaussianModel(100.0, 100.0, 1.0, 0.05, 5.0, 0.0, 0.2),
        "sabr": SABRVolatilityModel(100.0, 100.0, 1.0, 0.20, 0.5, -0.3, 0.4),
        "variance_gamma": VarianceGammaProcessModel(100.0, 100.0, 1.0, 0.05, 0.20, -0.1, 0.2),
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
        "bsm_d1_d2": bsm_d1_d2_summary(100.0, 100.0, 1.0, 0.05, 0.20),
        "bsm_call_diagnostics": models["black_scholes"].diagnostics("call").as_dict(),
        "bsm_put_diagnostics": models["black_scholes"].diagnostics("put").as_dict(),
        "crr_tree_parameters": crr_tree_parameters(1.0, 0.05, 0.20, N=50),
        "merton_jump_statistics": merton_jump_statistics(1.0, -0.05, 0.20, 0.20),
        "distribution_moments": distributions.distribution_moments(prices),
        "parity_check": parity.parity_check(10.0, 7.0, 100.0, 100.0, 1.0, 0.05),
        "realized_volatility_last": float(volatility.realized_vol(prices, window=2)[-1]),
        "solved_bsm_iv": implied_volatility_black_scholes(bsm_price, 100.0, 100.0, 1.0, 0.05),
    }


def run_simulations() -> dict[str, object]:
    """Run compact Monte Carlo and path-simulation examples."""
    return {
        "monte_carlo_bsm": monte_carlo_bsm(100.0, 100.0, 1.0, 0.05, 0.20, n_paths=2_000),
        "gbm_shape": simulate_gbm_paths(100.0, 1.0, 0.05, 0.20, n_paths=8, n_steps=20)[
            "paths"
        ].shape,
        "merton_shape": simulate_merton_paths(100.0, 1.0, 0.05, 0.20, n_paths=8, n_steps=20)[
            "paths"
        ].shape,
        "levy_keys": sorted(
            simulate_vg_nig_returns(1.0, 0.20, -0.1, 0.2, 5.0, 0.0, 0.2, 0.2, n_sim=500).keys()
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
        "crr_lattice": CoxRossRubinsteinModel(
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
    except VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
