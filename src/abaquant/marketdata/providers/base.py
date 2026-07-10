"""Composite optional provider protocol assembled from focused capabilities."""

from __future__ import annotations

from typing import Protocol

from .financial_statements import FinancialStatementProvider
from .history import PriceHistoryProvider
from .options import OptionChainProvider
from .quotes import QuoteProvider


class MarketDataProvider(
    QuoteProvider, PriceHistoryProvider, OptionChainProvider, FinancialStatementProvider, Protocol
):
    """Full provider used by the default ticker and universe factories."""
