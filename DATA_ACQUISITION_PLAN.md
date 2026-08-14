# Data acquisition decision — TSLA clean-room study

## Decision

Use a documented historical **one-minute OHLCV** source for the initial Phase 3 signal study, then use top-of-book trades/quotes only after the signal survives fixed out-of-sample and cost-stress checks.

The provider is **Databento US Equities**. Its documentation lists one-minute OHLCV bars and top-of-book schemas; the latter is appropriate for later bid/ask execution analysis, not a prerequisite for the current bar-level hypothesis. [Databento schemas](https://databento.com/docs/knowledge-base)

## Selected source and coverage

The selected source is **Databento Nasdaq TotalView-ITCH (`XNAS.ITCH`)**, TSLA's primary-listing venue. It supports one-minute OHLCV from 2018-05-01, covering the frozen 2019-2024 development and validation periods. This is a **primary-venue** series, not a consolidated US-equities series; it is fit for the clean-room research test but is not assumed to reproduce a TradingView chart exactly.

The user has created a provider account and API key outside this repository. No API key is stored here, and no data request has yet been submitted by this project.

## Phase 3 request

Request a vendor estimate before downloading:

| Field | Required choice |
|---|---|
| Symbol | TSLA, with provider-specific raw-symbol convention documented |
| Period | 2019-01-01 through the current available date |
| Granularity | 1-minute OHLCV, aggregated locally into 5-minute bars |
| Coverage | Nasdaq primary-listing venue; regular US trading session must be present; retain full-session source rows locally for audit |
| Price treatment | Document raw versus split-adjusted prices and ensure one convention for the entire period |
| File format | CSV normalized to the project contract, timestamps as bar opens with explicit UTC offsets |
| Storage | `data/raw/` locally only; never commit licensed raw data or API keys |

On 2026-08-14, the authenticated provider portal quoted **$1.04 in credits** for `XNAS.ITCH`, `OHLCV-1m`, TSLA, 2019-01-01 through 2026-08-13 UTC (92.90 MB). Submission remains pending the user’s confirmation.

## Why not use free short-retention bars?

The charter requires 2019–present data, fixed 2023/2024 validation blocks, and a forward holdout. A short-window download cannot test those conditions. It would make the reported result non-comparable and create a false sense of validation.

## Later execution upgrade

If the one-minute-bar signal passes Phase 3, request a bounded sample of top-of-book data around actual entry/exit windows. Databento’s MBP-1 schema contains top-of-book changes and trades; it is the appropriate input for measuring spread/market-order execution, while a five-minute strategy test remains a bar-level approximation. [MBP-1 documentation](https://databento.com/docs/schemas-and-data-formats/mbp-1?historical=python&live=raw)

## Local preparation

`tools/fetch_databento_ohlcv.py` is an optional downloader/normalizer. It does nothing unless `DATABENTO_API_KEY` is set locally. It converts provider one-minute bars to the repository’s required timezone-aware five-minute CSV and rejects incomplete five-minute aggregates.

```powershell
pip install -r requirements-data.txt
$env:DATABENTO_API_KEY = "..." # keep this outside the repository
python tools/fetch_databento_ohlcv.py --dataset XNAS.ITCH --symbol TSLA --start 2019-01-01 --end 2026-08-14 --output data/raw/tsla_5m.csv
```

Before running the command, confirm the dataset entitlement and vendor estimate in the provider portal. The dataset flag is explicit because availability depends on the account’s current entitlement.
