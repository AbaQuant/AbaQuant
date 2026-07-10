"""Immutable scalar parameter objects for named pricing models."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _finite_scalar(name: str, value: float) -> float:
    """Validate and return one finite scalar model input."""
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{name} must be a finite scalar.")
    return numeric


@dataclass(frozen=True)
class BlackScholesMertonParameters:
    """Scalar Black--Scholes--Merton inputs with explicit units."""

    spot_price: float
    strike_price: float
    maturity_years: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0

    def __post_init__(self):
        """Validate finite scalar Black--Scholes--Merton inputs."""
        for name, value in vars(self).items():
            object.__setattr__(self, name, _finite_scalar(name, value))
        if (
            self.spot_price <= 0
            or self.strike_price <= 0
            or self.maturity_years < 0
            or self.volatility < 0
        ):
            raise ValueError(
                "spot, strike, maturity, and volatility must be non-negative with positive prices."
            )


@dataclass(frozen=True)
class LatticeParameters(BlackScholesMertonParameters):
    """Scalar lattice inputs including step count and early-exercise policy."""

    number_of_steps: int = 200
    allow_early_exercise: bool = False

    def __post_init__(self):
        """Validate the lattice step count after base scalar validation."""
        super().__post_init__()
        if int(self.number_of_steps) != self.number_of_steps or self.number_of_steps <= 0:
            raise ValueError("number_of_steps must be a positive integer.")
