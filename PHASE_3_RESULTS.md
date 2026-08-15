# Phase 3 result — frozen TSLA five-minute baseline

## Decision

**Stop this baseline.** The clean-room breakout rule does not show evidence of alpha under the pre-registered bar-level cost assumptions. It was negative in the development window, both untouched validation years, the contaminated period, and the currently available forward slice. No tuning or filter search follows this result.

This is a rejection of this exact frozen specification, not a conclusion about TSLA trading generally or a reproduction of the Reddit post.

## Fixed replay results

All figures are one-share P&L, after the pre-registered bar-level cost model. Profit factor below 1.00 and negative mean P&L both fail the specified performance test.

| Cost case | Segment | Trades | Mean net P&L | Profit factor | Net P&L | Max drawdown |
|---|---|---:|---:|---:|---:|---:|
| Base | Development (2019–2022) | 7,090 | -0.3050 | 0.8398 | -2,162.24 | -2,166.89 |
| Base | Validation 2023 | 1,750 | -0.1034 | 0.8075 | -180.92 | -187.97 |
| Base | Validation 2024 | 1,771 | -0.1663 | 0.7392 | -294.44 | -303.23 |
| Base | Contaminated history | 2,580 | -0.1754 | 0.8149 | -452.66 | -480.02 |
| Base | Forward slice | 253 | -0.0746 | 0.8978 | -18.87 | -35.06 |
| Stress | Development (2019–2022) | 7,090 | -0.5288 | 0.7397 | -3,749.07 | -3,749.71 |
| Stress | Validation 2023 | 1,750 | -0.2469 | 0.6013 | -432.03 | -433.64 |
| Stress | Validation 2024 | 1,771 | -0.3123 | 0.5688 | -553.04 | -553.56 |
| Stress | Contaminated history | 2,580 | -0.3498 | 0.6661 | -902.40 | -923.64 |
| Stress | Forward slice | 253 | -0.2471 | 0.6999 | -62.53 | -67.22 |

The forward slice has only 253 trades and is supplementary; it does not rescue the earlier independent failures.

## Data controls applied

- Local input: 148,744 provider-native Alpaca SIP five-minute bars from 2019-01-02 through 2026-08-13; SHA-256 and full intake record are in `DATA_PROVENANCE.md`.
- Audit: zero invalid OHLC rows, duplicate timestamps, or unexplained incomplete regular-session days.
- Four verified 2020 market-wide circuit-breaker interruptions were left unfilled. The replay does not enter a trade across a non-contiguous sequence.
- Nasdaq early-close calendar excluded after-hours bars that the provider returned after 13:00 ET.
- TSLA raw-price split discontinuities were retained as expected data characteristics.

The machine-readable report and trade files are reproducible locally under the ignored `results/phase3_v1/` directory; only this non-sensitive summary is versioned.
