"""
Strategy-agnostic data models for the Olympus foundation.

These are deliberately free of any strategy-specific concept (no rank, score,
regime, or features). Every lifecycle record carries the three mandated tags —
strategy_id, experiment_id, environment — and a free-form signal_json slot for a
strategy to record its own reasoning without a schema change.

Standard dataclasses, no external dependencies. Timestamps are tz-aware UTC
datetimes; the repository serializes them to ISO-8601 text on write.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Side(str, Enum):
    """Broker order side."""
    BUY = "buy"
    SELL = "sell"


class Direction(str, Enum):
    """Position direction."""
    LONG = "long"
    SHORT = "short"


class OrderIntent(str, Enum):
    """Whether an order opens or closes exposure."""
    ENTRY = "entry"
    EXIT = "exit"


@dataclass
class Order:
    """An order Olympus SUBMITTED. Intent — not outcome. Keyed by broker order_id."""
    order_id: str                       # broker order id (truth anchor)
    strategy_id: str
    experiment_id: str
    environment: str                    # "paper" | "live"
    symbol: str
    side: Side
    requested_qty: int                  # INTENT: shares requested
    intent: OrderIntent = OrderIntent.ENTRY
    order_type: str = "market"
    time_in_force: str = "day"
    client_order_id: Optional[str] = None
    broker_status: Optional[str] = None
    submitted_at: Optional[datetime] = None
    signal_json: Optional[str] = None
    source: str = "olympus"


@dataclass
class Fill:
    """A BROKER-CONFIRMED fill. Article II: broker price/qty/time only."""
    fill_id: str
    order_id: str
    strategy_id: str
    experiment_id: str
    environment: str
    symbol: str
    side: Side
    fill_price: float                   # broker filled_avg_price
    fill_qty: int                       # broker filled_qty
    fill_time: datetime                 # broker filled_at
    source: str = "broker_poll"


@dataclass
class Position:
    """An open position built from a confirmed entry fill; closed on exit fill."""
    position_id: str
    strategy_id: str
    experiment_id: str
    environment: str
    symbol: str
    direction: Direction
    entry_price: float                  # broker fill price
    size: int                           # broker filled qty
    entry_order_id: str
    entry_fill_id: str
    entry_time: datetime
    status: str = "open"                # "open" | "closed"
    exit_order_id: Optional[str] = None
    exit_fill_id: Optional[str] = None
    exit_time: Optional[datetime] = None
    signal_json: Optional[str] = None


@dataclass
class Trade:
    """A completed round-trip (entry fill -> exit fill). PnL on broker truth only."""
    trade_id: str
    position_id: str
    strategy_id: str
    experiment_id: str
    environment: str
    symbol: str
    direction: Direction
    entry_price: float
    exit_price: float
    size: int
    entry_time: datetime
    exit_time: datetime
    realized_pnl: float
    exit_reason: str
    entry_order_id: str
    exit_order_id: str
    entry_fill_id: str
    exit_fill_id: str
    hold_duration_minutes: Optional[float] = None
    signal_json: Optional[str] = None
