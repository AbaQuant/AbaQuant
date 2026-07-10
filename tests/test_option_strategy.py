"""Deterministic tests for composable option strategies."""

from __future__ import annotations

import math
import os
import unittest

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

from abaquant.derivatives import (
    OptionStrategy,
    OptionStrategyLeg,
    option_payoff_leg,
    strategy_profile,
)


class OptionStrategyTests(unittest.TestCase):
    """Verify static option-strategy analytics and visualization hooks."""

    def test_bull_call_spread_diagnostics(self) -> None:
        """Bull call spread profit, loss, and break-even values are analytical."""
        strategy = OptionStrategy.bull_call_spread(
            lower_strike=110.0,
            upper_strike=120.0,
            lower_premium=4.2,
            upper_premium=1.8,
        )
        self.assertAlmostEqual(strategy.payoff(125.0), 7.6)
        self.assertAlmostEqual(strategy.max_profit(), 7.6)
        self.assertAlmostEqual(strategy.max_loss(), -2.4)
        self.assertEqual([round(value, 6) for value in strategy.break_even_points()], [112.4])

    def test_protective_put_has_finite_floor_and_unbounded_upside(self) -> None:
        """Protective put combines stock upside with a finite downside floor."""
        strategy = OptionStrategy.protective_put(
            underlying_entry_price=100.0,
            put_strike=95.0,
            put_premium=3.0,
        )
        self.assertTrue(math.isinf(strategy.max_profit()))
        self.assertAlmostEqual(strategy.max_loss(), -8.0)
        self.assertEqual([round(value, 6) for value in strategy.break_even_points()], [103.0])

    def test_predefined_constructors_build_expected_leg_counts(self) -> None:
        """Common named strategies create deterministic leg structures."""
        self.assertEqual(
            len(OptionStrategy.straddle(strike=100, call_premium=4, put_premium=5).legs), 2
        )
        self.assertEqual(
            len(
                OptionStrategy.strangle(
                    put_strike=95,
                    call_strike=105,
                    put_premium=3,
                    call_premium=3.5,
                ).legs
            ),
            2,
        )
        self.assertEqual(
            len(
                OptionStrategy.iron_condor(
                    lower_put_strike=85,
                    short_put_strike=95,
                    short_call_strike=105,
                    upper_call_strike=115,
                    lower_put_premium=1,
                    short_put_premium=3,
                    short_call_premium=3,
                    upper_call_premium=1,
                ).legs
            ),
            4,
        )
        self.assertEqual(
            len(
                OptionStrategy.butterfly(
                    lower_strike=90,
                    middle_strike=100,
                    upper_strike=110,
                    lower_premium=12,
                    middle_premium=6,
                    upper_premium=2,
                ).legs
            ),
            3,
        )

    def test_profile_and_legacy_helpers_remain_consistent(self) -> None:
        """Profiles expose aggregate columns and legacy helpers use the new model."""
        strategy = (
            OptionStrategy()
            .buy_call(strike=100.0, premium=6.0)
            .sell_call(strike=115.0, premium=2.0)
        )
        profile = strategy.profile(points=5)
        self.assertIn("spot_price", profile.columns)
        self.assertIn("net_profit", profile.columns)
        legacy = strategy_profile(
            spot=100.0,
            legs=[
                {"option_type": "call", "position": 1, "strike": 100.0, "premium": 6.0},
                {"option_type": "call", "position": -1, "strike": 115.0, "premium": 2.0},
            ],
            points=5,
        )
        self.assertIn("S_T", legacy.columns)
        self.assertIn("Net Payoff", legacy.columns)
        self.assertAlmostEqual(float(option_payoff_leg("call", 1, [150.0], 100.0, 6.0)[0]), 44.0)

    def test_strategy_visualization_returns_figure(self) -> None:
        """Strategy visualization returns a backend-native figure object."""
        pytest.importorskip("matplotlib")
        strategy = OptionStrategy.bull_call_spread(
            lower_strike=100.0,
            upper_strike=115.0,
            lower_premium=6.0,
            upper_premium=2.0,
        )
        self.assertIsNotNone(strategy.visualize(chart="payoff", points=25))
        self.assertIsNotNone(strategy.visualize(chart="components", points=25))

    def test_leg_validation_rejects_invalid_option_type(self) -> None:
        """Invalid option leg specifications raise clear errors."""
        with self.assertRaises(ValueError):
            OptionStrategyLeg.option(
                option_type="binary",
                position=1,
                strike=100.0,
                premium=1.0,
            )


if __name__ == "__main__":
    unittest.main()
