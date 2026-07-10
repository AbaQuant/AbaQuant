"""Atomic, versioned disk cache for financial-statement snapshots."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from abaquant.core import DataProvenance

from .line_item_resolver import resolve_line_items
from .models import FinancialPeriod, FinancialStatementSnapshot
from .normalizer import frame_from_payload, frame_to_payload


class FinancialStatementCacheStore:
    """Read and write snapshots atomically; invalid or corrupt files are cache misses."""

    schema_version = 2

    def __init__(self, directory: str | Path, source_name: str = "default") -> None:
        """Configure the root directory and provider namespace for snapshots."""
        self.directory = Path(directory).expanduser()
        self.source_name = str(source_name).lower().replace("/", "_")

    def path(self, symbol: str, period: FinancialPeriod) -> Path:
        """Return the deterministic cache path for one symbol, source, and period."""
        return self.directory / self.source_name / symbol / f"{period}.json"

    def load(self, symbol: str, period: FinancialPeriod) -> FinancialStatementSnapshot | None:
        """Load and checksum-validate one cache entry."""
        p = self.path(symbol, period)
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            checksum = payload.pop("checksum")
            serialized = json.dumps(
                payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            if hashlib.sha256(serialized.encode()).hexdigest() != checksum:
                return None
            if (
                payload.get("schema_version") != self.schema_version
                or payload.get("symbol") != symbol
                or payload.get("period") != period
            ):
                return None
            income = frame_from_payload(payload["income_statement"])
            balance = frame_from_payload(payload["balance_sheet"])
            cash = frame_from_payload(payload["cash_flow_statement"])
            return FinancialStatementSnapshot(
                symbol,
                str(payload.get("provider_name", "cached")),
                period,
                datetime.fromisoformat(payload["retrieved_at_utc"]),
                income,
                balance,
                cash,
                resolve_line_items(income, balance, cash),
                DataProvenance.from_dict(payload.get("provenance")),
            )
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, snapshot: FinancialStatementSnapshot) -> None:
        """Write a cache entry through a temporary file and atomic replacement."""
        p = self.path(snapshot.symbol, snapshot.period)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "symbol": snapshot.symbol,
            "provider_name": snapshot.provider_name,
            "period": snapshot.period,
            "retrieved_at_utc": snapshot.retrieved_at_utc.isoformat(),
            "income_statement": frame_to_payload(snapshot.income_statement),
            "balance_sheet": frame_to_payload(snapshot.balance_sheet),
            "cash_flow_statement": frame_to_payload(snapshot.cash_flow_statement),
            "provenance": snapshot.provenance.as_dict(),
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        payload["checksum"] = hashlib.sha256(serialized.encode()).hexdigest()
        temporary = p.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        os.replace(temporary, p)

    def remove(self, symbol: str, period: FinancialPeriod) -> None:
        """Remove one cache entry if it exists."""
        p = self.path(symbol, period)
        if p.exists():
            p.unlink()
