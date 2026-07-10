"""Retrieval repository coordinating provider access and snapshot persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from abaquant.core import DataProvenance

from ..errors import MarketDataProviderError, MarketDataValidationError, OptionalDependencyError
from .cache import FinancialStatementCacheStore
from .line_item_resolver import resolve_line_items
from .models import CacheMode, FinancialPeriod, FinancialStatementSnapshot, RefreshPolicy
from .normalizer import normalize_statement_frame


class FinancialStatementRepository:
    """Retrieve bundled statements and manage memory/disk snapshot lifecycles."""

    def __init__(
        self,
        symbol,
        provider,
        cache_mode: CacheMode = "memory",
        cache_directory=None,
        session=None,
        default_max_age_days: float = 7.0,
    ):
        """Bind one symbol, provider capability, session, and cache policy."""
        self.symbol = symbol
        self.provider = provider
        self.cache_mode = cache_mode
        self.default_max_age_days = float(default_max_age_days)
        self.source_name = getattr(provider, "name", type(provider).__name__).lower()
        self._memory = session.financial_snapshots if session is not None else {}
        self._store = FinancialStatementCacheStore(
            cache_directory or "~/.cache/abaquant/financials", self.source_name
        )

    def get(
        self,
        period: FinancialPeriod = "annual",
        refresh_policy: RefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> FinancialStatementSnapshot:
        """Return a cached or freshly retrieved bundled snapshot."""
        if period not in {"annual", "quarterly"}:
            raise MarketDataValidationError("period must be 'annual' or 'quarterly'.")
        if refresh_policy not in {"cache_only", "if_missing", "if_stale", "refresh"}:
            raise MarketDataValidationError("unsupported refresh policy")
        age = self.default_max_age_days if max_age_days is None else float(max_age_days)
        cache_key = (self.source_name, period)
        cached = self._memory.get(cache_key)
        if cached is None and self.cache_mode == "disk":
            cached = self._store.load(self.symbol, period)
            if cached is not None:
                self._memory[cache_key] = cached
        if refresh_policy == "cache_only":
            if cached is None:
                raise MarketDataProviderError(
                    f"No cached {period} financial snapshot exists for {self.symbol}."
                )
            return cached
        if cached is not None and (
            refresh_policy == "if_missing"
            or (refresh_policy == "if_stale" and not self.is_stale(cached, age))
        ):
            return cached
        snapshot = self._retrieve(period, refresh_policy=refresh_policy, max_age_days=age)
        if self.cache_mode != "none":
            self._memory[cache_key] = snapshot
        if self.cache_mode == "disk":
            self._store.save(snapshot)
        return snapshot

    def _retrieve(self, period, refresh_policy="if_stale", max_age_days=None):
        """Fetch all three statements exactly once for one reporting frequency."""
        statement_kwargs = {"period": period}
        if hasattr(self.provider, "company_facts"):
            statement_kwargs["refresh_policy"] = refresh_policy
            statement_kwargs["max_age_days"] = max_age_days
        try:
            income = normalize_statement_frame(
                self.provider.income_statement(self.symbol, **statement_kwargs)
            )
            balance = normalize_statement_frame(
                self.provider.balance_sheet(self.symbol, **statement_kwargs)
            )
            cash = normalize_statement_frame(
                self.provider.cash_flow_statement(self.symbol, **statement_kwargs)
            )
        except OptionalDependencyError:
            raise
        except Exception as exc:
            raise MarketDataProviderError(
                f"Could not retrieve {period} financial statements for {self.symbol}."
            ) from exc
        if income.empty and balance.empty and cash.empty:
            raise MarketDataProviderError(
                f"No {period} financial statements found for {self.symbol}."
            )
        retrieved_at = datetime.now(UTC)
        line_items = resolve_line_items(income, balance, cash)
        source_labels = tuple(
            item.source_label for item in line_items.values() if item.source_label
        )
        reporting_dates = tuple(
            item.reporting_date for item in line_items.values() if item.reporting_date
        )
        return FinancialStatementSnapshot(
            self.symbol,
            getattr(self.provider, "name", type(self.provider).__name__),
            period,
            retrieved_at,
            income,
            balance,
            cash,
            line_items,
            DataProvenance(
                provider=getattr(self.provider, "name", type(self.provider).__name__),
                dataset="financial_statement_snapshot",
                retrieved_at_utc=retrieved_at,
                cache_status=self.status(period),
                source_labels=source_labels,
                reporting_date=max(reporting_dates) if reporting_dates else period,
                transformation_steps=(
                    "provider statement retrieval",
                    "statement normalization",
                    "canonical line-item resolution",
                ),
                request={
                    "symbol": self.symbol,
                    "period": period,
                    "source": self.source_name,
                    "refresh_policy": refresh_policy,
                    "cache_mode": self.cache_mode,
                },
            ),
        )

    @staticmethod
    def is_stale(snapshot, max_age_days):
        """Return whether retrieval age exceeds the configured threshold."""
        timestamp = snapshot.retrieved_at_utc
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return (datetime.now(UTC) - timestamp).total_seconds() / 86400.0 > max_age_days

    def status(self, period):
        """Describe local snapshot availability without provider access."""
        cache_key = (self.source_name, period)
        memory = self._memory.get(cache_key)
        disk = self._store.load(self.symbol, period) if self.cache_mode == "disk" else None
        snapshot = memory or disk
        return {
            "cache_mode": self.cache_mode,
            "in_memory": memory is not None,
            "on_disk": disk is not None,
            "retrieved_at_utc": None if snapshot is None else snapshot.retrieved_at_utc.isoformat(),
            "is_stale": None
            if snapshot is None
            else self.is_stale(snapshot, self.default_max_age_days),
        }

    def clear(self, period=None):
        """Remove selected memory and disk snapshots."""
        periods = ("annual", "quarterly") if period is None else (period,)
        for item in periods:
            self._memory.pop((self.source_name, item), None)
            self._store.remove(self.symbol, item)
