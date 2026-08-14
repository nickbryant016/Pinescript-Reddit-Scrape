"""Audit and independently replay the frozen TSLA 5-minute clean-room study.

Input CSV timestamps represent bar *opens* and must be timezone-aware ISO-8601
timestamps. This program intentionally uses only the Python standard library so
that the data and execution assumptions stay visible and portable.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
BAR = timedelta(minutes=5)
RTH_OPEN = time(9, 30)
RTH_LAST = time(15, 55)
SIGNAL_FIRST = time(9, 50)  # closes at 09:55; four previous RTH bars exist
SIGNAL_LAST = time(15, 20)  # closes at 15:25


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def ny_time(self) -> datetime:
        return self.timestamp.astimezone(NY)


@dataclass(frozen=True)
class Trade:
    side: str
    signal_time: str
    entry_time: str
    exit_time: str
    range_high: float
    range_low: float
    entry_fill: float
    exit_fill: float
    gross_pnl: float
    commission: float
    net_pnl: float


def parse_timestamp(value: str) -> datetime:
    value = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit UTC offset or Z")
    return parsed


def load_bars(path: Path) -> list[Bar]:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain {sorted(required)}; found {reader.fieldnames}")
        bars = [
            Bar(
                timestamp=parse_timestamp(row["timestamp"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in reader
        ]
    if not bars:
        raise ValueError("CSV contains no bars")
    return sorted(bars, key=lambda bar: bar.timestamp)


def is_rth(bar: Bar) -> bool:
    local = bar.ny_time
    return local.weekday() < 5 and RTH_OPEN <= local.time() <= RTH_LAST


def audit(bars: list[Bar]) -> dict:
    issues: list[str] = []
    timestamps = [bar.timestamp for bar in bars]
    if len(set(timestamps)) != len(timestamps):
        issues.append("duplicate timestamps")
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            issues.append("timestamps are not strictly increasing")
            break
    for bar in bars:
        if min(bar.open, bar.high, bar.low, bar.close) <= 0:
            issues.append(f"non-positive price at {bar.timestamp.isoformat()}")
            break
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close) or bar.high < bar.low:
            issues.append(f"invalid OHLC at {bar.timestamp.isoformat()}")
            break

    rth = [bar for bar in bars if is_rth(bar)]
    by_day: dict[str, list[Bar]] = {}
    for bar in rth:
        by_day.setdefault(bar.ny_time.date().isoformat(), []).append(bar)

    incomplete_days: list[dict] = []
    for day, day_bars in by_day.items():
        expected = 42 if day_bars[-1].ny_time.time() == time(12, 55) else 78
        missing = []
        for earlier, later in zip(day_bars, day_bars[1:]):
            if later.timestamp - earlier.timestamp != BAR:
                missing.append({"after": earlier.timestamp.isoformat(), "before": later.timestamp.isoformat()})
        if len(day_bars) != expected or missing:
            incomplete_days.append({"date": day, "bars": len(day_bars), "expected": expected, "gaps": missing})

    discontinuities = []
    for previous, current in zip(rth, rth[1:]):
        if current.ny_time.date() != previous.ny_time.date() and previous.close:
            change = abs(current.open / previous.close - 1)
            if change > 0.20:
                discontinuities.append({"from": previous.timestamp.isoformat(), "to": current.timestamp.isoformat(), "open_gap_pct": round(change * 100, 3)})

    return {
        "input_bars": len(bars),
        "rth_bars": len(rth),
        "first_timestamp": bars[0].timestamp.isoformat(),
        "last_timestamp": bars[-1].timestamp.isoformat(),
        "issues": issues,
        "incomplete_rth_days": incomplete_days,
        "possible_corporate_action_or_data_discontinuities": discontinuities,
    }


def contiguous_same_day(bars: list[Bar], start: int, end: int) -> bool:
    segment = bars[start : end + 1]
    return (
        len(segment) == end - start + 1
        and all(is_rth(bar) for bar in segment)
        and all(bar.ny_time.date() == segment[0].ny_time.date() for bar in segment)
        and all(later.timestamp - earlier.timestamp == BAR for earlier, later in zip(segment, segment[1:]))
    )


def replay(bars: list[Bar], commission_rate: float, slippage_ticks: int, tick_size: float) -> list[Trade]:
    rth = [bar for bar in bars if is_rth(bar)]
    trades: list[Trade] = []
    active_through = -1
    for index in range(4, len(rth) - 7):
        if index < active_through or not contiguous_same_day(rth, index - 4, index + 7):
            continue
        signal = rth[index]
        if not SIGNAL_FIRST <= signal.ny_time.time() <= SIGNAL_LAST:
            continue
        range_bars = rth[index - 4 : index]
        high = max(bar.high for bar in range_bars)
        low = min(bar.low for bar in range_bars)
        prior_close = rth[index - 1].close
        side = "long" if signal.close > high and prior_close <= high else "short" if signal.close < low and prior_close >= low else None
        if side is None:
            continue
        entry = rth[index + 1]
        exit_ = rth[index + 7]
        slip = slippage_ticks * tick_size
        entry_fill = entry.open + slip if side == "long" else entry.open - slip
        exit_fill = exit_.open - slip if side == "long" else exit_.open + slip
        gross = exit_fill - entry_fill if side == "long" else entry_fill - exit_fill
        commission = commission_rate * (entry_fill + exit_fill)
        trades.append(
            Trade(
                side=side,
                signal_time=signal.timestamp.isoformat(),
                entry_time=entry.timestamp.isoformat(),
                exit_time=exit_.timestamp.isoformat(),
                range_high=high,
                range_low=low,
                entry_fill=entry_fill,
                exit_fill=exit_fill,
                gross_pnl=gross,
                commission=commission,
                net_pnl=gross - commission,
            )
        )
        active_through = index + 7
    return trades


def metrics(trades: list[Trade]) -> dict:
    pnl = [trade.net_pnl for trade in trades]
    positive = sum(value for value in pnl if value > 0)
    negative = abs(sum(value for value in pnl if value < 0))
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)
    return {
        "trade_count": len(trades),
        "long_count": sum(trade.side == "long" for trade in trades),
        "short_count": sum(trade.side == "short" for trade in trades),
        "win_rate": None if not pnl else sum(value > 0 for value in pnl) / len(pnl),
        "mean_net_pnl": None if not pnl else statistics.fmean(pnl),
        "median_net_pnl": None if not pnl else statistics.median(pnl),
        "profit_factor": None if negative == 0 else positive / negative,
        "net_pnl": sum(pnl),
        "max_drawdown": max_drawdown,
    }


def write_trades(path: Path, trades: list[Trade]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(Trade("", "", "", "", 0, 0, 0, 0, 0, 0, 0)).keys()))
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV with timestamp,open,high,low,close,volume")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--commission-rate", type=float, default=0.0001, help="per-side rate; v1 base is 0.0001")
    parser.add_argument("--slippage-ticks", type=int, default=5, help="per market order; v1 base is 5")
    parser.add_argument("--tick-size", type=float, default=0.01)
    args = parser.parse_args()
    bars = load_bars(args.input)
    audit_report = audit(bars)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "audit.json").write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
    if audit_report["issues"] or audit_report["incomplete_rth_days"]:
        raise SystemExit("Data audit failed; inspect the input before replaying the strategy.")
    trades = replay(bars, args.commission_rate, args.slippage_ticks, args.tick_size)
    (args.output_dir / "summary.json").write_text(json.dumps(metrics(trades), indent=2), encoding="utf-8")
    write_trades(args.output_dir / "trades.csv", trades)
    print(json.dumps(metrics(trades), indent=2))


if __name__ == "__main__":
    main()
