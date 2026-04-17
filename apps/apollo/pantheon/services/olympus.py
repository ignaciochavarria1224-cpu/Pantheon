from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from config import (
    OLYMPUS_API_TIMEOUT,
    OLYMPUS_API_URL,
    OLYMPUS_APP_PATH,
    OLYMPUS_DB_PATH,
    OLYMPUS_LOG_PATH,
    OLYMPUS_REPORT_PATH,
)


def _resolve_path(configured: str, pattern: str) -> Path:
    configured_path = Path(configured)
    if configured_path.exists():
        return configured_path

    root = Path(OLYMPUS_APP_PATH)
    if root.exists():
        matches = sorted(root.rglob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]
    return configured_path


def _db_path() -> Path:
    return _resolve_path(OLYMPUS_DB_PATH, "olympus.db")


def _report_path() -> Path:
    return _resolve_path(OLYMPUS_REPORT_PATH, "latest.md")


def _log_path() -> Path:
    return _resolve_path(OLYMPUS_LOG_PATH, "olympus.log")


def _remote_snapshot() -> dict[str, Any] | None:
    if not OLYMPUS_API_URL:
        return None
    try:
        health = requests.get(f"{OLYMPUS_API_URL}/health", timeout=OLYMPUS_API_TIMEOUT).json()
        summary = requests.get(f"{OLYMPUS_API_URL}/summary", timeout=OLYMPUS_API_TIMEOUT).json()
        trades = requests.get(f"{OLYMPUS_API_URL}/trades", timeout=OLYMPUS_API_TIMEOUT).json()
        cycle = requests.get(f"{OLYMPUS_API_URL}/cycle/latest", timeout=OLYMPUS_API_TIMEOUT).json()
        report = requests.get(f"{OLYMPUS_API_URL}/report/latest", timeout=OLYMPUS_API_TIMEOUT).json()
        return {
            "connected": bool(health.get("connected")),
            "source": "api",
            "api_url": OLYMPUS_API_URL,
            "db_exists": bool(health.get("db_exists")),
            "db_path": health.get("db_path", ""),
            "db_updated_at": health.get("db_updated_at"),
            "report_path": report.get("path", ""),
            "report_updated_at": report.get("updated_at"),
            "log_updated_at": health.get("log_updated_at"),
            "performance": summary.get("performance", {}) or {},
            "latest_cycle": cycle.get("cycle"),
            "recent_trades": trades.get("trades", []) or [],
            "recent_events": summary.get("recent_events", []) or [],
            "report_excerpt": report.get("content", "")[:2500],
            "error": health.get("error", ""),
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "connected": False,
            "source": "api",
            "api_url": OLYMPUS_API_URL,
            "db_exists": False,
            "db_path": "",
            "db_updated_at": None,
            "report_path": "",
            "report_updated_at": None,
            "log_updated_at": None,
            "performance": {},
            "latest_cycle": None,
            "recent_trades": [],
            "recent_events": [],
            "report_excerpt": "",
            "error": f"Olympus API unreachable: {exc}",
            "fetched_at": datetime.now().isoformat(),
        }


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
    remote = _remote_snapshot()
    if remote is not None:
        return remote
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
            "source": "local",
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
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "connected": False,
            "source": "local",
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
            "fetched_at": datetime.now().isoformat(),
        }
