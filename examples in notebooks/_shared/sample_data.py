"""Deterministic sample data used by all runnable examples."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sample_prices() -> pd.DataFrame:
    """Return a synthetic but smooth price panel for three assets."""
    dates = pd.date_range("2025-01-02", periods=36, freq="B")
    trend = np.linspace(0.0, 1.0, len(dates))
    seasonal = np.sin(np.linspace(0.0, 4.0 * np.pi, len(dates)))
    return pd.DataFrame(
        {
            "ALPHA": 100.0 + 9.0 * trend + 1.8 * seasonal,
            "BETA": 82.0 + 6.0 * trend - 1.2 * seasonal,
            "GAMMA": 54.0 + 3.0 * trend + 0.7 * np.cos(np.linspace(0.0, 3.0 * np.pi, len(dates))),
        },
        index=dates,
    )


def sample_returns() -> pd.DataFrame:
    """Return simple returns derived from :func:`sample_prices`."""
    return sample_prices().pct_change().dropna()


def sample_credit_input_values() -> dict[str, float]:
    """Return a compact deterministic accounting dataset."""
    return {
        "total_debt": 120.0,
        "total_equity": 300.0,
        "current_assets": 250.0,
        "inventory": 40.0,
        "current_liabilities": 100.0,
        "cash_and_cash_equivalents": 50.0,
        "total_assets": 500.0,
        "total_liabilities": 200.0,
        "retained_earnings": 110.0,
        "long_term_debt": 80.0,
        "revenue": 450.0,
        "gross_profit": 200.0,
        "ebit": 75.0,
        "ebitda": 90.0,
        "interest_expense": 10.0,
        "net_income": 60.0,
        "operating_cash_flow": 70.0,
        "previous_total_assets": 470.0,
        "previous_net_income": 55.0,
        "previous_long_term_debt": 90.0,
        "previous_current_assets": 220.0,
        "previous_current_liabilities": 105.0,
        "previous_shares_outstanding": 100.0,
        "previous_gross_profit": 180.0,
        "previous_revenue": 420.0,
    }
