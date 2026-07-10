"""Deterministic tests for FRED-backed rate curves."""

from __future__ import annotations

from typing import Any

import pytest

from abaquant.rates import (
    FredRateProvider,
    ManualRateProvider,
    RateCurve,
    RatesProviderError,
    get_rate_curve,
)


def test_manual_rate_curve_interpolates_and_discounts() -> None:
    """Interpolate a manual curve and produce continuous discount factors."""
    curve = RateCurve.from_rates({0.5: 0.04, 1.0: 0.045, 2.0: 0.05})

    assert curve.zero_rate(1.5) == pytest.approx(0.0475)
    assert curve.discount_factor(2.0) == pytest.approx(0.9048374180359595)
    assert tuple(curve.as_frame()["maturity_years"]) == (0.5, 1.0, 2.0)


def test_get_rate_curve_accepts_manual_provider() -> None:
    """Use the public factory with a deterministic provider object."""
    curve = get_rate_curve(provider=ManualRateProvider({1.0: 0.04, 3.0: 0.05}))

    assert curve.provider_name == "manual"
    assert curve.zero_rate(2.0) == pytest.approx(0.045)


class OfflineFredProvider(FredRateProvider):
    """FRED provider test double returning fixture JSON without network access."""

    def __init__(self, **kwargs: Any) -> None:
        """Create the provider and record request URLs."""
        super().__init__(
            api_key="fixture-key",
            series_by_maturity={1.0: "DGS1", 2.0: "DGS2"},
            **kwargs,
        )
        self.requests: list[str] = []

    def _request_json(self, url: str) -> dict[str, Any]:
        """Return descending observations with one missing value before a valid one."""
        self.requests.append(url)
        series_id = "DGS1" if "DGS1" in url else "DGS2"
        valid_value = "4.50" if series_id == "DGS1" else "5.00"
        return {
            "observations": [
                {"date": "2026-07-08", "value": "."},
                {"date": "2026-07-07", "value": valid_value},
            ]
        }


def test_fred_provider_converts_percent_observations_to_decimal_rates() -> None:
    """Convert fixture FRED percentage yields into a decimal rate curve."""
    provider = OfflineFredProvider(cache_mode="memory")

    curve = provider.rate_curve(date="latest", refresh_policy="refresh")

    assert len(provider.requests) == 2
    assert curve.zero_rate(1.0) == pytest.approx(0.045)
    assert curve.zero_rate(2.0) == pytest.approx(0.05)
    assert curve.observations[0].observation_date.isoformat() == "2026-07-07"


def test_fred_disk_cache_reuses_observations_without_api_key(tmp_path) -> None:
    """Persist FRED observations and reuse them with cache-only behavior."""
    first = OfflineFredProvider(cache_mode="disk", cache_directory=tmp_path)
    first_curve = first.rate_curve(date="2026-07-08", refresh_policy="refresh")
    assert first_curve.zero_rate(1.0) == pytest.approx(0.045)
    assert len(first.requests) == 2

    second = FredRateProvider(
        api_key=None,
        series_by_maturity={1.0: "DGS1", 2.0: "DGS2"},
        cache_mode="disk",
        cache_directory=tmp_path,
    )
    cached_curve = second.rate_curve(date="2026-07-08", refresh_policy="cache_only")

    assert cached_curve.zero_rate(1.0) == pytest.approx(0.045)
    assert cached_curve.zero_rate(2.0) == pytest.approx(0.05)
    assert second.cache_status(date="2026-07-08")["series"]["DGS1"]["disk"]["on_disk"] is True


def test_fred_provider_requires_api_key_for_live_cache_miss() -> None:
    """Raise an actionable error when no API key or cache entry is available."""
    provider = FredRateProvider(api_key=None, series_by_maturity={1.0: "DGS1"}, cache_mode="none")

    with pytest.raises(RatesProviderError, match="FRED requests require an API key"):
        provider.rate_curve(refresh_policy="refresh")
