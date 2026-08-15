# Mistakes log

This is a permanent process log for the TSLA research project. Entries record the mistake, its impact, and the control added to prevent a repeat. They are not retroactively edited; later corrections are appended.

## 2026-08-14 — Research scope was initially too narrow

- **Mistake:** I began with topic/indexed searches and inspected a volatility-squeeze indicator before enumerating every strategy posted in the requested four-month r/pinescript window.
- **Impact:** The initial shortlist was not supported by the requested exhaustive universe and should not have been presented as such.
- **Correction:** Built a chronological inventory first (360 posts), then screened the strategy-bearing threads before producing any shortlist.
- **Permanent control:** For any request to find the best examples in a time-bounded community, complete and preserve the full chronological inventory before ranking, sampling, or researching adjacent topics.

## 2026-08-14 — Recommendation due diligence initially omitted comment threads

- **Mistake:** The first shortlist was based mainly on original posts before every shortlisted thread’s comments had been reviewed.
- **Impact:** The comment audit materially weakened the overnight, SOL, and VWAP candidates; claims of robustness and reproducibility were less substantiated than the posts alone suggested.
- **Correction:** Reviewed and expanded the available comments for each shortlisted post before creating the clean-room TSLA research plan.
- **Permanent control:** A strategy cannot be recommended from a community post until the original post, visible replies, reproducibility discussion, reported costs, and live/forward-test evidence have all been reviewed.

## Commit policy

- Commit each material research artifact and every later code/data change with a descriptive message.
- Record any process, data, execution-model, or validation error in this file before changing the affected conclusion or implementation.
- Never rewrite history to conceal an error; append a correction and commit it.

## 2026-08-14 — First eligible signal time was off by one bar in the Phase 2 draft

- **Mistake:** The charter and initial Pine session window allowed a 09:50 bar-close signal, although four completed 5-minute regular-session bars do not exist until the 09:55 close.
- **Impact:** The implementation would have safely produced no early signal because the range was undefined, but the written specification and independent replay boundary were inconsistent.
- **Correction:** Changed the frozen first eligible signal to the 09:55 close (the bar opening at 09:50) in the charter, Pine script, and independent replay.
- **Permanent control:** For every time-based strategy rule, document whether timestamps represent bar open or bar close and verify the first and last executable event with a concrete session timeline.

## 2026-08-14 — Initial synthetic replay assertion ignored same-bar re-entry eligibility

- **Mistake:** The first deterministic replay test expected exactly one trade, but the frozen rules permit a new signal at the close of the bar where the prior 30-minute trade exits at the open.
- **Impact:** The test failed even though the replay followed the specified execution sequence. The same test also revealed that an audit failure would exit before preserving its diagnostic report.
- **Correction:** Updated the test expectation to verify the first known trade and changed the replay so it always writes `audit.json` before failing validation.
- **Permanent control:** Synthetic tests must model the complete state transition of order fill, bar close, and eligibility for the next signal; audit artifacts must be preserved on both pass and fail paths.

## 2026-08-14 — Data-plan coverage was assumed rather than verified in the provider portal

- **Mistake:** The documented intake example used Databento `EQUS.MINI` for the full 2019–present study before confirming that dataset's actual coverage.
- **Impact:** `EQUS.MINI` begins on 2023-03-28, which cannot support the frozen 2019–2022 development window. Proceeding would have silently broken the validation design.
- **Correction:** Verified coverage in the authenticated portal before any purchase. The plan now specifies `XNAS.ITCH` primary-listing one-minute OHLCV, available from 2018-05-01, and explicitly records its non-consolidated scope.
- **Permanent control:** Verify a vendor's symbol-level history, schema, venue scope, date bounds, and exact estimate in the authenticated catalog before recording a dataset in a research charter or sending a data request.

## 2026-08-14 — Free long-history sources were not screened before recommending paid data

- **Mistake:** I recommended a paid Databento request before checking whether a documented free provider could supply the frozen study's required historical bars.
- **Impact:** This created unnecessary account setup and delayed the research workflow.
- **Correction:** Verified Alpaca Basic's documented historical coverage since 2016 and its free historical SIP access for completed periods, then replaced the data-intake plan with an Alpaca adapter.
- **Permanent control:** Before recommending a paid dataset for a backtest, screen and document viable free sources against the exact symbol, bar interval, date range, feed scope, and retention requirement.

## 2026-08-14 — Alpaca one-minute bars failed the project's aggregation-completeness control

- **Mistake:** The initial Alpaca adapter assumed that every regular-session five-minute interval could be reconstructed from five vendor one-minute bars.
- **Impact:** The 2019-01-17 11:20 ET interval contained only four returned one-minute bars, so the strict normalizer correctly refused to create a research file.
- **Correction:** Verified that Alpaca's native SIP five-minute endpoint returns the affected interval. The initial run uses native five-minute bars, with no interpolation or gap filling, and the change is recorded before results are viewed.
- **Permanent control:** A provider's bar availability must be tested at every requested granularity. Do not infer five-minute completeness from a one-minute feed or substitute fabricated bars when a source timestamp is absent.

## 2026-08-14 — Regular-session filter initially treated early-close after-hours bars as RTH

- **Mistake:** The first native five-minute pull used a universal 16:00 ET session close. On Nasdaq early-close days, Alpaca returned later extended-hours bars that the filter incorrectly treated as regular-session data.
- **Impact:** A normal early-close transition appeared as an apparent data gap, so the provider could have been rejected for the wrong reason.
- **Correction:** Added the Nasdaq early-close calendar for the frozen study period to both the downloader and independent audit. Each affected day now ends at the 12:55 ET bar; the source remains subject to the same no-gap audit inside that session.
- **Permanent control:** Session filters must use the venue holiday and early-close calendar, not only weekday and clock-time rules.

## 2026-08-15 — Pine VWAP study initially used a clock-only RTH gate

- **Mistake:** The first Pine draft for the VWAP absorption study used `0930-1600` as its only regular-session gate.
- **Impact:** On a chart with extended-hours bars, that clock window can include bars after a Nasdaq early close, diverging from the independently audited data contract.
- **Correction:** Changed the Pine gate to `session.ismarket`, which uses the instrument exchange's actual regular-session state; the Python replay already applies the pre-registered early-close calendar.
- **Permanent control:** Pine implementations of an audited session rule must use exchange-session state where available, not a universal clock window alone.

## 2026-08-15 — Initial validation framework omitted Monte Carlo path-risk diagnostics

- **Mistake:** The first two candidate reports used fixed out-of-sample segments and cost stress but did not include a pre-registered resampling diagnostic.
- **Impact:** The rejection decisions remain supported by negative OOS performance, but reports did not quantify uncertainty in terminal P&L and drawdown due to trade ordering.
- **Correction:** Added a deterministic 20,000-replicate circular block bootstrap to the framework and required it for the next complete candidate run.
- **Permanent control:** Every candidate that clears a fixed OOS gate must include a documented, seeded path-risk diagnostic; it is supplementary and cannot be used to select parameters or overturn a failed OOS result.

## 2026-08-15 — Filtered-breakout replay initially reset completed higher-timeframe RSI at each session

- **Mistake:** The independent replay mapped confirmed 60-minute RSI values only within the same trading day.
- **Impact:** Pine's non-repainting `request.security(..., rsi[1], lookahead_on)` carries the last completed higher-timeframe value across the overnight boundary, so early-session signals could diverge from the Pine reference.
- **Correction:** Changed the replay to forward-fill the last confirmed hourly RSI across session boundaries and reran the same frozen rule set, splits, costs, and Monte Carlo seed.
- **Permanent control:** Every higher-timeframe Pine expression needs an explicit lower-timeframe availability map, including the session-boundary behavior of confirmed values.
