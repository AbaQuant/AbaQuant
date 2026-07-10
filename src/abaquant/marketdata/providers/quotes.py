"""Quote-provider protocol."""

from __future__ import annotations

from typing import Any, Protocol


class QuoteProvider(Protocol):
    """Provider capability for lightweight quote and issuer metadata."""

    name: str

    def fast_info(self, symbol: str) -> dict[str, Any]:
        """Return lightweight quote metadata for one normalized symbol."""
        ...

    def info(self, symbol: str) -> dict[str, Any]:
        """Return issuer metadata for one normalized symbol."""
        ...
