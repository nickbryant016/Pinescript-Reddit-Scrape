# Data acquisition decision — TSLA clean-room study

## Decision

Use documented historical **five-minute OHLCV** for the initial Phase 3 signal study, then use top-of-book trades/quotes only after the signal survives fixed out-of-sample and cost-stress checks.

The initial provider is **Alpaca Basic** using its historical SIP feed. Alpaca documents historical US stock coverage since 2016 and permits SIP historical queries on the free plan when the query end is at least 15 minutes old. The feed is consolidated across US exchanges, which is a better fit for a chart-level TSLA study than a single-venue proxy. [Alpaca plan and coverage](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api) and [historical feed rules](https://docs.alpaca.markets/us/docs/market-data-faq)

## Selected source and coverage

The selected source is **Alpaca SIP**, fetched as provider-native raw five-minute TSLA bars. It covers the frozen 2019-2024 development and validation periods without changing the strategy specification. A strict one-minute-to-five-minute aggregation probe failed its completeness control on 2019-01-17; this is retained in the trial log, and no synthetic bar was created.

No Alpaca credential is stored in this repository. The completed local request is recorded in `DATA_PROVENANCE.md`; raw data remains ignored by Git.

## Phase 3 request

Request a vendor estimate before downloading:

| Field | Required choice |
|---|---|
| Symbol | TSLA, with provider-specific raw-symbol convention documented |
| Period | 2019-01-01 through the current available date |
| Granularity | Provider-native 5-minute OHLCV for the initial run; retain the rejected 1-minute aggregation finding in the trial log |
| Coverage | Alpaca SIP consolidated US-equities feed; regular US trading session must be present; retain full-session source rows locally for audit |
| Price treatment | Document raw versus split-adjusted prices and ensure one convention for the entire period |
| File format | CSV normalized to the project contract, timestamps as bar opens with explicit UTC offsets |
| Storage | `data/raw/` locally only; never commit licensed raw data or API keys |

The data is free under Alpaca Basic's documented historical-access policy. Record the actual request time, credentials' plan, feed (`sip`), adjustment (`raw`), response pagination, and file hash before assessing any results.

## Why not use free short-retention bars?

The charter requires 2019–present data, fixed 2023/2024 validation blocks, and a forward holdout. A short-window download cannot test those conditions. It would make the reported result non-comparable and create a false sense of validation.

## Later execution upgrade

If the one-minute-bar signal passes Phase 3, request a bounded sample of top-of-book data around actual entry/exit windows. Databento’s MBP-1 schema contains top-of-book changes and trades; it is the appropriate input for measuring spread/market-order execution, while a five-minute strategy test remains a bar-level approximation. [MBP-1 documentation](https://databento.com/docs/schemas-and-data-formats/mbp-1?historical=python&live=raw)

## Local preparation

`tools/fetch_alpaca_ohlcv.py` is the primary downloader/normalizer. It requires `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` only in the local shell. The initial run uses its explicit `--native-5m` mode because the provider's one-minute history contained a detected gap; it rejects unexplained incomplete five-minute sequences and does not fill or synthesize bars. Four known 2020 market-wide circuit-breaker interruptions are retained as exceptions and are never bridged by the replay.

```powershell
$env:APCA_API_KEY_ID = "..." # keep both secrets outside the repository
$env:APCA_API_SECRET_KEY = "..."
python tools/fetch_alpaca_ohlcv.py --native-5m --symbol TSLA --start 2019-01-01T00:00:00Z --end 2026-08-14T00:00:00Z --output data/raw/tsla_5m.csv
```

Before running the command, confirm that the credentials belong to the Basic plan and record the data-access terms in `DATA_PROVENANCE.md`.
