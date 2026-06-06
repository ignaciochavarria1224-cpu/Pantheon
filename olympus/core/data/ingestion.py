"""
Market-data ingestion for Olympus — the "reliably collecting data" milestone.

A thin wrapper that fetches the watchlist and upserts the bars into market_data.
Strategy-agnostic: it computes no features and no scores; it only collects clean,
de-duplicated market truth. Idempotency comes from the repository's
INSERT OR IGNORE on (symbol, timeframe, timestamp), so a re-run never creates
duplicate rows.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from core.data.normalizer import normalize_bars
from core.db.repository import Repository
from core.logger import get_logger

logger = get_logger(__name__)


class MarketDataIngestion:
    """Fetch -> normalize -> idempotently upsert OHLCV bars for the watchlist."""

    def __init__(self, fetcher, repository: Repository, settings) -> None:
        self._fetcher = fetcher
        self._repo = repository
        self._settings = settings

    def ingest_watchlist(
        self,
        *,
        timeframe: Optional[str] = None,
        lookback_days: Optional[int] = None,
        symbols: Optional[list[str]] = None,
    ) -> dict:
        """
        Fetch historical bars for the watchlist and upsert them. Returns a
        summary: {symbols, timeframe, fetched, inserted}. `inserted` counts only
        genuinely new rows (re-running yields inserted == 0).
        """
        timeframe = timeframe or self._settings.BAR_TIMEFRAME
        lookback_days = lookback_days or self._settings.HISTORICAL_LOOKBACK_DAYS
        symbols = list(symbols or self._settings.WATCHLIST)

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=lookback_days)

        df = self._fetcher.fetch_historical_bars(
            symbols, start=start, end=end, timeframe=timeframe,
        )
        records = normalize_bars(df)
        inserted = self._repo.upsert_bars(records, timeframe=timeframe)

        summary = {
            "symbols": symbols,
            "timeframe": timeframe,
            "fetched": len(records),
            "inserted": inserted,
        }
        logger.info(
            "ingest_watchlist: %d symbols, %d bars fetched, %d new rows (tf=%s)",
            len(symbols), len(records), inserted, timeframe,
        )
        return summary
