"""
Central configuration for Olympus.
All parameters live here. Credentials are loaded from .env — never hardcoded.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the olympus root directory
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in your credentials."
        )
    return val


def _bool_env(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes")


def _str_env(key: str, default: str) -> str:
    return os.getenv(key, default)


def _int_env(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    return int(val)


def _float_env(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    return float(val)


@dataclass(frozen=True)
class Settings:
    # --- Credentials (from .env) ---
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str
    ALPACA_PAPER: bool

    # --- Data feed ---
    DATA_FEED: str          # "iex" or "sip"

    # --- Market hours (ET) ---
    MARKET_OPEN: str        # "09:30"
    MARKET_CLOSE: str       # "16:00"

    # --- Universe ---
    UNIVERSE_SIZE: int      # target asset count

    # --- Bar settings ---
    BAR_TIMEFRAME: str      # default bar resolution
    HISTORICAL_LOOKBACK_DAYS: int

    # --- Scheduler ---
    RANKING_INTERVAL_MINUTES: int

    # --- Storage ---
    CACHE_DIR: Path

    # --- Logging ---
    LOG_LEVEL: str
    LOG_DIR: Path

    # --- Timezone ---
    TIMEZONE: str

    # --- Phase 3: Paper Trading ---
    MAX_OPEN_POSITIONS: int       # Max concurrent open positions (longs + shorts)
    MAX_DAILY_LOSS_PCT: float     # Max daily loss as fraction of equity (e.g. 0.02 = 2%)
    MIN_REWARD_RISK: float        # Minimum reward/risk ratio required to enter
    MAX_RISK_PER_TRADE_PCT: float # Max risk per trade as fraction of equity (e.g. 0.005 = 0.5%)
    ATR_STOP_MULTIPLIER: float    # Stop = entry ± (ATR * multiplier)
    ATR_TARGET_MULTIPLIER: float  # Target = entry ± (ATR * multiplier)
    ROTATION_RANK_DROP_THRESHOLD: int  # Exit if rank drops below this value
    TRADES_DIR: Path              # Directory for JSON trade records

    # --- Phase 4: Memory & Storage ---
    DB_PATH: Path                 # Path to olympus.db SQLite database


def load_settings() -> Settings:
    """Load and validate all settings. Raises EnvironmentError on missing credentials."""
    cache_dir = Path(_str_env("CACHE_DIR", str(_ROOT / "data" / "cache")))
    log_dir = Path(_str_env("LOG_DIR", str(_ROOT / "data" / "logs")))
    trades_dir = Path(_str_env("TRADES_DIR", str(_ROOT / "data" / "trades")))
    db_path = Path(_str_env("DB_PATH", str(_ROOT / "data" / "olympus.db")))

    # Ensure directories exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    trades_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        ALPACA_API_KEY=_require_env("ALPACA_API_KEY"),
        ALPACA_SECRET_KEY=_require_env("ALPACA_SECRET_KEY"),
        ALPACA_PAPER=_bool_env("ALPACA_PAPER", True),
        DATA_FEED=_str_env("DATA_FEED", "iex"),
        MARKET_OPEN=_str_env("MARKET_OPEN", "09:30"),
        MARKET_CLOSE=_str_env("MARKET_CLOSE", "16:00"),
        UNIVERSE_SIZE=_int_env("UNIVERSE_SIZE", 200),
        BAR_TIMEFRAME=_str_env("BAR_TIMEFRAME", "5Min"),
        HISTORICAL_LOOKBACK_DAYS=_int_env("HISTORICAL_LOOKBACK_DAYS", 30),
        RANKING_INTERVAL_MINUTES=_int_env("RANKING_INTERVAL_MINUTES", 20),
        CACHE_DIR=cache_dir,
        LOG_LEVEL=_str_env("LOG_LEVEL", "INFO"),
        LOG_DIR=log_dir,
        TIMEZONE="America/New_York",
        # Phase 3 — Paper Trading
        MAX_OPEN_POSITIONS=_int_env("MAX_OPEN_POSITIONS", 20),
        MAX_DAILY_LOSS_PCT=_float_env("MAX_DAILY_LOSS_PCT", 0.02),
        MIN_REWARD_RISK=_float_env("MIN_REWARD_RISK", 1.8),
        MAX_RISK_PER_TRADE_PCT=_float_env("MAX_RISK_PER_TRADE_PCT", 0.005),
        ATR_STOP_MULTIPLIER=_float_env("ATR_STOP_MULTIPLIER", 1.5),
        ATR_TARGET_MULTIPLIER=_float_env("ATR_TARGET_MULTIPLIER", 3.0),
        ROTATION_RANK_DROP_THRESHOLD=_int_env("ROTATION_RANK_DROP_THRESHOLD", 15),
        TRADES_DIR=trades_dir,
        # Phase 4 — Memory & Storage
        DB_PATH=db_path,
    )


# Module-level singleton — imported by all other modules
settings = load_settings()
