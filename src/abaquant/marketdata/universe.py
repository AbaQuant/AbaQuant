"""Lazy multi-ticker market-data universe.

Purpose
-------
The module creates MarketUniverse instances that coordinate shared price histories, return statistics, and static portfolio workflows for normalized ticker collections.

Conventions
-----------
Symbols are uppercase and de-duplicated in first-seen order. Construction does not make provider calls.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

from collections.abc import Sequence

from .errors import UniverseValidationError
from .providers import MarketDataProvider, YahooFinanceProvider
from .sessions import UniverseSession
from .universe_history import UniverseHistory
from .universe_portfolio import UniversePortfolioAnalytics
from .universe_statistics import UniverseStatistics


def get_tickers(
    symbols: Sequence[str],
    provider: str | MarketDataProvider = "yahoo",
) -> MarketUniverse:
    """Create a lazy applied universe for normalized ticker symbols.

    Parameters
    ----------
    symbols : Sequence[str]
        Ticker symbols to normalize and include in the applied universe.
    provider : str | MarketDataProvider, default='yahoo'
        Provider name or object satisfying the market-data provider protocol.

    Returns
    -------
    MarketUniverse
        Lazy multi-ticker universe. Constructing it does not fetch remote data.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    normalized_symbols = normalize_symbols(symbols)
    resolved_provider = resolve_provider(provider)
    return MarketUniverse(normalized_symbols, resolved_provider)


class MarketUniverse:
    """Lazy multi-ticker facade with immutable symbols and a separate session."""

    def __init__(
        self,
        symbols: tuple[str, ...],
        provider: MarketDataProvider,
        session: UniverseSession | None = None,
    ) -> None:
        """Create a universe facade without loading any price history."""
        self.symbols = symbols
        self.provider = provider
        self.session = session or UniverseSession()
        self._price_cache = self.session.price_panels
        self.history = UniverseHistory(self)
        self.statistics = UniverseStatistics(self)
        self.portfolio = UniversePortfolioAnalytics(self)

    def visualize(
        self,
        *,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        alignment: str = "inner",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
    ):
        """Return a normalized multi-ticker price-history figure.

        The underlying price panel is retrieved lazily and rendered without an
        implicit interactive display call.
        """
        from abaquant.visualization import visualize_price_history

        prices = self.history.prices(
            period=period, interval=interval, auto_adjust=auto_adjust, alignment=alignment
        )
        return visualize_price_history(
            prices, backend=backend, theme=theme, save_path=save_path, filename=filename
        )


def normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    """Normalize, validate, and de-duplicate ticker symbols.

    Parameters
    ----------
    symbols : Sequence[str]
        Ticker symbols to normalize and include in the applied universe.

    Returns
    -------
    tuple[str, ...]
        Positional outputs produced by the normalize symbols calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    if isinstance(symbols, str) or not isinstance(symbols, Sequence):
        raise UniverseValidationError("symbols must be a non-empty sequence of strings.")
    if len(symbols) == 0:
        raise UniverseValidationError("symbols must contain at least one ticker.")

    normalized_symbols: list[str] = []
    seen_symbols: set[str] = set()
    for symbol in symbols:
        if not isinstance(symbol, str):
            raise UniverseValidationError("Each ticker symbol must be a string.")
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise UniverseValidationError("Ticker symbols cannot be blank.")
        if normalized_symbol not in seen_symbols:
            normalized_symbols.append(normalized_symbol)
            seen_symbols.add(normalized_symbol)

    if not normalized_symbols:
        raise UniverseValidationError("symbols must contain at least one ticker.")
    return tuple(normalized_symbols)


def resolve_provider(provider: str | MarketDataProvider) -> MarketDataProvider:
    """Resolve a provider name or provider instance to the market-data protocol.

    Parameters
    ----------
    provider : str | MarketDataProvider
        Provider name or object satisfying the market-data provider protocol.

    Returns
    -------
    MarketDataProvider
        Result of the resolve provider calculation.

    Notes
    -----
    The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
    """
    if isinstance(provider, str):
        if provider.lower() != "yahoo":
            raise UniverseValidationError("Only provider='yahoo' is supported.")
        return YahooFinanceProvider()
    if not hasattr(provider, "history_many"):
        raise UniverseValidationError("provider must implement history_many().")
    return provider
