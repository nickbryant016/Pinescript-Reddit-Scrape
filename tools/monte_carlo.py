"""Deterministic circular block-bootstrap diagnostics for fixed trade lists.

This assesses uncertainty in realized trade sequencing and path risk. It is not a
substitute for an untouched out-of-sample result and never selects parameters.
"""

from __future__ import annotations

import math
import random


def percentile(values: list[float], level: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * level
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def circular_block_bootstrap(pnl: list[float], *, replicates: int = 20_000, mean_block: int = 10, seed: int = 20260815) -> dict:
    """Resample contiguous trade blocks, preserving local dependence approximately."""
    if not pnl:
        return {"replicates": 0, "reason": "no trades"}
    if replicates < 1 or mean_block < 1:
        raise ValueError("replicates and mean_block must be positive")
    generator = random.Random(seed)
    terminal: list[float] = []
    drawdowns: list[float] = []
    n = len(pnl)
    restart_probability = 1 / mean_block
    for _ in range(replicates):
        sample: list[float] = []
        index = generator.randrange(n)
        while len(sample) < n:
            sample.append(pnl[index])
            index = (index + 1) % n
            if generator.random() < restart_probability:
                index = generator.randrange(n)
        equity = peak = max_drawdown = 0.0
        for value in sample:
            equity += value
            peak = max(peak, equity)
            max_drawdown = min(max_drawdown, equity - peak)
        terminal.append(equity)
        drawdowns.append(max_drawdown)
    return {
        "method": "circular block bootstrap of chronological trade P&L",
        "replicates": replicates,
        "mean_block_trades": mean_block,
        "seed": seed,
        "observed_trades": n,
        "probability_terminal_pnl_positive": sum(value > 0 for value in terminal) / replicates,
        "terminal_pnl_p05": percentile(terminal, 0.05),
        "terminal_pnl_p50": percentile(terminal, 0.50),
        "terminal_pnl_p95": percentile(terminal, 0.95),
        "max_drawdown_p05": percentile(drawdowns, 0.05),
        "max_drawdown_p50": percentile(drawdowns, 0.50),
        "max_drawdown_p95": percentile(drawdowns, 0.95),
    }
