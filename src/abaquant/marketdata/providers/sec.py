"""SEC EDGAR/XBRL financial-statement provider with persistent JSON caching.

Purpose
-------
This module adapts the official SEC EDGAR JSON APIs into AbaQuant's
financial-statement provider interface. It resolves ticker symbols to CIKs,
retrieves Company Facts data, caches raw SEC JSON payloads, and converts
selected US-GAAP facts into canonical line-item labels consumed by the
financial-statement and credit-proxy pipeline.

Conventions
-----------
The provider uses the SEC ``company_tickers.json`` file for symbol-to-CIK
resolution and the ``companyfacts`` endpoint for extracted XBRL data. Statement
DataFrames are indexed by AbaQuant's provider-neutral line-item labels, such as
``"Total Assets"`` and ``"Net Income"``. Columns are SEC ``end`` dates sorted
newest first. Disk cache entries are versioned and checksum-protected.

Scope and limitations
---------------------
Only company-level, non-custom taxonomy facts exposed through the SEC Company
Facts API are used. The provider does not parse individual filings, footnotes,
custom company extensions, or management-adjusted non-GAAP measures. Missing
facts remain missing rather than being imputed.

References
----------
[1] U.S. Securities and Exchange Commission, EDGAR Application Programming
    Interfaces and data.sec.gov Company Facts API documentation.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Literal

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance

from ..errors import MarketDataProviderError, MarketDataValidationError
from .financial_statements import FinancialPeriod

SecStatementType = Literal["income_statement", "balance_sheet", "cash_flow_statement"]
SecCacheMode = Literal["none", "memory", "disk"]
SecRefreshPolicy = Literal["cache_only", "if_missing", "if_stale", "refresh"]

_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
_DEFAULT_USER_AGENT = "abaquant/1.0.0rc1 research@example.com"

ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}
QUARTERLY_FORMS = {"10-Q", "10-Q/A"}

SEC_BALANCE_SHEET_TAGS: dict[str, tuple[str, ...]] = {
    "Stockholders Equity": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "Current Assets": ("AssetsCurrent",),
    "Inventory": ("InventoryNet", "InventoryFinishedGoodsNetOfReserves"),
    "Current Liabilities": ("LiabilitiesCurrent",),
    "Cash And Cash Equivalents": (
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ),
    "Total Assets": ("Assets",),
    "Total Liabilities": ("Liabilities", "LiabilitiesAndStockholdersEquity"),
    "Retained Earnings": ("RetainedEarningsAccumulatedDeficit",),
    "Long Term Debt": (
        "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        "LongTermDebtNoncurrent",
        "LongTermDebt",
    ),
    "Ordinary Shares Number": (
        "EntityCommonStockSharesOutstanding",
        "CommonStocksIncludingAdditionalPaidInCapital",
    ),
}
SEC_INCOME_STATEMENT_TAGS: dict[str, tuple[str, ...]] = {
    "Total Revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ),
    "Gross Profit": ("GrossProfit",),
    "Operating Income": ("OperatingIncomeLoss",),
    "Interest Expense": ("InterestExpenseNonOperating", "InterestExpense"),
    "Net Income": ("NetIncomeLoss", "ProfitLoss"),
    "EBITDA": ("EarningsBeforeInterestTaxesDepreciationAmortization",),
}
SEC_CASH_FLOW_TAGS: dict[str, tuple[str, ...]] = {
    "Operating Cash Flow": ("NetCashProvidedByUsedInOperatingActivities",),
}
SHORT_DEBT_TAGS: tuple[str, ...] = (
    "ShortTermBorrowings",
    "ShortTermDebt",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtCurrent",
)
LONG_DEBT_TAGS: tuple[str, ...] = (
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
)
TOTAL_DEBT_TAGS: tuple[str, ...] = (
    "DebtAndFinanceLeaseObligations",
    "Debt",
)


@dataclass(frozen=True)
class SecCompanyFacts:
    """Raw SEC Company Facts payload with resolved CIK provenance.

    Attributes
    ----------
    symbol : str
        Normalized ticker symbol used for CIK resolution.
    cik : str
        Ten-digit Central Index Key with leading zeros.
    payload : dict[str, Any]
        JSON payload returned by the SEC Company Facts API.
    retrieved_at_utc : datetime | None, default=None
        Retrieval or cache-write timestamp. ``None`` is allowed for deterministic
        in-memory fixtures that do not model retrieval time.
    """

    symbol: str
    cik: str
    payload: dict[str, Any]
    retrieved_at_utc: datetime | None = None
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach raw SEC Company Facts provenance when omitted."""
        if self.provenance is None:
            entity_name = self.payload.get("entityName") if isinstance(self.payload, dict) else None
            facts = self.payload.get("facts", {}) if isinstance(self.payload, dict) else {}
            source_labels = tuple(facts.keys()) if isinstance(facts, dict) else ()
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="sec",
                    dataset="sec_company_facts",
                    retrieved_at_utc=self.retrieved_at_utc,
                    source_labels=source_labels,
                    reporting_date=None,
                    transformation_steps=(
                        "ticker to CIK resolution",
                        "SEC Company Facts retrieval",
                    ),
                    request={"symbol": self.symbol, "cik": self.cik, "entity_name": entity_name},
                ),
            )


class SecJsonCacheStore:
    """Versioned, checksum-validated disk cache for SEC JSON payloads.

    The store persists the ticker-to-CIK mapping and per-company Company Facts
    payloads under one cache directory. Invalid, stale, or corrupt files are
    treated as cache misses so callers can safely fall back to a fresh SEC
    request.
    """

    schema_version = 1

    def __init__(self, directory: str | Path | None = None) -> None:
        """Configure the root directory for SEC raw JSON cache files."""
        self.directory = Path(directory or "~/.cache/abaquant/sec").expanduser()

    @property
    def ticker_mapping_path(self) -> Path:
        """Return the cache path for the SEC ticker-to-CIK mapping."""
        return self.directory / "company_tickers.json"

    def company_facts_path(self, symbol: str, cik: str) -> Path:
        """Return the cache path for one ticker's Company Facts payload."""
        return (
            self.directory
            / "company_facts"
            / f"{_normalize_symbol(symbol)}_{_format_cik(cik)}.json"
        )

    def load_ticker_mapping(self, *, max_age_days: float | None = None) -> dict[str, str] | None:
        """Load the cached ticker-to-CIK mapping when present and fresh."""
        payload = self._load_payload(self.ticker_mapping_path, max_age_days=max_age_days)
        if payload is None:
            return None
        mapping = payload.get("mapping")
        if not isinstance(mapping, dict):
            return None
        return {_normalize_symbol(key): _format_cik(value) for key, value in mapping.items()}

    def save_ticker_mapping(self, mapping: dict[str, str]) -> None:
        """Persist a normalized ticker-to-CIK mapping atomically."""
        normalized = {_normalize_symbol(key): _format_cik(value) for key, value in mapping.items()}
        self._save_payload(
            self.ticker_mapping_path, {"kind": "ticker_mapping", "mapping": normalized}
        )

    def load_company_facts(
        self, symbol: str, cik: str, *, max_age_days: float | None = None
    ) -> SecCompanyFacts | None:
        """Load a cached Company Facts payload when present and fresh."""
        clean_symbol = _normalize_symbol(symbol)
        clean_cik = _format_cik(cik)
        payload = self._load_payload(
            self.company_facts_path(clean_symbol, clean_cik), max_age_days=max_age_days
        )
        if payload is None:
            return None
        if payload.get("symbol") != clean_symbol or payload.get("cik") != clean_cik:
            return None
        facts = payload.get("company_facts")
        if not isinstance(facts, dict):
            return None
        retrieved_at = _parse_datetime(payload.get("retrieved_at_utc"))
        return SecCompanyFacts(
            clean_symbol,
            clean_cik,
            facts,
            retrieved_at,
            DataProvenance.from_dict(payload.get("provenance")),
        )

    def save_company_facts(self, facts: SecCompanyFacts) -> None:
        """Persist one Company Facts payload atomically."""
        self._save_payload(
            self.company_facts_path(facts.symbol, facts.cik),
            {
                "kind": "company_facts",
                "symbol": facts.symbol,
                "cik": facts.cik,
                "company_facts": facts.payload,
                "provenance": facts.provenance.as_dict(),
            },
        )

    def ticker_mapping_status(self, *, max_age_days: float | None = None) -> dict[str, object]:
        """Return local ticker-mapping cache availability without network access."""
        return self._status(self.ticker_mapping_path, max_age_days=max_age_days)

    def company_facts_status(
        self, symbol: str, cik: str | None = None, *, max_age_days: float | None = None
    ) -> dict[str, object]:
        """Return local Company Facts cache availability without network access."""
        clean_symbol = _normalize_symbol(symbol)
        if cik is None:
            pattern = f"{clean_symbol}_*.json"
            directory = self.directory / "company_facts"
            matches = sorted(directory.glob(pattern)) if directory.exists() else []
            path = matches[0] if matches else directory / f"{clean_symbol}_unknown.json"
        else:
            path = self.company_facts_path(clean_symbol, cik)
        return self._status(path, max_age_days=max_age_days)

    def remove_company_facts(self, symbol: str, cik: str | None = None) -> None:
        """Remove cached Company Facts payloads for one symbol."""
        clean_symbol = _normalize_symbol(symbol)
        paths: list[Path]
        if cik is None:
            directory = self.directory / "company_facts"
            paths = list(directory.glob(f"{clean_symbol}_*.json")) if directory.exists() else []
        else:
            paths = [self.company_facts_path(clean_symbol, cik)]
        for path in paths:
            if path.exists():
                path.unlink()

    def _load_payload(
        self, path: Path, *, max_age_days: float | None = None
    ) -> dict[str, Any] | None:
        """Load and validate one checksum-protected SEC cache payload."""
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
            checksum = raw_payload.pop("checksum")
            serialized = json.dumps(
                raw_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            if hashlib.sha256(serialized.encode()).hexdigest() != checksum:
                return None
            if raw_payload.get("schema_version") != self.schema_version:
                return None
            retrieved_at = _parse_datetime(raw_payload.get("retrieved_at_utc"))
            if max_age_days is not None and _is_stale(retrieved_at, max_age_days):
                return None
            return raw_payload
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _save_payload(self, path: Path, data: dict[str, Any]) -> None:
        """Write one SEC cache payload through a temporary file and atomic rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            **data,
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        payload["checksum"] = hashlib.sha256(serialized.encode()).hexdigest()
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        os.replace(temporary_path, path)

    def _status(self, path: Path, *, max_age_days: float | None = None) -> dict[str, object]:
        """Return cache status for one path while treating corruption as unavailable."""
        payload = self._load_payload(path, max_age_days=None)
        retrieved_at = None if payload is None else _parse_datetime(payload.get("retrieved_at_utc"))
        exists = payload is not None
        return {
            "on_disk": exists,
            "path": str(path),
            "retrieved_at_utc": None if retrieved_at is None else retrieved_at.isoformat(),
            "is_stale": None
            if retrieved_at is None or max_age_days is None
            else _is_stale(retrieved_at, max_age_days),
        }


class SecXbrlProvider:
    """Financial-statement provider backed by SEC EDGAR Company Facts.

    Parameters
    ----------
    user_agent : str | None, default=None
        Declared SEC request user agent. If omitted, the provider reads
        ``ABAQUANT_SEC_USER_AGENT`` and then falls back to a generic AbaQuant
        research user agent.
    cik_by_symbol : dict[str, str] | None, default=None
        Optional preloaded symbol-to-CIK mapping used by deterministic tests or
        users who want to avoid the ticker lookup request.
    timeout_seconds : float, default=30.0
        Request timeout for SEC JSON retrieval.
    min_request_interval_seconds : float, default=0.11
        Minimum spacing between SEC requests. The default is slightly below the
        SEC fair-access maximum of 10 requests per second.
    cache_mode : {'none', 'memory', 'disk'}, default='memory'
        Raw SEC JSON cache policy. ``'disk'`` persists ticker mappings and
        Company Facts payloads across Python sessions.
    cache_directory : str | Path | None, default=None
        Root directory for persistent SEC raw JSON cache files. If omitted,
        ``~/.cache/abaquant/sec`` is used.
    default_max_age_days : float, default=7.0
        Default freshness threshold for cached SEC JSON payloads.
    """

    name = "sec"

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        cik_by_symbol: dict[str, str] | None = None,
        timeout_seconds: float = 30.0,
        min_request_interval_seconds: float = 0.11,
        cache_mode: SecCacheMode = "memory",
        cache_directory: str | Path | None = None,
        default_max_age_days: float = 7.0,
    ) -> None:
        """Create a provider without requesting SEC data."""
        if cache_mode not in {"none", "memory", "disk"}:
            raise MarketDataValidationError("cache_mode must be 'none', 'memory', or 'disk'.")
        self.user_agent = user_agent or os.environ.get(
            "ABAQUANT_SEC_USER_AGENT", _DEFAULT_USER_AGENT
        )
        self.timeout_seconds = float(timeout_seconds)
        self.min_request_interval_seconds = float(min_request_interval_seconds)
        self.cache_mode = cache_mode
        self.default_max_age_days = float(default_max_age_days)
        self._last_request_started_at: float | None = None
        self._cik_by_symbol = {
            _normalize_symbol(symbol): _format_cik(cik)
            for symbol, cik in (cik_by_symbol or {}).items()
        }
        self._company_facts_cache: dict[str, SecCompanyFacts] = {}
        self._store = SecJsonCacheStore(cache_directory)

    def company_facts(
        self,
        symbol: str,
        *,
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> SecCompanyFacts:
        """Return the SEC Company Facts payload for one ticker symbol.

        The method uses memory and optional disk cache before requesting the SEC
        endpoint. ``refresh_policy='cache_only'`` never performs a network
        request and fails if no eligible cached payload exists.
        """
        if refresh_policy not in {"cache_only", "if_missing", "if_stale", "refresh"}:
            raise MarketDataValidationError("unsupported SEC refresh policy")
        clean_symbol = _normalize_symbol(symbol)
        age = self.default_max_age_days if max_age_days is None else float(max_age_days)
        cached = self._company_facts_cache.get(clean_symbol)
        if cached is None and self.cache_mode == "disk":
            try:
                cached_cik = self.cik_for_symbol(clean_symbol, refresh_policy="cache_only")
            except MarketDataProviderError:
                cached_cik = None
            if cached_cik is not None:
                cached = self._store.load_company_facts(clean_symbol, cached_cik, max_age_days=None)
                if cached is not None and self.cache_mode != "none":
                    self._company_facts_cache[clean_symbol] = cached
        if refresh_policy == "cache_only":
            if cached is None:
                raise MarketDataProviderError(
                    f"No cached SEC Company Facts payload exists for {clean_symbol}."
                )
            return cached
        if cached is not None and (
            refresh_policy == "if_missing"
            or (refresh_policy == "if_stale" and not _is_stale(cached.retrieved_at_utc, age))
        ):
            return cached
        cik = self.cik_for_symbol(clean_symbol, refresh_policy="if_stale", max_age_days=age)
        payload = self._request_json(_SEC_COMPANY_FACTS_URL.format(cik=cik))
        retrieved_at = datetime.now(UTC)
        facts = SecCompanyFacts(
            clean_symbol,
            cik,
            payload,
            retrieved_at,
            DataProvenance(
                provider="sec",
                dataset="sec_company_facts",
                retrieved_at_utc=retrieved_at,
                cache_status=self.cache_status(clean_symbol, max_age_days=age),
                source_labels=tuple((payload.get("facts") or {}).keys())
                if isinstance(payload.get("facts"), dict)
                else (),
                transformation_steps=("ticker to CIK resolution", "SEC Company Facts retrieval"),
                request={
                    "symbol": clean_symbol,
                    "cik": cik,
                    "refresh_policy": refresh_policy,
                    "cache_mode": self.cache_mode,
                    "entity_name": payload.get("entityName"),
                },
            ),
        )
        if self.cache_mode != "none":
            self._company_facts_cache[clean_symbol] = facts
        if self.cache_mode == "disk":
            self._store.save_company_facts(facts)
        return facts

    def sec_facts(
        self,
        symbol: str,
        *,
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> dict[str, Any]:
        """Return the raw SEC Company Facts JSON payload for one symbol."""
        return dict(
            self.company_facts(
                symbol, refresh_policy=refresh_policy, max_age_days=max_age_days
            ).payload
        )

    def cik_for_symbol(
        self,
        symbol: str,
        *,
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> str:
        """Resolve a ticker symbol to a ten-digit SEC CIK using cache when possible."""
        if refresh_policy not in {"cache_only", "if_missing", "if_stale", "refresh"}:
            raise MarketDataValidationError("unsupported SEC refresh policy")
        clean_symbol = _normalize_symbol(symbol)
        age = self.default_max_age_days if max_age_days is None else float(max_age_days)
        cached = self._cik_by_symbol.get(clean_symbol)
        if cached is not None and refresh_policy in {"cache_only", "if_missing"}:
            return cached
        if self.cache_mode == "disk" and refresh_policy != "refresh":
            mapping = self._store.load_ticker_mapping(max_age_days=None)
            if mapping:
                self._cik_by_symbol.update(mapping)
                cached = self._cik_by_symbol.get(clean_symbol)
                status = self._store.ticker_mapping_status(max_age_days=age)
                if cached is not None and (
                    refresh_policy == "cache_only"
                    or refresh_policy == "if_missing"
                    or (refresh_policy == "if_stale" and status["is_stale"] is False)
                ):
                    return cached
        if refresh_policy == "cache_only":
            raise MarketDataProviderError(
                f"No cached SEC CIK mapping exists for ticker symbol {clean_symbol!r}."
            )
        raw = self._request_json(_SEC_TICKERS_URL)
        mapping: dict[str, str] = {}
        for record in raw.values():
            try:
                ticker = _normalize_symbol(record.get("ticker", ""))
                cik_value = _format_cik(record.get("cik_str"))
            except MarketDataValidationError:
                continue
            mapping[ticker] = cik_value
        self._cik_by_symbol.update(mapping)
        if self.cache_mode == "disk":
            self._store.save_ticker_mapping(mapping)
        try:
            return self._cik_by_symbol[clean_symbol]
        except KeyError as exc:
            raise MarketDataProviderError(
                f"Could not resolve SEC CIK for ticker symbol {clean_symbol!r}."
            ) from exc

    def income_statement(
        self,
        symbol: str,
        *,
        period: FinancialPeriod = "annual",
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> pd.DataFrame:
        """Return a normalized SEC-derived income-statement table."""
        return _statement_from_company_facts(
            self.company_facts(
                symbol, refresh_policy=refresh_policy, max_age_days=max_age_days
            ).payload,
            statement_type="income_statement",
            period=period,
        )

    def balance_sheet(
        self,
        symbol: str,
        *,
        period: FinancialPeriod = "annual",
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> pd.DataFrame:
        """Return a normalized SEC-derived balance-sheet table."""
        return _statement_from_company_facts(
            self.company_facts(
                symbol, refresh_policy=refresh_policy, max_age_days=max_age_days
            ).payload,
            statement_type="balance_sheet",
            period=period,
        )

    def cash_flow_statement(
        self,
        symbol: str,
        *,
        period: FinancialPeriod = "annual",
        refresh_policy: SecRefreshPolicy = "if_stale",
        max_age_days: float | None = None,
    ) -> pd.DataFrame:
        """Return a normalized SEC-derived cash-flow statement table."""
        return _statement_from_company_facts(
            self.company_facts(
                symbol, refresh_policy=refresh_policy, max_age_days=max_age_days
            ).payload,
            statement_type="cash_flow_statement",
            period=period,
        )

    def cache_status(self, symbol: str, *, max_age_days: float | None = None) -> dict[str, object]:
        """Describe SEC raw-data cache availability without provider access."""
        clean_symbol = _normalize_symbol(symbol)
        age = self.default_max_age_days if max_age_days is None else float(max_age_days)
        cik = self._cik_by_symbol.get(clean_symbol)
        try:
            if cik is None and self.cache_mode == "disk":
                cik = self.cik_for_symbol(clean_symbol, refresh_policy="cache_only")
        except MarketDataProviderError:
            cik = None
        facts = self._company_facts_cache.get(clean_symbol)
        return {
            "cache_mode": self.cache_mode,
            "ticker_mapping": self._store.ticker_mapping_status(max_age_days=age)
            if self.cache_mode == "disk"
            else {"on_disk": False, "is_stale": None},
            "company_facts": self._store.company_facts_status(clean_symbol, cik, max_age_days=age)
            if self.cache_mode == "disk"
            else {"on_disk": False, "is_stale": None},
            "in_memory": facts is not None,
            "cik": cik,
        }

    def clear_cache(self, symbol: str | None = None) -> None:
        """Clear memory and disk Company Facts cache entries for one or all symbols."""
        if symbol is None:
            self._company_facts_cache.clear()
            return
        clean_symbol = _normalize_symbol(symbol)
        self._company_facts_cache.pop(clean_symbol, None)
        if self.cache_mode == "disk":
            cik = self._cik_by_symbol.get(clean_symbol)
            self._store.remove_company_facts(clean_symbol, cik)

    def _request_json(self, url: str) -> dict[str, Any]:
        """Retrieve one SEC JSON document using declared fair-access headers."""
        self._respect_rate_limit()
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                body = _decode_sec_response_body(
                    response.read(),
                    content_encoding=response.headers.get("Content-Encoding"),
                    charset=charset,
                )
        except urllib.error.HTTPError as exc:
            raise MarketDataProviderError(
                f"SEC request failed with HTTP {exc.code} for {url}."
            ) from exc
        except urllib.error.URLError as exc:
            raise MarketDataProviderError(f"SEC request failed for {url}.") from exc
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MarketDataProviderError(f"SEC response was not valid JSON for {url}.") from exc
        if not isinstance(parsed, dict):
            raise MarketDataProviderError(f"SEC response did not contain a JSON object for {url}.")
        return parsed

    def _respect_rate_limit(self) -> None:
        """Space requests so provider use remains below the SEC fair-access limit."""
        now = monotonic()
        if self._last_request_started_at is not None:
            elapsed = now - self._last_request_started_at
            if elapsed < self.min_request_interval_seconds:
                sleep(self.min_request_interval_seconds - elapsed)
        self._last_request_started_at = monotonic()


def _statement_from_company_facts(
    company_facts: dict[str, Any], *, statement_type: SecStatementType, period: FinancialPeriod
) -> pd.DataFrame:
    """Build one canonical statement DataFrame from a Company Facts payload."""
    if period not in {"annual", "quarterly"}:
        raise MarketDataValidationError("period must be 'annual' or 'quarterly'.")
    if statement_type == "income_statement":
        tag_map = SEC_INCOME_STATEMENT_TAGS
    elif statement_type == "balance_sheet":
        tag_map = SEC_BALANCE_SHEET_TAGS
    elif statement_type == "cash_flow_statement":
        tag_map = SEC_CASH_FLOW_TAGS
    else:
        raise MarketDataValidationError(f"Unsupported SEC statement type: {statement_type!r}.")

    rows: dict[str, dict[str, float]] = {}
    for row_label, tag_candidates in tag_map.items():
        rows[row_label] = _series_for_tags(company_facts, tag_candidates, period=period)
    if statement_type == "balance_sheet":
        rows["Total Debt"] = _total_debt_series(company_facts, period=period)
    return _rows_to_frame(rows)


def _series_for_tags(
    company_facts: dict[str, Any], tag_candidates: tuple[str, ...], *, period: FinancialPeriod
) -> dict[str, float]:
    """Return the first available finite SEC fact series for preferred tags."""
    for tag in tag_candidates:
        series = _series_for_tag(company_facts, tag, period=period)
        if series:
            return series
    return {}


def _series_for_tag(
    company_facts: dict[str, Any], tag: str, *, period: FinancialPeriod
) -> dict[str, float]:
    """Collect latest-filed facts for one US-GAAP or DEI tag by reporting end date."""
    concept = _concept(company_facts, tag)
    if not concept:
        return {}
    preferred_units = _preferred_units(tag)
    chosen: dict[str, tuple[str, float]] = {}
    for unit in preferred_units:
        facts = concept.get("units", {}).get(unit, [])
        if facts:
            break
    else:
        facts = [fact for unit_facts in concept.get("units", {}).values() for fact in unit_facts]
    for fact in facts:
        if not _matches_period(fact, period):
            continue
        end = fact.get("end")
        value = fact.get("val")
        filed = str(fact.get("filed", ""))
        if not end or not _is_finite_number(value):
            continue
        current = chosen.get(str(end))
        if current is None or filed >= current[0]:
            chosen[str(end)] = (filed, float(value))
    return {end: value for end, (_, value) in chosen.items()}


def _total_debt_series(
    company_facts: dict[str, Any], *, period: FinancialPeriod
) -> dict[str, float]:
    """Return total debt from a direct tag or from short-plus-long debt tags."""
    direct = _series_for_tags(company_facts, TOTAL_DEBT_TAGS, period=period)
    if direct:
        return direct
    short_debt = _sum_series(
        [_series_for_tag(company_facts, tag, period=period) for tag in SHORT_DEBT_TAGS]
    )
    long_debt = _series_for_tags(company_facts, LONG_DEBT_TAGS, period=period)
    return _sum_series([short_debt, long_debt])


def _sum_series(series_list: list[dict[str, float]]) -> dict[str, float]:
    """Add aligned SEC fact series by reporting date."""
    result: dict[str, float] = {}
    for series in series_list:
        for end, value in series.items():
            result[end] = result.get(end, 0.0) + float(value)
    return result


def _rows_to_frame(rows: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Convert row mappings into a numeric DataFrame with newest dates first."""
    columns = sorted({date for values in rows.values() for date in values}, reverse=True)
    data = {
        label: [values.get(column, np.nan) for column in columns] for label, values in rows.items()
    }
    frame = pd.DataFrame.from_dict(data, orient="index", columns=columns)
    frame.index.name = "line_item"
    return frame.apply(pd.to_numeric, errors="coerce")


def _concept(company_facts: dict[str, Any], tag: str) -> dict[str, Any]:
    """Return a concept from supported SEC taxonomies."""
    for taxonomy in ("us-gaap", "dei", "ifrs-full"):
        concept = company_facts.get("facts", {}).get(taxonomy, {}).get(tag)
        if isinstance(concept, dict):
            return concept
    return {}


def _preferred_units(tag: str) -> tuple[str, ...]:
    """Return preferred SEC units for one taxonomy tag."""
    return ("shares",) if "Shares" in tag or "StockShares" in tag else ("USD", "usd")


def _matches_period(fact: dict[str, Any], period: FinancialPeriod) -> bool:
    """Return whether an SEC fact corresponds to the requested frequency."""
    form = str(fact.get("form", "")).upper()
    fiscal_period = str(fact.get("fp", "")).upper()
    if period == "annual":
        return form in ANNUAL_FORMS or fiscal_period == "FY"
    return form in QUARTERLY_FORMS or fiscal_period in {"Q1", "Q2", "Q3", "Q4"}


def _format_cik(cik: object) -> str:
    """Return a ten-digit SEC CIK string with leading zeros."""
    try:
        return f"{int(cik):010d}"
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(f"Invalid SEC CIK value: {cik!r}.") from exc


def _normalize_symbol(symbol: str) -> str:
    """Normalize a ticker symbol for provider lookup."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise MarketDataValidationError("symbol must be a non-empty string.")
    return symbol.strip().upper()


def _is_finite_number(value: object) -> bool:
    """Return whether a value can be interpreted as a finite floating point number."""
    try:
        return np.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _decode_sec_response_body(
    payload: bytes,
    *,
    content_encoding: str | None,
    charset: str,
) -> str:
    """Decode one SEC JSON response body, including compressed payloads."""
    normalized_encoding = (content_encoding or "").lower()
    if "gzip" in normalized_encoding or payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)
    elif "deflate" in normalized_encoding:
        payload = zlib.decompress(payload)
    return payload.decode(charset)


def _parse_datetime(value: object) -> datetime | None:
    """Parse an ISO datetime value used in SEC cache metadata."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _is_stale(timestamp: datetime | None, max_age_days: float) -> bool:
    """Return whether a timestamp is absent or older than the allowed age."""
    if timestamp is None:
        return True
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return (datetime.now(UTC) - timestamp).total_seconds() / 86400.0 > float(max_age_days)


__all__ = [
    "SecCompanyFacts",
    "SecJsonCacheStore",
    "SecXbrlProvider",
    "_statement_from_company_facts",
]
