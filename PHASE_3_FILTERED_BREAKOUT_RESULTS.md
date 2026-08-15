# Phase 3 result — frozen TSLA filtered-breakout proxy

## Decision

**Reject.** This clean-room proxy fails both untouched validation years in both cost cases. The deterministic block-bootstrap diagnostic reinforces the rejection: its 2024 base and stress resamples produced a positive terminal P&L in 0% of 20,000 draws.

The public post claims a different, undisclosed implementation and roughly 150 trades/year. This proxy generated roughly 490 validation trades/year, so it must not be presented as a reproduction or a contradiction of the author's exact system. It is evidence only that the fully documented proxy below lacks alpha on the audited TSLA dataset.

## Fixed OOS results

All figures are one-share P&L after the committed bar-level market-order costs.

| Cost case | Segment | Trades | Mean net P&L | Profit factor | Net P&L | Max drawdown |
|---|---|---:|---:|---:|---:|---:|
| Base | Development | 1,946 | -0.2354 | 0.8545 | -458.07 | -537.74 |
| Base | Validation 2023 | 488 | -0.0346 | 0.9244 | -16.87 | -33.32 |
| Base | Validation 2024 | 489 | -0.2484 | 0.5804 | -121.45 | -125.31 |
| Base | Contaminated history | 774 | -0.1255 | 0.8523 | -97.17 | -106.75 |
| Base | Forward slice | 80 | -0.0198 | 0.9693 | -1.59 | -23.37 |
| Stress | Development | 1,949 | -0.4631 | 0.7400 | -902.62 | -916.89 |
| Stress | Validation 2023 | 489 | -0.1826 | 0.6748 | -89.28 | -101.14 |
| Stress | Validation 2024 | 490 | -0.3957 | 0.4412 | -193.87 | -197.34 |
| Stress | Contaminated history | 775 | -0.3075 | 0.6855 | -238.31 | -244.98 |
| Stress | Forward slice | 80 | -0.1936 | 0.7478 | -15.49 | -33.39 |

The short positive forward slice is not a validation success: it is small, was observed after the public post, and does not overturn failures in the two fixed OOS years.

## Monte Carlo diagnostic

The report uses a fixed circular block bootstrap of chronological P&Ls: 20,000 replicates, mean 10-trade block, seed `20260815`. It estimates uncertainty in realized trade ordering and drawdown; it does not establish statistical significance or replace OOS testing.

| Cost case | Segment | Probability terminal P&L > 0 | 5th percentile terminal P&L | 5th percentile max drawdown |
|---|---|---:|---:|---:|
| Base | Development | 1.68% | -810.09 | -862.18 |
| Base | Validation 2023 | 26.10% | -59.46 | -70.32 |
| Base | Validation 2024 | 0.00% | -166.49 | -170.55 |
| Base | Forward slice | 43.90% | -26.06 | -30.82 |
| Stress | Development | 0.00% | -1,260.76 | -1,294.66 |
| Stress | Validation 2023 | 0.08% | -130.75 | -135.61 |
| Stress | Validation 2024 | 0.00% | -238.92 | -241.18 |
| Stress | Forward slice | 17.32% | -39.91 | -43.19 |

The provider audit is unchanged: 148,744 native five-minute SIP bars, zero unexplained regular-session gaps, and four documented 2020 market-wide halts retained without interpolation. Ignored machine-readable trade and Monte Carlo reports are under `results/phase3_filtered_breakout_v1/`.

The Pine reference is versioned but has not yet been compiled in TradingView and matched trade-for-trade against the local replay. That parity check remains mandatory before any strategy can advance; it is not necessary to justify rejecting this strongly negative proxy.
