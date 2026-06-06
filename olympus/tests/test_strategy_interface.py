"""
Tests for the Strategy interface (Step 4).

Proves the contract is sound and, crucially, that a strategy's strategy_id /
experiment_id thread end-to-end through the confirmed-state ExecutionEngine onto
every recorded order / fill / position / trade — the tag plumbing that separates
pooled capital by strategy (Principle 4). No real strategy exists; a no-op test
double stands in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.db.database import Database
from core.db.repository import Repository
from core.trading.execution import ExecutionEngine
from core.trading.models import Direction
from core.strategy.base import Signal, SignalAction, Strategy


class NoOpStrategy(Strategy):
    """A minimal strategy double: emits whatever signals it is handed."""

    def __init__(self, strategy_id, experiment_id, signals=None):
        super().__init__(strategy_id, experiment_id)
        self._signals = signals or []

    def generate_signals(self, market_data):
        return list(self._signals)


# --- Fakes mirrored from the execution suite (kept local for isolation) ---

class FakeBroker:
    def __init__(self, order_id="ORD-1"):
        self._order_id = order_id
        self._responses = []

    def queue(self, *r):
        self._responses = list(r)

    def submit_market_order(self, symbol, qty, side):
        return {"order_id": self._order_id, "symbol": symbol, "qty": qty,
                "side": side, "status": "accepted", "filled_avg_price": None}

    def get_order(self, order_id):
        return self._responses[0] if self._responses else None


@pytest.fixture
def settings():
    return SimpleNamespace(FILL_CONFIRM_BACKOFF=(0.0,), ENVIRONMENT="paper")


@pytest.fixture
def repo(tmp_path: Path):
    db = Database(tmp_path / "strat.db")
    db.initialize()
    yield Repository(db)
    db.close()


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy("s1", "e1")  # cannot instantiate the ABC directly


def test_strategy_requires_ids():
    with pytest.raises(ValueError):
        NoOpStrategy("", "e1")
    with pytest.raises(ValueError):
        NoOpStrategy("s1", "")


def test_enter_signal_requires_direction_and_size():
    with pytest.raises(ValueError):
        Signal(symbol="AAPL", action=SignalAction.ENTER)  # missing direction/size


def test_strategy_emits_signals():
    sig = Signal(symbol="AAPL", action=SignalAction.ENTER,
                 direction=Direction.LONG, size=10)
    strat = NoOpStrategy("momentum_v1", "exp1", signals=[sig])
    out = strat.generate_signals(market_data=None)
    assert out == [sig]


def test_strategy_id_threads_through_to_records(repo, settings):
    """The strategy's tags must land on every record the engine writes."""
    sig = Signal(symbol="AAPL", action=SignalAction.ENTER,
                 direction=Direction.LONG, size=10, signal_json='{"reason":"test"}')
    strat = NoOpStrategy("momentum_v1", "exp_alpha", signals=[sig])

    broker = FakeBroker()
    broker.queue({
        "status": "filled", "filled_avg_price": 100.0, "filled_qty": 10,
        "filled_at": datetime(2026, 6, 5, 18, 0, tzinfo=timezone.utc),
    })
    engine = ExecutionEngine(broker, settings, repo)

    # The loop (simulated here) drives the engine using the strategy's identity.
    signal = strat.generate_signals(market_data=None)[0]
    pos = engine.enter_position(
        signal.symbol, signal.direction, signal.size,
        strategy_id=strat.strategy_id, experiment_id=strat.experiment_id,
        signal_json=signal.signal_json,
    )

    assert pos is not None
    for table in ("orders", "fills", "positions"):
        row = repo._db.query_one(f"SELECT strategy_id, experiment_id, environment FROM {table}")
        assert row["strategy_id"] == "momentum_v1"
        assert row["experiment_id"] == "exp_alpha"
        assert row["environment"] == "paper"
    # the strategy's reasoning was persisted verbatim
    order = repo._db.query_one("SELECT signal_json FROM orders")
    assert order["signal_json"] == '{"reason":"test"}'
