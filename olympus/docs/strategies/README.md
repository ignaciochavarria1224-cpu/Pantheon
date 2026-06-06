# Olympus — Strategy Specifications

This folder holds the strategies Olympus will trade. Strategies are **chosen by the owner
after deep research** and wired in at **Phase 2** (the foundation in Phase 1 is
strategy-agnostic). Each strategy is tagged by `strategy_id` and runs in the shared pooled
paper account.

> **Source of record:** the full deep-research document (v1.0, June 2026) is authoritative
> for every backtest number and citation. Save the original file here as
> **`STRATEGY_RESEARCH_v1.md`** (kept verbatim from the owner's source to preserve exact
> figures). This README is the clean, actionable summary.

## Scope (locked)

US stocks & ETFs only (Alpaca equities). No futures/FX/options; crypto deferred. Standalone,
self-contained strategies (not ranking-engine variants — that comes later). Daily primary;
intraday no finer than 15-min. No HFT, no hard-to-borrow shorts. All long-only to start.

## The 7 strategies

| # | `strategy_id` | Direction | Timeframe | Core edge | Evidence grade |
|---|---|---|---|---|---|
| 1 | `dual_momentum_gem` | Long-only rotation (SPY/VEU/AGG) | Monthly, daily bars | Absolute + relative momentum (Antonacci 2014) | Established |
| 2 | `residual_momentum_xs` | Long-only top decile, S&P 500 | Monthly, daily bars | Cross-sectional momentum on FF3 residuals (Blitz, Huij, Martens 2011) | Established |
| 3 | `rsi2_pullback_etf` | Long-only, ETF basket | Daily bars | Short-term mean-reversion in uptrend (Connors & Alvarez 2008) | Established-but-decayed |
| 4 | `ibs_etf_meanrev` | Long-only, ETF basket | Daily bars | Close-position mean reversion via IBS (Pagonidis 2014) | Established |
| 5 | `bab_low_vol` | Long-only low-beta (or SPLV proxy) | Monthly, daily bars | Low-volatility / BAB (Frazzini & Pedersen 2014; Baker et al. 2011) | Established |
| 6 | `quality_qmj_long` | Long-only top-30% quality (or QUAL proxy) | Quarterly, daily bars | Quality factor (Asness, Frazzini, Pedersen 2019) | Established |
| 7 | `pead_sue` | Long-only positive-surprise basket | Daily bars; 60-day hold | Post-earnings-announcement drift (Bernard & Thomas 1989) | Established-but-decayed |

Diversified across three return drivers (trend, mean-reversion, factor) and three horizons
(days, a month, a quarter), engineered for low pairwise correlation rather than max
individual Sharpe.

## Implementation order (staged over Phase 2+)

1. **`dual_momentum_gem` + `ibs_etf_meanrev`** — need only Alpaca-native daily bars. GEM
   proves the slow-rebalance path; IBS gives trade count to validate the plumbing.
2. **`rsi2_pullback_etf`** — same data; complementary signal; measure live correlation vs IBS.
3. **`bab_low_vol` + `quality_qmj_long`** — via SPLV / QUAL ETF proxies (no fundamentals).
4. **`residual_momentum_xs`** — needs Ken French factor data + S&P 500 constituents.
5. **`pead_sue`** — needs a third-party earnings/SUE feed (highest data complexity).

## Promotion bar to real capital (per strategy — Article IV; tunable numbers)

- ≥ 50 paper trades (3, 4, 7) or ≥ 24 monthly rebalances (1, 2, 5, 6).
- Net Sharpe ≥ 0.5 on data the strategy was **not** tuned against.
- Max drawdown ≤ 1.5× the documented academic max drawdown.
- No single trade contributing > 25% of total PnL (concentration check).
- Correlation with SPY < 0.7 for at least four of the seven (diversification check).

## Deliberately excluded (decayed net of costs — documented in the full research)

- Overnight close-to-open effect (collapses under retail ETF frictions).
- Turn-of-the-month effect (arbitraged to ~zero post-2010).
- Naive Jegadeesh-Titman 12-1 momentum (dominated by residual momentum; partly captured by GEM).
