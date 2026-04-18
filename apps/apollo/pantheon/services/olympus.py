from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import OLYMPUS_DB_PATH, OLYMPUS_LOG_PATH, OLYMPUS_REPORT_PATH


def _db_path() -> Path:
    return Path(OLYMPUS_DB_PATH)


def _report_path() -> Path:
    return Path(OLYMPUS_REPORT_PATH)


def _log_path() -> Path:
    return Path(OLYMPUS_LOG_PATH)


def _iso_modified(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def _query_all(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    path = _db_path()
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _query_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    rows = _query_all(sql, params)
    return rows[0] if rows else None


def get_snapshot() -> dict[str, Any]:
    try:
        db_exists = _db_path().exists()
        latest_cycle = _query_one(
            "SELECT cycle_id, cycle_timestamp, universe_size, scored_count, error_count, top_longs_json, top_shorts_json "
            "FROM ranking_cycles ORDER BY cycle_timestamp DESC LIMIT 1"
        )
        performance = _query_one(
            """
            SELECT
                COUNT(*) AS total_trades,
                SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) AS winners,
                SUM(CASE WHEN realized_pnl <= 0 THEN 1 ELSE 0 END) AS losers,
                ROUND(COALESCE(SUM(realized_pnl), 0), 2) AS total_pnl,
                ROUND(COALESCE(AVG(realized_pnl), 0), 2) AS avg_pnl,
                ROUND(COALESCE(AVG(r_multiple), 0), 2) AS avg_r_multiple,
                MAX(exit_time) AS last_trade_at
            FROM trades
            """
        ) or {}
        recent_trades = _query_all(
            """
            SELECT symbol, direction, realized_pnl, r_multiple, exit_reason, exit_time
            FROM trades
            ORDER BY exit_time DESC
            LIMIT 8
            """
        )
        events = _query_all(
            """
            SELECT event_time, event_type, symbol, description
            FROM system_events
            ORDER BY event_time DESC
            LIMIT 8
            """
        )
        report_excerpt = ""
        report_path = _report_path()
        if report_path.exists():
            report_excerpt = report_path.read_text(encoding="utf-8")[:2500]

        if latest_cycle:
            latest_cycle["top_longs"] = json.loads(latest_cycle.pop("top_longs_json") or "[]")
            latest_cycle["top_shorts"] = json.loads(latest_cycle.pop("top_shorts_json") or "[]")

        return {
            "connected": db_exists or report_path.exists(),
            "db_exists": db_exists,
            "db_path": str(_db_path()),
            "db_updated_at": _iso_modified(_db_path()),
            "report_path": str(report_path),
            "report_updated_at": _iso_modified(report_path),
            "log_updated_at": _iso_modified(_log_path()),
            "performance": performance,
            "latest_cycle": latest_cycle,
            "recent_trades": recent_trades,
            "recent_events": events,
            "report_excerpt": report_excerpt,
        }
    except Exception as exc:
        return {
            "connected": False,
            "error": str(exc),
            "db_exists": False,
            "db_path": str(_db_path()),
            "db_updated_at": None,
            "report_path": str(_report_path()),
            "report_updated_at": None,
            "log_updated_at": None,
            "performance": {},
            "latest_cycle": None,
            "recent_trades": [],
            "recent_events": [],
            "report_excerpt": "",
        }
