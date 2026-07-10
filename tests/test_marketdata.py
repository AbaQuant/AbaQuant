from __future__ import annotations

import builtins
from typing import Any

import pandas as pd
import pytest

from abaquant.derivatives import black_scholes, calculate_greeks
from abaquant.marketdata import MarketDataError, OptionalDependencyError, get_ticker
from abaquant.marketdata.providers import YahooFinanceProvider


class FakeProvider:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {
            "fast_info": 0,
            "info": 0,
            "history": 0,
            "option_expirations": 0,
            "option_chain": 0,
        }

    def fast_info(self, symbol: str) -> dict[str, Any]:
        self.calls["fast_info"] += 1
        assert symbol == "NVDA"
        return {"last_price": 100.0}

    def info(self, symbol: str) -> dict[str, Any]:
        self.calls["info"] += 1
        assert symbol == "NVDA"
        return {"dividendYield": 0.02, "longName": "NVIDIA Corporation"}

    def history(
        self,
        symbol: str,
        *,
        period: str | None = "1y",
        start: str | None = None,
        end: str | None = None,
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        self.calls["history"] += 1
        assert symbol == "NVDA"
        close = [90.0 + i for i in range(30)]
        return pd.DataFrame(
            {
                "Close": close,
                "Open": [value - 1.0 for value in close],
                "Volume": list(range(10, 40)),
            },
            index=pd.date_range("2026-01-01", periods=30),
        )

    def option_expirations(self, symbol: str) -> list[str]:
        self.calls["option_expirations"] += 1
        assert symbol == "NVDA"
        return ["2027-01-15"]

    def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        self.calls["option_chain"] += 1
        assert symbol == "NVDA"
        assert expiry == "2027-01-15"
        calls = pd.DataFrame(
            {
                ("strike", ""): [95.0, 100.0, 105.0],
                ("bid", ""): [9.0, 6.0, 0.0],
                ("ask", ""): [11.0, 8.0, 0.0],
                ("lastPrice", ""): [10.0, 7.0, 4.0],
                ("impliedVolatility", ""): [9.0, 0.25, -1.0],
                ("openInterest", ""): [120, 200, 80],
                ("volume", ""): [12, 20, 8],
            }
        )
        puts = pd.DataFrame(
            {
                "strike": [95.0, 100.0, 105.0],
                "lastPrice": [4.0, 6.0, 9.0],
                "bid": [3.5, 5.5, 8.5],
                "ask": [4.5, 6.5, 9.5],
                "impliedVolatility": [0.22, 0.24, 0.27],
                "openInterest": [150, 180, 140],
                "volume": [15, 18, 14],
            }
        )
        return calls, puts


def test_get_ticker_normalizes_symbol_and_is_lazy() -> None:
    provider = FakeProvider()
    ticker = get_ticker(" nvda ", provider=provider)

    assert ticker.symbol == "NVDA"
    assert provider.calls == {
        "fast_info": 0,
        "info": 0,
        "history": 0,
        "option_expirations": 0,
        "option_chain": 0,
    }

    assert ticker.spot() == 100.0
    assert provider.calls["fast_info"] == 1
    assert provider.calls["history"] == 0


def test_missing_yfinance_dependency_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "yfinance":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    provider = YahooFinanceProvider()

    with pytest.raises(OptionalDependencyError, match="abaquant\\[market\\]"):
        provider.fast_info("NVDA")


def test_option_pricing_delegates_to_existing_bsm_math() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    actual = ticker.options.bsm(
        strike=100.0,
        maturity=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="call",
        dividend_yield=0.02,
    )
    expected = black_scholes(100.0, 100.0, 0.05, 0.20, 1.0, is_call=True, q=0.02)

    assert actual == pytest.approx(expected)


def test_option_greeks_delegate_to_existing_greek_math() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    actual = ticker.options.greeks(
        strike=100.0,
        maturity=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="put",
        dividend_yield=0.02,
    )
    expected = calculate_greeks(100.0, 100.0, 0.05, 0.20, 1.0, is_call=False, q=0.02)

    assert actual == pytest.approx(expected)


def test_option_chain_cleaning_handles_multiindex_invalid_iv_and_missing_quotes() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    calls = ticker.options.chain("2027-01-15", option_type="call")
    puts = ticker.options.chain("2027-01-15", option_type="put")

    assert list(calls["option_type"].unique()) == ["call"]
    assert calls.loc[0, "mid_price"] == pytest.approx(10.0)
    assert pd.isna(calls.loc[0, "implied_volatility"])
    assert calls.loc[1, "implied_volatility"] == pytest.approx(0.25)
    assert pd.isna(calls.loc[2, "implied_volatility"])
    assert pd.isna(calls.loc[2, "mid_price"])
    assert puts.loc[0, "mid_price"] == pytest.approx(4.0)


def test_missing_volatility_raises_clear_error() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    with pytest.raises(ValueError, match="No default volatility is assumed"):
        ticker.options.bsm(strike=100.0, maturity=1.0, risk_free_rate=0.05)


def test_realized_volatility_is_explicit_opt_in() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    value = ticker.options.bsm(
        strike=100.0,
        maturity=1.0,
        risk_free_rate=0.05,
        volatility="realized",
        option_type="call",
        dividend_yield=0.02,
    )

    assert value > 0.0
    assert provider.calls["history"] == 1


def test_market_volatility_reads_listed_option_chain_iv() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    value = ticker.options.bsm(
        strike=100.0,
        expiry="2027-01-15",
        risk_free_rate=0.05,
        volatility="market",
        option_type="call",
        dividend_yield=0.02,
    )

    expected = black_scholes(
        100.0,
        100.0,
        0.05,
        0.25,
        ticker.options._resolve_maturity(None, "2027-01-15"),
        is_call=True,
        q=0.02,
    )
    assert value == pytest.approx(expected)
    assert provider.calls["option_chain"] == 1


def test_listed_implied_volatility_returns_provider_field() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    iv = ticker.options.listed_implied_volatility(
        strike=100.0,
        expiry="2027-01-15",
        option_type="call",
    )

    assert iv == pytest.approx(0.25)


def test_solve_implied_volatility_uses_supplied_market_price() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    market_price = black_scholes(100.0, 100.0, 0.05, 0.30, 1.0, is_call=True, q=0.02)
    iv = ticker.options.solve_implied_volatility(
        market_price=market_price,
        strike=100.0,
        maturity=1.0,
        risk_free_rate=0.05,
        option_type="call",
        dividend_yield=0.02,
    )

    assert iv == pytest.approx(0.30)
    assert provider.calls["option_chain"] == 0


def test_empty_option_chain_raises_market_data_error() -> None:
    class EmptyProvider(FakeProvider):
        def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
            self.calls["option_chain"] += 1
            return pd.DataFrame(), pd.DataFrame()

    ticker = get_ticker("NVDA", provider=EmptyProvider())

    with pytest.raises(MarketDataError, match="No option chain"):
        ticker.options.chain("2027-01-15")


def test_option_chain_analytics_smile_skew_rich_cheap_and_visualization() -> None:
    provider = FakeProvider()
    ticker = get_ticker("NVDA", provider=provider)

    analytics = ticker.options.analytics("2027-01-15")

    smile = analytics.iv_smile(option_type="call", spot_price=100.0)
    assert list(smile["strike"]) == [100.0]
    assert smile.loc[0, "moneyness"] == pytest.approx(1.0)

    put_smile = analytics.iv_smile(option_type="put", spot_price=100.0)
    assert len(put_smile) == 3

    skew = analytics.skew(option_type="put", spot_price=100.0)
    assert skew.observations == 3
    assert skew.at_the_money_iv == pytest.approx(0.24)

    term = analytics.term_structure(
        strike=100.0, option_type="call", expiries=["2027-01-15"], spot_price=100.0
    )
    assert term.loc[0, "implied_volatility"] == pytest.approx(0.25)

    rich_cheap = analytics.rich_cheap_table(
        model="bsm", risk_free_rate=0.05, option_type="put", spot_price=100.0
    )
    assert {"market_price", "model_value", "rich_cheap", "rich_cheap_label"}.issubset(
        rich_cheap.columns
    )

    open_interest = analytics.open_interest_grid(
        expiries=["2027-01-15"], option_type="put", spot_price=100.0
    )
    assert open_interest["open_interest"].sum() == pytest.approx(470.0)

    figure = analytics.visualize(chart="iv_smile", option_type="put", spot_price=100.0)
    assert figure is not None
