"""Shared reporting and figure-export helpers for examples."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.visualization import (
    VisualizationTheme,
    configure_visualization,
    reset_visualization_theme,
)

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = EXAMPLE_ROOT / "generated_figures"


def print_section(title: str) -> None:
    """Print one consistent section heading."""
    print(f"\n=== {title} ===")


def print_mapping(title: str, values: Mapping[str, object], *, decimals: int = 6) -> None:
    """Print a small mapping with stable formatting."""
    print_section(title)
    for key, value in values.items():
        if isinstance(value, float):
            print(f"{key}: {value:.{decimals}f}")
        else:
            print(f"{key}: {value}")


def print_frame(title: str, frame, *, max_rows: int = 8) -> None:
    """Print a pandas-like table with a consistent section heading."""
    print_section(title)
    if hasattr(frame, "tail") and len(frame) > max_rows:
        frame = frame.tail(max_rows)
    print(frame)


def configure_example_visuals(
    *, backend: str = "matplotlib", subdirectory: str = "example_outputs"
) -> Path:
    """Apply a deterministic visual theme and return its output directory."""
    output_directory = FIGURE_DIR / subdirectory
    output_directory.mkdir(parents=True, exist_ok=True)
    configure_visualization(
        VisualizationTheme(
            backend=backend,
            color_sequence=("#0F4C81", "#E07A5F", "#3D9970", "#6C5B7B", "#2E86AB"),
            background_color="#FAFAFA",
            paper_color="#FAFAFA",
            grid_color="#D0D7DE",
            font_family="DejaVu Sans",
            base_font_size=10.0,
            title_font_size=14.0,
            figure_size=(9.0, 5.4),
            dpi=120,
            line_width=2.2,
            marker_size=6.0,
            save_directory=output_directory,
            save_format="png" if backend == "matplotlib" else "html",
            auto_save=False,
            filename_prefix="example",
        )
    )
    return output_directory


def reset_example_visuals() -> None:
    """Restore the package's default visualization theme."""
    reset_visualization_theme()
