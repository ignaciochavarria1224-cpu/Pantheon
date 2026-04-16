# Olympus

Olympus is the trading execution system in the Pantheon stack.

It owns the market-facing workflow: fetching data, ranking a liquid equity universe, running paper-trading logic, persisting trade memory, and producing artifacts the rest of Pantheon can consume. If Apollo is the interface and Pantheon is the orchestration layer, Olympus is the subsystem that actually watches markets and manages simulated execution behavior.

## Purpose

Olympus exists to turn market inputs into structured trading decisions and durable records.

Its current responsibilities are:

- authenticate with Alpaca paper trading
- fetch and normalize intraday market data
- rank a broad equity universe into long and short candidates
- run an always-on paper-trading loop with risk controls
- persist trade events, rankings, and execution memory into SQLite and JSON artifacts
- generate reports and utilities for inspection and debugging

This means Olympus is not just a script that places paper orders. It is a runtime with its own data layer, ranking logic, execution policy, and memory model.

## What The System Contains

### `main.py`
The phase-gate entrypoint.

This script performs a structured startup validation across settings, logging, Alpaca connectivity, market data access, normalization, cache behavior, and scheduler behavior. It is the quickest way to confirm a fresh machine is wired correctly before running the live loop.

### `run_live.py`
The continuous paper-trading runtime.

This is the main operational process. It:

- loads settings
- initializes the SQLite database
- ingests existing ranking and trade JSON into durable storage
- starts the ranking cycle
- starts the memory-aware paper-trading loop
- keeps a heartbeat running until shutdown

It also uses a PID lockfile so two live runtimes do not start accidentally on the same machine.

### `config/`
Environment-driven configuration.

`config/settings.py` defines Olympus's runtime contract: Alpaca credentials, market hours, ranking cadence, cache paths, log paths, trading risk limits, and storage paths.

### `core/`
The trading engine itself.

Important areas include:

- `core/broker/`
  Alpaca integration and broker-facing behavior
- `core/data/`
  market-data fetch, normalization, and cache handling
- `core/ranking/`
  feature computation, scoring, classification, and cycle orchestration
- `core/trading/`
  execution, position management, sizing, risk logic, and the live loop
- `core/memory/`
  SQLite initialization, ingestion, repository access, and memory writing
- `core/reporting/`
  reporting utilities such as the daily report generator

### `tests/`
Phase-organized test coverage.

The suite is grouped by major system milestones:

- `phase1`
  connectivity, data, and scheduler basics
- `phase2`
  ranking and feature logic
- `phase3`
  trading loop, risk, sizing, and position management
- `phase4`
  memory, schema, ingestion, and repository behavior

### `tools/` and `scripts/`
Operational utilities.

These include local helpers for backtesting, DuckDB inspection, and targeted repair/migration tasks for trade-memory data.

## Current Role In The Pantheon Stack

Olympus is currently the trading execution source of truth.

That means the broader stack should rely on Olympus for:

- current paper-trading state
- ranked symbols and directional bias
- recorded trades and trade features
- runtime health for the market-facing system

Apollo already includes an Olympus connector, but that connector currently reads exported runtime status rather than directly invoking Olympus code in-process. The code in this folder is the system behind that boundary.

## Current State Of Olympus

Olympus is already a real multi-part trading runtime, not just an experiment.

It already has:

- Alpaca paper broker connectivity
- a hardcoded liquid-equity universe
- repeated ranking cycles over recent intraday bars
- risk-aware paper-trading flow
- SQLite-backed trade memory
- JSON ingestion for trade and ranking artifacts
- tests across the major subsystems

What it does not yet claim is live-money execution. The present code is organized around paper-trading, runtime stability, and structured storage first.

## Runtime And Dependencies

Olympus currently depends on:

- Python
- Alpaca paper trading credentials
- `alpaca-py`
- `pandas`
- `pyarrow`
- `python-dotenv`
- `pytz`
- writable local storage for cache, logs, trades, rankings, and SQLite state

Runtime data is intentionally excluded from Git. On a working machine, Olympus will create and use local paths under `data/` for:

- market-data cache files
- logs
- ranking exports
- JSON trade records
- `olympus.db`

## Quick Start

```bash
# 1. Move into the Olympus app
cd apps/olympus

# 2. Create a local environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Fill in credentials
copy .env.example .env
# then edit .env with Alpaca paper keys

# 4. Run the gate check
python main.py

# 5. Start the live paper runtime
python run_live.py
```

## Common Commands

```bash
cd apps/olympus
python main.py
python run_live.py
pytest
pytest -m "not integration"
python check_db.py
python tools/backtest_runner.py
```

## Data Ownership

Olympus owns:

- market-facing trading logic
- ranking outputs and signal generation
- paper-trade execution records
- trade-memory persistence
- trading runtime health and scheduling behavior

Olympus does not own:

- Apollo's user-facing interfaces
- Pantheon's cross-system reasoning policy
- BlackBook's financial ledger
- Maridian's reflective memory and journal processing

That boundary matters because Olympus should stay execution-focused and operationally reliable rather than absorbing unrelated reasoning or interface concerns.

## Documentation Contract

This README is a living system summary.

Whenever Olympus changes in any material way, this file should be updated in the same commit if the change affects:

- runtime entrypoints
- risk or execution behavior
- storage responsibilities
- subsystem boundaries
- external dependencies
- how Olympus integrates with Apollo or Pantheon

If code and documentation disagree, the code is the source of truth until this file is corrected.
