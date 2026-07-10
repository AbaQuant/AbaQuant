"""Listed-option-chain provider protocol."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class OptionChainProvider(Protocol):
    """Provider capability for expirations and raw call/put option tables."""

    def option_expirations(self, symbol: str) -> list[str]:
        """Return listed expiration dates for one normalized symbol."""
        ...

    def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return raw call and put tables for one expiration date."""
        ...
