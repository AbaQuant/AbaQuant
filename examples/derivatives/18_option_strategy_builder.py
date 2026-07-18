"""Composable option-strategy builder examples."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)


def build_bull_call_spread() -> aq.OptionStrategy:
    """Create a debit call spread using the strategy builder."""
    return (
        aq.OptionStrategy().buy_call(strike=110.0, premium=4.2).sell_call(strike=120.0, premium=1.8)
    )


def compare_named_strategies() -> dict[str, object]:
    """Compute diagnostics for predefined strategy constructors."""
    strategies = {
        "bull_call_spread": aq.OptionStrategy.bull_call_spread(
            lower_strike=110.0,
            upper_strike=120.0,
            lower_premium=4.2,
            upper_premium=1.8,
        ),
        "protective_put": aq.OptionStrategy.protective_put(
            underlying_entry_price=100.0,
            put_strike=95.0,
            put_premium=3.0,
        ),
        "straddle": aq.OptionStrategy.straddle(
            strike=100.0,
            call_premium=5.0,
            put_premium=4.5,
        ),
        "strangle": aq.OptionStrategy.strangle(
            put_strike=95.0,
            call_strike=105.0,
            put_premium=3.0,
            call_premium=3.4,
        ),
        "iron_condor": aq.OptionStrategy.iron_condor(
            lower_put_strike=85.0,
            short_put_strike=95.0,
            short_call_strike=105.0,
            upper_call_strike=115.0,
            lower_put_premium=1.0,
            short_put_premium=3.2,
            short_call_premium=3.0,
            upper_call_premium=1.1,
        ),
        "butterfly": aq.OptionStrategy.butterfly(
            lower_strike=90.0,
            middle_strike=100.0,
            upper_strike=110.0,
            lower_premium=12.0,
            middle_premium=6.0,
            upper_premium=2.0,
        ),
    }
    return {
        name: {
            "legs": len(strategy.legs),
            "max_profit": strategy.max_profit(),
            "max_loss": strategy.max_loss(),
            "break_even_points": strategy.break_even_points(),
        }
        for name, strategy in strategies.items()
    }


def print_strategy_profile(strategy: aq.OptionStrategy) -> None:
    """Print a small payoff profile for one strategy."""
    profile = strategy.profile(spot_prices=[90.0, 110.0, 112.4, 120.0, 130.0])
    print_section("Bull call spread profile")
    print(profile[["spot_price", "gross_payoff", "net_profit"]].to_string(index=False))


def create_strategy_figures(strategy: aq.OptionStrategy) -> dict[str, object]:
    """Create aggregate and component payoff charts."""
    output_directory = configure_example_visuals(subdirectory="option_strategy_builder")
    figures = {
        "payoff": strategy.visualize(chart="payoff", filename="01_bull_call_spread_payoff"),
        "components": strategy.visualize(
            chart="components", filename="02_bull_call_spread_components"
        ),
        "iron_condor": aq.OptionStrategy.iron_condor(
            lower_put_strike=85.0,
            short_put_strike=95.0,
            short_call_strike=105.0,
            upper_call_strike=115.0,
            lower_put_premium=1.0,
            short_put_premium=3.2,
            short_call_premium=3.0,
            upper_call_premium=1.1,
        ).visualize(chart="payoff", filename="03_iron_condor_payoff"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the option-strategy builder examples."""
    try:
        spread = build_bull_call_spread()
        print_mapping(
            "Composable bull call spread",
            {
                "profit_at_125": spread.payoff(spot_price=125.0),
                "gross_payoff_at_125": spread.payoff(spot_price=125.0, include_premium=False),
                "net_inception_cost": spread.net_inception_cost(),
                "max_profit": spread.max_profit(),
                "max_loss": spread.max_loss(),
                "break_even_points": spread.break_even_points(),
            },
        )
        print_strategy_profile(spread)
        print_mapping("Named strategy constructors", compare_named_strategies(), decimals=4)
        print_mapping("Strategy visualizations", create_strategy_figures(spread))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
