"""Item audit: items that give no signal or look broken.

A sample passes when its score is >= 1, so the flags are exact for 0/1 scores. A continuous
score below 1 counts as a fail for passing, but an item only counts as "all fail" when every
sample scores exactly 0 (an item with partial credit is not broken).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .results import ItemKey, ResultsTable


@dataclass
class AuditReport:
    all_fail: list[ItemKey]
    saturated: list[ItemKey]
    baseline_pass: dict[ItemKey, list[str]]
    """Item -> baselines that passed at least one sample."""
    disagreement: dict[ItemKey, dict[str, float]]
    """Item -> model -> min(p, 1 - p), only for models above the threshold."""


def audit(
    table: ResultsTable,
    baselines: Sequence[str] = (),
    oracle: str | None = None,
    disagreement: float = 0.3,
) -> AuditReport:
    """Flag items; raises ValueError for a baseline or oracle that is not in the table."""
    models = table.models()
    unknown = [m for m in [*baselines, *([oracle] if oracle else [])] if m not in models]
    if unknown:
        raise ValueError(f"not in the results file: {', '.join(unknown)}")
    judged = [m for m in models if m not in baselines or m == oracle]
    items = sorted({k for m in models for k in table.samples[m]})
    report = AuditReport([], [], {}, {})
    for key in items:
        by_model = {m: table.samples[m][key] for m in models if key in table.samples[m]}
        if all(s <= 0 for v in by_model.values() for s in v):
            report.all_fail.append(key)
        if judged and all(m in by_model and min(by_model[m]) >= 1 for m in judged):
            report.saturated.append(key)
        if passed := [m for m in baselines if m in by_model and max(by_model[m]) >= 1]:
            report.baseline_pass[key] = passed
        mixed = {}
        for m, v in by_model.items():
            p = sum(s >= 1 for s in v) / len(v)
            if len(v) > 1 and min(p, 1 - p) > disagreement:
                mixed[m] = min(p, 1 - p)
        if mixed:
            report.disagreement[key] = mixed
    return report


def render_audit(report: AuditReport, disagreement: float) -> str:
    """One section per flag, then one summary line per flag."""

    def name(key: ItemKey) -> str:
        return f"{key[0]}/{key[1]}"

    sections = [
        ("all models fail (candidate broken task)", [name(k) for k in report.all_fail]),
        ("saturated (every non-baseline model passes)", [name(k) for k in report.saturated]),
        (
            "passed by a trivial baseline",
            [f"{name(k)} ({', '.join(m)})" for k, m in report.baseline_pass.items()],
        ),
        (
            f"cross-trial disagreement > {disagreement:g}",
            [
                f"{name(k)} ({', '.join(f'{m} {d:.2f}' for m, d in v.items())})"
                for k, v in report.disagreement.items()
            ],
        ),
    ]
    lines: list[str] = []
    for title, rows in sections:
        lines.append(f"{title}: {len(rows)}")
        lines.extend(f"  {r}" for r in rows)
    lines.append("")
    lines.append(
        "summary: " + ", ".join(f"{t.split(' (')[0].split(' >')[0]} {len(r)}" for t, r in sections)
    )
    return "\n".join(lines)
