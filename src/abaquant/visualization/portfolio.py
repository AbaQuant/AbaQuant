"""Theme-aware portfolio allocation visualizations."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from .core import (
    VisualizationBackend,
    VisualizationError,
    VisualizationTheme,
    finalize_figure,
    matplotlib_axes,
    require_matplotlib,
    require_plotly,
    resolve_theme,
    style_matplotlib_axes,
    style_matplotlib_title,
    style_plotly_figure,
)


def visualize_portfolio_allocator(
    allocator: object,
    *,
    weights: Sequence[float] | pd.Series | np.ndarray | None = None,
    chart: str = "cumulative_returns",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize weights, cumulative returns, or correlation using one theme."""
    active_theme = resolve_theme(theme, backend)
    context = getattr(allocator, "context", allocator)
    periodic_returns = getattr(context, "periodic_returns", None)
    asset_symbols = list(getattr(context, "asset_symbols", []))
    if not isinstance(periodic_returns, pd.DataFrame) or not asset_symbols:
        raise VisualizationError("allocator must expose a populated portfolio estimation context.")
    if weights is None:
        weight_values = np.repeat(1.0 / len(asset_symbols), len(asset_symbols))
    elif isinstance(weights, pd.Series):
        weight_values = weights.reindex(asset_symbols).to_numpy(dtype=float)
    else:
        weight_values = np.asarray(weights, dtype=float)
    if weight_values.shape != (len(asset_symbols),):
        raise VisualizationError("weights must contain one value per portfolio asset.")
    if chart == "correlation":
        figure = _correlation_figure(periodic_returns.corr(), theme=active_theme)
        return finalize_figure(
            figure,
            backend=active_theme.backend,
            theme=active_theme,
            save_path=save_path,
            filename=filename,
            default_name="portfolio_correlation",
        )
    if chart == "weights":
        x_values, y_values, title, x_label, y_label, kind = (
            asset_symbols,
            weight_values,
            "Portfolio weights",
            "Asset",
            "Weight",
            "bar",
        )
    elif chart == "cumulative_returns":
        portfolio_returns = periodic_returns.to_numpy(dtype=float) @ weight_values
        x_values, y_values = periodic_returns.index, np.cumprod(1.0 + portfolio_returns)
        title, x_label, y_label, kind = (
            "Cumulative portfolio return",
            "Observation",
            "Growth of one currency unit",
            "line",
        )
    else:
        raise VisualizationError("chart must be 'weights', 'cumulative_returns', or 'correlation'.")
    if active_theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, active_theme)
        style_matplotlib_axes(axes, active_theme)
        if kind == "bar":
            axes.bar(x_values, y_values)
        else:
            axes.plot(x_values, y_values, linewidth=active_theme.line_width)
        style_matplotlib_title(axes, title, active_theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        figure.tight_layout()
    else:
        graph_objects = require_plotly()
        figure = graph_objects.Figure()
        if kind == "bar":
            figure.add_bar(x=x_values, y=y_values, name="Weights")
        else:
            figure.add_scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name="Portfolio",
                line={"width": active_theme.line_width},
            )
        style_plotly_figure(
            figure, active_theme, title=title, xaxis_title=x_label, yaxis_title=y_label
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"portfolio_{chart}",
    )


def _correlation_figure(correlation: pd.DataFrame, *, theme: VisualizationTheme):
    """Render a themed correlation matrix heatmap."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        image = axes.imshow(correlation.to_numpy(dtype=float), vmin=-1, vmax=1)
        axes.set_xticks(
            range(len(correlation.columns)), correlation.columns, rotation=45, ha="right"
        )
        axes.set_yticks(range(len(correlation.index)), correlation.index)
        style_matplotlib_title(axes, "Asset return correlation", theme)
        figure.colorbar(image, ax=axes, label="Correlation")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(
        data=graph_objects.Heatmap(
            z=correlation.to_numpy(dtype=float),
            x=list(correlation.columns),
            y=list(correlation.index),
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
        )
    )
    return style_plotly_figure(
        figure, theme, title="Asset return correlation", xaxis_title="Asset", yaxis_title="Asset"
    )


def visualize_portfolio_scenario(
    scenario: object,
    *,
    chart: str = "contributions",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize one portfolio shock scenario.

    Parameters
    ----------
    scenario : object
        Scenario object exposing ``as_frame()``, ``portfolio_return``,
        ``base_value``, and ``ending_value``.
    chart : {"contributions", "shocks", "waterfall"}, default="contributions"
        Scenario diagnostic to plot.
    backend : {"matplotlib", "plotly"}, optional
        Backend override for this figure.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme's save directory.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    active_theme = resolve_theme(theme, backend)
    frame_method = getattr(scenario, "as_frame", None)
    if frame_method is None or not callable(frame_method):
        raise VisualizationError("scenario must expose as_frame().")
    frame = frame_method()
    if chart == "contributions":
        x_values = list(frame.index)
        y_values = frame["contribution"].to_numpy(dtype=float)
        title, y_label = "Portfolio shock return contributions", "Return contribution"
    elif chart == "shocks":
        x_values = list(frame.index)
        y_values = frame["shock"].to_numpy(dtype=float)
        title, y_label = "Asset shock returns", "Shock return"
    elif chart == "waterfall":
        x_values = ["Base value", "After shocks"]
        y_values = [float(scenario.base_value), float(scenario.ending_value)]
        title, y_label = "Portfolio scenario value", "Portfolio value"
    else:
        raise VisualizationError("chart must be 'contributions', 'shocks', or 'waterfall'.")
    if active_theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, active_theme)
        style_matplotlib_axes(axes, active_theme, grid_axis="y")
        axes.bar(x_values, y_values)
        style_matplotlib_title(axes, title, active_theme)
        axes.set_ylabel(y_label)
        figure.tight_layout()
    else:
        graph_objects = require_plotly()
        figure = graph_objects.Figure()
        figure.add_bar(x=x_values, y=y_values)
        style_plotly_figure(
            figure,
            active_theme,
            title=title,
            xaxis_title="Asset" if chart != "waterfall" else "Scenario state",
            yaxis_title=y_label,
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"portfolio_scenario_{chart}",
    )


def visualize_portfolio_backtest(
    backtest: object,
    *,
    chart: str = "equity_curve",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
    rolling_window: int = 63,
):
    """Visualize deterministic portfolio-backtest diagnostics.

    Parameters
    ----------
    backtest : object
        Backtest result exposing path, drawdown, weight, trade, and summary
        methods.
    chart : str, default="equity_curve"
        Supported values are ``"equity_curve"``, ``"benchmark"``,
        ``"drawdown"``, ``"weights"``, ``"turnover"``,
        ``"transaction_costs"``, ``"rolling_sharpe"``,
        ``"rolling_volatility"``, ``"return_heatmap"``,
        ``"contributions"``, and ``"trade_weights"``.
    backend : {"matplotlib", "plotly"}, optional
        Backend override for this figure.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme's save directory.
    rolling_window : int, default=63
        Rolling window used for rolling-metric figures.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    active_theme = resolve_theme(theme, backend)
    chart = str(chart).lower()
    if chart in {"equity_curve", "benchmark"}:
        strategy = backtest.equity_curve()
        benchmark_method = getattr(backtest, "benchmark_equity_curve", None)
        benchmark = benchmark_method() if callable(benchmark_method) else None
        figure = _portfolio_multi_series_figure(
            {"Strategy": strategy, "Benchmark": benchmark}
            if benchmark is not None
            else {"Strategy": strategy},
            title="Backtest equity curve"
            if chart == "equity_curve"
            else "Strategy versus benchmark",
            y_label="Portfolio value",
            theme=active_theme,
        )
    elif chart == "drawdown":
        series = backtest.drawdowns()
        figure = _portfolio_series_figure(
            series, title="Backtest drawdown", y_label="Drawdown", theme=active_theme
        )
    elif chart == "turnover":
        series = backtest.turnover_series
        figure = _portfolio_series_figure(
            series,
            title="Backtest rebalance turnover",
            y_label="One-way turnover",
            theme=active_theme,
            kind="bar",
        )
    elif chart == "transaction_costs":
        series = backtest.transaction_cost_series
        figure = _portfolio_series_figure(
            series,
            title="Backtest transaction costs",
            y_label="Transaction cost",
            theme=active_theme,
            kind="bar",
        )
    elif chart == "weights":
        weights = backtest.weights_history
        if not isinstance(weights, pd.DataFrame) or weights.empty:
            raise VisualizationError("backtest must expose a populated weights_history DataFrame.")
        figure = _portfolio_weights_history_figure(weights, theme=active_theme)
    elif chart == "trade_weights":
        trades = backtest.trade_weight_frame
        if not isinstance(trades, pd.DataFrame) or trades.empty:
            raise VisualizationError(
                "backtest must expose a populated trade_weight_frame DataFrame."
            )
        figure = _portfolio_trade_weights_figure(trades, theme=active_theme)
    elif chart in {"rolling_sharpe", "rolling_volatility"}:
        metrics_method = getattr(backtest, "rolling_metrics", None)
        if metrics_method is None or not callable(metrics_method):
            raise VisualizationError("backtest must expose rolling_metrics().")
        metrics = metrics_method(window=rolling_window)
        column = "sharpe_ratio" if chart == "rolling_sharpe" else "annualized_volatility"
        label = (
            "Rolling Sharpe ratio" if chart == "rolling_sharpe" else "Rolling annualized volatility"
        )
        figure = _portfolio_series_figure(
            metrics[column], title=label, y_label=label, theme=active_theme
        )
    elif chart == "return_heatmap":
        table_method = getattr(backtest, "return_table", None)
        if table_method is None or not callable(table_method):
            raise VisualizationError("backtest must expose return_table().")
        figure = _portfolio_return_heatmap_figure(table_method(), theme=active_theme)
    elif chart == "contributions":
        summary_method = getattr(backtest, "contribution_summary", None)
        if summary_method is None or not callable(summary_method):
            raise VisualizationError("backtest must expose contribution_summary().")
        figure = _portfolio_contribution_figure(summary_method(), theme=active_theme)
    else:
        raise VisualizationError(
            "chart must be one of 'equity_curve', 'benchmark', 'drawdown', 'weights', "
            "'turnover', 'transaction_costs', 'rolling_sharpe', 'rolling_volatility', "
            "'return_heatmap', 'contributions', or 'trade_weights'."
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"portfolio_backtest_{chart}",
    )


def _portfolio_series_figure(
    series: pd.Series,
    *,
    title: str,
    y_label: str,
    theme: VisualizationTheme,
    kind: str = "line",
):
    """Render one backtest time series as a themed figure."""
    series = pd.Series(series).dropna()
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        if kind == "bar":
            axes.bar(series.index, series.to_numpy(dtype=float))
        else:
            axes.plot(series.index, series.to_numpy(dtype=float), linewidth=theme.line_width)
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel("Date")
        axes.set_ylabel(y_label)
        figure.autofmt_xdate()
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    if kind == "bar":
        figure.add_bar(x=series.index, y=series.to_numpy(dtype=float), name=y_label)
    else:
        figure.add_scatter(
            x=series.index,
            y=series.to_numpy(dtype=float),
            mode="lines",
            name=y_label,
            line={"width": theme.line_width},
        )
    return style_plotly_figure(figure, theme, title=title, xaxis_title="Date", yaxis_title=y_label)


def _portfolio_multi_series_figure(
    series_by_name: dict[str, pd.Series | None],
    *,
    title: str,
    y_label: str,
    theme: VisualizationTheme,
):
    """Render multiple backtest series as one themed line figure."""
    clean = {
        name: pd.Series(series).dropna()
        for name, series in series_by_name.items()
        if series is not None
    }
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        for name, series in clean.items():
            axes.plot(
                series.index, series.to_numpy(dtype=float), linewidth=theme.line_width, label=name
            )
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel("Date")
        axes.set_ylabel(y_label)
        axes.legend(loc="best")
        figure.autofmt_xdate()
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for name, series in clean.items():
        figure.add_scatter(
            x=series.index,
            y=series.to_numpy(dtype=float),
            mode="lines",
            name=name,
            line={"width": theme.line_width},
        )
    return style_plotly_figure(figure, theme, title=title, xaxis_title="Date", yaxis_title=y_label)


def _portfolio_weights_history_figure(weights: pd.DataFrame, *, theme: VisualizationTheme):
    """Render rebalance weights through time as a themed stacked area chart."""
    weights = weights.astype(float)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        axes.stackplot(
            weights.index,
            [weights[column].to_numpy(dtype=float) for column in weights.columns],
            labels=list(weights.columns),
        )
        style_matplotlib_title(axes, "Backtest rebalance weights", theme)
        axes.set_xlabel("Date")
        axes.set_ylabel("Weight")
        axes.legend(loc="best")
        figure.autofmt_xdate()
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for column in weights.columns:
        figure.add_scatter(
            x=weights.index,
            y=weights[column].to_numpy(dtype=float),
            mode="lines",
            stackgroup="one",
            name=str(column),
        )
    return style_plotly_figure(
        figure,
        theme,
        title="Backtest rebalance weights",
        xaxis_title="Date",
        yaxis_title="Weight",
    )


def _portfolio_trade_weights_figure(trades: pd.DataFrame, *, theme: VisualizationTheme):
    """Render signed rebalance trades by asset."""
    trades = trades.astype(float)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        width = 0.8 / max(1, len(trades.columns))
        x_positions = np.arange(len(trades.index))
        for offset, column in enumerate(trades.columns):
            axes.bar(
                x_positions + offset * width,
                trades[column].to_numpy(dtype=float),
                width=width,
                label=str(column),
            )
        axes.set_xticks(
            x_positions + width * max(0, len(trades.columns) - 1) / 2,
            [str(x.date()) for x in trades.index],
            rotation=45,
            ha="right",
        )
        style_matplotlib_title(axes, "Backtest rebalance trades", theme)
        axes.set_xlabel("Date")
        axes.set_ylabel("Weight trade")
        axes.legend(loc="best")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for column in trades.columns:
        figure.add_bar(x=trades.index, y=trades[column].to_numpy(dtype=float), name=str(column))
    return style_plotly_figure(
        figure,
        theme,
        title="Backtest rebalance trades",
        xaxis_title="Date",
        yaxis_title="Weight trade",
    )


def _portfolio_return_heatmap_figure(return_table: pd.DataFrame, *, theme: VisualizationTheme):
    """Render a monthly return table as a themed heatmap."""
    table = return_table.copy()
    if "Year" in table.columns:
        table = table.drop(columns=["Year"])
    table = table.astype(float)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        image = axes.imshow(table.to_numpy(dtype=float), aspect="auto")
        axes.set_xticks(range(len(table.columns)), list(table.columns), rotation=45, ha="right")
        axes.set_yticks(range(len(table.index)), list(table.index))
        style_matplotlib_title(axes, "Backtest monthly returns", theme)
        figure.colorbar(image, ax=axes, label="Return")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(
        data=graph_objects.Heatmap(
            z=table.to_numpy(dtype=float),
            x=list(table.columns),
            y=list(table.index),
            colorscale="RdBu",
        )
    )
    return style_plotly_figure(
        figure, theme, title="Backtest monthly returns", xaxis_title="Month", yaxis_title="Year"
    )


def _portfolio_contribution_figure(
    contribution_summary: pd.DataFrame, *, theme: VisualizationTheme
):
    """Render asset-level return contributions as a themed bar chart."""
    if "total_return_contribution" not in contribution_summary.columns:
        raise VisualizationError("contribution_summary must include total_return_contribution.")
    series = contribution_summary["total_return_contribution"].dropna()
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme, grid_axis="y")
        axes.bar(list(series.index), series.to_numpy(dtype=float))
        style_matplotlib_title(axes, "Backtest return contributions", theme)
        axes.set_xlabel("Asset")
        axes.set_ylabel("Return contribution")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_bar(x=list(series.index), y=series.to_numpy(dtype=float), name="Contribution")
    return style_plotly_figure(
        figure,
        theme,
        title="Backtest return contributions",
        xaxis_title="Asset",
        yaxis_title="Return contribution",
    )
