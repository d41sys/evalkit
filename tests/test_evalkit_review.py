import csv
import json
import math
from pathlib import Path

from evalkit.cli import main
from evalkit.statscheck import wilson_interval


def _results(path: Path) -> Path:
    rows = [
        {"task": "t", "model": "m1", "example_id": "b", "score": 0.0, "transcript": "m1/b.jsonl"},
        {"task": "t", "model": "m1", "example_id": "a", "score": 0.5, "output": "x"},
        {"task": "t", "model": "m1", "example_id": "c", "score": 1.0},
        {"task": "t", "model": "m1", "example_id": "d", "score": 0.0},
        {"task": "t", "model": "m2", "example_id": "a", "score": 0.0},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def _fill(sheet: Path, modes: dict[tuple[str, str], str]) -> None:
    with open(sheet, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["failure_mode"] = modes.get((r["model"], r["example_id"]), "")
    with open(sheet, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_sheet_failing_only_sorted_with_optional_columns(tmp_path):
    sheet = tmp_path / "s.csv"
    assert main(["review", str(_results(tmp_path / "r.jsonl")), "--out", str(sheet)]) == 0
    with open(sheet, newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0]) == [
        "model", "task", "example_id", "score", "output", "transcript", "note", "failure_mode",
    ]  # fmt: skip
    assert [(r["model"], r["example_id"]) for r in rows] == [
        ("m1", "a"), ("m1", "b"), ("m1", "d"), ("m2", "a"),
    ]  # fmt: skip
    assert rows[1]["transcript"] == "m1/b.jsonl" and rows[0]["output"] == "x"
    assert rows[0]["note"] == rows[0]["failure_mode"] == ""


def test_model_filter_and_all(tmp_path):
    res = _results(tmp_path / "r.jsonl")
    sheet = tmp_path / "s.csv"
    main(["review", str(res), "--out", str(sheet), "--model", "m1", "--all"])
    with open(sheet, newline="") as f:
        assert len(list(csv.DictReader(f))) == 4


def test_round_trip_counts_multi_mode_and_unannotated(tmp_path, capsys):
    sheet = tmp_path / "s.csv"
    main(["review", str(_results(tmp_path / "r.jsonl")), "--out", str(sheet)])
    _fill(sheet, {("m1", "a"): "wrong tool; hallucination", ("m1", "b"): " wrong tool ;;"})
    capsys.readouterr()
    assert main(["failure-modes", str(sheet)]) == 0
    out = capsys.readouterr().out

    from evalkit.review import failure_mode_counts

    reviewed, unannotated, modes = failure_mode_counts(sheet)["m1"]
    assert (reviewed, unannotated) == (2, 1)
    assert [(m, c) for m, c, _ in modes] == [("wrong tool", 2), ("hallucination", 1)]
    lo, hi = modes[0][2]
    exp = wilson_interval(2, 2)
    assert math.isclose(lo, exp[0]) and math.isclose(hi, exp[1])
    assert "m1: 2 reviewed, 1 unannotated" in out
    assert "wrong tool" in out and "100.0%" in out and "50.0%" in out
    assert failure_mode_counts(sheet)["m2"][:2] == (0, 1)


def test_missing_column_is_an_error(tmp_path, capsys):
    p = tmp_path / "s.csv"
    p.write_text("model,task\nm,t\n")
    assert main(["failure-modes", str(p)]) == 1
    assert "failure_mode" in capsys.readouterr().err


def test_missing_file_is_an_error(tmp_path):
    assert main(["failure-modes", str(tmp_path / "nope.csv")]) == 1
