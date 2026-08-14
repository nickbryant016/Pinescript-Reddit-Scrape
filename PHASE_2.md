# Phase 2 — data audit and dual implementation

Phase 2 implements the frozen signal specification from `TSLA_5m_Clean_Room_Research_Charter.md`; it does not test a modified version of it.

## Artifacts

- `tsla_5m_clean_room_v1.pine` is the TradingView/Pine reference implementation.
- `tools/tsla_breakout_v1.py` is an independent standard-library replay and data audit.

The Pine script is deliberately configured for standard 5-minute bars, one-share fixed quantity, next-bar order processing, 0.01% commission per side, and five ticks of slippage. To run the stress scenario, make an exact copy with 0.02% commission and ten ticks of slippage; do not alter any signal or holding-period rule.

## Required CSV contract

The independent replay accepts UTF-8 CSV with these exact columns:

```text
timestamp,open,high,low,close,volume
2024-01-02T14:30:00+00:00,248.42,249.10,248.31,248.89,123456
```

`timestamp` is the opening time of a 5-minute bar and must include a UTC offset (or end in `Z`). The export may contain extended-hours rows, but the audit reports counts and the replay only uses standard RTH rows. Do not use a CSV that silently changes timezone, price-adjustment convention, or bar timestamp convention.

## Run sequence

1. Obtain a documented full-history TSLA 5-minute export. Record provider, pull date, exchange/session coverage, timestamp convention, and corporate-action adjustment convention in the trial log.
2. Run the audit and baseline replay:

   ```powershell
   python tools/tsla_breakout_v1.py --input data/raw/tsla_5m.csv --output-dir results/base
   ```

3. Do not proceed if the audit reports invalid OHLC, duplicate/non-monotonic timestamps, missing RTH bars, or unexplained discontinuities.
4. Run the unchanged code under the stress-cost command:

   ```powershell
   python tools/tsla_breakout_v1.py --input data/raw/tsla_5m.csv --output-dir results/stress --commission-rate 0.0002 --slippage-ticks 10
   ```

5. Compare the Pine Strategy Tester’s trade list against `results/base/trades.csv`. Investigate every mismatch before looking at performance metrics.

## Data boundary

No historical market data is committed to this repository. We need a provider/export that supports the entire chartered date range before a valid result exists. Free 5-minute web downloads with short retention windows are not a substitute.
