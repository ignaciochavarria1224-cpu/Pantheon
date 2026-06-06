# Pantheon

A private life operating system for one owner. This repository is the single
consolidated home for Pantheon and all of its systems. Each system lives in its own
subfolder. **Olympus is its own sealed codebase** — its own data, reachable by the rest
of Pantheon only through a read-only API, never written to from outside (the "Seal").

The supreme founding document is [`Pantheon_Constitution.md`](Pantheon_Constitution.md).

## Structure

| Folder | System | Status |
|---|---|---|
| `olympus/` | Trading & market-learning — sealed; own DB, read-only API out | **in progress (Phase 0/1)** |
| `pantheon-os/` | The shell that holds and displays everything | planned |
| `apollo/` | The voice that becomes the mentor | planned |
| `atlas/` | The shared memory (Obsidian words + a local numbers DB + search) | planned |
| `blackbook/` | Financial command center | planned |
| `meridian/` | Reflective journaling & goals | planned |
| `zenith/` | The writing gym | planned |

## Build order (per the constitution)

1. **Olympus first** — until it reliably collects *trustworthy* data.
2. **Pantheon shell** + Meridian, BlackBook, Zenith (built inside Pantheon).
3. **Apex** (Olympus's historian) → **Areopagus** (the five-role council).
4. **Apollo** as the full mentor (after the PC upgrade).

## Laws that never bend

- **Never record a state the broker hasn't confirmed** (Olympus Article II).
- **The owner is the only gate;** live money is always human-gated.
- **Local-first and private;** secrets never leave the machine and are never committed.
