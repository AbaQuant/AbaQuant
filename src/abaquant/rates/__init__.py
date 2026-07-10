"""Rate curves, FRED integration, and pure interest-rate helpers.

Purpose
-------
This module combines AbaQuant's pure interest-rate conversion functions with an
optional applied risk-free-rate curve interface. The applied interface can read
U.S. Treasury constant-maturity yields from the Federal Reserve Economic Data
(FRED) API, cache downloaded observations, interpolate a decimal annual zero
rate, and convert that rate into discount factors for pricing workflows.

Conventions
-----------
FRED Treasury constant-maturity series are reported as annual percentage yields.
AbaQuant converts them to annual decimal rates, so ``4.50`` from FRED becomes
``0.045``. ``RateCurve.zero_rate`` uses linear interpolation across maturity in
years by default. ``RateCurve.discount_factor`` uses continuous compounding by
default, :math:`D(T)=\\exp(-rT)`.

Scope and limitations
---------------------
Treasury constant-maturity yields are treated as a pragmatic risk-free-rate
proxy. They are not bootstrapped zero-coupon curves, do not include collateral
or funding adjustments, and should not be interpreted as production-grade curve
construction.

References
----------
[1] Federal Reserve Bank of St. Louis, FRED API documentation.
[2] Kellison, S. G. (2009), The Theory of Interest.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance
from abaquant.financial_math import *  # noqa: F403
from abaquant.financial_math import __all__ as _financial_math_all

FredCacheMode = Literal["none", "memory", "disk"]
FredRefreshPolicy = Literal["cache_only", "if_missing", "if_stale", "refresh"]
RateInterpolation = Literal["linear"]
RateExtrapolation = Literal["flat", "error"]
DiscountCompounding = Literal["continuous", "annual", "simple"]

_DEFAULT_FRED_SERIES: dict[float, str] = {
    1.0 / 12.0: "DGS1MO",
    3.0 / 12.0: "DGS3MO",
    6.0 / 12.0: "DGS6MO",
    1.0: "DGS1",
    2.0: "DGS2",
    3.0: "DGS3",
    5.0: "DGS5",
    7.0: "DGS7",
    10.0: "DGS10",
    20.0: "DGS20",
    30.0: "DGS30",
}
_FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
_DEFAULT_FRED_USER_AGENT = "abaquant/1.0.0rc1"


class RatesProviderError(RuntimeError):
    """Raised when an applied rate provider cannot supply usable data."""


class RatesValidationError(ValueError):
    """Raised when a rate-curve request violates a domain constraint."""


@dataclass(frozen=True)
class FredObservation:
    """One FRED observation converted to an annual decimal rate.

    Attributes
    ----------
    series_id : str
        FRED series identifier, such as ``"DGS10"``.
    maturity_years : float
        Maturity represented by the series, expressed in years.
    observation_date : date
        Date of the FRED observation used for the curve point.
    annual_rate : float
        Annual rate in decimal units. For example, ``0.045`` denotes 4.5%.
    raw_value_percent : float
        Raw FRED observation in percentage-point units.
    """

    series_id: str
    maturity_years: float
    observation_date: date
    annual_rate: float
    raw_value_percent: float


@dataclass(frozen=True)
class RateCurve:
    """Provider-neutral annual decimal rate curve.

    Parameters
    ----------
    observations : sequence of FredObservation
        Curve points sorted internally by maturity. Rates are annual decimal
        rates; maturities are measured in years.
    provider_name : str, default="manual"
        Source label recorded for provenance.
    curve_date : date | None, default=None
        Requested curve date. ``None`` is allowed for synthetic or latest curves
        whose observations can have slightly different dates.
    retrieved_at_utc : datetime | None, default=None
        Retrieval or construction timestamp in UTC.

    Notes
    -----
    The class intentionally does not bootstrap a zero-coupon curve. It
    interpolates the supplied annual yields directly.
    """

    observations: tuple[FredObservation, ...]
    provider_name: str = "manual"
    curve_date: date | None = None
    retrieved_at_utc: datetime | None = None
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Validate and sort curve observations by maturity."""
        if not self.observations:
            raise RatesValidationError("RateCurve requires at least one observation.")
        sorted_observations = tuple(sorted(self.observations, key=lambda item: item.maturity_years))
        previous_maturity = -np.inf
        for observation in sorted_observations:
            if not np.isfinite(observation.maturity_years) or observation.maturity_years <= 0.0:
                raise RatesValidationError("Curve maturities must be finite and positive.")
            if observation.maturity_years <= previous_maturity:
                raise RatesValidationError("Curve maturities must be unique.")
            if not np.isfinite(observation.annual_rate):
                raise RatesValidationError("Curve rates must be finite decimal quantities.")
            previous_maturity = observation.maturity_years
        object.__setattr__(self, "observations", sorted_observations)
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider=self.provider_name,
                    dataset="rate_curve",
                    retrieved_at_utc=self.retrieved_at_utc,
                    source_labels=tuple(
                        observation.series_id for observation in sorted_observations
                    ),
                    currency="USD" if self.provider_name in {"fred", "manual"} else None,
                    reporting_date=self.curve_date.isoformat() if self.curve_date else "latest",
                    transformation_steps=(
                        "annual percentage yield conversion to decimal rate",
                        "maturity sorting",
                        "linear interpolation ready curve",
                    ),
                    request={
                        "curve_date": self.curve_date.isoformat() if self.curve_date else "latest"
                    },
                ),
            )

    @classmethod
    def from_rates(
        cls,
        rates_by_maturity: Mapping[float, float],
        *,
        curve_date: date | str | None = None,
        provider_name: str = "manual",
    ) -> RateCurve:
        """Create a curve from manually supplied decimal annual rates.

        Parameters
        ----------
        rates_by_maturity : mapping of float to float
            Mapping from maturity in years to annual decimal rate.
        curve_date : date | str | None, default=None
            Optional observation date recorded for all synthetic points.
        provider_name : str, default="manual"
            Provenance label stored on the returned curve.

        Returns
        -------
        RateCurve
            Curve constructed without making any provider request.
        """
        parsed_curve_date = _parse_curve_date(curve_date)
        observation_date = parsed_curve_date or date.today()
        observations = tuple(
            FredObservation(
                series_id=f"MANUAL_{maturity:g}Y",
                maturity_years=float(maturity),
                observation_date=observation_date,
                annual_rate=float(rate),
                raw_value_percent=float(rate) * 100.0,
            )
            for maturity, rate in rates_by_maturity.items()
        )
        return cls(
            observations,
            provider_name=provider_name,
            curve_date=parsed_curve_date,
            retrieved_at_utc=datetime.now(UTC),
            provenance=DataProvenance(
                provider=provider_name,
                dataset="rate_curve",
                currency="USD" if provider_name in {"manual", "fred"} else None,
                reporting_date=parsed_curve_date.isoformat() if parsed_curve_date else "latest",
                source_labels=tuple(
                    f"MANUAL_{float(maturity):g}Y" for maturity in rates_by_maturity
                ),
                transformation_steps=("manual rate curve construction", "maturity sorting"),
                request={
                    "curve_date": parsed_curve_date.isoformat() if parsed_curve_date else "latest"
                },
            ),
        )

    @property
    def maturities(self) -> tuple[float, ...]:
        """Return curve maturities in ascending order."""
        return tuple(observation.maturity_years for observation in self.observations)

    @property
    def rates(self) -> tuple[float, ...]:
        """Return annual decimal rates in ascending maturity order."""
        return tuple(observation.annual_rate for observation in self.observations)

    def as_frame(self) -> pd.DataFrame:
        """Return the curve points as a tidy DataFrame.

        Returns
        -------
        pandas.DataFrame
            Columns are ``maturity_years``, ``annual_rate``,
            ``observation_date``, ``series_id``, ``provider_name``, and
            ``raw_value_percent``.
        """
        return pd.DataFrame(
            [
                {
                    "maturity_years": observation.maturity_years,
                    "annual_rate": observation.annual_rate,
                    "observation_date": observation.observation_date.isoformat(),
                    "series_id": observation.series_id,
                    "provider_name": self.provider_name,
                    "raw_value_percent": observation.raw_value_percent,
                }
                for observation in self.observations
            ]
        )

    def zero_rate(
        self,
        maturity: float,
        *,
        interpolation: RateInterpolation = "linear",
        extrapolation: RateExtrapolation = "flat",
    ) -> float:
        """Interpolate an annual decimal zero-rate proxy for one maturity.

        Parameters
        ----------
        maturity : float
            Requested maturity in years. Must be positive.
        interpolation : {"linear"}, default="linear"
            Interpolation method across the supplied curve points.
        extrapolation : {"flat", "error"}, default="flat"
            Out-of-range behavior. ``"flat"`` returns the nearest endpoint
            rate; ``"error"`` raises when maturity is outside the curve range.

        Returns
        -------
        float
            Annual decimal rate for the requested maturity.
        """
        requested_maturity = _validate_positive_float(maturity, "maturity")
        if interpolation != "linear":
            raise RatesValidationError("Only interpolation='linear' is currently supported.")
        if extrapolation not in {"flat", "error"}:
            raise RatesValidationError("extrapolation must be either 'flat' or 'error'.")
        maturities = np.asarray(self.maturities, dtype=float)
        rates = np.asarray(self.rates, dtype=float)
        if extrapolation == "error" and (
            requested_maturity < maturities[0] or requested_maturity > maturities[-1]
        ):
            raise RatesValidationError(
                "Requested maturity is outside the curve range and extrapolation='error'."
            )
        return float(np.interp(requested_maturity, maturities, rates))

    def discount_factor(
        self,
        maturity: float,
        *,
        compounding: DiscountCompounding = "continuous",
    ) -> float:
        """Convert the interpolated annual rate into a discount factor.

        Parameters
        ----------
        maturity : float
            Maturity in years.
        compounding : {"continuous", "annual", "simple"}, default="continuous"
            Discounting convention applied to the interpolated annual rate.

        Returns
        -------
        float
            Present-value factor for one currency unit paid at ``maturity``.
        """
        requested_maturity = _validate_positive_float(maturity, "maturity")
        annual_rate = self.zero_rate(requested_maturity)
        if compounding == "continuous":
            return float(np.exp(-annual_rate * requested_maturity))
        if compounding == "annual":
            return float((1.0 + annual_rate) ** (-requested_maturity))
        if compounding == "simple":
            return float(1.0 / (1.0 + annual_rate * requested_maturity))
        raise RatesValidationError("compounding must be 'continuous', 'annual', or 'simple'.")

    def visualize(
        self,
        *,
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename: str | None = None,
    ):
        """Return a themed figure of the annual decimal rate curve.

        The method follows AbaQuant's visualization convention: it returns a
        backend-native figure and never calls ``show`` automatically.
        """
        from abaquant.visualization import finalize_figure
        from abaquant.visualization.core import (
            matplotlib_axes,
            require_matplotlib,
            require_plotly,
            resolve_theme,
            style_matplotlib_axes,
            style_matplotlib_title,
            style_plotly_figure,
        )

        active_theme = resolve_theme(theme, backend)
        frame = self.as_frame()
        if active_theme.backend == "matplotlib":
            pyplot = require_matplotlib()
            figure, axes = matplotlib_axes(pyplot, active_theme)
            axes.plot(
                frame["maturity_years"],
                frame["annual_rate"],
                marker="o",
                linewidth=active_theme.line_width,
            )
            axes.set_xlabel("Maturity (years)")
            axes.set_ylabel("Annual decimal rate")
            style_matplotlib_axes(axes, active_theme)
            style_matplotlib_title(axes, "Rate curve", active_theme)
        else:
            graph_objects = require_plotly()
            figure = graph_objects.Figure()
            figure.add_scatter(
                x=frame["maturity_years"],
                y=frame["annual_rate"],
                mode="lines+markers",
                name="Zero-rate proxy",
            )
            style_plotly_figure(
                figure,
                active_theme,
                title="Rate curve",
                xaxis_title="Maturity (years)",
                yaxis_title="Annual decimal rate",
            )
        return finalize_figure(
            figure,
            backend=active_theme.backend,
            theme=active_theme,
            save_path=save_path,
            filename=filename,
            default_name="rate_curve",
        )


class FredJsonCacheStore:
    """Versioned, checksum-protected disk cache for FRED curve inputs."""

    schema_version = 1

    def __init__(self, directory: str | Path | None = None) -> None:
        """Configure the root directory used for FRED JSON cache files."""
        self.directory = Path(directory or "~/.cache/abaquant/fred").expanduser()

    def observation_path(self, series_id: str, date_label: str) -> Path:
        """Return the deterministic cache path for one series/date request."""
        clean_series = _normalize_series_id(series_id)
        clean_date_label = str(date_label).replace("/", "_").replace(":", "_")
        return self.directory / "observations" / clean_series / f"{clean_date_label}.json"

    def load_observation(
        self, series_id: str, date_label: str, *, max_age_days: float | None = None
    ) -> FredObservation | None:
        """Load one cached observation when it is present, valid, and fresh."""
        payload = self._load_payload(
            self.observation_path(series_id, date_label), max_age_days=max_age_days
        )
        if payload is None:
            return None
        try:
            return FredObservation(
                series_id=_normalize_series_id(payload["series_id"]),
                maturity_years=float(payload["maturity_years"]),
                observation_date=date.fromisoformat(payload["observation_date"]),
                annual_rate=float(payload["annual_rate"]),
                raw_value_percent=float(payload["raw_value_percent"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def save_observation(self, date_label: str, observation: FredObservation) -> None:
        """Persist one FRED observation through atomic temporary-file replacement."""
        self._save_payload(
            self.observation_path(observation.series_id, date_label),
            {
                "kind": "fred_observation",
                "series_id": observation.series_id,
                "maturity_years": observation.maturity_years,
                "observation_date": observation.observation_date.isoformat(),
                "annual_rate": observation.annual_rate,
                "raw_value_percent": observation.raw_value_percent,
            },
        )

    def observation_status(
        self, series_id: str, date_label: str, *, max_age_days: float | None = None
    ) -> dict[str, object]:
        """Return cache availability metadata for one observation request."""
        return self._status(self.observation_path(series_id, date_label), max_age_days=max_age_days)

    def clear_observation(self, series_id: str, date_label: str) -> None:
        """Remove one cached observation if it exists."""
        path = self.observation_path(series_id, date_label)
        if path.exists():
            path.unlink()

    def _load_payload(
        self, path: Path, *, max_age_days: float | None = None
    ) -> dict[str, Any] | None:
        """Load and validate one checksum-protected cache payload."""
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
            checksum = raw_payload.pop("checksum")
            serialized = json.dumps(
                raw_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            if hashlib.sha256(serialized.encode()).hexdigest() != checksum:
                return None
            if raw_payload.get("schema_version") != self.schema_version:
                return None
            retrieved_at = _parse_datetime(raw_payload.get("retrieved_at_utc"))
            if max_age_days is not None and _is_stale(retrieved_at, max_age_days):
                return None
            return raw_payload
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _save_payload(self, path: Path, data: dict[str, Any]) -> None:
        """Write one payload atomically with a schema version and checksum."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            **data,
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        payload["checksum"] = hashlib.sha256(serialized.encode()).hexdigest()
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        os.replace(temporary_path, path)

    def _status(self, path: Path, *, max_age_days: float | None = None) -> dict[str, object]:
        """Return cache metadata without raising on missing or corrupt files."""
        exists = path.exists()
        payload = self._load_payload(path, max_age_days=None) if exists else None
        retrieved_at = _parse_datetime(payload.get("retrieved_at_utc")) if payload else None
        return {
            "path": str(path),
            "on_disk": payload is not None,
            "exists": exists,
            "retrieved_at_utc": retrieved_at.isoformat() if retrieved_at else None,
            "is_stale": _is_stale(retrieved_at, max_age_days) if max_age_days is not None else None,
        }


class FredRateProvider:
    """FRED Treasury constant-maturity provider with optional disk caching.

    Parameters
    ----------
    api_key : str | None, default=None
        FRED API key. When omitted, ``FRED_API_KEY`` is read from the
        environment. Cache-only calls can work without an API key when the
        required observation files already exist.
    series_by_maturity : mapping of float to str, optional
        Mapping from maturity in years to FRED series IDs. The default uses U.S.
        Treasury constant-maturity series such as ``DGS1`` and ``DGS10``.
    cache_mode : {"none", "memory", "disk"}, default="memory"
        Cache layer used for observations.
    cache_directory : str | pathlib.Path | None, default=None
        Directory used by ``cache_mode='disk'``.
    """

    name = "fred"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        series_by_maturity: Mapping[float, str] | None = None,
        cache_mode: FredCacheMode = "memory",
        cache_directory: str | Path | None = None,
        timeout_seconds: float = 10.0,
        user_agent: str = _DEFAULT_FRED_USER_AGENT,
    ) -> None:
        """Configure provider credentials, curve series, cache, and timeout."""
        if cache_mode not in {"none", "memory", "disk"}:
            raise RatesValidationError("cache_mode must be 'none', 'memory', or 'disk'.")
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.series_by_maturity = {
            float(maturity): _normalize_series_id(series)
            for maturity, series in (series_by_maturity or _DEFAULT_FRED_SERIES).items()
        }
        self.cache_mode = cache_mode
        self.cache_store = FredJsonCacheStore(cache_directory) if cache_mode == "disk" else None
        self.timeout_seconds = float(timeout_seconds)
        self.user_agent = user_agent
        self._memory_cache: dict[tuple[str, str], FredObservation] = {}

    def rate_curve(
        self,
        *,
        date: str | date = "latest",
        refresh_policy: FredRefreshPolicy = "if_stale",
        max_age_days: float | None = 1.0,
    ) -> RateCurve:
        """Return a Treasury-rate curve from FRED observations.

        Parameters
        ----------
        date : str | date, default="latest"
            ``"latest"`` requests each series' latest valid observation. A date
            uses the most recent valid observation on or before that date.
        refresh_policy : {"cache_only", "if_missing", "if_stale", "refresh"}, default="if_stale"
            Cache policy applied independently to each FRED series.
        max_age_days : float | None, default=1.0
            Freshness threshold for cached observation files. ``None`` disables
            staleness checks.

        Returns
        -------
        RateCurve
            Provider-neutral curve with annual decimal rates.
        """
        date_label = _date_label(date)
        if refresh_policy not in {"cache_only", "if_missing", "if_stale", "refresh"}:
            raise RatesValidationError("Unsupported FRED refresh_policy.")
        observations = tuple(
            self._observation_for_series(
                series_id,
                maturity,
                date_label=date_label,
                requested_date=date,
                refresh_policy=refresh_policy,
                max_age_days=max_age_days,
            )
            for maturity, series_id in sorted(self.series_by_maturity.items())
        )
        curve_date = None if date_label == "latest" else _parse_curve_date(date)
        retrieved_at = datetime.now(UTC)
        return RateCurve(
            observations,
            provider_name=self.name,
            curve_date=curve_date,
            retrieved_at_utc=retrieved_at,
            provenance=DataProvenance(
                provider=self.name,
                dataset="rate_curve",
                retrieved_at_utc=retrieved_at,
                cache_status=self.cache_status(date=date, max_age_days=max_age_days),
                source_labels=tuple(observation.series_id for observation in observations),
                currency="USD",
                reporting_date=curve_date.isoformat() if curve_date else "latest",
                transformation_steps=(
                    "FRED observations retrieval",
                    "percentage yield to decimal rate conversion",
                    "maturity sorting",
                    "linear interpolation ready curve",
                ),
                request={
                    "date": date_label,
                    "refresh_policy": refresh_policy,
                    "max_age_days": max_age_days,
                    "cache_mode": self.cache_mode,
                },
            ),
        )

    def cache_status(
        self, *, date: str | date = "latest", max_age_days: float | None = 1.0
    ) -> dict[str, object]:
        """Return memory and disk cache status for all configured FRED series."""
        date_label = _date_label(date)
        series_status: dict[str, object] = {}
        for maturity, series_id in sorted(self.series_by_maturity.items()):
            memory_key = (series_id, date_label)
            disk_status = (
                self.cache_store.observation_status(
                    series_id, date_label, max_age_days=max_age_days
                )
                if self.cache_store is not None
                else None
            )
            series_status[series_id] = {
                "maturity_years": maturity,
                "in_memory": memory_key in self._memory_cache,
                "disk": disk_status,
            }
        return {"date": date_label, "series": series_status}

    def clear_cache(self, *, date: str | date = "latest") -> None:
        """Clear memory and disk observations for the configured date label."""
        date_label = _date_label(date)
        for series_id in self.series_by_maturity.values():
            self._memory_cache.pop((series_id, date_label), None)
            if self.cache_store is not None:
                self.cache_store.clear_observation(series_id, date_label)

    def _observation_for_series(
        self,
        series_id: str,
        maturity: float,
        *,
        date_label: str,
        requested_date: str | date,
        refresh_policy: FredRefreshPolicy,
        max_age_days: float | None,
    ) -> FredObservation:
        """Resolve one observation from memory, disk, or a live FRED request."""
        memory_key = (series_id, date_label)
        if refresh_policy != "refresh" and memory_key in self._memory_cache:
            return self._memory_cache[memory_key]
        if refresh_policy != "refresh" and self.cache_store is not None:
            cached_observation = self.cache_store.load_observation(
                series_id,
                date_label,
                max_age_days=max_age_days if refresh_policy == "if_stale" else None,
            )
            if cached_observation is not None:
                self._memory_cache[memory_key] = cached_observation
                return cached_observation
        if refresh_policy == "cache_only":
            raise RatesProviderError(
                f"No cached FRED observation is available for {series_id} and date={date_label}."
            )
        observation = self._fetch_observation(series_id, maturity, requested_date=requested_date)
        if self.cache_mode in {"memory", "disk"}:
            self._memory_cache[memory_key] = observation
        if self.cache_store is not None:
            self.cache_store.save_observation(date_label, observation)
        return observation

    def _fetch_observation(
        self, series_id: str, maturity: float, *, requested_date: str | date
    ) -> FredObservation:
        """Fetch and parse one valid FRED observation."""
        payload = self._request_json(
            _fred_observations_url(series_id, requested_date, self._api_key())
        )
        observations = payload.get("observations")
        if not isinstance(observations, list):
            raise RatesProviderError(f"FRED response for {series_id} did not contain observations.")
        for raw_observation in observations:
            try:
                raw_value = raw_observation.get("value")
                if raw_value in {None, ".", ""}:
                    continue
                raw_percent = float(raw_value)
                if not np.isfinite(raw_percent):
                    continue
                observation_date = date.fromisoformat(str(raw_observation["date"]))
                return FredObservation(
                    series_id=series_id,
                    maturity_years=float(maturity),
                    observation_date=observation_date,
                    annual_rate=raw_percent / 100.0,
                    raw_value_percent=raw_percent,
                )
            except (KeyError, TypeError, ValueError):
                continue
        raise RatesProviderError(f"No valid FRED observation found for {series_id}.")

    def _request_json(self, url: str) -> dict[str, Any]:
        """Request one FRED JSON endpoint and translate failures."""
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                text = response.read().decode(charset)
        except urllib.error.HTTPError as error:
            raise RatesProviderError(
                f"FRED request failed with HTTP {error.code}: {url}"
            ) from error
        except urllib.error.URLError as error:
            raise RatesProviderError(f"FRED request failed: {error}") from error
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise RatesProviderError("FRED response was not valid JSON.") from error
        if "error_code" in payload or "error_message" in payload:
            raise RatesProviderError(
                f"FRED API error {payload.get('error_code')}: {payload.get('error_message')}"
            )
        return payload

    def _api_key(self) -> str:
        """Return the configured FRED API key or raise an actionable error."""
        if not self.api_key:
            raise RatesProviderError(
                "FRED requests require an API key. Pass api_key=... or set FRED_API_KEY. "
                "Use refresh_policy='cache_only' to avoid network requests when cached data exists."
            )
        return self.api_key


class ManualRateProvider:
    """Provider object that returns a manually supplied curve without network access."""

    name = "manual"

    def __init__(self, rates_by_maturity: Mapping[float, float]) -> None:
        """Store manual annual decimal rates keyed by maturity in years."""
        self.rates_by_maturity = dict(rates_by_maturity)

    def rate_curve(self, *, date: str | date = "latest", **_: object) -> RateCurve:
        """Return the configured manual curve for tests and examples."""
        curve_date = None if date == "latest" else _parse_curve_date(date)
        return RateCurve.from_rates(
            self.rates_by_maturity,
            curve_date=curve_date,
            provider_name=self.name,
        )


def get_rate_curve(
    *,
    provider: str | FredRateProvider | ManualRateProvider = "fred",
    date: str | date = "latest",
    api_key: str | None = None,
    series_by_maturity: Mapping[float, str] | None = None,
    cache_mode: FredCacheMode = "memory",
    cache_directory: str | Path | None = None,
    refresh_policy: FredRefreshPolicy = "if_stale",
    max_age_days: float | None = 1.0,
) -> RateCurve:
    """Return a provider-backed risk-free-rate curve.

    Parameters
    ----------
    provider : {"fred"} or provider object, default="fred"
        Provider name or object exposing ``rate_curve``. FRED is the built-in
        live provider; manual providers can be used for deterministic examples.
    date : str | date, default="latest"
        Curve date. A concrete date uses the latest available observation on or
        before that date.
    api_key : str | None, default=None
        FRED API key. When omitted, ``FRED_API_KEY`` is read by the provider.
    series_by_maturity : mapping of float to str, optional
        Custom FRED series mapping from maturity in years to series ID.
    cache_mode : {"none", "memory", "disk"}, default="memory"
        Observation cache mode.
    cache_directory : str | pathlib.Path | None, default=None
        Disk cache directory used when ``cache_mode='disk'``.
    refresh_policy : {"cache_only", "if_missing", "if_stale", "refresh"}, default="if_stale"
        Cache policy passed to the provider.
    max_age_days : float | None, default=1.0
        Cache freshness threshold.

    Returns
    -------
    RateCurve
        Provider-neutral curve exposing ``zero_rate`` and ``discount_factor``.
    """
    if isinstance(provider, str):
        provider_name = provider.lower()
        if provider_name != "fred":
            raise RatesValidationError("provider must be 'fred' or a provider object.")
        provider_object: Any = FredRateProvider(
            api_key=api_key,
            series_by_maturity=series_by_maturity,
            cache_mode=cache_mode,
            cache_directory=cache_directory,
        )
    else:
        provider_object = provider
    rate_curve_method = getattr(provider_object, "rate_curve", None)
    if not callable(rate_curve_method):
        raise RatesValidationError("provider object must expose a rate_curve method.")
    return rate_curve_method(
        date=date,
        refresh_policy=refresh_policy,
        max_age_days=max_age_days,
    )


def _fred_observations_url(series_id: str, requested_date: str | date, api_key: str) -> str:
    """Build one FRED series observations URL with descending observations."""
    parameters: dict[str, object] = {
        "series_id": _normalize_series_id(series_id),
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 30,
    }
    if requested_date != "latest":
        parameters["observation_end"] = _parse_curve_date(requested_date).isoformat()
    return _FRED_OBSERVATIONS_URL + "?" + urllib.parse.urlencode(parameters)


def _normalize_series_id(series_id: object) -> str:
    """Normalize one FRED series ID to uppercase text."""
    normalized = str(series_id).strip().upper()
    if not normalized:
        raise RatesValidationError("FRED series IDs cannot be blank.")
    return normalized


def _date_label(value: str | date) -> str:
    """Return the stable cache label for a curve-date request."""
    if value == "latest":
        return "latest"
    return _parse_curve_date(value).isoformat()


def _parse_curve_date(value: str | date | None) -> date | None:
    """Parse a concrete curve date or return ``None`` for latest/manual curves."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped == "latest":
            return None
        try:
            return date.fromisoformat(stripped)
        except ValueError as error:
            raise RatesValidationError(
                "Dates must be 'latest' or ISO format YYYY-MM-DD."
            ) from error
    raise RatesValidationError("Dates must be 'latest', datetime.date, or ISO format text.")


def _parse_datetime(value: object) -> datetime | None:
    """Parse ISO datetime text used by cache metadata."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _is_stale(retrieved_at: datetime | None, max_age_days: float | None) -> bool:
    """Return whether a cache timestamp exceeds the configured age limit."""
    if retrieved_at is None:
        return True
    if max_age_days is None:
        return False
    age_seconds = (datetime.now(UTC) - retrieved_at.astimezone(UTC)).total_seconds()
    return age_seconds > float(max_age_days) * 86400.0


def _validate_positive_float(value: float, name: str) -> float:
    """Return one finite positive float or raise a validation error."""
    numeric_value = float(value)
    if not np.isfinite(numeric_value) or numeric_value <= 0.0:
        raise RatesValidationError(f"{name} must be finite and positive.")
    return numeric_value


__all__ = sorted(
    set(_financial_math_all)
    | {
        "DataProvenance",
        "DiscountCompounding",
        "FredCacheMode",
        "FredJsonCacheStore",
        "FredObservation",
        "FredRateProvider",
        "FredRefreshPolicy",
        "ManualRateProvider",
        "RateCurve",
        "RateExtrapolation",
        "RateInterpolation",
        "RatesProviderError",
        "RatesValidationError",
        "get_rate_curve",
    }
)
