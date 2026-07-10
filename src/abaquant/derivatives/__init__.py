"""Derivatives pricing, strategies, diagnostics, and calibration.

Purpose
-------
This package gathers vanilla pricing functions, lattice methods, exotic-option
approximations, option strategies, advanced model classes, diagnostics,
scenario grids, numerical helpers, and calibration workflows behind one
coherent derivatives namespace.

Conventions
-----------
Maturities are measured in years. Rates, dividend yields, carry rates, and
volatilities are decimal annual quantities unless a function states a different
convention.

Scope and limitations
---------------------
The package provides valuation and research primitives. It does not supply
market-data retrieval or trading execution.
"""

from .analytics.distributions import distribution_moments, excess_kurtosis, theoretical_mc_error
from .analytics.parity import forward_price_continuous, intrinsic_time_value, parity_check
from .analytics.volatility import iv_rv_spread, realized_vol
from .calibration import (
    BSMFlatVolCalibration,
    CalibrationError,
    CalibrationResult,
    HestonCalibration,
    SABRSmileCalibration,
    calibrate_heston,
    calibrate_sabr,
)
from .comparison import compare_all_models
from .exotics import (
    arithmetic_asian_options,
    asset_or_nothing_options,
    cash_or_nothing_options,
    compound_options,
    down_and_out_barrier_option,
    exchange_options,
    exotic_payoff_leg,
    floating_lookback_options,
    gap_options,
    geometric_asian_options,
    perpetual_option,
    simple_chooser_option,
)
from .forwards import (
    commodity_forward_price,
    forward_contract_value,
    forward_price,
    forward_price_with_continuous_dividend,
    forward_price_with_discrete_dividends,
    forward_price_with_yield,
    fra,
    fx_forward_price,
    live_forward_value,
    simple_forward_price,
)
from .models import (
    BlackScholesMertonModel,
    BlackScholesMertonParameters,
    CoxRossRubinsteinModel,
    DerivativeDiagnosticsReport,
    DerivativeScenarioGrid,
    HestonStochasticVolatilityModel,
    LatticeParameters,
    MertonJumpDiffusionModel,
    NormalBachelierModel,
    NormalInverseGaussianModel,
    SABRVolatilityModel,
    VarianceGammaProcessModel,
    bsm_d1_d2_summary,
    crr_tree_parameters,
    merton_jump_statistics,
)
from .monte_carlo import monte_carlo_bsm
from .simulation.gbm import simulate_gbm_paths
from .simulation.levy import simulate_vg_nig_returns
from .simulation.merton import simulate_merton_paths
from .strategies import OptionStrategy, OptionStrategyLeg, option_payoff_leg, strategy_profile
from .trees import binomial_tree, crr_binomial_tree
from .vanilla import (
    black_76,
    black_scholes,
    bsm_d1_d2,
    bsm_greeks,
    bsm_option_prices,
    calculate_greeks,
    implied_volatility_bsm,
    second_order_greeks,
    vanilla_extrinsic_value,
    vanilla_intrinsic_value,
)

__all__ = [
    "BSMFlatVolCalibration",
    "BlackScholesMertonModel",
    "BlackScholesMertonParameters",
    "CalibrationError",
    "CalibrationResult",
    "CoxRossRubinsteinModel",
    "DerivativeDiagnosticsReport",
    "DerivativeScenarioGrid",
    "HestonCalibration",
    "HestonStochasticVolatilityModel",
    "LatticeParameters",
    "MertonJumpDiffusionModel",
    "NormalBachelierModel",
    "NormalInverseGaussianModel",
    "OptionStrategy",
    "OptionStrategyLeg",
    "SABRSmileCalibration",
    "SABRVolatilityModel",
    "VarianceGammaProcessModel",
    "arithmetic_asian_options",
    "asset_or_nothing_options",
    "binomial_tree",
    "black_76",
    "black_scholes",
    "bsm_d1_d2",
    "bsm_d1_d2_summary",
    "bsm_greeks",
    "bsm_option_prices",
    "calculate_greeks",
    "calibrate_heston",
    "calibrate_sabr",
    "cash_or_nothing_options",
    "commodity_forward_price",
    "compare_all_models",
    "compound_options",
    "crr_binomial_tree",
    "crr_tree_parameters",
    "distribution_moments",
    "down_and_out_barrier_option",
    "excess_kurtosis",
    "exchange_options",
    "exotic_payoff_leg",
    "floating_lookback_options",
    "forward_contract_value",
    "forward_price",
    "forward_price_continuous",
    "forward_price_with_continuous_dividend",
    "forward_price_with_discrete_dividends",
    "forward_price_with_yield",
    "fra",
    "fx_forward_price",
    "gap_options",
    "geometric_asian_options",
    "implied_volatility_bsm",
    "intrinsic_time_value",
    "iv_rv_spread",
    "live_forward_value",
    "merton_jump_statistics",
    "monte_carlo_bsm",
    "option_payoff_leg",
    "parity_check",
    "perpetual_option",
    "realized_vol",
    "second_order_greeks",
    "simple_chooser_option",
    "simple_forward_price",
    "simulate_gbm_paths",
    "simulate_merton_paths",
    "simulate_vg_nig_returns",
    "strategy_profile",
    "theoretical_mc_error",
    "vanilla_extrinsic_value",
    "vanilla_intrinsic_value",
]
