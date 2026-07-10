"""Tests for exportable AbaQuant reports."""

from __future__ import annotations

import numpy as np
import pandas as pd

from abaquant import ExportableReport, RiskDashboard
from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    IncomeStatementInputs,
    MarketEquityObservation,
    PriorPeriodInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives.models import BlackScholesMertonModel
from abaquant.portfolio import PortfolioAllocator


def sample_returns() -> pd.DataFrame:
    """Return a deterministic panel of synthetic asset returns."""
    index = pd.date_range("2024-01-01", periods=90, freq="D")
    step = np.arange(len(index), dtype=float)
    return pd.DataFrame(
        {
            "ALPHA": 0.0007 + np.sin(step / 5.0) * 0.002,
            "BETA": 0.0004 + np.cos(step / 7.0) * 0.0015,
            "GAMMA": 0.0005 + np.sin(step / 11.0) * 0.001,
        },
        index=index,
    )


def sample_credit_assessment():
    """Return a deterministic credit-proxy assessment."""
    inputs = CreditAnalysisInputs(
        balance_sheet=BalanceSheetInputs(
            total_debt=120.0,
            total_equity=240.0,
            current_assets=180.0,
            inventory=30.0,
            current_liabilities=90.0,
            cash_and_cash_equivalents=40.0,
            total_assets=620.0,
            total_liabilities=280.0,
            retained_earnings=95.0,
            long_term_debt=100.0,
        ),
        income_statement=IncomeStatementInputs(
            revenue=500.0,
            gross_profit=260.0,
            ebit=75.0,
            ebitda=95.0,
            interest_expense=12.0,
            net_income=55.0,
        ),
        cash_flow_statement=CashFlowInputs(operating_cash_flow=82.0),
        prior_period=PriorPeriodInputs(
            total_assets=590.0,
            net_income=47.0,
            long_term_debt=110.0,
            current_assets=170.0,
            current_liabilities=94.0,
            shares_outstanding=10.0,
            gross_profit=245.0,
            revenue=470.0,
        ),
        market_equity=MarketEquityObservation(market_value_equity=720.0),
        historical_series=CreditHistoricalSeries(
            earnings_history=(38.0, 45.0, 49.0, 55.0),
            leverage_history=(0.58, 0.52, 0.48, 0.43),
        ),
        reporting_currency="USD",
        reporting_period="FY2025",
    )
    return calculate_credit_proxy_metrics(inputs)


def assert_report_exports(report: ExportableReport, tmp_path) -> None:
    """Assert Markdown, HTML, and PDF exports work for a report."""
    markdown = report.to_markdown(tmp_path / "report.md")
    html = report.to_html(tmp_path / "report.html")
    pdf_path = report.to_pdf(tmp_path / "report.pdf")
    assert report.title in markdown
    assert "<!doctype html>" in html
    assert (tmp_path / "report.md").read_text(encoding="utf-8") == markdown
    assert (tmp_path / "report.html").read_text(encoding="utf-8") == html
    assert pdf_path.read_bytes().startswith(b"%PDF-")


def test_option_model_report_exports(tmp_path) -> None:
    """Option models expose exportable pricing reports."""
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.04, 0.22, 0.01)
    report = model.report(option_type="call")
    assert "Option Model Report" in report.title
    assert "extrinsic_value" in report.as_dict()["sections"][1]["metrics"]
    assert_report_exports(report, tmp_path)


def test_portfolio_allocator_and_backtest_reports_export(tmp_path) -> None:
    """Portfolio allocators and backtest results expose exportable reports."""
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    portfolio_report = allocator.report(
        backtest_kwargs={
            "weights": "equal_weight",
            "rebalance": "monthly",
            "benchmark": "equal_weight",
        }
    )
    assert portfolio_report.title == "Portfolio Report"
    assert_report_exports(portfolio_report, tmp_path / "portfolio")
    backtest = allocator.backtest(weights="inverse_volatility", rebalance="monthly", lookback=10)
    backtest_report = backtest.report()
    assert backtest_report.title == "Portfolio Backtest Report"
    assert_report_exports(backtest_report, tmp_path / "backtest")


def test_credit_and_dashboard_reports_export(tmp_path) -> None:
    """Credit assessments and risk dashboards expose exportable reports."""
    assessment = sample_credit_assessment()
    credit_report = assessment.report()
    assert credit_report.title == "Credit Proxy Report"
    assert_report_exports(credit_report, tmp_path / "credit")
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    backtest = allocator.backtest(
        weights="equal_weight", rebalance="monthly", benchmark="equal_weight"
    )
    dashboard = RiskDashboard(
        allocator,
        credit_assessments={"ALPHA": assessment},
        weights=backtest.weights_history.iloc[-1],
        backtest=backtest,
    )
    dashboard_report = dashboard.report()
    assert dashboard_report.title == "Integrated Risk Dashboard Report"
    assert_report_exports(dashboard_report, tmp_path / "dashboard")


def test_report_save_multiple_formats(tmp_path) -> None:
    """The generic report saver writes several requested formats."""
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.04, 0.22)
    outputs = model.report().save(tmp_path, "option", formats=("markdown", "html", "pdf"))
    assert outputs["markdown"].exists()
    assert outputs["html"].exists()
    assert outputs["pdf"].read_bytes().startswith(b"%PDF-")
