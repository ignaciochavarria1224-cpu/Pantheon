# The Olympus Constitution

*The founding law of Olympus — the money-maker.*
*A subsystem of Pantheon. Subordinate to the Pantheon Constitution.*

**Version:** 1.0
**Ratified:** May 2026
**Owner:** Ignacio Chavarria

---

## Preamble

Olympus is the trading subsystem of Pantheon. Its purpose is to make money.

This document is the founding law of Olympus. It inherits from the Pantheon Constitution and may never contradict it. Where this document is silent, the Pantheon Constitution governs. Where the Pantheon Constitution speaks, it wins.

This is not a build plan. It does not say how Olympus is constructed. It says what is true about Olympus and what cannot change. The build plan and the migration plan live beneath this document and must obey it.

Olympus is governed by hard experience. Its first generation ran for seven weeks, reported a profit while the real account was losing money, and taught one permanent lesson: a trading system that records its own intentions as if they were facts will lie to you. Every article here is built to make that failure impossible to repeat.

---

## Article I — Identity and Purpose

Olympus is a private, single-user algorithmic trading system.

Its purpose is singular: **generate cashflow through trading.** Learning about markets and quantitative systems happens along the way, but that learning is a byproduct, not the goal. When a decision must be judged, it is judged against whether it helps Olympus make money safely — not against whether it is interesting.

Olympus is permanently a trading system. It is not a research lab, not a general analytics tool, and not a place for ideas that do not serve trading.

---

## Article II — The Supreme Law of Olympus

**No state is recorded without broker confirmation.**

Olympus may never write a trade, a fill, a price, or a position into its own records until the broker has confirmed it. There is no fallback to planned or intended values. If confirmation does not arrive, the event did not happen as far as Olympus is concerned, and nothing is recorded.

This is the most important rule in the entire subsystem. It is the direct answer to the failure that defined the first generation. It is not an engineering preference. It is constitutional, and it is absolute. Every other part of Olympus is built on top of it.

A companion rule follows from it: **the broker is always the truth.** When Olympus's own records and the broker's records disagree, the broker is right and Olympus is wrong, and Olympus must correct itself to match.

---

## Article III — The Two Gates

Olympus separates two kinds of decisions, and treats them completely differently.

**The trade gate is open.** Individual trades — entering, exiting, rotating positions — are fully autonomous. Olympus never asks permission to place a trade. This is true in paper and in live. Asking a human to approve individual trades would be impossible at the system's speed and pointless given that no human can judge a single trade in isolation.

**The capital gate is closed.** The decisions that put real money at risk — whether to trade live at all, how much real money to allocate, and whether to increase that allocation — are never made by Olympus alone. These decisions are rare, deliberate, and human-gated. Areopagus may propose them; the owner approves them; nothing real moves until that approval is given.

The principle beneath both: **Olympus may trade freely, but it may never decide on its own to risk more of the owner's real money.**

---

## Article IV — The Promotion Bar

Real capital is never risked on an unproven strategy.

Before any strategy may be promoted from paper to live, it must clear a high bar of demonstrated performance — strong profitability, performance that holds up on data it was not tuned against, a meaningful number of trades, positive expectancy, and no dangerous concentration in a few lucky wins.

The **requirement** of a high bar is constitutional and permanent. The **specific numbers** that define the bar are tunable parameters that Areopagus may propose adjusting, with the owner's approval. The bar may move; the existence of a demanding bar may not.

---

## Article V — Autonomous Safety Limits

Because trades are autonomous, Olympus must protect itself between the owner's rare decisions. The following safety mechanisms are constitutionally required to exist, even though their exact thresholds are tunable:

- A hard limit on how much can be lost in a single day, after which trading halts on its own.
- A maximum drawdown that, once reached, automatically stops live trading.
- Caps on how large any single position may be.
- A kill switch the owner can trigger at any time to halt all trading instantly.

These are not optional features to be added later. A version of Olympus that trades real money without them is unconstitutional. The numbers may be set and changed through the gated process; the existence of these protections may not be removed.

---

## Article VI — Apex, the Brain

Apex is the intelligence of Olympus: its memory, its interpretation, and its judgment. Apex lives inside Olympus and its authority does not extend beyond it.

Apex has two faces:

**Apex looks backward — the historian.** It reads the full record of what Olympus has done and makes it understandable: which conditions produced good trades, which produced losses, what patterns repeat, what dangers cluster. This is its foundational job and the one it must always do well.

**Apex looks forward — the advisor.** What it learns from the past feeds into better trade selection in the future. But this influence is never direct and never unchecked. Apex does not seize control of trading. Its learning reaches the live machinery only through Areopagus and the owner's approval. Apex advises; it does not command.

**Apex begins simple and grows only as clean data justifies it.** Its earliest form is plain summarization and rule-based interpretation. More sophisticated methods are added only after there is enough trustworthy data to support them and the simpler version has proven it works. Complexity is earned, never assumed. Acting on conclusions drawn from thin or dirty data is precisely the mistake Olympus exists to avoid.

---

## Article VII — Areopagus, the Council

Areopagus is the deliberative council inside Olympus. It is the only automated body permitted to change Olympus's machinery, and even then only with the owner's approval.

Areopagus examines every proposed change through five fixed roles, each a distinct way of thinking:

- **Researcher** — what is promising, and what evidence supports it.
- **Critic** — what looks good but is weak, thin, or misleading.
- **Risk Manager** — what is dangerous and must not be touched.
- **Optimizer** — how a sound idea could be made better.
- **Judge** — who compresses the debate into one clear, prioritized conclusion and a single recommended action.

Areopagus may both **propose** changes to Olympus and **carry them out** once approved — including changes to strategies, parameters, and ranking behavior. This power exists deliberately: the owner is not a technical builder, and the intelligence inside the system will, over time, understand Olympus more deeply than the owner does. It is better for that intelligence to propose well-reasoned changes than for changes to be made carelessly or not at all.

But every Areopagus conclusion is a recommendation until the owner approves it. The owner expects to evaluate these recommendations with the help of an outside reviewer before approving. Areopagus is exclusive to Olympus; its adversarial discipline is justified only where real money is at stake.

---

## Article VIII — The Seal

Olympus is sealed. This is the strongest protection in Pantheon, and Olympus carries it because Olympus is the only subsystem that risks real money and acts on its own in live markets.

The Seal has two halves:

**Reading is open.** Pantheon — and the owner through Apollo — may read everything Olympus produces and everything about how it is configured: its trades, its performance, its strategies, its parameters, its history. The owner should be able to ask how trading is going and get a complete, truthful answer.

**Writing is sealed.** No part of Pantheon, and no autonomous process anywhere, may change Olympus's internal machinery on its own. The only paths that may change the machinery are the owner directly, and Areopagus with the owner's approval. Nothing else reaches in.

---

## Article IX — The Self-Improvement Loop

Olympus is built to get better over time through a repeating loop: it trades, Apex studies the results, Areopagus debates what should change, the owner approves, the change goes in, and the loop runs again.

**The learning is recursive and autonomous.** Olympus observes and learns from itself continuously, without asking permission, especially in paper where experimentation is free.

**Changing the machinery is human-gated.** No matter how confident the loop becomes, no change to the real money-making machinery takes effect without the owner's approval. The system may learn as fast as it can; it may only change itself as deliberately as the owner allows.

This is the same spine that runs through all of Pantheon: learn broadly, change selectively, risk real money slowly.

---

## Article X — Paper and Live

Olympus operates in two environments, and the boundary between them is permanent.

**Paper is the learning environment.** Here Olympus is fully autonomous and free to experiment, scan, enter, exit, rotate, and accumulate experience. No real money is at stake, so speed and freedom are the priority.

**Live is the proving ground for real capital.** Entry into live is governed by the capital gate (Article III), the promotion bar (Article IV), and the safety limits (Article V). Live execution of individual trades is autonomous once a strategy is approved and funded, but the decision to be in live at all, and with how much, always belongs to the owner.

Paper trading being autonomous does not make live trading autonomous. The separation does not dissolve as the system matures. It is permanent.

---

## Article XI — Outside Tools

Olympus may, once stable, bring in outside tools to strengthen its judgment — for example, external models that forecast where prices may move.

Two rules bind any such tool:

1. **An outside tool is only ever an input, never a replacement.** It may inform Olympus's ranking or Apex's interpretation. It may never become the decision-maker or override Olympus's own judgment.
2. **An outside tool enters only through the gate.** Adopting one is a change to the machinery, and so it follows the same path as any other change: proposed, debated by Areopagus, approved by the owner, recorded.

No specific outside tool is named in this constitution. Any tool that is adopted is recorded in the build plan and the change log, not here. This keeps Olympus free to use the best tool available without binding its founding law to any one product.

---

## Article XII — The Broker

Olympus trades through a brokerage. At the time of this writing that broker is Alpaca, chosen because it is capable and free.

The broker is a choice, not a law. It may be changed if a better option appears, through the normal gated process. What is constitutional is not *which* broker Olympus uses, but that Olympus is always bound to a real broker as its source of truth (Article II) and that real-capital decisions through that broker are always gated (Article III).

---

## Article XIII — Amendment

This constitution changes only by the owner's deliberate act. No part of Olympus — not Apex, not Areopagus, not the self-improvement loop — may rewrite this document or loosen its protections on its own.

Areopagus may propose amendments to this constitution the same way it proposes any other change. But amending the founding law is the most consequential change of all, and it takes effect only when the owner consciously records it here.

The protections in this document — broker confirmation, the two gates, the promotion bar, the safety limits, the Seal — exist because their absence already cost the owner real money once. They are not to be weakened casually, and never automatically.

---

## Final Position

Olympus exists to make money, slowly and safely, and to get better at it over time.

It records nothing it cannot confirm. It trades freely but risks real money only with the owner's blessing. Its brain learns from the past and advises the future, but never seizes control. Its council may propose and build, but only the owner may approve. It is sealed against every hand but the owner's and the council's.

It learns as fast as it can. It changes only as carefully as it must.

---

*Olympus · Apex · Areopagus*
*A subsystem of Pantheon.*
*Confirm before recording. Trade freely. Risk slowly. Change with care.*
