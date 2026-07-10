from __future__ import annotations

import pytest

import abaquant as quact
from abaquant.derivatives import forwards


def test_discrete_forward_prices_use_discrete_growth_factors() -> None:
    assert quact.simple_forward_price(100, 0.05, 2, compounding="Discrete") == pytest.approx(
        100 * 1.05**2
    )
    assert quact.forward_price_with_continuous_dividend(
        100, 0.05, 0.02, 2, compounding="Discrete"
    ) == pytest.approx(100 * 1.05**2 / 1.02**2)
    assert quact.forward_price_with_discrete_dividends(
        100, 0.05, 2, 3, compounding="Discrete"
    ) == pytest.approx(97 * 1.05**2)
    assert quact.commodity_forward_price(
        100, 0.05, 0.01, 2, compounding="Discrete"
    ) == pytest.approx(100 * 1.05**2 * 1.01**2)
    assert quact.fx_forward_price(20, 0.08, 0.04, 2, compounding="Discrete") == pytest.approx(
        20 * 1.08**2 / 1.04**2
    )


def test_discrete_forward_value_uses_discrete_discount_factors() -> None:
    value = quact.live_forward_value(105, 102, 0.05, 0.02, 0.5, compounding="Discrete")
    expected = 105 / 1.02**0.5 - 102 / 1.05**0.5
    assert value == pytest.approx(expected)


def test_discrete_fra_uses_discrete_forward_rate_and_discounting() -> None:
    forward_rate, value = quact.fra(0.045, 0.05, 0.5, 1.0, 1_000_000, 0.055, compounding="Discrete")
    expected_rate = ((1.05**1.0) / (1.045**0.5)) ** 2 - 1
    expected_value = 1_000_000 * (expected_rate - 0.055) * 0.5 / 1.05

    assert forward_rate == pytest.approx(expected_rate)
    assert value == pytest.approx(expected_value)


def test_forwards_module_does_not_convert_discrete_rates_with_log_shortcut() -> None:
    source_names = set(forwards.__dict__)

    assert "discrete_rate_to_continuous_shortcut" not in source_names
