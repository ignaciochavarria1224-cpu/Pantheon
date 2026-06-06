"""
Tests for market-data ingestion (Step 3).

Verifies the constitution's "reliably collecting data" milestone: bars land in
market_data, and a re-run adds ZERO duplicate rows (idempotent on
symbol/timeframe/timestamp). Uses a fake fetcher, so it runs with no .env.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from core.data.ingestion import MarketDataIngestion
from core.db.database import Database
from core.db.repository import Repository

WATCHLIST = ["SPY", "AAPL"]


class FakeFetcher:
    """Returns a fixed two-bar-per-symbol frame, ignoring the date range."""

    def __init__(self, symbols):
        self._symbols = symbols
        self.calls = 0

    def fetch_historical_bars(self, symbols, start, end, timeframe=None, **kwargs):
        self.calls += 1
        rows = []
        for sym in symbols:
            for day in (4, 5):
                rows.append({
                    "symbol": sym,
                    "timestamp": pd.Timestamp(2026, 6, day, 20, 0, tz="UTC"),
                    "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5,
                    "volume": 1_000_000.0, "vwap": 100.25,
                })
        return pd.DataFrame(rows)


@pytest.fixture
def settings():
    return SimpleNamespace(
        WATCHLIST=tuple(WATCHLIST),
        BAR_TIMEFRAME="1Day",
        HISTORICAL_LOOKBACK_DAYS=30,
    )


@pytest.fixture
def repo(tmp_path: Path):
    db = Database(tmp_path / "ingest.db")
    db.initialize()
    yield Repository(db)
    db.close()


def test_first_ingest_inserts_rows(repo, settings):
    ingestion = MarketDataIngestion(FakeFetcher(WATCHLIST), repo, settings)
    summary = ingestion.ingest_watchlist()
    # 2 symbols x 2 days = 4 rows
    assert summary["fetched"] == 4
    assert summary["inserted"] == 4
    n = repo._db.query_one("SELECT COUNT(*) AS n FROM market_data")["n"]
    assert n == 4


def test_reingest_adds_no_duplicates(repo, settings):
    ingestion = MarketDataIngestion(FakeFetcher(WATCHLIST), repo, settings)
    ingestion.ingest_watchlist()
    second = ingestion.ingest_watchlist()
    assert second["inserted"] == 0, "re-running must not create duplicate rows"
    n = repo._db.query_one("SELECT COUNT(*) AS n FROM market_data")["n"]
    assert n == 4


def test_bars_have_provenance_and_utc_timestamps(repo, settings):
    ingestion = MarketDataIngestion(FakeFetcher(WATCHLIST), repo, settings)
    ingestion.ingest_watchlist()
    row = repo._db.query_one(
        "SELECT * FROM market_data WHERE symbol = 'SPY' ORDER BY timestamp LIMIT 1"
    )
    assert row["source"] == "alpaca"
    assert row["timeframe"] == "1Day"
    assert row["vwap"] == 100.25
    assert row["ingested_at"] is not None
    # stored as UTC ISO-8601 text
    assert "+00:00" in row["timestamp"]
    datetime.fromisoformat(row["timestamp"])  # parses cleanly


def test_market_data_has_no_strategy_tags(repo, settings):
    """Market data is shared truth — it must NOT carry per-strategy tags."""
    cols = {c["name"] for c in repo._db.query("PRAGMA table_info(market_data)")}
    assert "strategy_id" not in cols
    assert "experiment_id" not in cols
