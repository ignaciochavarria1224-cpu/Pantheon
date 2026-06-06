"""
Repository — the typed read/write layer over the Olympus database.

Translates the strategy-agnostic dataclasses (Order, Fill, Position, Trade) into
rows and back. Every write stamps strategy_id / experiment_id / environment and a
provenance recorded_at. Writes are idempotent (INSERT OR IGNORE on stable ids) so
a restart or retry never double-writes.

This layer assumes its inputs are already broker-truth: the ExecutionEngine only
ever hands it confirmed fills. The schema's CHECK (confirmed = 1) is the backstop.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.db.database import Database
from core.logger import get_logger
from core.trading.models import Direction, Fill, Order, Position, Side, Trade

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime to UTC ISO-8601 text. Naive datetimes are assumed UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _enum_value(v: Any) -> Any:
    """Return .value for an Enum, else the value unchanged."""
    return v.value if hasattr(v, "value") else v


class Repository:
    """Typed persistence for the trade lifecycle and market data."""

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Orders (intent)
    # ------------------------------------------------------------------

    def record_order(self, order: Order) -> bool:
        """Persist a submitted order (intent). Idempotent on order_id."""
        self._db.execute(
            """
            INSERT OR IGNORE INTO orders (
                order_id, client_order_id, strategy_id, experiment_id, environment,
                symbol, side, requested_qty, order_type, time_in_force, intent,
                broker_status, submitted_at, signal_json, source, recorded_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                order.order_id,
                order.client_order_id,
                order.strategy_id,
                order.experiment_id,
                order.environment,
                order.symbol,
                _enum_value(order.side),
                int(order.requested_qty),
                order.order_type,
                order.time_in_force,
                _enum_value(order.intent),
                order.broker_status,
                _iso(order.submitted_at),
                order.signal_json,
                order.source,
                _utc_now_iso(),
            ),
        )
        return True

    def update_order_status(self, order_id: str, broker_status: str) -> None:
        """Update the last-observed broker status on an order row."""
        self._db.execute(
            "UPDATE orders SET broker_status = ? WHERE order_id = ?",
            (broker_status, order_id),
        )

    # ------------------------------------------------------------------
    # Fills (broker-confirmed only)
    # ------------------------------------------------------------------

    def record_fill(self, fill: Fill) -> bool:
        """Persist a broker-confirmed fill. Idempotent on fill_id."""
        self._db.execute(
            """
            INSERT OR IGNORE INTO fills (
                fill_id, order_id, strategy_id, experiment_id, environment,
                symbol, side, fill_price, fill_qty, fill_time,
                confirmed, source, recorded_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?)
            """,
            (
                fill.fill_id,
                fill.order_id,
                fill.strategy_id,
                fill.experiment_id,
                fill.environment,
                fill.symbol,
                _enum_value(fill.side),
                float(fill.fill_price),
                int(fill.fill_qty),
                _iso(fill.fill_time),
                fill.source,
                _utc_now_iso(),
            ),
        )
        return True

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def open_position(self, position: Position) -> bool:
        """Persist a newly opened position. Idempotent on position_id."""
        now = _utc_now_iso()
        self._db.execute(
            """
            INSERT OR IGNORE INTO positions (
                position_id, strategy_id, experiment_id, environment,
                symbol, direction, entry_price, size,
                entry_order_id, entry_fill_id, entry_time, status,
                signal_json, recorded_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                position.position_id,
                position.strategy_id,
                position.experiment_id,
                position.environment,
                position.symbol,
                _enum_value(position.direction),
                float(position.entry_price),
                int(position.size),
                position.entry_order_id,
                position.entry_fill_id,
                _iso(position.entry_time),
                "open",
                position.signal_json,
                now,
                now,
            ),
        )
        return True

    def close_position(
        self,
        position_id: str,
        *,
        exit_order_id: str,
        exit_fill_id: str,
        exit_time: datetime,
    ) -> None:
        """Mark a position closed, linking the confirmed exit order/fill."""
        self._db.execute(
            """
            UPDATE positions
               SET status = 'closed',
                   exit_order_id = ?,
                   exit_fill_id = ?,
                   exit_time = ?,
                   updated_at = ?
             WHERE position_id = ?
            """,
            (exit_order_id, exit_fill_id, _iso(exit_time), _utc_now_iso(), position_id),
        )

    # ------------------------------------------------------------------
    # Trades (completed round-trips)
    # ------------------------------------------------------------------

    def record_trade(self, trade: Trade) -> bool:
        """Persist a completed trade. Idempotent on trade_id."""
        self._db.execute(
            """
            INSERT OR IGNORE INTO trades (
                trade_id, position_id, strategy_id, experiment_id, environment,
                symbol, direction, entry_price, exit_price, size,
                entry_time, exit_time, hold_duration_minutes, realized_pnl, exit_reason,
                entry_order_id, exit_order_id, entry_fill_id, exit_fill_id,
                signal_json, recorded_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                trade.trade_id,
                trade.position_id,
                trade.strategy_id,
                trade.experiment_id,
                trade.environment,
                trade.symbol,
                _enum_value(trade.direction),
                float(trade.entry_price),
                float(trade.exit_price),
                int(trade.size),
                _iso(trade.entry_time),
                _iso(trade.exit_time),
                float(trade.hold_duration_minutes) if trade.hold_duration_minutes is not None else None,
                float(trade.realized_pnl),
                trade.exit_reason,
                trade.entry_order_id,
                trade.exit_order_id,
                trade.entry_fill_id,
                trade.exit_fill_id,
                trade.signal_json,
                _utc_now_iso(),
            ),
        )
        return True

    # ------------------------------------------------------------------
    # System events (everything Olympus tried to do)
    # ------------------------------------------------------------------

    def write_event(
        self,
        event_type: str,
        summary: str,
        *,
        environment: str,
        strategy_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        symbol: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Record a system_event. Returns the new event_id."""
        event_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO system_events (
                event_id, event_type, strategy_id, experiment_id, environment,
                symbol, summary, metadata_json, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                event_type,
                strategy_id,
                experiment_id,
                environment,
                symbol,
                summary,
                json.dumps(metadata) if metadata is not None else None,
                _utc_now_iso(),
            ),
        )
        return event_id

    # ------------------------------------------------------------------
    # Market data (shared truth — idempotent ingestion)
    # ------------------------------------------------------------------

    def upsert_bars(
        self,
        bars: list[dict[str, Any]],
        timeframe: str,
        source: str = "alpaca",
    ) -> int:
        """
        Insert OHLCV bars idempotently. Uniqueness on (symbol, timeframe,
        timestamp) means a re-run never creates duplicate rows. Returns the
        number of NEW rows inserted.
        """
        if not bars:
            return 0
        now = _utc_now_iso()
        params = []
        for b in bars:
            ts = b["timestamp"]
            params.append((
                str(b["symbol"]).upper(),
                timeframe,
                _iso(ts) if isinstance(ts, datetime) else str(ts),
                float(b["open"]),
                float(b["high"]),
                float(b["low"]),
                float(b["close"]),
                float(b["volume"]),
                float(b["vwap"]) if b.get("vwap") is not None else None,
                source,
                now,
            ))
        # Count rows before/after to report how many were genuinely new.
        before = self._db.query_one("SELECT COUNT(*) AS n FROM market_data")["n"]
        self._db.executemany(
            """
            INSERT OR IGNORE INTO market_data (
                symbol, timeframe, timestamp, open, high, low, close, volume,
                vwap, source, ingested_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            params,
        )
        after = self._db.query_one("SELECT COUNT(*) AS n FROM market_data")["n"]
        inserted = after - before
        logger.info(
            "upsert_bars: %d submitted, %d new rows (timeframe=%s)",
            len(params), inserted, timeframe,
        )
        return inserted

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_open_positions(self, strategy_id: Optional[str] = None) -> list[Position]:
        """Return open positions, optionally filtered to one strategy."""
        if strategy_id is None:
            rows = self._db.query("SELECT * FROM positions WHERE status = 'open'")
        else:
            rows = self._db.query(
                "SELECT * FROM positions WHERE status = 'open' AND strategy_id = ?",
                (strategy_id,),
            )
        return [self._row_to_position(r) for r in rows]

    def get_position(self, position_id: str) -> Optional[Position]:
        row = self._db.query_one(
            "SELECT * FROM positions WHERE position_id = ?", (position_id,)
        )
        return self._row_to_position(row) if row is not None else None

    @staticmethod
    def _row_to_position(row: dict) -> Position:
        def _dt(v: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(v) if v else None

        return Position(
            position_id=row["position_id"],
            strategy_id=row["strategy_id"],
            experiment_id=row["experiment_id"],
            environment=row["environment"],
            symbol=row["symbol"],
            direction=Direction(row["direction"]),
            entry_price=row["entry_price"],
            size=row["size"],
            entry_order_id=row["entry_order_id"],
            entry_fill_id=row["entry_fill_id"],
            entry_time=_dt(row["entry_time"]),
            status=row["status"],
            exit_order_id=row["exit_order_id"],
            exit_fill_id=row["exit_fill_id"],
            exit_time=_dt(row["exit_time"]),
            signal_json=row["signal_json"],
        )
