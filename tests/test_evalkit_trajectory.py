"""Vertex trajectory metrics on hand-built trajectories, and the CLI table."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evalkit.cli import main
from evalkit.trajectory import (
    METRICS,
    load_trajectory_rows,
    mean_ci,
    trajectory_any_order_match,
    trajectory_exact_match,
    trajectory_in_order_match,
    trajectory_precision,
    trajectory_recall,
    trajectory_single_tool_use,
    trajectory_table,
)

# (actual, expected) -> exact, in_order, any_order, precision, recall
CASES = [
    (["a", "b"], ["a", "b"], 1, 1, 1, 1.0, 1.0),
    (["b", "a"], ["a", "b"], 0, 0, 1, 1.0, 1.0),  # order only
    (["a", "x", "b"], ["a", "b"], 0, 1, 1, 2 / 3, 1.0),  # extra call
    (["a"], ["a", "b"], 0, 0, 0, 1.0, 0.5),  # missing call
    (["x", "y"], ["a", "b"], 0, 0, 0, 0.0, 0.0),
    # duplicates: in-order and any-order need the multiplicity, precision/recall are membership
    (["a"], ["a", "a"], 0, 0, 0, 1.0, 1.0),
    (["a", "a", "a"], ["a"], 0, 1, 1, 1.0, 1.0),
    (["a", "b", "a"], ["a", "a", "b"], 0, 0, 1, 1.0, 1.0),
    (["a", "x", "a"], ["a", "a"], 0, 1, 1, 2 / 3, 1.0),
    # empties
    ([], [], 1, 1, 1, 1.0, 1.0),
    ([], ["a"], 0, 0, 0, 0.0, 0.0),
    (["a"], [], 0, 1, 1, 0.0, 1.0),
]


@pytest.mark.parametrize(("actual", "expected", "ex", "io", "ao", "p", "r"), CASES)
def test_metrics(actual, expected, ex, io, ao, p, r) -> None:
    assert trajectory_exact_match(actual, expected) == ex
    assert trajectory_in_order_match(actual, expected) == io
    assert trajectory_any_order_match(actual, expected) == ao
    assert trajectory_precision(actual, expected) == pytest.approx(p)
    assert trajectory_recall(actual, expected) == pytest.approx(r)


def test_single_tool_use() -> None:
    assert trajectory_single_tool_use(["a", "b", "a"], "a") == 1.0
    assert trajectory_single_tool_use(["b"], "a") == 0.0
    assert trajectory_single_tool_use([], "a") == 0.0


def test_in_order_implies_any_order() -> None:
    pool = ["a", "b", "c"]
    seqs = [[], *([x] for x in pool), *([x, y] for x in pool for y in pool)]
    for actual in seqs:
        for expected in seqs:
            assert trajectory_in_order_match(actual, expected) <= trajectory_any_order_match(
                actual, expected
            )
            assert set(METRICS) == {"exact", "in_order", "any_order", "precision", "recall"}


def test_mean_ci_binary_is_wilson_and_fractional_is_bootstrap() -> None:
    m, lo, hi = mean_ci([1.0] * 10)
    assert (
        m == 1.0 and lo == pytest.approx(0.7225, abs=1e-3) and hi == pytest.approx(1.0)
    )  # Wilson 10/10
    m, lo, hi = mean_ci([0.5, 1.0, 0.0, 1.0])
    assert m == pytest.approx(0.625) and lo < m < hi


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


ROWS = [
    {"task": "t", "model": "m", "example_id": "1", "score": 1, "category": "c1",
     "tool_calls": ["a", "b"], "expected_tools": ["a", "b"]},
    {"task": "t", "model": "m", "example_id": "2", "score": 0, "category": "c2",
     "tool_calls": ["b"], "expected_tools": ["a", "b"]},
    {"task": "t", "model": "m", "example_id": "3", "score": 1, "category": "c2"},
    {"task": "t", "model": "n", "example_id": "1", "score": 1, "category": "c1",
     "tool_calls": [], "expected_tools": []},
]  # fmt: skip


def test_table_pass_rate_and_groups(tmp_path: Path) -> None:
    f = tmp_path / "r.jsonl"
    _write(f, ROWS)
    loaded = load_trajectory_rows(f)
    assert (len(loaded.rows), loaded.skipped) == (3, 1)
    assert [r["example_id"] for r in load_trajectory_rows(f, "n").rows] == ["1"]

    by_model = {label: (n, c) for label, n, c in trajectory_table(loaded.rows, tool="a")}
    n, cols = by_model["m"]
    assert n == 2
    assert cols["pass"][0] == 0.5 and cols["exact"][0] == 0.5 and cols["recall"][0] == 0.75
    assert cols["uses a"][0] == 0.5

    by_cat = {label: n for label, n, _ in trajectory_table(loaded.rows, by="category")}
    assert by_cat == {"m / c1": 1, "m / c2": 1, "n / c1": 1}


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "r.jsonl"
    _write(f, ROWS)
    assert main(["trajectory", str(f), "--model", "m", "--by", "category"]) == 0
    out = capsys.readouterr().out
    assert "## m / c1 (n=1)" in out and "| recall |" in out and "1 rows without" in out
    assert "uses" not in out

    _write(f, [ROWS[2]])
    assert main(["trajectory", str(f)]) == 1
