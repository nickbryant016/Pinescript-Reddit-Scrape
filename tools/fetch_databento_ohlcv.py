"""Fetch provider-authorized 1-minute OHLCV and normalize it to project 5-minute CSV.

This tool deliberately requires a user-supplied Databento API key. It never
prints the key and writes licensed data only to the caller-selected local path.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="provider dataset allowed by the account")
    parser.add_argument("--symbol", default="TSLA")
    parser.add_argument("--start", required=True, help="inclusive ISO date/time")
    parser.add_argument("--end", required=True, help="exclusive ISO date/time")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        raise SystemExit("DATABENTO_API_KEY is required; do not place it in a repository file.")
    try:
        import databento as db
        import pandas as pd
    except ImportError as error:
        raise SystemExit("Install the optional dependencies: pip install -r requirements-data.txt") from error

    client = db.Historical(api_key)
    response = client.timeseries.get_range(
        dataset=args.dataset,
        schema="ohlcv-1m",
        symbols=args.symbol,
        stype_in="raw_symbol",
        start=args.start,
        end=args.end,
    )
    frame = response.to_df().reset_index()
    timestamp_column = next((name for name in ("ts_event", "timestamp") if name in frame.columns), None)
    required = {"open", "high", "low", "close", "volume"}
    if timestamp_column is None or not required.issubset(frame.columns):
        raise SystemExit(f"Unexpected provider response columns: {list(frame.columns)}")

    frame["timestamp"] = pd.to_datetime(frame[timestamp_column], utc=True)
    frame = frame.sort_values("timestamp").set_index("timestamp")
    local = frame.index.tz_convert("America/New_York")
    rth_mask = (
        (local.weekday < 5)
        & (local.time >= __import__("datetime").time(9, 30))
        & (local.time <= __import__("datetime").time(15, 59))
    )
    rth = frame.loc[rth_mask, ["open", "high", "low", "close", "volume"]]
    five = rth.resample("5min", origin="start_day").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        source_minutes=("close", "count"),
    )
    incomplete = five[five["source_minutes"] != 5]
    if not incomplete.empty:
        raise SystemExit(f"Refusing to create 5-minute bars from incomplete minute groups: {len(incomplete)}")
    normalized = five.drop(columns="source_minutes").dropna().reset_index()
    normalized["timestamp"] = normalized["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(args.output, index=False)
    print(f"Wrote {len(normalized)} normalized five-minute bars to {args.output}")


if __name__ == "__main__":
    main()
