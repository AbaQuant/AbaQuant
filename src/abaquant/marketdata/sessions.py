"""Mutable request-local state separated from immutable market-data configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class TickerIdentity:
    """Immutable identifier for one normalized ticker and provider."""

    symbol: str
    provider_name: str


@dataclass(frozen=True)
class TickerConfiguration:
    """Immutable cache and request policy for a ticker facade."""

    financial_cache_mode: str = "memory"
    cache_directory: str | None = None


@dataclass
class TickerSession:
    """Mutable in-memory financial snapshots and request-local diagnostics."""

    financial_snapshots: dict[str, Any] = field(default_factory=dict)
    request_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UniverseSession:
    """Mutable in-memory price panels for one universe facade."""

    price_panels: dict[tuple[Any, ...], pd.DataFrame] = field(default_factory=dict)
