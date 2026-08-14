"""Run the Phase 3 fixed-segment and execution-cost validation for TSLA v1.

The signal has no fitted parameters, so segments are evaluation blocks rather
than opportunities to retune. This command intentionally requires every segment
to be named on the command line, preserving the choice in the shell history and
the generated report.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

try:  # Supports both `python tools/...` and package-style test imports.
    from .tsla_breakout_v1 import NY, Trade, audit, load_bars, metrics, replay, write_trades
except ImportError:  # pragma: no cover - direct-script execution path
    from tsla_breakout_v1 import NY, Trade, audit, load_bars, metrics, replay, write_trades

CASES = {
    "base": {"commission_rate": 0.0001, "slippage_ticks": 5},
    "stress": {"commission_rate": 0.0002, "slippage_ticks": 10},
}


def parse_segment(raw: str) -> tuple[str, date, date]:
    try:
        name, start_raw, end_raw = raw.split(":")
        start, end = date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("segment must be NAME:YYYY-MM-DD:YYYY-MM-DD") from error
    if not name or end < start:
        raise argparse.ArgumentTypeError("segment name is required and end must not precede start")
    return name, start, end


def local_signal_date(trade: Trade) -> date:
    return datetime.fromisoformat(trade.signal_time).astimezone(NY).date()


def in_segment(trades: list[Trade], start: date, end: date) -> list[Trade]:
    return [trade for trade in trades if start <= local_signal_date(trade) <= end]


def breakdown(trades: list[Trade]) -> dict:
    groups: dict[str, list[Trade]] = {}
    for trade in trades:
        timestamp = datetime.fromisoformat(trade.signal_time).astimezone(NY)
        keys = (
            f"year/{timestamp.year}",
            f"month/{timestamp.year}-{timestamp.month:02d}",
            f"hour/{timestamp.hour:02d}:{timestamp.minute:02d}",
            f"side/{trade.side}",
        )
        for key in keys:
            groups.setdefault(key, []).append(trade)
    return {key: metrics(value) for key, value in sorted(groups.items())}


def gate_preview(summary: dict) -> dict:
    count = summary["trade_count"]
    return {
        "has_observations": count > 0,
        "positive_mean_after_cost": bool(count and summary["mean_net_pnl"] > 0),
        "positive_median_after_cost": bool(count and summary["median_net_pnl"] > 0),
        "note": "This is a transparent preview only. The charter's regime concentration and Pine parity gates require the full trade lists and Pine export.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--segment",
        type=parse_segment,
        action="append",
        required=True,
        metavar="NAME:START:END",
        help="repeat for each fixed evaluation segment",
    )
    parser.add_argument("--tick-size", type=float, default=0.01)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    bars = load_bars(args.input)
    audit_report = audit(bars)
    (args.output_dir / "audit.json").write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
    if audit_report["issues"] or audit_report["incomplete_rth_days"]:
        raise SystemExit("Data audit failed; Phase 3 result not produced. Read audit.json.")

    report = {
        "input": str(args.input),
        "segments": [{"name": name, "start": start.isoformat(), "end": end.isoformat()} for name, start, end in args.segment],
        "cases": CASES,
        "results": {},
    }
    for case_name, case in CASES.items():
        all_trades = replay(bars, tick_size=args.tick_size, **case)
        report["results"][case_name] = {}
        for name, start, end in args.segment:
            selected = in_segment(all_trades, start, end)
            report["results"][case_name][name] = {
                "summary": metrics(selected),
                "breakdown": breakdown(selected),
                "gate_preview": gate_preview(metrics(selected)),
            }
            write_trades(args.output_dir / f"trades_{case_name}_{name}.csv", selected)

    (args.output_dir / "phase3_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
