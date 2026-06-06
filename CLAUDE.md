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
- **NEXT — Phase 1: The Correct Foundation.** Strategy-agnostic. Build, in order:
  1. The corrected, **empty** SQLite database (WAL): `strategy_id` + `experiment_id` +
     environment marker on every record; one append-only trade-lifecycle (entry -> fill ->
     exit); provenance labels; an honest quality model (only signals the system emits).
  2. The **confirmed-state recording spine** (Article II): submit -> poll broker until
     terminal -> record only broker-confirmed fills at broker price/qty; reconcile to broker
     on startup. Port the *repaired* fill-confirmation engine + reconciler from the old
     Olympus as reference (see "Reference material" below).
  3. **Market-data ingestion** for the watchlist (the "reliably collecting data" milestone).
  4. A clean **`Strategy` interface** + `strategy_id` plumbing, empty of real strategies.

## Owner to-dos still open (do not block Phase 1's early steps)

1. Create `olympus/.env` from `olympus/.env.example` and add Alpaca **paper** keys
   (never commit `.env` — it is git-ignored).
2. Verify **BitLocker** is on for `C:` (Start -> "Manage BitLocker").

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
