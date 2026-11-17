"""Pass rate per period of graded production sessions, with an alert on the latest period.

Rows are ``results.jsonl`` rows with the period (for example ``2026-W47``) as ``task`` and one
session as ``example_id``; a session passes when its score is >= 1 (as in ``audit``). Periods sort
as strings, so ISO weeks or dates order correctly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .results import load_results
from .small_n_ci import wilson_interval


@dataclass(frozen=True)
class PeriodRate:
    period: str
    passed: int
    n: int
    lo: float
    hi: float

    @property
    def rate(self) -> float:
        return self.passed / self.n


def period_rates(results: str | Path, model: str | None = None) -> list[PeriodRate]:
    """Wilson 95% interval of the session pass rate per period, oldest first."""
    table = load_results(results)
    models = [model] if model else table.models()
    if model and model not in table.samples:
        raise ValueError(f"{results}: no rows for model {model!r}")
    counts: dict[str, list[int]] = {}
    for m in models:
        for (period, _), score in table.item_scores(m).items():
            c = counts.setdefault(period, [0, 0])
            c[0] += score >= 1
            c[1] += 1
    return [PeriodRate(p, k, n, *wilson_interval(k, n)) for p, (k, n) in sorted(counts.items())]


def render_monitor(rates: list[PeriodRate], threshold: float) -> tuple[str, bool]:
    """Markdown table and whether the latest period's lower bound is below ``threshold``."""
    lines = ["| period | sessions | pass rate | 95% Wilson CI |", "|---|---|---|---|"]
    lines += [f"| {r.period} | {r.n} | {r.rate:.3f} | [{r.lo:.3f}, {r.hi:.3f}] |" for r in rates]
    alert = bool(rates) and rates[-1].lo < threshold
    if alert:
        last = rates[-1]
        lines.append(
            f"\nALERT: {last.period} lower bound {last.lo:.3f} < threshold {threshold:.3f} "
            f"({last.passed}/{last.n} passed)"
        )
    return "\n".join(lines), alert
