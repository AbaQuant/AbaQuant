"""Small public facade for cached financial statement retrieval."""

from __future__ import annotations

from ..errors import MarketDataValidationError
from .input_builder import build_credit_inputs
from .line_item_resolver import CANONICAL_FINANCIAL_LINE_ITEMS
from .models import (
    FinancialPeriod,
    RefreshPolicy,
)
from .repository import FinancialStatementRepository


class FinancialStatements:
    """Public financial-statement facade with source-aware repositories.

    The facade keeps user-facing calls stable while delegating retrieval and
    caching to one repository per configured source. A ticker can therefore use
    Yahoo for quotes and SEC XBRL for fundamentals without mixing provider
    responsibilities.
    """

    def __init__(
        self,
        ticker,
        repository: FinancialStatementRepository | None = None,
        *,
        repositories: dict[str, FinancialStatementRepository] | None = None,
        default_source: str | None = None,
    ):
        """Attach one or more statement repositories to the presentation facade."""
        self.ticker = ticker
        if repositories is None:
            if repository is None:
                raise MarketDataValidationError("a financial statement repository is required")
            source_name = getattr(repository.provider, "name", "default").lower()
            repositories = {source_name: repository}
        self._repositories = {str(name).lower(): repo for name, repo in repositories.items()}
        self._default_source = (default_source or next(iter(self._repositories))).lower()

    def _repository_for(self, source: str | None = None) -> FinancialStatementRepository:
        """Return the repository configured for a financial-statement source."""
        source_name = self._default_source if source is None else str(source).lower()
        try:
            return self._repositories[source_name]
        except KeyError as exc:
            available = ", ".join(sorted(self._repositories))
            raise MarketDataValidationError(
                f"Unsupported financial statement source {source_name!r}; available sources: {available}."
            ) from exc

    def snapshot(
        self,
        *,
        period: FinancialPeriod = "annual",
        refresh_policy: RefreshPolicy = "if_stale",
        max_age_days: float | None = None,
        source: str | None = None,
    ):
        """Return one repository-managed statement snapshot."""
        return self._repository_for(source).get(period, refresh_policy, max_age_days)

    def refresh(
        self, *, period: FinancialPeriod = "annual", force: bool = False, source: str | None = None
    ):
        """Refresh a period when forced or when its cache is stale."""
        return self.snapshot(
            period=period, source=source, refresh_policy="refresh" if force else "if_stale"
        )

    def cache_status(self, *, period="annual", source: str | None = None):
        """Describe cache availability without a provider request."""
        return self._repository_for(source).status(period)

    def clear_cache(self, *, period=None, source: str | None = None):
        """Remove selected cache entries from memory and disk."""
        self._repository_for(source).clear(period)

    def sec_company_facts(
        self,
        *,
        source: str = "sec",
        refresh_policy: RefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ):
        """Return raw SEC Company Facts with attached provenance metadata.

        Returns
        -------
        SecCompanyFacts
            Immutable wrapper exposing ``payload`` and ``provenance``.
        """
        provider = self._repository_for(source).provider
        if not hasattr(provider, "company_facts"):
            raise MarketDataValidationError(
                f"Configured financial source {source!r} does not expose SEC Company Facts."
            )
        return provider.company_facts(
            self.ticker.symbol, refresh_policy=refresh_policy, max_age_days=max_age_days
        )

    def sec_facts(
        self,
        *,
        source: str = "sec",
        refresh_policy: RefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ):
        """Return raw SEC Company Facts JSON for the configured SEC source.

        The SEC provider honors the same refresh policies used by normalized
        statement snapshots. With disk caching enabled, repeated Python
        sessions can reuse cached Company Facts payloads without a new SEC
        request.
        """
        provider = self._repository_for(source).provider
        if not hasattr(provider, "sec_facts"):
            raise MarketDataValidationError(
                f"Configured financial source {source!r} does not expose SEC Company Facts."
            )
        return dict(
            self.sec_company_facts(
                source=source, refresh_policy=refresh_policy, max_age_days=max_age_days
            ).payload
        )

    def sec_cache_status(self, *, source: str = "sec", max_age_days: float | None = None):
        """Describe SEC raw-data cache availability without a provider request."""
        provider = self._repository_for(source).provider
        if not hasattr(provider, "cache_status"):
            raise MarketDataValidationError(
                f"Configured financial source {source!r} does not expose SEC raw-data cache status."
            )
        return provider.cache_status(self.ticker.symbol, max_age_days=max_age_days)

    def clear_sec_cache(self, *, source: str = "sec"):
        """Clear SEC raw Company Facts cache entries for this ticker when supported."""
        provider = self._repository_for(source).provider
        if not hasattr(provider, "clear_cache"):
            raise MarketDataValidationError(
                f"Configured financial source {source!r} does not expose SEC raw-data cache clearing."
            )
        provider.clear_cache(self.ticker.symbol)

    def income_statement(self, *, period="annual", **kwargs):
        """Return a defensive copy of the normalized income statement."""
        return self.snapshot(period=period, **kwargs).income_statement

    def balance_sheet(self, *, period="annual", **kwargs):
        """Return a defensive copy of the normalized balance sheet."""
        return self.snapshot(period=period, **kwargs).balance_sheet

    def cash_flow_statement(self, *, period="annual", **kwargs):
        """Return a defensive copy of the normalized cash-flow statement."""
        return self.snapshot(period=period, **kwargs).cash_flow_statement

    def get_line_item_details(self, canonical_name, *, period="annual", **kwargs):
        """Return a resolved line item with provider-label provenance."""
        if canonical_name not in CANONICAL_FINANCIAL_LINE_ITEMS:
            raise MarketDataValidationError(
                f"Unsupported canonical financial line item: {canonical_name!r}."
            )
        return self.snapshot(period=period, **kwargs).canonical_line_items[canonical_name]

    def get_line_item(self, canonical_name, *, period="annual", **kwargs):
        """Return a resolved scalar value or ``None`` when unavailable."""
        return self.get_line_item_details(canonical_name, period=period, **kwargs).value

    def credit_inputs(self, *, period="annual", **kwargs):
        """Build grouped credit-analysis inputs from one snapshot."""
        snapshot = self.snapshot(period=period, **kwargs)
        try:
            market_cap = self.ticker.provider.info(self.ticker.symbol).get("marketCap")
        except Exception:
            market_cap = None
        return build_credit_inputs(snapshot, market_cap)

    def visualize(
        self,
        *,
        statement: str = "balance_sheet",
        period: FinancialPeriod = "annual",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
        **kwargs,
    ):
        """Return a figure for the latest column of one cached statement table."""
        from abaquant.visualization import visualize_financial_snapshot

        return visualize_financial_snapshot(
            self.snapshot(period=period, **kwargs),
            statement=statement,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )

    def total_debt(self, *, period="annual", **kwargs):
        """Return the latest resolved `total_debt` statement value."""
        value = self.get_line_item("total_debt", period=period, **kwargs)
        return abs(value) if "total_debt" == "interest_expense" and value is not None else value

    def total_equity(self, *, period="annual", **kwargs):
        """Return the latest resolved `total_equity` statement value."""
        value = self.get_line_item("total_equity", period=period, **kwargs)
        return abs(value) if "total_equity" == "interest_expense" and value is not None else value

    def current_assets(self, *, period="annual", **kwargs):
        """Return the latest resolved `current_assets` statement value."""
        value = self.get_line_item("current_assets", period=period, **kwargs)
        return abs(value) if "current_assets" == "interest_expense" and value is not None else value

    def inventory(self, *, period="annual", **kwargs):
        """Return the latest resolved `inventory` statement value."""
        value = self.get_line_item("inventory", period=period, **kwargs)
        return abs(value) if "inventory" == "interest_expense" and value is not None else value

    def current_liabilities(self, *, period="annual", **kwargs):
        """Return the latest resolved `current_liabilities` statement value."""
        value = self.get_line_item("current_liabilities", period=period, **kwargs)
        return (
            abs(value)
            if "current_liabilities" == "interest_expense" and value is not None
            else value
        )

    def cash_and_cash_equivalents(self, *, period="annual", **kwargs):
        """Return the latest resolved `cash_and_cash_equivalents` statement value."""
        value = self.get_line_item("cash_and_cash_equivalents", period=period, **kwargs)
        return (
            abs(value)
            if "cash_and_cash_equivalents" == "interest_expense" and value is not None
            else value
        )

    def ebit(self, *, period="annual", **kwargs):
        """Return the latest resolved `ebit` statement value."""
        value = self.get_line_item("ebit", period=period, **kwargs)
        return abs(value) if "ebit" == "interest_expense" and value is not None else value

    def ebitda(self, *, period="annual", **kwargs):
        """Return the latest resolved `ebitda` statement value."""
        value = self.get_line_item("ebitda", period=period, **kwargs)
        return abs(value) if "ebitda" == "interest_expense" and value is not None else value

    def interest_expense(self, *, period="annual", **kwargs):
        """Return the latest resolved `interest_expense` statement value."""
        value = self.get_line_item("interest_expense", period=period, **kwargs)
        return (
            abs(value) if "interest_expense" == "interest_expense" and value is not None else value
        )

    def operating_cash_flow(self, *, period="annual", **kwargs):
        """Return the latest resolved `operating_cash_flow` statement value."""
        value = self.get_line_item("operating_cash_flow", period=period, **kwargs)
        return (
            abs(value)
            if "operating_cash_flow" == "interest_expense" and value is not None
            else value
        )

    def total_assets(self, *, period="annual", **kwargs):
        """Return the latest resolved `total_assets` statement value."""
        value = self.get_line_item("total_assets", period=period, **kwargs)
        return abs(value) if "total_assets" == "interest_expense" and value is not None else value

    def total_liabilities(self, *, period="annual", **kwargs):
        """Return the latest resolved `total_liabilities` statement value."""
        value = self.get_line_item("total_liabilities", period=period, **kwargs)
        return (
            abs(value) if "total_liabilities" == "interest_expense" and value is not None else value
        )

    def retained_earnings(self, *, period="annual", **kwargs):
        """Return the latest resolved `retained_earnings` statement value."""
        value = self.get_line_item("retained_earnings", period=period, **kwargs)
        return (
            abs(value) if "retained_earnings" == "interest_expense" and value is not None else value
        )

    def revenue(self, *, period="annual", **kwargs):
        """Return the latest resolved `revenue` statement value."""
        value = self.get_line_item("revenue", period=period, **kwargs)
        return abs(value) if "revenue" == "interest_expense" and value is not None else value

    def net_income(self, *, period="annual", **kwargs):
        """Return the latest resolved `net_income` statement value."""
        value = self.get_line_item("net_income", period=period, **kwargs)
        return abs(value) if "net_income" == "interest_expense" and value is not None else value

    def long_term_debt(self, *, period="annual", **kwargs):
        """Return the latest resolved `long_term_debt` statement value."""
        value = self.get_line_item("long_term_debt", period=period, **kwargs)
        return abs(value) if "long_term_debt" == "interest_expense" and value is not None else value

    def shares_outstanding(self, *, period="annual", **kwargs):
        """Return the latest resolved `shares_outstanding` statement value."""
        value = self.get_line_item("shares_outstanding", period=period, **kwargs)
        return (
            abs(value)
            if "shares_outstanding" == "interest_expense" and value is not None
            else value
        )

    def gross_profit(self, *, period="annual", **kwargs):
        """Return the latest resolved `gross_profit` statement value."""
        value = self.get_line_item("gross_profit", period=period, **kwargs)
        return abs(value) if "gross_profit" == "interest_expense" and value is not None else value
