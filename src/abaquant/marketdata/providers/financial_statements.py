"""Financial-statement provider protocol."""

from __future__ import annotations

from typing import Any, Literal, Protocol

import pandas as pd

FinancialPeriod = Literal["annual", "quarterly"]


class FinancialStatementProvider(Protocol):
    """Provider capability for annual or quarterly financial statements."""

    def sec_facts(
        self, symbol: str, *, refresh_policy: str = "if_stale", max_age_days: float | None = None
    ) -> dict[str, Any]:
        """Return raw SEC Company Facts JSON when the provider supports it.

        Providers without SEC support may omit this method at runtime; the
        financial-statement facade checks for the method before calling it.
        """
        ...

    def income_statement(self, symbol: str, *, period: FinancialPeriod = "annual") -> pd.DataFrame:
        """Return the requested income statement table."""
        ...

    def balance_sheet(self, symbol: str, *, period: FinancialPeriod = "annual") -> pd.DataFrame:
        """Return the requested balance-sheet table."""
        ...

    def cash_flow_statement(
        self, symbol: str, *, period: FinancialPeriod = "annual"
    ) -> pd.DataFrame:
        """Return the requested cash-flow statement table."""
        ...
