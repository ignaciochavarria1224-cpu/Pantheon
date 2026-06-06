> **Transcription note.** This is the owner's deep-research document (v1.0, June 2026),
> saved into the repo. Special symbols (—, ≥, ≤, ×, σ, β, α, ε, →, ~) were normalized from a
> copy that arrived with encoding artifacts; **all backtest figures and citations are
> preserved verbatim.** If any symbol looks off, the owner's original file is authoritative.

---

# Olympus Strategy Specification Document
## 7 Proven, Codeable Systematic Equity Strategies for a Private Algorithmic Trading System

**Scope:** US stocks and ETFs only, traded via Alpaca equities. No futures, options, FX, or crypto. Daily bars primary; intraday no finer than 15-minute bars. No HFT, no co-location, no hard-to-borrow shorts.

---

## TL;DR (the 3 things)

- **Seven strategies, deliberately diversified across three return drivers (trend, mean-reversion, factor) and three holding horizons (1–10 days, 1 month, 1 quarter):** GEM dual momentum, residual cross-sectional momentum, RSI(2) pullback on ETFs, Internal Bar Strength mean reversion, low-volatility/BAB long-only, Quality (QMJ) long-only, and Post-Earnings-Announcement Drift. Every strategy has a peer-reviewed academic source or a documented practitioner backtest. None require shorting illiquid names or executing faster than 15-minute bars.
- **Three are graded "established-but-decayed"** (RSI(2), PEAD, and to a lesser extent GEM). Two well-known anomalies — turn-of-the-month and the overnight close-to-open effect — were **deliberately excluded** as standalone strategies because honest post-publication evidence shows their net-of-cost edge has collapsed (Quantseeker 2024; Bartolini 2020). This document does not pretend the 1990s headline numbers will repeat.
- **The set is engineered for low pairwise correlation, not maximum individual Sharpe.** Pairwise correlations of monthly return streams are estimated low (~0.0–0.3) across most pairs, with one deliberate redundancy (RSI(2) and IBS) kept for trade-count robustness on overlapping ETF universes. This gives the downstream learning layer genuine contrast rather than seven flavors of momentum.

---

## Summary Table

| # | strategy_id | Direction | Timeframe | Core Edge | Evidence Grade |
|---|---|---|---|---|---|
| 1 | `dual_momentum_gem` | Long-only rotation (SPY/VEU/AGG) | Monthly, daily bars | Absolute + relative momentum (Antonacci 2014) | Established |
| 2 | `residual_momentum_xs` | Long-only top decile of S&P 500 | Monthly, daily bars | Cross-sectional momentum on FF3 residuals (Blitz, Huij, Martens 2011) | Established |
| 3 | `rsi2_pullback_etf` | Long-only on ETF basket | Daily bars | Short-term mean-reversion in uptrend (Connors & Alvarez 2008) | Established-but-decayed |
| 4 | `ibs_etf_meanrev` | Long-only on ETF basket | Daily bars | Close-position mean reversion via IBS (Pagonidis 2014, NAAIM) | Established |
| 5 | `bab_low_vol` | Long-only top-100 low-beta (or SPLV proxy) | Monthly, daily bars | Low-volatility / BAB anomaly (Frazzini & Pedersen 2014; Baker, Bradley, Wurgler 2011) | Established |
| 6 | `quality_qmj_long` | Long-only top-30% quality (or QUAL proxy) | Quarterly, daily bars | Quality factor (Asness, Frazzini, Pedersen 2019) | Established |
| 7 | `pead_sue` | Long-only positive-surprise basket | Daily bars; 60-day hold | Post-earnings-announcement drift (Bernard & Thomas 1989; Ball & Brown 1968) | Established-but-decayed |

---

## Key Findings

1. **Trend + factor + mean-reversion is the canonical three-legged diversification stool.** The selected set covers all three legs with at least two well-documented strategies per leg, and intentionally spans daily through quarterly horizons.
2. **Post-publication decay is real, uneven, and well-documented.** Naive Jegadeesh-Titman cross-sectional momentum and naive PEAD have weakened materially since their seminal papers. Residual momentum (Blitz et al. 2011) and multi-quarter SUE patterns (Beyond the Last Surprise, 2024) survive out-of-sample where the naive versions did not. RSI(2) on a single index has decayed but still works in a diversified ETF basket with regime filter.
3. **Frictions matter more than academic backtests admit.** Every strategy below has been screened for survivability under Alpaca-style retail equity frictions (~1–3 bps slippage on liquid ETFs, zero commissions). The most cost-fragile candidates — overnight return strategy on SPY, equal-weighted small-cap BAB long-short — were excluded or restricted to long-only large-cap implementations.
4. **The promotion bar is set against modern out-of-sample replications, not original-paper headline statistics**, in every "Evidence" section below. Where a gap between original numbers and recent replications exists, both are reported.

---

## Strategy 1 — `dual_momentum_gem` (Global Equities Momentum)

### 1. Name + Thesis
**Antonacci Global Equities Momentum (GEM).** Combines absolute (time-series) momentum and relative (cross-sectional) momentum across just three ETFs to ride equity trends and rotate into bonds during equity bear markets.

### 2. Direction
Long-only, rotational. Holds exactly one of {SPY, VEU, AGG} at any time.

### 3. Timeframe & Data
- **Bars:** Daily; signal computed on last trading day of each month at close.
- **Universe:** SPY (S&P 500), VEU (FTSE All-World ex-US), AGG (US Aggregate Bonds), BIL (1–3 month T-Bills, used as the absolute-momentum benchmark).
- **Inputs:** 12-month total return (252 trading days) for each instrument.

### 4. Entry Rules (executed at close of last trading day of month)
Let `R12(X)` = trailing 252-trading-day total return of instrument X (dividends reinvested).
1. If `R12(SPY) > R12(BIL)` **AND** `R12(SPY) >= R12(VEU)` -> hold 100% SPY for next month.
2. Else if `R12(VEU) > R12(BIL)` **AND** `R12(VEU) > R12(SPY)` -> hold 100% VEU for next month.
3. Else (both equities fail the absolute-momentum test vs. T-bills) -> hold 100% AGG for next month.

### 5. Exit Rules
Exit only occurs at the next month-end rebalance when the rule above selects a different instrument. No intra-month stops, no take-profits.

### 6. Sizing & Risk
- 100% of `strategy_id` sleeve equity into one ETF.
- Account-level sleeve: 15–25% of Olympus equity; within the sleeve fully invested.
- No leverage. Maximum historical drawdown for GEM in Antonacci's publication was under 20%; assume up to 30% in live use.

### 7. Filters
None beyond the rule itself. The absolute-momentum check vs. T-bills *is* the regime filter.

### 8. Evidence
- **Primary source:** Antonacci, Gary (2014). *Dual Momentum Investing: An Innovative Strategy for Higher Returns with Lower Risk.* McGraw-Hill Education. Also: Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum." *Journal of Management & Entrepreneurship*, 2(1), 27–55.
- **Theoretical foundations:** Jegadeesh, N. & Titman, S. (1993). "Returns to Buying Winners and Selling Losers," *Journal of Finance*, 48(1), 65–91 (relative momentum); Moskowitz, T. J., Ooi, Y. H., Pedersen, L. H. (2012). "Time Series Momentum," *Journal of Financial Economics*, 104(2), 228–250 (absolute momentum).
- **Reported backtest (Antonacci, applied to indices 1971–2013 in the book; extended on optimalmomentum.com):**
  - CAGR ~ 16.2% vs. S&P 500 ~ 10.5% (cited verbatim in the Meb Faber podcast episode #45: "The compound annual growth rate applied to the indices is 16.2% dating back to 1971, compared to the S&P's 10.5%").
  - Maximum month-end drawdown: under 20% vs. S&P 500's ~51%.
  - "The combined whole is greater than the sum of the parts... GEM shows an impressive 440 basis [points of outperformance]" — Antonacci 2017, *Medium*.
- **Out-of-sample / decay (honestly stated):** Performance since 2014 publication has been mediocre. Hoffstein, C. (January 2019), "Fragility Case Study: Dual Momentum GEM," *Flirting with Models* blog (Newfound Research), documents material specification risk: moving the lookback from 9 to 10 months changed 2010 GEM returns from -9.31% to +12.2%. From 2015 onward GEM has roughly matched but not beaten a US-equity buy-and-hold. The strategy remains valid as a regime-aware risk reducer but the published 16% CAGR is unlikely to repeat.
- **Win rate / trade count:** Approximately 2–4 trades per year (most months are "stay put"). Not reported as a win-rate metric in the source — the strategy is regime-based, not trade-based.

---

## Strategy 2 — `residual_momentum_xs` (Residual / Idiosyncratic Momentum)

### 1. Name + Thesis
**Cross-sectional momentum on Fama-French residual returns.** Standard 12-1 momentum suffers periodic crashes (e.g., 2009) due to time-varying factor exposures. Ranking stocks on the *residuals* from a Fama-French 3-factor regression isolates idiosyncratic price persistence and approximately doubles the risk-adjusted return of naive momentum.

### 2. Direction
Long-only top decile (recommended for Olympus to avoid borrow constraints and crash risk). The long-short version is documented but defers to a later cross-sectional ranking project.

### 3. Timeframe & Data
- **Bars:** Daily; signals/rebalancing monthly (last trading day).
- **Universe:** S&P 500 constituents as of the rebalance date. (Russell 1000 if data is available; the original paper used CRSP all-US-stocks, but Olympus should stick to S&P 500 for liquidity conservatism.)
- **Inputs:**
  - Monthly total returns for each stock for the trailing 36 months.
  - Monthly Fama-French 3-factor data (Mkt-Rf, SMB, HML) from Ken French's data library.
  - Fama-French regression of stock excess returns on the three factors over the trailing 36 months.

### 4. Entry Rules (executed at close of last trading day of month)
1. For each stock i in the S&P 500 universe with >= 36 months of return history:
   - Run regression: `R_i(t) - Rf(t) = α_i + β_1·MKT(t) + β_2·SMB(t) + β_3·HML(t) + ε_i(t)` over trailing 36 months.
   - Compute the standardized residual momentum signal: sum of monthly residuals over months t-12 through t-2 (skip the most recent month to avoid 1-month reversal), divided by the standard deviation of those 11 residuals.
2. Rank all qualifying stocks by this standardized residual-momentum score, descending.
3. Buy the top decile (~50 names) equally weighted. Hold for one month, then re-rank.

### 5. Exit Rules
Pure rebalance: stocks dropping out of the top decile at month-end are sold; new top-decile entrants are bought. No stops or take-profits.

### 6. Sizing & Risk
- Equal-weight across ~50 names within the sleeve.
- Per-name cap: 2% of sleeve equity (1/50).
- Sleeve cap: 15–25% of Olympus equity.

### 7. Filters
- Liquidity: exclude any stock with 20-day average dollar volume below $10M (S&P 500 names almost always pass).
- Price floor: >= $5.
- No signal-level regime filter, but Olympus may overlay a portfolio-level kill switch (e.g., halve allocation if SPY < 200-day SMA).

### 8. Evidence
- **Primary source:** Blitz, D., Huij, J., Martens, M. (2011). "Residual Momentum." *Journal of Empirical Finance*, 18(3), 506–521.
- **Supporting:** Blitz, D., Hanauer, M. X., Vidojevic, M. (2017). "The Idiosyncratic Momentum Anomaly." SSRN; Huij, J. & Lansdorp, S. (2017). "Residual Momentum and Reversal Strategies Revisited." SSRN.
- **Original backtest (Blitz et al. 2011, US stocks 1926–2009):**
  - "Residual momentum earns risk-adjusted profits that are about twice as large as those associated with total return momentum; is more consistent over time; and less concentrated in the extremes of the cross-section of stocks." (Verbatim abstract.)
  - Crucially during Jan 2000–Dec 2009: "total return momentum strategies appear to have lost their profitability... we find a return of -8.5% per annum over the period January 2000 to December 2009. Residual momentum, on the other hand, has remained profitable, generating a return of 4.7% per annum over the same time period." (Verbatim.)
- **Out-of-sample (Huij & Lansdorp 2017, post-publication 2009–2015):** Residual momentum strategies "have significantly higher return-to-risk ratios... are robust across different global stock universes and hold up out-of-sample."
- **Reported Sharpe ratio:** Blitz, Hanauer, Vidojevic (2017) document Sharpe ratio of the long-short residual momentum factor approximately 2x that of conventional momentum over 1926–2015.
- **Win rate / expectancy:** Not reported in source (this is a portfolio-sort study, not a discrete-trade study). Reported instead is a monotonic mean-return relationship across deciles; the long-only top decile delivers several percentage points of annual excess return over the equal-weight benchmark.

---

## Strategy 3 — `rsi2_pullback_etf` (Connors RSI(2) Mean Reversion on ETFs)

### 1. Name + Thesis
**RSI(2) pullback in an uptrend.** Even strongly trending ETFs experience 1–3 day pullbacks that revert. Buy oversold short-term dips during confirmed long-term uptrends.

### 2. Direction
Long-only.

### 3. Timeframe & Data
- **Bars:** Daily.
- **Universe:** Liquid index and sector ETFs — SPY, QQQ, IWM, DIA, EFA, EEM, XLK, XLF, XLE, XLY, XLP, XLV, XLI, XLU, XLB, XLRE, XLC (17 ETFs). All trivially borrowable, sub-penny-spread, billions of daily dollar volume.
- **Indicators:**
  - 2-period RSI (Wilder smoothing).
  - 200-day simple moving average (regime filter).
  - 5-day simple moving average (exit trigger).

### 4. Entry Rules (evaluated at daily close)
For each ETF in the universe:
1. Today's close > 200-day SMA of close (long-term uptrend confirmed).
2. 2-period RSI of close < 10 (deeply oversold short-term).
3. No existing position in this ETF.
4. If all three true -> buy at today's close (market-on-close order) or next-day open if execution constraints require.

### 5. Exit Rules
Exit at the close of the next day on which **either**:
- The closing price > 5-day SMA of close, **or**
- 10 calendar days (~7 trading days) have passed since entry (time stop).

No fixed-percent stop-loss. Connors' research demonstrated fixed stops degrade RSI(2) performance. The 10-day time stop is a tail-risk safeguard not in the original.

### 6. Sizing & Risk
- Risk per trade: 0.5–1.0% of sleeve equity, sized via ATR(10) × 2.5 as the implicit stop distance for position sizing (even though no hard stop is placed): `shares = (sleeve_equity × 0.005) / (2.5 × ATR10)`.
- Cap any single position at 10% of sleeve equity.
- Sleeve allocation: 10–15% of Olympus equity.
- Maximum concurrent positions: 8 (avoid correlated piling-in during sector-wide selloffs).

### 7. Filters
- Volatility filter: skip a signal if the ETF's 20-day realized volatility is in the top 5% of its 5-year history (avoids panic-day knife-catching where the next day can gap further).
- 200-day SMA regime filter is built into the entry rule itself.

### 8. Evidence
- **Primary source:** Connors, L. & Alvarez, C. (2008). *Short Term Trading Strategies That Work: A Quantified Guide to Trading Stocks and ETFs.* TradingMarkets Publishing. Chapter "The 2-Period RSI — The Trader's Holy Grail of Indicators?"
- **Original Connors research scale:** The book's publisher description for Chapter 9 confirms "test results when applied to over 77,000 trades since 1995" for the 2-period RSI oscillator. The book itself does not state a single headline win-rate percentage; the often-quoted "70–85% win rate on broad indices" figure traces to a secondary source — QuantifiedStrategies.com's "RSI 2 Strategy" article: "His work with collaborator Cesar Alvarez from the mid-1990s through 2010 produced rigorous backtests demonstrating win rates exceeding 70-85% on broad indices when following specific trading rules." Treat as approximate.
- **Independent replications:**
  - StockCharts ChartSchool RSI(2) page (chartschool.stockcharts.com) confirms the four-step rule (200-day SMA, RSI(2) < 5 or 10, enter at close, exit on 5-day SMA cross).
  - Trade2Win Forums backtest (russs123's RSI replication, 2018) confirms the strategy "seems to hold up over a long testing period... It has been in the public domain since the book was published in 2010, and yet in my backtest it continues to perform well after that" — but flags "the annualised return is poor... a result of the infrequent trades."
- **Post-publication decay:** RSI(2) on SPY alone has degraded; the strategy is in the market only ~15–20% of the time, so total return is modest. Win rate remains high (~70%), but per-trade edge has compressed since 2010. The 17-ETF basket specified above restores enough trade count to be useful.
- **Evidence grade:** **Established-but-decayed.** Use as a diversifier, not a workhorse.
- **Win rate / expectancy (modern replication consensus):** Win rate ~70–80%; average win and average loss similar in magnitude (1–2% per trade); expectancy ~0.4–0.6% gross per trade. Sharpe of standalone strategy approximately 0.7–1.0 on a diversified ETF basket; lower on single instruments.

---

## Strategy 4 — `ibs_etf_meanrev` (Internal Bar Strength Mean Reversion)

### 1. Name + Thesis
**IBS mean reversion on equity ETFs.** Equity index ETFs that close near the *low* of their daily range tend to outperform the next day; those closing near the *high* tend to underperform. IBS captures intraday distress/exuberance that mean-reverts over 1–3 days.

### 2. Direction
Long-only. (A short variant exists but is less reliable on ETFs in a secular uptrend.)

### 3. Timeframe & Data
- **Bars:** Daily.
- **Universe:** SPY, QQQ, IWM, EFA, EEM, plus the 11 sector SPDRs (same as Strategy 3 universe, intentionally overlapping — the two signals will not always coincide).
- **Indicator:** IBS = (Close - Low) / (High - Low), computed on daily bars. Range [0, 1].

### 4. Entry Rules (evaluated at daily close)
For each ETF:
1. Today's IBS < 0.20.
2. Today's close > 200-day SMA of close (regime filter — added to the base Pagonidis rule for robustness in bear markets).
3. No existing position in this ETF.
4. If all true -> enter long at today's close.

### 5. Exit Rules
Exit at the close of any subsequent day where **either**:
- IBS > 0.80 (mean reversion complete), **or**
- Close > previous day's high (price has broken upward), **or**
- 5 trading days have elapsed since entry (time stop).

### 6. Sizing & Risk
- Fixed-fractional: each open position = 1/8 of sleeve equity (max 8 concurrent positions).
- Sleeve allocation: 10–15% of Olympus equity.
- No hard stop-loss for the same reason as Strategy 3.

### 7. Filters
- The 200-day SMA filter is built into the entry rule.
- Optional volatility-spike confirmation: also require VIX > 15 (Pagonidis 2014 documents mean reversion works better when volatility is elevated).

### 8. Evidence
- **Primary source:** Pagonidis, A. S. (2014). "The IBS Effect: Mean Reversion in Equity ETFs." *NAAIM Wagner Award paper.* Available at naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf
- **Reported backtest (Pagonidis 2014, multiple equity index ETFs ~1993–2013):**
  - "Equity indices exhibit mean reversion in daily returns. A simple and powerful way to capture this effect is the Internal Bar Strength technical indicator... When the closing price is near the bottom of the day's range, close-to-close returns on the following day tend to be higher than average, and vice versa." (Verbatim.)
  - Adding an IBS filter to a separate RSI strategy: "improves total returns by almost 10 percentage points while decreasing time spent in the market by almost 45%." (Verbatim.)
- **Independent replications (Quantified Strategies; Robust Trader; Backtestwizard):**
  - On SPY 1993–2020 with IBS < 0.20 long entries, exit at IBS > 0.80: annual return ~7–9% with time-in-market ~20–25%.
  - Backtestwizard documents that, when combined with a trend-following SPY strategy, the IBS QQQ sleeve standalone "produced a maximum draw-down of 14.83% and a CAR/MDD of 0.86."
- **Win rate / expectancy:** Win rate ~60–65%; average winners modestly larger than losers. 30–60 trades/year per ETF.
- **Evidence grade:** Established. The effect has persisted post-2014 publication in independent replications, though magnitudes are smaller than in the original sample.

---

## Strategy 5 — `bab_low_vol` (Low-Volatility / Betting-Against-Beta, Long-Only)

### 1. Name + Thesis
**Low-volatility / low-beta anomaly.** Stocks with low market beta have produced *higher* risk-adjusted returns than the CAPM predicts. Leverage-constrained investors bid up high-beta names, leaving low-beta stocks under-priced. Olympus exploits this in a long-only top-decile form rather than the leveraged long-short BAB, to avoid leverage and shorting.

### 2. Direction
Long-only. (The pure Frazzini-Pedersen BAB is long-leveraged-low-beta / short-de-leveraged-high-beta. For Olympus, simplified to long-only.)

### 3. Timeframe & Data
- **Bars:** Daily, signals computed monthly (last trading day).
- **Universe:** S&P 500 constituents. **Implementation choice:** for low-cost simplicity, hold the SPLV (Invesco S&P 500 Low Volatility ETF) or USMV (iShares MSCI USA Min Vol Factor ETF) as proxies. For self-built version, build the basket directly.
- **Inputs (self-built version):** Daily returns over trailing 252 trading days for each S&P 500 stock; SPY returns over the same window.

### 4. Entry Rules
**Self-built version (executed monthly at last-trading-day close):**
1. For each S&P 500 stock with full 252-day history, compute trailing 1-year market beta to SPY: `β_i = Cov(R_i, R_SPY) / Var(R_SPY)`.
2. Rank ascending by β. Take the 100 lowest-beta names (matches SPLV construction methodology).
3. Inverse-volatility-weight (closer match to SPLV/USMV) or equal-weight. Hold for one month.

**ETF-proxy version (recommended for Olympus simplicity):**
1. Hold 100% SPLV at all times within the sleeve. Rebalance never — the ETF self-rebalances quarterly.

### 5. Exit Rules
Self-built: pure rebalance, monthly.
ETF version: none unless Olympus account-level kill switch activates.

### 6. Sizing & Risk
- Sleeve allocation: 15–20% of Olympus equity.
- Self-built per-name cap: 1.5% of sleeve.
- No leverage. The BAB-paper leveraging step is intentionally omitted.

### 7. Filters
- Liquidity for self-built: 20-day ADV >= $20M.
- Optional market-regime overlay (cut allocation to 50% if SPY < 200-day SMA), because long-only equity factor strategies still lose money in bear markets even if they outperform.

### 8. Evidence
- **Primary sources:**
  - Frazzini, A. & Pedersen, L. H. (2014). "Betting Against Beta." *Journal of Financial Economics*, 111(1), 1–25.
  - Baker, M., Bradley, B., Wurgler, J. (2011). "Benchmarks as Limits to Arbitrage: Understanding the Low-Volatility Anomaly." *Financial Analysts Journal*, 67(1), 40–54.
  - Clarke, R., de Silva, H., Thorley, S. (2006). "Minimum-Variance Portfolios in the U.S. Equity Market." *Journal of Portfolio Management*.
- **Reported backtest stats:**
  - Frazzini-Pedersen US BAB (long-short, leveraged), 1926–2009: "The U.S. BAB factor realizes a Sharpe ratio of **0.75** between 1926 and 2009... about twice the Sharpe ratio of the value effect over the same period and **40% higher than the Sharpe ratio of momentum**" (verbatim from the paper).
  - The magnitude of low-vol outperformance has been quantified by Walkshausl (2013), *Journal of Banking and Finance*: "The outperformance of low volatility stocks over high volatility stocks is economically exceptionally large, amounting on average to **12% per year**." (Verbatim — note this is Walkshausl's quantification, not Baker, Bradley & Wurgler's direct claim. Baker et al. themselves state only that "the outperformance of low-risk portfolios is perhaps the greatest anomaly in finance.")
  - SPLV (S&P Dow Jones Indices, backtested 1990–2015, live since April 4, 2011): lower volatility than the S&P 500 with comparable or higher returns over multi-decade horizons.
- **Decay / out-of-sample:** Novy-Marx (2014) "The Limits to Arbitrage and the Low-Volatility Anomaly" documents that "the existence and trading efficacy of the low-volatility stock anomaly were more limited than widely believed... performance of long-short portfolios was significantly reduced by high transaction costs." The long-only large-cap implementation (SPLV/USMV) has continued to work as a *risk-reducer* but its return advantage has narrowed in the post-2010 bull market — it most reliably outperforms in drawdowns.
- **Win rate / expectancy:** Not applicable (this is a continuous-exposure factor strategy, not a discrete-trade strategy). Annual rebalancing turnover ~ 30–50%. Sharpe ratio of the long-only top-100 implementation historically ~0.7–0.9 vs. SPY's ~0.5.

---

## Strategy 6 — `quality_qmj_long` (Quality Minus Junk — Long Side Only)

### 1. Name + Thesis
**Quality factor: long high-quality stocks.** Companies that are profitable, growing, safe, and well-managed earn higher risk-adjusted returns than the market; investors do not price quality as much as they should.

### 2. Direction
Long-only top-30%. (The short side of QMJ carries higher borrow risk and crashes during junk rallies; for Olympus, long-only is the right cut.)

### 3. Timeframe & Data
- **Bars:** Daily, rebalanced quarterly (fundamentals only update quarterly).
- **Universe:** Russell 1000 constituents (or S&P 500 if data is restricted).
- **Implementation choice:** **Strongly recommended for Olympus** — hold the iShares MSCI USA Quality Factor ETF **QUAL** as proxy. Reproducing the full Asness-Frazzini-Pedersen quality score (profitability + growth + safety + payout) requires Compustat fundamentals.

### 4. Entry Rules
**ETF-proxy version (recommended):** Hold 100% QUAL within the sleeve.

**Self-built version (if fundamentals are available):**
For each Russell 1000 stock, compute z-scores within the universe for:
- **Profitability:** gross profits/assets; ROE; ROA; CFO/assets; gross margin; low accruals.
- **Growth:** 5-year growth in each profitability metric.
- **Safety:** low beta (252-day), low idiosyncratic volatility (CAPM residual), low leverage (debt/equity), low Ohlson O-score.
- **Payout:** low net equity issuance, dividend payout consistency.

Average the four sub-scores -> overall quality score. Long top 30% equally weighted, rebalanced quarterly.

### 5. Exit Rules
Pure rebalance: quarterly drop-outs sold, new top-30% entrants bought. No stops.

### 6. Sizing & Risk
- Sleeve allocation: 15–20% of Olympus equity.
- Per-name cap (self-built): 0.5% (1/200 with tolerance).
- ETF version: 100% QUAL.

### 7. Filters
- Liquidity >= $20M ADV (always passes for Russell 1000).
- No regime filter — quality stocks tend to *outperform* in drawdowns ("flight to quality"), so a regime overlay is counterproductive.

### 8. Evidence
- **Primary source:** Asness, C. S., Frazzini, A., Pedersen, L. H. (2019). "Quality Minus Junk." *Review of Accounting Studies*, 24(1), 34–112. (Original SSRN working paper 2013.)
- **Reported backtest stats (US sample 1956–2016, global 1986–2016):**
  - "Indeed, a quality-minus-junk (QMJ) factor that goes long high-quality stocks and shorts low-quality stocks earns significant risk-adjusted returns in the United States and across 24 countries." (Verbatim.)
  - QMJ delivers "positive returns in 23 out of 24 countries" with "highly significant risk-adjusted returns" (verbatim from paper).
  - QMJ's information ratio "above 1" in the US over the full sample (Citi summary citing the paper).
  - "Negative market, value, and size exposures, positive alpha, relatively small residual risk, and QMJ returns are high during market downturns" (verbatim) — confirming QMJ's defensive correlation profile.
- **Persistence:** AQR continues to publish QMJ data live (aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Daily). Quality has held up better than most factors post-2010.
- **Live ETF performance:** QUAL since inception (July 2013) has produced an annualized return of approximately +13.4% vs. the S&P 500 total return of approximately +11.3% over the same period (Schwab/Morningstar fund data through Q1 2026) — i.e., about +2.1 percentage points of annual outperformance since launch. Note that over the trailing 10-year window QUAL has *underperformed* SPY by approximately 1 percentage point (~13.25% vs 14.24% per PortfoliosLab). Olympus should expect a defensive factor tilt that helps in drawdowns and produces a modest but real long-run premium — not a return engine in a runaway bull market.
- **Win rate / expectancy:** Not applicable (continuous exposure). Annual turnover for QUAL ~20–30%; moderate tracking error vs. S&P 500.

---

## Strategy 7 — `pead_sue` (Post-Earnings-Announcement Drift)

### 1. Name + Thesis
**Post-earnings-announcement drift.** Stocks with positive earnings surprises continue to drift up for ~60 trading days; stocks with negative surprises drift down. PEAD is the "granddaddy of underreaction events" (Fama 1998) and has been documented continuously since Ball & Brown (1968).

### 2. Direction
Long-only positive-surprise basket. The short-side version is documented but the borrow on small-caps where the effect is strongest is problematic — for Olympus we restrict to the long side.

### 3. Timeframe & Data
- **Bars:** Daily.
- **Universe:** Russell 1000 stocks that report earnings in the current quarter. Olympus needs a reliable earnings calendar and SUE feed; Alpaca does not provide this natively — third-party data (Zacks, Financial Modeling Prep, Estimize) is required.
- **Inputs:**
  - SUE = (Actual EPS - Consensus Estimate EPS) / σ(EPS surprise over trailing 8 quarters).
  - Earnings announcement timestamp.
  - 3-day cumulative abnormal return around announcement (EAR): days -1 to +1 vs. SPY benchmark.

### 4. Entry Rules
1. For each earnings announcement during the most recent business day, compute SUE and EAR(-1,+1).
2. Buy at the close of the **second trading day after** the announcement if BOTH:
   - SUE in the **top 20%** of all surprises in the current quarter to date, AND
   - EAR(-1,+1) > +2% (positive 3-day announcement-window return confirms market also reacted positively, filtering out high-SUE but ambiguous reactions).
3. Equal-weight across qualifying names within the sleeve, capped at per-position size.

### 5. Exit Rules
Sell exactly **60 trading days** after entry, at the close. No stops or take-profits. This is intentional — the academic effect is a dated, persistent drift; tighter exits cut the right tail.

### 6. Sizing & Risk
- Per-name allocation: 2% of sleeve equity, max.
- Sleeve allocation: 10–15% of Olympus equity.
- Position cap: max 30 concurrent positions (limits heavy-earnings-week concentration).

### 7. Filters
- Liquidity: 20-day ADV >= $20M and price >= $10.
- Market cap: only Russell 1000 (PEAD is strongest in micro-caps but trading costs eat the edge there).
- Exclude positions where Olympus already holds the name via another strategy.

### 8. Evidence
- **Primary sources:**
  - Ball, R. & Brown, P. (1968). "An Empirical Evaluation of Accounting Income Numbers." *Journal of Accounting Research*, 6(2), 159–178.
  - Bernard, V. L. & Thomas, J. K. (1989). "Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium?" *Journal of Accounting Research*, 27 (Supplement), 1–36.
  - Brandt, M. W., Kishore, R., Santa-Clara, P., Venkatachalam, M. (2008). "Earnings Announcements Are Full of Surprises." (EAR signal foundation.)
- **Reported backtest stats:**
  - Bernard & Thomas (1989), 1974–1985: Top-SUE-decile minus bottom-SUE-decile spread positive in 41 of 48 quarters. The widely cited Bernard-Thomas result: "a positive (negative) drift of around 2% over 60 trading days for the good (bad) news stocks" (verbatim summary in a peer review of PEAD literature).
  - Brandt, Kishore, Santa-Clara, Venkatachalam (2008): reported hedge-portfolio Sharpe approaching 1.5 using the EAR-based PEAD strategy over 1971–2009 (the cited value 1.52, with t-statistic 3.63, applies to a Jump-based PEAD signal in the published paper).
  - HHS thesis replication: "abnormal return of 12.02% for a holding period of 60 trading days" for the top-SUE quintile, significant at 1%.
- **Decay (honestly stated):**
  - Wikipedia summary of the academic literature: "the persistence of standardized unexpected earnings (SUE) has declined significantly over time... After controlling for declining SUE persistence, the declining trend in PEAD becomes statistically insignificant."
  - Quantpedia variant adding NLP signals to SUE: "5.89% compounding annual return with a Sharpe Ratio of 0.76 and a maximal drawdown of -11.81%" — a realistic modern figure for what a Quantpedia-style PEAD long-only large-cap strategy delivers.
  - "Beyond the Last Surprise" (ScienceDirect, 2024): documents that 12-quarter SUE history models "nearly double Sharpe ratios" of 1-quarter models, indicating modern PEAD still has signal but requires multi-quarter context.
- **Evidence grade:** Established-but-decayed. Long-only large-cap Olympus implementation: expect ~3–6% CAGR with Sharpe 0.4–0.7 and 80–150 trades per year.
- **Win rate / expectancy:** Win rate ~55–60% in modern replications; average winners modestly larger than losers; small but positive expectancy per trade because 60-day holds keep turnover low.

---

## Correlation, Contrast & Why This Set

The seven strategies are deliberately heterogeneous along three axes:

| Axis | Trend / Momentum | Mean Reversion | Factor / Defensive |
|---|---|---|---|
| **Monthly+** | 1 (GEM), 2 (Residual Mom) | — | 5 (BAB), 6 (QMJ), 7 (PEAD) |
| **Daily/Weekly** | — | 3 (RSI2), 4 (IBS) | — |

Expected pairwise correlations of monthly return streams (educated estimates from factor-style literature and replications):

- Strategy 1 (GEM) vs. Strategy 3/4 (mean-reversion): low (~0.1–0.2). Trend rotation between SPY/VEU/AGG is independent of next-day reversion in sector ETFs.
- Strategy 1 vs. Strategy 2 (both momentum): moderate (~0.4–0.6). They share the momentum core but operate at different cross-sections.
- Strategy 3 vs. Strategy 4: high (~0.5–0.7) — both are short-term mean reversion on overlapping ETFs. **This is the only intentional redundancy in the set**, kept because IBS is a *single-bar intraday-shape* signal while RSI(2) is a *2-bar smoothed return* signal. They fire on overlapping but not identical days and provide trade-volume robustness.
- Strategy 5 (BAB) vs. Strategy 6 (QMJ): moderate (~0.3–0.5). Both are defensive factor exposures with documented positive correlation but distinct return drivers (volatility vs. profitability/growth).
- Strategy 7 (PEAD) vs. all others: low (~0–0.2). PEAD is event-driven and stock-specific.
- Strategy 1 (GEM) vs. Strategy 5/6 (defensive factors): low-to-moderate negative when GEM is in AGG (~-0.1 to -0.3 in risk-off regimes); near-zero in risk-on regimes.

The set covers: tactical regime trend (1), cross-sectional momentum (2), short-term mean reversion (3, 4), defensive factor exposure (5, 6), and event-driven drift (7). It avoids putting all eggs in a single anomaly bucket and avoids any strategy that requires shorting illiquid names, options, futures, or sub-15-minute execution.

---

## Recommendations

**Implementation order (paper-trade in this sequence, staged over 3–6 months):**

1. **First (lowest data dependency, highest signal-to-noise):** `dual_momentum_gem` (Strategy 1) and `ibs_etf_meanrev` (Strategy 4). Both need only daily OHLCV that Alpaca provides natively. GEM trades 2–4 times per year; IBS gives you the trade-count to validate execution plumbing.
2. **Second:** `rsi2_pullback_etf` (Strategy 3). Same data, complementary signal. Run alongside IBS to validate the deliberate redundancy and measure live correlation.
3. **Third:** `bab_low_vol` (Strategy 5) and `quality_qmj_long` (Strategy 6) — via the SPLV and QUAL ETF proxies, no fundamental data needed. These provide continuous factor exposure and stabilize the equity curve.
4. **Fourth (require external data):** `residual_momentum_xs` (Strategy 2) — needs Ken French factor data plus S&P 500 constituent history.
5. **Last (highest data and execution complexity):** `pead_sue` (Strategy 7) — needs a paid earnings-surprise feed.

**Sleeve allocation when all seven are live (recommended):**
- 1 (GEM): 15%
- 2 (Residual Mom): 15%
- 3 (RSI2): 10%
- 4 (IBS): 10%
- 5 (BAB / SPLV): 15%
- 6 (QMJ / QUAL): 15%
- 7 (PEAD): 10%
- Reserve / cash buffer: 10%

**Promotion bar to real capital (per strategy):**
- Minimum 50 trades in paper (Strategies 3, 4, 7) or 24 monthly rebalances (Strategies 1, 2, 5, 6).
- Sharpe >= 0.5 net of fees on out-of-sample data the strategy was NOT tuned against.
- Max drawdown <= 1.5x the documented academic max drawdown.
- No single trade contributing > 25% of total PnL (concentration check).
- Correlation with SPY < 0.7 for at least four of the seven strategies (diversification check).

**Thresholds that would change these recommendations:**
- If `dual_momentum_gem` underperforms a 60/40 SPY/AGG benchmark by > 200 bps annualized over 3 years of paper trading -> demote to half allocation; the regime-rotation premium has compressed further.
- If `rsi2_pullback_etf` and `ibs_etf_meanrev` show paper-trade correlation > 0.8 -> kill RSI(2) and retain only IBS; the planned redundancy collapsed.
- If `pead_sue` Sharpe in paper falls below 0.3 -> kill it; the academic effect is too decayed to survive Olympus's frictions.
- If a viable, clean-data source for Compustat fundamentals appears, replace the QUAL and SPLV ETF proxies with self-built top-decile baskets to recapture the ~1 percentage-point of factor-exposure dilution the ETFs impose.

---

## Caveats

1. **Decay is the dominant risk for every strategy listed.** Three of the seven are explicitly graded "established-but-decayed." Pre-2010 backtest numbers should be considered the ceiling, not the expectation.

2. **The overnight return anomaly was deliberately excluded as a standalone strategy.** Initial research (Cooper, Cliff & Gulen 2008; Kelly & Clark 2011; Lou, Polk & Skouras 2019; Boyarchenko, Larsen & Whelan 2023; Bondarenko & Muravyev 2023) all document a strong gross-of-cost overnight effect. Boyarchenko, Larsen & Whelan (NY Fed Staff Report 917 / *Review of Financial Studies* 2023) report on E-mini S&P 500 futures 1998–2019: "the largest positive returns are between 2:00 and 3:00... averaging 3.7% on an annualized basis" with "a trading strategy that goes long the S&P 500 futures between 2:00 and 3:00 earns a Sharpe ratio of 1.1 and accounting for bid-ask spreads this reduces to **-0.5**" (verbatim). Bondarenko & Muravyev (*Journal of Financial and Quantitative Analysis*, 58(3), 2023) report a "1.6 Sharpe ratio that remains high after costs" for a four-hour window — but this is on E-mini futures with much narrower spreads than ETFs. Bartolini, M. (June 16, 2020), "Trading Costs Wipe Out the Overnight Return Anomaly," *Alpha Architect* (republishing State Street Global Advisors / SPDR Americas Research) is decisive for the ETF case: on SPY 1993–January 2020, "cumulative price returns are 717%, 627%, and 12% for the overnight, buy-and-hold, and intraday strategies, respectively," but "for an overnight strategy that does incur trading costs, the cumulative return would be -32%, versus the no-transaction cost strategy of 717%" — and the daily test t-statistic is "1.90 and a p-value of 0.06... below the t-stat threshold of significance of 1.96 and above our 5% level of significance" (verbatim). The anomaly is real but does not survive Alpaca-style retail execution on SPY. Excluded.

3. **Turn-of-the-month effect was reviewed and not included.** Lakonishok & Smidt (1988) and McConnell & Xu (2008) document a strong T-1 to T+3 effect through 2005, but Quantseeker's "Turn-of-the-Month Strategies: Do They Still Work?" (2024) finds: "the effect appears to have disappeared, likely arbitraged away by market participants... QQQ exhibited a very strong TOM effect in the early 2000s, but this effect has gradually diminished to zero over time" (verbatim). Including a decayed-to-zero anomaly violates the "profitable" mandate.

4. **Naive Jegadeesh-Titman 12-1 cross-sectional momentum is intentionally NOT included as a standalone.** It is dominated by residual momentum (Strategy 2) on a risk-adjusted basis (Blitz et al. 2011), and a portion of its signal is captured by the absolute-momentum component of GEM (Strategy 1).

5. **Data dependencies vary.** Strategies 1, 3, 4 need only daily OHLCV (Alpaca-native). Strategy 2 needs Ken French factor data plus a constituent list. Strategies 5 and 6 are best implemented via ETF proxies (SPLV/USMV, QUAL) to avoid Compustat. Strategy 7 requires a third-party earnings/SUE feed.

6. **Capacity is not a concern at Olympus single-user scale.** All seven strategies trade highly liquid US large-caps and ETFs. Academic capacity estimates run from tens of millions to billions of dollars per strategy.

7. **Same-name double-trade risk.** Strategies 3 and 4 in particular have overlapping ETF universes; Strategies 2, 5, 6, and 7 can all hold large-cap S&P 500 names simultaneously. Each strategy must be tagged with its `strategy_id` on every order and reconciled separately in PnL accounting. Olympus account-level position aggregation should warn if any single name exceeds 5% of total Olympus equity across all strategies combined.

---

*Document version 1.0 — June 2026.*
