"""
The Strategy interface — the seam every Phase 2 strategy plugs into.

This is deliberately EMPTY of real strategies. The foundation stays
strategy-agnostic: it defines what a strategy emits (Signal) and the contract it
implements (Strategy.generate_signals), plus the stable strategy_id /
experiment_id identity that threads through every order, fill, position, and
trade. The actual strategies — the seven the owner chose — are wired in at
Phase 2 without touching this contract.

A strategy NEVER places orders or writes to the database itself. It only reads
market data and emits Signals. The trading loop (Phase 2) is what turns a Signal
into a broker order through the confirmed-state ExecutionEngine, so Article II
holds for every strategy uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from core.trading.models import Direction


class SignalAction(str, Enum):
    """What a strategy is asking the loop to do."""
    ENTER = "enter"
    EXIT = "exit"


@dataclass
class Signal:
    """
    A strategy's intent. Strategy-agnostic and broker-free — the loop, not the
    strategy, decides how/whether to act on it through the ExecutionEngine.

    For ENTER: symbol, direction, and size are required.
    For EXIT:  symbol identifies the position to close; direction/size are unused.
    signal_json carries the strategy's own reasoning (it lands verbatim in the
    provenance-tagged signal_json column).
    """
    symbol: str
    action: SignalAction
    direction: Optional[Direction] = None
    size: Optional[int] = None
    exit_reason: Optional[str] = None
    signal_json: Optional[str] = None

    def __post_init__(self) -> None:
        if self.action == SignalAction.ENTER:
            if self.direction is None or self.size is None:
                raise ValueError("ENTER signals require both direction and size")


class Strategy(ABC):
    """
    Base class for every Olympus strategy.

    Subclasses implement generate_signals(). Each strategy carries a stable
    strategy_id (its identity for the life of the system) and an experiment_id
    (the run/configuration it belongs to). These tags are what separate pooled
    capital by strategy (Principle 4) — every record the loop writes on this
    strategy's behalf is stamped with them.
    """

    def __init__(self, strategy_id: str, experiment_id: str) -> None:
        if not strategy_id:
            raise ValueError("strategy_id is required")
        if not experiment_id:
            raise ValueError("experiment_id is required")
        self._strategy_id = strategy_id
        self._experiment_id = experiment_id

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def experiment_id(self) -> str:
        return self._experiment_id

    @abstractmethod
    def generate_signals(self, market_data: Any) -> list[Signal]:
        """
        Inspect market data and return the signals to act on this cycle.

        Pure and side-effect-free: a strategy must not place orders, mutate
        shared state, or write to the database. Returning [] (no action) is
        always valid. market_data is whatever the Phase 2 loop supplies (e.g.
        recent bars from market_data); the foundation does not constrain it.
        """
        raise NotImplementedError
