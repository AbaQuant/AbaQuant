"""Provider-statement table normalization and JSON-safe serialization."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd


def normalize_statement_frame(frame: pd.DataFrame | None) -> pd.DataFrame:
    """Normalize statement axes and numeric values without changing line labels."""
    if frame is None:
        return pd.DataFrame()
    normalized = pd.DataFrame(frame).copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [" | ".join(map(str, column)).strip() for column in normalized.columns]
    normalized.index = pd.Index(
        [str(index).strip() for index in normalized.index], name="line_item"
    )
    normalized.columns = [str(column) for column in normalized.columns]
    return normalized.apply(pd.to_numeric, errors="coerce")


def json_value(value: object) -> object:
    """Convert pandas and NumPy scalars into JSON-safe values."""
    if value is None or (isinstance(value, float) and not np.isfinite(value)) or pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def frame_to_payload(frame: pd.DataFrame) -> dict[str, object]:
    """Serialize a normalized statement frame to a portable JSON payload."""
    return {
        "index": [str(value) for value in frame.index],
        "columns": [str(value) for value in frame.columns],
        "data": [[json_value(value) for value in row] for row in frame.to_numpy(dtype=object)],
    }


def frame_from_payload(payload: dict[str, object]) -> pd.DataFrame:
    """Deserialize one normalized statement frame from a JSON payload."""
    return normalize_statement_frame(
        pd.DataFrame(payload["data"], index=payload["index"], columns=payload["columns"])
    )
