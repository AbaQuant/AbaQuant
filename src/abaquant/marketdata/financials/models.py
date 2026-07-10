"""Immutable financial-statement snapshot and line-item models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Literal

import pandas as pd

from abaquant.core import DataProvenance

FinancialPeriod = Literal["annual", "quarterly"]
RefreshPolicy = Literal["cache_only", "if_missing", "if_stale", "refresh"]
CacheMode = Literal["none", "memory", "disk"]


@dataclass(frozen=True)
class FinancialLineItem:
    """Resolved canonical line item with provider provenance."""

    canonical_name: str
    value: float | None
    statement_type: str
    reporting_date: str | None
    source_label: str | None


@dataclass(frozen=True)
class FinancialStatementSnapshot:
    """Immutable metadata wrapper around three normalized statement tables.

    Table accessors return defensive deep copies; canonical line items are a
    read-only mapping. This prevents a caller from mutating cached state.
    """

    symbol: str
    provider_name: str
    period: FinancialPeriod
    retrieved_at_utc: datetime
    _income_statement: pd.DataFrame
    _balance_sheet: pd.DataFrame
    _cash_flow_statement: pd.DataFrame
    _canonical_line_items: Mapping[str, FinancialLineItem]
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach default statement provenance when none was supplied."""
        if self.provenance is None:
            labels = tuple(
                item.source_label
                for item in self._canonical_line_items.values()
                if item.source_label
            )
            reporting_dates = [
                item.reporting_date
                for item in self._canonical_line_items.values()
                if item.reporting_date
            ]
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider=self.provider_name,
                    dataset="financial_statement_snapshot",
                    retrieved_at_utc=self.retrieved_at_utc,
                    source_labels=labels,
                    currency=None,
                    reporting_date=max(reporting_dates) if reporting_dates else self.period,
                    transformation_steps=(
                        "provider statement retrieval",
                        "statement normalization",
                        "canonical line-item resolution",
                    ),
                    request={"symbol": self.symbol, "period": self.period},
                ),
            )

    @property
    def income_statement(self) -> pd.DataFrame:
        """Return a defensive copy of the normalized income statement."""
        return self._income_statement.copy(deep=True)

    @property
    def balance_sheet(self) -> pd.DataFrame:
        """Return a defensive copy of the normalized balance sheet."""
        return self._balance_sheet.copy(deep=True)

    @property
    def cash_flow_statement(self) -> pd.DataFrame:
        """Return a defensive copy of the normalized cash-flow statement."""
        return self._cash_flow_statement.copy(deep=True)

    @property
    def canonical_line_items(self) -> Mapping[str, FinancialLineItem]:
        """Return a read-only canonical item mapping."""
        return MappingProxyType(dict(self._canonical_line_items))

    def raw_tables(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Return defensive copies of income, balance-sheet, and cash-flow tables."""
        return self.income_statement, self.balance_sheet, self.cash_flow_statement

    def visualize(
        self,
        *,
        statement: str = "balance_sheet",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
    ):
        """Return a figure for the latest numeric column of one statement table."""
        from abaquant.visualization import visualize_financial_snapshot

        return visualize_financial_snapshot(
            self,
            statement=statement,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )
