"""Import every public module used by the examples.

The script is intentionally small and function-based so it can double as a
smoke test for source-package imports.
"""

from __future__ import annotations

import importlib

from _shared.output import print_mapping, print_section
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

PUBLIC_MODULES = (
    "abaquant",
    "abaquant.derivatives.vanilla",
    "abaquant.derivatives.trees",
    "abaquant.derivatives.forwards",
    "abaquant.derivatives.strategies",
    "abaquant.derivatives.exotics",
    "abaquant.financial_math.tvm",
    "abaquant.financial_math.rates",
    "abaquant.rates",
    "abaquant.financial_math.annuities",
    "abaquant.financial_math.bonds",
    "abaquant.financial_math.cashflows",
    "abaquant.financial_math.corporate",
    "abaquant.financial_math.equity",
    "abaquant.financial_math.loans",
    "abaquant.financial_math.portfolio",
    "abaquant.financial_math.risk",
    "abaquant.derivatives.models",
    "abaquant.derivatives.advanced",
    "abaquant.derivatives.models.black_scholes",
    "abaquant.derivatives.models.binomial",
    "abaquant.derivatives.models.bachelier",
    "abaquant.derivatives.models.heston",
    "abaquant.derivatives.models.merton",
    "abaquant.derivatives.models.nig",
    "abaquant.derivatives.models.sabr",
    "abaquant.derivatives.models.variance_gamma",
    "abaquant.derivatives.calibration",
    "abaquant.derivatives.calibration.core",
    "abaquant.derivatives.analytics.distributions",
    "abaquant.derivatives.analytics.parity",
    "abaquant.derivatives.analytics.volatility",
    "abaquant.derivatives.monte_carlo",
    "abaquant.derivatives.numerics.implied_volatility",
    "abaquant.derivatives.simulation.gbm",
    "abaquant.derivatives.simulation.merton",
    "abaquant.derivatives.simulation.levy",
    "abaquant.credit.fundamentals",
    "abaquant.credit.cds",
    "abaquant.credit.cdo",
    "abaquant.credit.copula",
    "abaquant.credit.transitions",
    "abaquant.credit.valuation",
    "abaquant.credit.risk",
    "abaquant.credit.distribution",
    "abaquant.portfolio.optimization",
    "abaquant.portfolio.efficient_frontier",
    "abaquant.portfolio.risk_metrics",
    "abaquant.portfolio.backtesting",
    "abaquant.portfolio.stress_testing",
    "abaquant.portfolio.hierarchical",
    "abaquant.risk",
    "abaquant.risk.dashboard",
    "abaquant.reports",
    "abaquant.reports.exportable",
    "abaquant.core",
    "abaquant.core.provenance",
    "abaquant.marketdata",
    "abaquant.marketdata.financials",
    "abaquant.marketdata.option_chain_analytics",
    "abaquant.marketdata.providers.sec",
    "abaquant.visualization",
)


def import_public_modules() -> dict[str, str]:
    """Import every public module and return its import status."""
    return {
        module_name: type(importlib.import_module(module_name)).__name__
        for module_name in PUBLIC_MODULES
    }


def run() -> None:
    """Execute the import smoke test."""
    print_section("Public module import coverage")
    statuses = import_public_modules()
    print(f"Imported {len(statuses)} modules.")
    print_mapping("Representative imports", dict(list(statuses.items())[:8]))


if __name__ == "__main__":
    run()
