from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from abaquant.marketdata import (
    MarketDataProviderError,
    PortfolioOptimizationError,
    PortfolioValidationError,
    UniverseValidationError,
    get_tickers,
)
from abaquant.marketdata.universe_history import normalize_price_panel


class FakeUniverseProvider:
    name = "fake"

    def __init__(self, raw: pd.DataFrame | None = None) -> None:
        self.raw = raw if raw is not None else _multiindex_prices()
        self.calls: dict[str, int] = {
            "fast_info": 0,
            "info": 0,
            "history": 0,
            "history_many": 0,
            "option_expirations": 0,
            "option_chain": 0,
        }
        self.last_kwargs: dict[str, Any] = {}

    def fast_info(self, symbol: str) -> dict[str, Any]:
        self.calls["fast_info"] += 1
        return {"last_price": 100.0}

    def info(self, symbol: str) -> dict[str, Any]:
        self.calls["info"] += 1
        return {}

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
        return pd.DataFrame()

    def history_many(
        self,
        symbols: tuple[str, ...],
        *,
        start: str | None = None,
        end: str | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        self.calls["history_many"] += 1
        self.last_kwargs = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "period": period,
            "interval": interval,
            "auto_adjust": auto_adjust,
        }
        return self.raw

    def option_expirations(self, symbol: str) -> list[str]:
        self.calls["option_expirations"] += 1
        return []

    def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        self.calls["option_chain"] += 1
        return pd.DataFrame(), pd.DataFrame()


def _multiindex_prices() -> pd.DataFrame:
    index = pd.date_range("2026-01-02", periods=5, freq="B", tz="UTC")
    columns = pd.MultiIndex.from_product([["MSFT", "NVDA", "AAPL"], ["Open", "Close"]])
    return pd.DataFrame(
        [
            [99.0, 100.0, 49.0, 50.0, 199.0, 200.0],
            [100.0, 101.0, 50.0, 52.0, 200.0, 202.0],
            [101.0, 103.0, 52.0, 51.0, 202.0, 204.0],
            [102.0, 104.0, 51.0, 53.0, 204.0, 205.0],
            [104.0, 106.0, 53.0, 55.0, 205.0, 207.0],
        ],
        index=index,
        columns=columns,
    )


def test_get_tickers_normalizes_deduplicates_and_is_lazy() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers([" nvda ", "MSFT", "NVDA"], provider=provider)

    assert universe.symbols == ("NVDA", "MSFT")
    assert provider.calls["history_many"] == 0
    assert provider.calls["fast_info"] == 0


def test_get_tickers_validates_symbols_and_provider() -> None:
    provider = FakeUniverseProvider()

    with pytest.raises(UniverseValidationError, match="non-empty"):
        get_tickers("NVDA", provider=provider)
    with pytest.raises(UniverseValidationError, match="cannot be blank"):
        get_tickers(["NVDA", " "], provider=provider)
    with pytest.raises(UniverseValidationError, match="must be a string"):
        get_tickers(["NVDA", 1], provider=provider)  # type: ignore[list-item]
    with pytest.raises(UniverseValidationError, match="Only provider"):
        get_tickers(["NVDA"], provider="unknown")


def test_history_prices_normalizes_multiindex_and_caches_by_request() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["nvda", "msft"], provider=provider)

    first = universe.history.prices(period="1mo")
    second = universe.history.prices(period="1mo")
    third = universe.history.prices(period="3mo")

    assert provider.calls["history_many"] == 2
    assert list(first.columns) == ["NVDA", "MSFT"]
    assert first.index.tz is None
    assert first.iloc[0].to_dict() == {"NVDA": 50.0, "MSFT": 100.0}
    pd.testing.assert_frame_equal(first, second)
    assert not third.empty


def test_history_prices_supports_outer_alignment_without_filling() -> None:
    raw = _multiindex_prices()
    raw.loc[raw.index[1], ("NVDA", "Close")] = np.nan
    provider = FakeUniverseProvider(raw)
    universe = get_tickers(["NVDA", "MSFT"], provider=provider)

    outer = universe.history.prices(period="1mo", alignment="outer")
    inner = universe.history.prices(period="1mo", alignment="inner")

    assert pd.isna(outer.loc[outer.index[1], "NVDA"])
    assert len(outer) == 5
    assert len(inner) == 4


def test_normalize_price_panel_supports_reversed_multiindex() -> None:
    raw = _multiindex_prices()
    reversed_columns = pd.MultiIndex.from_tuples([(field, symbol) for symbol, field in raw.columns])
    reversed_raw = raw.copy()
    reversed_raw.columns = reversed_columns

    prices = normalize_price_panel(reversed_raw, ("AAPL", "NVDA"), alignment="inner")

    assert list(prices.columns) == ["AAPL", "NVDA"]
    assert prices.iloc[-1].to_dict() == {"AAPL": 207.0, "NVDA": 55.0}


def test_history_prices_reports_missing_symbol() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["NVDA", "TSLA"], provider=provider)

    with pytest.raises(MarketDataProviderError, match="TSLA"):
        universe.history.prices(period="1mo")


def test_returns_summary_and_covariance_are_deterministic() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["NVDA", "MSFT"], provider=provider)

    returns = universe.history.returns(period="1mo")
    expected_returns = universe.history.prices(period="1mo").pct_change(fill_method=None).iloc[1:]
    summary = universe.statistics.summary(period="1mo", periods_per_year=252)
    covariance = universe.statistics.covariance(period="1mo", periods_per_year=252)

    pd.testing.assert_frame_equal(returns, expected_returns)
    assert summary.loc["NVDA", "observations"] == 4
    assert summary.loc["MSFT", "annualized_return"] == pytest.approx(
        expected_returns["MSFT"].mean() * 252
    )
    pd.testing.assert_frame_equal(covariance, expected_returns.cov() * 252)


def test_portfolio_equal_weight_and_custom_evaluation() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["NVDA", "MSFT", "AAPL"], provider=provider)

    equal = universe.portfolio.equal_weight(risk_free_rate=0.03, period="1mo")
    custom = universe.portfolio.evaluate(
        {"NVDA": 0.5, "MSFT": 0.3, "AAPL": 0.2},
        risk_free_rate=0.03,
        period="1mo",
    )

    assert equal.method == "equal_weight"
    assert sum(equal.weights.values()) == pytest.approx(1.0)
    assert custom.method == "custom"
    assert custom.weights["NVDA"] == pytest.approx(0.5)
    assert custom.observations == 4


def test_portfolio_optimizers_return_fully_invested_weights() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["NVDA", "MSFT", "AAPL"], provider=provider)

    min_var = universe.portfolio.minimum_variance(risk_free_rate=0.03, period="1mo")
    max_sharpe = universe.portfolio.max_sharpe(risk_free_rate=0.03, period="1mo")

    assert min_var.method == "minimum_variance"
    assert max_sharpe.method == "max_sharpe"
    assert sum(min_var.weights.values()) == pytest.approx(1.0)
    assert sum(max_sharpe.weights.values()) == pytest.approx(1.0)


def test_portfolio_validation_errors_are_clear() -> None:
    provider = FakeUniverseProvider()
    universe = get_tickers(["NVDA", "MSFT"], provider=provider)

    with pytest.raises(PortfolioValidationError, match="sum to 1"):
        universe.portfolio.evaluate([0.9, 0.2], risk_free_rate=0.03, period="1mo")
    with pytest.raises(PortfolioOptimizationError, match="bounds are infeasible"):
        universe.portfolio.minimum_variance(
            risk_free_rate=0.03,
            period="1mo",
            bounds=(0.8, 1.0),
        )


def test_single_symbol_history_allowed_but_optimization_requires_two_assets() -> None:
    raw = pd.DataFrame(
        {"Open": [99.0, 100.0, 101.0], "Close": [100.0, 101.0, 103.0]},
        index=pd.date_range("2026-01-02", periods=3, freq="B"),
    )
    provider = FakeUniverseProvider(raw)
    universe = get_tickers(["NVDA"], provider=provider)

    prices = universe.history.prices(period="1mo")

    assert list(prices.columns) == ["NVDA"]
    with pytest.raises(PortfolioValidationError, match="At least two assets"):
        universe.portfolio.equal_weight(risk_free_rate=0.03, period="1mo")
