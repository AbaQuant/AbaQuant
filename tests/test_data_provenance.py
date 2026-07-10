"""Tests for provider-neutral data provenance metadata."""

from __future__ import annotations

import numpy as np
import pandas as pd

from abaquant import DataProvenance, RiskDashboard
from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    IncomeStatementInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives.calibration import BSMFlatVolCalibration
from abaquant.derivatives.models import BlackScholesMertonModel
from abaquant.marketdata.financials.models import FinancialStatementSnapshot
from abaquant.marketdata.providers import SecCompanyFacts
from abaquant.portfolio import PortfolioAllocator
from abaquant.rates import RateCurve


def sample_returns() -> pd.DataFrame:
    """Return a compact deterministic asset-return panel."""
    index = pd.date_range("2026-01-01", periods=12, freq="D")
    step = np.arange(len(index), dtype=float)
    return pd.DataFrame(
        {
            "NVDA": 0.001 + np.sin(step) * 0.001,
            "MSFT": 0.0008 + np.cos(step) * 0.0008,
        },
        index=index,
    )


def sample_credit_assessment():
    """Return a credit assessment with manual input provenance."""
    inputs = CreditAnalysisInputs(
        balance_sheet=BalanceSheetInputs(
            total_debt=120.0,
            total_equity=240.0,
            current_assets=180.0,
            inventory=20.0,
            current_liabilities=90.0,
            cash_and_cash_equivalents=40.0,
            total_assets=600.0,
            total_liabilities=300.0,
            retained_earnings=90.0,
            long_term_debt=100.0,
        ),
        income_statement=IncomeStatementInputs(
            revenue=500.0,
            gross_profit=260.0,
            ebit=80.0,
            ebitda=95.0,
            interest_expense=10.0,
            net_income=55.0,
        ),
        cash_flow_statement=CashFlowInputs(operating_cash_flow=75.0),
        reporting_currency="USD",
        reporting_period="FY2026",
    )
    return calculate_credit_proxy_metrics(inputs)


def test_data_provenance_serializes_and_round_trips() -> None:
    """DataProvenance exposes stable dictionary serialization."""
    provenance = DataProvenance(
        provider="SEC",
        dataset="company_facts",
        source_labels=("us-gaap", "dei"),
        currency="usd",
        reporting_date="2026-01-31",
        transformation_steps=("fetch", "normalize"),
        cache_status={"on_disk": True},
        request={"symbol": "NVDA"},
    )

    payload = provenance.as_dict()
    restored = DataProvenance.from_dict(payload)

    assert payload["provider"] == "sec"
    assert payload["currency"] == "USD"
    assert restored is not None
    assert restored.source_labels == ("us-gaap", "dei")


def test_derivative_rate_and_calibration_objects_have_provenance() -> None:
    """Derivative diagnostics, curves, and calibration results expose provenance."""
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.04, 0.22)
    diagnostics = model.diagnostics("call")
    curve = RateCurve.from_rates({0.5: 0.04, 1.0: 0.045})
    chain = pd.DataFrame(
        [
            {
                "option_type": "call",
                "strike": 95.0,
                "implied_volatility": 0.22,
                "spot_price": 100.0,
                "maturity_years": 1.0,
            },
            {
                "option_type": "call",
                "strike": 105.0,
                "implied_volatility": 0.22,
                "spot_price": 100.0,
                "maturity_years": 1.0,
            },
        ]
    )
    calibration = BSMFlatVolCalibration(chain, objective="iv").fit()

    assert diagnostics.provenance.dataset == "derivative_diagnostics"
    assert curve.provenance.provider == "manual"
    assert calibration.provenance.dataset == "derivative_calibration"


def test_financial_credit_portfolio_and_dashboard_provenance() -> None:
    """Financial snapshots, credit assessments, portfolios, and dashboards preserve provenance."""
    income = pd.DataFrame({"2026-01-31": {"Net Income": 50.0, "Total Revenue": 500.0}})
    balance = pd.DataFrame(
        {"2026-01-31": {"Total Assets": 600.0, "Total Debt": 120.0, "Stockholders Equity": 240.0}}
    )
    cash = pd.DataFrame({"2026-01-31": {"Operating Cash Flow": 75.0}})
    snapshot = FinancialStatementSnapshot(
        "NVDA",
        "sec",
        "annual",
        pd.Timestamp("2026-03-01", tz="UTC").to_pydatetime(),
        income,
        balance,
        cash,
        {},
    )
    assessment = sample_credit_assessment()
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    backtest = allocator.backtest(weights="equal_weight", rebalance="weekly")
    dashboard = RiskDashboard(allocator, credit_assessments={"NVDA": assessment}, backtest=backtest)

    assert snapshot.provenance.provider == "sec"
    assert assessment.provenance.dataset == "credit_proxy_assessment"
    assert allocator.context.provenance.dataset == "portfolio_optimization_inputs"
    assert backtest.provenance.dataset == "portfolio_backtest"
    assert dashboard.provenance.dataset == "risk_dashboard"


def test_sec_company_facts_and_reports_carry_provenance() -> None:
    """SEC raw facts and exportable reports include provenance metadata."""
    facts = SecCompanyFacts(
        "NVDA",
        "0001045810",
        {"entityName": "NVIDIA CORP", "facts": {"us-gaap": {}, "dei": {}}},
    )
    report = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.04, 0.22).report()

    assert facts.provenance.provider == "sec"
    assert facts.provenance.request["cik"] == "0001045810"
    assert report.provenance.dataset == "option_model_report"
    assert "Provenance" in report.to_markdown()


def test_data_provenance_mappings_are_read_only() -> None:
    """DataProvenance freezes request and cache mappings after construction."""
    provenance = DataProvenance(
        provider="manual",
        dataset="unit_test",
        cache_status={"disk": {"on_disk": True}},
        request={"symbols": ["A", "B"]},
    )

    try:
        provenance.cache_status["new"] = True  # type: ignore[index]
    except TypeError:
        pass
    else:  # pragma: no cover - defensive assertion branch
        raise AssertionError("cache_status should be read-only")

    try:
        provenance.request["symbols"] += ("C",)  # type: ignore[index]
    except TypeError:
        pass
    else:  # pragma: no cover - defensive assertion branch
        raise AssertionError("nested request values should be read-only")

    payload = provenance.as_dict()
    assert payload["cache_status"] == {"disk": {"on_disk": True}}
    assert payload["request"] == {"symbols": ["A", "B"]}
