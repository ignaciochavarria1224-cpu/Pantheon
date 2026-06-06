"""
Data normalization pipeline for Olympus.
Pure-function layer: accepts raw bar data and returns a consistently structured
format. No business logic — data cleaning and structure only.

Ported near-verbatim from the stabilized old Olympus.

Output format: list[dict], each guaranteed to have:
    symbol      str
    timestamp   datetime (timezone-aware, US/Eastern)
    open        float64
    high        float64
    low         float64
    close       float64
    volume      float64
    vwap        float64 | None
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytz

from core.logger import get_logger

logger = get_logger(__name__)

_ET = pytz.timezone("America/New_York")

SCHEMA_COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume", "vwap"]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "vwap"]


def normalize_bars(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Normalize a raw bar DataFrame into a list of canonical bar dicts.

    Guarantees:
    - All ohlcv fields are float64 (NaN filled with 0.0; vwap NaN -> None)
    - Zero-volume bars are preserved, never dropped
    - timestamp is timezone-aware ET datetime
    """
    if df is None or df.empty:
        logger.debug("normalize_bars received empty DataFrame — returning []")
        return []

    df = df.copy()

    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"normalize_bars: missing required columns: {missing}")

    if "vwap" not in df.columns:
        df["vwap"] = None

    df["timestamp"] = _normalize_timestamps(df["timestamp"])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["vwap"] = pd.to_numeric(df["vwap"], errors="coerce").astype("float64")

    for col in ["open", "high", "low", "close", "volume"]:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.warning(
                "normalize_bars: %d NaN values in column '%s' — filling with 0.0",
                nan_count, col,
            )
        df[col] = df[col].fillna(0.0)

    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()

    records: list[dict[str, Any]] = []
    for row in df.itertuples(index=False):
        vwap_val = getattr(row, "vwap", None)
        if vwap_val is not None and pd.isna(vwap_val):
            vwap_val = None
        records.append({
            "symbol": str(row.symbol),
            "timestamp": row.timestamp,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": float(row.volume),
            "vwap": vwap_val,
        })

    logger.debug("normalize_bars: produced %d normalized records", len(records))
    return records


def validate_schema(records: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Validate a list of normalized bar dicts. Returns (is_valid, errors)."""
    if not records:
        return False, ["No records to validate"]

    errors: list[str] = []
    sample = records[0]
    for col in SCHEMA_COLUMNS:
        if col not in sample:
            errors.append(f"Missing key: '{col}'")
    for col in NUMERIC_COLUMNS:
        if col in sample and col != "vwap":
            if not isinstance(sample[col], (int, float)):
                errors.append(f"Column '{col}' is not numeric: {type(sample[col])}")
    ts = sample.get("timestamp")
    if ts is not None and hasattr(ts, "tzinfo"):
        if ts.tzinfo is None:
            errors.append("timestamp is not timezone-aware")
    elif ts is not None:
        errors.append(f"timestamp has unexpected type: {type(ts)}")
    return len(errors) == 0, errors


def _normalize_timestamps(ts_series: pd.Series) -> pd.Series:
    """Convert a timestamp series to US/Eastern timezone-aware datetimes."""
    ts_series = pd.to_datetime(ts_series, utc=True, errors="coerce")
    if hasattr(ts_series, "dt"):
        return ts_series.dt.tz_convert(_ET)

    def _convert(ts: Any) -> Any:
        if ts is None or (isinstance(ts, float) and pd.isna(ts)):
            return None
        if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
            return ts.astimezone(_ET)
        return _ET.localize(ts)

    return ts_series.apply(_convert)
