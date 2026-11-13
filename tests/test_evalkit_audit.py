"""Item audit flags, including a fixture shaped like the ezcross forecast-v1 floor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evalkit.audit import audit
from evalkit.cli import main
from evalkit.results import load_results

FORECAST_IDS = [
    "clarify-no-dataset", "clarify-two-datasets", "clarify-m1-unscoped",
    "clarify-rerun-two-tasks", "blocked-late-weather", "blocked-leaky-covariates",
    "blocked-short-history", "happy-m1-better", "happy-no-baseline",
    "happy-rollout-accepted", "nonwin-worse", "nonwin-not-significant", "nonwin-failed-run",
    "followup-latest-mae", "followup-model-used", "numbers-percent-better", "numbers-mwh",
    "refusal-dispatch", "refusal-no-run", "denied-no-run",
]  # fmt: skip


def _write(path: Path, rows: list[tuple[str, str, float]]) -> Path:
    """Rows (model, example_id, score); a repeated pair becomes consecutive samples."""
    path.write_text(
        "".join(
            json.dumps({"task": "t", "model": m, "example_id": i, "score": s}) + "\n"
            for m, i, s in rows
        )
    )
    return path


def test_floor_fixture_flags_refusal_dispatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    rows = [("local/scripted", i, 1.0) for i in FORECAST_IDS]
    rows += [("local/donothing", i, 0.0) for i in FORECAST_IDS]
    rows += [("local/refuseall", i, float(i == "refusal-dispatch")) for i in FORECAST_IDS]
    path = _write(tmp_path / "r.jsonl", rows)
    argv = ["audit", str(path), "--baseline", "local/donothing", "local/refuseall"]
    assert main([*argv, "--oracle", "local/scripted"]) == 0
    out = capsys.readouterr().out
    assert "passed by a trivial baseline: 1\n  t/refusal-dispatch (local/refuseall)" in out
    assert "all models fail (candidate broken task): 0" in out
    assert "saturated (every non-baseline model passes): 20" in out


def test_all_fail_and_saturated(tmp_path: Path):
    rows = [
        ("a", "dead", 0.0), ("b", "dead", 0.0),
        ("a", "easy", 1.0), ("b", "easy", 1.0),
        ("a", "mid", 1.0), ("b", "mid", 0.0),
        ("a", "partial", 0.4), ("b", "partial", 0.0),
    ]  # fmt: skip
    r = audit(load_results(_write(tmp_path / "r.jsonl", rows)))
    assert r.all_fail == [("t", "dead")]  # partial credit is not "broken"
    assert r.saturated == [("t", "easy")]
    assert r.baseline_pass == {}


def test_baseline_is_excluded_from_saturation(tmp_path: Path):
    rows = [("a", "x", 1.0), ("base", "x", 0.0), ("a", "y", 1.0), ("base", "y", 1.0)]
    r = audit(load_results(_write(tmp_path / "r.jsonl", rows)), baselines=["base"])
    assert r.saturated == [("t", "x"), ("t", "y")]
    assert r.baseline_pass == {("t", "y"): ["base"]}


def test_disagreement_needs_mixed_samples_above_threshold(tmp_path: Path):
    # "flaky": 2 of 4 samples pass (0.5); "mostly": 3 of 4 (0.25); "stable": all pass
    rows = [("a", "flaky", s) for s in (1, 0, 1, 0)]
    rows += [("a", "mostly", s) for s in (1, 1, 1, 0)]
    rows += [("a", "stable", 1.0)] * 4
    table = load_results(_write(tmp_path / "r.jsonl", rows))
    assert audit(table, disagreement=0.3).disagreement == {("t", "flaky"): {"a": 0.5}}
    assert set(audit(table, disagreement=0.2).disagreement) == {("t", "flaky"), ("t", "mostly")}


def test_unknown_baseline_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    path = _write(tmp_path / "r.jsonl", [("a", "x", 1.0)])
    assert main(["audit", str(path), "--baseline", "nope"]) == 1
    assert "nope" in capsys.readouterr().err
