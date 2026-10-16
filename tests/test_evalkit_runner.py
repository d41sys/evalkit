from __future__ import annotations

import json
from pathlib import Path

from evalkit.cli import main
from evalkit.models import NoisyModel, OracleModel, RandomModel
from evalkit.runner import EvalRecord, generate_leaderboard, run
from evalkit.spec import TaskSpec


def test_runner_execution_and_resumability(tmp_path: Path) -> None:
    # 1. Create a small mock task
    data_file = tmp_path / "data.jsonl"
    rows = [
        {
            "id": f"q_{i}",
            "question": f"What is {i}+{i}?",
            "target": str(i + i),
            "targets": [str(i + i)],
        }
        for i in range(5)
    ]
    with open(data_file, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(
        f"""
name: test_arithmetic
version: 1.0.0
type: generation
dataset: {data_file.name}
prompt_template: "Q: {{question}}\\nA:"
metrics:
  - exact_match
""",
        encoding="utf-8",
    )

    spec = TaskSpec.from_yaml(spec_file)
    models = [OracleModel(), NoisyModel(noise_rate=0.4, seed=42), RandomModel(seed=42)]
    out_dir = tmp_path / "eval_out"

    # First run: should evaluate 5 examples * 3 models = 15 runs
    summary1 = run([spec], models, out_dir=out_dir, max_workers=2)
    assert summary1.total_evaluated == 15
    assert summary1.total_skipped == 0
    assert summary1.results_path.is_file()
    assert summary1.leaderboard_path.is_file()

    # Verify ranking: oracle > noisy > random
    ranked_names = [m.model_name for m in summary1.leaderboard.models]
    assert ranked_names[0] == "oracle"

    # Second run: Resume should skip all 15 runs!
    summary2 = run([spec], models, out_dir=out_dir, max_workers=2)
    assert summary2.total_evaluated == 0
    assert summary2.total_skipped == 15
    # Leaderboard still generated
    assert len(summary2.leaderboard.models) == 3


def test_classification_mock_models_pick_from_label_set(tmp_path: Path) -> None:
    # Rows carry no "type" key: the label set must come from the spec's targets.
    labels = ["negative", "positive"]
    rows = [{"id": f"s{i}", "text": f"t{i}", "target": labels[i % 2]} for i in range(40)]
    data_file = tmp_path / "data.jsonl"
    data_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    spec = TaskSpec(
        name="sent",
        version="1",
        type="classification",
        dataset=str(data_file),
        prompt_template="{text}",
        metrics=["accuracy"],
    )
    run([spec], [RandomModel(), NoisyModel(noise_rate=1.0)], tmp_path / "out")
    lines = (tmp_path / "out" / "results.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert {r["prediction"] for r in records} <= set(labels)
    noisy = [r for r in records if r["model"].startswith("noisy")]
    assert all(r["score"] == 0.0 for r in noisy)


def test_compare_pairs_only_shared_examples(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    import json as _json

    from evalkit.cli import main

    rows = [
        {"task": "t", "model": "A", "example_id": "1", "score": 1.0},
        {"task": "t", "model": "A", "example_id": "2", "score": 1.0},
        {"task": "t", "model": "A", "example_id": "3", "score": 0.0},
        {"task": "t", "model": "B", "example_id": "1", "score": 0.0},
        {"task": "t", "model": "B", "example_id": "2", "score": 1.0},
    ]
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(_json.dumps(r) for r in rows) + "\n")

    assert main(["compare", str(path), "--a", "A", "--b", "B"]) == 0
    out = capsys.readouterr().out
    assert "paired on 2 examples" in out
    assert "| ALL | 2 | 1.000 | 0.500 | +0.500 |" in out
    assert main(["compare", str(path), "--a", "A", "--b", "missing"]) == 1


def _write_results(path, rows) -> None:  # type: ignore[no-untyped-def]
    with open(path, "w", encoding="utf-8") as f:
        for model, ex, score in rows:
            f.write(
                json.dumps({"task": "t", "model": model, "example_id": ex, "score": score}) + "\n"
            )


def test_compare_all_pairs_cli(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "results.jsonl"
    rows = []
    for i in range(30):
        rows += [("hi", f"e{i}", 1.0), ("mid", f"e{i}", 1.0 if i else 0.0), ("lo", f"e{i}", 0.0)]
    _write_results(path, rows)

    assert main(["compare", str(path), "--all-pairs"]) == 0
    out = capsys.readouterr().out
    assert "3 comparisons" in out
    assert "| hi vs lo | 30 |" in out and "| hi vs mid | 30 |" in out
    assert "| mid vs lo | 30 |" in out
    assert "unresolved (needs n≈" in out
    assert out.count("| resolved |") == 2

    assert main(["compare", str(path), "--all-pairs", "--models", "hi,lo"]) == 0
    out = capsys.readouterr().out
    assert "1 comparisons" in out and "mid" not in out

    assert main(["compare", str(path), "--all-pairs", "--models", "hi,nope"]) == 1
    assert main(["compare", str(path), "--all-pairs", "--a", "hi"]) == 1
    assert main(["compare", str(path)]) == 1


def test_leaderboard_tie_groups() -> None:
    def rec(model: str, ex: int, score: float) -> EvalRecord:
        return EvalRecord("t", model, f"e{ex}", score, {}, "", [], 0.5, int(score))

    records = []
    for i in range(30):
        records += [rec("hi", i, 1.0), rec("mid", i, 1.0 if i else 0.0), rec("lo", i, 0.0)]
    board = generate_leaderboard(records)
    groups = {m.model_name: m.tie_group for m in board.models}
    assert groups == {"hi": 1, "mid": 1, "lo": 2}
    assert "Tie group" in board.to_markdown()
