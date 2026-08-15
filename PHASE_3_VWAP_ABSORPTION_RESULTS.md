# Phase 3 result — frozen TSLA VWAP absorption baseline

## Decision

**Reject this clean-room implementation.** The setup fails the pre-registered decision rule: Validation 2024 has negative mean P&L and profit factor below 1.0 in both cost cases. The stress case also fails development and Validation 2023. The low number of independent validation trades is an additional reason not to rescue it by tuning.

This does not validate or invalidate the original author's undisclosed ES/YM implementation. The public post did not provide a complete rule set or reproducible full-history export, so this project tested only the explicitly frozen TSLA interpretation in `TSLA_5m_VWAP_Absorption_Clean_Room_Charter.md`.

## Fixed replay results

All figures are one-share P&L after the committed bar-level cost assumptions. No threshold, exit rule, instrument, or date split was changed after observing these results.

| Cost case | Segment | Trades | Mean net P&L | Profit factor | Net P&L | Max drawdown |
|---|---|---:|---:|---:|---:|---:|
| Base | Development | 48 | 0.1636 | 1.1562 | 7.85 | -17.36 |
| Base | Validation 2023 | 6 | 0.1094 | 1.3770 | 0.66 | -1.61 |
| Base | Validation 2024 | 4 | -0.0901 | 0.7999 | -0.36 | -0.98 |
| Base | Contaminated history | 12 | -0.4763 | 0.4578 | -5.72 | -8.01 |
| Base | Forward slice | 7 | -0.6956 | 0.4333 | -4.87 | -5.77 |
| Stress | Development | 48 | -0.0389 | 0.9664 | -1.87 | -18.93 |
| Stress | Validation 2023 | 6 | -0.0380 | 0.8955 | -0.23 | -1.91 |
| Stress | Validation 2024 | 4 | -0.2340 | 0.5529 | -0.94 | -1.42 |
| Stress | Contaminated history | 12 | -0.6552 | 0.3314 | -7.86 | -8.86 |
| Stress | Forward slice | 7 | -0.8698 | 0.3564 | -6.09 | -6.82 |

The completed intake audit was reused unchanged: 148,744 provider-native SIP five-minute bars, zero unexplained regular-session gaps, and four documented 2020 market-wide halt interruptions left unfilled. Machine-readable local outputs remain ignored under `results/phase3_vwap_absorption_v1/`.

## Next action

Do not optimize this candidate. The next strategy should be chosen from a post with fully disclosed, executable rules and enough trade frequency to make independent validation meaningful.
