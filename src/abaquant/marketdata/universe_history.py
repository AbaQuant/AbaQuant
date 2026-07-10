"""Normalized historical price and return panels for ticker universes.

Purpose
-------
The module obtains batched provider histories, extracts close-like fields, aligns trading dates, and converts price panels to simple or log returns.

Conventions
-----------
Inner alignment keeps only dates with complete data for every asset; outer alignment preserves missing values. No forward filling or interpolation is performed.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

import pandas as pd

from abaquant.financial_math import (
    log_returns_from_prices,
    simple_returns_from_prices,
)

from .errors import MarketDataProviderError, UniverseValidationError

if TYPE_CHECKING:
    from .universe import MarketUniverse

Alignment = Literal["inner", "outer"]
ReturnKind = Literal["simple", "log"]


@dataclass(frozen=True)
class UniverseHistory:
    """Lazy historical-price and return retrieval namespace for a universe.

    Attributes
    ----------
    universe : MarketUniverse
        Universe that supplies symbol ordering, provider access, and the
        in-memory normalized-price cache.

    Notes
    -----
    Retrieval requests are lazy. Construction does not invoke the configured
    provider; ``prices`` and ``returns`` do so only when their cache key is
    absent.
    """

    universe: MarketUniverse

    def prices(
        self,
        *,
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        alignment: Alignment = "inner",
    ) -> pd.DataFrame:
        """Return the normalized price data required by this interface.

        Parameters
        ----------
        start : str | date | None, default=None
            Optional inclusive history start date.
        end : str | date | None, default=None
            Optional exclusive or provider-defined history end date.
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        interval : str, default='1d'
            Provider sampling interval label, such as ``"1d"``.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.
        alignment : Alignment, default='inner'
            Date-alignment rule: ``"inner"`` keeps complete common dates and ``"outer"`` preserves the date union.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        _validate_history_request(start=start, end=end, period=period, alignment=alignment)
        cache_key = (
            tuple(self.universe.symbols),
            _date_key(start),
            _date_key(end),
            period,
            interval,
            auto_adjust,
            alignment,
        )
        cached_price_panel = self.universe._price_cache.get(cache_key)
        if cached_price_panel is not None:
            return cached_price_panel.copy()

        provider_history_panel = self.universe.provider.history_many(
            self.universe.symbols,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
        )
        normalized_price_panel = normalize_price_panel(
            provider_history_panel,
            self.universe.symbols,
            alignment=alignment,
        )
        self.universe._price_cache[cache_key] = normalized_price_panel.copy()
        return normalized_price_panel

    def returns(
        self,
        *,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        alignment: Alignment = "inner",
    ) -> pd.DataFrame:
        """Compute periodic returns from the normalized price panel.

        Parameters
        ----------
        kind : ReturnKind, default='simple'
            Return convention: ``"simple"`` for arithmetic returns or ``"log"`` for logarithmic returns.
        start : str | date | None, default=None
            Optional inclusive history start date.
        end : str | date | None, default=None
            Optional exclusive or provider-defined history end date.
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        interval : str, default='1d'
            Provider sampling interval label, such as ``"1d"``.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.
        alignment : Alignment, default='inner'
            Date-alignment rule: ``"inner"`` keeps complete common dates and ``"outer"`` preserves the date union.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        aligned_price_panel = self.prices(
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            alignment=alignment,
        )
        if kind == "simple":
            return simple_returns_from_prices(aligned_price_panel)
        if kind == "log":
            return log_returns_from_prices(aligned_price_panel)
        raise UniverseValidationError("kind must be 'simple' or 'log'.")


def normalize_price_panel(
    provider_price_panel: pd.DataFrame,
    symbols: tuple[str, ...],
    *,
    alignment: Alignment = "inner",
) -> pd.DataFrame:
    """Compute the result defined by ``normalize_price_panel`` under this module's documented convention.

    Parameters
    ----------
    provider_price_panel : pandas.DataFrame
        Raw batched provider output before field extraction and date alignment.
    symbols : tuple[str, ...]
        Ticker symbols to normalize and include in the applied universe.
    alignment : Alignment, default='inner'
        Date-alignment rule: ``"inner"`` keeps complete common dates and ``"outer"`` preserves the date union.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    if alignment not in {"inner", "outer"}:
        raise UniverseValidationError("alignment must be 'inner' or 'outer'.")
    if provider_price_panel.empty:
        raise MarketDataProviderError("Provider returned an empty price panel.")

    normalized_provider_frame = provider_price_panel.copy()
    normalized_provider_frame.index = _normalize_index(normalized_provider_frame.index)
    normalized_provider_frame = normalized_provider_frame.sort_index()
    normalized_provider_frame = normalized_provider_frame.groupby(level=0).last()

    price_series_by_symbol: dict[str, pd.Series] = {}
    symbols_without_usable_prices: list[str] = []
    for symbol in symbols:
        extracted_close_prices = _extract_symbol_close(
            normalized_provider_frame,
            symbol,
            single_symbol=len(symbols) == 1,
        )
        if extracted_close_prices is None:
            symbols_without_usable_prices.append(symbol)
            continue
        numeric_close_prices = pd.to_numeric(extracted_close_prices, errors="coerce").astype(float)
        if numeric_close_prices.dropna().empty:
            symbols_without_usable_prices.append(symbol)
            continue
        price_series_by_symbol[symbol] = numeric_close_prices

    if symbols_without_usable_prices:
        raise MarketDataProviderError(
            f"No usable price data for: {', '.join(symbols_without_usable_prices)}."
        )

    normalized_price_panel = pd.DataFrame(
        price_series_by_symbol,
        index=normalized_provider_frame.index,
    )
    normalized_price_panel = normalized_price_panel.loc[:, list(symbols)]
    if alignment == "inner":
        normalized_price_panel = normalized_price_panel.dropna(how="any")
        if normalized_price_panel.empty:
            raise MarketDataProviderError(
                "No usable common trading dates remain after inner alignment."
            )
    return normalized_price_panel


def _extract_symbol_close(
    frame: pd.DataFrame, symbol: str, *, single_symbol: bool
) -> pd.Series | None:
    """Extract one symbol's close-like price series from provider output.

    Parameters
    ----------
    frame : pd.DataFrame
        Pandas DataFrame used by an internal normalization helper.
    symbol : str
        Ticker symbol to normalize and query.
    single_symbol : bool
        Whether raw provider history represents one symbol rather than a multi-symbol panel.

    Returns
    -------
    pd.Series | None
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    if isinstance(frame.columns, pd.MultiIndex):
        direct = _extract_from_multiindex(frame, symbol, symbol_level=0, field_level=1)
        if direct is not None:
            return direct
        return _extract_from_multiindex(frame, symbol, symbol_level=1, field_level=0)

    lower_map = {str(column).strip().lower(): column for column in frame.columns}
    if symbol.lower() in lower_map:
        return frame[lower_map[symbol.lower()]]
    for field in ("close", "adj close", "adj_close", "lastprice", "last_price"):
        column = lower_map.get(field)
        if column is not None and single_symbol:
            return frame[column]
        prefixed = lower_map.get(f"{symbol.lower()}_{field}") or lower_map.get(
            f"{field}_{symbol.lower()}"
        )
        if prefixed is not None:
            return frame[prefixed]
    if len(frame.columns) == 1 and single_symbol:
        return frame.iloc[:, 0]
    return None


def _extract_from_multiindex(
    frame: pd.DataFrame,
    symbol: str,
    *,
    symbol_level: int,
    field_level: int,
) -> pd.Series | None:
    """Extract one symbol's close-like price series from provider output.

    Parameters
    ----------
    frame : pd.DataFrame
        Pandas DataFrame used by an internal normalization helper.
    symbol : str
        Ticker symbol to normalize and query.
    symbol_level : int
        MultiIndex level that identifies provider ticker symbols.
    field_level : int
        MultiIndex level that identifies provider price fields.

    Returns
    -------
    pd.Series | None
        One-dimensional labeled result aligned to the documented input order.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    wanted_fields = {"close", "adj close", "adj_close"}
    candidates: list[tuple[object, ...]] = []
    for column in frame.columns:
        if len(column) <= max(symbol_level, field_level):
            continue
        column_symbol = str(column[symbol_level]).strip().lower()
        field = str(column[field_level]).strip().lower()
        if column_symbol == symbol.lower() and field in wanted_fields:
            candidates.append(column)
    for field_name in ("close", "adj close", "adj_close"):
        for candidate in candidates:
            if str(candidate[field_level]).strip().lower() == field_name:
                return frame[candidate]
    return None


def _normalize_index(index: pd.Index) -> pd.DatetimeIndex:
    """Normalize provider timestamps to a timezone-naive ``DatetimeIndex``.

    Parameters
    ----------
    index : pd.Index
        Datetime-like index to normalize in the internal data helper.

    Returns
    -------
    pd.DatetimeIndex
        Result of the  normalize index calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    normalized = pd.DatetimeIndex(pd.to_datetime(index))
    if normalized.tz is not None:
        normalized = normalized.tz_convert(None)
    return normalized


def _validate_history_request(
    *,
    start: str | date | None,
    end: str | date | None,
    period: str | None,
    alignment: Alignment,
) -> None:
    """Validate mutually exclusive date-selection and alignment arguments.

    Parameters
    ----------
    start : str | date | None
        Optional inclusive history start date.
    end : str | date | None
        Optional exclusive or provider-defined history end date.
    period : str | None
        Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
    alignment : Alignment
        Date-alignment rule: ``"inner"`` keeps complete common dates and ``"outer"`` preserves the date union.

    Returns
    -------
    None
        Result of the  validate history request calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    if alignment not in {"inner", "outer"}:
        raise UniverseValidationError("alignment must be 'inner' or 'outer'.")
    if period is not None and (start is not None or end is not None):
        raise UniverseValidationError("Use either period or start/end, not both.")


def _date_key(value: str | date | None) -> str | None:
    """Convert a date-like cache-key input to a stable string representation.

    Parameters
    ----------
    value : str | date | None
        Numerical value being validated or transformed.

    Returns
    -------
    str | None
        Result of the  date key calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    return value.isoformat() if isinstance(value, date) else value


# Backward-compatible alias for the original Phase-2 namespace class name.
MarketUniverseHistory = UniverseHistory
