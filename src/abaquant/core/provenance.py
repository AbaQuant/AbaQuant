"""Provider-neutral data provenance metadata for AbaQuant objects.

Purpose
-------
This module defines a compact immutable provenance record used by market data,
financial statements, rate curves, option chains, portfolio inputs, backtests,
calibrations, reports, and risk dashboards. The record is intentionally simple:
it captures where data came from, when it was retrieved or constructed, how cache
was used, which source labels were transformed, and the reporting conventions
attached to the dataset.

Conventions
-----------
Timestamps are stored as ISO-8601 UTC text. ``cache_status`` and ``request`` are
read-only mappings so provider-specific cache keys, URLs, refresh policies, or
shape diagnostics can be preserved without forcing a global schema.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import MappingProxyType


@dataclass(frozen=True)
class DataProvenance:
    """Immutable metadata describing how a dataset or result was produced.

    Parameters
    ----------
    provider : str
        Source provider or construction mechanism, such as ``"yahoo"``,
        ``"sec"``, ``"fred"``, ``"manual"``, or ``"derived"``.
    dataset : str
        Dataset or object category, for example ``"option_chain"`` or
        ``"financial_statement_snapshot"``.
    retrieved_at_utc : str | None, default=None
        ISO-8601 UTC retrieval/construction timestamp. When omitted, the current
        UTC time is used.
    cache_status : Mapping[str, object], optional
        Provider-specific cache diagnostics.
    source_labels : Sequence[str], optional
        Provider-native labels or series identifiers used in the dataset.
    currency : str | None, default=None
        Reporting currency where applicable.
    reporting_date : str | None, default=None
        Reporting date, observation date, or period label.
    transformation_steps : Sequence[str], optional
        Ordered human-readable transformations applied to the source data.
    request : Mapping[str, object], optional
        Request metadata such as symbol, period, source, or refresh policy.
    notes : Sequence[str], optional
        Additional limitations or interpretation notes.
    """

    provider: str
    dataset: str
    retrieved_at_utc: str | None = None
    cache_status: Mapping[str, object] = field(default_factory=dict)
    source_labels: tuple[str, ...] = ()
    currency: str | None = None
    reporting_date: str | None = None
    transformation_steps: tuple[str, ...] = ()
    request: Mapping[str, object] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Normalize mappings, sequences, provider labels, and timestamps."""
        provider = str(self.provider).strip().lower() or "unknown"
        dataset = str(self.dataset).strip() or "unknown"
        retrieved_at = self.retrieved_at_utc or utc_now_iso()
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "retrieved_at_utc", _timestamp_to_iso(retrieved_at))
        object.__setattr__(self, "cache_status", _freeze_mapping(self.cache_status or {}))
        object.__setattr__(self, "request", _freeze_mapping(self.request or {}))
        object.__setattr__(self, "source_labels", _string_tuple(self.source_labels))
        object.__setattr__(self, "transformation_steps", _string_tuple(self.transformation_steps))
        object.__setattr__(self, "notes", _string_tuple(self.notes))
        if self.currency is not None:
            object.__setattr__(self, "currency", str(self.currency).upper())
        if self.reporting_date is not None:
            object.__setattr__(self, "reporting_date", str(self.reporting_date))

    def __deepcopy__(self, memo: dict[int, object]) -> DataProvenance:
        """Return self because the normalized provenance record is immutable."""
        memo[id(self)] = self
        return self

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable provenance dictionary."""
        return {
            "provider": self.provider,
            "dataset": self.dataset,
            "retrieved_at_utc": self.retrieved_at_utc,
            "cache_status": _thaw_value(self.cache_status),
            "source_labels": list(self.source_labels),
            "currency": self.currency,
            "reporting_date": self.reporting_date,
            "transformation_steps": list(self.transformation_steps),
            "request": _thaw_value(self.request),
            "notes": list(self.notes),
        }

    def with_step(self, step: str) -> DataProvenance:
        """Return a copy with one additional transformation step appended."""
        return DataProvenance(
            provider=self.provider,
            dataset=self.dataset,
            retrieved_at_utc=self.retrieved_at_utc,
            cache_status=self.cache_status,
            source_labels=self.source_labels,
            currency=self.currency,
            reporting_date=self.reporting_date,
            transformation_steps=(*self.transformation_steps, str(step)),
            request=self.request,
            notes=self.notes,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, object] | None) -> DataProvenance | None:
        """Build a provenance object from a saved dictionary payload.

        Parameters
        ----------
        payload : mapping or None
            Serialized provenance dictionary. ``None`` returns ``None``.

        Returns
        -------
        DataProvenance | None
            Reconstructed provenance record or ``None`` when unavailable.
        """
        if payload is None:
            return None
        try:
            return cls(
                provider=str(payload.get("provider", "unknown")),
                dataset=str(payload.get("dataset", "unknown")),
                retrieved_at_utc=payload.get("retrieved_at_utc"),
                cache_status=_mapping_or_empty(payload.get("cache_status")),
                source_labels=tuple(payload.get("source_labels") or ()),
                currency=payload.get("currency"),
                reporting_date=payload.get("reporting_date"),
                transformation_steps=tuple(payload.get("transformation_steps") or ()),
                request=_mapping_or_empty(payload.get("request")),
                notes=tuple(payload.get("notes") or ()),
            )
        except (AttributeError, TypeError, ValueError):
            return None


class ProvenanceMixin:
    """Mixin for objects that expose a ``provenance`` metadata attribute."""

    provenance: DataProvenance

    def provenance_dict(self) -> dict[str, object]:
        """Return this object's provenance as a plain dictionary."""
        return self.provenance.as_dict()


def utc_now_iso() -> str:
    """Return the current UTC timestamp in second precision."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def provenance_from_dataframe(
    frame: object,
    *,
    provider: str,
    dataset: str,
    source_labels: Sequence[str] = (),
    transformation_steps: Sequence[str] = (),
    currency: str | None = None,
    reporting_date: str | None = None,
    request: Mapping[str, object] | None = None,
    cache_status: Mapping[str, object] | None = None,
) -> DataProvenance:
    """Build provenance with shape metadata for a tabular object.

    Parameters
    ----------
    frame : object
        DataFrame-like object exposing ``shape``.
    provider, dataset, source_labels, transformation_steps, currency, reporting_date, request, cache_status
        Fields passed to :class:`DataProvenance`.

    Returns
    -------
    DataProvenance
        Provenance record including table-shape request metadata.
    """
    shape = getattr(frame, "shape", None)
    request_payload = dict(request or {})
    if shape is not None:
        request_payload.setdefault("shape", tuple(int(value) for value in shape))
    return DataProvenance(
        provider=provider,
        dataset=dataset,
        cache_status=cache_status or {},
        source_labels=tuple(source_labels),
        currency=currency,
        reporting_date=reporting_date,
        transformation_steps=tuple(transformation_steps),
        request=request_payload,
    )


def merge_provenance(
    records: Sequence[DataProvenance | None],
    *,
    provider: str = "derived",
    dataset: str = "combined",
    transformation_steps: Sequence[str] = (),
    request: Mapping[str, object] | None = None,
) -> DataProvenance:
    """Combine several provenance records into one derived record.

    Parameters
    ----------
    records : sequence of DataProvenance or None
        Input provenance records. ``None`` values are ignored.
    provider : str, default="derived"
        Provider label for the combined object.
    dataset : str, default="combined"
        Dataset label for the combined object.
    transformation_steps : sequence of str, optional
        Extra transformation steps appended after source steps.
    request : mapping, optional
        Combined-object request metadata.

    Returns
    -------
    DataProvenance
        Derived provenance record with nested source metadata in ``request``.
    """
    valid = [record for record in records if record is not None]
    source_labels: list[str] = []
    steps: list[str] = []
    for record in valid:
        source_labels.extend(record.source_labels)
        steps.extend(record.transformation_steps)
    combined_request = dict(request or {})
    combined_request["source_provenance"] = [record.as_dict() for record in valid]
    return DataProvenance(
        provider=provider,
        dataset=dataset,
        source_labels=tuple(dict.fromkeys(source_labels)),
        transformation_steps=tuple(dict.fromkeys([*steps, *map(str, transformation_steps)])),
        request=combined_request,
    )


def _timestamp_to_iso(value: object) -> str:
    """Return an ISO-8601 UTC timestamp from a supported value."""
    if isinstance(value, datetime):
        timestamp = value if value.tzinfo else value.replace(tzinfo=UTC)
        return timestamp.astimezone(UTC).replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC).isoformat()
    text = str(value)
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError:
        return utc_now_iso()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).replace(microsecond=0).isoformat()


def _string_tuple(values: Sequence[object] | object) -> tuple[str, ...]:
    """Normalize one optional sequence into a tuple of non-empty strings."""
    if values is None:
        return ()
    raw_values = (values,) if isinstance(values, (str, bytes)) else tuple(values)
    return tuple(str(value) for value in raw_values if str(value))


def _freeze_value(value: object) -> object:
    """Recursively convert mutable mapping/list containers into read-only values."""
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a read-only copy of a mapping with recursively frozen containers."""
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _thaw_value(value: object) -> object:
    """Return a JSON-serializable mutable representation of a frozen value."""
    if isinstance(value, Mapping):
        return {str(key): _thaw_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_value(item) for item in value]
    return value


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    """Return a mapping if available, otherwise an empty dictionary."""
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "DataProvenance",
    "ProvenanceMixin",
    "merge_provenance",
    "provenance_from_dataframe",
    "utc_now_iso",
]
