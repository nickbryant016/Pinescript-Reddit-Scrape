# TSLA 5-minute VWAP absorption clean-room charter — v1.0

**Purpose:** test one fully specified, Pine-compatible mean-reversion hypothesis inspired by the public [VWAP absorption reversal discussion](https://www.reddit.com/r/pinescript/comments/1u1tr0p/i_built_a_vwap_absorption_reversal_strategy_and_a/). This is not a reproduction of the author's unpublished code or a trading recommendation.

## Frozen hypothesis

On standard five-minute TSLA regular-session bars, does an unusually high-volume, unusually small-range bar on one side of session VWAP revert toward VWAP after conservative market-order costs?

The public post describes the concept but does not disclose its thresholds or complete exit code. The following values are therefore a single pre-registered clean-room implementation, selected before viewing its result. They must not be tuned after this run.

| Element | Frozen rule |
|---|---|
| Instrument and resolution | TSLA common stock, standard 5-minute candles, regular US session only |
| Session VWAP | Cumulative typical-price (`hlc3`) volume-weighted average from the 09:30 ET open, reset each session |
| Volume condition | Current volume is at least the 80th-nearest-rank percentile of the 20 completed prior RTH bars |
| Compression condition | Current true range is no more than 0.50 × 14-bar Wilder ATR |
| Direction | Close above VWAP: short candidate. Close below VWAP: long candidate. A close exactly at VWAP is ignored. |
| Signal window | Signal-bar opens from 11:10 through 14:45 ET; signal evaluated only at bar close |
| Entry | One market order at the next five-minute bar open; one position maximum; no pyramiding or reversal |
| Exit | Submit a market exit after a close reaches/passes the signal-session VWAP, after a close crosses a fixed one-ATR adverse threshold measured from filled entry, after 60 minutes, or at the 15:50 close; the order fills at the next bar open |
| Data gap rule | Reject a signal unless its 20-bar lookback and possible 60-minute exit path are contiguous within one RTH session. No bar is filled or synthesized. |
| Base costs | 0.01% per side plus five $0.01 ticks per market order |
| Stress costs | 0.02% per side plus ten $0.01 ticks per market order |

## Pine constraints

- `strategy()` only; no `request.security()`, no lower-timeframe assumptions, no lookahead, and no synthetic charts.
- Use `process_orders_on_close = false`, `calc_on_every_tick = false`, `calc_on_order_fills = false`, and Bar Magnifier off for the initial parity test.
- The TradingView chart must use TSLA and the regular session. The corresponding Python replay audits the local provider-native bars before computing results.
- Exit decisions are close-confirmed rather than intrabar stop/limit fills. This intentionally avoids a bar-path assumption and is less favorable to a mean-reversion claim.

## Evaluation plan

The data file and calendar controls are the committed Phase 3 TSLA dataset. No new data, threshold, instrument, or date split is selected after results are observed.

| Segment | Dates | Role |
|---|---|---|
| Development | 2019-01-01 to 2022-12-30 | Baseline robustness check only; no retuning allowed |
| Validation 2023 | 2023-01-03 to 2023-12-29 | Untouched validation |
| Validation 2024 | 2024-01-02 to 2024-12-31 | Untouched validation |
| Contaminated history | 2025-01-02 to 2026-06-22 | Report only |
| Forward slice | 2026-06-23 to 2026-08-13 | Report only; too short for a deployment decision |

## Decision rule

The candidate is rejected if either untouched validation year has non-positive mean net P&L or a profit factor at or below 1.0 in either cost case. A passing bar-level test would still require Pine parity and bid/ask execution validation before paper or live trading.
