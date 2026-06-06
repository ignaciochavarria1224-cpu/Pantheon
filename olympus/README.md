# Olympus

Olympus is Pantheon's **sealed** trading and market-learning system. It is its own
self-contained codebase with its own database. The rest of Pantheon may **read** Olympus's
status through a read-only API but can never write into it or place a trade (the Seal).

Its founding law is [`OLYMPUS_CONSTITUTION.md`](OLYMPUS_CONSTITUTION.md), which is
subordinate to the Pantheon Constitution.

## The one rule above all (Article II)

**No state is recorded without broker confirmation.** The broker is always the truth; when
Olympus's records and the broker disagree, Olympus corrects itself to match. There is no
fallback to intended or planned values. This is the law that the first generation violated
(it reported profit while the real account lost money), and everything here is built on it.

## Current status — Phase 0/1

- **Phase 0 (now):** clean home, environment, and safety net.
- **Phase 1 (next):** the correct foundation — a fresh, empty, corrected database; the
  truthful confirmed-state recording spine; and market-data collection. All
  strategy-agnostic.
- Strategies are chosen separately (see `docs/strategies/`) and wired in at **Phase 2**.

## Starting watchlist (provisional, configurable)

SPY, AAPL, TSLA, NVDA, AMZN.

## Capital model

Pooled — one paper account (one live account later). Strategies are separated by
`strategy_id`, never by separate accounts. Per-strategy results come from filtering on the
tag. Nothing faked (Principle 4).

## Setup

```
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in your Alpaca PAPER keys (never commit .env)
```
