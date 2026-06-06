"""
Alpaca broker client for Olympus — paper trading only.

Ported from the stabilized old Olympus (core/broker/alpaca.py), trimmed to the
methods the Phase 1 spine needs. A hard guard refuses to construct in live mode,
and a credentials check refuses to construct without Alpaca keys. The broker is
the source of truth (Article II): get_order returns the broker's
filled_avg_price / filled_qty / filled_at, which are the only values the
ExecutionEngine will ever record.
"""

from __future__ import annotations

import concurrent.futures
import time
from datetime import datetime, timezone
from typing import Any, Optional

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from config.settings import settings as _default_settings
from core.logger import get_logger

logger = get_logger(__name__)


class LiveTradingGuardError(RuntimeError):
    """Raised if someone attempts to initialize a live (non-paper) trading client."""


class AlpacaClient:
    """Authenticated Alpaca trading client (paper only)."""

    def __init__(self, settings=None) -> None:
        self._settings = settings or _default_settings

        # --- Hard guard: refuse to initialize in live mode ---
        if not self._settings.ALPACA_PAPER:
            raise LiveTradingGuardError(
                "ALPACA_PAPER=False is set, but live trading is not enabled in this "
                "phase. Set ALPACA_PAPER=true in your .env to use the paper client."
            )
        # --- Refuse without credentials (raises MissingCredentialsError) ---
        self._settings.require_broker_credentials()

        self._client = TradingClient(
            api_key=self._settings.ALPACA_API_KEY,
            secret_key=self._settings.ALPACA_SECRET_KEY,
            paper=True,
        )
        self._last_successful_healthcheck: Optional[str] = None
        logger.info("AlpacaClient initialized (paper=True)")

    # ------------------------------------------------------------------
    # Account / connectivity
    # ------------------------------------------------------------------

    def get_account(self) -> dict[str, Any]:
        """Return equity, buying_power, status, currency. Raises on failure."""
        try:
            acct = self._client.get_account()
            result = {
                "equity": float(acct.equity),
                "buying_power": float(acct.buying_power),
                "status": str(acct.status.value),
                "currency": str(acct.currency),
                "account_number": str(acct.account_number),
            }
            logger.info(
                "Account: equity=$%.2f, buying_power=$%.2f, status=%s",
                result["equity"], result["buying_power"], result["status"],
            )
            return result
        except Exception as exc:
            logger.error("AlpacaClient.get_account() failed: %s", exc)
            raise

    def healthcheck(self) -> dict[str, Any]:
        """
        Lightweight broker connectivity + account-state probe under a hard
        timeout, so a hung broker call cannot stall a cycle.
        """
        checked_at = datetime.now(timezone.utc).isoformat()
        timeout = float(getattr(self._settings, "BROKER_HEALTHCHECK_TIMEOUT_SECONDS", 5.0))

        def _probe() -> dict[str, Any]:
            acct = self._client.get_account()
            return {
                "status": str(acct.status.value) if acct.status else "unknown",
                "account_blocked": bool(getattr(acct, "account_blocked", False)),
                "trading_blocked": bool(getattr(acct, "trading_blocked", False)),
            }

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                info = ex.submit(_probe).result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            reason = f"healthcheck timed out after {timeout:.0f}s"
            logger.warning("healthcheck: %s", reason)
            return {"healthy": False, "reason": reason, "checked_at": checked_at,
                    "last_successful_check": self._last_successful_healthcheck}
        except Exception as exc:
            reason = f"broker unreachable: {exc}"
            logger.warning("healthcheck: %s", reason)
            return {"healthy": False, "reason": reason, "checked_at": checked_at,
                    "last_successful_check": self._last_successful_healthcheck}

        if info["account_blocked"] or info["trading_blocked"] or info["status"] != "ACTIVE":
            reason = (
                f"account not tradeable (status={info['status']}, "
                f"account_blocked={info['account_blocked']}, "
                f"trading_blocked={info['trading_blocked']})"
            )
            logger.warning("healthcheck: %s", reason)
            return {"healthy": False, "reason": reason, "checked_at": checked_at,
                    "last_successful_check": self._last_successful_healthcheck}

        self._last_successful_healthcheck = checked_at
        return {"healthy": True, "reason": "ok", "checked_at": checked_at,
                "last_successful_check": checked_at}

    def is_market_open(self) -> bool:
        """Return True if the US equity market is currently open."""
        try:
            return bool(self._client.get_clock().is_open)
        except Exception as exc:
            logger.error("AlpacaClient.is_market_open() failed: %s", exc)
            raise

    def get_clock(self) -> dict[str, Any]:
        """Return current market clock: timestamp, is_open, next_open, next_close."""
        try:
            clock = self._client.get_clock()
            return {
                "timestamp": clock.timestamp,
                "is_open": bool(clock.is_open),
                "next_open": clock.next_open,
                "next_close": clock.next_close,
            }
        except Exception as exc:
            logger.error("AlpacaClient.get_clock() failed: %s", exc)
            raise

    def ping(self) -> tuple[bool, float]:
        """Connectivity check. Returns (success, latency_ms). Never raises."""
        t0 = time.monotonic()
        try:
            self._client.get_clock()
            latency_ms = (time.monotonic() - t0) * 1000
            logger.info("Alpaca ping OK — latency=%.1fms", latency_ms)
            return True, latency_ms
        except Exception as exc:
            logger.error("Alpaca ping FAILED: %s", exc)
            return False, -1.0

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def submit_market_order(self, symbol: str, qty: int, side: str) -> dict[str, Any]:
        """
        Submit a market order to the paper account. Returns a dict with order_id,
        symbol, qty, side, status, filled_avg_price. Raises on failure.
        """
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=symbol.upper(), qty=qty, side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        try:
            order = self._client.submit_order(order_data=req)
            result = {
                "order_id": str(order.id),
                "symbol": str(order.symbol),
                "qty": int(float(order.qty)) if order.qty is not None else qty,
                "side": side.lower(),
                "status": str(order.status.value) if order.status else "unknown",
                "filled_avg_price": (
                    float(order.filled_avg_price)
                    if order.filled_avg_price is not None else None
                ),
            }
            logger.info(
                "Order submitted: %s %d %s — id=%s status=%s",
                side.upper(), qty, symbol, result["order_id"][:8], result["status"],
            )
            return result
        except Exception as exc:
            logger.error("submit_market_order failed: %s %d %s — %s", side.upper(), qty, symbol, exc)
            raise

    def get_order(self, order_id: str) -> Optional[dict[str, Any]]:
        """
        Get details for a specific order by id. Returns None if not found / on
        API rejection. The returned dict carries the broker-truth fill fields:
        filled_avg_price, filled_qty, filled_at.
        """
        try:
            order = self._client.get_order_by_id(order_id)
            return {
                "order_id": str(order.id),
                "client_order_id": str(order.client_order_id) if order.client_order_id else None,
                "symbol": str(order.symbol),
                "qty": int(float(order.qty)) if order.qty is not None else None,
                "filled_qty": int(float(order.filled_qty)) if order.filled_qty is not None else None,
                "side": str(order.side.value) if order.side else None,
                "type": str(order.type.value) if order.type else None,
                "status": str(order.status.value) if order.status else None,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price is not None else None,
                "submitted_at": order.submitted_at,
                "filled_at": order.filled_at,
                "expired_at": order.expired_at,
                "canceled_at": order.canceled_at,
            }
        except APIError as exc:
            logger.info("get_order_by_id(%s) not found / API rejection: %s", order_id, exc)
            return None
        except Exception as exc:
            logger.error("get_order_by_id(%s) unexpected failure: %s", order_id, exc, exc_info=True)
            return None

    def get_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        """Return all open (pending) orders, optionally filtered by symbol."""
        try:
            params = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                symbols=[symbol.upper()] if symbol else None,
            )
            orders = self._client.get_orders(filter=params)
            return [
                {
                    "order_id": str(o.id),
                    "symbol": str(o.symbol),
                    "side": str(o.side.value) if o.side else "unknown",
                    "status": str(o.status.value) if o.status else "unknown",
                }
                for o in orders
            ]
        except Exception as exc:
            logger.error("get_open_orders failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Positions / reconciliation helpers
    # ------------------------------------------------------------------

    def get_positions(self) -> list[dict[str, Any]]:
        """Return all current open positions in the paper account. [] on failure."""
        try:
            positions = self._client.get_all_positions()
            result = []
            for pos in positions:
                result.append({
                    "symbol": str(pos.symbol),
                    "qty": float(pos.qty) if pos.qty is not None else 0.0,
                    "side": str(pos.side.value) if pos.side else "unknown",
                    "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0.0,
                    "current_price": float(pos.current_price) if pos.current_price else None,
                    "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0.0,
                })
            logger.debug("get_positions: %d open position(s)", len(result))
            return result
        except Exception as exc:
            logger.error("get_positions failed: %s", exc)
            return []

    def cancel_all_orders(self) -> bool:
        """Cancel all open orders. True on success."""
        try:
            responses = self._client.cancel_orders()
            logger.info("Cancelled %d open Alpaca order(s)", len(responses))
            return True
        except Exception as exc:
            logger.error("cancel_all_orders failed: %s", exc)
            return False

    def close_all_positions(self, cancel_orders: bool = True) -> bool:
        """Liquidate all open positions (paper fail-safe). True if accepted."""
        try:
            responses = self._client.close_all_positions(cancel_orders=cancel_orders)
            logger.warning(
                "Broker fail-safe liquidation submitted for %d position(s)", len(responses)
            )
            return True
        except Exception as exc:
            logger.error("close_all_positions failed: %s", exc)
            return False
