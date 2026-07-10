"""Public import-path tests for the v1-style package structure."""

from __future__ import annotations

import importlib

import pytest


def test_clean_v1_import_paths_are_available() -> None:
    """Import the public v1 namespaces used in user-facing examples."""
    from abaquant.core import DataProvenance
    from abaquant.credit import CreditAnalysisInputs
    from abaquant.derivatives import BlackScholesMertonModel, OptionStrategy
    from abaquant.derivatives.advanced import HestonModel, SABRModel
    from abaquant.derivatives.calibration import HestonCalibration
    from abaquant.portfolio import PortfolioAllocator
    from abaquant.rates import get_rate_curve
    from abaquant.reports import ExportableReport
    from abaquant.risk import RiskDashboard

    assert BlackScholesMertonModel.__name__ == "BlackScholesMertonModel"
    assert HestonModel.__name__ == "HestonStochasticVolatilityModel"
    assert SABRModel.__name__ == "SABRVolatilityModel"
    assert OptionStrategy.__name__ == "OptionStrategy"
    assert HestonCalibration.__name__ == "HestonCalibration"
    assert PortfolioAllocator.__name__ == "PortfolioAllocator"
    assert CreditAnalysisInputs.__name__ == "CreditAnalysisInputs"
    assert RiskDashboard.__name__ == "RiskDashboard"
    assert ExportableReport.__name__ == "ExportableReport"
    assert DataProvenance.__name__ == "DataProvenance"
    assert callable(get_rate_curve)


def test_pre_v1_module_paths_are_removed() -> None:
    """Ensure old pre-v1 module families are not part of the clean API."""
    for module_name in (
        "abaquant.advanced_derivatives",
        "abaquant.portfolioopt",
        "abaquant.creditrisk",
        "abaquant.provenance",
        "abaquant.reporting",
        "abaquant.risk_dashboard",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_root_version_and_exports_are_consistent() -> None:
    """The v1 root namespace exposes all documented public facade names."""
    import abaquant

    assert abaquant.__version__ == "1.0.0rc1"
    for name in (
        "future_value",
        "get_ticker",
        "MarketTicker",
        "configure_visualization",
        "VisualizationTheme",
        "ExportableReport",
        "RiskDashboard",
        "DataProvenance",
    ):
        assert hasattr(abaquant, name)
        assert name in abaquant.__all__
