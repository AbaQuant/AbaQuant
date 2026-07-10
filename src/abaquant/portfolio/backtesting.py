"""Deterministic portfolio backtesting with transparent periodic rebalancing.

Purpose
-------
This module implements a compact but useful portfolio backtesting layer. It
applies transparent target-weight policies to a historical return panel,
rebalances on explicit calendar dates, records transaction costs, compares a
benchmark when supplied, and produces common performance, risk, turnover,
drawdown, rolling, and contribution diagnostics.

Conventions
-----------
Input data are periodic simple returns with observations on a date-like index
and assets on columns. Rebalance schedules are calendar labels such as
``"none"``, ``"daily"``, ``"weekly"``, ``"monthly"``, ``"quarterly"``, or
``"annual"``. Transaction costs and slippage are expressed in basis points of
one-way turnover. ``payoff`` style path values are not annualized; summary
statistics use ``periods_per_year``.

Scope and limitations
---------------------
The backtest is deterministic and close-to-close. It does not model intraday
execution, market impact beyond explicit slippage, taxes, cash interest,
borrowing costs, dividends outside the supplied return series, survivorship
bias, or point-in-time index membership.

References
----------
[1] Bailey, D. H., Borwein, J. M., Lopez de Prado, M., and Zhu, Q. J. (2014),
    "Pseudo-Mathematics and Financial Charlatanism".
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance

RebalanceFrequency = Literal["none", "daily", "weekly", "monthly", "quarterly", "annual"]
WeightSpec = (
    Literal["equal_weight", "buy_and_hold", "inverse_volatility"]
    | Mapping[str, float]
    | Sequence[float]
    | pd.Series
)
DynamicWeightSpec = WeightSpec | Callable[[pd.DataFrame, pd.Timestamp], WeightSpec]
BenchmarkSpec = None | Literal["equal_weight"] | Mapping[str, float] | Sequence[float] | pd.Series

_REBALANCE_FREQUENCIES: dict[str, str] = {
    "daily": "D",
    "weekly": "W",
    "monthly": "M",
    "quarterly": "Q",
    "annual": "Y",
}

# Active returns below this threshold are numerical ties, not benchmark wins.
_ACTIVE_RETURN_TIE_TOLERANCE = 1e-12

_MONTH_COLUMNS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@dataclass(frozen=True)
class PortfolioBacktestResult:
    """Result of a deterministic periodically rebalanced portfolio backtest.

    Parameters
    ----------
    equity_curve_series : pandas.Series
        Portfolio value after each return observation. The first value is the
        initial portfolio value before the first period return.
    periodic_return_series : pandas.Series
        Realized portfolio simple returns after transaction costs. The index
        matches the simulated return dates.
    drawdown_series : pandas.Series
        Portfolio drawdown series, calculated as value divided by running peak
        minus one.
    weights_history : pandas.DataFrame
        Portfolio weights after each rebalance date. Rows are rebalance dates
        and columns are asset labels.
    turnover_series : pandas.Series
        One-way turnover at each rebalance date. The initial allocation records
        zero turnover by convention.
    transaction_cost_series : pandas.Series
        Currency cost paid at each rebalance date.
    asset_contribution_frame : pandas.DataFrame
        Periodic asset-level return contributions to portfolio return.
    trade_weight_frame : pandas.DataFrame
        Weight trades at each rebalance date, target weight minus pre-trade
        drifted weight.
    drifted_weight_frame : pandas.DataFrame
        Pre-trade drifted weights observed at each rebalance date.
    target_weight_frame : pandas.DataFrame
        Target weights selected at each rebalance date.
    benchmark_return_series : pandas.Series, optional
        Realized periodic benchmark returns aligned to the backtest returns.
    benchmark_equity_series : pandas.Series, optional
        Benchmark value path scaled to the same initial capital.
    transaction_cost_bps : float
        Transaction cost in basis points of one-way turnover.
    slippage_bps : float
        Slippage in basis points of one-way turnover.
    fixed_transaction_cost : float
        Fixed currency cost charged whenever a non-zero rebalance trade occurs.
    periods_per_year : int
        Number of return observations interpreted as one year.
    annual_risk_free_rate : float
        Annualized risk-free rate in decimal units.
    initial_capital : float
        Initial portfolio value.
    rebalance : str
        Rebalance-frequency label used for the simulation.
    weight_policy : str
        Human-readable weight policy label.
    """

    equity_curve_series: pd.Series
    periodic_return_series: pd.Series
    drawdown_series: pd.Series
    weights_history: pd.DataFrame
    turnover_series: pd.Series
    transaction_cost_series: pd.Series
    asset_contribution_frame: pd.DataFrame
    trade_weight_frame: pd.DataFrame
    drifted_weight_frame: pd.DataFrame
    target_weight_frame: pd.DataFrame
    benchmark_return_series: pd.Series | None
    benchmark_equity_series: pd.Series | None
    transaction_cost_bps: float
    slippage_bps: float
    fixed_transaction_cost: float
    periods_per_year: int
    annual_risk_free_rate: float
    initial_capital: float
    rebalance: str
    weight_policy: str
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Store defensive pandas copies inside the frozen result object."""
        object.__setattr__(self, "equity_curve_series", self.equity_curve_series.copy(deep=True))
        object.__setattr__(
            self, "periodic_return_series", self.periodic_return_series.copy(deep=True)
        )
        object.__setattr__(self, "drawdown_series", self.drawdown_series.copy(deep=True))
        object.__setattr__(self, "weights_history", self.weights_history.copy(deep=True))
        object.__setattr__(self, "turnover_series", self.turnover_series.copy(deep=True))
        object.__setattr__(
            self, "transaction_cost_series", self.transaction_cost_series.copy(deep=True)
        )
        object.__setattr__(
            self, "asset_contribution_frame", self.asset_contribution_frame.copy(deep=True)
        )
        object.__setattr__(self, "trade_weight_frame", self.trade_weight_frame.copy(deep=True))
        object.__setattr__(self, "drifted_weight_frame", self.drifted_weight_frame.copy(deep=True))
        object.__setattr__(self, "target_weight_frame", self.target_weight_frame.copy(deep=True))
        if self.benchmark_return_series is not None:
            object.__setattr__(
                self, "benchmark_return_series", self.benchmark_return_series.copy(deep=True)
            )
        if self.benchmark_equity_series is not None:
            object.__setattr__(
                self, "benchmark_equity_series", self.benchmark_equity_series.copy(deep=True)
            )
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="portfolio_backtest",
                    source_labels=tuple(str(column) for column in self.weights_history.columns),
                    currency=None,
                    reporting_date=(
                        self.equity_curve_series.index[-1].date().isoformat()
                        if len(self.equity_curve_series.index)
                        else None
                    ),
                    transformation_steps=(
                        "periodic return validation",
                        "rebalance schedule generation",
                        "target weight policy evaluation",
                        "transaction cost and slippage application",
                        "performance metric calculation",
                    ),
                    request={
                        "rebalance": self.rebalance,
                        "weight_policy": self.weight_policy,
                        "periods_per_year": self.periods_per_year,
                        "initial_capital": self.initial_capital,
                        "transaction_cost_bps": self.transaction_cost_bps,
                        "slippage_bps": self.slippage_bps,
                    },
                ),
            )

    def equity_curve(self) -> pd.Series:
        """Return the simulated portfolio value path."""
        return self.equity_curve_series.copy(deep=True)

    def returns(self) -> pd.Series:
        """Return realized periodic portfolio returns after transaction costs."""
        return self.periodic_return_series.copy(deep=True)

    def drawdowns(self) -> pd.Series:
        """Return realized portfolio drawdowns."""
        return self.drawdown_series.copy(deep=True)

    def benchmark_returns(self) -> pd.Series | None:
        """Return benchmark returns when a benchmark was supplied."""
        if self.benchmark_return_series is None:
            return None
        return self.benchmark_return_series.copy(deep=True)

    def benchmark_equity_curve(self) -> pd.Series | None:
        """Return the benchmark value path when a benchmark was supplied."""
        if self.benchmark_equity_series is None:
            return None
        return self.benchmark_equity_series.copy(deep=True)

    def active_returns(self) -> pd.Series | None:
        """Return strategy returns minus benchmark returns when available."""
        if self.benchmark_return_series is None:
            return None
        return (self.periodic_return_series - self.benchmark_return_series).rename("active_return")

    def summary(self) -> dict[str, float]:
        """Return scalar performance, risk, benchmark, turnover, and cost diagnostics."""
        returns = self.periodic_return_series.dropna()
        n_obs = len(returns)
        ending_value = float(self.equity_curve_series.iloc[-1])
        total_turnover = float(self.turnover_series.sum())
        total_transaction_cost = float(self.transaction_cost_series.sum())
        if n_obs == 0:
            return {
                "ending_value": ending_value,
                "total_return": 0.0,
                "cagr": 0.0,
                "annualized_return": 0.0,
                "annualized_volatility": 0.0,
                "downside_deviation": 0.0,
                "sharpe_ratio": np.nan,
                "sortino_ratio": np.nan,
                "max_drawdown": 0.0,
                "average_drawdown": 0.0,
                "calmar_ratio": np.nan,
                "omega_ratio": np.nan,
                "best_period_return": np.nan,
                "worst_period_return": np.nan,
                "win_rate": np.nan,
                "value_at_risk_95": np.nan,
                "conditional_value_at_risk_95": np.nan,
                "skewness": np.nan,
                "kurtosis": np.nan,
                "total_turnover": total_turnover,
                "average_turnover": float(self.turnover_series.mean())
                if len(self.turnover_series)
                else 0.0,
                "transaction_cost_drag": float(total_transaction_cost / self.initial_capital),
                "total_transaction_cost": total_transaction_cost,
            }
        total_return = float(ending_value / self.initial_capital - 1.0)
        cagr = float((ending_value / self.initial_capital) ** (self.periods_per_year / n_obs) - 1.0)
        annualized_return = float(returns.mean() * self.periods_per_year)
        volatility = (
            float(returns.std(ddof=1) * np.sqrt(self.periods_per_year)) if n_obs > 1 else 0.0
        )
        downside_returns = returns[returns < 0.0]
        downside_deviation = (
            float(downside_returns.std(ddof=1) * np.sqrt(self.periods_per_year))
            if len(downside_returns) > 1
            else 0.0
        )
        sharpe_ratio = (
            float((cagr - self.annual_risk_free_rate) / volatility) if volatility > 0 else np.nan
        )
        sortino_ratio = (
            float((cagr - self.annual_risk_free_rate) / downside_deviation)
            if downside_deviation > 0
            else np.nan
        )
        drawdowns = self.drawdown_series.dropna()
        max_drawdown = float(drawdowns.min()) if len(drawdowns) else 0.0
        average_drawdown = (
            float(drawdowns[drawdowns < 0.0].mean()) if (drawdowns < 0.0).any() else 0.0
        )
        calmar_ratio = float(cagr / abs(max_drawdown)) if max_drawdown < 0 else np.nan
        excess_threshold = self.annual_risk_free_rate / self.periods_per_year
        excess = returns - excess_threshold
        gains = excess[excess > 0.0].sum()
        losses = abs(excess[excess < 0.0].sum())
        omega_ratio = float(gains / losses) if losses > 0 else np.nan
        var_95 = float(returns.quantile(0.05))
        cvar_95 = float(returns[returns <= var_95].mean()) if (returns <= var_95).any() else var_95
        summary = {
            "ending_value": ending_value,
            "total_return": total_return,
            "cagr": cagr,
            "annualized_return": annualized_return,
            "annualized_volatility": volatility,
            "downside_deviation": downside_deviation,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "average_drawdown": average_drawdown,
            "calmar_ratio": calmar_ratio,
            "omega_ratio": omega_ratio,
            "best_period_return": float(returns.max()),
            "worst_period_return": float(returns.min()),
            "win_rate": float((returns > 0.0).mean()),
            "value_at_risk_95": var_95,
            "conditional_value_at_risk_95": cvar_95,
            "skewness": float(returns.skew()) if n_obs > 2 else np.nan,
            "kurtosis": float(returns.kurt()) if n_obs > 3 else np.nan,
            "total_turnover": total_turnover,
            "average_turnover": float(self.turnover_series.mean())
            if len(self.turnover_series)
            else 0.0,
            "turnover_events": float((self.turnover_series > 0.0).sum()),
            "transaction_cost_drag": float(total_transaction_cost / self.initial_capital),
            "total_transaction_cost": total_transaction_cost,
        }
        benchmark_summary = self.benchmark_summary()
        summary.update(benchmark_summary)
        return summary

    def benchmark_summary(self) -> dict[str, float]:
        """Return benchmark-relative statistics when a benchmark is available."""
        if self.benchmark_return_series is None or self.benchmark_equity_series is None:
            return {}
        strategy = self.periodic_return_series.reindex(self.benchmark_return_series.index).dropna()
        benchmark = self.benchmark_return_series.reindex(strategy.index).dropna()
        strategy = strategy.reindex(benchmark.index)
        if len(strategy) < 2 or len(benchmark) < 2:
            return {}
        active = strategy - benchmark
        tracking_error = float(active.std(ddof=1) * np.sqrt(self.periods_per_year))
        information_ratio = (
            float(active.mean() * self.periods_per_year / tracking_error)
            if tracking_error > 0
            else np.nan
        )
        variance = float(benchmark.var(ddof=1))
        beta = float(strategy.cov(benchmark) / variance) if variance > 0 else np.nan
        benchmark_cagr = float(
            (self.benchmark_equity_series.iloc[-1] / self.initial_capital)
            ** (self.periods_per_year / len(benchmark))
            - 1.0
        )
        strategy_cagr = float(
            (self.equity_curve_series.iloc[-1] / self.initial_capital)
            ** (self.periods_per_year / len(strategy))
            - 1.0
        )
        alpha = (
            float(
                strategy_cagr
                - (
                    self.annual_risk_free_rate
                    + beta * (benchmark_cagr - self.annual_risk_free_rate)
                )
            )
            if np.isfinite(beta)
            else np.nan
        )
        up_mask = benchmark > 0.0
        down_mask = benchmark < 0.0
        up_capture = (
            float(strategy[up_mask].mean() / benchmark[up_mask].mean())
            if up_mask.any() and benchmark[up_mask].mean() != 0
            else np.nan
        )
        down_capture = (
            float(strategy[down_mask].mean() / benchmark[down_mask].mean())
            if down_mask.any() and benchmark[down_mask].mean() != 0
            else np.nan
        )
        return {
            "benchmark_total_return": float(
                self.benchmark_equity_series.iloc[-1] / self.initial_capital - 1.0
            ),
            "benchmark_cagr": benchmark_cagr,
            "active_total_return": float(
                self.equity_curve_series.iloc[-1] / self.benchmark_equity_series.iloc[-1] - 1.0
            ),
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
            "beta": beta,
            "alpha": alpha,
            "up_capture": up_capture,
            "down_capture": down_capture,
            "hit_rate_vs_benchmark": float((active > _ACTIVE_RETURN_TIE_TOLERANCE).mean()),
        }

    def rolling_metrics(self, window: int = 63) -> pd.DataFrame:
        """Return rolling annualized return, volatility, Sharpe, Sortino, and drawdown metrics."""
        validated_window = _validate_window(window)
        returns = self.periodic_return_series.dropna()
        risk_free_periodic = self.annual_risk_free_rate / self.periods_per_year
        rolling_return = returns.rolling(validated_window).mean() * self.periods_per_year
        rolling_volatility = returns.rolling(validated_window).std(ddof=1) * np.sqrt(
            self.periods_per_year
        )
        rolling_downside = returns.where(returns < 0.0).rolling(validated_window).std(
            ddof=1
        ) * np.sqrt(self.periods_per_year)
        rolling_sharpe = (
            (returns - risk_free_periodic).rolling(validated_window).mean() * self.periods_per_year
        ) / rolling_volatility
        rolling_sortino = (
            (returns - risk_free_periodic).rolling(validated_window).mean() * self.periods_per_year
        ) / rolling_downside
        rolling_max_drawdown = (
            self.drawdown_series.reindex(returns.index).rolling(validated_window).min()
        )
        frame = pd.DataFrame(
            {
                "annualized_return": rolling_return,
                "annualized_volatility": rolling_volatility,
                "sharpe_ratio": rolling_sharpe,
                "sortino_ratio": rolling_sortino,
                "max_drawdown": rolling_max_drawdown,
            }
        )
        if self.benchmark_return_series is not None:
            active = self.active_returns()
            if active is not None:
                frame["tracking_error"] = active.rolling(validated_window).std(ddof=1) * np.sqrt(
                    self.periods_per_year
                )
        return frame.replace([np.inf, -np.inf], np.nan)

    def monthly_returns(self) -> pd.Series:
        """Return calendar-month compounded strategy returns."""
        return _compound_by_period(
            self.periodic_return_series,
            pd.offsets.MonthEnd(),
            name="monthly_return",
        )

    def annual_returns(self) -> pd.Series:
        """Return calendar-year compounded strategy returns."""
        return _compound_by_period(
            self.periodic_return_series,
            pd.offsets.YearEnd(),
            name="annual_return",
        )

    def return_table(self) -> pd.DataFrame:
        """Return a year-by-month table of compounded strategy returns."""
        monthly = self.monthly_returns()
        if monthly.empty:
            return pd.DataFrame(columns=_MONTH_COLUMNS)
        table = pd.DataFrame(
            {
                "year": monthly.index.year,
                "month": monthly.index.month,
                "return": monthly.to_numpy(dtype=float),
            }
        )
        pivot = table.pivot(index="year", columns="month", values="return")
        pivot = pivot.reindex(columns=range(1, 13))
        pivot.columns = _MONTH_COLUMNS
        pivot["Year"] = (
            self.annual_returns().reindex(pivot.index, fill_value=np.nan).to_numpy(dtype=float)
        )
        return pivot

    def drawdown_events(self, top: int = 5) -> pd.DataFrame:
        """Return the largest drawdown episodes sorted by trough drawdown."""
        validated_top = int(top)
        if validated_top <= 0:
            raise ValueError("top must be positive.")
        drawdowns = self.drawdown_series.dropna()
        if drawdowns.empty:
            return pd.DataFrame(
                columns=[
                    "start",
                    "trough",
                    "recovery",
                    "drawdown",
                    "duration_periods",
                    "recovery_periods",
                ]
            )
        events: list[dict[str, object]] = []
        in_drawdown = False
        start_date = drawdowns.index[0]
        segment_dates: list[pd.Timestamp] = []
        segment_values: list[float] = []
        for timestamp, value in drawdowns.items():
            if value < 0.0 and not in_drawdown:
                in_drawdown = True
                start_date = timestamp
                segment_dates = [timestamp]
                segment_values = [float(value)]
            elif value < 0.0 and in_drawdown:
                segment_dates.append(timestamp)
                segment_values.append(float(value))
            elif value >= 0.0 and in_drawdown:
                trough_idx = int(np.argmin(segment_values))
                trough_date = segment_dates[trough_idx]
                trough_value = segment_values[trough_idx]
                events.append(
                    {
                        "start": start_date,
                        "trough": trough_date,
                        "recovery": timestamp,
                        "drawdown": trough_value,
                        "duration_periods": len(segment_dates),
                        "recovery_periods": max(0, len(segment_dates) - trough_idx),
                    }
                )
                in_drawdown = False
        if in_drawdown and segment_dates:
            trough_idx = int(np.argmin(segment_values))
            events.append(
                {
                    "start": start_date,
                    "trough": segment_dates[trough_idx],
                    "recovery": pd.NaT,
                    "drawdown": segment_values[trough_idx],
                    "duration_periods": len(segment_dates),
                    "recovery_periods": np.nan,
                }
            )
        frame = pd.DataFrame(events)
        if frame.empty:
            return pd.DataFrame(
                columns=[
                    "start",
                    "trough",
                    "recovery",
                    "drawdown",
                    "duration_periods",
                    "recovery_periods",
                ]
            )
        return frame.sort_values("drawdown").head(validated_top).reset_index(drop=True)

    def contribution_summary(self) -> pd.DataFrame:
        """Return asset-level cumulative contribution and share diagnostics."""
        contributions = self.asset_contribution_frame.copy(deep=True)
        cumulative = contributions.sum(axis=0)
        absolute = contributions.abs().sum(axis=0)
        share = cumulative / cumulative.sum() if cumulative.sum() != 0 else cumulative * np.nan
        frame = pd.DataFrame(
            {
                "total_return_contribution": cumulative,
                "absolute_return_contribution": absolute,
                "contribution_share": share,
            }
        )
        return frame.sort_values("total_return_contribution", ascending=False)

    def trade_summary(self) -> pd.DataFrame:
        """Return rebalance-date turnover, cost, and largest-trade diagnostics."""
        trades = self.trade_weight_frame.copy(deep=True)
        if trades.empty:
            return pd.DataFrame(
                columns=["turnover", "transaction_cost", "largest_buy", "largest_sell"]
            )
        return pd.DataFrame(
            {
                "turnover": self.turnover_series.reindex(trades.index).fillna(0.0),
                "transaction_cost": self.transaction_cost_series.reindex(trades.index).fillna(0.0),
                "largest_buy": trades.max(axis=1),
                "largest_sell": trades.min(axis=1),
            }
        )

    def cost_summary(self) -> dict[str, float]:
        """Return transaction-cost totals and averages."""
        total_transaction_cost = float(self.transaction_cost_series.sum())
        return {
            "transaction_cost_bps": float(self.transaction_cost_bps),
            "slippage_bps": float(self.slippage_bps),
            "fixed_transaction_cost": float(self.fixed_transaction_cost),
            "total_transaction_cost": total_transaction_cost,
            "transaction_cost_drag": float(total_transaction_cost / self.initial_capital),
            "average_transaction_cost": float(self.transaction_cost_series.mean())
            if len(self.transaction_cost_series)
            else 0.0,
        }

    def as_frame(self) -> pd.DataFrame:
        """Return a compact tabular summary of the simulated path."""
        frame = pd.DataFrame(
            {
                "equity": self.equity_curve_series,
                "return": self.periodic_return_series.reindex(self.equity_curve_series.index),
                "drawdown": self.drawdown_series,
                "turnover": self.turnover_series.reindex(self.equity_curve_series.index).fillna(
                    0.0
                ),
                "transaction_cost": self.transaction_cost_series.reindex(
                    self.equity_curve_series.index
                ).fillna(0.0),
            }
        )
        if self.benchmark_equity_series is not None:
            frame["benchmark_equity"] = self.benchmark_equity_series.reindex(
                self.equity_curve_series.index
            )
        if self.benchmark_return_series is not None:
            frame["benchmark_return"] = self.benchmark_return_series.reindex(
                self.equity_curve_series.index
            )
            frame["active_return"] = frame["return"] - frame["benchmark_return"]
        return frame

    def to_frame(self) -> pd.DataFrame:
        """Alias for :meth:`as_frame` for pandas-style workflows."""
        return self.as_frame()

    def report(self):
        """Return an exportable report for this portfolio backtest result.

        Returns
        -------
        ExportableReport
            Report object with Markdown, HTML, and PDF export methods.
        """
        from abaquant.reports import build_backtest_report

        return build_backtest_report(self)

    def visualize(
        self,
        *,
        chart: str = "equity_curve",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
        rolling_window: int = 63,
    ):
        """Return a figure for a backtest diagnostic.

        Parameters
        ----------
        chart : str, default="equity_curve"
            Diagnostic to visualize. Supported values are ``"equity_curve"``,
            ``"benchmark"``, ``"drawdown"``, ``"weights"``, ``"turnover"``,
            ``"transaction_costs"``, ``"rolling_sharpe"``,
            ``"rolling_volatility"``, ``"return_heatmap"``,
            ``"contributions"``, and ``"trade_weights"``.
        backend : {"matplotlib", "plotly"}, optional
            Visualization backend override.
        theme : VisualizationTheme, optional
            Per-call style override.
        save_path : str or pathlib.Path, optional
            Explicit export path.
        filename : str, optional
            Filename relative to the active theme's save directory.
        rolling_window : int, default=63
            Rolling window used by rolling-metric charts.

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure
            Backend-native figure object.
        """
        from abaquant.visualization import visualize_portfolio_backtest

        return visualize_portfolio_backtest(
            self,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
            rolling_window=rolling_window,
        )


def rebalance_dates(dates: pd.DatetimeIndex, rebalance: str) -> list[pd.Timestamp]:
    """Select the first available observation in each rebalance period."""
    normalized = str(rebalance).strip().lower()
    if normalized == "none":
        return [dates[0]] if len(dates) else []
    if normalized not in _REBALANCE_FREQUENCIES:
        raise ValueError(
            "rebalance must be one of 'none', 'daily', 'weekly', 'monthly', 'quarterly', or 'annual'."
        )
    if normalized == "daily":
        return list(dates)
    periods = dates.to_period(_REBALANCE_FREQUENCIES[normalized])
    date_series = pd.Series(dates, index=dates)
    return list(date_series.groupby(periods).first())


def coerce_backtest_weights(
    weights: WeightSpec,
    asset_symbols: Sequence[str],
    *,
    allow_short: bool = False,
) -> pd.Series:
    """Validate and align a target-weight specification."""
    symbols = [str(symbol) for symbol in asset_symbols]
    if not symbols:
        raise ValueError("at least one asset symbol is required.")
    if isinstance(weights, str):
        normalized = weights.strip().lower()
        if normalized not in {"equal_weight", "buy_and_hold"}:
            raise ValueError(
                "weights as a string must be 'equal_weight', 'buy_and_hold', or handled as a dynamic policy."
            )
        series = pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
    elif isinstance(weights, pd.Series):
        series = weights.reindex(symbols).astype(float)
    elif isinstance(weights, Mapping):
        normalized_map = {str(key): float(value) for key, value in weights.items()}
        if set(normalized_map) != set(symbols):
            missing = sorted(set(symbols) - set(normalized_map))
            extra = sorted(set(normalized_map) - set(symbols))
            details = []
            if missing:
                details.append(f"missing assets: {', '.join(missing)}")
            if extra:
                details.append(f"unknown assets: {', '.join(extra)}")
            raise ValueError("; ".join(details))
        series = pd.Series(normalized_map, dtype=float).reindex(symbols)
    else:
        values = np.asarray(list(weights), dtype=float)
        if values.shape != (len(symbols),):
            raise ValueError("weights must contain one value per asset.")
        series = pd.Series(values, index=symbols, dtype=float)
    if not np.all(np.isfinite(series.to_numpy(dtype=float))):
        raise ValueError("weights must be finite.")
    if not allow_short and (series < -1e-12).any():
        raise ValueError("negative weights require allow_short=True.")
    if not np.isclose(float(series.sum()), 1.0, atol=1e-8):
        raise ValueError("weights must sum to one.")
    return series


def inverse_volatility_weights(
    periodic_returns: pd.DataFrame,
    asset_symbols: Sequence[str],
    *,
    lookback: int = 63,
    min_periods: int = 2,
) -> pd.Series:
    """Return inverse-volatility weights estimated from a historical return window."""
    symbols = [str(symbol) for symbol in asset_symbols]
    history = periodic_returns.reindex(columns=symbols).dropna(how="any")
    if len(history) < min_periods:
        return pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
    window = history.tail(int(lookback)) if lookback and lookback > 0 else history
    vol = window.std(ddof=1).replace(0.0, np.nan)
    inverse = 1.0 / vol
    if inverse.isna().all() or not np.all(np.isfinite(inverse.fillna(0.0).to_numpy(dtype=float))):
        return pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
    inverse = inverse.fillna(0.0)
    if float(inverse.sum()) <= 0.0:
        return pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
    return (inverse / inverse.sum()).astype(float)


def run_rebalanced_backtest(
    periodic_returns: pd.DataFrame,
    *,
    weights: DynamicWeightSpec = "equal_weight",
    rebalance: RebalanceFrequency = "monthly",
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
    fixed_transaction_cost: float = 0.0,
    initial_capital: float = 1.0,
    annual_risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    benchmark: BenchmarkSpec = "equal_weight",
    lookback: int = 63,
    min_history: int = 2,
    allow_short: bool = False,
) -> PortfolioBacktestResult:
    """Run a deterministic periodically rebalanced portfolio backtest.

    Parameters
    ----------
    periodic_returns : pandas.DataFrame
        Periodic simple asset returns with observations in rows and assets in
        columns. Missing rows are removed by complete-case filtering.
    weights : DynamicWeightSpec, default="equal_weight"
        Target allocation applied at each rebalance date. Supported string
        policies are ``"equal_weight"``, ``"buy_and_hold"``, and
        ``"inverse_volatility"``. A callable may return any static weight spec
        from historical returns and the current rebalance date.
    rebalance : {"none", "daily", "weekly", "monthly", "quarterly", "annual"}, default="monthly"
        Calendar rebalance frequency. ``"none"`` applies the initial allocation
        and lets weights drift.
    transaction_cost_bps : float, default=0.0
        One-way transaction cost in basis points of turnover.
    slippage_bps : float, default=0.0
        Additional slippage in basis points of turnover.
    fixed_transaction_cost : float, default=0.0
        Fixed currency cost charged whenever a non-zero rebalance trade occurs.
    initial_capital : float, default=1.0
        Starting portfolio value.
    annual_risk_free_rate : float, default=0.0
        Annualized risk-free rate in decimal units used by performance ratios.
    periods_per_year : int, default=252
        Number of return observations interpreted as one year.
    benchmark : BenchmarkSpec, default="equal_weight"
        Benchmark return specification. A pandas Series is interpreted as
        precomputed benchmark returns. Other weight specs are applied to the
        asset return panel.
    lookback : int, default=63
        Historical window for dynamic policies such as ``"inverse_volatility"``.
    min_history : int, default=2
        Minimum observations before dynamic policy estimates are used.
    allow_short : bool, default=False
        Whether negative weights are permitted.

    Returns
    -------
    PortfolioBacktestResult
        Simulated portfolio path, returns, drawdowns, weights, costs, turnover,
        benchmark diagnostics, and summary statistics.
    """
    returns = _validate_return_panel(periodic_returns)
    validated_cost_bps = _validate_non_negative_float(transaction_cost_bps, "transaction_cost_bps")
    validated_slippage_bps = _validate_non_negative_float(slippage_bps, "slippage_bps")
    validated_fixed_cost = _validate_non_negative_float(
        fixed_transaction_cost, "fixed_transaction_cost"
    )
    validated_initial_capital = _validate_positive_float(initial_capital, "initial_capital")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")
    annual_risk_free_rate = float(annual_risk_free_rate)
    if not np.isfinite(annual_risk_free_rate):
        raise ValueError("annual_risk_free_rate must be finite.")

    symbols = list(returns.columns)
    normalized_rebalance = str(rebalance).strip().lower()
    schedule = set(rebalance_dates(returns.index, normalized_rebalance))
    weight_policy = _weight_policy_label(weights)

    initial_target = _target_weights_for_date(
        weights,
        returns.iloc[:0],
        returns.index[0],
        symbols,
        lookback=lookback,
        min_history=min_history,
        allow_short=allow_short,
    )
    portfolio_value = validated_initial_capital
    current_weights = initial_target.copy()
    holding_values = portfolio_value * current_weights

    initial_timestamp = returns.index[0] - pd.Timedelta(nanoseconds=1)
    equity_records: list[tuple[pd.Timestamp, float]] = [(initial_timestamp, portfolio_value)]
    realized_returns: list[tuple[pd.Timestamp, float]] = []
    contribution_records: list[tuple[pd.Timestamp, pd.Series]] = []
    weights_records: dict[pd.Timestamp, pd.Series] = {returns.index[0]: current_weights.copy()}
    target_records: dict[pd.Timestamp, pd.Series] = {returns.index[0]: current_weights.copy()}
    drifted_records: dict[pd.Timestamp, pd.Series] = {returns.index[0]: current_weights.copy()}
    trade_records: dict[pd.Timestamp, pd.Series] = {
        returns.index[0]: pd.Series(0.0, index=symbols, dtype=float)
    }
    turnover_records: list[tuple[pd.Timestamp, float]] = [(returns.index[0], 0.0)]
    cost_records: list[tuple[pd.Timestamp, float]] = [(returns.index[0], 0.0)]

    for simulation_date, asset_returns in returns.iterrows():
        start_value = float(holding_values.sum())
        if start_value <= 0:
            raise ValueError("portfolio value became non-positive during simulation.")
        drifted_weights = (holding_values / start_value).astype(float)
        if simulation_date in schedule and simulation_date != returns.index[0]:
            history = returns.loc[returns.index < simulation_date]
            target_weights = _target_weights_for_date(
                weights,
                history,
                simulation_date,
                symbols,
                lookback=lookback,
                min_history=min_history,
                allow_short=allow_short,
            )
            trade_weights = target_weights - drifted_weights
            turnover = float(trade_weights.abs().sum())
            variable_cost = (
                start_value * turnover * (validated_cost_bps + validated_slippage_bps) / 10_000.0
            )
            fixed_cost = validated_fixed_cost if turnover > 0.0 else 0.0
            transaction_cost = min(start_value, variable_cost + fixed_cost)
            investable_value = start_value - transaction_cost
            holding_values = investable_value * target_weights
            current_weights = target_weights.copy()
            weights_records[simulation_date] = current_weights.copy()
            target_records[simulation_date] = target_weights.copy()
            drifted_records[simulation_date] = drifted_weights.copy()
            trade_records[simulation_date] = trade_weights.copy()
            turnover_records.append((simulation_date, turnover))
            cost_records.append((simulation_date, transaction_cost))
        else:
            transaction_cost = 0.0
            investable_value = start_value
            current_weights = drifted_weights.copy()
        period_returns = asset_returns.astype(float).reindex(symbols)
        contribution = (holding_values * period_returns) / start_value
        holding_values = holding_values * (1.0 + period_returns)
        end_value = float(holding_values.sum())
        period_return = end_value / start_value - 1.0
        realized_returns.append((simulation_date, period_return))
        contribution_records.append((simulation_date, contribution.astype(float)))
        equity_records.append((simulation_date, end_value))
        portfolio_value = end_value

    equity_curve = pd.Series(
        [value for _, value in equity_records],
        index=pd.DatetimeIndex([date for date, _ in equity_records]),
        name="equity",
    )
    periodic_return_series = pd.Series(
        [value for _, value in realized_returns],
        index=pd.DatetimeIndex([date for date, _ in realized_returns]),
        name="return",
    )
    running_peak = equity_curve.cummax()
    drawdown_series = (equity_curve / running_peak - 1.0).rename("drawdown")
    asset_contribution_frame = pd.DataFrame(
        {date: contribution for date, contribution in contribution_records}
    ).T.reindex(columns=symbols)
    asset_contribution_frame.index = pd.DatetimeIndex(asset_contribution_frame.index)
    weights_history = pd.DataFrame(weights_records).T.reindex(columns=symbols)
    target_weight_frame = pd.DataFrame(target_records).T.reindex(columns=symbols)
    drifted_weight_frame = pd.DataFrame(drifted_records).T.reindex(columns=symbols)
    trade_weight_frame = pd.DataFrame(trade_records).T.reindex(columns=symbols)
    turnover_series = pd.Series(
        [value for _, value in turnover_records],
        index=pd.DatetimeIndex([date for date, _ in turnover_records]),
        name="turnover",
    )
    transaction_cost_series = pd.Series(
        [value for _, value in cost_records],
        index=pd.DatetimeIndex([date for date, _ in cost_records]),
        name="transaction_cost",
    )
    benchmark_returns, benchmark_equity = _build_benchmark(
        benchmark,
        returns,
        initial_capital=validated_initial_capital,
        allow_short=allow_short,
    )
    return PortfolioBacktestResult(
        equity_curve_series=equity_curve,
        periodic_return_series=periodic_return_series,
        drawdown_series=drawdown_series,
        weights_history=weights_history,
        turnover_series=turnover_series,
        transaction_cost_series=transaction_cost_series,
        asset_contribution_frame=asset_contribution_frame,
        trade_weight_frame=trade_weight_frame,
        drifted_weight_frame=drifted_weight_frame,
        target_weight_frame=target_weight_frame,
        benchmark_return_series=benchmark_returns,
        benchmark_equity_series=benchmark_equity,
        transaction_cost_bps=validated_cost_bps,
        slippage_bps=validated_slippage_bps,
        fixed_transaction_cost=validated_fixed_cost,
        periods_per_year=int(periods_per_year),
        annual_risk_free_rate=annual_risk_free_rate,
        initial_capital=validated_initial_capital,
        rebalance=normalized_rebalance,
        weight_policy=weight_policy,
        provenance=DataProvenance(
            provider="derived",
            dataset="portfolio_backtest",
            source_labels=tuple(symbols),
            reporting_date=equity_curve.index[-1].date().isoformat()
            if len(equity_curve.index)
            else None,
            transformation_steps=(
                "periodic return validation",
                "rebalance schedule generation",
                "target weight policy evaluation",
                "transaction cost and slippage application",
                "performance metric calculation",
            ),
            request={
                "rows": len(returns),
                "assets": tuple(symbols),
                "rebalance": normalized_rebalance,
                "weight_policy": weight_policy,
                "transaction_cost_bps": validated_cost_bps,
                "slippage_bps": validated_slippage_bps,
                "fixed_transaction_cost": validated_fixed_cost,
                "initial_capital": validated_initial_capital,
                "benchmark_supplied": benchmark is not None,
            },
        ),
    )


def run_backtest(
    prices: pd.DataFrame,
    strategy_name: str = "equal_weight",
    rebalance_freq: str = "monthly",
    lookback_days: int = 252,
    rf: float = 0.0,
    allow_short: bool = False,
    initial_capital: float = 10_000.0,
    cvar_alpha: float = 0.05,
    target_vol: float = 0.10,
) -> dict | None:
    """Run the legacy dictionary backtest wrapper with English labels."""
    del cvar_alpha, target_vol
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        return None
    returns = prices.pct_change().dropna(how="any")
    if len(returns) < 2:
        return None
    strategy = str(strategy_name).strip().lower()
    if strategy not in {"equal_weight", "buy_and_hold", "inverse_volatility"}:
        strategy = "equal_weight"
    result = run_rebalanced_backtest(
        returns,
        weights=strategy,
        rebalance=rebalance_freq.lower(),
        initial_capital=initial_capital,
        annual_risk_free_rate=rf,
        lookback=lookback_days,
        allow_short=allow_short,
    )
    benchmark_returns = result.benchmark_returns()
    benchmark_equity = result.benchmark_equity_curve()
    return {
        "equity_curve": result.equity_curve().iloc[1:],
        "returns": result.returns(),
        "weights_history": result.weights_history,
        "benchmark_equity": benchmark_equity,
        "benchmark_returns": benchmark_returns,
        "rebalance_dates": list(result.weights_history.index),
        "summary": result.summary(),
        "drawdown_events": result.drawdown_events(),
        "monthly_returns": result.monthly_returns(),
        "annual_returns": result.annual_returns(),
    }


def _validate_return_panel(periodic_returns: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean a periodic return panel."""
    if not isinstance(periodic_returns, pd.DataFrame) or periodic_returns.empty:
        raise ValueError("periodic_returns must be a non-empty DataFrame.")
    returns = periodic_returns.copy().dropna(how="any")
    if len(returns) < 2:
        raise ValueError("at least two complete return observations are required.")
    if not isinstance(returns.index, pd.DatetimeIndex):
        returns.index = pd.to_datetime(returns.index)
    returns = returns.sort_index()
    if returns.index.has_duplicates:
        returns = returns.groupby(level=0).last()
    returns.columns = [str(column) for column in returns.columns]
    if not np.all(np.isfinite(returns.to_numpy(dtype=float))):
        raise ValueError("periodic_returns must contain finite numeric values after dropna().")
    return returns.astype(float)


def _validate_non_negative_float(value: float, name: str) -> float:
    """Validate a finite non-negative float."""
    validated = float(value)
    if not np.isfinite(validated) or validated < 0:
        raise ValueError(f"{name} must be finite and non-negative.")
    return validated


def _validate_positive_float(value: float, name: str) -> float:
    """Validate a finite positive float."""
    validated = float(value)
    if not np.isfinite(validated) or validated <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return validated


def _validate_window(window: int) -> int:
    """Validate a rolling-window length."""
    validated = int(window)
    if validated <= 1:
        raise ValueError("window must be greater than one.")
    return validated


def _weight_policy_label(weights: DynamicWeightSpec) -> str:
    """Return a readable label for a weight policy."""
    if isinstance(weights, str):
        return weights.strip().lower()
    if callable(weights):
        return getattr(weights, "__name__", "callable")
    return "custom"


def _target_weights_for_date(
    weights: DynamicWeightSpec,
    history: pd.DataFrame,
    simulation_date: pd.Timestamp,
    asset_symbols: Sequence[str],
    *,
    lookback: int,
    min_history: int,
    allow_short: bool,
) -> pd.Series:
    """Resolve a static or dynamic target-weight policy for one rebalance date."""
    if callable(weights):
        resolved = weights(history.copy(deep=True), simulation_date)
        return coerce_backtest_weights(resolved, asset_symbols, allow_short=allow_short)
    if isinstance(weights, str) and weights.strip().lower() == "inverse_volatility":
        return inverse_volatility_weights(
            history, asset_symbols, lookback=lookback, min_periods=min_history
        )
    return coerce_backtest_weights(weights, asset_symbols, allow_short=allow_short)


def _build_benchmark(
    benchmark: BenchmarkSpec,
    returns: pd.DataFrame,
    *,
    initial_capital: float,
    allow_short: bool,
) -> tuple[pd.Series | None, pd.Series | None]:
    """Build benchmark return and equity series from a benchmark specification."""
    if benchmark is None:
        return None, None
    if isinstance(benchmark, pd.Series):
        benchmark_returns = benchmark.copy().astype(float)
        benchmark_returns.index = pd.to_datetime(benchmark_returns.index)
        benchmark_returns = benchmark_returns.reindex(returns.index).dropna()
        if benchmark_returns.empty:
            return None, None
        benchmark_returns = benchmark_returns.rename("benchmark_return")
    else:
        benchmark_weights = coerce_backtest_weights(
            benchmark, list(returns.columns), allow_short=allow_short
        )
        benchmark_returns = (returns @ benchmark_weights).rename("benchmark_return")
    start_index = returns.index[0] - pd.Timedelta(nanoseconds=1)
    benchmark_equity = pd.concat(
        [
            pd.Series([initial_capital], index=pd.DatetimeIndex([start_index])),
            initial_capital * (1.0 + benchmark_returns).cumprod(),
        ]
    ).rename("benchmark_equity")
    return benchmark_returns, benchmark_equity


def _compound_by_period(
    returns: pd.Series,
    frequency: str | pd.DateOffset,
    *,
    name: str,
) -> pd.Series:
    """Compound a periodic return series by calendar frequency."""
    series = pd.Series(returns).dropna()
    if series.empty:
        return pd.Series(dtype=float, name=name)
    compounded = (1.0 + series).resample(frequency).prod() - 1.0
    return compounded.dropna().rename(name)


__all__ = [
    "BenchmarkSpec",
    "DynamicWeightSpec",
    "PortfolioBacktestResult",
    "RebalanceFrequency",
    "WeightSpec",
    "coerce_backtest_weights",
    "rebalance_dates",
    "run_backtest",
    "run_rebalanced_backtest",
]
