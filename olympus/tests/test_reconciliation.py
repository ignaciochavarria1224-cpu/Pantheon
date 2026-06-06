"""
Tests for the broker reconciler — the broker is always the truth (Article II).

Covers mismatch detection (symbol set + quantity/side), the clean case, and the
paper-guarded repair path (repair is refused unless explicitly enabled, and is
forbidden entirely outside paper mode).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.trading.models import Direction
from core.trading.reconciliation import BrokerReconciler, detect_position_mismatch


class FakeBroker:
    def __init__(self):
        self.positions = []
        self.open_orders = []
        self.cancel_called = False
        self.close_called = False

    def get_positions(self):
        return self.positions

    def get_open_orders(self):
        return self.open_orders

    def cancel_all_orders(self):
        self.cancel_called = True
        return True

    def close_all_positions(self, cancel_orders=True):
        self.close_called = True
        return True


def _local(symbol, size, direction=Direction.LONG):
    return SimpleNamespace(symbol=symbol, direction=direction, size=size)


def test_clean_when_local_matches_broker():
    result = detect_position_mismatch(
        [_local("AAPL", 10)],
        [{"symbol": "AAPL", "side": "long", "qty": 10}],
    )
    assert result.mismatch is False
    assert result.reason == "clean"
    assert result.entries_blocked is False


def test_quantity_mismatch_blocks_entries():
    result = detect_position_mismatch(
        [_local("AAPL", 10)],
        [{"symbol": "AAPL", "side": "long", "qty": 7}],
    )
    assert result.mismatch is True
    assert result.reason == "quantity_or_side_mismatch"
    assert result.entries_blocked is True


def test_side_mismatch_detected():
    result = detect_position_mismatch(
        [_local("AAPL", 10, Direction.LONG)],
        [{"symbol": "AAPL", "side": "short", "qty": 10}],
    )
    assert result.mismatch is True
    assert result.reason == "quantity_or_side_mismatch"


def test_repair_refused_when_disabled():
    settings = SimpleNamespace(
        ALPACA_PAPER=True,
        OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS=False,
        OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH=True,
    )
    broker = FakeBroker()
    broker.positions = [{"symbol": "AAPL", "side": "long", "qty": 10}]
    reconciler = BrokerReconciler(broker, settings)

    result = reconciler.check_and_repair([])  # local empty, broker has AAPL
    assert result.mismatch is True
    assert result.repair_attempted is False
    assert broker.cancel_called is False
    assert broker.close_called is False


def test_repair_runs_when_enabled_in_paper():
    settings = SimpleNamespace(
        ALPACA_PAPER=True,
        OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS=True,
        OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH=True,
    )
    broker = FakeBroker()
    broker.positions = [{"symbol": "AAPL", "side": "long", "qty": 10}]
    reconciler = BrokerReconciler(broker, settings)

    result = reconciler.check_and_repair([])
    assert result.repair_attempted is True
    assert result.repair_succeeded is True
    assert broker.cancel_called is True
    assert broker.close_called is True


def test_repair_forbidden_outside_paper():
    settings = SimpleNamespace(
        ALPACA_PAPER=False,
        OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS=True,
        OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH=True,
    )
    broker = FakeBroker()
    broker.positions = [{"symbol": "AAPL", "side": "long", "qty": 10}]
    reconciler = BrokerReconciler(broker, settings)
    with pytest.raises(RuntimeError):
        reconciler.check_and_repair([])
