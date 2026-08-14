# Data provenance and intake record

No market data may be used for a Phase 3 conclusion until this record is filled in and committed with a non-sensitive metadata file. Licensed raw data stays outside Git and is excluded by `.gitignore`.

| Field | Required entry |
|---|---|
| Provider and product | |
| Retrieval date/time | |
| Instrument identifier and exchange/feed | |
| Earliest/latest timestamp | |
| Bar timestamp convention | Bar **open** timestamp, with explicit timezone/offset |
| Session coverage | Must include or allow isolating 09:30–16:00 America/New_York |
| Corporate-action treatment | Raw or adjusted; specify split/dividend convention |
| OHLC construction | Trade, midpoint, or vendor bar definition |
| Volume definition | |
| Known gaps / early closes / halts | |
| License / redistribution restriction | |
| SHA-256 of local source file | |

## Required intake checks

1. Preserve the source file unchanged under `data/raw/` locally; it is not committed.
2. Run `tools/tsla_breakout_v1.py` once. It writes `audit.json` even when it rejects the file.
3. Resolve every invalid OHLC, duplicate timestamp, missing regular-session bar, and unexplained discontinuity before strategy replay.
4. Commit this completed record and the non-sensitive audit metadata before viewing validation metrics.

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
