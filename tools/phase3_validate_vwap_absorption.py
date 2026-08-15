"""Fixed-segment validation for the frozen TSLA VWAP absorption study."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

try:
    from .tsla_breakout_v1 import NY, audit, load_bars
    from .tsla_vwap_absorption_v1 import Trade, metrics, replay, write_trades
except ImportError:  # pragma: no cover
    from tsla_breakout_v1 import NY, audit, load_bars
    from tsla_vwap_absorption_v1 import Trade, metrics, replay, write_trades

CASES = {"base": {"commission_rate": 0.0001, "slippage_ticks": 5}, "stress": {"commission_rate": 0.0002, "slippage_ticks": 10}}


def parse_segment(raw: str) -> tuple[str, date, date]:
    try:
        name, start_raw, end_raw = raw.split(":")
        start, end = date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("segment must be NAME:YYYY-MM-DD:YYYY-MM-DD") from error
    if not name or end < start:
        raise argparse.ArgumentTypeError("segment name is required and end must not precede start")
    return name, start, end


def signal_date(trade: Trade) -> date:
    return datetime.fromisoformat(trade.signal_time).astimezone(NY).date()


def breakdown(trades: list[Trade]) -> dict:
    groups: dict[str, list[Trade]] = {}
    for trade in trades:
        stamp = datetime.fromisoformat(trade.signal_time).astimezone(NY)
        for key in (f"year/{stamp.year}", f"month/{stamp.year}-{stamp.month:02d}", f"side/{trade.side}", f"exit/{trade.exit_reason}"):
            groups.setdefault(key, []).append(trade)
    return {key: metrics(value) for key, value in sorted(groups.items())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--segment", type=parse_segment, action="append", required=True, metavar="NAME:START:END")
    parser.add_argument("--tick-size", type=float, default=0.01)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    bars = load_bars(args.input)
    intake = audit(bars)
    (args.output_dir / "audit.json").write_text(json.dumps(intake, indent=2), encoding="utf-8")
    if intake["issues"] or intake["incomplete_rth_days"]:
        raise SystemExit("Data audit failed; Phase 3 result not produced. Read audit.json.")
    report = {"input": str(args.input), "segments": [{"name": n, "start": s.isoformat(), "end": e.isoformat()} for n, s, e in args.segment], "cases": CASES, "results": {}}
    for case_name, case in CASES.items():
        all_trades = replay(bars, tick_size=args.tick_size, **case)
        report["results"][case_name] = {}
        for name, start, end in args.segment:
            selected = [trade for trade in all_trades if start <= signal_date(trade) <= end]
            summary = metrics(selected)
            report["results"][case_name][name] = {"summary": summary, "breakdown": breakdown(selected)}
            write_trades(args.output_dir / f"trades_{case_name}_{name}.csv", selected)
    (args.output_dir / "phase3_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({case: {segment: value["summary"] for segment, value in values.items()} for case, values in report["results"].items()}, indent=2))


if __name__ == "__main__":
    main()
