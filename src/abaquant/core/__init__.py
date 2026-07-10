"""Shared infrastructure for AbaQuant result objects.

The core package contains cross-domain primitives that are reused by market
providers, derivatives, portfolios, credit analytics, reports, and dashboards.
These objects do not belong to a single financial domain and are therefore
exposed from ``abaquant.core``.
"""

from .provenance import (
    DataProvenance,
    ProvenanceMixin,
    merge_provenance,
    provenance_from_dataframe,
)

__all__ = [
    "DataProvenance",
    "ProvenanceMixin",
    "merge_provenance",
    "provenance_from_dataframe",
]
