"""Configure a global visualization template and export figures."""

from __future__ import annotations

from pathlib import Path

import abaquant as aq
from examples._shared.output import FIGURE_DIR, print_mapping


def configure_blue_theme(output_directory: Path) -> object:
    """Apply a reusable Matplotlib theme for all later visualizations."""
    return aq.configure_visualization(
        aq.VisualizationTheme(
            backend="matplotlib",
            color_sequence=("#0F4C81", "#E07A5F", "#3D9970"),
            background_color="#FAFAFA",
            paper_color="#FAFAFA",
            grid_color="#CBD5E1",
            font_family="DejaVu Sans",
            figure_size=(10.0, 5.8),
            dpi=140,
            line_width=2.5,
            marker_size=6.0,
            save_directory=output_directory,
            save_format="svg",
            auto_save=False,
            filename_prefix="theme_example",
        )
    )


def create_themed_figures(output_directory: Path) -> dict[str, str]:
    """Create figures with global and temporary theme settings."""
    model = aq.BlackScholesMertonModel(100.0, 100.0, 1.0, 0.05, 0.20)
    global_figure = model.visualize(chart="price_profile", filename="global_theme_profile")
    with aq.visualization_theme(
        backend="plotly",
        color_sequence=("#5B2C6F", "#1F618D"),
        save_format="html",
        save_directory=output_directory,
    ):
        temporary_figure = model.visualize(chart="payoff", filename="temporary_plotly_payoff")
    active_theme = aq.get_visualization_theme()
    return {
        "global_figure": type(global_figure).__name__,
        "temporary_figure": type(temporary_figure).__name__,
        "active_backend_after_context": active_theme.backend,
        "output_directory": str(output_directory),
    }


def run() -> None:
    """Run the theme customization example."""
    output_directory = FIGURE_DIR / "visualization_theme"
    output_directory.mkdir(parents=True, exist_ok=True)
    try:
        theme = configure_blue_theme(output_directory)
        print_mapping(
            "Configured theme",
            {"backend": theme.backend, "font_family": theme.font_family, "dpi": theme.dpi},
        )
        print_mapping("Themed figures", create_themed_figures(output_directory))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")
    finally:
        aq.reset_visualization_theme()


if __name__ == "__main__":
    run()
