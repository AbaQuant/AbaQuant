"""Derivative-pricing examples organised by instrument family."""

from __future__ import annotations

from _shared.output import print_mapping, print_section
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.derivatives.exotics import (
    asset_or_nothing_options,
    cash_or_nothing_options,
    down_and_out_barrier_option,
    exchange_options,
    geometric_asian_options,
)
from abaquant.derivatives.forwards import forward_contract_value, forward_price, fx_forward_price
from abaquant.derivatives.strategies import OptionStrategy, strategy_profile
from abaquant.derivatives.trees import binomial_tree, crr_binomial_tree
from abaquant.derivatives.vanilla import (
    black_76,
    black_scholes,
    calculate_greeks,
    implied_volatility_bsm,
    second_order_greeks,
)


def price_vanilla_options() -> dict[str, float]:
    """Compute vanilla Black--Scholes and Black-76 quantities."""
    call_price = black_scholes(100.0, 100.0, 0.05, 0.20, 1.0, is_call=True)
    put_price = black_scholes(100.0, 100.0, 0.05, 0.20, 1.0, is_call=False)
    future_option = black_76(102.0, 100.0, 0.05, 0.20, 1.0, is_call=True)
    solved_volatility = implied_volatility_bsm(call_price, 100.0, 100.0, 0.05, 1.0)
    return {
        "european_call": call_price,
        "european_put": put_price,
        "black_76_call": future_option,
        "implied_volatility": solved_volatility,
    }


def compute_greek_ladders() -> dict[str, float]:
    """Compute first- and second-order Greeks for one call option."""
    first_order = calculate_greeks(100.0, 100.0, 0.05, 0.20, 1.0, is_call=True)
    second_order = second_order_greeks(100.0, 100.0, 0.05, 0.0, 0.20, 1.0, is_call=True)
    return {
        "delta": first_order["delta"],
        "gamma": first_order["gamma"],
        "vega": first_order["vega"],
        "vanna": second_order["vanna"],
        "vomma": second_order["vomma"],
    }


def compare_tree_models() -> dict[str, float]:
    """Compare European and American binomial-tree prices."""
    european_price, _ = binomial_tree(100.0, 100.0, 1.0, 0.05, 0.20, 80, option_type="put")
    american_price, _ = binomial_tree(
        100.0, 100.0, 1.0, 0.05, 0.20, 80, option_type="put", american=True
    )
    crr_price, _, _ = crr_binomial_tree(100.0, 100.0, 0.05, 0.20, 1.0, 80, is_call=True)
    return {"european_put": european_price, "american_put": american_price, "crr_call": crr_price}


def value_forward_contracts() -> dict[str, float]:
    """Value equity, FX, and live forward contracts."""
    return {
        "equity_forward_price": forward_price(100.0, 0.05, 1.0),
        "fx_forward_price": fx_forward_price(18.0, 0.07, 0.04, 1.0),
        "long_forward_value": forward_contract_value(105.0, 100.0, 0.05, 0.01, 0.5),
    }


def price_exotic_examples() -> dict[str, float]:
    """Compute representative exotic-option values."""
    return {
        "cash_or_nothing_call": cash_or_nothing_options(100.0, 100.0, 10.0, 1.0, 0.05, 0.20),
        "asset_or_nothing_call": asset_or_nothing_options(100.0, 100.0, 1.0, 0.05, 0.20),
        "geometric_asian_call": geometric_asian_options(100.0, 100.0, 1.0, 0.05, 0.20),
        "down_and_out_call": down_and_out_barrier_option(100.0, 100.0, 80.0, 1.0, 0.05, 0.20),
        "exchange_option": exchange_options(100.0, 95.0, 0.01, 0.02, 0.20, 0.25, 0.4, 1.0),
    }


def build_strategy_table() -> None:
    """Build and print a compact composable option-strategy payoff table."""
    strategy = OptionStrategy.bull_call_spread(
        lower_strike=100.0,
        upper_strike=115.0,
        lower_premium=6.0,
        upper_premium=2.0,
    )
    table = strategy.profile(points=6)
    print_section("Bull call spread payoff sample")
    print(table[["spot_price", "gross_payoff", "net_profit"]].head().to_string(index=False))
    print_mapping(
        "Bull call spread diagnostics",
        {
            "profit_at_125": strategy.payoff(125.0),
            "maximum_profit": strategy.max_profit(),
            "maximum_loss": strategy.max_loss(),
            "break_even_points": strategy.break_even_points(),
        },
    )

    legacy_table = strategy_profile(
        spot=100.0,
        legs=[
            {"option_type": "call", "position": 1, "strike": 100.0, "premium": 6.0},
            {"option_type": "call", "position": -1, "strike": 115.0, "premium": 2.0},
        ],
        points=4,
    )
    print_section("Legacy dictionary strategy helper")
    print(legacy_table[["S_T", "Net Payoff"]].to_string(index=False))


def run() -> None:
    """Run all derivative-pricing examples."""
    print_mapping("Vanilla option prices", price_vanilla_options())
    print_mapping("Greek ladder", compute_greek_ladders())
    print_mapping("Tree-model comparison", compare_tree_models())
    print_mapping("Forward contracts", value_forward_contracts())
    print_mapping("Exotic option prices", price_exotic_examples())
    build_strategy_table()


if __name__ == "__main__":
    run()
