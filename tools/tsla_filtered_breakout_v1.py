"""Independent replay for the frozen TSLA five-minute filtered-breakout study."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from datetime import time
from pathlib import Path

try:
    from .tsla_breakout_v1 import Bar, audit, contiguous_same_day, is_rth, load_bars
except ImportError:  # pragma: no cover
    from tsla_breakout_v1 import Bar, audit, contiguous_same_day, is_rth, load_bars

ATR_LENGTH = 14
ADX_SMOOTHING = 14
ADX_MINIMUM = 20.0
RSI_LENGTH = 14
SIGNAL_FIRST = time(9, 50)
SIGNAL_LAST = time(14, 45)
EXIT_TRIGGER_LAST = time(15, 50)
MAX_HOLD_BARS = 12


@dataclass(frozen=True)
class Trade:
    side: str
    signal_time: str
    entry_time: str
    exit_time: str
    entry_fill: float
    exit_fill: float
    adx: float
    completed_hour_rsi: float
    exit_reason: str
    gross_pnl: float
    commission: float
    net_pnl: float


def rma(values: list[float | None], length: int) -> list[float | None]:
    output: list[float | None] = []
    seed: list[float] = []
    current: float | None = None
    for value in values:
        if value is None:
            output.append(None)
            continue
        if current is None:
            seed.append(value)
            if len(seed) == length:
                current = statistics.fmean(seed)
                output.append(current)
            else:
                output.append(None)
        else:
            current = (current * (length - 1) + value) / length
            output.append(current)
    return output


def ema(values: list[float], length: int) -> list[float]:
    alpha = 2 / (length + 1)
    output: list[float] = []
    current: float | None = None
    for value in values:
        current = value if current is None else current + alpha * (value - current)
        output.append(current)
    return output


def rsi(values: list[float], length: int) -> list[float | None]:
    changes = [None] + [current - prior for prior, current in zip(values, values[1:])]
    gains = [None if change is None else max(change, 0.0) for change in changes]
    losses = [None if change is None else max(-change, 0.0) for change in changes]
    average_gain, average_loss = rma(gains, length), rma(losses, length)
    output: list[float | None] = []
    for gain, loss in zip(average_gain, average_loss):
        if gain is None or loss is None:
            output.append(None)
        elif loss == 0:
            output.append(100.0)
        else:
            output.append(100 - 100 / (1 + gain / loss))
    return output


def indicators(bars: list[Bar]) -> tuple[list[float | None], list[float | None], list[float | None], list[float], list[float]]:
    """Return ATR, ADX, last completed hourly RSI, EMA20, and EMA8."""
    true_ranges: list[float | None] = []
    plus_dm: list[float | None] = []
    minus_dm: list[float | None] = []
    for index, bar in enumerate(bars):
        if index == 0:
            true_ranges.append(bar.high - bar.low)
            plus_dm.append(0.0)
            minus_dm.append(0.0)
            continue
        prior = bars[index - 1]
        up_move, down_move = bar.high - prior.high, prior.low - bar.low
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
        true_ranges.append(max(bar.high - bar.low, abs(bar.high - prior.close), abs(bar.low - prior.close)))
    atr = rma(true_ranges, ATR_LENGTH)
    smoothed_plus, smoothed_minus = rma(plus_dm, ATR_LENGTH), rma(minus_dm, ATR_LENGTH)
    dx: list[float | None] = []
    for tr, positive, negative in zip(atr, smoothed_plus, smoothed_minus):
        if tr is None or positive is None or negative is None or tr == 0:
            dx.append(None)
            continue
        plus_di, minus_di = 100 * positive / tr, 100 * negative / tr
        denominator = plus_di + minus_di
        dx.append(None if denominator == 0 else 100 * abs(plus_di - minus_di) / denominator)
    adx = rma(dx, ADX_SMOOTHING)

    completed_hour_rsi: list[float | None] = [None] * len(bars)
    hourly_close: list[float] = []
    hourly_end_indexes: list[int] = []
    day_start = 0
    while day_start < len(bars):
        day = bars[day_start].ny_time.date()
        day_end = day_start
        while day_end < len(bars) and bars[day_end].ny_time.date() == day:
            day_end += 1
        for start in range(day_start, day_end - 11, 12):
            end = start + 11
            hourly_close.append(bars[end].close)
            hourly_end_indexes.append(end)
        day_start = day_end
    hourly_rsi = rsi(hourly_close, RSI_LENGTH)
    # Pine's `request.security(..., rsi[1], lookahead_on)` supplies the last
    # confirmed hourly value throughout the current hour, including across an
    # overnight boundary. Update only after the ending 5-minute bar has closed.
    values_by_end = dict(zip(hourly_end_indexes, hourly_rsi))
    last_completed: float | None = None
    for index in range(len(bars)):
        completed_hour_rsi[index] = last_completed
        if index in values_by_end:
            last_completed = values_by_end[index]
    return atr, adx, completed_hour_rsi, ema([bar.close for bar in bars], 20), ema([bar.close for bar in bars], 8)


def replay(bars: list[Bar], commission_rate: float, slippage_ticks: int, tick_size: float) -> list[Trade]:
    rth = [bar for bar in bars if is_rth(bar)]
    atrs, adxs, hourly_rsi, ema20, ema8 = indicators(rth)
    trades: list[Trade] = []
    active: dict | None = None
    pending: dict | None = None
    slip = slippage_ticks * tick_size
    for index, bar in enumerate(rth):
        if pending is not None and pending["entry_index"] == index:
            entry_fill = bar.open + slip if pending["side"] == "long" else bar.open - slip
            active = {**pending, "entry_fill": entry_fill, "entry_index": index, "entry_time": bar.timestamp.isoformat()}
            pending = None
        was_active = active is not None
        if active is not None:
            side = active["side"]
            close = bar.close
            target = close >= active["entry_fill"] * 1.0275 if side == "long" else close <= active["entry_fill"] * 0.9725
            trailing_ema = ema8[index] if bar.ny_time.time() >= time(15, 0) else ema20[index]
            trail = close < trailing_ema if side == "long" else close > trailing_ema
            back_inside = close <= active["range_high"] if side == "long" else close >= active["range_low"]
            no_progress = index - active["entry_index"] >= 5 and (close <= active["entry_fill"] if side == "long" else close >= active["entry_fill"])
            time_exit = index - active["entry_index"] >= MAX_HOLD_BARS - 1
            session_exit = bar.ny_time.time() >= EXIT_TRIGGER_LAST
            reason = "target" if target else "trailing_ema" if trail else "back_inside" if back_inside else "no_progress" if no_progress else "time" if time_exit else "session" if session_exit else None
            if reason is not None:
                exit_bar = rth[index + 1]
                exit_fill = exit_bar.open - slip if side == "long" else exit_bar.open + slip
                gross = exit_fill - active["entry_fill"] if side == "long" else active["entry_fill"] - exit_fill
                commission = commission_rate * (active["entry_fill"] + exit_fill)
                trades.append(Trade(side, active["signal_time"], active["entry_time"], exit_bar.timestamp.isoformat(), active["entry_fill"], exit_fill, active["adx"], active["hourly_rsi"], reason, gross, commission, gross - commission))
                active = None
        if was_active or pending is not None or index < 4 or index + MAX_HOLD_BARS + 1 >= len(rth):
            continue
        if not SIGNAL_FIRST <= bar.ny_time.time() <= SIGNAL_LAST or not contiguous_same_day(rth, index - 4, index + MAX_HOLD_BARS + 1):
            continue
        atr, adx, htf_rsi = atrs[index], adxs[index], hourly_rsi[index]
        if atr is None or adx is None or htf_rsi is None or adx < ADX_MINIMUM:
            continue
        previous = rth[index - 1]
        range_high, range_low = max(item.high for item in rth[index - 4:index]), min(item.low for item in rth[index - 4:index])
        range_size, candle_range, body = range_high - range_low, bar.high - bar.low, abs(bar.close - bar.open)
        if range_size < 0.50 * atr or candle_range <= 0 or body < 0.50 * atr:
            continue
        long_signal = bar.close > range_high and previous.close <= range_high and bar.close >= bar.high - 0.25 * candle_range and 45 <= htf_rsi <= 70
        short_signal = bar.close < range_low and previous.close >= range_low and bar.close <= bar.low + 0.25 * candle_range and 30 <= htf_rsi <= 55
        side = "long" if long_signal else "short" if short_signal else None
        if side is not None:
            pending = {"side": side, "signal_time": bar.timestamp.isoformat(), "entry_index": index + 1, "range_high": range_high, "range_low": range_low, "adx": adx, "hourly_rsi": htf_rsi}
    return trades


def metrics(trades: list[Trade]) -> dict:
    pnl = [trade.net_pnl for trade in trades]
    positive, negative = sum(value for value in pnl if value > 0), abs(sum(value for value in pnl if value < 0))
    equity = peak = max_drawdown = 0.0
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)
    return {"trade_count": len(trades), "long_count": sum(trade.side == "long" for trade in trades), "short_count": sum(trade.side == "short" for trade in trades), "win_rate": None if not pnl else sum(value > 0 for value in pnl) / len(pnl), "mean_net_pnl": None if not pnl else statistics.fmean(pnl), "median_net_pnl": None if not pnl else statistics.median(pnl), "profit_factor": None if negative == 0 else positive / negative, "net_pnl": sum(pnl), "max_drawdown": max_drawdown}


def write_trades(path: Path, trades: list[Trade]) -> None:
    import csv
    with path.open("w", newline="", encoding="utf-8") as handle:
        fields = list(asdict(Trade("", "", "", "", 0, 0, 0, 0, "", 0, 0, 0)).keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
