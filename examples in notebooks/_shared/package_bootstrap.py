"""Import helper for running examples from installed or source-tree layouts."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")


def ensure_package_importable() -> None:
    """Make ``abaquant`` imports resolve locally.

    Installed packages are used when available. In a source checkout, the
    ``src`` directory is inserted into ``sys.path`` so examples import the
    current local AbaQuant package.
    """
    try:
        importlib.util.find_spec("abaquant")
        import abaquant  # noqa: F401

        return
    except ModuleNotFoundError:
        pass

    example_directory = Path(__file__).resolve().parents[1]
    project_root = example_directory.parent
    source_root = project_root / "src"
    package_init = source_root / "abaquant" / "__init__.py"
    if package_init.exists():
        sys.path.insert(0, str(source_root))
        return

    raise ModuleNotFoundError(
        "Could not import abaquant and could not locate src/abaquant next to examples."
    )
