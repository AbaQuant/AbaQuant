"""Theme-aware integrated risk-dashboard visualizations."""

from __future__ import annotations

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


def visualize_risk_dashboard(
    dashboard: object,
    *,
    chart: str = "risk_contribution",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize one integrated risk-dashboard diagnostic.

    Parameters
    ----------
    dashboard : object
        Dashboard object exposing the relevant diagnostic method for ``chart``.
    chart : {"risk_contribution", "drawdown", "credit_scores", "correlation"}, default="risk_contribution"
        Dashboard diagnostic to plot.
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
    normalized = str(chart).strip().lower()
    if normalized == "risk_contribution":
        table = _call_frame(dashboard, "risk_contribution")
        figure = _risk_contribution_figure(table, theme=active_theme)
    elif normalized == "drawdown":
        series = _call_series(dashboard, "drawdown")
        figure = _series_figure(
            series, title="Portfolio drawdown", y_label="Drawdown", theme=active_theme
        )
    elif normalized == "credit_scores":
        table = _call_frame(dashboard, "credit_scores")
        figure = _credit_scores_figure(table, theme=active_theme)
    elif normalized == "correlation":
        table = _call_frame(dashboard, "correlation")
        figure = _correlation_figure(table, theme=active_theme)
    else:
        raise VisualizationError(
            "chart must be one of 'risk_contribution', 'drawdown', 'credit_scores', or 'correlation'."
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"risk_dashboard_{normalized}",
    )


def _call_frame(source: object, method_name: str) -> pd.DataFrame:
    """Call a dashboard method and require a pandas DataFrame result."""
    method = getattr(source, method_name, None)
    if method is None or not callable(method):
        raise VisualizationError(f"dashboard must expose {method_name}().")
    frame = method()
    if not isinstance(frame, pd.DataFrame):
        raise VisualizationError(f"dashboard.{method_name}() must return a DataFrame.")
    return frame


def _call_series(source: object, method_name: str) -> pd.Series:
    """Call a dashboard method and require a pandas Series result."""
    method = getattr(source, method_name, None)
    if method is None or not callable(method):
        raise VisualizationError(f"dashboard must expose {method_name}().")
    series = method()
    if not isinstance(series, pd.Series):
        raise VisualizationError(f"dashboard.{method_name}() must return a Series.")
    return series


def _risk_contribution_figure(table: pd.DataFrame, *, theme: VisualizationTheme):
    """Render percent risk contributions as a themed bar chart."""
    if "percent_risk_contribution" not in table.columns:
        raise VisualizationError("risk_contribution() must include percent_risk_contribution.")
    series = table["percent_risk_contribution"].astype(float).dropna()
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme, grid_axis="y")
        axes.bar(list(series.index), series.to_numpy(dtype=float))
        style_matplotlib_title(axes, "Portfolio risk contribution", theme)
        axes.set_xlabel("Asset")
        axes.set_ylabel("Share of portfolio volatility")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_bar(x=list(series.index), y=series.to_numpy(dtype=float), name="Risk contribution")
    return style_plotly_figure(
        figure,
        theme,
        title="Portfolio risk contribution",
        xaxis_title="Asset",
        yaxis_title="Share of portfolio volatility",
    )


def _series_figure(series: pd.Series, *, title: str, y_label: str, theme: VisualizationTheme):
    """Render one dashboard time series as a themed line chart."""
    clean = series.dropna()
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        axes.plot(clean.index, clean.to_numpy(dtype=float), linewidth=theme.line_width)
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel("Date")
        axes.set_ylabel(y_label)
        figure.autofmt_xdate()
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_scatter(
        x=clean.index,
        y=clean.to_numpy(dtype=float),
        mode="lines",
        name=y_label,
        line={"width": theme.line_width},
    )
    return style_plotly_figure(figure, theme, title=title, xaxis_title="Date", yaxis_title=y_label)


def _credit_scores_figure(table: pd.DataFrame, *, theme: VisualizationTheme):
    """Render synthetic credit-proxy scores by symbol."""
    if "synthetic_credit_proxy_score" not in table.columns:
        raise VisualizationError("credit_scores() must include synthetic_credit_proxy_score.")
    scores = pd.to_numeric(table["synthetic_credit_proxy_score"], errors="coerce").dropna()
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme, grid_axis="y")
        axes.bar(list(scores.index), scores.to_numpy(dtype=float))
        axes.set_ylim(0, 100)
        style_matplotlib_title(axes, "Synthetic credit proxy scores", theme)
        axes.set_xlabel("Issuer")
        axes.set_ylabel("Score")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_bar(x=list(scores.index), y=scores.to_numpy(dtype=float), name="Credit score")
    return style_plotly_figure(
        figure,
        theme,
        title="Synthetic credit proxy scores",
        xaxis_title="Issuer",
        yaxis_title="Score",
    )


def _correlation_figure(correlation: pd.DataFrame, *, theme: VisualizationTheme):
    """Render an asset-correlation heatmap."""
    values = correlation.astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        image = axes.imshow(values.to_numpy(dtype=float), vmin=-1, vmax=1)
        axes.set_xticks(range(len(values.columns)), list(values.columns), rotation=45, ha="right")
        axes.set_yticks(range(len(values.index)), list(values.index))
        style_matplotlib_title(axes, "Asset return correlation", theme)
        figure.colorbar(image, ax=axes, label="Correlation")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(
        data=graph_objects.Heatmap(
            z=values.to_numpy(dtype=float),
            x=list(values.columns),
            y=list(values.index),
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
        )
    )
    return style_plotly_figure(
        figure,
        theme,
        title="Asset return correlation",
        xaxis_title="Asset",
        yaxis_title="Asset",
    )
