"""Deterministic tests for global visualization style and export behavior."""

from __future__ import annotations

import pytest

from abaquant.derivatives.models import BlackScholesMertonModel
from abaquant.visualization import (
    VisualizationTheme,
    configure_visualization,
    get_visualization_theme,
    reset_visualization_theme,
    visualization_theme,
)


def _model() -> BlackScholesMertonModel:
    """Create one scalar model suitable for a deterministic payoff plot."""
    return BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)


def test_global_theme_controls_default_matplotlib_figure_size(tmp_path) -> None:
    """Configured global dimensions and auto-save apply without per-call options."""
    pytest.importorskip("matplotlib")
    try:
        configure_visualization(
            VisualizationTheme(
                backend="matplotlib",
                figure_size=(4.0, 2.5),
                dpi=80,
                color_sequence=("#123456", "#abcdef"),
                save_directory=tmp_path,
                auto_save=True,
            )
        )
        figure = _model().visualize(chart="payoff")
        assert tuple(round(value, 1) for value in figure.get_size_inches()) == (4.0, 2.5)
        assert list(tmp_path.glob("*.png"))
    finally:
        reset_visualization_theme()


def test_context_theme_restores_previous_global_theme() -> None:
    """A context-managed style override does not change the outer template."""
    try:
        configure_visualization(VisualizationTheme(backend="matplotlib"))
        with visualization_theme(backend="plotly"):
            assert get_visualization_theme().backend == "plotly"
        assert get_visualization_theme().backend == "matplotlib"
    finally:
        reset_visualization_theme()
