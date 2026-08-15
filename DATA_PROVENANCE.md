# Data provenance and intake record

No market data may be used for a Phase 3 conclusion until this record is filled in and committed with a non-sensitive metadata file. Licensed raw data stays outside Git and is excluded by `.gitignore`.

| Field | Required entry |
|---|---|
| Provider and product | Alpaca Basic historical US equities, SIP feed |
| Retrieval date/time | 2026-08-14 21:31 America/New_York; eight annual requests, merged locally |
| Instrument identifier and exchange/feed | TSLA; consolidated US-equities SIP bars |
| Earliest/latest timestamp | 2019-01-02T09:30:00-05:00 / 2026-08-13T15:55:00-04:00 |
| Bar timestamp convention | Bar **open** timestamp, with explicit timezone/offset |
| Session coverage | Provider-native 5-minute bars, filtered to Nasdaq regular session: 09:30–16:00 ET, with pre-registered 13:00 ET early closes |
| Corporate-action treatment | `adjustment=raw`; expected TSLA split discontinuities remain in the raw series |
| OHLC construction | Alpaca historical SIP five-minute OHLCV bars; provider bar-construction methodology is not independently reconstructed |
| Volume definition | Provider-reported five-minute bar volume |
| Known gaps / early closes / halts | No unexplained RTH gaps. Four verified market-wide circuit-breaker interruptions (2020-03-09, 03-12, 03-16, 03-18) remain unfilled and are excluded when a trade would span a gap. Nasdaq early-close calendar applied. |
| License / redistribution restriction | Raw provider response remains local under `data/raw/`, ignored by Git; no credentials or raw data are committed. |
| SHA-256 of local source file | `D46261838B08A0F640B9E5199D1894892615EA668414CF67250FD88C5D34D584` (`data/raw/tsla_5m.csv`, 148,744 bars) |

## Required intake checks

1. Preserve the source file unchanged under `data/raw/` locally; it is not committed.
2. Run `tools/tsla_breakout_v1.py` once. It writes `audit.json` even when it rejects the file.
3. Resolve every invalid OHLC, duplicate timestamp, missing regular-session bar, and unexplained discontinuity before strategy replay.
4. Commit this completed record and the non-sensitive audit metadata before viewing validation metrics.

## Intake result

The completed independent audit reported zero invalid OHLC records, duplicate timestamps, or unexplained incomplete regular-session days. It retained the four verified interruption days above, plus the expected raw-price discontinuities around TSLA's 2020 and 2022 stock splits. Those facts are source characteristics, not strategy changes.

## Fixed Phase 3 segments

These segments are not parameter-selection opportunities:

| Segment | Dates | Status |
|---|---|---|
| Validation-2023 | 2023-01-03 to 2023-12-29 | Fixed, do not retune after viewing |
| Validation-2024 | 2024-01-02 to 2024-12-31 | Fixed, do not retune after viewing |
| Contaminated-history | 2025-01-01 to 2026-06-22 | Report separately; public Reddit results prevent independent interpretation |
| Forward holdout | 2026-06-23 onward | Accumulate without design changes until 100 eligible signals |

Example after data intake:

```powershell
python tools/phase3_validate.py --input data/raw/tsla_5m.csv --output-dir results/phase3 `
  --segment Validation-2023:2023-01-03:2023-12-29 `
  --segment Validation-2024:2024-01-02:2024-12-31 `
  --segment Contaminated-history:2025-01-01:2026-06-22 `
  --segment Forward-holdout:2026-06-23:2026-12-31
```
