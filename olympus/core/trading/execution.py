"""
Confirmed-state order execution for Olympus — the heart of Article II.

This is the repaired phantom-trade fix. Every Position/Trade this module
produces is backed by a real, broker-confirmed fill at the real fill price:

  submit -> poll the broker until the order reaches a TERMINAL status ->
  record ONLY on a confirmed fill, at the broker's filled_avg_price /
  filled_qty / filled_at — never the requested price, the requested qty, or a
  local clock.

If the order is canceled / expired / rejected, or polling times out without
confirmation, NOTHING is recorded except an 'order_unfilled' system_event, and
the method returns cleanly so the trading loop continues. Submission failures
emit an 'order_submission_failed' event. The methods never raise.

The fill-confirmation internals (_poll_order, _build_filled_outcome,
_confirm_fill) are ported near-verbatim from the stabilized old Olympus — the
proven core. What changed for the foundation: results are persisted through the
strategy-agnostic Repository (orders, fills, positions, trades), and every row
is stamped with strategy_id / experiment_id / environment. No ranker concepts.
"""

from __future__ import annotations

import concurrent.futures
import time
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from core.broker.alpaca import AlpacaClient
from core.db.repository import Repository
from core.logger import get_logger
from core.trading.models import (
    Direction,
    Fill,
    Order,
    OrderIntent,
    Position,
    Side,
    Trade,
)

logger = get_logger(__name__)

# Shared pool for fill-confirmation polling, giving each confirmation a hard
# wall-clock ceiling via Future.result(timeout=...).
_FILL_POLL_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=16, thread_name_prefix="fill-confirm"
)

# Alpaca order statuses that are NOT terminal — keep polling while in these.
# Everything else that is not 'filled' is treated as terminal-not-filled.
_NON_TERMINAL_STATUSES = frozenset({
    "new", "accepted", "pending_new", "partially_filled",
    "pending_replace", "pending_cancel", "accepted_for_bidding", "held",
})


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Coerce a broker-supplied datetime to a tz-aware UTC datetime, or None."""
    if not isinstance(dt, datetime):
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class _FillOutcome:
    """
    Result of confirming an order against the broker.

    filled=True  -> fill_price / fill_qty / fill_time are all broker-truth and a
                    trade may be recorded.
    filled=False -> no confirmed, fully-described fill; record nothing.
    """
    filled: bool
    status: str
    fill_price: Optional[float] = None
    fill_qty: Optional[int] = None
    fill_time: Optional[datetime] = None
    reason: str = ""


class ExecutionEngine:
    """
    Submits paper orders and confirms their fills before any state is recorded.

    enter_position() — market entry; on a confirmed fill records the order, the
                       fill, and an open Position (broker-truth values). Returns
                       the Position, or None if unconfirmed.
    exit_position()  — counter-side market exit; on a confirmed fill records the
                       order, the fill, closes the Position, and records a Trade.
                       Returns the Trade, or None if unconfirmed (position stays
                       open; the loop retries next cycle).
    """

    def __init__(self, alpaca_client: AlpacaClient, settings, repository: Repository) -> None:
        self._alpaca = alpaca_client
        self._settings = settings
        self._repo = repository
        self._environment = getattr(settings, "ENVIRONMENT", "paper")
        logger.info("ExecutionEngine initialized (environment=%s)", self._environment)

    # ------------------------------------------------------------------
    # Fill confirmation (the proven Article II core)
    # ------------------------------------------------------------------

    def _poll_order(self, order_id: str) -> _FillOutcome:
        """
        Poll AlpacaClient.get_order() on the configured backoff schedule until
        the order reaches a terminal state. Never raises — a broker lookup
        failure is treated as 'keep polling'; an exhausted schedule is a timeout.
        """
        backoff = self._settings.FILL_CONFIRM_BACKOFF
        last_status = "unknown"
        last_order: Optional[dict] = None

        for wait in backoff:
            time.sleep(float(wait))
            order = self._alpaca.get_order(order_id)
            if order is None:
                continue  # transient broker lookup failure — keep polling
            last_order = order
            last_status = str(order.get("status") or "unknown").lower()

            if last_status == "filled":
                return self._build_filled_outcome(order, last_status)
            if last_status not in _NON_TERMINAL_STATUSES:
                # canceled / expired / rejected / other terminal: did NOT happen.
                return _FillOutcome(
                    filled=False, status=last_status,
                    reason=f"terminal_not_filled:{last_status}",
                )
            # non-terminal — keep polling

        # Schedule exhausted. Accept a genuine partial fill, but only if the
        # broker confirms shares, an average price, AND a fill timestamp.
        if last_order is not None:
            outcome = self._build_filled_outcome(last_order, last_status)
            if outcome.filled:
                return outcome
        return _FillOutcome(filled=False, status=last_status, reason="timeout_unconfirmed")

    @staticmethod
    def _build_filled_outcome(order: dict, status: str) -> _FillOutcome:
        """
        Extract broker-truth fill fields. Refuses to declare a fill if
        filled_avg_price, filled_qty, or filled_at is missing — there is NO
        fallback to planned prices, requested quantities, or a local clock.
        """
        fill_price = order.get("filled_avg_price")
        fill_qty = order.get("filled_qty")
        fill_time = _to_utc(order.get("filled_at"))
        if fill_price is None or not fill_qty or fill_time is None:
            return _FillOutcome(
                filled=False, status=status,
                reason=(
                    "missing_broker_truth("
                    f"price={fill_price}, qty={fill_qty}, "
                    f"time={'set' if fill_time is not None else 'none'})"
                ),
            )
        return _FillOutcome(
            filled=True, status=status,
            fill_price=float(fill_price),
            fill_qty=int(fill_qty),
            fill_time=fill_time,
            reason="filled" if status == "filled" else "accepted_partial_fill",
        )

    def _confirm_fill(self, order_id: str) -> _FillOutcome:
        """Confirm a fill via the shared poll pool, under a hard wall-clock ceiling."""
        backoff = self._settings.FILL_CONFIRM_BACKOFF
        hard_ceiling = float(sum(backoff)) + 5.0  # +5s margin for HTTP latency
        future = _FILL_POLL_POOL.submit(self._poll_order, order_id)
        try:
            return future.result(timeout=hard_ceiling)
        except concurrent.futures.TimeoutError:
            future.cancel()
            logger.warning(
                "fill-confirm: order %s exceeded %.1fs hard ceiling — unconfirmed",
                order_id[:8], hard_ceiling,
            )
            return _FillOutcome(filled=False, status="unknown", reason="hard_ceiling_exceeded")

    # ------------------------------------------------------------------
    # Event recording (everything Olympus tried to do)
    # ------------------------------------------------------------------

    def _record_order_intent(
        self,
        order_id: str,
        *,
        strategy_id: str,
        experiment_id: str,
        symbol: str,
        side: str,
        qty: int,
        intent: OrderIntent,
        broker_status: Optional[str],
        signal_json: Optional[str],
    ) -> None:
        self._repo.record_order(Order(
            order_id=order_id,
            strategy_id=strategy_id,
            experiment_id=experiment_id,
            environment=self._environment,
            symbol=symbol,
            side=Side(side),
            requested_qty=qty,
            intent=intent,
            broker_status=broker_status,
            signal_json=signal_json,
        ))

    def _write_unfilled_event(
        self, *, strategy_id, experiment_id, symbol, side, requested_qty,
        order_id, alpaca_status, reason,
    ) -> None:
        logger.warning(
            "ORDER UNFILLED %s %s qty=%d — status=%s reason=%s order=%s; no trade recorded",
            side.upper(), symbol, requested_qty, alpaca_status, reason,
            (order_id[:8] if order_id else "none"),
        )
        self._repo.write_event(
            "order_unfilled",
            f"Order not confirmed filled: {side} {requested_qty} {symbol} ({alpaca_status})",
            environment=self._environment,
            strategy_id=strategy_id, experiment_id=experiment_id, symbol=symbol,
            metadata={
                "side": side, "requested_qty": int(requested_qty),
                "order_id": order_id, "alpaca_status": alpaca_status, "reason": reason,
            },
        )

    def _write_submission_failed_event(
        self, *, strategy_id, experiment_id, symbol, side, requested_qty, exc,
    ) -> None:
        self._repo.write_event(
            "order_submission_failed",
            f"Order submission failed: {side} {requested_qty} {symbol}",
            environment=self._environment,
            strategy_id=strategy_id, experiment_id=experiment_id, symbol=symbol,
            metadata={
                "side": side, "requested_qty": int(requested_qty),
                "error_class": type(exc).__name__, "error_message": str(exc),
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enter_position(
        self,
        symbol: str,
        direction: Direction,
        size: int,
        *,
        strategy_id: str,
        experiment_id: str,
        signal_json: Optional[str] = None,
    ) -> Optional[Position]:
        """
        Place a market entry and confirm the fill before returning. Returns a
        Position built from broker-truth values on a confirmed fill; returns None
        (and emits 'order_unfilled') if the order is not confirmed. Never raises.
        """
        side = "buy" if direction == Direction.LONG else "sell"
        try:
            order_info = self._alpaca.submit_market_order(symbol, size, side)
            order_id = order_info.get("order_id")
            if not order_id:
                self._write_unfilled_event(
                    strategy_id=strategy_id, experiment_id=experiment_id,
                    symbol=symbol, side=side, requested_qty=size, order_id=None,
                    alpaca_status="no_order_id", reason="submit returned no order_id",
                )
                return None

            # Record the order as INTENT before we know the outcome.
            self._record_order_intent(
                order_id, strategy_id=strategy_id, experiment_id=experiment_id,
                symbol=symbol, side=side, qty=size, intent=OrderIntent.ENTRY,
                broker_status=order_info.get("status"), signal_json=signal_json,
            )

            outcome = self._confirm_fill(order_id)
            self._repo.update_order_status(order_id, outcome.status)
            if not outcome.filled:
                self._write_unfilled_event(
                    strategy_id=strategy_id, experiment_id=experiment_id,
                    symbol=symbol, side=side, requested_qty=size, order_id=order_id,
                    alpaca_status=outcome.status, reason=outcome.reason,
                )
                return None

            # --- Broker-truth only ---
            fill = Fill(
                fill_id=str(uuid.uuid4()), order_id=order_id,
                strategy_id=strategy_id, experiment_id=experiment_id,
                environment=self._environment, symbol=symbol, side=Side(side),
                fill_price=outcome.fill_price, fill_qty=outcome.fill_qty,
                fill_time=outcome.fill_time,
            )
            self._repo.record_fill(fill)

            position = Position(
                position_id=str(uuid.uuid4()),
                strategy_id=strategy_id, experiment_id=experiment_id,
                environment=self._environment, symbol=symbol, direction=direction,
                entry_price=outcome.fill_price, size=outcome.fill_qty,
                entry_order_id=order_id, entry_fill_id=fill.fill_id,
                entry_time=outcome.fill_time, signal_json=signal_json,
            )
            self._repo.open_position(position)

            logger.info(
                "ENTER %s %s | size=%d entry=%.4f order=%s status=%s",
                direction.value.upper(), symbol, outcome.fill_qty,
                outcome.fill_price, order_id[:8], outcome.status,
            )
            return position

        except Exception as exc:
            self._write_submission_failed_event(
                strategy_id=strategy_id, experiment_id=experiment_id,
                symbol=symbol, side=side, requested_qty=size, exc=exc,
            )
            logger.error(
                "enter_position failed — %s %s size=%d:\n%s",
                direction.value.upper(), symbol, size, traceback.format_exc(),
            )
            return None

    def exit_position(
        self,
        position: Position,
        exit_reason: str,
        *,
        signal_json: Optional[str] = None,
    ) -> Optional[Trade]:
        """
        Place a counter-side market exit and confirm the fill before returning.
        Returns a Trade built from broker-truth values on a confirmed fill;
        returns None (and emits 'order_unfilled', position stays open) if the
        order is not confirmed. Never raises.

        exit_reason is free-form (e.g. "stop", "target", "rotation", "manual",
        "eod_close") — the foundation does not constrain a strategy's vocabulary.
        """
        side = "sell" if position.direction == Direction.LONG else "buy"
        try:
            order_info = self._alpaca.submit_market_order(position.symbol, position.size, side)
            order_id = order_info.get("order_id")
            if not order_id:
                self._write_unfilled_event(
                    strategy_id=position.strategy_id, experiment_id=position.experiment_id,
                    symbol=position.symbol, side=side, requested_qty=position.size,
                    order_id=None, alpaca_status="no_order_id",
                    reason="submit returned no order_id",
                )
                return None

            self._record_order_intent(
                order_id, strategy_id=position.strategy_id,
                experiment_id=position.experiment_id, symbol=position.symbol,
                side=side, qty=position.size, intent=OrderIntent.EXIT,
                broker_status=order_info.get("status"), signal_json=signal_json,
            )

            outcome = self._confirm_fill(order_id)
            self._repo.update_order_status(order_id, outcome.status)
            if not outcome.filled:
                # Exit not confirmed — record nothing; position stays open.
                self._write_unfilled_event(
                    strategy_id=position.strategy_id, experiment_id=position.experiment_id,
                    symbol=position.symbol, side=side, requested_qty=position.size,
                    order_id=order_id, alpaca_status=outcome.status, reason=outcome.reason,
                )
                return None

            fill_price = outcome.fill_price
            fill_qty = outcome.fill_qty
            exit_time = outcome.fill_time

            if fill_qty != position.size:
                logger.warning(
                    "EXIT partial %s %s — requested %d, filled %d (residual %d to reconciler)",
                    position.direction.value.upper(), position.symbol,
                    position.size, fill_qty, position.size - fill_qty,
                )

            exit_fill = Fill(
                fill_id=str(uuid.uuid4()), order_id=order_id,
                strategy_id=position.strategy_id, experiment_id=position.experiment_id,
                environment=self._environment, symbol=position.symbol, side=Side(side),
                fill_price=fill_price, fill_qty=fill_qty, fill_time=exit_time,
            )
            self._repo.record_fill(exit_fill)

            # Realized P&L on broker-confirmed fill price and filled quantity only.
            if position.direction == Direction.LONG:
                realized_pnl = (fill_price - position.entry_price) * fill_qty
            else:
                realized_pnl = (position.entry_price - fill_price) * fill_qty

            hold_minutes = (exit_time - position.entry_time).total_seconds() / 60.0

            self._repo.close_position(
                position.position_id, exit_order_id=order_id,
                exit_fill_id=exit_fill.fill_id, exit_time=exit_time,
            )

            trade = Trade(
                trade_id=str(uuid.uuid4()), position_id=position.position_id,
                strategy_id=position.strategy_id, experiment_id=position.experiment_id,
                environment=self._environment, symbol=position.symbol,
                direction=position.direction, entry_price=position.entry_price,
                exit_price=fill_price, size=fill_qty, entry_time=position.entry_time,
                exit_time=exit_time, hold_duration_minutes=hold_minutes,
                realized_pnl=realized_pnl, exit_reason=exit_reason,
                entry_order_id=position.entry_order_id, exit_order_id=order_id,
                entry_fill_id=position.entry_fill_id, exit_fill_id=exit_fill.fill_id,
                signal_json=signal_json,
            )
            self._repo.record_trade(trade)

            logger.info(
                "EXIT %s %s | exit=%.4f reason=%s pnl=%.2f hold=%.1fmin order=%s status=%s",
                position.direction.value.upper(), position.symbol, fill_price,
                exit_reason, realized_pnl, hold_minutes, order_id[:8], outcome.status,
            )
            return trade

        except Exception as exc:
            self._write_submission_failed_event(
                strategy_id=position.strategy_id, experiment_id=position.experiment_id,
                symbol=position.symbol, side=side, requested_qty=position.size, exc=exc,
            )
            logger.error(
                "exit_position failed — %s %s reason=%s:\n%s",
                position.direction.value.upper(), position.symbol, exit_reason,
                traceback.format_exc(),
            )
            return None
