"""
Olympus entrypoint — Phase 1 (The Correct Foundation).

A thin, restart-safe startup sequence. It does only what the foundation can do
honestly today; the paper-trading loop and the strategies arrive in Phase 2.

On every start, in order:
  1. Initialize logging.
  2. Initialize the database (idempotent — safe on every start).
  3. If Alpaca paper keys are present:
       a. Broker healthcheck.
       b. RECONCILE TO BROKER TRUTH before doing anything else (Article II):
          compare the persisted open positions against the broker; the broker
          wins on any disagreement. The result is recorded as a system_event.
       c. Ingest the watchlist's market data (idempotent — no duplicate rows).
  4. If keys are absent, the database is still initialized and the broker steps
     are skipped with a clear message (so this runs cleanly before .env exists).

This file is intentionally not a long-running process yet — it performs one
honest startup pass and exits. Run it from the olympus/ directory:

    venv\\Scripts\\python main.py
"""

from __future__ import annotations

import sys

from config.settings import MissingCredentialsError, settings
from core.data.ingestion import MarketDataIngestion
from core.db.database import Database
from core.db.repository import Repository
from core.logger import get_logger, init_logging


def run() -> int:
    init_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    logger = get_logger("olympus.main")
    logger.info("=== Olympus starting (environment=%s) ===", settings.ENVIRONMENT)

    # --- Step 2: database (always; key-free) ---
    db = Database(settings.DB_PATH)
    db.initialize()
    repo = Repository(db)

    # --- Broker-dependent steps (only with credentials) ---
    try:
        settings.require_broker_credentials()
    except MissingCredentialsError as exc:
        logger.warning(
            "Broker steps skipped — %s The database is initialized and ready; "
            "add olympus/.env paper keys to enable reconciliation and ingestion.",
            exc,
        )
        logger.info("=== Olympus startup complete (database-only) ===")
        db.close()
        return 0

    # Imported lazily so the database-only path needs no alpaca-py import errors.
    from core.broker.alpaca import AlpacaClient
    from core.trading.reconciliation import BrokerReconciler

    alpaca = AlpacaClient(settings)

    health = alpaca.healthcheck()
    if not health["healthy"]:
        logger.error("Broker healthcheck failed: %s — aborting startup", health["reason"])
        repo.write_event(
            "broker_connectivity_failed", f"Healthcheck failed: {health['reason']}",
            environment=settings.ENVIRONMENT, metadata=health,
        )
        db.close()
        return 1

    # --- Step 3b: reconcile to broker truth BEFORE anything else ---
    local_open = repo.get_open_positions()
    reconciler = BrokerReconciler(alpaca, settings)
    result = reconciler.check(local_open)
    repo.write_event(
        "reconciliation",
        f"Startup reconciliation: {result.reason}",
        environment=settings.ENVIRONMENT,
        metadata=result.to_event_metadata(),
    )
    if result.mismatch:
        logger.warning(
            "Startup reconciliation MISMATCH (%s) — the broker is the truth; "
            "entries will be blocked until resolved.", result.reason,
        )
    else:
        logger.info("Startup reconciliation clean — local matches broker.")

    # --- Step 3c: ingest market data ---
    from core.data.fetcher import DataFetcher

    fetcher = DataFetcher(settings)
    ingestion = MarketDataIngestion(fetcher, repo, settings)
    summary = ingestion.ingest_watchlist()
    logger.info(
        "Market-data ingestion: %d bars fetched, %d new rows for %s",
        summary["fetched"], summary["inserted"], summary["symbols"],
    )

    logger.info("=== Olympus startup complete ===")
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(run())
