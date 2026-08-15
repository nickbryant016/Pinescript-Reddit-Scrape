"""Fetch Alpaca SIP one-minute bars and normalize them to the project's five-minute CSV.

Credentials are read from APCA_API_KEY_ID/APCA_API_SECRET_KEY or, for a single
process, from standard input. The script never writes credentials and refuses
to emit incomplete five-minute bars.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


API_URL = "https://data.alpaca.markets/v2/stocks/{symbol}/bars"
NEW_YORK = ZoneInfo("America/New_York")
EARLY_CLOSE_DATES = frozenset(
    {
        "2019-07-03", "2019-11-29", "2019-12-24",
        "2020-11-27", "2020-12-24",
        "2021-11-26",
        "2022-11-25",
        "2023-07-03", "2023-11-24",
        "2024-07-03", "2024-11-29", "2024-12-24",
        "2025-07-03", "2025-11-28", "2025-12-24",
    }
)
MARKET_WIDE_HALT_DATES = frozenset({"2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"})


def regular_session_last(local: datetime) -> clock_time:
    return clock_time(12, 55) if local.date().isoformat() in EARLY_CLOSE_DATES else clock_time(15, 55)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="TSLA")
    parser.add_argument("--start", required=True, help="inclusive ISO date/time")
    parser.add_argument("--end", required=True, help="exclusive ISO date/time; must be 15+ minutes old")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--native-5m",
        action="store_true",
        help="request vendor five-minute bars directly after a logged one-minute completeness failure",
    )
    parser.add_argument(
        "--stdin-credentials",
        action="store_true",
        help="read key ID then secret from stdin for one process only; do not use shell history",
    )
    return parser.parse_args()


def request_page(symbol: str, params: dict[str, str], headers: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(API_URL.format(symbol=symbol) + "?" + query, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Alpaca request failed ({error.code}): {body}") from error


def fetch_bars(symbol: str, start: str, end: str, headers: dict[str, str], timeframe: str) -> list[dict]:
    params = {
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": "10000",
        "adjustment": "raw",
        "feed": "sip",
        "sort": "asc",
    }
    bars: list[dict] = []
    while True:
        payload = request_page(symbol, params, headers)
        page = payload.get("bars", [])
        if not isinstance(page, list):
            raise SystemExit(f"Unexpected Alpaca response: {payload}")
        bars.extend(page)
        token = payload.get("next_page_token")
        if not token:
            return bars
        params["page_token"] = token
        time.sleep(0.31)  # Basic-plan ceiling is 200 historical calls per minute.


def to_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def normalize(bars: list[dict]) -> list[dict[str, str | int | float]]:
    groups: dict[datetime, list[dict]] = defaultdict(list)
    seen: set[datetime] = set()
    for bar in bars:
        required = {"t", "o", "h", "l", "c", "v"}
        if not required.issubset(bar):
            raise SystemExit(f"Unexpected Alpaca bar fields: {sorted(bar)}")
        stamp = to_datetime(str(bar["t"]))
        if stamp in seen:
            raise SystemExit(f"Duplicate one-minute timestamp: {stamp.isoformat()}")
        seen.add(stamp)
        local = stamp.astimezone(NEW_YORK)
        if local.weekday() < 5 and clock_time(9, 30) <= local.time() <= regular_session_last(local):
            bucket = local.replace(minute=(local.minute // 5) * 5, second=0, microsecond=0)
            groups[bucket].append(bar)

    output: list[dict[str, str | int | float]] = []
    for bucket in sorted(groups):
        minutes = sorted(groups[bucket], key=lambda item: item["t"])
        if len(minutes) != 5:
            raise SystemExit(f"Incomplete five-minute group at {bucket.isoformat()}: {len(minutes)} source bars")
        output.append(
            {
                "timestamp": bucket.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "open": minutes[0]["o"],
                "high": max(item["h"] for item in minutes),
                "low": min(item["l"] for item in minutes),
                "close": minutes[-1]["c"],
                "volume": sum(item["v"] for item in minutes),
            }
        )
    return output


def normalize_native_five(bars: list[dict]) -> list[dict[str, str | int | float]]:
    """Normalize provider-native five-minute bars without inventing missing minutes."""
    output: list[dict[str, str | int | float]] = []
    seen: set[datetime] = set()
    for bar in bars:
        required = {"t", "o", "h", "l", "c", "v"}
        if not required.issubset(bar):
            raise SystemExit(f"Unexpected Alpaca bar fields: {sorted(bar)}")
        stamp = to_datetime(str(bar["t"]))
        if stamp in seen:
            raise SystemExit(f"Duplicate five-minute timestamp: {stamp.isoformat()}")
        seen.add(stamp)
        local = stamp.astimezone(NEW_YORK)
        if local.weekday() >= 5 or not (clock_time(9, 30) <= local.time() <= regular_session_last(local)):
            continue
        output.append(
            {
                "timestamp": local.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"],
            }
        )
    for earlier, later in zip(output, output[1:]):
        earlier_stamp = datetime.fromisoformat(str(earlier["timestamp"]))
        later_stamp = datetime.fromisoformat(str(later["timestamp"]))
        local_day = earlier_stamp.astimezone(NEW_YORK).date().isoformat()
        if (
            earlier_stamp.astimezone(NEW_YORK).date() == later_stamp.astimezone(NEW_YORK).date()
            and later_stamp - earlier_stamp != timedelta(minutes=5)
            and local_day not in MARKET_WIDE_HALT_DATES
        ):
            raise SystemExit(f"Incomplete provider-native five-minute sequence after {earlier['timestamp']}")
    return output


def main() -> None:
    args = parse_args()
    if args.stdin_credentials:
        key_id = sys.stdin.readline().strip()
        secret = sys.stdin.readline().strip()
    else:
        key_id = os.environ.get("APCA_API_KEY_ID")
        secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key_id or not secret:
        raise SystemExit("Set APCA_API_KEY_ID and APCA_API_SECRET_KEY locally; never add them to the repository.")
    headers = {"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret}
    timeframe = "5Min" if args.native_5m else "1Min"
    source = fetch_bars(args.symbol, args.start, args.end, headers, timeframe)
    normalized = normalize_native_five(source) if args.native_5m else normalize(source)
    if not normalized:
        raise SystemExit("No regular-session bars were returned.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(normalized)
    print(f"Wrote {len(normalized)} normalized five-minute bars to {args.output}")


if __name__ == "__main__":
    main()
