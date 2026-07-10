"""Pure data transformations for portfolio analysis.

Purpose
-------
The module normalizes ticker labels and converts already-loaded price panels into simple return matrices without downloading market data.

Conventions
-----------
Prices are arranged with dates on the index and assets on columns. Missing observations are preserved until the return-cleaning step described by each function.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def get_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute the result defined by ``get_returns`` under this module's documented convention.

    Parameters
    ----------
    prices : pd.DataFrame
        Price observations with dates on the index and assets on columns where applicable.

    Returns
    -------
    pd.DataFrame
        Tabular result with schema defined by the module-level convention.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if prices.empty:
        return prices.copy()
    returns = prices.pct_change().dropna(how="all")
    return returns.dropna()


def validate_tickers(tickers: Iterable[str]) -> list[str]:
    """Compute the result defined by ``validate_tickers`` under this module's documented convention.

    Parameters
    ----------
    tickers : Iterable[str]
        Ticker labels or an iterable of raw ticker strings.

    Returns
    -------
    list[str]
        Ordered collection produced by the validate tickers calculation.
    """
    cleaned: list[str] = []
    for ticker in tickers:
        normalized = ticker.strip().upper()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
    return cleaned


__all__ = ["get_returns", "validate_tickers"]
