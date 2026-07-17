"""Deterministic offline market-data provider used by runnable examples."""

from __future__ import annotations

import pandas as pd

from .sample_data import sample_prices


class DeterministicMarketDataProvider:
    """Provide repeatable quote, history, option, and statement fixtures."""

    name = "deterministic-example"

    def fast_info(self, symbol: str) -> dict[str, float]:
        """Return a deterministic lightweight quote mapping."""
        prices = sample_prices()
        return {"lastPrice": float(prices.iloc[-1, 0])}

    def info(self, symbol: str) -> dict[str, object]:
        """Return deterministic ticker metadata."""
        return {"currency": "USD", "marketCap": 600.0, "symbol": symbol}

    def history(self, symbol: str, **kwargs: object) -> pd.DataFrame:
        """Return deterministic single-symbol price history."""
        return pd.DataFrame({"Close": sample_prices().iloc[:, 0]})

    def history_many(self, symbols: object, **kwargs: object) -> pd.DataFrame:
        """Return a deterministic batched price panel."""
        return sample_prices().reindex(columns=list(symbols))

    def option_expirations(self, symbol: str) -> list[str]:
        """Return deterministic option expiries."""
        return ["2027-01-15", "2027-06-18", "2028-01-21"]

    def option_chain(self, symbol: str, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return deterministic call and put option-chain tables."""
        expiry_shift = {"2027-01-15": 0.00, "2027-06-18": 0.025, "2028-01-21": 0.045}.get(
            expiry, 0.0
        )
        strikes = [80.0, 90.0, 100.0, 110.0, 120.0]
        calls = pd.DataFrame(
            {
                "contractSymbol": [f"{symbol}C{int(strike)}" for strike in strikes],
                "strike": strikes,
                "lastPrice": [22.0, 14.5, 8.0, 4.5, 2.4],
                "bid": [21.5, 14.0, 7.6, 4.1, 2.0],
                "ask": [22.5, 15.0, 8.4, 4.9, 2.8],
                "impliedVolatility": [
                    0.31 + expiry_shift,
                    0.27 + expiry_shift,
                    0.23 + expiry_shift,
                    0.25 + expiry_shift,
                    0.29 + expiry_shift,
                ],
                "openInterest": [120, 240, 520, 310, 180],
                "volume": [12, 28, 65, 34, 16],
            }
        )
        puts = pd.DataFrame(
            {
                "contractSymbol": [f"{symbol}P{int(strike)}" for strike in strikes],
                "strike": strikes,
                "lastPrice": [2.2, 4.1, 7.8, 13.9, 21.0],
                "bid": [1.9, 3.8, 7.4, 13.4, 20.4],
                "ask": [2.5, 4.4, 8.2, 14.4, 21.6],
                "impliedVolatility": [
                    0.35 + expiry_shift,
                    0.30 + expiry_shift,
                    0.24 + expiry_shift,
                    0.26 + expiry_shift,
                    0.32 + expiry_shift,
                ],
                "openInterest": [210, 330, 610, 270, 155],
                "volume": [18, 36, 70, 29, 14],
            }
        )
        return calls, puts

    def income_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a deterministic income-statement fixture."""
        return pd.DataFrame(
            {
                "2025-12-31": {
                    "Total Revenue": 450.0,
                    "EBITDA": 90.0,
                    "EBIT": 75.0,
                    "Interest Expense": 10.0,
                    "Net Income": 60.0,
                    "Gross Profit": 200.0,
                }
            }
        )

    def balance_sheet(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a deterministic balance-sheet fixture."""
        return pd.DataFrame(
            {
                "2025-12-31": {
                    "Total Debt": 120.0,
                    "Stockholders Equity": 300.0,
                    "Current Assets": 250.0,
                    "Inventory": 40.0,
                    "Current Liabilities": 100.0,
                    "Cash And Cash Equivalents": 50.0,
                    "Total Assets": 500.0,
                    "Total Liabilities": 200.0,
                    "Retained Earnings": 110.0,
                    "Long Term Debt": 80.0,
                }
            }
        )

    def cash_flow_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a deterministic cash-flow fixture."""
        return pd.DataFrame({"2025-12-31": {"Operating Cash Flow": 70.0}})
