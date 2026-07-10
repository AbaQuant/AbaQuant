"""Theme-aware market-price and financial-statement visualizations."""

from __future__ import annotations

from pathlib import Path

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


def visualize_price_history(
    price_history: pd.DataFrame,
    *,
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize one or more normalized market-price columns using one theme."""
    active_theme = resolve_theme(theme, backend)
    if not isinstance(price_history, pd.DataFrame) or price_history.empty:
        raise VisualizationError("price_history must be a non-empty pandas DataFrame.")
    numeric_history = price_history.select_dtypes(include="number")
    if numeric_history.empty:
        raise VisualizationError("price_history contains no numeric columns.")
    if active_theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, active_theme)
        style_matplotlib_axes(axes, active_theme)
        numeric_history.plot(
            ax=axes, linewidth=active_theme.line_width, color=list(active_theme.color_sequence)
        )
        style_matplotlib_title(axes, "Market price history", active_theme)
        axes.set_xlabel("Date")
        axes.set_ylabel("Price")
        figure.tight_layout()
    else:
        graph_objects = require_plotly()
        figure = graph_objects.Figure()
        for column in numeric_history.columns:
            figure.add_scatter(
                x=numeric_history.index,
                y=numeric_history[column],
                mode="lines",
                name=str(column),
                line={"width": active_theme.line_width},
            )
        style_plotly_figure(
            figure,
            active_theme,
            title="Market price history",
            xaxis_title="Date",
            yaxis_title="Price",
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name="market_price_history",
    )


def visualize_financial_snapshot(
    snapshot: object,
    *,
    statement: str = "balance_sheet",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize the latest numeric column of one normalized statement table."""
    active_theme = resolve_theme(theme, backend)
    statement_frame = getattr(snapshot, statement, None)
    if not isinstance(statement_frame, pd.DataFrame) or statement_frame.empty:
        raise VisualizationError(
            "statement must name a non-empty FinancialStatementSnapshot table property."
        )
    numeric_frame = statement_frame.select_dtypes(include="number")
    if numeric_frame.empty:
        raise VisualizationError("The requested statement has no numeric values.")
    values = numeric_frame.iloc[:, 0].dropna().sort_values()
    title = f"{statement.replace('_', ' ').title()} (latest column)"
    if active_theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, active_theme)
        style_matplotlib_axes(axes, active_theme, grid_axis="x")
        axes.barh([str(index) for index in values.index], values.to_numpy())
        style_matplotlib_title(axes, title, active_theme)
        axes.set_xlabel("Reported value")
        figure.tight_layout()
    else:
        graph_objects = require_plotly()
        figure = graph_objects.Figure()
        figure.add_bar(
            y=[str(index) for index in values.index], x=values.to_numpy(), orientation="h"
        )
        style_plotly_figure(
            figure, active_theme, title=title, xaxis_title="Reported value", yaxis_title="Line item"
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=statement,
    )
