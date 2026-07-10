"""Theme-aware fundamental credit-proxy visualizations."""

from __future__ import annotations

from pathlib import Path

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


def visualize_credit_assessment(
    assessment: object,
    *,
    chart: str = "metrics",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize a synthetic score or available metrics with the active theme."""
    active_theme = resolve_theme(theme, backend)
    if chart == "score":
        score = getattr(assessment, "synthetic_credit_proxy_score", None)
        if score is None:
            raise VisualizationError(
                "A synthetic credit proxy score is unavailable for this assessment."
            )
        labels, values, title, y_label = (
            ["Synthetic proxy score"],
            [float(score)],
            "Synthetic credit-proxy score",
            "Score (0-100)",
        )
    elif chart == "metrics":
        raw_metrics = getattr(assessment, "metrics", None)
        if raw_metrics is None:
            raise VisualizationError("assessment must expose a metrics mapping.")
        numeric_metrics = {
            name: value
            for name, value in raw_metrics.items()
            if isinstance(value, (int, float)) and value is not None
        }
        if not numeric_metrics:
            raise VisualizationError("No numeric credit metrics are available to visualize.")
        labels, values, title, y_label = (
            list(numeric_metrics),
            [float(value) for value in numeric_metrics.values()],
            "Available credit-proxy metrics",
            "Metric value",
        )
    else:
        raise VisualizationError("chart must be 'metrics' or 'score'.")
    if active_theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, active_theme)
        style_matplotlib_axes(axes, active_theme, grid_axis="y")
        axes.bar(labels, values)
        style_matplotlib_title(axes, title, active_theme)
        axes.set_ylabel(y_label)
        axes.tick_params(axis="x", rotation=45)
        figure.tight_layout()
    else:
        graph_objects = require_plotly()
        figure = graph_objects.Figure()
        figure.add_bar(x=labels, y=values)
        style_plotly_figure(
            figure, active_theme, title=title, xaxis_title="Metric", yaxis_title=y_label
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"credit_{chart}",
    )


def visualize_credit_scenario(
    scenario: object,
    *,
    metric: str = "synthetic_credit_proxy_score",
    chart: str = "heatmap",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize a credit multiplier scenario grid.

    Parameters
    ----------
    scenario : object
        Scenario object exposing a long-form ``data`` DataFrame with multiplier
        columns and the requested metric.
    metric : str, default="synthetic_credit_proxy_score"
        Numeric credit scenario metric to display.
    chart : {"heatmap", "curves", "bar"}, default="heatmap"
        Visual form for the scenario table.
    backend : {"matplotlib", "plotly"}, optional
        Backend override for this figure.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme's save directory.
    """
    active_theme = resolve_theme(theme, backend)
    data = getattr(scenario, "data", None)
    if data is None or metric not in data.columns:
        raise VisualizationError(f"scenario must expose metric column {metric!r}.")
    numeric = data.dropna(subset=[metric]).copy()
    if numeric.empty:
        raise VisualizationError(f"No numeric values are available for {metric!r}.")
    metric_label = metric.replace("_", " ").title()
    if chart == "heatmap":
        pivot = numeric.pivot_table(
            index="ebitda_multiplier",
            columns="debt_multiplier",
            values=metric,
            aggfunc="mean",
        ).sort_index()
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)
        figure = _credit_scenario_heatmap(pivot, metric_label=metric_label, theme=active_theme)
    elif chart == "curves":
        figure = _credit_scenario_curves(
            numeric, metric=metric, metric_label=metric_label, theme=active_theme
        )
    elif chart == "bar":
        labels = [
            f"D*{row.debt_multiplier:g}, EBITDA*{row.ebitda_multiplier:g}"
            for row in numeric.itertuples()
        ]
        values = numeric[metric].astype(float).to_numpy()
        figure = _credit_scenario_bar(labels, values, metric_label=metric_label, theme=active_theme)
    else:
        raise VisualizationError("chart must be 'heatmap', 'curves', or 'bar'.")
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"credit_scenario_{metric}_{chart}",
    )


def _credit_scenario_heatmap(frame, *, metric_label: str, theme: VisualizationTheme):
    """Render a debt-by-EBITDA credit scenario heatmap."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        image = axes.imshow(frame.to_numpy(dtype=float), aspect="auto", origin="lower")
        axes.set_xticks(range(len(frame.columns)), [f"{value:g}" for value in frame.columns])
        axes.set_yticks(range(len(frame.index)), [f"{value:g}" for value in frame.index])
        axes.set_xlabel("Debt multiplier")
        axes.set_ylabel("EBITDA multiplier")
        style_matplotlib_title(axes, f"Credit scenario {metric_label}", theme)
        figure.colorbar(image, ax=axes, label=metric_label)
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(
        data=graph_objects.Heatmap(
            x=list(frame.columns),
            y=list(frame.index),
            z=frame.to_numpy(dtype=float),
            colorbar={"title": metric_label},
        )
    )
    return style_plotly_figure(
        figure,
        theme,
        title=f"Credit scenario {metric_label}",
        xaxis_title="Debt multiplier",
        yaxis_title="EBITDA multiplier",
    )


def _credit_scenario_curves(data, *, metric: str, metric_label: str, theme: VisualizationTheme):
    """Render credit scenario curves by EBITDA multiplier."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        for ebitda_multiplier, group in data.groupby("ebitda_multiplier"):
            ordered = group.sort_values("debt_multiplier")
            axes.plot(
                ordered["debt_multiplier"],
                ordered[metric],
                linewidth=theme.line_width,
                marker="o",
                label=f"EBITDA*{ebitda_multiplier:g}",
            )
        style_matplotlib_title(axes, f"Credit scenario {metric_label}", theme)
        axes.set_xlabel("Debt multiplier")
        axes.set_ylabel(metric_label)
        axes.legend(prop={"family": theme.font_family, "size": theme.base_font_size})
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for ebitda_multiplier, group in data.groupby("ebitda_multiplier"):
        ordered = group.sort_values("debt_multiplier")
        figure.add_scatter(
            x=ordered["debt_multiplier"],
            y=ordered[metric],
            mode="lines+markers",
            name=f"EBITDA*{ebitda_multiplier:g}",
            line={"width": theme.line_width},
        )
    return style_plotly_figure(
        figure,
        theme,
        title=f"Credit scenario {metric_label}",
        xaxis_title="Debt multiplier",
        yaxis_title=metric_label,
    )


def _credit_scenario_bar(labels, values, *, metric_label: str, theme: VisualizationTheme):
    """Render compact bar scenarios for a small credit grid."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme, grid_axis="y")
        axes.bar(labels, values)
        axes.tick_params(axis="x", rotation=45)
        axes.set_ylabel(metric_label)
        style_matplotlib_title(axes, f"Credit scenario {metric_label}", theme)
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_bar(x=labels, y=values)
    return style_plotly_figure(
        figure,
        theme,
        title=f"Credit scenario {metric_label}",
        xaxis_title="Scenario",
        yaxis_title=metric_label,
    )
