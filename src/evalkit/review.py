"""Annotation sheet for failing items and failure-mode counts (open, then axial coding)."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from .statscheck import wilson_interval

OPTIONAL_COLUMNS = ("sample", "prompt", "output", "transcript")


def write_review_sheet(
    results: str | Path, out: str | Path, *, model: str | None = None, include_passes: bool = False
) -> int:
    """Write one CSV row per failing results row (all rows with ``include_passes``)."""
    with open(results, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    rows = [
        r
        for r in rows
        if (model is None or r["model"] == model) and (include_passes or float(r["score"]) < 1)
    ]
    rows.sort(
        key=lambda r: (
            str(r["model"]),
            str(r["task"]),
            str(r["example_id"]),
            str(r.get("sample", "")),
        )
    )
    extra = [c for c in OPTIONAL_COLUMNS if any(c in r for r in rows)]
    header = ["model", "task", "example_id", "score", *extra, "note", "failure_mode"]
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            vals = [r.get(c, "") for c in extra]
            w.writerow([r["model"], r["task"], r["example_id"], r["score"], *vals, "", ""])
    return len(rows)


def failure_mode_counts(
    sheet: str | Path,
) -> dict[str, tuple[int, int, list[tuple[str, int, tuple[float, float]]]]]:
    """Per model: (reviewed rows, unannotated rows, [(mode, count, Wilson 95% CI)] by count).

    A row is reviewed when its ``failure_mode`` cell is non-blank; the cell may hold several
    modes separated by ``;``. Shares are over reviewed rows, so they can sum to more than 1.
    """
    with open(sheet, encoding="utf-8", newline="") as f:
        sheet_rows = list(csv.DictReader(f))
    if sheet_rows and "failure_mode" not in sheet_rows[0]:
        raise ValueError(f"{sheet}: no failure_mode column")
    out: dict[str, tuple[int, int, list[tuple[str, int, tuple[float, float]]]]] = {}
    for model in sorted({r["model"] for r in sheet_rows}):
        counts: Counter[str] = Counter()
        reviewed = unannotated = 0
        for r in (r for r in sheet_rows if r["model"] == model):
            modes = {m.strip() for m in r["failure_mode"].split(";") if m.strip()}
            if not modes:
                unannotated += 1
                continue
            reviewed += 1
            counts.update(modes)
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        out[model] = (
            reviewed,
            unannotated,
            [(m, c, wilson_interval(c, reviewed)) for m, c in ranked],
        )
    return out


def render_failure_modes(
    counts: dict[str, tuple[int, int, list[tuple[str, int, tuple[float, float]]]]],
) -> str:
    lines: list[str] = []
    for model, (reviewed, unannotated, modes) in counts.items():
        lines.append(f"{model}: {reviewed} reviewed, {unannotated} unannotated")
        lines.append(f"  {'failure_mode':<30} {'count':>5} {'share':>7}  95% Wilson CI")
        for mode, c, (lo, hi) in modes:
            lines.append(f"  {mode:<30} {c:>5} {c / reviewed:>7.1%}  [{lo:.1%}, {hi:.1%}]")
    return "\n".join(lines)
