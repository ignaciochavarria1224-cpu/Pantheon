"""
Market data fetcher for Olympus.
Uses alpaca-py to fetch latest and historical OHLCV bars. Handles batch requests,
timezone conversion, market-hours filtering, and retries.

Ported from the stabilized old Olympus, adapted to the lean Phase 1 settings and
to refuse construction without credentials (so unit tests that don't touch the
network never need keys).
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, Union

import pandas as pd
import pytz
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from config.settings import settings as _default_settings
from core.logger import get_logger

logger = get_logger(__name__)

_ET = pytz.timezone("America/New_York")
_UTC = pytz.utc

_MAX_BATCH_SIZE = 200
_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY = 1.0  # seconds — doubles on each retry


def _parse_timeframe(tf_str: str) -> TimeFrame:
    """Convert a human-readable timeframe string to an alpaca-py TimeFrame."""
    tf_map: dict[str, TimeFrame] = {
        "1min": TimeFrame(1, TimeFrameUnit.Minute),
        "5min": TimeFrame(5, TimeFrameUnit.Minute),
        "15min": TimeFrame(15, TimeFrameUnit.Minute),
        "30min": TimeFrame(30, TimeFrameUnit.Minute),
        "1hour": TimeFrame(1, TimeFrameUnit.Hour),
        "1day": TimeFrame(1, TimeFrameUnit.Day),
    }
    key = tf_str.lower().replace(" ", "")
    if key not in tf_map:
        raise ValueError(
            f"Unsupported timeframe '{tf_str}'. Supported: {list(tf_map.keys())}"
        )
    return tf_map[key]


def _flatten_bars_response(bars_response) -> pd.DataFrame:
    """Convert an alpaca-py StockBarsResponse into a flat DataFrame."""
    try:
        raw_df = bars_response.df
    except Exception:
        raw_df = None
    if raw_df is None or (hasattr(raw_df, "empty") and raw_df.empty):
        return pd.DataFrame()
    df = raw_df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    if "symbol" not in df.columns and "level_0" in df.columns:
        df = df.rename(columns={"level_0": "symbol"})
    return df


def _to_et(ts: pd.Series) -> pd.Series:
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC")
    return ts.dt.tz_convert(_ET)


def _filter_market_hours(df: pd.DataFrame, market_open: str, market_close: str) -> pd.DataFrame:
    if df.empty or "timestamp" not in df.columns:
        return df
    open_h, open_m = map(int, market_open.split(":"))
    close_h, close_m = map(int, market_close.split(":"))
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m

    def _in_market(ts: datetime) -> bool:
        bar_minutes = ts.hour * 60 + ts.minute
        return open_minutes <= bar_minutes < close_minutes

    return df[df["timestamp"].apply(_in_market)].reset_index(drop=True)


def _retry(fn, *args, attempts=_RETRY_ATTEMPTS, base_delay=_RETRY_BASE_DELAY, **kwargs):
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Attempt %d/%d failed: %s — retrying in %.1fs", attempt, attempts, exc, delay
            )
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


class DataFetcher:
    """Fetches market data from Alpaca. Requires credentials at construction."""

    def __init__(self, settings=None) -> None:
        self._settings = settings or _default_settings
        self._settings.require_broker_credentials()
        self._client = StockHistoricalDataClient(
            api_key=self._settings.ALPACA_API_KEY,
            secret_key=self._settings.ALPACA_SECRET_KEY,
        )
        self._feed = self._settings.DATA_FEED
        logger.info("DataFetcher initialized (feed=%s)", self._feed)

    def fetch_latest_bars(self, symbols: Union[str, list[str]]) -> pd.DataFrame:
        """Fetch the latest available bar for each symbol."""
        if isinstance(symbols, str):
            symbols = [symbols]
        symbols = [s.upper() for s in symbols]
        logger.info("Fetching latest bars for %d symbol(s)", len(symbols))

        def _do_fetch():
            req = StockLatestBarRequest(symbol_or_symbols=symbols, feed=self._feed)
            return self._client.get_stock_latest_bar(req)

        response = _retry(_do_fetch)
        rows = []
        for sym, bar in response.items():
            rows.append({
                "symbol": sym,
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
                "vwap": float(bar.vwap) if bar.vwap is not None else None,
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df["timestamp"] = _to_et(df["timestamp"])
        logger.info("fetch_latest_bars: got %d bars", len(df))
        return df

    def fetch_historical_bars(
        self,
        symbols: Union[str, list[str]],
        start: datetime,
        end: Optional[datetime] = None,
        timeframe: Optional[str] = None,
        filter_market_hours: bool = True,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV bars for one or more symbols."""
        if isinstance(symbols, str):
            symbols = [symbols]
        symbols = [s.upper() for s in symbols]
        if end is None:
            end = datetime.now(_UTC)
        if timeframe is None:
            timeframe = self._settings.BAR_TIMEFRAME
        alpaca_tf = _parse_timeframe(timeframe)

        logger.info(
            "Fetching historical bars: %d symbol(s), %s -> %s, tf=%s",
            len(symbols), start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), timeframe,
        )

        all_frames: list[pd.DataFrame] = []
        for batch_start in range(0, len(symbols), _MAX_BATCH_SIZE):
            batch = symbols[batch_start: batch_start + _MAX_BATCH_SIZE]

            def _do_fetch(b=batch):
                req = StockBarsRequest(
                    symbol_or_symbols=b, timeframe=alpaca_tf,
                    start=start, end=end, feed=self._feed,
                )
                return self._client.get_stock_bars(req)

            batch_df = _flatten_bars_response(_retry(_do_fetch))
            if not batch_df.empty:
                all_frames.append(batch_df)

        if not all_frames:
            logger.warning("fetch_historical_bars: no data returned")
            return pd.DataFrame()

        df = pd.concat(all_frames, ignore_index=True)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df["timestamp"] = _to_et(df["timestamp"])
        if "vwap" not in df.columns:
            df["vwap"] = None
        if filter_market_hours and timeframe.lower() not in ("1day",):
            before = len(df)
            df = _filter_market_hours(df, self._settings.MARKET_OPEN, self._settings.MARKET_CLOSE)
            logger.debug("Market-hours filter: %d -> %d bars", before, len(df))

        logger.info("fetch_historical_bars: got %d total bars", len(df))
        return df
