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
