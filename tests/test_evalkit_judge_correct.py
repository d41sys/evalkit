"""Judge-corrected pass rate: known answers, error cases, CLI, Monte Carlo coverage."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from evalkit.cli import main
from evalkit.judge_correct import correct_pass_rate, coverage_check


def _calibration(tp: int, fn: int, tn: int, fp: int) -> tuple[list[int], list[int]]:
    judge = [1] * tp + [0] * fn + [0] * tn + [1] * fp
    human = [1] * (tp + fn) + [0] * (tn + fp)
    return judge, human


def test_known_answer() -> None:
    # TPR 0.7, TNR 0.9; true theta 0.5 gives judge rate 0.5*0.7 + 0.5*0.1 = 0.4
    cj, ch = _calibration(70, 30, 90, 10)
    c = correct_pass_rate([1] * 400 + [0] * 600, cj, ch)
    assert (c.tpr, c.tnr, c.raw_rate) == (0.7, 0.9, 0.4)
    assert c.theta == pytest.approx(0.5)
    # delta-method variance by hand
    var = (0.4 * 0.6 / 1000 + 0.25 * 0.21 / 100 + 0.25 * 0.09 / 100) / 0.6**2
    assert c.ci[0] == pytest.approx(0.5 - 1.959964 * math.sqrt(var), abs=1e-5)
    assert c.ci[1] == pytest.approx(0.5 + 1.959964 * math.sqrt(var), abs=1e-5)
    assert c.ci[0] < c.raw_ci[0] or c.ci[1] > c.raw_ci[1]


def test_clipped_to_unit_interval() -> None:
    cj, ch = _calibration(70, 30, 90, 10)
    assert correct_pass_rate([1] * 100, cj, ch).theta == 1.0  # raw 1.0 > TPR
    c = correct_pass_rate([0] * 100, cj, ch)  # raw 0 < 1 - TNR... corrected is negative
    assert c.theta == 0.0 and c.ci[0] == 0.0


@pytest.mark.parametrize(
    "cal, msg",
    [
        (_calibration(50, 50, 50, 50), "TPR \\+ TNR"),  # chance
        (_calibration(30, 70, 40, 60), "TPR \\+ TNR"),  # worse than chance
        (_calibration(5, 5, 0, 0), "both classes"),
    ],
)
def test_unusable_judge_errors(cal: tuple[list[int], list[int]], msg: str) -> None:
    with pytest.raises(ValueError, match=msg):
        correct_pass_rate([1, 0, 1, 0], *cal)


def _write(path: Path, rows: list[dict[str, object]]) -> str:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(path)


def test_cli_matches_library_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cj, ch = _calibration(7, 3, 9, 1)
    verdicts = cj + [1] * 10 + [0] * 20  # 20 labelled + 30 unlabelled
    judge = _write(
        tmp_path / "j.jsonl",
        [
            {"task": "t", "model": "m", "example_id": str(i), "score": v}
            for i, v in enumerate(verdicts)
        ],
    )
    labels = _write(
        tmp_path / "l.jsonl", [{"example_id": str(i), "label": h} for i, h in enumerate(ch)]
    )
    assert main(["judge-correct", "--judge", judge, "--labels", labels]) == 0
    out = capsys.readouterr().out
    expect = correct_pass_rate(verdicts, cj, ch)
    assert f"corrected pass rate:  {100 * expect.theta:.1f}%" in out
    assert "TPR" in out and "TNR" in out and "raw judge pass rate" in out

    # label for an unjudged item, and a judge no better than chance, are errors (exit 1)
    bad = _write(tmp_path / "b.jsonl", [{"example_id": "nope", "label": 1}])
    assert main(["judge-correct", "--judge", judge, "--labels", bad]) == 1
    chance = _write(
        tmp_path / "c.jsonl",
        [{"example_id": str(i), "label": 1 - v} for i, v in enumerate(cj)],
    )
    assert main(["judge-correct", "--judge", judge, "--labels", chance]) == 1
    assert "TPR + TNR" in capsys.readouterr().err


def test_coverage_in_lee_setup() -> None:
    rows = coverage_check(reps=400, seed=1)
    for r in rows:
        assert 0.91 <= r.corrected.value <= 0.99, r
    # the naive interval ignores the judge's bias: far off wherever the bias is large
    assert next(r for r in rows if r.theta == 0.5).naive.value < 0.2
