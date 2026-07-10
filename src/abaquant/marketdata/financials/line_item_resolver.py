"""Canonical financial-line-item resolution across provider-specific labels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models import FinancialLineItem

CANONICAL_FINANCIAL_LINE_ITEMS: dict[str, tuple[str, ...]] = {
    "total_debt": (
        "Total Debt",
        "Short Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
    ),
    "total_equity": (
        "Stockholders Equity",
        "Total Equity Gross Minority Interest",
        "Stockholders Equity Including Minority Interest",
    ),
    "current_assets": ("Current Assets", "Total Current Assets"),
    "inventory": ("Inventory", "Inventories"),
    "current_liabilities": ("Current Liabilities", "Total Current Liabilities"),
    "cash_and_cash_equivalents": (
        "Cash Cash Equivalents And Short Term Investments",
        "Cash And Cash Equivalents",
        "Cash Financial",
    ),
    "ebit": ("EBIT", "Operating Income"),
    "ebitda": ("EBITDA", "Normalized EBITDA"),
    "interest_expense": ("Interest Expense", "Interest Expense Non Operating"),
    "operating_cash_flow": ("Operating Cash Flow", "Total Cash From Operating Activities"),
    "total_assets": ("Total Assets",),
    "total_liabilities": ("Total Liabilities Net Minority Interest", "Total Liabilities"),
    "retained_earnings": ("Retained Earnings", "Retained Earnings Accumulated Deficit"),
    "revenue": ("Total Revenue", "Operating Revenue"),
    "net_income": ("Net Income", "Net Income Common Stockholders"),
    "long_term_debt": ("Long Term Debt", "Long Term Debt And Capital Lease Obligation"),
    "shares_outstanding": (
        "Ordinary Shares Number",
        "Share Issued",
        "Common Stock Shares Outstanding",
    ),
    "gross_profit": ("Gross Profit",),
}
LINE_ITEM_STATEMENT = {
    "total_debt": "balance_sheet",
    "total_equity": "balance_sheet",
    "current_assets": "balance_sheet",
    "inventory": "balance_sheet",
    "current_liabilities": "balance_sheet",
    "cash_and_cash_equivalents": "balance_sheet",
    "ebit": "income_statement",
    "ebitda": "income_statement",
    "interest_expense": "income_statement",
    "operating_cash_flow": "cash_flow_statement",
    "total_assets": "balance_sheet",
    "total_liabilities": "balance_sheet",
    "retained_earnings": "balance_sheet",
    "revenue": "income_statement",
    "net_income": "income_statement",
    "long_term_debt": "balance_sheet",
    "shares_outstanding": "balance_sheet",
    "gross_profit": "income_statement",
}


def find_label(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    """Resolve a provider label by case-insensitive exact matching."""
    labels = {str(index).casefold(): str(index) for index in frame.index}
    return next((labels[c.casefold()] for c in candidates if c.casefold() in labels), None)


def latest_value(frame: pd.DataFrame, label: str | None) -> tuple[float | None, str | None]:
    """Return the first finite value from provider-order statement columns."""
    if label is None or label not in frame.index:
        return None, None
    for col, value in pd.to_numeric(frame.loc[label], errors="coerce").items():
        if pd.notna(value) and np.isfinite(float(value)):
            return float(value), str(col)
    return None, None


def resolve_line_items(
    income: pd.DataFrame, balance: pd.DataFrame, cash_flow: pd.DataFrame
) -> dict[str, FinancialLineItem]:
    """Build canonical latest-value items with original-label provenance."""
    frames = {
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow_statement": cash_flow,
    }
    result = {}
    for name, candidates in CANONICAL_FINANCIAL_LINE_ITEMS.items():
        statement_type = LINE_ITEM_STATEMENT[name]
        label = find_label(frames[statement_type], candidates)
        value, reported = latest_value(frames[statement_type], label)
        result[name] = FinancialLineItem(name, value, statement_type, reported, label)
    return result


def history_for_item(frame: pd.DataFrame, candidates: tuple[str, ...]) -> tuple[float, ...]:
    """Return finite values ordered oldest-to-newest where dates are parseable."""
    label = find_label(frame, candidates)
    if label is None:
        return ()
    dated = []
    fallback = []
    for column, value in pd.to_numeric(frame.loc[label], errors="coerce").items():
        if pd.notna(value) and np.isfinite(float(value)):
            try:
                dated.append((pd.Timestamp(column), float(value)))
            except (TypeError, ValueError):
                fallback.append(float(value))
    return tuple(v for _, v in sorted(dated)) if dated else tuple(reversed(fallback))
