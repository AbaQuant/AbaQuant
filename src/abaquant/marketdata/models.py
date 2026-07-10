"""Immutable result models for applied market-data workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from abaquant.core import DataProvenance


@dataclass(frozen=True)
class PortfolioResult:
    """Immutable summary of one static allocation or user-specified evaluation.

    The stored weight mapping is converted to a read-only mapping during
    construction. ``as_dict`` returns a plain copy for serialization.
    """

    symbols: tuple[str, ...]
    weights: Mapping[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    risk_free_rate: float
    observations: int
    method: str
    solver_status: str = "not_applicable"
    diagnostics: Mapping[str, object] | None = None
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Freeze mapping fields so callers cannot mutate result state."""
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics or {})))
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="portfolio_result",
                    source_labels=self.symbols,
                    transformation_steps=("portfolio moments", "allocation evaluation"),
                    request={"method": self.method, "observations": self.observations},
                ),
            )

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly defensive copy of all fields."""
        return {
            "symbols": self.symbols,
            "weights": dict(self.weights),
            "expected_return": self.expected_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "risk_free_rate": self.risk_free_rate,
            "observations": self.observations,
            "method": self.method,
            "solver_status": self.solver_status,
            "diagnostics": dict(self.diagnostics),
            "provenance": self.provenance.as_dict(),
        }
