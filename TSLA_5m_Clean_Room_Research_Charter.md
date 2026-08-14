# TSLA 5-minute clean-room research charter — v1.0

**Status:** approved for implementation only after this document is frozen.  
**Purpose:** test a narrow continuation hypothesis inspired by a public Reddit post. This is not a reproduction of the post author's unpublished strategy and is not a trading recommendation.

## 1. Research question

Does a break of the preceding four completed 5-minute TSLA bars during regular US trading hours exhibit positive continuation over the next 30 minutes, *after conservative Pine-compatible execution costs*?

This first experiment tests a **signal**, not a finished trading system. It intentionally has no ADX, ATR, RSI, trailing stop, take-profit, scaling, or discretionary “no progress” rule. Adding those now would make it too easy to optimize the answer we want.

## 2. Frozen v1 signal specification

| Item | Frozen rule |
|---|---|
| Instrument | TSLA common stock, standard candles only |
| Chart resolution | 5 minutes |
| Session | 09:30–16:00 America/New_York; no extended-hours data |
| Range | `rangeHigh` = highest high of bars `[1]` through `[4]`; `rangeLow` = lowest low of bars `[1]` through `[4]`. The signal bar is never part of its own range. |
| Long signal | Confirmed bar closes above `rangeHigh` **and** prior confirmed close is at or below `rangeHigh`. |
| Short signal | Confirmed bar closes below `rangeLow` **and** prior confirmed close is at or above `rangeLow`. |
| Signal window | A signal may occur only on bars closing from 09:50 through 15:25, so all simulated execution stays in regular hours. |
| Entry | One market order created at the signal-bar close; Pine must fill it no earlier than the next bar’s open. |
| Holding period | Six complete 5-minute bars after entry (30 minutes). A market exit is created at the close of the sixth bar and fills at the next bar open. |
| Positioning | One position maximum; no pyramiding, reversal, averaging, leverage, or overnight carry. New signals while a position is open are ignored. |
| Quantity | One share. Results are evaluated per-share and per-trade, with no compounding. Position sizing is a later, separate experiment. |

## 3. Pine Script execution contract

The eventual Pine implementation must conform to all of the following:

- Use `strategy()`, not an indicator; use standard OHLC candles, never Heikin-Ashi, Renko, Kagi, or another synthetic chart.
- Set `process_orders_on_close = false`, `calc_on_every_tick = false`, and `calc_on_order_fills = false`.
- Gate signals with `barstate.isconfirmed`; any alert must be **Once Per Bar Close**.
- Do not use `request.security()` in v1. Later higher-timeframe work is allowed only in a separately versioned charter, using confirmed values (for example, prior-bar expression plus `barmerge.lookahead_on`), never a future-leaking request.
- Use session logic with the `America/New_York` timezone. Do not rely on the chart’s displayed timezone.
- Store the range and the intended exit bar at entry. Do not recalculate historical state from future bars.
- Run the same code with Bar Magnifier off and on. The report must state which historical bars lack lower-timeframe coverage; the initial conclusion cannot rely solely on Bar Magnifier fills.

TradingView’s broker emulator normally infers intrabar paths from OHLC data, and strategies normally submit on a closed bar for execution on a later tick/bar. Bar Magnifier improves intrabar handling but does not replace trade-and-quote execution data. See the sources in Section 9.

## 4. Costs and fill assumptions

The research output must report both cases below. A result that works only before cost stress fails v1.

| Case | Commission | Slippage | Fill rule |
|---|---:|---:|---|
| Base | 0.01% per side | 5 ticks per market order | Next bar open, adjusted by Pine’s market-order slippage model |
| Stress | 0.02% per side | 10 ticks per market order | Same rule |

For TSLA’s $0.01 minimum tick, these are deliberately conservative placeholders. Before live or paper deployment, they must be replaced by the actual broker schedule and a bid/ask-derived model using timestamped trade-and-quote data.

## 5. Data and split plan

All input data must be preserved unchanged with its source, retrieval date, timezone, adjustment convention, and session setting recorded.

| Segment | Dates | Allowed use |
|---|---|---|
| Development | 2019-01-01 to 2022-12-30 | Implement the frozen baseline and debug data/code only. Do not change v1 rules for performance. |
| Validation | 2023-01-03 to 2024-12-31 | Run once after the implementation is committed. No parameter changes after viewing it. |
| Contaminated historical check | 2025-01-01 to 2026-06-22 | Report separately only. The public Reddit discussion makes this unsuitable as an independent holdout. |
| Forward holdout | 2026-06-23 onward | No design changes. It remains an accumulating forward sample until at least 100 eligible signals have occurred. |

The implementation must reject or flag missing bars, early closes, halts, and any event whose six-bar holding period cannot complete inside the selected session. Prices must use one documented adjustment convention throughout; intraday execution studies should ultimately use raw trade/quote prices with corporate-action handling explicitly documented.

## 6. Pre-registered outcomes and pass/fail gates

### Primary outcome

Net per-trade return, separately for long and short trades, after base and stress costs.

### Required report

- trade count, win rate, mean and median net return, profit factor, expectancy, maximum drawdown, and the complete trade list;
- results by calendar year, long/short direction, month, and hour of entry;
- base versus stress-cost result;
- Bar Magnifier off versus on result;
- distribution of maximum adverse/favourable excursion over the fixed 30-minute hold;
- every code/data correction and every strategy variant attempted in a trial log.

### v1 may advance only if all are true

1. Development, validation, and forward-holdout results have positive median net return after **stress** costs.
2. Neither direction’s result is dominated by one calendar year or a handful of trades.
3. Bar Magnifier changes neither the sign nor the basic conclusion.
4. An independent implementation (Python or another event-driven engine) reproduces Pine’s trade timestamps, direction, and approximate P&L before the data is unblinded further.
5. No rule, parameter, session, cost, or sample boundary was changed after validation or forward-holdout results were observed.

Failure is useful information: we archive the result and do not add filters to rescue it. A new idea requires a new charter and a new trial-log entry.

## 7. Explicitly prohibited in v1

- optimizing range length, hold length, session, stop, target, ADX, ATR, RSI, or any threshold;
- selecting the best long-only/short-only subset after results are known;
- using a same-bar close fill, intrabar alert, or hindsight-confirmed pivot;
- viewing a result and then moving the date split, deleting trades, or changing data vendor/session settings;
- using the public author’s reported performance as an acceptance target.

## 8. What happens after v1

Only if v1 clears its gates, v2 may test one separately justified extension at a time—first a range-size/volatility regime filter, then (if warranted) an exit/risk model. Each extension gets its own written hypothesis, small pre-declared parameter set, full trial-log count, validation, and forward holdout. Monte Carlo is reserved for drawdown/path-risk analysis; it does not establish that a signal has alpha.

## 9. Reference constraints

- [TradingView strategy and broker-emulator documentation](https://www.tradingview.com/pine-script-docs/v5/concepts/strategies/)
- [TradingView broker-emulator settings](https://www.tradingview.com/support/solutions/43000786181-broker-emulator/)
- [TradingView repainting and confirmed higher-timeframe requests](https://www.tradingview.com/pine-script-docs/v5/concepts/repainting/)
- [Bailey et al., Statistical Overfitting and Backtest Performance](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf)
