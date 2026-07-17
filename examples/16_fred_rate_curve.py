"""Build a risk-free-rate curve for pricing examples.

This example is deterministic by default: it uses ``ManualRateProvider`` with
Treasury-like rates so it can run without network access or a FRED API key. If
``FRED_API_KEY`` is available, the same public factory can request live FRED
observations by setting ``provider='fred'``.
"""

from __future__ import annotations

import os

import abaquant as aq
from _shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)


def build_manual_curve():
    """Create a deterministic Treasury-like curve for repeatable examples."""
    return aq.get_rate_curve(
        provider=aq.ManualRateProvider(
            {
                1.0 / 12.0: 0.0520,
                0.25: 0.0505,
                0.50: 0.0485,
                1.00: 0.0460,
                2.00: 0.0430,
                5.00: 0.0410,
                10.00: 0.0425,
                30.00: 0.0440,
            }
        )
    )


def price_option_with_curve_rate(curve):
    """Price a one-year option using the curve's interpolated one-year rate."""
    one_year_rate = curve.zero_rate(1.0)
    model = aq.BlackScholesMertonModel(
        spot_price=100.0,
        strike_price=105.0,
        maturity_years=1.0,
        risk_free_rate=one_year_rate,
        volatility=0.20,
    )
    report = model.diagnostics(option_type="call")
    return model, report


def maybe_fetch_live_fred_curve():
    """Fetch a live FRED curve only when the user has configured an API key."""
    if not os.getenv("FRED_API_KEY"):
        return None
    return aq.get_rate_curve(
        provider="fred",
        date="latest",
        cache_mode="disk",
        cache_directory="~/.cache/abaquant",
        refresh_policy="if_stale",
        max_age_days=1.0,
    )


def run() -> None:
    """Run the deterministic rate-curve workflow and optional live FRED branch."""
    print_section("Manual risk-free-rate curve")
    curve = build_manual_curve()
    print(curve.as_frame().head())

    print_mapping(
        "Interpolated rates and discount factors",
        {
            "six_month_rate": curve.zero_rate(0.5),
            "one_year_rate": curve.zero_rate(1.0),
            "two_year_discount_factor": curve.discount_factor(2.0),
        },
    )

    print_section("Option pricing with curve-derived rate")
    _, report = price_option_with_curve_rate(curve)
    print_mapping(
        "Black-Scholes-Merton call diagnostics",
        {
            "price": report.price,
            "intrinsic_value": report.intrinsic_value,
            "extrinsic_value": report.extrinsic_value,
            "moneyness": report.moneyness,
            "break_even_price": report.break_even_price,
        },
    )

    print_section("Visualization export")
    output_directory = configure_example_visuals(subdirectory="fred_rate_curve")
    curve.visualize(filename="manual_rate_curve")
    reset_example_visuals()
    print(f"Saved curve visualization in: {output_directory}")

    print_section("Optional live FRED branch")
    live_curve = maybe_fetch_live_fred_curve()
    if live_curve is None:
        print("Skipped live FRED request because FRED_API_KEY is not set.")
    else:
        print(live_curve.as_frame().head())
        print_mapping(
            "Live FRED curve checks",
            {
                "one_year_rate": live_curve.zero_rate(1.0),
                "two_year_discount_factor": live_curve.discount_factor(2.0),
            },
        )


if __name__ == "__main__":
    run()
