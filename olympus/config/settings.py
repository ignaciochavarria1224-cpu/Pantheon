"""
Central configuration for Olympus — Phase 1 (The Correct Foundation).

All parameters live here. Credentials are loaded from `.env` — never hardcoded,
never committed. This is the strategy-agnostic foundation: there are NO ranking,
regime, or qualification parameters here. Those belong to strategies, which are
wired in at Phase 2.

Design note — key-free unit tests:
    Loading settings never raises on missing Alpaca keys. The credentials are
    read into the Settings object as (possibly empty) strings. Only components
    that actually talk to the broker (AlpacaClient, DataFetcher) validate that
    the keys are present, at construction time. This lets the database, schema,
    and strategy-interface tests run with no `.env` at all.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the olympus root directory (one level up from config/).
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


def _str_env(key: str, default: str) -> str:
    return os.getenv(key, default)


def _bool_env(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes")


def _int_env(key: str, default: int) -> int:
    val = os.getenv(key)
    return int(val) if val is not None else default


def _float_env(key: str, default: float) -> float:
    val = os.getenv(key)
    return float(val) if val is not None else default


def _float_tuple_env(key: str, default: tuple) -> tuple:
    """Parse a comma-separated env var into a tuple of floats."""
    val = os.getenv(key)
    if val is None:
        return default
    return tuple(float(x.strip()) for x in val.split(",") if x.strip())


def _list_env(key: str, default: list[str]) -> list[str]:
    """Parse a comma-separated env var into a list of upper-cased symbols."""
    val = os.getenv(key)
    if val is None:
        return default
    return [s.strip().upper() for s in val.split(",") if s.strip()]


class MissingCredentialsError(EnvironmentError):
    """Raised when a broker/data component is constructed without Alpaca keys."""


@dataclass(frozen=True)
class Settings:
    # --- Credentials (from .env; may be empty until the owner adds them) ---
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str
    ALPACA_PAPER: bool          # hard guard — must be True this phase

    # --- Environment marker stamped on every record ---
    ENVIRONMENT: str            # "paper" or "live"

    # --- Data feed ---
    DATA_FEED: str              # "iex" or "sip"

    # --- Market hours (ET) ---
    MARKET_OPEN: str            # "09:30"
    MARKET_CLOSE: str           # "16:00"

    # --- Watchlist (provisional, configurable) ---
    WATCHLIST: tuple            # tuple[str, ...]

    # --- Bar settings ---
    BAR_TIMEFRAME: str          # default bar resolution, e.g. "1Day"
    HISTORICAL_LOOKBACK_DAYS: int

    # --- Storage / paths ---
    DB_PATH: Path
    CACHE_DIR: Path
    LOG_DIR: Path

    # --- Logging ---
    LOG_LEVEL: str
    TIMEZONE: str

    # --- Fill-confirmation gate (Article II) ---
    FILL_CONFIRM_BACKOFF: tuple             # per-attempt wait schedule (seconds)
    BROKER_HEALTHCHECK_TIMEOUT_SECONDS: float

    # --- Reconciliation guards ---
    OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS: bool
    OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH: bool

    def require_broker_credentials(self) -> None:
        """
        Validate that Alpaca keys are present. Called by AlpacaClient/DataFetcher
        at construction. The database and strategy-interface layers never call
        this, so they run with no `.env`.
        """
        if not self.ALPACA_API_KEY or not self.ALPACA_SECRET_KEY:
            raise MissingCredentialsError(
                "Alpaca credentials are not set. Copy olympus/.env.example to "
                "olympus/.env and fill in your PAPER keys (never commit .env)."
            )


def load_settings() -> Settings:
    """Load all settings from the environment. Never raises on missing keys."""
    db_path = Path(_str_env("DB_PATH", str(_ROOT / "data" / "olympus.db")))
    cache_dir = Path(_str_env("CACHE_DIR", str(_ROOT / "data" / "cache")))
    log_dir = Path(_str_env("LOG_DIR", str(_ROOT / "data" / "logs")))

    # Ensure storage directories exist (the DB and logs are git-ignored).
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        ALPACA_API_KEY=_str_env("ALPACA_API_KEY", ""),
        ALPACA_SECRET_KEY=_str_env("ALPACA_SECRET_KEY", ""),
        ALPACA_PAPER=_bool_env("ALPACA_PAPER", True),
        ENVIRONMENT=_str_env("ENVIRONMENT", "paper"),
        DATA_FEED=_str_env("DATA_FEED", "iex"),
        MARKET_OPEN=_str_env("MARKET_OPEN", "09:30"),
        MARKET_CLOSE=_str_env("MARKET_CLOSE", "16:00"),
        WATCHLIST=tuple(_list_env("WATCHLIST", ["SPY", "AAPL", "TSLA", "NVDA", "AMZN"])),
        BAR_TIMEFRAME=_str_env("BAR_TIMEFRAME", "1Day"),
        HISTORICAL_LOOKBACK_DAYS=_int_env("HISTORICAL_LOOKBACK_DAYS", 30),
        DB_PATH=db_path,
        CACHE_DIR=cache_dir,
        LOG_DIR=log_dir,
        LOG_LEVEL=_str_env("LOG_LEVEL", "INFO"),
        TIMEZONE=_str_env("TIMEZONE", "America/New_York"),
        FILL_CONFIRM_BACKOFF=_float_tuple_env(
            "FILL_CONFIRM_BACKOFF", (0.5, 1.0, 2.0, 4.0, 2.5)
        ),
        BROKER_HEALTHCHECK_TIMEOUT_SECONDS=_float_env(
            "BROKER_HEALTHCHECK_TIMEOUT_SECONDS", 5.0
        ),
        OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS=_bool_env(
            "OLYMPUS_AUTO_REPAIR_PAPER_POSITIONS", False
        ),
        OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH=_bool_env(
            "OLYMPUS_BLOCK_ENTRIES_ON_BROKER_MISMATCH", True
        ),
    )


# Module-level singleton — imported by all other modules.
settings = load_settings()
