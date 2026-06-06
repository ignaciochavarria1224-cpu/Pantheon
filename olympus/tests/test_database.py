"""
Tests for the corrected, empty database foundation (Step 1).

Verifies the constitution's requirements: a fresh database initializes EMPTY,
WAL is on, all tables/indexes/views exist, the strategy/experiment/environment
tags are present on every lifecycle table, and Article II is enforced at the
storage layer (a fill cannot exist unconfirmed; market data cannot duplicate).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.db.database import Database

_LIFECYCLE_TABLES = ["orders", "fills", "positions", "trades", "system_events"]
_ALL_TABLES = _LIFECYCLE_TABLES + ["market_data"]


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "test_olympus.db")
    database.initialize()
    yield database
    database.close()


def test_initialize_is_idempotent(tmp_path: Path):
    database = Database(tmp_path / "idem.db")
    database.initialize()
    database.initialize()  # second call must not raise
    tables = database.query("SELECT name FROM sqlite_master WHERE type='table'")
    names = {t["name"] for t in tables}
    for table in _ALL_TABLES:
        assert table in names
    database.close()


def test_wal_mode_enabled(db: Database):
    row = db.query_one("PRAGMA journal_mode")
    assert str(row["journal_mode"]).lower() == "wal"


def test_foreign_keys_enabled(db: Database):
    row = db.query_one("PRAGMA foreign_keys")
    assert row["foreign_keys"] == 1


def test_all_tables_exist(db: Database):
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table'")
    names = {t["name"] for t in tables}
    for table in _ALL_TABLES:
        assert table in names, f"missing table: {table}"


def test_quality_view_exists(db: Database):
    views = db.query("SELECT name FROM sqlite_master WHERE type='view'")
    names = {v["name"] for v in views}
    assert "v_trade_quality" in names


def test_database_starts_empty(db: Database):
    for table in _ALL_TABLES:
        row = db.query_one(f"SELECT COUNT(*) AS n FROM {table}")
        assert row["n"] == 0, f"table {table} should start empty"


def test_lifecycle_tables_carry_required_tags(db: Database):
    """strategy_id, experiment_id, environment must exist on every lifecycle table."""
    for table in _LIFECYCLE_TABLES:
        cols = {c["name"] for c in db.query(f"PRAGMA table_info({table})")}
        assert "strategy_id" in cols, f"{table} missing strategy_id"
        assert "experiment_id" in cols, f"{table} missing experiment_id"
        assert "environment" in cols, f"{table} missing environment"


def test_fill_cannot_be_unconfirmed(db: Database):
    """Article II at the storage layer: a fill row with confirmed != 1 is rejected."""
    # First insert a parent order so the FK is satisfiable.
    db.execute(
        """
        INSERT INTO orders (order_id, strategy_id, experiment_id, environment,
                            symbol, side, requested_qty, recorded_at)
        VALUES ('o1','s1','e1','paper','AAPL','buy',10,'2026-06-06T00:00:00+00:00')
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO fills (fill_id, order_id, strategy_id, experiment_id,
                               environment, symbol, side, fill_price, fill_qty,
                               fill_time, confirmed, source, recorded_at)
            VALUES ('f1','o1','s1','e1','paper','AAPL','buy',100.0,10,
                    '2026-06-06T00:00:00+00:00', 0, 'broker_poll',
                    '2026-06-06T00:00:00+00:00')
            """
        )


def test_environment_marker_is_constrained(db: Database):
    """environment must be 'paper' or 'live' — nothing else."""
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO orders (order_id, strategy_id, experiment_id, environment,
                                symbol, side, requested_qty, recorded_at)
            VALUES ('o2','s1','e1','staging','AAPL','buy',10,
                    '2026-06-06T00:00:00+00:00')
            """
        )


def test_market_data_is_idempotent(db: Database):
    """UNIQUE(symbol, timeframe, timestamp) prevents duplicate bars."""
    insert = """
        INSERT OR IGNORE INTO market_data (symbol, timeframe, timestamp,
            open, high, low, close, volume, source, ingested_at)
        VALUES ('AAPL','1Day','2026-06-05T00:00:00+00:00',
                1,2,0.5,1.5,1000,'alpaca','2026-06-06T00:00:00+00:00')
    """
    db.execute(insert)
    db.execute(insert)  # duplicate — must be ignored
    row = db.query_one("SELECT COUNT(*) AS n FROM market_data")
    assert row["n"] == 1
