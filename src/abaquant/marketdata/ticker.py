"""Lazy single-ticker applied market-data interface.

Purpose
-------
The module provides a ``MarketTicker`` object with namespaces for spot quotes, price history, listed options, and delegation to pure option-pricing functions.

Conventions
-----------
Symbols are normalized to uppercase. Volatility is always explicit: a decimal input, realized historical volatility, or listed implied volatility. Rates and yields are decimal annual quantities; maturity is in years.

Scope and limitations
---------------------
No market request occurs at object construction. Provider values can be missing or stale, and model outputs are not investment recommendations.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance
from abaquant.credit import (
    CreditAnalysisInputs,
    CreditProxyAssessment,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives import (
    black_scholes,
    calculate_greeks,
    compare_all_models,
    implied_volatility_bsm,
    realized_vol,
)

from .errors import MarketDataError
from .financials import CacheMode, FinancialStatementRepository, FinancialStatements
from .option_chain_analytics import OptionChainAnalytics
from .providers import (
    FinancialStatementProvider,
    MarketDataProvider,
    SecXbrlProvider,
    YahooFinanceProvider,
)
from .sessions import TickerConfiguration, TickerIdentity, TickerSession

OptionType = Literal["call", "put"]
VolatilityInput = float | Literal["realized", "market"] | None


def get_ticker(
    symbol: str,
    provider: str | MarketDataProvider = "yahoo",
    *,
    fundamentals_provider: str | FinancialStatementProvider | None = None,
    sec_user_agent: str | None = None,
    sec_cik_by_symbol: dict[str, str] | None = None,
    financial_cache: CacheMode = "memory",
    cache_directory: str | None = None,
) -> MarketTicker:
    """Create a lazy applied interface for one normalized ticker symbol.

    Parameters
    ----------
    symbol : str
        Ticker symbol to normalize and query.
    provider : str | MarketDataProvider, default='yahoo'
        Provider name or object satisfying the market-data provider protocol.
    fundamentals_provider : str | FinancialStatementProvider | None, default=None
        Optional provider used only for financial statements and credit-input
        construction. Use ``"sec"`` to retrieve SEC EDGAR/XBRL Company Facts
        while retaining the main provider for quotes, history, and options.
    sec_user_agent : str | None, default=None
        Declared SEC request user agent when ``fundamentals_provider="sec"``.
        If omitted, the SEC provider reads ``ABAQUANT_SEC_USER_AGENT``.
    sec_cik_by_symbol : dict[str, str] | None, default=None
        Optional symbol-to-CIK mapping used by the SEC provider to avoid ticker
        lookup requests.
    financial_cache : {'none', 'memory', 'disk'}, default='memory'
        Financial-statement cache mode. Disk mode persists normalized statement
        snapshots between Python sessions.
    cache_directory : str | None, default=None
        Optional directory used when ``financial_cache='disk'``.

    Returns
    -------
    MarketTicker
        Lazy ticker object. Constructing it does not fetch remote data.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    clean_symbol = _normalize_symbol(symbol)
    if isinstance(provider, str):
        if provider.lower() != "yahoo":
            raise ValueError("Only provider='yahoo' is supported by this market-data factory.")
        provider_obj: MarketDataProvider = YahooFinanceProvider()
    else:
        provider_obj = provider
    financial_provider = _resolve_fundamentals_provider(
        fundamentals_provider,
        default_provider=provider_obj,
        sec_user_agent=sec_user_agent,
        sec_cik_by_symbol=sec_cik_by_symbol,
        financial_cache=financial_cache,
        cache_directory=cache_directory,
    )
    return MarketTicker(
        TickerIdentity(clean_symbol, getattr(provider_obj, "name", type(provider_obj).__name__)),
        provider_obj,
        TickerConfiguration(financial_cache_mode=financial_cache, cache_directory=cache_directory),
        financial_statement_provider=financial_provider,
    )


def _resolve_fundamentals_provider(
    provider: str | FinancialStatementProvider | None,
    *,
    default_provider: MarketDataProvider,
    sec_user_agent: str | None,
    sec_cik_by_symbol: dict[str, str] | None,
    financial_cache: CacheMode,
    cache_directory: str | None,
) -> FinancialStatementProvider:
    """Resolve the statement provider used by ``MarketTicker.financials``."""
    if provider is None:
        return default_provider
    if isinstance(provider, str):
        provider_name = provider.lower()
        if provider_name == "yahoo":
            return default_provider
        if provider_name == "sec":
            return SecXbrlProvider(
                user_agent=sec_user_agent,
                cik_by_symbol=sec_cik_by_symbol,
                cache_mode=financial_cache,
                cache_directory=cache_directory,
            )
        raise ValueError(
            "fundamentals_provider must be None, 'yahoo', 'sec', or a provider object."
        )
    return provider


class MarketTicker:
    """Lazy market-data facade with immutable identity and mutable session state.

    ``identity`` and ``configuration`` never change after construction. The
    separate ``session`` owns cache state, avoiding frozen-object mutation.
    """

    def __init__(
        self,
        identity: TickerIdentity,
        provider: MarketDataProvider,
        configuration: TickerConfiguration,
        session: TickerSession | None = None,
        financial_statement_provider: FinancialStatementProvider | None = None,
    ) -> None:
        """Create a ticker facade without making a provider request."""
        self.identity = identity
        self.provider = provider
        self.configuration = configuration
        self.session = session or TickerSession()
        self.symbol = identity.symbol
        self.provenance = DataProvenance(
            provider=identity.provider_name,
            dataset="market_ticker",
            source_labels=(identity.symbol,),
            transformation_steps=("ticker normalization", "lazy market-data facade construction"),
            request={
                "symbol": identity.symbol,
                "provider_name": identity.provider_name,
                "financial_cache_mode": configuration.financial_cache_mode,
            },
        )
        self.history = TickerHistory(self)
        self.options = TickerOptionAnalytics(self)
        self.fundamentals = TickerFundamentalData(self)
        statement_provider = financial_statement_provider or provider
        repository = FinancialStatementRepository(
            self.symbol,
            statement_provider,
            cache_mode=configuration.financial_cache_mode,
            cache_directory=configuration.cache_directory,
            session=self.session,
        )
        self.financials = FinancialStatements(
            self,
            repository,
            repositories={getattr(statement_provider, "name", "default").lower(): repository},
            default_source=getattr(statement_provider, "name", "default"),
        )
        self.credit = TickerCreditMetrics(self)

    def spot(self) -> float:
        """Return the latest available spot-like quote supplied by the configured provider.

        Returns
        -------
        float
            Computed spot as a scalar in the units implied by the input values.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        provider_quote_info = self.provider.fast_info(self.symbol)
        for quote_field in ("last_price", "lastPrice", "regularMarketPrice", "currentPrice"):
            candidate_spot_price = provider_quote_info.get(quote_field)
            if _is_valid_number(candidate_spot_price):
                return float(candidate_spot_price)

        recent_price_history = self.history.prices(period="5d")
        closing_price_series = _first_column(recent_price_history, "close", "adj close")
        if closing_price_series is None or closing_price_series.dropna().empty:
            raise MarketDataError(f"No usable spot price found for {self.symbol}.")
        return float(closing_price_series.dropna().iloc[-1])

    def dividend_yield(self, default: float = 0.0) -> float:
        """Return the provider dividend yield or the documented fallback.

        Parameters
        ----------
        default : float, default=0.0
            Fallback value used when the provider does not expose a usable value.

        Returns
        -------
        float
            Computed dividend yield as a dimensionless decimal quantity.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        provider_company_info = self.provider.info(self.symbol)
        raw_dividend_yield = provider_company_info.get(
            "dividendYield", provider_company_info.get("trailingAnnualDividendYield", default)
        )
        if not _is_valid_number(raw_dividend_yield):
            return default
        decimal_dividend_yield = float(raw_dividend_yield)
        return (
            decimal_dividend_yield / 100.0
            if decimal_dividend_yield > 1.0
            else decimal_dividend_yield
        )

    def visualize(
        self,
        *,
        period: str | None = "1y",
        start: str | None = None,
        end: str | None = None,
        auto_adjust: bool = True,
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
    ):
        """Return a market-price history figure for this ticker.

        The method fetches history lazily through ``history.prices`` and returns
        a figure without invoking the backend display function.
        """
        from abaquant.visualization import visualize_price_history

        prices = self.history.prices(period=period, start=start, end=end, auto_adjust=auto_adjust)
        return visualize_price_history(
            prices, backend=backend, theme=theme, save_path=save_path, filename=filename
        )


@dataclass(frozen=True)
class TickerHistory:
    """Historical-price and realized-volatility namespace for a market ticker.

    Attributes
    ----------
    ticker : MarketTicker
        Ticker facade supplying the normalized symbol and market-data provider.

    Notes
    -----
    ``prices`` retrieves only historical data. ``realized_volatility`` derives
    annualized volatility from those prices and does not retrieve option-chain
    implied volatility.
    """

    ticker: MarketTicker

    def prices(
        self,
        *,
        period: str | None = "1y",
        start: str | None = None,
        end: str | None = None,
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        """Return the normalized price data required by this interface.

        Parameters
        ----------
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        start : str | None, default=None
            Optional inclusive history start date.
        end : str | None, default=None
            Optional exclusive or provider-defined history end date.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        provider_price_history = self.ticker.provider.history(
            self.ticker.symbol,
            period=period,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
        )
        normalized_price_history = _normalize_frame(provider_price_history)
        if normalized_price_history.empty:
            raise MarketDataError(f"No historical prices found for {self.ticker.symbol}.")
        normalized_price_history.attrs["provenance"] = DataProvenance(
            provider=getattr(self.ticker.provider, "name", type(self.ticker.provider).__name__),
            dataset="price_history",
            source_labels=tuple(str(column) for column in normalized_price_history.columns),
            reporting_date=(
                normalized_price_history.index[-1].date().isoformat()
                if len(normalized_price_history.index)
                and hasattr(normalized_price_history.index[-1], "date")
                else None
            ),
            transformation_steps=("provider history retrieval", "price-frame normalization"),
            request={
                "symbol": self.ticker.symbol,
                "period": period,
                "start": start,
                "end": end,
                "auto_adjust": auto_adjust,
                "shape": tuple(int(value) for value in normalized_price_history.shape),
            },
        )
        return normalized_price_history

    def realized_volatility(
        self, *, period: str = "1y", window: int = 21, annualize: int = 252
    ) -> float:
        """Estimate trailing historical realized volatility from ticker prices.

        Parameters
        ----------
        period : str, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        window : int, default=21
            Rolling observation window length used for realized volatility.
        annualize : int, default=252
            Annualization factor or flag accepted by the volatility routine.

        Returns
        -------
        float
            Computed realized volatility as a dimensionless decimal quantity.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        price_history = self.prices(period=period)
        closing_price_series = _first_column(price_history, "close", "adj close")
        if closing_price_series is None or closing_price_series.dropna().empty:
            raise MarketDataError(f"No close prices found for {self.ticker.symbol}.")
        rolling_realized_volatility = realized_vol(
            closing_price_series.dropna().to_numpy(dtype=float),
            window=window,
            annualize=annualize,
        )
        finite_volatility_estimates = rolling_realized_volatility[
            np.isfinite(rolling_realized_volatility)
        ]
        if len(finite_volatility_estimates) == 0:
            raise MarketDataError("Not enough price history to compute realized volatility.")
        return float(finite_volatility_estimates[-1])


@dataclass(frozen=True)
class TickerOptionAnalytics:
    """Listed-option retrieval and model-analytics namespace for one ticker.

    Attributes
    ----------
    ticker : MarketTicker
        Applied ticker object that owns this listed-options namespace.

    Notes
    -----
    Construction is lazy where documented: provider data are requested only by retrieval methods, not by object creation.
    """

    ticker: MarketTicker

    def expirations(self) -> list[str]:
        """Return the available listed option expiration dates.

        Returns
        -------
        list[str]
            Available labels in the order supplied by the provider or defined by the implementation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        return self.ticker.provider.option_expirations(self.ticker.symbol)

    def chain(self, expiry: str, option_type: OptionType | None = None) -> pd.DataFrame:
        """Return a normalized listed option chain for one expiration.

        Parameters
        ----------
        expiry : str
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        option_type : OptionType | None, default=None
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        raw_call_contracts, raw_put_contracts = self.ticker.provider.option_chain(
            self.ticker.symbol, expiry
        )
        normalized_option_sides: list[pd.DataFrame] = []
        if option_type in (None, "call"):
            normalized_option_sides.append(_normalize_option_side(raw_call_contracts, "call"))
        if option_type in (None, "put"):
            normalized_option_sides.append(_normalize_option_side(raw_put_contracts, "put"))
        normalized_option_chain = (
            pd.concat(normalized_option_sides, ignore_index=True)
            if normalized_option_sides
            else pd.DataFrame()
        )
        if normalized_option_chain.empty:
            raise MarketDataError(f"No option chain found for {self.ticker.symbol} at {expiry}.")
        normalized_option_chain.attrs["provenance"] = DataProvenance(
            provider=getattr(self.ticker.provider, "name", type(self.ticker.provider).__name__),
            dataset="option_chain",
            source_labels=tuple(
                str(value) for value in normalized_option_chain["option_type"].dropna().unique()
            ),
            reporting_date=expiry,
            transformation_steps=("provider option-chain retrieval", "call/put side normalization"),
            request={
                "symbol": self.ticker.symbol,
                "expiry": expiry,
                "option_type": option_type,
                "shape": tuple(int(value) for value in normalized_option_chain.shape),
            },
        )
        return normalized_option_chain

    def analytics(self, expiry: str) -> OptionChainAnalytics:
        """Return listed-option-chain analytics for one expiration.

        Parameters
        ----------
        expiry : str
            Option expiry date in ISO ``YYYY-MM-DD`` form. The underlying raw
            chain is retrieved once and then reused by the returned analytics
            object.

        Returns
        -------
        OptionChainAnalytics
            Provider-independent analytics object exposing IV smile, IV
            surface, skew, term structure, rich/cheap, open-interest, and
            visualization methods.
        """
        chain = self.chain(expiry)
        return OptionChainAnalytics(
            self.ticker,
            expiry,
            chain,
            provenance=chain.attrs.get("provenance"),
        )

    def bsm(
        self,
        *,
        strike: float,
        risk_free_rate: float,
        maturity: float | None = None,
        expiry: str | None = None,
        volatility: VolatilityInput = None,
        option_type: OptionType = "call",
        dividend_yield: float | None = None,
    ) -> float:
        """Price a European option under Black--Scholes--Merton using applied ticker inputs.

        Parameters
        ----------
        strike : float
            Option strike price in the same currency units as the underlying.
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        maturity : float | None, default=None
            Time to option expiry in years.
        expiry : str | None, default=None
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        volatility : VolatilityInput, default=None
            Volatility input: a positive annualized decimal number, ``"realized"``, or ``"market"`` as documented by the applied interface.
        option_type : OptionType, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        dividend_yield : float | None, default=None
            Continuous dividend yield in decimal annual units.

        Returns
        -------
        float
            Computed bsm as a scalar in the units implied by the input values.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        spot_price = self.ticker.spot()
        option_maturity = self._resolve_maturity(maturity, expiry)
        resolved_volatility = self._resolve_volatility(volatility, strike, expiry, option_type)
        resolved_dividend_yield = (
            self.ticker.dividend_yield() if dividend_yield is None else dividend_yield
        )
        return black_scholes(
            spot_price,
            strike,
            risk_free_rate,
            resolved_volatility,
            option_maturity,
            is_call=option_type == "call",
            q=resolved_dividend_yield,
        )

    def greeks(
        self,
        *,
        strike: float,
        risk_free_rate: float,
        maturity: float | None = None,
        expiry: str | None = None,
        volatility: VolatilityInput = None,
        option_type: OptionType = "call",
        dividend_yield: float | None = None,
    ) -> dict[str, float]:
        """Return the model sensitivities implemented by this model.

        Parameters
        ----------
        strike : float
            Option strike price in the same currency units as the underlying.
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        maturity : float | None, default=None
            Time to option expiry in years.
        expiry : str | None, default=None
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        volatility : VolatilityInput, default=None
            Volatility input: a positive annualized decimal number, ``"realized"``, or ``"market"`` as documented by the applied interface.
        option_type : OptionType, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        dividend_yield : float | None, default=None
            Continuous dividend yield in decimal annual units.

        Returns
        -------
        dict[str, float]
            Named outputs of the greeks calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        spot_price = self.ticker.spot()
        option_maturity = self._resolve_maturity(maturity, expiry)
        resolved_volatility = self._resolve_volatility(volatility, strike, expiry, option_type)
        resolved_dividend_yield = (
            self.ticker.dividend_yield() if dividend_yield is None else dividend_yield
        )
        return calculate_greeks(
            spot_price,
            strike,
            risk_free_rate,
            resolved_volatility,
            option_maturity,
            is_call=option_type == "call",
            q=resolved_dividend_yield,
        )

    def listed_implied_volatility(
        self,
        *,
        strike: float,
        expiry: str,
        option_type: OptionType = "call",
    ) -> float:
        """Retrieve the listed implied volatility of the nearest available contract.

        Parameters
        ----------
        strike : float
            Option strike price in the same currency units as the underlying.
        expiry : str
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        option_type : OptionType, default='call'
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        float
            Computed listed implied volatility as a dimensionless decimal quantity.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        normalized_option_chain = self.chain(expiry, option_type=option_type)
        if "strike" not in normalized_option_chain.columns:
            raise MarketDataError("Option chain has no strike column.")
        if "implied_volatility" not in normalized_option_chain.columns:
            raise MarketDataError("Option chain has no implied volatility column.")
        nearest_contract_index = (normalized_option_chain["strike"] - strike).abs().idxmin()
        listed_volatility = normalized_option_chain.loc[
            nearest_contract_index, "implied_volatility"
        ]
        if not _is_valid_number(listed_volatility) or float(listed_volatility) <= 0:
            raise MarketDataError("No usable listed implied volatility found.")
        return float(listed_volatility)

    def solve_implied_volatility(
        self,
        *,
        market_price: float,
        strike: float,
        maturity: float | None = None,
        expiry: str | None = None,
        risk_free_rate: float = 0.0,
        option_type: OptionType = "call",
        dividend_yield: float | None = None,
    ) -> float:
        """Solve the inverse Black--Scholes--Merton problem for implied volatility.

        Parameters
        ----------
        market_price : float
            Observed option premium in the same currency units as spot and strike.
        strike : float
            Option strike price in the same currency units as the underlying.
        maturity : float | None, default=None
            Time to option expiry in years.
        expiry : str | None, default=None
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        risk_free_rate : float, default=0.0
            Annual risk-free rate in decimal units.
        option_type : OptionType, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        dividend_yield : float | None, default=None
            Continuous dividend yield in decimal annual units.

        Returns
        -------
        float
            Computed solve implied volatility as a dimensionless decimal quantity.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        spot_price = self.ticker.spot()
        option_maturity = self._resolve_maturity(maturity, expiry)
        resolved_dividend_yield = (
            self.ticker.dividend_yield() if dividend_yield is None else dividend_yield
        )
        return implied_volatility_bsm(
            market_price,
            spot_price,
            strike,
            risk_free_rate,
            option_maturity,
            is_call=option_type == "call",
            q=resolved_dividend_yield,
        )

    def compare_models(
        self,
        *,
        strike: float,
        risk_free_rate: float,
        maturity: float | None = None,
        expiry: str | None = None,
        volatility: VolatilityInput = None,
        dividend_yield: float | None = None,
    ) -> dict[str, dict[str, float]]:
        """Compare the option prices generated by the available pricing models.

        Parameters
        ----------
        strike : float
            Option strike price in the same currency units as the underlying.
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        maturity : float | None, default=None
            Time to option expiry in years.
        expiry : str | None, default=None
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        volatility : VolatilityInput, default=None
            Volatility input: a positive annualized decimal number, ``"realized"``, or ``"market"`` as documented by the applied interface.
        dividend_yield : float | None, default=None
            Continuous dividend yield in decimal annual units.

        Returns
        -------
        dict[str, dict[str, float]]
            Named outputs of the compare models calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        spot_price = self.ticker.spot()
        option_maturity = self._resolve_maturity(maturity, expiry)
        resolved_volatility = self._resolve_volatility(volatility, strike, expiry, "call")
        resolved_dividend_yield = (
            self.ticker.dividend_yield() if dividend_yield is None else dividend_yield
        )
        return compare_all_models(
            spot_price,
            strike,
            option_maturity,
            risk_free_rate,
            resolved_volatility,
            q=resolved_dividend_yield,
        )

    def _resolve_volatility(
        self,
        volatility: VolatilityInput,
        strike: float,
        expiry: str | None,
        option_type: OptionType,
    ) -> float:
        """Resolve and validate an internal derived input for the surrounding workflow.

        Parameters
        ----------
        volatility : VolatilityInput
            Volatility input: a positive annualized decimal number, ``"realized"``, or ``"market"`` as documented by the applied interface.
        strike : float
            Option strike price in the same currency units as the underlying.
        expiry : str | None
            Option expiry date in ISO ``YYYY-MM-DD`` form.
        option_type : OptionType
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        float
            Computed  resolve volatility as a dimensionless decimal quantity.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        if volatility is None:
            raise ValueError(
                "volatility must be supplied explicitly, or set to 'realized' or 'market'. "
                "No default volatility is assumed."
            )
        if isinstance(volatility, str):
            if volatility == "realized":
                return self.ticker.history.realized_volatility()
            if volatility == "market":
                if expiry is None:
                    raise ValueError("expiry is required when volatility='market'.")
                return self.listed_implied_volatility(
                    strike=strike, expiry=expiry, option_type=option_type
                )
            raise ValueError("volatility must be a float, 'realized', 'market', or None.")
        numeric_volatility = float(volatility)
        if numeric_volatility <= 0:
            raise ValueError("volatility must be positive.")
        return numeric_volatility

    @staticmethod
    def _resolve_maturity(maturity: float | None, expiry: str | None) -> float:
        """Resolve and validate an internal derived input for the surrounding workflow.

        Parameters
        ----------
        maturity : float | None
            Time to option expiry in years.
        expiry : str | None
            Option expiry date in ISO ``YYYY-MM-DD`` form.

        Returns
        -------
        float
            Computed  resolve maturity as a scalar in the units implied by the input values.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        if maturity is not None:
            option_maturity = float(maturity)
        elif expiry is not None:
            option_maturity = _year_fraction_to_expiry(expiry)
        else:
            raise ValueError("maturity must be supplied, or expiry must be supplied.")
        if option_maturity <= 0:
            raise ValueError("maturity must be positive.")
        return option_maturity


@dataclass(frozen=True)
class TickerFundamentalData:
    """Lazy fundamental-statement retrieval namespace for one ticker.

    Attributes
    ----------
    ticker : MarketTicker
        Applied ticker object that owns this fundamentals namespace.

    Notes
    -----
    Construction is lazy where documented: provider data are requested only by retrieval methods, not by object creation.
    """

    ticker: MarketTicker

    def info(self) -> dict:
        """Return provider metadata normalized to a plain Python dictionary.

        Returns
        -------
        dict
            Named outputs of the info calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        return self.ticker.provider.info(self.ticker.symbol)


@dataclass(frozen=True)
class TickerCreditMetrics:
    """Manual fundamental credit-proxy namespace for one ticker.

    This namespace deliberately does not request fundamental statements from a
    provider in Phase 3. Callers create :class:`CreditAnalysisInputs` from
    reconciled manual inputs and then evaluate it against the ticker. This
    keeps accounting definitions, reporting dates, and currency choices
    explicit.

    Attributes
    ----------
    ticker : MarketTicker
        Applied ticker object used only to associate a manual assessment with a
        normalized symbol. No provider call is made by this namespace.

    Notes
    -----
    The reported synthetic score is a heuristic credit proxy, not a rating,
    default probability, CDS spread, or investment recommendation.
    """

    ticker: MarketTicker

    def assess(self, inputs: CreditAnalysisInputs) -> CreditProxyAssessment:
        """Evaluate manually supplied fundamentals for the ticker.

        Parameters
        ----------
        inputs : CreditAnalysisInputs
            Manual, internally consistent statement and market-value inputs.
            The object should use one currency, one consolidation perimeter, and
            comparable reporting periods.

        Returns
        -------
        CreditProxyAssessment
            Full transparent assessment containing ratios, Altman Z-score,
            Piotroski signals, earnings and leverage diagnostics, a normalized
            synthetic proxy score, and mandatory limitations.

        Notes
        -----
        This method does not call the configured market-data provider.
        """
        if not isinstance(inputs, CreditAnalysisInputs):
            raise TypeError("inputs must be a CreditAnalysisInputs instance.")
        return calculate_credit_proxy_metrics(inputs)

    def assess_from_financials(
        self, *, period: str = "annual", **kwargs: object
    ) -> CreditProxyAssessment:
        """Build provider-fed credit inputs from cached statements and assess them.

        Parameters
        ----------
        period : {"annual", "quarterly"}, default="annual"
            Statement frequency used to construct the input bundle.
        **kwargs : object
            Cache controls accepted by ``ticker.financials.credit_inputs``.

        Returns
        -------
        CreditProxyAssessment
            Transparent fundamental credit-proxy assessment.

        Notes
        -----
        This method may retrieve one three-statement snapshot when no allowed
        cache is available. It reuses the existing pure credit-risk model.
        """
        return self.assess(self.ticker.financials.credit_inputs(period=period, **kwargs))

    def proxy_metrics(self, inputs: CreditAnalysisInputs) -> dict[str, object]:
        """Return flat manual credit-proxy metrics for convenient inspection.

        Parameters
        ----------
        inputs : CreditAnalysisInputs
            Manual fundamental inputs used by :meth:`assess`.

        Returns
        -------
        dict[str, object]
            Flat mapping with debt-to-equity, liquidity, coverage, cash-flow,
            Altman, Piotroski, earnings, leverage, and synthetic proxy fields.
            Missing required inputs are represented by ``None``; they are never
            inferred from market data.
        """
        return self.assess(inputs).as_dict()

    def synthetic_score(self, inputs: CreditAnalysisInputs) -> float | None:
        """Return the 0--100 heuristic synthetic credit-proxy score.

        Parameters
        ----------
        inputs : CreditAnalysisInputs
            Manual fundamental inputs used by :meth:`assess`.

        Returns
        -------
        float or None
            Coverage-normalized proxy score, or ``None`` when no score component
            can be computed. The value is not an agency rating or default
            probability.
        """
        return self.assess(inputs).synthetic_credit_proxy_score

    def altman_z_score(self, inputs: CreditAnalysisInputs) -> float | None:
        """Return the traditional public-company Altman Z-score when available.

        Parameters
        ----------
        inputs : CreditAnalysisInputs
            Manual inputs including current assets, current liabilities, total
            assets, retained earnings, EBIT, market equity value, total
            liabilities, and revenue.

        Returns
        -------
        float or None
            Traditional five-factor Altman Z-score, or ``None`` if one or more
            required values are unavailable. This formulation is not a generic
            model for financial companies or every private issuer.
        """
        return self.assess(inputs).metrics["altman_z_score"]  # type: ignore[return-value]

    def piotroski_f_score(self, inputs: CreditAnalysisInputs) -> int | None:
        """Return the complete nine-signal Piotroski F-score when available.

        Parameters
        ----------
        inputs : CreditAnalysisInputs
            Manual current and prior-period accounting inputs. All nine signal
            inputs are required; partial F-scores are not reported.

        Returns
        -------
        int or None
            Integer from 0 through 9, or ``None`` when any required current or
            prior-period signal input is unavailable.
        """
        return self.assess(inputs).metrics["piotroski_f_score"]  # type: ignore[return-value]


def _normalize_symbol(symbol: str) -> str:
    """Normalize an internal representation used by the surrounding workflow.

    Parameters
    ----------
    symbol : str
        Ticker symbol to normalize and query.

    Returns
    -------
    str
        Result of the  normalize symbol calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    normalized_symbol = str(symbol).strip().upper()
    if not normalized_symbol:
        raise ValueError("Ticker symbol cannot be empty.")
    return normalized_symbol


def _normalize_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize an internal representation used by the surrounding workflow.

    Parameters
    ----------
    data : pd.DataFrame
        Input table or mapping to normalize.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    frame = data.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(col[0]).strip().lower() for col in frame.columns]
    else:
        frame.columns = [str(col).strip().lower() for col in frame.columns]
    return frame.sort_index()


def _normalize_option_side(data: pd.DataFrame, option_type: OptionType) -> pd.DataFrame:
    """Normalize an internal representation used by the surrounding workflow.

    Parameters
    ----------
    data : pd.DataFrame
        Input table or mapping to normalize.
    option_type : OptionType
        Option type label, normally ``"call"`` or ``"put"``.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    frame = _normalize_frame(data).reset_index(drop=True)
    if frame.empty:
        return frame
    frame["option_type"] = option_type
    if "strike" in frame.columns:
        frame["strike"] = pd.to_numeric(frame["strike"], errors="coerce")
        frame = frame[frame["strike"] > 0].copy()
    for col in (
        "bid",
        "ask",
        "lastprice",
        "last_price",
        "impliedvolatility",
        "openinterest",
        "volume",
    ):
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if "bid" in frame.columns and "ask" in frame.columns:
        frame["mid_price"] = ((frame["bid"].fillna(0.0) + frame["ask"].fillna(0.0)) / 2).where(
            (frame["bid"] > 0) & (frame["ask"] > 0)
        )
    if "impliedvolatility" in frame.columns:
        frame["implied_volatility"] = frame["impliedvolatility"].where(
            frame["impliedvolatility"].between(0.01, 2.50)
        )
    if "openinterest" in frame.columns:
        frame["open_interest"] = frame["openinterest"].where(frame["openinterest"] >= 0.0)
    return frame.reset_index(drop=True)


def _first_column(frame: pd.DataFrame, *names: str) -> pd.Series | None:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    frame : pd.DataFrame
        Pandas DataFrame used by an internal normalization helper.
    names : str
        Candidate column names searched by the internal DataFrame helper.

    Returns
    -------
    pd.Series | None
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    columns = {str(col).lower(): col for col in frame.columns}
    for name in names:
        if name.lower() in columns:
            return frame[columns[name.lower()]]
    return None


def _is_valid_number(value: object) -> bool:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    value : object
        Numerical value being validated or transformed.

    Returns
    -------
    bool
        Whether the input satisfies the documented condition.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return np.isfinite(numeric)


def _year_fraction_to_expiry(expiry: str) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    expiry : str
        Option expiry date in ISO ``YYYY-MM-DD`` form.

    Returns
    -------
    float
        Computed  year fraction to expiry as a scalar in the units implied by the input values.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
    return max((expiry_date - date.today()).days / 365.0, 1.0 / 365.0)
