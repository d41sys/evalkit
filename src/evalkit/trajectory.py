"""Trajectory diagnostics: the Vertex AI agent-evaluation metrics over tool-name lists.

Definitions follow https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-agents.
The page leaves duplicates and empty lists open; the choices here are fixed and pinned by tests:

* ``in_order``: ``expected`` is a subsequence of ``actual`` (a repeated tool must be repeated).
* ``any_order``: every expected call is in ``actual`` with at least its multiplicity.
* ``precision``/``recall``: membership, as the page words them. Precision counts each actual call
  whose tool appears in ``expected``; recall counts each expected call whose tool appears in
  ``actual``. So ``recall`` can be 1 where ``any_order`` is 0 (expected ``[a, a]``, actual ``[a]``).
* Empty ``expected`` is satisfied by anything (``in_order``, ``any_order``, ``recall`` = 1).
  Empty ``actual`` against a non-empty ``expected`` scores 0 everywhere. Both empty scores 1
  everywhere, including ``precision``; ``precision`` of an empty ``actual`` is 0 otherwise.

These are diagnostics. They never feed ``score``: an agent that reaches the right outcome by a
different path is not wrong (Anthropic, "Demystifying evals for AI agents").
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .aggregate import bootstrap_mean_ci
from .statscheck import wilson_interval

Trajectory = Sequence[str]


def trajectory_exact_match(actual: Trajectory, expected: Trajectory) -> float:
    return float(list(actual) == list(expected))


def trajectory_in_order_match(actual: Trajectory, expected: Trajectory) -> float:
    it = iter(actual)
    return float(all(tool in it for tool in expected))  # `in` consumes the iterator


def trajectory_any_order_match(actual: Trajectory, expected: Trajectory) -> float:
    return float(not Counter(expected) - Counter(actual))


def trajectory_precision(actual: Trajectory, expected: Trajectory) -> float:
    if not actual:
        return float(not expected)
    return sum(t in set(expected) for t in actual) / len(actual)


def trajectory_recall(actual: Trajectory, expected: Trajectory) -> float:
    if not expected:
        return 1.0
    return sum(t in set(actual) for t in expected) / len(expected)


def trajectory_single_tool_use(actual: Trajectory, tool: str) -> float:
    return float(tool in actual)


METRICS: dict[str, Callable[[Trajectory, Trajectory], float]] = {
    "exact": trajectory_exact_match,
    "in_order": trajectory_in_order_match,
    "any_order": trajectory_any_order_match,
    "precision": trajectory_precision,
    "recall": trajectory_recall,
}


def mean_ci(values: Sequence[float]) -> tuple[float, float, float]:
    """Mean and 95% interval: Wilson for 0/1 values, percentile bootstrap otherwise."""
    if all(v in (0.0, 1.0) for v in values):
        lo, hi = wilson_interval(int(sum(values)), len(values), 0.95)
        return (float(np.mean(values)) if values else 0.0, lo, hi)
    return bootstrap_mean_ci(values, method="percentile")


@dataclass
class TrajectoryRows:
    rows: list[dict[str, object]]
    skipped: int


def load_trajectory_rows(path: str | Path, model: str | None = None) -> TrajectoryRows:
    """Rows with list-valued ``tool_calls`` and ``expected_tools``; the rest are counted."""
    rows: list[dict[str, object]] = []
    skipped = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if model is not None and row["model"] != model:
                continue
            if isinstance(row.get("tool_calls"), list) and isinstance(
                row.get("expected_tools"), list
            ):
                rows.append(row)
            else:
                skipped += 1
    return TrajectoryRows(rows, skipped)


def trajectory_table(
    rows: Sequence[dict[str, object]], by: str | None = None, tool: str | None = None
) -> list[tuple[str, int, dict[str, tuple[float, float, float]]]]:
    """(label, n, {column: (mean, lo, hi)}) per model, or per (model, group) with ``by``.

    ``pass`` is the mean ``score`` of the same rows, for reading next to the metrics.
    """
    cells: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        label = str(row["model"])
        if by:
            label += f" / {row.get(by, '(none)')}"
        actual, expected = row["tool_calls"], row["expected_tools"]
        assert isinstance(actual, list) and isinstance(expected, list)
        cols = cells.setdefault(label, {})
        cols.setdefault("pass", []).append(float(row["score"]))  # type: ignore[arg-type]
        for name, fn in METRICS.items():
            cols.setdefault(name, []).append(fn(actual, expected))
        if tool:
            cols.setdefault(f"uses {tool}", []).append(trajectory_single_tool_use(actual, tool))
    return [
        (label, len(cols["pass"]), {c: mean_ci(v) for c, v in cols.items()})
        for label, cols in cells.items()
    ]


def render_trajectory(
    table: Sequence[tuple[str, int, dict[str, tuple[float, float, float]]]], skipped: int
) -> str:
    out = []
    for label, n, cols in table:
        out.append(f"## {label} (n={n})\n")
        out.append("| metric | mean | 95% CI |\n|---|---|---|")
        out.extend(f"| {c} | {m:.3f} | [{lo:.3f}, {hi:.3f}] |" for c, (m, lo, hi) in cols.items())
        out.append("")
    if skipped:
        out.append(f"{skipped} rows without `tool_calls` and `expected_tools` skipped.")
    return "\n".join(out)
