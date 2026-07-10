"""Yahoo Finance adapter backed by the optional yfinance dependency.

Purpose
-------
The module translates yfinance quote, history, and option-chain responses into package-level primitives and DataFrames.

Conventions
-----------
The yfinance import is lazy. Dates and data fields retain provider semantics until normalized by the ticker or universe layer.

Scope and limitations
---------------------
Yahoo Finance and yfinance are external, unofficial, and potentially rate-limited data sources. Their data should not be treated as production-grade or authoritative.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

import pandas as pd

from ..errors import OptionalDependencyError


class YahooFinanceProvider:
    """Yahoo Finance provider adapter backed by optional yfinance.

    Notes
    -----
    Construction is lazy where documented: provider data are requested only by retrieval methods, not by object creation.
    """

    name = "yahoo"

    def __init__(self) -> None:
        """Create a provider adapter without importing yfinance or fetching data."""
        self._yf = None

    def _require_yfinance(self) -> Any:
        """Import and memoize the optional yfinance package on first use."""
        if self._yf is None:
            try:
                import yfinance as yf
            except ImportError as exc:
                raise OptionalDependencyError(
                    "Yahoo market data requires the optional dependency 'yfinance'. "
                    "Install it with: pip install abaquant[market]"
                ) from exc
            self._yf = yf
        return self._yf

    def _ticker(self, symbol: str) -> Any:
        """Perform an internal calculation used by the documented public workflow.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.

        Returns
        -------
        Any
            Result of the  ticker calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        return self._require_yfinance().Ticker(symbol)

    def fast_info(self, symbol: str) -> dict[str, Any]:
        """Retrieve a lightweight quote metadata mapping from the provider.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.

        Returns
        -------
        dict[str, Any]
            Named outputs of the fast info calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        data = self._ticker(symbol).fast_info
        try:
            return dict(data)
        except TypeError:
            return {key: data[key] for key in data}

    def info(self, symbol: str) -> dict[str, Any]:
        """Return provider metadata normalized to a plain Python dictionary.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.

        Returns
        -------
        dict[str, Any]
            Named outputs of the info calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        return dict(self._ticker(symbol).info)

    def history(
        self,
        symbol: str,
        *,
        period: str | None = "1y",
        start: str | None = None,
        end: str | None = None,
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        """Retrieve historical market data through the configured provider.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.
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
        kwargs: dict[str, Any] = {"auto_adjust": auto_adjust}
        if start is not None or end is not None:
            kwargs["start"] = start
            kwargs["end"] = end
        else:
            kwargs["period"] = period
        return self._ticker(symbol).history(**kwargs)

    def history_many(
        self,
        symbols: Sequence[str],
        *,
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        """Retrieve batched historical market data through the configured provider.

        Parameters
        ----------
        symbols : Sequence[str]
            Ticker symbols to normalize and include in the applied universe.
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

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        kwargs: dict[str, Any] = {
            "auto_adjust": auto_adjust,
            "group_by": "ticker",
            "interval": interval,
            "progress": False,
            "threads": True,
        }
        if start is not None or end is not None:
            kwargs["start"] = start
            kwargs["end"] = end
        else:
            kwargs["period"] = period
        return self._require_yfinance().download(list(symbols), **kwargs)

    def option_expirations(self, symbol: str) -> list[str]:
        """Retrieve listed option expiration dates from the provider.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.

        Returns
        -------
        list[str]
            Available labels in the order supplied by the provider or defined by the implementation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        return list(self._ticker(symbol).options)

    def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Retrieve raw call and put option-chain tables from the provider.

        Parameters
        ----------
        symbol : str
            Ticker symbol to normalize and query.
        expiry : str
            Option expiry date in ISO ``YYYY-MM-DD`` form.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            Positional outputs produced by the option chain calculation.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        chain = self._ticker(symbol).option_chain(expiry)
        return chain.calls, chain.puts

    def income_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Retrieve a structured annual or quarterly income statement from yfinance."""
        frequency = "yearly" if period == "annual" else "quarterly"
        return self._ticker(symbol).get_income_stmt(freq=frequency)

    def balance_sheet(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Retrieve a structured annual or quarterly balance sheet from yfinance."""
        frequency = "yearly" if period == "annual" else "quarterly"
        return self._ticker(symbol).get_balance_sheet(freq=frequency)

    def cash_flow_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Retrieve a structured annual or quarterly cash-flow statement from yfinance."""
        frequency = "yearly" if period == "annual" else "quarterly"
        return self._ticker(symbol).get_cashflow(freq=frequency)
