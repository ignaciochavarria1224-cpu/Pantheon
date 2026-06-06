-- ===========================================================================
-- Olympus — Phase 1 schema (The Correct Foundation)
--
-- Strategy-agnostic. Every trade/position/lifecycle record carries the three
-- mandated tags: strategy_id, experiment_id, and an environment marker
-- ('paper' | 'live'). There are NO ranker-specific columns (no rank, score,
-- regime, or cycle) — strategy-specific reasoning lives in a provenance-tagged
-- signal_json column, so any strategy can record its own context without a
-- schema change.
--
-- The governing law is Olympus Article II: NO STATE IS RECORDED WITHOUT BROKER
-- CONFIRMATION. The schema enforces this at the storage layer:
--   * `orders` is the ONLY place intended/requested values live, and they are
--     explicitly labelled as intent, never as outcome.
--   * `fills` may ONLY hold broker-confirmed fills, at the broker's price/qty/
--     time. A CHECK constraint makes an unconfirmed fill row impossible.
--   * `positions` and `trades` are built strictly from confirmed fills.
--
-- All timestamps are stored as UTC ISO-8601 text.
-- ===========================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- orders — every order Olympus SUBMITS. This is INTENT, not outcome.
-- Keyed by the broker's order_id. The requested_qty / requested side here are
-- what Olympus asked for; what actually happened lives in `fills`.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id          TEXT PRIMARY KEY,          -- broker order id (truth anchor)
    client_order_id   TEXT,
    strategy_id       TEXT NOT NULL,
    experiment_id     TEXT NOT NULL,
    environment       TEXT NOT NULL CHECK (environment IN ('paper', 'live')),
    symbol            TEXT NOT NULL,
    side              TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    requested_qty     INTEGER NOT NULL,          -- INTENT: shares requested
    order_type        TEXT NOT NULL DEFAULT 'market',
    time_in_force     TEXT NOT NULL DEFAULT 'day',
    intent            TEXT NOT NULL DEFAULT 'entry' CHECK (intent IN ('entry', 'exit')),
    broker_status     TEXT,                      -- last broker status observed
    submitted_at      TEXT,                      -- broker submitted_at (UTC ISO)
    signal_json       TEXT,                      -- strategy reasoning (provenance-tagged)
    source            TEXT NOT NULL DEFAULT 'olympus',  -- provenance
    recorded_at       TEXT NOT NULL              -- when Olympus wrote this row (UTC ISO)
);
CREATE INDEX IF NOT EXISTS idx_orders_strategy ON orders (strategy_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol   ON orders (symbol);
CREATE INDEX IF NOT EXISTS idx_orders_env      ON orders (environment);

-- ---------------------------------------------------------------------------
-- fills — BROKER-CONFIRMED fills only. Article II made physical.
-- A fill row literally cannot exist unless confirmed = 1, and it stores the
-- broker's filled_avg_price / filled_qty / filled_at — never planned values.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fills (
    fill_id           TEXT PRIMARY KEY,          -- uuid4
    order_id          TEXT NOT NULL REFERENCES orders (order_id),
    strategy_id       TEXT NOT NULL,
    experiment_id     TEXT NOT NULL,
    environment       TEXT NOT NULL CHECK (environment IN ('paper', 'live')),
    symbol            TEXT NOT NULL,
    side              TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    fill_price        REAL NOT NULL,             -- broker filled_avg_price
    fill_qty          INTEGER NOT NULL,          -- broker filled_qty
    fill_time         TEXT NOT NULL,             -- broker filled_at (UTC ISO)
    confirmed         INTEGER NOT NULL DEFAULT 1 CHECK (confirmed = 1),  -- invariant
    source            TEXT NOT NULL DEFAULT 'broker_poll',  -- provenance
    recorded_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fills_order    ON fills (order_id);
CREATE INDEX IF NOT EXISTS idx_fills_strategy ON fills (strategy_id);
CREATE INDEX IF NOT EXISTS idx_fills_symbol   ON fills (symbol);

-- ---------------------------------------------------------------------------
-- positions — open positions built from a confirmed entry fill, closed out
-- when the exit fill confirms. Prices/qty are broker-truth (carried from fills).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS positions (
    position_id       TEXT PRIMARY KEY,          -- uuid4
    strategy_id       TEXT NOT NULL,
    experiment_id     TEXT NOT NULL,
    environment       TEXT NOT NULL CHECK (environment IN ('paper', 'live')),
    symbol            TEXT NOT NULL,
    direction         TEXT NOT NULL CHECK (direction IN ('long', 'short')),
    entry_price       REAL NOT NULL,             -- broker fill price
    size              INTEGER NOT NULL,          -- broker filled qty
    entry_order_id    TEXT NOT NULL REFERENCES orders (order_id),
    entry_fill_id     TEXT NOT NULL REFERENCES fills (fill_id),
    entry_time        TEXT NOT NULL,             -- broker fill time (UTC ISO)
    status            TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    exit_order_id     TEXT REFERENCES orders (order_id),
    exit_fill_id      TEXT REFERENCES fills (fill_id),
    exit_time         TEXT,
    signal_json       TEXT,                      -- strategy reasoning at entry
    recorded_at       TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_positions_strategy ON positions (strategy_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol   ON positions (symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status   ON positions (status);

-- ---------------------------------------------------------------------------
-- trades — completed round-trips (entry fill -> exit fill). Append-only.
-- realized_pnl is computed on broker-confirmed prices and the broker-confirmed
-- filled quantity only.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trades (
    trade_id              TEXT PRIMARY KEY,      -- uuid4
    position_id           TEXT NOT NULL REFERENCES positions (position_id),
    strategy_id           TEXT NOT NULL,
    experiment_id         TEXT NOT NULL,
    environment           TEXT NOT NULL CHECK (environment IN ('paper', 'live')),
    symbol                TEXT NOT NULL,
    direction             TEXT NOT NULL CHECK (direction IN ('long', 'short')),
    entry_price           REAL NOT NULL,
    exit_price            REAL NOT NULL,
    size                  INTEGER NOT NULL,
    entry_time            TEXT NOT NULL,
    exit_time             TEXT NOT NULL,
    hold_duration_minutes REAL,
    realized_pnl          REAL NOT NULL,
    exit_reason           TEXT NOT NULL,
    entry_order_id        TEXT NOT NULL REFERENCES orders (order_id),
    exit_order_id         TEXT NOT NULL REFERENCES orders (order_id),
    entry_fill_id         TEXT NOT NULL REFERENCES fills (fill_id),
    exit_fill_id          TEXT NOT NULL REFERENCES fills (fill_id),
    signal_json           TEXT,
    recorded_at           TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades (strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol   ON trades (symbol);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades (exit_time);

-- ---------------------------------------------------------------------------
-- system_events — everything Olympus TRIED to do that isn't a recorded trade:
-- order_unfilled, order_submission_failed, reconciliation, broker_connectivity_failed.
-- This is how the database reflects the full truth, including non-events.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_events (
    event_id          TEXT PRIMARY KEY,          -- uuid4
    event_type        TEXT NOT NULL,
    strategy_id       TEXT,                      -- nullable: some events are system-wide
    experiment_id     TEXT,
    environment       TEXT NOT NULL CHECK (environment IN ('paper', 'live')),
    symbol            TEXT,
    summary           TEXT NOT NULL,
    metadata_json     TEXT,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type   ON system_events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_symbol ON system_events (symbol);
CREATE INDEX IF NOT EXISTS idx_events_created ON system_events (created_at);

-- ---------------------------------------------------------------------------
-- market_data — OHLCV bars for the watchlist. This is shared market truth, not
-- a per-strategy record, so it carries no strategy tags — only provenance.
-- UNIQUE(symbol, timeframe, timestamp) guarantees idempotent ingestion: a
-- re-run can never create duplicate rows.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_data (
    symbol            TEXT NOT NULL,
    timeframe         TEXT NOT NULL,             -- e.g. '1Day', '15Min'
    timestamp         TEXT NOT NULL,             -- bar timestamp (UTC ISO)
    open              REAL NOT NULL,
    high              REAL NOT NULL,
    low               REAL NOT NULL,
    close             REAL NOT NULL,
    volume            REAL NOT NULL,
    vwap              REAL,
    source            TEXT NOT NULL DEFAULT 'alpaca',  -- provenance
    ingested_at       TEXT NOT NULL,
    PRIMARY KEY (symbol, timeframe, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_tf ON market_data (symbol, timeframe);

-- ---------------------------------------------------------------------------
-- v_trade_quality — the honest quality model. A trade is 'clean' ONLY when it
-- is backed by linked, broker-confirmed entry AND exit fills. Because fills
-- cannot exist unconfirmed (CHECK confirmed = 1), 'clean' is provably clean:
-- it is derived solely from signals the system actually emits, never assumed.
-- ---------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_trade_quality AS
SELECT
    t.trade_id,
    t.strategy_id,
    t.experiment_id,
    t.environment,
    t.symbol,
    t.realized_pnl,
    CASE
        WHEN ef.fill_id IS NOT NULL AND xf.fill_id IS NOT NULL THEN 'clean'
        ELSE 'incomplete'
    END AS quality
FROM trades t
LEFT JOIN fills ef ON ef.fill_id = t.entry_fill_id AND ef.confirmed = 1
LEFT JOIN fills xf ON xf.fill_id = t.exit_fill_id  AND xf.confirmed = 1;
