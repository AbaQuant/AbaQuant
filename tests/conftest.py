"""Shared pytest configuration for deterministic, resource-safe tests."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture(autouse=True)
def close_matplotlib_figures() -> Iterator[None]:
    """Close figures created by a test without importing optional Matplotlib."""
    yield
    pyplot = sys.modules.get("matplotlib.pyplot")
    if pyplot is not None:
        pyplot.close("all")
