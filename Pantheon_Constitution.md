# THE PANTHEON CONSTITUTION

**The supreme founding document of Pantheon — a private life operating system.**

| | |
|---|---|
| **Version** | 1.0 — Founding Document |
| **Date** | June 5, 2026 |
| **Owner** | Ignacio (single user) |
| **For** | The owner, and Claude Code as the technical executor |
| **Status** | Stable law |

---

## How to Read This Document

This is the constitution of Pantheon. It is the supreme document — the place everything starts and the document every other one answers to. It holds the full vision: what Pantheon is, the law it runs by, every system and its boundaries, how the systems become one, the end goal, and the order it gets built in.

It is written to do three jobs at once: to be the single place the whole project lives, to bring any AI (Claude Code especially) fully up to speed in one read, and to keep the owner honest about what each system is and is not.

Because the full vision lives here, the subsystems do **not** get master plans of their own. Each subsystem gets a *build plan* — the how, the phases, the technical wiring — but its vision, identity, boundaries, and definition of done are defined here and only here.

The document is layered. The vision comes first, the hard law beneath it. It is meant to be stable: you build from it, you don't rewrite it. When it changes, it changes by deliberate amendment, never by starting over.

---

# PART I — IDENTITY AND PURPOSE

## What Pantheon Is

Pantheon is the owner's eyes into his own life. It is a private life operating system that lets one person see and track his whole world — his finances, his thinking, his trading, his writing — in one place, and eventually be guided through it by a personal mentor built from his own history.

Pantheon is the CEO of the system: the layer that organizes and holds everything together. The real work happens inside the subsystems; Pantheon is where it all becomes visible, coherent, and usable as one thing.

It is built on a belief in compounding. Small things tracked faithfully over time — a daily journal, a daily financial snapshot, a steady writing practice, a trading system that learns — become something far larger than any of them alone. Pantheon exists to capture that compounding and make it legible.

## Why Pantheon Exists

Today the owner's life is spread across disconnected tools and untracked corners. Money goes unwatched, thoughts go unorganized, good systems sit separated and unused. Pantheon exists to pull all of it into one view, reduce the friction of staying on top of it, and — over time — grow an intelligence that knows his history well enough to give him real guidance: to notice trends, surface what he's missing, ask him good questions, and help him stay on a good path.

The earlier version of this project failed not because the systems didn't work — they did — but because they grew up separately, without a shared vision binding them. This document is that binding vision, written before the rebuild, so the systems are built as one from the start.

## What Pantheon Is Not

- **Not a subsystem.** Pantheon owns no data of its own. It holds and displays; the subsystems and Atlas own the truth.
- **Not autonomous.** Pantheon never acts on its own. It is a CEO that executes only on the owner's say.
- **Not where Olympus runs.** Olympus lives outside Pantheon and is only *viewed* through it.
- **Not the owner of truth.** Financial truth lives in BlackBook, reflective truth in Meridian, trading truth in Olympus. Pantheon is the window onto them.
- **Not a replacement for the owner's own words.** It remembers and reflects, but the owner still writes Meridian and Zenith himself.
- **Not public, and not multi-user.** One owner. Private. His.

## The Horizon

**One year out.** Open the computer, Pantheon is there. Talk to Apollo by voice and ask how investments are doing, how Olympus performed this week, what today's Meridian questions are; have it read the calendar and help organize the day around when the owner wakes. Everything in one place, frictionless.

**Five years out.** Apollo has matured into a personal mentor with persistent memory, and work has begun on hardware to bring it further into physical life.

**The far future.** A holographic command center — a room where the system surrounds the owner in projected light and he builds and reasons in real space. This is a stated direction, not a commitment, and likely a decade away or more. It does not shape any decision in this document; it is recorded only as the true north the project points toward.

---

# PART II — THE LAW

These are the non-negotiable principles that govern the whole system. They are the most stable part of this document and change least of all.

## The Eight Principles

1. **The owner is the only gate.** Nothing acts on its own. Everything the system does on the owner's behalf happens because he told it to, and the highest-stakes actions — moving real money, touching his own words — are held the tightest.

2. **Never record an unconfirmed state.** The record only ever reflects what truly happened. Nothing is written as fact until it is confirmed. (This is the failure that broke the first Olympus, and it is law now.)

3. **Change is deliberate and proportional to stakes.** The higher the stakes, the slower and more careful the change. Olympus, which touches real money, changes most cautiously of all. Sensitive stores — finances, journals, writing — change with care.

4. **Your words stay yours.** Meridian and Zenith are written by the owner, by hand, never by an AI. The record of his mind and his craft must be authentically his. No system rewrites, summarizes over, or speaks for his own writing.

5. **Each system owns its domain; none absorbs another.** BlackBook owns money. Meridian owns the mind. Olympus owns trading. Zenith owns writing craft. They connect, but they never collapse into each other.

6. **Nothing is a black box.** Every system shows its activity and can be inspected. Olympus especially — even though it runs walled off, its workings are always visible through Pantheon.

7. **Local-first and private.** The system lives on the owner's machine. His most sensitive data stays local and protected. The outside world is touched only where it must be, and as little as possible.

8. **Built by compounding.** Value accumulates over time. The system is built in dependency order, each layer earning the next. It becomes intelligent through accumulation, not through rushing.

## Authority and the Gate

Pantheon and Apollo operate strictly within the authority the owner grants:

- **Apollo may read** everything in Atlas, whenever asked.
- **Apollo may write** to BlackBook — for example, logging an expense the owner tells it about.
- **Apollo may never edit** Olympus, Meridian, or Zenith. The owner writes Meridian and Zenith himself, by hand. Olympus is sealed.
- **Everything else stays behind the owner's gate.** The system acts only when told.

## How Pantheon Changes

Two rules protect the project from its own past:

- **We amend, we don't restart.** New ideas are added to this structure, never used as a reason to tear it down and rebuild from scratch. The single habit that has cost the most time — starting over whenever inspiration strikes — ends here. Improvements are amendments to what exists.
- **New subsystems may be added deliberately.** The owner will have new ideas for systems that serve him (health is a likely future one). New subsystems may be added — but deliberately, as considered amendments to this document, with their own vision, boundaries, and definition of done written in before they are built.

---

# PART III — ARCHITECTURE

## The Shape

The systems are not a chain. They are a set of domains that produce data, a single memory that holds it, and a mentor that reads it — all viewed through one shell.

- The **subsystems** (Zenith, BlackBook, Meridian) produce data and feed it into Atlas.
- **Atlas** is the one organized memory that holds it.
- **Apollo** reads Atlas and is the single interface the owner talks to; over time it matures into the mentor.
- **Olympus** is the exception: it is self-contained and walled off, viewed through Pantheon's window but never feeding the shared memory.
- **Pantheon** is the shell that holds and displays all of it.

Data flows *toward* the memory and the mentor. Nothing flows out of the memory back down into the subsystems to control them.

## Atlas: The Two Shelves

Atlas is the owner's organized memory, living on his machine. It naturally has two shelves:

- **The words shelf — Obsidian.** Journals and finished writing live as linked notes in Obsidian, where the owner can see how everything connects. This is the honest, human-readable home for the mind and the craft.
- **The numbers shelf — a local database.** Finances and their daily history live as structured data that can be summed, charted, and queried.

"Atlas" is the name for both shelves together, plus the lightweight search layer that lets Apollo read across them as if they were one. The owner experiences one place, because he only ever talks to Apollo.

Apollo's own conversations with the owner are also remembered in Atlas, so the mentor does not forget what it is told directly.

## Inside and Outside Pantheon

- **Built inside Pantheon:** Zenith, BlackBook, and Meridian are coded into the Pantheon application itself — not separate websites. The owner reaches them through tabs.
- **Outside Pantheon:** Olympus runs as its own separate code because it holds real money and must be its own self-contained system. Pantheon reaches it only through a read-only API, to display its status.

## How You Use It

- **Log in** to Pantheon (with a password, for security).
- **The Apollo tab** — talk to or chat with Apollo; it retrieves whatever it needs from Atlas.
- **The subsystem tab** — open Zenith, BlackBook, or Meridian directly inside Pantheon.
- **The Olympus view** — see Olympus's activity (PnL, Sharpe ratio, positions, what it's doing). View-only. Never run or edited from inside Pantheon.

The whole experience is frictionless and in one place: log in, write a little, do the daily journal, check finances, talk through life plans, move on.

---

# PART IV — THE SYSTEMS

Each system below is defined in full: its identity, what it is responsible for, its boundaries, and what "done and trustworthy" means for it. Specific tools (Alpaca, Plaid, Coinbase, Fidelity, Ollama, Obsidian) are named as *today's choices* — they are not law and may be swapped. How each system is wired belongs to its build plan.

## Apollo — the voice, and the mentor

**Identity.** Apollo is the single interface the owner talks to, and it grows up over time. It starts as a chatbot, gains voice (first transcribing what the owner says, then speaking back), and eventually becomes the mentor — the intelligence at the center of Pantheon. Apollo and the mentor are one and the same thing at different stages of maturity.

**What it is.** A mentor, not a mirror. Apollo is meant to understand the owner's perspective, then weigh other perspectives and challenge him — to give good advice on situations he needs help with, not simply agree or reflect him back. A mentor that only agrees is not a mentor.

**How it works.** Apollo runs on a local open-source model (Ollama), so the owner's data never leaves the machine. It is *not* a model the owner trains from scratch — he does not have the data or the hardware for that, and training is parked as a far-future option, not the plan. Apollo becomes a mentor by reading the owner's accumulated memory in Atlas through a capable model, with persistent memory of everything.

**Authority.** Reads all of Atlas. Writes only to BlackBook. Never edits Olympus, Meridian, or Zenith. Everything behind the owner's gate.

**Done.** Apollo correctly handles the everyday — for example, when the owner says he spent money, it logs it to BlackBook accurately, sorting it out so he isn't constantly entering things by hand — and it can answer questions about the owner's life with real context behind the answer.

## Atlas — the memory

**Identity.** The owner's single organized memory, living locally on his machine. The one place Apollo looks to know his whole life.

**What it is.** Two shelves and a search layer: Obsidian for the words (journals, finished writing), a local database for the numbers (finances and their daily history), and a lightweight index so Apollo can find the relevant pieces across both. It also holds Apollo's own conversation history.

**Boundaries.** Atlas holds everything the mentor reasons about — except Olympus, which is walled off and never feeds it. Atlas stores; it never rewrites the owner's words.

**Done.** Apollo can reliably retrieve relevant words and numbers from Atlas to answer a question or ask a good one.

## Olympus — the money maker (the star)

**Identity.** The autonomous trading and market-intelligence system. The key system — the one meant to generate real cashflow. It is a recursive self-improvement loop: it learns from market data, the debate council works on better strategies, and over time it finds profitable strategies and trades them, eventually on prop accounts with real money.

**What it owns.** Trading execution, ranking, its own trade history, and its own market intelligence. It is self-contained.

**Boundaries — the seal.** Olympus lives *outside* Pantheon and runs as its own code, because it holds real money. Pantheon reaches it only through a read-only API to display its status — PnL, Sharpe ratio, positions, activity. Nothing in Pantheon can ever write into Olympus or place a trade. Olympus does **not** feed Atlas: the owner does not ask the mentor about trading strategy (that work lives inside Olympus), so its deep data stays inside Olympus. The only exception is that when Olympus eventually holds real money, BlackBook shows that account balance as a read-only line, so the owner's net worth stays whole.

**Inside Olympus:**
- **Apex** — Olympus's brain. The machine-learning core that learns from Olympus's own trade data and informs its decisions.
- **Areopagus** — the five-agent debate council (Researcher, Critic, Risk Manager, Optimizer, Judge). It works on strategies and proposes improvements to Olympus, with owner approval.

**Current broker.** Alpaca (a choice, not law).

**Done.** Olympus is profitable for two months on paper trading. Only then is real money introduced — and live trading is permanently gated by the owner's explicit approval. Paper trading may be fully autonomous; live trading never is.

## BlackBook — the financial command center

**Identity.** The command center for all of the owner's personal money, and the source of financial truth.

**What it owns.** Everything money: cash accounts (Capital One), credit cards, crypto (Coinbase), and stock investments (Fidelity). It shows balances, holdings, today's performance and performance since purchase, and unrealized gains. It takes a **daily snapshot** at the end of each day — a record of the figures, not a screenshot — so the owner's financial history accumulates and his growth over time becomes visible. That daily snapshot is the data that goes to the numbers shelf in Atlas. It shows net worth at a glance, including the read-only line from Olympus once that holds real money.

**Scope.** Personal money only — no business. Today that means Capital One, Coinbase, and Fidelity.

**Boundaries.** BlackBook owns the money and only the money. It never holds journals or reflective writing (that is Meridian) and never holds Olympus's trading internals.

**Frictionless capture.** The goal is to make capturing all of it as automatic as possible — eventually connecting accounts directly (Plaid for the bank, plus Coinbase and Fidelity) so spending and balances track themselves. Quick manual capture remains a fallback, because automatic syncing across providers is the hardest, least reliable part and must never become a single point of failure that lets the system quietly fall out of date.

**Done.** Everything is visible in one place, capture is as frictionless as possible, and the daily record is trustworthy.

## Meridian — the reflective mind

**Identity.** The owner's reflective memory and self-understanding system — the "mind" half of the operating system. A clean place to write, and a way to learn about himself from what he's written.

**What it owns.** Journaling and reflection. Two kinds of entry: a **journal entry**, or a **goal**. The owner writes both himself, by hand.

**What it does.**
- Gives the owner good **daily reflective questions**, drawn from reading his past entries and writing to find the gaps — a person he hasn't written about, a feeling he keeps circling, a stretch he went quiet. No limits on what it can ask. The aim is to help him reflect and to track his thinking over time.
- Keeps his journals **organized and linked** in Obsidian (a second-brain method — broadly, the kind of approach popularized by "Building a Second Brain"; the exact method is a build-plan detail), so he can look back, see how his thinking shifts, and notice where he contradicts himself.
- Feeds the **mentor**: Meridian's raw journals and goals are the main well Apollo draws on to understand how the owner thinks and to give him grounded guidance.

**Boundaries — what it must never do.** Meridian does **not** auto-summarize, rewrite, or process the owner's writing into short summaries. The earlier version's "cycle" did this, and it flattened his writing and failed to truly link things — so it is removed. The raw journals stay exactly as written. The only thing under the hood is a lightweight index that *finds* relevant entries; it never replaces them. (See Principle 4: your words stay yours.)

**Where it lives.** Inside Pantheon, with its journals stored locally; Obsidian reads that same vault directly.

**Done.** The owner can write his entries and goals, get his daily questions, browse his history, and ask Apollo about himself with real context behind the answer.

## Zenith — the writing gym

**Identity.** The owner's writing studio and coach — a place to write against the clock and get better at the craft.

**What it does.** Runs timed writing sessions and coaches and scores the owner's writing on craft, so he improves over time. It is a coach, never a ghostwriter: it never writes for him. Over time it builds a clean corpus of his real, authentic writing. Its finished pieces land in Obsidian (the words shelf), so they join his linked notes and the mentor can read them.

**Boundaries.** Zenith never writes on the owner's behalf and never edits his words into something that isn't his. It coaches; he writes.

**Done.** Zenith has its full set of writing tools — the timer, free-write, stopwatch, and the rest — and works.

## Naming (locked)

- **Pantheon** refers only to the life operating system. It is not used for anything else.
- **Areopagus** is the name of Olympus's debate council. (Earlier documents called it the "Pantheon debate layer"; that name is retired.)
- **Atlas** is the name of the shared memory.
- The reflective system is spelled **Meridian**.

## Connectors

Some capabilities are reached through connectors rather than being subsystems. The **calendar** is one: Apollo reads the owner's Google Calendar through a connector to help organize his day. It is not a subsystem of its own.

---

# PART V — SECURITY

The owner is not technical, and the rule is caution over convenience. The model, in plain terms and most important first:

1. **Keep it local.** The biggest protection is that the data lives on the owner's machine, not in someone's cloud — there is nothing remote to breach. Atlas, journals, and finances all stay local. Only the few things that must touch the outside (bank sync, the broker) do.
2. **Local AI.** Because Apollo runs on a local model, the owner's journals and finances are never sent to any AI company.
3. **Lock the door and the safe.** A login password on Pantheon, plus full-disk encryption turned on (BitLocker, which is included on the owner's Windows 10 Pro). If the machine is lost or stolen, the data is unreadable, not just behind a password.
4. **Secrets never get committed.** API keys live in local files that never go to GitHub. This is the most common way people accidentally leak themselves, and it is a hard rule.
5. **Bank sync is read-only.** Plaid only reads transactions — it cannot move money — and its token is stored encrypted and local.
6. **Back it up.** Local-first has one catch: a dead drive must not erase everything. The data is small (text and a small database), so an encrypted backup — external drive or encrypted cloud — covers it easily. The code and plans are already backed up on GitHub; only the private data needs separate backup.
7. **Stay off the open internet for now.** Phone and remote access are wanted, but deferred until the systems are built, and then added through a private tunnel rather than by exposing the machine to the web.

**Current-machine note.** The owner's computer (a Dell OptiPlex 9020, Intel i7-4790, 32 GB RAM, no graphics card) runs everything except the full mentor comfortably. Two security facts matter: Windows 10 no longer receives security updates, and this machine cannot officially run Windows 11. The planned PC upgrade therefore does double duty — it enables the full local mentor *and* returns the system to a supported, patched operating system. Until then, be especially cautious with the bank-sync piece.

---

# PART VI — BUILD ORDER

Built in dependency order. Each step earns the next.

1. **This constitution** — the unison contract. Everything starts here.
2. **Olympus first** — build it until it is reliably collecting data.
3. **Pantheon and its inside systems** — while Olympus collects data, build Pantheon and, with it, Meridian, Zenith, and BlackBook (they are built inside Pantheon).
4. **Apex, then Areopagus** — once Olympus has accumulated enough clean data, bring Apex (its brain) online, then build Areopagus (the council).
5. **Apollo as the mentor — last** — the full local AI mentor comes after the PC upgrade. A small local model can run on the current machine earlier to handle lightweight work like generating Meridian questions, so there is reflection during the build; the upgrade is only for a *more capable* mentor, not for having one at all.

---

# PART VII — DEFINITION OF DONE

A system is "done and trustworthy" when:

- **Apollo** — handles the everyday accurately (e.g., logging finances to BlackBook with minimal manual entry) and answers questions about the owner's life with real context.
- **Olympus** — has been profitable for two months on paper; only then is real money introduced, always human-gated.
- **BlackBook** — shows everything in one place, with capture as frictionless as possible and a trustworthy daily record.
- **Zenith** — has all its writing tools (timer, free-write, stopwatch, and the rest) and works.
- **Meridian** — lets the owner write entries and goals, gives daily questions, lets him browse his history, and feeds Apollo real context.

"Done" never means finished forever. By the amend-don't-restart rule, the owner will deliberately add to this over time. That is the document working as designed.

---

# PART VIII — THE FAR FUTURE

The true north — recorded as direction, not commitment — is a holographic command center: a room where Pantheon surrounds the owner in projected light, where he speaks naturally while the system executes, and where he builds and reasons in real space rather than on a flat screen. It is likely a decade out and may never be built, and no decision in this document depends on it. It is here because it is the destination the whole project quietly points toward.

---

## Closing

Pantheon is one person's private operating system for his own life. Apollo is the voice that becomes the mentor. BlackBook knows the money. Meridian knows the mind. Zenith sharpens the craft. Olympus makes the money and stays sealed. Atlas remembers all of it, and Pantheon is the one place it can all be seen.

Built by compounding. Changed by amendment. Owned, and gated, by one person.

**PANTHEON**
