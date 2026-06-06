# Pantheon / Olympus — Clean Restart Build Plan (FINAL)

## In plain terms (read this first)

You're deliberately **starting over** with one clean, organized home — a single project
folder with a subfolder for each system — and building fresh. The old systems are kept only
as **reference**, for three things: (1) the mistakes to not repeat, (2) working code to reuse,
(3) a head-start so we build faster.

We begin with **Olympus** (the constitution's build order). But we build the **foundation
first** — the part that records trades truthfully and can hold *any* strategy — so that when
you've finished your research and chosen your strategies, they drop straight in. **You pick
the strategies; we build the stage they perform on.** Starting with a few stocks does not
block the big universe or the ranking engine later — those are added on the same foundation.

---

## What we keep from the old systems (reference only — nothing imported live)

- **The lesson.** The first Olympus reported profit while really losing money because it
  recorded *intended* trades as if they were real ("phantom trades"). The fix — **never record
  anything the broker hasn't confirmed** (Article II) — is the core of everything below.
- **Working code to port.** The *repaired* fill-confirmation engine, the broker reconciler,
  the market-data fetcher/normalizer/cache, the SQLite core, and the scheduler from the
  stabilized old Olympus. Ported deliberately, not copied wholesale.
- **A reference blueprint.** The old `Olympus_V2` rebuild docs (Master/Build/Migration) and
  its corrected-schema design, used to move faster. **The Pantheon Constitution and Olympus
  Constitution remain the source of truth above them.**
- **Old data: none imported.** The new database starts **empty**. The old database stays as a
  read-only archive you can always look back at. (This is your "fresh start" decision; it also
  removes any chance of broken data contaminating the new system.)

---

## The home & structure (honors the Seal + your "consolidated, simple" goal)

One git-backed project root, pushed to **GitHub** (Security rule 6), with a subfolder per
system. Olympus is its **own sealed subfolder** — its own code and its own database, which
Pantheon may only **read** through an API, never write. *That* is the Seal; physical proximity
in the same parent folder is fine and is what keeps your content from scattering.

```
Pantheon/                 <- one consolidated home, a git repo on GitHub
  Pantheon_Constitution.md
  pantheon-os/            <- the shell/OS (built later)
  apollo/  blackbook/  meridian/   <- built later, in their phases
  olympus/                <- OWN sealed codebase + OWN database (read-only API out)
```

**Location (decided):** `C:\Users\ignac\Documents\Pantheon` — a local path **outside OneDrive**
(OneDrive sync can corrupt a live database/git). Remote already created:
`https://github.com/ignaciochavarria1224-cpu/Pantheon.git`. In Phase 0 we create **all** system
subfolders up front (empty is fine) so the structure exists from day one.

---

## What we are deliberately NOT deciding yet

- **The actual strategies.** You will choose these after your own deep research. We build a
  strategy **framework** — a clean interface plus `strategy_id` tagging — that holds whatever
  you later pick. No strategy is hard-coded into the foundation.
- **The full large universe + ranking engine.** Deferred. The foundation is built so they slot
  in later as additional strategies, with no rework.

---

## Binding law (the constitution is the source of truth)

- **Article II — never record unconfirmed state.** The broker is the truth; on any disagreement
  the system corrects itself to match the broker. No fallback to intended/planned values.
- **Article III — two gates.** Trade gate open (paper trading is fully autonomous); **capital
  gate closed** (going live + sizing real money is permanently human-gated — far out of scope).
- **Article V — safety limits**, scaffolded and tested in paper: daily-loss auto-halt,
  max-drawdown stop, position-size caps, and an owner kill switch.
- **Principle 4 — pooled capital, logical separation** (decided). One paper account (one live
  account later); strategies separated by `strategy_id`, never by separate accounts; no invented
  per-strategy equity. Per-strategy results come from filtering on the tag. Nothing faked.
- **The Seal** — Olympus is separate, sealed code; Pantheon reaches it read-only.
- **Apex** (starts as a backward-looking historian, ML only much later) and **Areopagus** (the
  five-role council) are **later phases, out of scope now.**
- **Naming:** the council is **Areopagus** (the constitution locks this; the old docs' "Pantheon
  debate layer" name is retired).

---

## Starting watchlist (provisional, configurable)

**SPY, AAPL, TSLA, NVDA, AMZN** — the index plus four big names (TSLA swapped in for its
volatility, per your preference). The list lives in config and expands later toward the big
universe.

---

## Build phases

### Phase 0 — Clean home + safety net  (COMPLETE)
- Initialize the git repo at `C:\Users\ignac\Documents\Pantheon`, connect the existing remote,
  push. `.gitignore` excludes secrets (`.env`), the database, `venv/`, logs.
- Create **all** system subfolders now (empty placeholders): `pantheon-os/`, `apollo/`,
  `atlas/`, `blackbook/`, `meridian/`, `zenith/`, `olympus/`. Constitution in the repo.
- In `olympus/`: Python venv; `.env` with Alpaca **paper** keys (never committed); confirm the
  Alpaca paper feed covers the watchlist.
- Confirm **BitLocker on**; choose an encrypted backup target for the database.

### Phase 1 — The Correct Foundation (Olympus)  <- where we begin next
- **Corrected, empty database** (SQLite, WAL): `strategy_id` + `experiment_id` + environment
  marker (paper/live) on every trade/position/feature record; a single **append-only
  trade-lifecycle** record (entry -> fill -> exit); provenance labels on every derived field; an
  honest quality model that depends only on signals the system actually emits.
- **Port the proven spine** (reference: the stabilized old Olympus): account-parameterized
  broker client (paper-only guard), the **confirmed-state fill engine** (add the unit test it
  never had), the **broker reconciler**, the data fetcher/normalizer/cache, the SQLite core, the
  scheduler.
- **Principles in structure:** no inert config (every setting runs on the path it governs);
  never substitute a default for missing truth; trustworthy, queryable record; pooled capital.
- **Market-data ingestion** for the watchlist — this is the constitution's "Olympus first:
  reliably collecting data" milestone, and it's strategy-agnostic.
- **Strategy framework:** a clean `Strategy` interface + `strategy_id` plumbing, **empty of real
  strategies**, ready for the ones chosen after research.

### Phase 2 — Paper trading loop, fully wired (begins once >=1 strategy is chosen)
- Wire entry/exit/sizing/risk gates + the reconciler **act**-path + a decision trail (every
  entry, exit, **and rejection** queryable).
- **Article V safety + kill switch**, tested in paper.
- Run the first chosen strategy end-to-end in paper, fully autonomous, with **every control
  actually executing**. Prove one clean loop, then add further strategies (each `strategy_id`-
  tagged) into the shared pooled paper account.

### Phase 3 — Trustworthy memory
- Persistent storage of every trade and cycle with full context; honest quality labeling
  (clean means provably clean); retrieval by time/strategy/outcome.

### Later phases (mapped to the constitution; detailed when reached)
- **Apex** (historian first -> ML only once clean data justifies it) -> **Areopagus**
  (Researcher, Critic, Risk Manager, Optimizer, Judge; every conclusion human-gated) ->
  controlled evolution -> the **app UI + live gate**. The **big universe + ranking engine** are
  added here as additional strategies. Live trading is always human-gated. **Olympus "done" =
  profitable for two months on paper before any real money.**

---

## Operational note
The PC stays on at all times, so no sleep/power changes are needed. The engine is still built
**restart-safe** — on any restart it reconciles to the broker's truth before doing anything.

---

## Verification
- **Article II (the critical suite):** an unfilled, rejected, or partial order **never** becomes
  a phantom position or PnL; confirmed fills are recorded at the **broker's** price/qty only;
  startup reconcile rewrites local records to match the broker and logs the correction.
- **Strategy framework:** every signal/order/fill/trade carries the correct `strategy_id`;
  per-strategy stats compute independently.
- **Safety:** breaching the daily-loss limit halts the loop; the kill switch flattens to the
  broker's confirmed state.
- **Reliability:** kill and restart mid-session -> it reconciles and resumes without double-
  writing or corruption.
- **Data collection:** market data ingests for the watchlist with no duplicate rows.

---

## Resolved decisions
- **Home:** `C:\Users\ignac\Documents\Pantheon`, remote `...Pantheon.git`.
- **Watchlist:** SPY, AAPL, TSLA, NVDA, AMZN.
- **Operations:** PC always on; engine still restart-safe.
- **Phase 0 folders:** all systems created empty up front.
- **Capital model:** pooled — one account, separated by `strategy_id` (Principle 4).
- **Strategies:** 7 researched and delivered (see `olympus/docs/strategies/`); wired at Phase 2.

---

## Strategy research scope (locked)
- **Instruments:** US stocks & ETFs only (Alpaca equities). No futures/FX/options; crypto deferred.
- **Type:** standalone, self-contained systematic strategies that coexist on the watchlist
  (each tagged by `strategy_id`). Not variants of the ranker — that's a later addition.
- **Timeframe:** daily primary; intraday OK down to ~15-min. Exclude tick data, sub-second/
  low-latency execution, and hard-to-borrow shorting.
- **Count & depth:** 5–8 strategies, each in deep, codeable detail with cited backtests.
  (Delivered: 7 — see `olympus/docs/strategies/STRATEGY_RESEARCH_v1.md`.)
