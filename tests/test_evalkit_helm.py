from __future__ import annotations

import itertools
import json
import math
import urllib.parse
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from evalkit.cli import main
from evalkit.helm import (
    compact_calibration,
    compact_references,
    compact_run,
    family_of,
    import_helm_lite,
    read_table,
    reference_file,
    run_file,
)
from evalkit.helm_metrics import check_calibration, gold_texts, kendall_tau, run_metric_check
from evalkit.helm_study import (
    load_matrix,
    mean_win_rate,
    rank_bootstrap,
    replicate,
    run_study,
    win_rates,
)
from evalkit.metrics.calibration import expected_calibration_error
from evalkit.metrics.code_exec import estimate_pass_at_k

# model -> (gsm scores, mmlu subject x scores, mmlu subject y scores); the HELM table lists the
# models in a scrambled order on purpose, read_table must sort by mean win rate.
SCORES: dict[str, tuple[list[float], list[float], list[float]]] = {
    "Alpha": ([1, 1, 1, 0], [1, 0], [1, 0]),
    "Beta": ([1, 0, 0, 0], [0, 0], [1, 0]),
    "Gamma": ([0, 0, 0, 0], [0, 0], [0, 0]),
}
GSM_REF = [["... The answer is 7", True]]
# model -> predictions behind SCORES; HELM's strict scores are consistent with them except that
# Beta's gsm id1 "7.00" is 0 for HELM (string compare) and Alpha/Beta "The" for gold "A" is 0
MMLU_PREDS = {
    "Alpha": {"x": ["A", "The"], "y": ["B", "A"]},
    "Beta": {"x": ["B", "The"], "y": ["B", "A"]},
    "Gamma": {"x": ["B", "B"], "y": ["A", "A"]},
}


def gsm_predictions(name: str) -> list[str]:
    out = ["The answer is 7" if s == 1 else "The answer is 9" for s in SCORES[name][0]]
    if name == "Beta":
        out[1] = "The answer is 7.00"
    return out


MMLU_REFS = {"x": [[["one", True], ["two", False]]] * 2, "y": [[["one", False], ["two", True]]] * 2}


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def build_fixture(root: Path, drop_run: bool = False) -> None:
    """A miniature of the compact HELM Lite layout (see evalkit.helm)."""
    scenarios = ("GSM8K - EM", "MMLU - EM")
    rows = []
    for name in ("Beta", "Gamma", "Alpha"):
        slug = name.lower()
        gsm, mx, my = SCORES[name]
        gsm_run = f"gsm:model={slug},stop=none"
        mmlu_runs = [f"mmlu:subject={s},method=multiple_choice_joint,model={slug}" for s in "xy"]
        win = {"Alpha": 1.0, "Beta": 0.5, "Gamma": 0.0}[name]
        rows.append(
            [
                {"value": name},
                {"value": win},
                {"value": float(np.mean(gsm)), "run_spec_names": [gsm_run]},
                {
                    "value": (float(np.mean(mx)) + float(np.mean(my))) / 2,
                    "run_spec_names": mmlu_runs,
                },
            ]
        )
        _write(
            run_file(root, gsm_run),
            {
                "metric": "final_number_exact_match",
                "scores": {f"id{i}": v for i, v in enumerate(gsm)},
                "predictions": {f"id{i}": t for i, t in enumerate(gsm_predictions(name))},
            },
        )
        for run, sub, vals in zip(mmlu_runs, "xy", (mx, my), strict=True):
            if drop_run and name == "Gamma" and sub == "y":
                continue
            _write(
                run_file(root, run),
                {
                    "metric": "exact_match",
                    "scores": {f"id{i}": v for i, v in enumerate(vals)},
                    "predictions": {f"id{i}": t for i, t in enumerate(MMLU_PREDS[name][sub])},
                },
            )
    _write(
        root / "core_scenarios.json",
        [{"header": [{"value": h} for h in ("Model", "Mean win rate", *scenarios)], "rows": rows}],
    )
    _write(
        reference_file(root, "gsm:model=a,stop=none"),
        {f"id{i}": GSM_REF for i in range(4)},
    )
    for sub in "xy":
        _write(
            reference_file(root, f"mmlu:subject={sub},method=multiple_choice_joint,model=a"),
            {f"id{i}": ref for i, ref in enumerate(MMLU_REFS[sub])},
        )


def test_family_and_file_names() -> None:
    assert family_of("gsm:model=a,stop=none") == "gsm:stop=none"
    assert family_of("mmlu:subject=x,method=m,model=a") == "mmlu:subject=x,method=m"
    assert family_of("narrative_qa:model=a") == "narrative_qa"
    assert run_file(Path("r"), "a:b,c=d").name == urllib.parse.quote("a:b,c=d", safe="") + ".json"


def test_compact_run_and_references_keep_only_the_evaluation_split() -> None:
    preds = [
        {"instance_id": "id1", "predicted_text": "A", "stats": {"exact_match": 1.0, "x": 5}},
        {"instance_id": "id2", "predicted_text": "B", "stats": {"exact_match": 0.0}},
    ]
    out = compact_run(preds, "exact_match", {"id1"}, keep_text=False)
    assert out == {"metric": "exact_match", "scores": {"id1": 1.0}}
    with_text = compact_run(preds, "exact_match", None, keep_text=True)
    assert with_text["predictions"] == {"id1": "A", "id2": "B"}
    instances = [
        {
            "id": "id1",
            "split": "test",
            "references": [{"output": {"text": "t"}, "tags": ["correct"]}],
        },
        {"id": "id2", "split": "train", "references": [{"output": {"text": "u"}, "tags": []}]},
    ]
    assert compact_references(instances, "test") == {"id1": [["t", True]]}


def test_read_table_sorts_by_win_rate(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    table = read_table(tmp_path)
    assert table.models == ["Alpha", "Beta", "Gamma"]
    assert table.published["Alpha"] == {"gsm8k": 0.75, "mmlu": 0.5}
    assert table.runs["Beta"]["mmlu"][0].startswith("mmlu:subject=x")


def test_import_writes_results_with_subset_prefixed_ids(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    out = tmp_path / "out" / "results.jsonl"
    stats = import_helm_lite(tmp_path, out)
    assert (stats.models, stats.rows, stats.tasks, stats.skipped) == (3, 24, ["gsm8k", "mmlu"], [])
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    alpha = {(r["task"], r["example_id"]): r for r in rows if r["model"] == "Alpha"}
    assert alpha[("gsm8k", "id3")]["score"] == 0.0
    assert alpha[("mmlu", "x/id0")]["score"] == 1.0
    assert alpha[("mmlu", "y/id1")]["metrics"] == {"exact_match": 0.0}
    assert len({r["example_id"] for r in rows if r["task"] == "mmlu"}) == 4


def test_import_skips_models_with_missing_runs_and_validates_names(tmp_path: Path) -> None:
    build_fixture(tmp_path, drop_run=True)
    stats = import_helm_lite(tmp_path, tmp_path / "r.jsonl")
    assert stats.skipped == ["Gamma"] and stats.models == 2
    with pytest.raises(KeyError):
        import_helm_lite(tmp_path, tmp_path / "r.jsonl", ["Nope"])


def test_import_helm_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build_fixture(tmp_path)
    out = tmp_path / "results.jsonl"
    assert (
        main(["import-helm", "--dir", str(tmp_path), "--out", str(out), "--models", "Alpha,Beta"])
        == 0
    )
    assert "Imported 2 models, 16 rows" in capsys.readouterr().out
    assert main(["import-helm", "--dir", str(tmp_path / "nope"), "--out", str(out)]) == 1
    assert main(["import-helm", "--dir", str(tmp_path), "--out", str(out), "--models", "Zed"]) == 1
    # the file feeds the existing commands unchanged
    assert main(["compare", str(out), "--all-pairs"]) == 0
    assert "Alpha vs Beta" in capsys.readouterr().out


def test_win_rates_follow_helm_rule() -> None:
    np.testing.assert_allclose(win_rates(np.array([3.0, 1.0, 2.0])), [1.0, 0.0, 0.5])
    np.testing.assert_allclose(win_rates(np.array([1.0, 1.0, 2.0])), [0.25, 0.25, 1.0])
    got = win_rates(np.array([1.0, np.nan, 2.0]))
    assert got[0] == 0.0 and got[2] == 1.0 and math.isnan(got[1])
    table = np.array([[3.0, 1.0], [1.0, 3.0], [2.0, 2.0]])
    np.testing.assert_allclose(mean_win_rate(table), [0.5, 0.5, 0.5])


def test_replication_matches_the_published_table(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    results = tmp_path / "results.jsonl"
    import_helm_lite(tmp_path, results)
    table = read_table(tmp_path)
    m = load_matrix(results, table.models)
    rep = replicate(m, table)
    assert rep.max_abs_diff == {"gsm8k": 0.0, "mmlu": 0.0}
    assert rep.mwr_max_abs_diff < 1e-12 and rep.order_identical
    boot = rank_bootstrap(m, resamples=30, seed=1)
    assert boot.p_adjacent.shape == (2,) and np.all((boot.p_adjacent >= 0) & (boot.p_adjacent <= 1))
    assert np.all(boot.rank_lo >= 1) and np.all(boot.rank_hi <= 3)


def test_helm_study_report_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build_fixture(tmp_path)
    results = tmp_path / "results.jsonl"
    import_helm_lite(tmp_path, results)
    text = run_study(results, tmp_path, resamples=20, gaps=(1,), num_draws=500)
    assert "## 1. Replication" in text and "## 4. Adjacent pairs" in text
    assert "| 1-2 | Alpha vs Beta |" in text
    report = tmp_path / "report.md"
    args = ["helm-study", "--dir", str(tmp_path), "--results", str(results), "--out", str(report)]
    assert main([*args, "--resamples", "10", "--gaps", "1"]) == 0
    assert report.read_text().startswith("# HELM Lite")
    assert main(["helm-study", "--results", str(tmp_path / "missing.jsonl")]) == 1
    assert "not found" in capsys.readouterr().err


def test_metric_check_finds_the_article_collision(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    assert gold_texts("mmlu", [["a", False], ["b", True]]) == ["B"]
    assert gold_texts("legalbench", [["Yes", True], ["No", False]]) == ["Yes"]
    text = run_metric_check(tmp_path, stride=1)
    # "The" vs gold letter A: evalkit strips the articles "the" and "a" to "" and credits it
    rows = {
        line.split("|")[1].strip(): line for line in text.splitlines() if line.startswith("| m")
    }
    cells = [c.strip() for c in rows["mmlu"].split("|")]
    assert cells[3:7] == ["12", "83.33%", "2", "0"]  # instances, identical, higher, lower
    gsm_line = next(x for x in text.splitlines() if x.startswith("| gsm8k"))
    gsm = [c.strip() for c in gsm_line.split("|")]
    assert gsm[3:7] == ["12", "91.67%", "1", "0"]  # Beta "7.00": numeric equality vs string
    assert kendall_tau([1, 2, 3], [1, 2, 3]) == 1.0 and kendall_tau([1, 2, 3], [3, 2, 1]) == -1.0


def helm_pass_at_k_estimator(n: int, c: int, k: int) -> float:
    """Verbatim from stanford-crfm/helm evaluate_reference_metrics.pass_at_k_estimator."""
    if n - c < k:
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)).item())


def test_pass_at_k_matches_helm_reference_and_brute_force() -> None:
    for n in range(1, 31):
        for c in range(n + 1):
            for k in range(1, n + 1):
                ours = estimate_pass_at_k(n, c, k)
                assert ours == pytest.approx(helm_pass_at_k_estimator(n, c, k), abs=1e-12)
    # exhaustive: fraction of k-subsets of n samples (c correct) containing a correct one
    n, c = 8, 3
    for k in (1, 2, 5):
        subsets = list(itertools.combinations(range(n), k))
        hit = sum(any(i < c for i in s) for s in subsets) / len(subsets)
        assert estimate_pass_at_k(n, c, k) == pytest.approx(hit, abs=1e-12)


def _stat(name: str, mean: float, split: str = "test", perturbed: bool = False) -> dict[str, Any]:
    n: dict[str, Any] = {"name": name, "split": split}
    if perturbed:
        n["perturbation"] = {"name": "robustness"}
    return {"name": n, "mean": mean}


def test_compact_calibration_keeps_plain_test_stats_only() -> None:
    stats = [
        _stat("ece_1_bin", 0.1),
        _stat("ece_10_bin", 0.2),
        _stat("ece_1_bin", 9.0, perturbed=True),
        _stat("ece_1_bin", 8.0, split="valid"),
    ]
    per_instance = [
        {"instance_id": "a", "stats": [_stat("max_prob", 0.9), _stat("exact_match", 1.0)]},
        {"instance_id": "b", "stats": [_stat("max_prob", 0.6, perturbed=True)]},
        {"instance_id": "c", "stats": [_stat("max_prob", 0.7), _stat("exact_match", 0.0)]},
    ]
    cal = compact_calibration(stats, per_instance, "test")
    assert cal == {
        "ece_1_bin": 0.1,
        "ece_10_bin": 0.2,
        "max_prob": {"a": 0.9, "c": 0.7},
        "correct": {"a": 1, "c": 0},
    }
    assert compact_calibration([_stat("exact_match", 1.0)], per_instance, "test") is None


def test_ece_check_agrees_with_helm_for_one_bin(tmp_path: Path) -> None:
    run = "commonsense:dataset=openbookqa,method=multiple_choice_joint,model=m"
    conf = {"a": 0.9, "b": 0.8, "c": 0.6, "d": 0.99}
    correct = {"a": 1, "b": 0, "c": 1, "d": 1}
    one_bin = abs(float(np.mean(list(conf.values()))) - float(np.mean(list(correct.values()))))
    _write(
        run_file(tmp_path, run),
        {
            "metric": "exact_match",
            "scores": {k: float(v) for k, v in correct.items()},
            "calibration": {
                "ece_1_bin": one_bin,
                "ece_10_bin": 0.5,
                "max_prob": conf,
                "correct": correct,
            },
        },
    )
    _write(
        tmp_path / "core_scenarios.json",
        [
            {
                "header": [{"value": h} for h in ("Model", "Mean win rate", "OpenbookQA - EM")],
                "rows": [
                    [
                        {"value": "M"},
                        {"value": 0.5},
                        {"value": 0.75, "run_spec_names": [run]},
                    ]
                ],
            }
        ],
    )
    (check,) = check_calibration(tmp_path, read_table(tmp_path), ["M"])
    assert (check.model, check.task, check.n) == ("M", "openbookqa", 4)
    assert check.evalkit_ece_1 == pytest.approx(check.helm_ece_1, abs=1e-12)
    assert check.evalkit_ece_10 == pytest.approx(
        expected_calibration_error(list(conf.values()), list(correct.values()), n_bins=10)
    )
