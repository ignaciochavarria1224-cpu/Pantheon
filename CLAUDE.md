# CLAUDE.md — Pantheon (read this first, every session)

This repository is the single consolidated home for **Pantheon**, a private life operating
system for one owner (Ignacio), and all of its systems. Read this file fully before doing
anything. If anything here conflicts with the constitutions, **the constitutions win**.

---

## What this is

Pantheon holds several systems, each in its own subfolder. **Olympus** (trading) is built
first and is **sealed**: its own code, its own database, reachable by the rest of Pantheon
only through a read-only API — never written to from outside.

## Source-of-truth documents — read before building

1. `Pantheon_Constitution.md` — the supreme founding law.
2. `olympus/OLYMPUS_CONSTITUTION.md` — Olympus's law (subordinate to Pantheon's).
3. `BUILD_PLAN.md` — the execution roadmap: phases, decisions, verification.
4. `olympus/docs/strategies/` — the strategies (`README.md` overview + `STRATEGY_RESEARCH_v1.md`).

## The one rule above all (Olympus Article II)

**No state is recorded without broker confirmation.** The broker is always the truth; when
records disagree, Olympus corrects itself to match. No fallback to intended/planned values.
This is the law the first generation violated (it reported profit while really losing money),
and the whole foundation is built on it.

---

## Where we are — LIVING STATUS (update at the end of every session)

- **Phase 0 — COMPLETE (2026-06-06).** Clean repo home, all system folders, both
  constitutions, the Olympus Python environment (venv + pinned deps, import-verified on
  Python 3.14), and the strategy docs are in place and pushed to GitHub.
- **Phase 1 — The Correct Foundation: COMPLETE (2026-06-09).** All four steps are coded,
  tested (36 passing tests), live-verified against the Alpaca paper feed, and pushed.
  Strategy-agnostic throughout. Layout under
  `olympus/`: `config/settings.py` (lean, key-free at import), `core/logger.py`, `core/db/`
  (`schema.sql` + `database.py` + `repository.py`), `core/broker/alpaca.py`, `core/trading/`
  (`models.py` + `execution.py` + `reconciliation.py`), `core/data/` (`fetcher.py` +
  `normalizer.py` + `ingestion.py`), `core/strategy/base.py`, `tests/`, and `main.py`.
  1. **DB (done):** WAL SQLite. `orders` (intent only), `fills` (broker-confirmed only —
     `CHECK confirmed = 1`), `positions`, `trades`, `system_events`, `market_data`. Every
     lifecycle table carries `strategy_id` + `experiment_id` + `environment`; provenance
     columns throughout; `v_trade_quality` derives "clean" solely from linked confirmed fills.
  2. **Confirmed-state spine (done):** ported fill-confirmation engine (submit -> poll until
     terminal -> record only broker-truth fills; unconfirmed -> `order_unfilled` event, no
     phantom state) + broker reconciler (broker wins, paper-guarded repair). The Article II
     unit suite the first Olympus never had now exists.
  3. **Market-data ingestion (done):** ported fetcher/normalizer + idempotent `upsert_bars`
     (no duplicate rows). Unit-tested with a mocked fetcher.
  4. **`Strategy` interface (done):** `Signal` + abstract `Strategy` (`strategy_id` /
     `experiment_id` identity), empty of real strategies; tag plumbing verified end-to-end.
  - `main.py` runs a restart-safe startup pass: init DB -> (with keys) healthcheck ->
    reconcile-to-broker -> ingest. **Live-verified 2026-06-09:** authenticated against the
    Alpaca paper account, startup reconcile reported clean, ingested 105 daily bars
    (21 × 5 watchlist symbols) into `market_data`; a second run inserted **0** new rows
    (idempotent — no duplicates). `olympus/.env` now holds the owner's paper keys (git-ignored).
- **NEXT — Phase 2: the paper-trading loop, fully wired.** Begins now that the foundation is
  complete. Wire entry/exit/sizing/risk gates + the reconciler act-path + a queryable decision
  trail (every entry, exit, and rejection); add Article V safety + kill switch (tested in
  paper); then run the first of the owner's 7 chosen strategies end-to-end in paper, fully
  autonomous, every control actually executing. See `BUILD_PLAN.md` Phase 2.

## Owner to-dos still open

1. ✅ DONE (2026-06-09) — `olympus/.env` created with Alpaca **paper** keys (git-ignored).
2. Verify **BitLocker** is on for `C:` (Start -> "Manage BitLocker") before the database
   holds anything worth protecting.

---

## Key decisions locked

- **Home:** `C:\Users\ignac\Documents\Pantheon` (deliberately **not** OneDrive — sync can
  corrupt a live DB/git). Remote: `github.com/ignaciochavarria1224-cpu/Pantheon`.
- **Watchlist (provisional, configurable):** SPY, AAPL, TSLA, NVDA, AMZN.
- **Capital model:** pooled — one paper account, strategies separated by `strategy_id`,
  nothing faked (Principle 4).
- **Strategies:** 7 chosen by the owner via deep research (US stocks/ETFs only, standalone,
  daily-primary, long-only). Wired in at **Phase 2**; the foundation stays strategy-agnostic.
- **Old systems = reference only.** Nothing is imported; the new database starts empty.

## Reference material (read-only; never build inside, never import data)

The stabilized old Olympus and the prior rebuild docs live in the separate monorepo at
`C:\Users\ignac\Documents\AI_PROJECTS_MONOREPO` (folders `active/Olympus-Trading` and
`active/Olympus_V2`). Use them only to (a) avoid repeating the phantom-trade bug, (b) port
proven code (fill-confirmation engine, broker reconciler, data layer, SQLite core, scheduler),
and (c) move faster. They are NOT the source of truth — the constitutions and `BUILD_PLAN.md`
here are.

## How to work in this repo

- **Confirm before acting.** Never record a state the broker hasn't confirmed.
- **One scoped change at a time;** don't batch large changes.
- **Don't build later-phase items early** (no ranking engine, Apex, Areopagus, UI, or live
  trading until their phase — see `BUILD_PLAN.md`).
- **Secrets never committed;** local-first and private.
- The owner is non-technical: explain plainly, and the owner is the only gate on anything
  that risks real money.

---

## Git workflow (standing rule — the owner has set this)

- **Repo:** `github.com/ignaciochavarria1224-cpu/Pantheon` — remote `origin`, branch `main`.
  Local home: `C:\Users\ignac\Documents\Pantheon`.
- **Commit AND push after every completed, working step.** Not every tiny edit — each time a
  change is finished and verified, make one clear, descriptive commit and **push to GitHub
  immediately**. The backup must always be current. Do this automatically; the owner does not
  need to ask each time.
- **Before each commit, run `git status`** and confirm no secrets (`.env`), database files,
  `venv/`, or logs are staged. These are git-ignored — keep it that way; never commit them.
- End every commit message with the trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- If a push fails (e.g., auth or network), tell the owner plainly rather than leaving work
  unpushed and silent.
