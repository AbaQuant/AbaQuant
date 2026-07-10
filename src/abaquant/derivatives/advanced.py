"""Convenience imports for advanced derivative models.

This module groups stochastic-volatility, jump-process, Levy-process, and SABR
models under ``abaquant.derivatives.advanced`` while keeping the concrete model
implementations in ``abaquant.derivatives.models``.
"""

from .models import (
    CoxRossRubinsteinModel,
    HestonStochasticVolatilityModel,
    MertonJumpDiffusionModel,
    NormalBachelierModel,
    NormalInverseGaussianModel,
    SABRVolatilityModel,
    VarianceGammaProcessModel,
)

HestonModel = HestonStochasticVolatilityModel
SABRModel = SABRVolatilityModel
MertonModel = MertonJumpDiffusionModel
BachelierModel = NormalBachelierModel
NIGModel = NormalInverseGaussianModel
VarianceGammaModel = VarianceGammaProcessModel

__all__ = [
    "BachelierModel",
    "CoxRossRubinsteinModel",
    "HestonModel",
    "HestonStochasticVolatilityModel",
    "MertonJumpDiffusionModel",
    "MertonModel",
    "NIGModel",
    "NormalBachelierModel",
    "NormalInverseGaussianModel",
    "SABRModel",
    "SABRVolatilityModel",
    "VarianceGammaModel",
    "VarianceGammaProcessModel",
]
