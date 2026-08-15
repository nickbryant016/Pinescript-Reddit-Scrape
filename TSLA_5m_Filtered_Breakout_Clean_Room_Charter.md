# TSLA 5-minute filtered-breakout clean-room charter — v1.0

**Purpose:** test a fully specified, Pine-compatible filter stack inspired by the public [TSLA walk-forward post](https://www.reddit.com/r/pinescript/comments/1ucgi3o/tsla_5min_intraday_breakout_walkforward_results/). The author did not disclose exact thresholds or source code. This is therefore a pre-registered clean-room proxy, not a replication or verification of the author's claimed live strategy.

## Frozen rules

| Component | Rule |
|---|---|
| Market | TSLA common stock, regular-session standard 5-minute bars |
| Breakout | Close beyond the high/low of the four prior completed bars, with prior close still inside that boundary |
| Trend filter | 14/14 Wilder ADX at least 20 |
| Range filter | Prior four-bar high-low range at least 0.50 × 14-bar Wilder ATR |
| Candle-strength filter | Signal real body at least 0.50 × ATR and close in the upper/lower 25% of its own range for long/short |
| Higher-timeframe filter | Last *completed* 60-minute RSI(14), mapped without lookahead: 45–70 for long, 30–55 for short |
| Entry | Next bar open; one position maximum; no pyramiding or reversal |
| Base target | Close-confirmed 2.75% favorable move from filled entry, then market exit at next open |
| Trailing exit | Close through EMA(20); use EMA(8) for bars opening 15:00–15:55 ET, then market exit at next open |
| No-follow-through exit | Close back inside the original four-bar breakout range, then market exit at next open |
| No-progress exit | After 30 minutes, close at or beyond entry in the adverse direction, then market exit at next open |
| Time exit | 60-minute holding limit or 15:50 close, then market exit at next open |
| Signal window | Signal bars opening 09:50–14:45 ET. Signals requiring a missing bar or an exit path across a session interruption are rejected. |
| Cost cases | Base: 0.01%/side + 5 ticks/order. Stress: 0.02%/side + 10 ticks/order. |

Close-confirmed exits deliberately avoid assuming intrabar fill order. This is less favorable than treating target/stop levels as guaranteed intrabar fills and is the contract implemented by both the Pine reference and independent replay.

## Validation and Monte Carlo gate

The local audited TSLA data is unchanged. Results are reported separately for 2019–2022 development, 2023 validation, 2024 validation, contaminated history, and the current forward slice. No parameter is selected from any segment.

For each fixed segment and cost case, a deterministic 20,000-replicate circular block bootstrap (mean block: 10 chronological trades, seed: `20260815`) reports terminal-P&L and drawdown uncertainty. It preserves short local dependence approximately; it is a risk diagnostic, **not** a statistical proof of edge and does not replace OOS validation.

Reject the candidate if either 2023 or 2024 has mean net P&L at or below zero or profit factor at or below 1.0 in either cost case. A candidate passing those gates would still need Pine trade-list parity, multi-market evidence, bid/ask execution study, and forward observation before paper or live trading.
