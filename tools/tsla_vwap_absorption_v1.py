"""Independent replay for the frozen TSLA five-minute VWAP absorption study."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from datetime import time
from pathlib import Path

try:
    from .tsla_breakout_v1 import BAR, NY, Bar, audit, contiguous_same_day, is_rth, load_bars
except ImportError:  # pragma: no cover - direct-script execution path
    from tsla_breakout_v1 import BAR, NY, Bar, audit, contiguous_same_day, is_rth, load_bars

LOOKBACK = 20
ATR_LENGTH = 14
VOLUME_PERCENTILE = 80
COMPRESSION_MULTIPLE = 0.50
SIGNAL_FIRST = time(11, 10)
SIGNAL_LAST = time(14, 45)
EXIT_TRIGGER_LAST = time(15, 50)
MAX_HOLD_BARS = 12  # next-open exit after 60 minutes


@dataclass(frozen=True)
class Trade:
    side: str
    signal_time: str
    entry_time: str
    exit_time: str
    signal_vwap: float
    signal_atr: float
    entry_fill: float
    exit_fill: float
    exit_reason: str
    gross_pnl: float
    commission: float
    net_pnl: float


def nearest_rank(values: list[float], percentile: int) -> float:
    """Pine-compatible nearest-rank percentile, where rank is one-indexed."""
    ordered = sorted(values)
    rank = max(1, (len(ordered) * percentile + 99) // 100)
    return ordered[rank - 1]


def indicators(bars: list[Bar]) -> tuple[list[float], list[float | None]]:
    """Return session VWAP and continuous 14-bar Wilder ATR at each RTH bar."""
    vwaps: list[float] = []
    atrs: list[float | None] = []
    cumulative_pv = 0.0
    cumulative_volume = 0.0
    previous_day = None
    previous_close: float | None = None
    seed_tr: list[float] = []
    atr: float | None = None
    for bar in bars:
        day = bar.ny_time.date()
        if day != previous_day:
            cumulative_pv = 0.0
            cumulative_volume = 0.0
            previous_day = day
        typical = (bar.high + bar.low + bar.close) / 3
        cumulative_pv += typical * bar.volume
        cumulative_volume += bar.volume
        vwaps.append(cumulative_pv / cumulative_volume)

        true_range = bar.high - bar.low if previous_close is None else max(
            bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close)
        )
        if atr is None:
            seed_tr.append(true_range)
            if len(seed_tr) == ATR_LENGTH:
                atr = statistics.fmean(seed_tr)
        else:
            atr = (atr * (ATR_LENGTH - 1) + true_range) / ATR_LENGTH
        atrs.append(atr)
        previous_close = bar.close
    return vwaps, atrs


def replay(bars: list[Bar], commission_rate: float, slippage_ticks: int, tick_size: float) -> list[Trade]:
    rth = [bar for bar in bars if is_rth(bar)]
    vwaps, atrs = indicators(rth)
    trades: list[Trade] = []
    active: dict | None = None
    pending: dict | None = None
    slip = slippage_ticks * tick_size

    for index, bar in enumerate(rth):
        # A market entry submitted at the prior close fills at this bar's open.
        if pending is not None and pending["entry_index"] == index:
            entry_fill = bar.open + slip if pending["side"] == "long" else bar.open - slip
            active = {**pending, "entry_fill": entry_fill, "entry_index": index, "entry_time": bar.timestamp.isoformat()}
            pending = None

        was_active = active is not None
        if active is not None:
            side = active["side"]
            reached_vwap = bar.close >= active["signal_vwap"] if side == "long" else bar.close <= active["signal_vwap"]
            adverse = bar.close <= active["entry_fill"] - active["signal_atr"] if side == "long" else bar.close >= active["entry_fill"] + active["signal_atr"]
            time_exit = index - active["entry_index"] >= MAX_HOLD_BARS - 1
            session_exit = bar.ny_time.time() >= EXIT_TRIGGER_LAST
            reason = "vwap" if reached_vwap else "adverse_atr" if adverse else "time" if time_exit else "session" if session_exit else None
            if reason is not None:
                exit_bar = rth[index + 1]
                exit_fill = exit_bar.open - slip if side == "long" else exit_bar.open + slip
                gross = exit_fill - active["entry_fill"] if side == "long" else active["entry_fill"] - exit_fill
                commission = commission_rate * (active["entry_fill"] + exit_fill)
                trades.append(Trade(
                    side=side,
                    signal_time=active["signal_time"],
                    entry_time=active["entry_time"],
                    exit_time=exit_bar.timestamp.isoformat(),
                    signal_vwap=active["signal_vwap"],
                    signal_atr=active["signal_atr"],
                    entry_fill=active["entry_fill"],
                    exit_fill=exit_fill,
                    exit_reason=reason,
                    gross_pnl=gross,
                    commission=commission,
                    net_pnl=gross - commission,
                ))
                active = None

        if was_active or pending is not None or index < LOOKBACK or index + MAX_HOLD_BARS + 1 >= len(rth):
            continue
        if not SIGNAL_FIRST <= bar.ny_time.time() <= SIGNAL_LAST:
            continue
        if not contiguous_same_day(rth, index - LOOKBACK, index + MAX_HOLD_BARS + 1):
            continue
        atr = atrs[index]
        if atr is None:
            continue
        volume_threshold = nearest_rank([prior.volume for prior in rth[index - LOOKBACK:index]], VOLUME_PERCENTILE)
        compressed = (bar.high - bar.low) <= COMPRESSION_MULTIPLE * atr
        side = "short" if bar.close > vwaps[index] else "long" if bar.close < vwaps[index] else None
        if side is None or bar.volume < volume_threshold or not compressed:
            continue
        pending = {
            "side": side,
            "signal_time": bar.timestamp.isoformat(),
            "signal_vwap": vwaps[index],
            "signal_atr": atr,
            "entry_index": index + 1,
        }
    return trades


def metrics(trades: list[Trade]) -> dict:
    pnl = [trade.net_pnl for trade in trades]
    positive = sum(value for value in pnl if value > 0)
    negative = abs(sum(value for value in pnl if value < 0))
    equity = peak = max_drawdown = 0.0
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
    import csv
    with path.open("w", newline="", encoding="utf-8") as handle:
        fields = list(asdict(Trade("", "", "", "", 0, 0, 0, 0, "", 0, 0, 0)).keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
