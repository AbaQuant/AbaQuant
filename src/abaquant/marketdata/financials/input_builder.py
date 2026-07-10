"""Build grouped credit-analysis inputs from canonical statement snapshots."""

from __future__ import annotations

from abaquant.core import DataProvenance
from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    IncomeStatementInputs,
    MarketEquityObservation,
    PriorPeriodInputs,
)

from .line_item_resolver import (
    CANONICAL_FINANCIAL_LINE_ITEMS,
    LINE_ITEM_STATEMENT,
    history_for_item,
)


def build_credit_inputs(snapshot, market_value_equity=None, reporting_currency=None):
    """Map one snapshot into grouped immutable credit-analysis inputs."""
    latest = {name: item.value for name, item in snapshot.canonical_line_items.items()}
    frames = {
        "income_statement": snapshot.income_statement,
        "balance_sheet": snapshot.balance_sheet,
        "cash_flow_statement": snapshot.cash_flow_statement,
    }

    def previous(name):
        values = history_for_item(
            frames[LINE_ITEM_STATEMENT[name]], CANONICAL_FINANCIAL_LINE_ITEMS[name]
        )
        return values[-2] if len(values) >= 2 else None

    earnings = history_for_item(
        snapshot.income_statement, CANONICAL_FINANCIAL_LINE_ITEMS["net_income"]
    )
    debt = history_for_item(snapshot.balance_sheet, CANONICAL_FINANCIAL_LINE_ITEMS["total_debt"])
    equity = history_for_item(
        snapshot.balance_sheet, CANONICAL_FINANCIAL_LINE_ITEMS["total_equity"]
    )
    leverage = tuple(d / e for d, e in zip(debt, equity, strict=False) if e > 0)
    return CreditAnalysisInputs(
        BalanceSheetInputs(
            **{name: latest.get(name) for name in BalanceSheetInputs.__dataclass_fields__}
        ),
        IncomeStatementInputs(
            **{name: latest.get(name) for name in IncomeStatementInputs.__dataclass_fields__}
        ),
        CashFlowInputs(operating_cash_flow=latest.get("operating_cash_flow")),
        PriorPeriodInputs(
            **{name: previous(name) for name in PriorPeriodInputs.__dataclass_fields__}
        ),
        MarketEquityObservation(market_value_equity),
        CreditHistoricalSeries(earnings, leverage),
        reporting_currency=reporting_currency,
        reporting_period=snapshot.period,
        provenance=DataProvenance(
            provider=snapshot.provider_name,
            dataset="credit_analysis_inputs",
            retrieved_at_utc=snapshot.retrieved_at_utc,
            cache_status=snapshot.provenance.cache_status,
            source_labels=snapshot.provenance.source_labels,
            currency=reporting_currency or snapshot.provenance.currency,
            reporting_date=snapshot.provenance.reporting_date or snapshot.period,
            transformation_steps=(
                *snapshot.provenance.transformation_steps,
                "financial statement snapshot to credit input mapping",
            ),
            request={
                "symbol": snapshot.symbol,
                "period": snapshot.period,
                "source_provenance": snapshot.provenance.as_dict(),
            },
        ),
    )
