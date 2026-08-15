# Trial log

This log counts research attempts, including failures. Do not delete, renumber, or replace entries after observing a result.

| ID | Date | Version | Action | Data status | Outcome |
|---|---|---|---|---|---|
| 001 | 2026-08-14 | Charter v1.0 | Defined a four-prior-bar, 30-minute TSLA RTH continuation signal. | No data ingested | Frozen specification; no performance claim. |
| 002 | 2026-08-14 | Phase 2 | Implemented Pine and independent Python replay; verified deterministic synthetic timing. | Synthetic test only | Passed timing test; no market-data result. |
| 003 | 2026-08-14 | Phase 3 | Added fixed-segment base/stress validator and provenance intake contract. | No data ingested | Pending documented full-history CSV. |
| 004 | 2026-08-14 | Phase 3 | Selected a provider-neutral one-minute OHLCV intake path and added an optional Databento normalizer. | No account/key/data request | Pending user approval of provider account, entitlement, and estimate. |
| 005 | 2026-08-14 | Phase 3 | Verified the authenticated provider catalog and quoted the pre-registered TSLA study period. | No data ingested; user account/API key remain external to repo | `EQUS.MINI` failed the 2019 coverage requirement; selected `XNAS.ITCH` primary-venue OHLCV-1m. Portal quote: $1.04 in credits for 2019-01-01 through 2026-08-13 UTC; submission pending approval. |
| 006 | 2026-08-14 | Phase 3 | Replaced the paid-data intake path after screening documented free alternatives. | No data ingested | Alpaca Basic historical SIP bars cover the fixed period; adapter prepared, pending local API credentials. |

## Log rule

Any new filter, threshold, date boundary, fill model, data correction, or code change gets a new row before its result is viewed. A failed version is retained; it cannot be silently replaced by a better-looking variant.
