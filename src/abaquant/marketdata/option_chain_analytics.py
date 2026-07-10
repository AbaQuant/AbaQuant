"""Listed-option-chain analytics that connect provider data to pricing models.

The module turns normalized listed option chains into applied analytics such as
implied-volatility smiles, term structures, rich/cheap comparisons, and open-
interest grids. It does not retrieve data directly; retrieval remains the
responsibility of ``TickerOptionAnalytics`` and the configured market provider.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance
from abaquant.derivatives import black_scholes

from .errors import MarketDataError

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class OptionSkewSummary:
    """Linear implied-volatility skew summary for one listed option slice.

    Attributes
    ----------
    option_type : {"call", "put"}
        Option family used for the fitted slice.
    observations : int
        Number of finite observations used in the fit.
    slope : float
        Least-squares slope of implied volatility against log-moneyness.
    intercept : float
        Least-squares intercept of implied volatility against log-moneyness.
    at_the_money_iv : float | None
        Implied volatility at the observation with moneyness closest to one.
    """

    option_type: OptionType
    observations: int
    slope: float
    intercept: float
    at_the_money_iv: float | None

    def as_dict(self) -> dict[str, float | int | str | None]:
        """Return a serialization-friendly representation of the skew summary."""
        return {
            "option_type": self.option_type,
            "observations": self.observations,
            "slope": self.slope,
            "intercept": self.intercept,
            "at_the_money_iv": self.at_the_money_iv,
        }


@dataclass(frozen=True)
class OptionChainAnalytics:
    """Provider-independent analytics for one ticker's listed option chains.

    Parameters
    ----------
    ticker : object
        Applied ticker object exposing ``symbol``, ``spot()``, and
        ``options.chain(...)``.
    expiry : str
        Primary expiration date in ISO ``YYYY-MM-DD`` form.
    chain : pandas.DataFrame
        Normalized raw option chain for ``expiry``.

    Notes
    -----
    This object keeps market-data retrieval separate from option analytics. The
    primary chain is supplied at construction, while multi-expiry methods fetch
    extra expirations lazily through ``ticker.options.chain`` only when needed.
    """

    ticker: object
    expiry: str
    chain: pd.DataFrame
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Store default provenance for the primary option-chain snapshot."""
        if self.provenance is None:
            provider = getattr(getattr(self.ticker, "provider", None), "name", "marketdata")
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider=provider,
                    dataset="option_chain",
                    source_labels=tuple(
                        str(value)
                        for value in self.chain.get("option_type", pd.Series(dtype=object))
                        .dropna()
                        .unique()
                    ),
                    reporting_date=self.expiry,
                    transformation_steps=(
                        "provider option-chain retrieval",
                        "contract normalization",
                        "option-chain analytics enrichment",
                    ),
                    request={
                        "symbol": getattr(self.ticker, "symbol", None),
                        "expiry": self.expiry,
                        "shape": tuple(int(value) for value in self.chain.shape),
                    },
                ),
            )

    def enriched_chain(self, *, spot_price: float | None = None) -> pd.DataFrame:
        """Return the chain with midpoint, moneyness, and log-moneyness columns.

        Parameters
        ----------
        spot_price : float | None, default=None
            Current underlying price. When omitted, ``ticker.spot()`` is used.

        Returns
        -------
        pandas.DataFrame
            Copy of the normalized option chain with derived ``market_price``,
            ``moneyness``, ``log_moneyness``, and ``days_to_expiry`` columns.
        """
        spot = _positive_float(
            spot_price if spot_price is not None else self.ticker.spot(), "spot_price"
        )
        frame = _ensure_chain_columns(self.chain).copy()
        frame["market_price"] = _market_price(frame)
        frame["moneyness"] = spot / frame["strike"]
        frame["log_moneyness"] = np.log(frame["moneyness"])
        frame["spot_price"] = spot
        frame["expiry"] = self.expiry
        frame["days_to_expiry"] = _days_to_expiry(self.expiry)
        return frame

    def iv_smile(
        self,
        *,
        option_type: OptionType = "call",
        spot_price: float | None = None,
        min_open_interest: float | None = None,
    ) -> pd.DataFrame:
        """Return implied volatility by strike and moneyness for one expiry.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Listed option family used for the smile.
        spot_price : float | None, default=None
            Current underlying price used to compute moneyness.
        min_open_interest : float | None, default=None
            Optional minimum open-interest filter. If omitted, no liquidity
            filter is applied.

        Returns
        -------
        pandas.DataFrame
            Sorted table with ``strike``, ``moneyness``, ``log_moneyness``,
            ``implied_volatility``, ``market_price``, and ``open_interest`` when
            available.
        """
        frame = self._slice(option_type=option_type, spot_price=spot_price)
        frame = _filter_positive_iv(frame)
        if min_open_interest is not None and "open_interest" in frame.columns:
            frame = frame[frame["open_interest"] >= float(min_open_interest)].copy()
        if frame.empty:
            raise MarketDataError(
                f"No usable implied-volatility smile for {self.ticker.symbol} {self.expiry}."
            )
        columns = [
            column
            for column in (
                "expiry",
                "option_type",
                "strike",
                "moneyness",
                "log_moneyness",
                "days_to_expiry",
                "implied_volatility",
                "market_price",
                "open_interest",
                "volume",
            )
            if column in frame.columns
        ]
        return frame[columns].sort_values("strike").reset_index(drop=True)

    def iv_surface(
        self,
        *,
        expiries: Sequence[str] | None = None,
        option_type: OptionType = "call",
        spot_price: float | None = None,
    ) -> pd.DataFrame:
        """Return a long-form implied-volatility surface across expirations.

        Parameters
        ----------
        expiries : sequence of str | None, default=None
            Expiration dates to include. When omitted, all provider-listed
            expirations are requested. If the provider cannot supply them, the
            primary ``expiry`` is used.
        option_type : {"call", "put"}, default="call"
            Option family used for the surface.
        spot_price : float | None, default=None
            Current underlying price used to compute moneyness.

        Returns
        -------
        pandas.DataFrame
            Long-form surface with one row per contract containing ``expiry``,
            ``strike``, ``moneyness``, ``days_to_expiry``, and
            ``implied_volatility``.
        """
        selected_expiries = list(expiries) if expiries is not None else self._available_expiries()
        if not selected_expiries:
            selected_expiries = [self.expiry]
        frames: list[pd.DataFrame] = []
        for expiry in selected_expiries:
            try:
                analytics = self if expiry == self.expiry else self._for_expiry(expiry)
                frame = analytics.iv_smile(option_type=option_type, spot_price=spot_price)
                frames.append(frame)
            except MarketDataError:
                continue
        if not frames:
            raise MarketDataError(f"No usable implied-volatility surface for {self.ticker.symbol}.")
        return (
            pd.concat(frames, ignore_index=True)
            .sort_values(["days_to_expiry", "strike"])
            .reset_index(drop=True)
        )

    def skew(
        self,
        *,
        option_type: OptionType = "call",
        spot_price: float | None = None,
    ) -> OptionSkewSummary:
        """Estimate linear implied-volatility skew against log-moneyness.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Option family used for the fitted smile.
        spot_price : float | None, default=None
            Current underlying price used to compute moneyness.

        Returns
        -------
        OptionSkewSummary
            Least-squares slope/intercept and the closest-to-the-money IV.
        """
        smile = self.iv_smile(option_type=option_type, spot_price=spot_price)
        if len(smile) < 2:
            raise MarketDataError(
                "At least two finite IV observations are required to estimate skew."
            )
        x = smile["log_moneyness"].to_numpy(dtype=float)
        y = smile["implied_volatility"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(x, y, deg=1)
        atm_index = (smile["moneyness"] - 1.0).abs().idxmin()
        return OptionSkewSummary(
            option_type=option_type,
            observations=len(smile),
            slope=float(slope),
            intercept=float(intercept),
            at_the_money_iv=float(smile.loc[atm_index, "implied_volatility"]),
        )

    def term_structure(
        self,
        *,
        strike: float | None = None,
        option_type: OptionType = "call",
        expiries: Sequence[str] | None = None,
        spot_price: float | None = None,
    ) -> pd.DataFrame:
        """Return implied volatility across expirations for one strike.

        Parameters
        ----------
        strike : float | None, default=None
            Target strike. When omitted, the current spot price is used and the
            nearest listed strike is selected for each expiry.
        option_type : {"call", "put"}, default="call"
            Option family used for the term structure.
        expiries : sequence of str | None, default=None
            Expirations to include. When omitted, all provider-listed
            expirations are requested.
        spot_price : float | None, default=None
            Current spot price. Used as the default target strike and for
            moneyness calculations.

        Returns
        -------
        pandas.DataFrame
            Table with nearest-strike IV by expiry.
        """
        spot = _positive_float(
            spot_price if spot_price is not None else self.ticker.spot(), "spot_price"
        )
        target_strike = spot if strike is None else _positive_float(strike, "strike")
        surface = self.iv_surface(expiries=expiries, option_type=option_type, spot_price=spot)
        rows: list[pd.Series] = []
        for _expiry, group in surface.groupby("expiry", sort=False):
            nearest_index = (group["strike"] - target_strike).abs().idxmin()
            rows.append(group.loc[nearest_index])
        result = pd.DataFrame(rows).sort_values("days_to_expiry").reset_index(drop=True)
        return result[
            [
                column
                for column in (
                    "expiry",
                    "days_to_expiry",
                    "option_type",
                    "strike",
                    "moneyness",
                    "implied_volatility",
                    "market_price",
                )
                if column in result.columns
            ]
        ]

    def rich_cheap_table(
        self,
        *,
        model: Literal["bsm"] = "bsm",
        risk_free_rate: float,
        option_type: OptionType | None = None,
        volatility: float | Literal["listed"] = "listed",
        dividend_yield: float = 0.0,
        spot_price: float | None = None,
    ) -> pd.DataFrame:
        """Compare listed market prices with model values contract by contract.

        Parameters
        ----------
        model : {"bsm"}, default="bsm"
            Pricing model used for theoretical values. Only Black--Scholes--
            Merton is supported in this release.
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        option_type : {"call", "put"} | None, default=None
            Optional option family filter. When omitted, calls and puts are
            included.
        volatility : float or {"listed"}, default="listed"
            Volatility used in the BSM model. ``"listed"`` uses each contract's
            provider-reported implied volatility.
        dividend_yield : float, default=0.0
            Continuous dividend yield in decimal annual units.
        spot_price : float | None, default=None
            Current underlying price. When omitted, ``ticker.spot()`` is used.

        Returns
        -------
        pandas.DataFrame
            Contract-level table with market price, model value, difference,
            relative difference, and rich/cheap label. Positive differences mean
            the listed contract is rich versus the model value.
        """
        if model != "bsm":
            raise ValueError("Only model='bsm' is supported.")
        spot = _positive_float(
            spot_price if spot_price is not None else self.ticker.spot(), "spot_price"
        )
        maturity = max(_days_to_expiry(self.expiry) / 365.25, 1e-12)
        frame = self.enriched_chain(spot_price=spot)
        if option_type is not None:
            frame = frame[frame["option_type"] == option_type].copy()
        if frame.empty:
            raise MarketDataError("No contracts available for rich/cheap analytics.")
        model_values: list[float] = []
        used_volatilities: list[float] = []
        for row in frame.itertuples(index=False):
            contract_volatility = (
                float(volatility)
                if volatility != "listed"
                else float(getattr(row, "implied_volatility", np.nan))
            )
            if not np.isfinite(contract_volatility) or contract_volatility <= 0.0:
                model_values.append(np.nan)
                used_volatilities.append(np.nan)
                continue
            value = black_scholes(
                spot,
                float(row.strike),
                float(risk_free_rate),
                contract_volatility,
                maturity,
                is_call=row.option_type == "call",
                q=float(dividend_yield),
            )
            model_values.append(float(value))
            used_volatilities.append(contract_volatility)
        frame["model"] = model
        frame["model_volatility"] = used_volatilities
        frame["model_value"] = model_values
        frame["rich_cheap"] = frame["market_price"] - frame["model_value"]
        frame["rich_cheap_pct"] = frame["rich_cheap"] / frame["model_value"].replace(0.0, np.nan)
        frame["rich_cheap_label"] = np.where(frame["rich_cheap"] > 0.0, "rich", "cheap")
        frame.loc[~np.isfinite(frame["rich_cheap"]), "rich_cheap_label"] = "unpriced"
        columns = [
            column
            for column in (
                "expiry",
                "option_type",
                "strike",
                "moneyness",
                "market_price",
                "implied_volatility",
                "model_volatility",
                "model_value",
                "rich_cheap",
                "rich_cheap_pct",
                "rich_cheap_label",
                "open_interest",
                "volume",
            )
            if column in frame.columns
        ]
        return frame[columns].sort_values("rich_cheap", ascending=False).reset_index(drop=True)

    def open_interest_grid(
        self,
        *,
        expiries: Sequence[str] | None = None,
        option_type: OptionType | None = None,
        spot_price: float | None = None,
    ) -> pd.DataFrame:
        """Return open interest by expiry, strike, and option type.

        Parameters
        ----------
        expiries : sequence of str | None, default=None
            Expiration dates to include. When omitted, all provider-listed
            expirations are requested.
        option_type : {"call", "put"} | None, default=None
            Optional option family filter.
        spot_price : float | None, default=None
            Current underlying price used to compute moneyness.

        Returns
        -------
        pandas.DataFrame
            Long-form table suitable for open-interest heatmaps.
        """
        selected_expiries = list(expiries) if expiries is not None else self._available_expiries()
        if not selected_expiries:
            selected_expiries = [self.expiry]
        frames: list[pd.DataFrame] = []
        for expiry in selected_expiries:
            try:
                analytics = self if expiry == self.expiry else self._for_expiry(expiry)
                frame = analytics.enriched_chain(spot_price=spot_price)
                if option_type is not None:
                    frame = frame[frame["option_type"] == option_type].copy()
                if "open_interest" in frame.columns:
                    frames.append(frame)
            except MarketDataError:
                continue
        if not frames:
            raise MarketDataError("No open-interest observations are available.")
        result = pd.concat(frames, ignore_index=True)
        columns = [
            column
            for column in (
                "expiry",
                "days_to_expiry",
                "option_type",
                "strike",
                "moneyness",
                "open_interest",
            )
            if column in result.columns
        ]
        return (
            result[columns]
            .sort_values(["days_to_expiry", "strike", "option_type"])
            .reset_index(drop=True)
        )

    def visualize(
        self,
        *,
        chart: Literal[
            "iv_smile", "iv_surface", "term_structure", "rich_cheap", "open_interest_heatmap"
        ] = "iv_smile",
        option_type: OptionType = "call",
        metric: str = "implied_volatility",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
        **kwargs: object,
    ):
        """Visualize a listed-option-chain analytic table.

        Parameters
        ----------
        chart : {"iv_smile", "iv_surface", "term_structure", "rich_cheap", "open_interest_heatmap"}, default="iv_smile"
            Listed-option-chain diagnostic to render.
        option_type : {"call", "put"}, default="call"
            Option family used when the selected chart accepts a family filter.
        metric : str, default="implied_volatility"
            Surface metric used by ``chart="iv_surface"``.
        backend, theme, save_path, filename
            Standard AbaQuant visualization overrides.
        **kwargs : object
            Additional arguments forwarded to the underlying analytics method.

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure
            Backend-native figure object.
        """
        from abaquant.visualization import visualize_option_chain_analytics

        return visualize_option_chain_analytics(
            self,
            chart=chart,
            option_type=option_type,
            metric=metric,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
            **kwargs,
        )

    def calibrate_bsm_flat_vol(
        self,
        *,
        option_type: OptionType = "call",
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        objective: Literal["price", "iv"] = "price",
        spot_price: float | None = None,
        maturity_years: float | None = None,
        **kwargs: object,
    ):
        """Calibrate one flat Black--Scholes--Merton volatility to the chain.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Listed option family used during the fit.
        risk_free_rate : float
            Continuously compounded annual risk-free rate.
        dividend_yield : float, default=0.0
            Continuous annual dividend yield.
        objective : {"price", "iv"}, default="price"
            Whether to fit listed premiums or listed implied volatilities.
        spot_price : float | None, default=None
            Spot price override. When omitted, ``ticker.spot()`` is used.
        maturity_years : float | None, default=None
            Time to expiration override. When omitted, days to the analytics
            object's primary expiry are used.
        **kwargs : object
            Additional keyword arguments forwarded to
            :class:`abaquant.derivatives.calibration.BSMFlatVolCalibration`.

        Returns
        -------
        CalibrationResult
            Fitted flat-volatility calibration result.
        """
        from abaquant.derivatives.calibration import BSMFlatVolCalibration

        return BSMFlatVolCalibration(
            self,
            spot_price=spot_price if spot_price is not None else self.ticker.spot(),
            maturity_years=maturity_years
            if maturity_years is not None
            else max(_days_to_expiry(self.expiry) / 365.25, 1e-12),
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,
            objective=objective,
            **kwargs,
        ).fit()

    def calibrate_sabr(
        self,
        *,
        option_type: OptionType = "call",
        beta: float = 1.0,
        risk_free_rate: float = 0.0,
        dividend_yield: float = 0.0,
        spot_price: float | None = None,
        forward_price: float | None = None,
        maturity_years: float | None = None,
        **kwargs: object,
    ):
        """Calibrate SABR smile parameters to listed implied volatilities.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Listed option family used during the fit.
        beta : float, default=1.0
            Fixed SABR elasticity parameter.
        risk_free_rate : float, default=0.0
            Continuously compounded annual risk-free rate.
        dividend_yield : float, default=0.0
            Continuous annual dividend yield.
        spot_price : float | None, default=None
            Spot price override. When omitted, ``ticker.spot()`` is used.
        forward_price : float | None, default=None
            Forward price override. When omitted, it is inferred from spot and
            carry assumptions.
        maturity_years : float | None, default=None
            Time to expiration override.
        **kwargs : object
            Additional keyword arguments forwarded to
            :class:`abaquant.derivatives.calibration.SABRSmileCalibration`.

        Returns
        -------
        CalibrationResult
            SABR calibration result.
        """
        from abaquant.derivatives.calibration import SABRSmileCalibration

        return SABRSmileCalibration(
            self,
            spot_price=spot_price if spot_price is not None else self.ticker.spot(),
            forward_price=forward_price,
            maturity_years=maturity_years
            if maturity_years is not None
            else max(_days_to_expiry(self.expiry) / 365.25, 1e-12),
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            beta=beta,
            option_type=option_type,
            **kwargs,
        ).fit()

    def calibrate_heston(
        self,
        *,
        option_type: OptionType = "call",
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        spot_price: float | None = None,
        maturity_years: float | None = None,
        objective: Literal["price", "iv"] = "iv",
        **kwargs: object,
    ):
        """Calibrate Heston parameters to listed option observations.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Listed option family used during the fit.
        risk_free_rate : float
            Continuously compounded annual risk-free rate.
        dividend_yield : float, default=0.0
            Continuous annual dividend yield.
        spot_price : float | None, default=None
            Spot price override. When omitted, ``ticker.spot()`` is used.
        maturity_years : float | None, default=None
            Time to expiration override.
        objective : {"price", "iv"}, default="iv"
            Whether the fit targets premiums or implied volatilities.
        **kwargs : object
            Additional keyword arguments forwarded to
            :class:`abaquant.derivatives.calibration.HestonCalibration`.

        Returns
        -------
        CalibrationResult
            Heston stochastic-volatility calibration result.
        """
        from abaquant.derivatives.calibration import HestonCalibration

        return HestonCalibration(
            self,
            spot_price=spot_price if spot_price is not None else self.ticker.spot(),
            maturity_years=maturity_years
            if maturity_years is not None
            else max(_days_to_expiry(self.expiry) / 365.25, 1e-12),
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,
            objective=objective,
            **kwargs,
        ).fit()

    def _slice(self, *, option_type: OptionType, spot_price: float | None) -> pd.DataFrame:
        """Return one enriched option-family slice."""
        if option_type not in {"call", "put"}:
            raise ValueError("option_type must be 'call' or 'put'.")
        frame = self.enriched_chain(spot_price=spot_price)
        frame = frame[frame["option_type"] == option_type].copy()
        if frame.empty:
            raise MarketDataError(f"No {option_type} contracts found for {self.expiry}.")
        return frame

    def _available_expiries(self) -> list[str]:
        """Return provider expirations with the primary expiry first when present."""
        try:
            expiries = list(self.ticker.options.expirations())
        except Exception:
            expiries = [self.expiry]
        if self.expiry not in expiries:
            expiries.insert(0, self.expiry)
        return expiries

    def _for_expiry(self, expiry: str) -> OptionChainAnalytics:
        """Return a sibling analytics object for another expiration."""
        return type(self)(self.ticker, expiry, self.ticker.options.chain(expiry))


def _ensure_chain_columns(chain: pd.DataFrame) -> pd.DataFrame:
    """Validate a normalized option-chain table and standardize common labels."""
    if not isinstance(chain, pd.DataFrame) or chain.empty:
        raise MarketDataError("option chain must be a non-empty pandas DataFrame.")
    frame = chain.copy()
    rename_map = {
        "lastprice": "last_price",
        "lastPrice": "last_price",
        "impliedvolatility": "implied_volatility",
        "impliedVolatility": "implied_volatility",
        "openinterest": "open_interest",
        "openInterest": "open_interest",
        "midpoint": "mid_price",
    }
    frame = frame.rename(
        columns={column: rename_map.get(str(column), str(column)) for column in frame.columns}
    )
    if frame.columns.has_duplicates:
        collapsed = pd.DataFrame(index=frame.index)
        for column in dict.fromkeys(frame.columns):
            duplicate_columns = frame.loc[:, frame.columns == column]
            if duplicate_columns.shape[1] == 1:
                collapsed[column] = duplicate_columns.iloc[:, 0]
            else:
                collapsed[column] = duplicate_columns.iloc[:, -1]
        frame = collapsed
    required_columns = {"strike", "option_type"}
    missing = required_columns - set(frame.columns)
    if missing:
        raise MarketDataError(f"option chain is missing required columns: {sorted(missing)}")
    frame["strike"] = pd.to_numeric(frame["strike"], errors="coerce")
    frame = frame[frame["strike"] > 0.0].copy()
    for column in (
        "bid",
        "ask",
        "last_price",
        "mid_price",
        "implied_volatility",
        "open_interest",
        "volume",
    ):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "implied_volatility" in frame.columns:
        frame["implied_volatility"] = frame["implied_volatility"].where(
            np.isfinite(frame["implied_volatility"]) & (frame["implied_volatility"] > 0.0)
        )
    if frame.empty:
        raise MarketDataError("option chain has no valid positive strikes.")
    return frame.reset_index(drop=True)


def _market_price(frame: pd.DataFrame) -> pd.Series:
    """Return market premium using midpoint, then bid/ask midpoint, then last price."""
    if "mid_price" in frame.columns:
        market = frame["mid_price"].copy()
    else:
        market = pd.Series(np.nan, index=frame.index, dtype=float)
    if "bid" in frame.columns and "ask" in frame.columns:
        bid_ask_midpoint = ((frame["bid"] + frame["ask"]) / 2.0).where(
            (frame["bid"] > 0.0) & (frame["ask"] > 0.0) & (frame["ask"] >= frame["bid"])
        )
        market = market.where(np.isfinite(market) & (market > 0.0), bid_ask_midpoint)
    if "last_price" in frame.columns:
        market = market.where(np.isfinite(market) & (market > 0.0), frame["last_price"])
    return pd.to_numeric(market, errors="coerce")


def _filter_positive_iv(frame: pd.DataFrame) -> pd.DataFrame:
    """Return only contracts with finite positive implied volatility."""
    if "implied_volatility" not in frame.columns:
        raise MarketDataError("Option chain has no implied_volatility column.")
    return frame[
        np.isfinite(frame["implied_volatility"]) & (frame["implied_volatility"] > 0.0)
    ].copy()


def _positive_float(value: object, name: str) -> float:
    """Return one positive finite float or raise a domain error."""
    numeric_value = float(value)
    if not np.isfinite(numeric_value) or numeric_value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return numeric_value


def _days_to_expiry(expiry: str) -> int:
    """Return non-negative calendar days from today to an ISO expiry date."""
    expiry_date = datetime.strptime(str(expiry), "%Y-%m-%d").date()
    return max((expiry_date - date.today()).days, 0)
