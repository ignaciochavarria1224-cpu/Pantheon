"""
The Article II suite — the unit test the first Olympus never had.

Proves the supreme law at the execution layer:
  * an unfilled / rejected / expired order writes NO fill, NO position, NO trade
    (only the order intent + an 'order_unfilled' event);
  * a confirmed fill is recorded at the BROKER's price / qty / time, never the
    requested values;
  * a partial fill records only the confirmed (partial) portion;
  * realized PnL is computed on broker-confirmed prices and filled quantity;
  * the broker reconciler detects local/broker disagreement (broker wins);
  * every recorded row carries strategy_id / experiment_id / environment.

All tests use a fake broker, so they run with no .env and in well under a second.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.db.database import Database
from core.db.repository import Repository
from core.trading.execution import ExecutionEngine
from core.trading.models import Direction, Position
from core.trading.reconciliation import BrokerReconciler, detect_position_mismatch

STRATEGY = "test_strategy"
EXPERIMENT = "exp_phase1"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def _filled(price, qty, status="filled", t=None):
    return {
        "status": status,
        "filled_avg_price": price,
        "filled_qty": qty,
        "filled_at": t or datetime(2026, 6, 5, 14, 30, tzinfo=timezone.utc),
    }


def _terminal_unfilled(status):
    return {"status": status, "filled_avg_price": None, "filled_qty": None, "filled_at": None}


class FakeBroker:
    """Minimal broker double: queue get_order responses; record submissions."""

    def __init__(self, order_id="ORD-1", submit_status="accepted"):
        self._order_id = order_id
        self._submit_status = submit_status
        self._responses: list[dict] = []
        self.positions: list[dict] = []
        self.open_orders: list[dict] = []
        self.submitted: list[tuple] = []

    def queue(self, *responses):
        self._responses = list(responses)

    def submit_market_order(self, symbol, qty, side):
        self.submitted.append((symbol, qty, side))
        return {"order_id": self._order_id, "symbol": symbol, "qty": qty,
                "side": side, "status": self._submit_status, "filled_avg_price": None}

    def get_order(self, order_id):
        if not self._responses:
            return None
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)

    def get_positions(self):
        return self.positions

    def get_open_orders(self):
        return self.open_orders


@pytest.fixture
def settings():
    # Tiny backoff so polling is instant; paper environment marker.
    return SimpleNamespace(
        FILL_CONFIRM_BACKOFF=(0.0, 0.0),
        ENVIRONMENT="paper",
        ALPACA_PAPER=True,
        OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS=False,
        OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH=True,
    )


@pytest.fixture
def repo(tmp_path: Path):
    db = Database(tmp_path / "exec.db")
    db.initialize()
    yield Repository(db)
    db.close()


def _counts(repo: Repository):
    db = repo._db
    return {
        "orders": db.query_one("SELECT COUNT(*) AS n FROM orders")["n"],
        "fills": db.query_one("SELECT COUNT(*) AS n FROM fills")["n"],
        "positions": db.query_one("SELECT COUNT(*) AS n FROM positions")["n"],
        "trades": db.query_one("SELECT COUNT(*) AS n FROM trades")["n"],
        "events": db.query_one("SELECT COUNT(*) AS n FROM system_events")["n"],
    }


# ---------------------------------------------------------------------------
# 1. Unconfirmed orders never become phantom state
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["rejected", "canceled", "expired"])
def test_terminal_unfilled_records_no_phantom_state(repo, settings, status):
    broker = FakeBroker()
    broker.queue(_terminal_unfilled(status))
    engine = ExecutionEngine(broker, settings, repo)

    result = engine.enter_position(
        "AAPL", Direction.LONG, 10, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )

    assert result is None
    c = _counts(repo)
    assert c["fills"] == 0, "an unfilled order must never write a fill"
    assert c["positions"] == 0, "an unfilled order must never open a position"
    assert c["trades"] == 0, "an unfilled order must never write a trade"
    assert c["orders"] == 1, "the order intent should still be recorded"
    # exactly one order_unfilled event
    ev = repo._db.query_one("SELECT event_type FROM system_events")
    assert ev["event_type"] == "order_unfilled"


def test_timeout_without_confirmation_records_nothing(repo, settings):
    broker = FakeBroker()
    broker.queue(_terminal_unfilled("new"))  # never reaches a fill — times out
    engine = ExecutionEngine(broker, settings, repo)

    result = engine.enter_position(
        "TSLA", Direction.LONG, 5, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )
    assert result is None
    c = _counts(repo)
    assert c["fills"] == 0 and c["positions"] == 0 and c["trades"] == 0


# ---------------------------------------------------------------------------
# 2. Confirmed fills are recorded at broker truth
# ---------------------------------------------------------------------------

def test_confirmed_fill_records_broker_price_not_requested(repo, settings):
    broker = FakeBroker()
    broker_price = 101.2345
    broker_time = datetime(2026, 6, 5, 18, 0, tzinfo=timezone.utc)
    broker.queue(_filled(broker_price, 10, t=broker_time))
    engine = ExecutionEngine(broker, settings, repo)

    pos = engine.enter_position(
        "AAPL", Direction.LONG, 10, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )

    assert pos is not None
    assert pos.entry_price == broker_price
    fill = repo._db.query_one("SELECT * FROM fills")
    assert fill["fill_price"] == broker_price
    assert fill["fill_qty"] == 10
    assert fill["confirmed"] == 1
    # broker fill time, not a local clock
    assert fill["fill_time"] == broker_time.isoformat()
    # tags stamped everywhere
    order = repo._db.query_one("SELECT * FROM orders")
    for row in (order, fill):
        assert row["strategy_id"] == STRATEGY
        assert row["experiment_id"] == EXPERIMENT
        assert row["environment"] == "paper"


# ---------------------------------------------------------------------------
# 3. Partial fills record only the confirmed portion
# ---------------------------------------------------------------------------

def test_partial_fill_records_confirmed_portion_only(repo, settings):
    broker = FakeBroker()
    # Never reaches terminal 'filled'; stays partially_filled with 6 of 10 shares.
    broker.queue(_filled(99.5, 6, status="partially_filled"))
    engine = ExecutionEngine(broker, settings, repo)

    pos = engine.enter_position(
        "NVDA", Direction.LONG, 10, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )

    assert pos is not None
    assert pos.size == 6, "must record the broker's filled qty, not the requested 10"
    fill = repo._db.query_one("SELECT fill_qty FROM fills")
    assert fill["fill_qty"] == 6


# ---------------------------------------------------------------------------
# 4. Exit path: PnL on broker truth, position closed, trade recorded
# ---------------------------------------------------------------------------

def test_exit_computes_pnl_on_broker_truth(repo, settings):
    # Entry confirmed at 100.0 x 10
    entry_broker = FakeBroker(order_id="ENTRY-1")
    entry_broker.queue(_filled(100.0, 10))
    engine = ExecutionEngine(entry_broker, settings, repo)
    pos = engine.enter_position(
        "AAPL", Direction.LONG, 10, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )
    assert pos is not None

    # Exit confirmed at 110.0 x 10 -> PnL = (110-100)*10 = 100
    exit_broker = FakeBroker(order_id="EXIT-1")
    exit_broker.queue(_filled(110.0, 10, t=datetime(2026, 6, 5, 19, 0, tzinfo=timezone.utc)))
    engine_exit = ExecutionEngine(exit_broker, settings, repo)
    trade = engine_exit.exit_position(pos, "target")

    assert trade is not None
    assert trade.realized_pnl == pytest.approx(100.0)
    assert trade.exit_price == 110.0
    # position now closed, exactly one trade, two fills (entry + exit)
    closed = repo._db.query_one("SELECT status FROM positions WHERE position_id = ?", (pos.position_id,))
    assert closed["status"] == "closed"
    c = _counts(repo)
    assert c["trades"] == 1 and c["fills"] == 2
    # the quality view reports this trade as provably clean
    q = repo._db.query_one("SELECT quality FROM v_trade_quality")
    assert q["quality"] == "clean"


def test_unconfirmed_exit_leaves_position_open(repo, settings):
    entry_broker = FakeBroker(order_id="ENTRY-2")
    entry_broker.queue(_filled(100.0, 10))
    engine = ExecutionEngine(entry_broker, settings, repo)
    pos = engine.enter_position(
        "TSLA", Direction.LONG, 10, strategy_id=STRATEGY, experiment_id=EXPERIMENT
    )

    exit_broker = FakeBroker(order_id="EXIT-2")
    exit_broker.queue(_terminal_unfilled("rejected"))
    engine_exit = ExecutionEngine(exit_broker, settings, repo)
    trade = engine_exit.exit_position(pos, "stop")

    assert trade is None
    still_open = repo._db.query_one(
        "SELECT status FROM positions WHERE position_id = ?", (pos.position_id,)
    )
    assert still_open["status"] == "open", "an unconfirmed exit must leave the position open"
    assert repo._db.query_one("SELECT COUNT(*) AS n FROM trades")["n"] == 0


# ---------------------------------------------------------------------------
# 5. Reconciliation — the broker is the truth
# ---------------------------------------------------------------------------

def test_detect_mismatch_local_only_position():
    local = [SimpleNamespace(symbol="AAPL", direction=Direction.LONG, size=10)]
    result = detect_position_mismatch(local, [])  # broker shows nothing
    assert result.mismatch is True
    assert result.reason == "local_only_position"
    assert result.entries_blocked is True


def test_detect_mismatch_broker_only_position():
    broker_positions = [{"symbol": "AAPL", "side": "long", "qty": 10}]
    result = detect_position_mismatch([], broker_positions)
    assert result.mismatch is True
    assert result.reason == "broker_only_position"


def test_reconciler_clean_when_matching(settings):
    broker = FakeBroker()
    broker.positions = [{"symbol": "AAPL", "side": "long", "qty": 10}]
    reconciler = BrokerReconciler(broker, settings)
    local = [SimpleNamespace(symbol="AAPL", direction=Direction.LONG, size=10)]
    result = reconciler.check(local)
    assert result.mismatch is False
    assert result.reason == "clean"
