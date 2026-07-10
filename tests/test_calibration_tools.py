"""Regression tests for option-model calibration tools."""

from __future__ import annotations

import numpy as np
import pandas as pd

from abaquant.derivatives.calibration import (
    BSMFlatVolCalibration,
    CalibrationResult,
    HestonCalibration,
    SABRSmileCalibration,
)
from abaquant.derivatives.models import BlackScholesMertonModel, SABRVolatilityModel
from abaquant.marketdata.option_chain_analytics import OptionChainAnalytics


def synthetic_bsm_chain() -> pd.DataFrame:
    """Build a deterministic Black--Scholes option-chain fixture."""
    spot = 100.0
    maturity = 1.0
    risk_free_rate = 0.03
    dividend_yield = 0.01
    volatility = 0.24
    rows = []
    for strike in (85.0, 95.0, 100.0, 105.0, 115.0):
        model = BlackScholesMertonModel(
            spot,
            strike,
            maturity,
            risk_free_rate,
            volatility,
            dividend_yield,
        )
        price = model.call_price()
        rows.append(
            {
                "option_type": "call",
                "strike": strike,
                "market_price": price,
                "implied_volatility": volatility,
                "spot_price": spot,
                "maturity_years": maturity,
                "open_interest": 100,
            }
        )
    return pd.DataFrame(rows)


def synthetic_sabr_chain() -> pd.DataFrame:
    """Build a deterministic SABR implied-volatility smile fixture."""
    forward = 100.0
    maturity = 1.0
    rows = []
    for strike in (80.0, 90.0, 100.0, 110.0, 120.0):
        implied_volatility = SABRVolatilityModel(
            forward,
            strike,
            maturity,
            0.32,
            0.8,
            -0.2,
            0.55,
        ).implied_vol()
        rows.append(
            {
                "option_type": "call",
                "strike": strike,
                "implied_volatility": implied_volatility,
                "spot_price": 100.0,
                "forward_price": forward,
                "maturity_years": maturity,
                "open_interest": 100,
            }
        )
    return pd.DataFrame(rows)


class FakeOptions:
    """Minimal option namespace for analytics-calibration tests."""

    def __init__(self, ticker):
        """Store the parent fake ticker."""
        self.ticker = ticker

    def expirations(self) -> list[str]:
        """Return deterministic expiration labels."""
        return ["2027-01-15"]

    def chain(self, expiry: str) -> pd.DataFrame:
        """Return the deterministic synthetic chain."""
        return self.ticker.chain.copy()


class FakeTicker:
    """Minimal ticker object compatible with OptionChainAnalytics."""

    def __init__(self, chain: pd.DataFrame):
        """Store synthetic quote and chain data."""
        self.symbol = "SYN"
        self.chain = chain
        self.options = FakeOptions(self)

    def spot(self) -> float:
        """Return the deterministic spot price."""
        return 100.0


def test_bsm_flat_vol_calibration_recovers_synthetic_volatility() -> None:
    """Flat-vol calibration recovers a deterministic Black--Scholes smile."""
    result = BSMFlatVolCalibration(
        synthetic_bsm_chain(),
        spot_price=100.0,
        maturity_years=1.0,
        risk_free_rate=0.03,
        dividend_yield=0.01,
        objective="price",
    ).fit()
    assert isinstance(result, CalibrationResult)
    assert abs(result.parameters["volatility"] - 0.24) < 1e-4
    assert result.error < 1e-4
    assert set(result.error_table().columns) >= {"market_value", "model_value", "residual"}


def test_sabr_smile_calibration_returns_parameterized_result() -> None:
    """SABR calibration returns calibrated smile parameters and diagnostics."""
    result = SABRSmileCalibration(
        synthetic_sabr_chain(),
        forward_price=100.0,
        maturity_years=1.0,
        beta=0.8,
        initial_parameters={"alpha": 0.25, "rho": -0.1, "nu": 0.4},
    ).fit()
    assert result.success
    assert result.parameters["alpha"] > 0.0
    assert result.parameters["nu"] > 0.0
    assert -1.0 < result.parameters["rho"] < 1.0
    assert np.isfinite(result.error)


def test_heston_calibration_runs_on_small_smile() -> None:
    """Heston calibration produces a bounded result on a compact smile."""
    small_chain = synthetic_bsm_chain().iloc[[1, 2, 3]].copy()
    result = HestonCalibration(
        small_chain,
        spot_price=100.0,
        maturity_years=1.0,
        risk_free_rate=0.03,
        dividend_yield=0.01,
        objective="iv",
        max_iter=2,
        max_contracts=3,
    ).fit()
    assert set(result.parameters) == {"kappa", "theta", "xi", "rho", "v0"}
    assert len(result.model_data) == 3
    assert np.isfinite(result.error)


def test_option_chain_analytics_calibration_methods() -> None:
    """Option-chain analytics exposes calibration convenience methods."""
    ticker = FakeTicker(synthetic_bsm_chain())
    analytics = OptionChainAnalytics(ticker, "2027-01-15", ticker.chain)
    result = analytics.calibrate_bsm_flat_vol(
        option_type="call",
        risk_free_rate=0.03,
        dividend_yield=0.01,
        maturity_years=1.0,
        objective="iv",
    )
    assert abs(result.parameters["volatility"] - 0.24) < 1e-12
    figure = result.visualize(chart="model_vs_market")
    assert figure is not None
