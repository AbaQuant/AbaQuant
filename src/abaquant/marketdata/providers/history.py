"""Historical-price provider protocol."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

import pandas as pd


class PriceHistoryProvider(Protocol):
    """Provider capability for single-asset and batched price history."""

    def history(
        self,
        symbol: str,
        *,
        period: str | None = "1y",
        start: str | None = None,
        end: str | None = None,
        auto_adjust: bool = True,
    ) -> pd.DataFrame:
        """Return one symbol's historical market data."""
        ...

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
        """Return a batched historical price panel."""
        ...
