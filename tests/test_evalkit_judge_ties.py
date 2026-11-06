"""Tie margin analysis (docs/protocol-judge-ties.md): verdicts, split, selection, rule, replay."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

from evalkit.judge_stats import AgreementData, Estimate, cluster_bootstrap

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "mtbench_tie_margin.py"


@pytest.fixture(scope="module")
def tm() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mtbench_tie_margin_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(cluster: str, votes: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "cluster_id": cluster,
        "human_votes": votes,
        "length_a": 10,
        "length_b": 12,
        "gpt4_verdict": "tie",
    }


def test_margin_verdict_boundary_and_missing(tm: ModuleType) -> None:
    assert tm.margin_verdict(5, 5, 0) == "tie"
    assert tm.margin_verdict(6, 5, 0) == "A"
    assert tm.margin_verdict(5, 6, 0) == "B"
    assert tm.margin_verdict(6, 5, 1) == "tie"  # |diff| <= delta is a tie
    assert tm.margin_verdict(7, 5, 1) == "A"
    assert tm.margin_verdict(5, 7, 1) == "B"
    assert tm.margin_verdict(None, 5, 0) == "tie"
    assert tm.margin_verdict(5, None, 3) == "tie"


def test_split_is_whole_questions_deterministic_and_order_free(tm: ModuleType) -> None:
    qs = [f"q{81 + i}" for i in range(71)]
    dev, conf = tm.split_questions(qs)
    assert (len(dev), len(conf)) == (36, 35)
    assert not set(dev) & set(conf) and set(dev) | set(conf) == set(qs)
    assert tm.split_questions(list(reversed(qs)) + qs) == (dev, conf)
    assert tm.split_questions(qs, seed=1) != (dev, conf)


def test_choose_delta_largest_and_ties_to_smaller(tm: ModuleType) -> None:
    s1 = {0.0: np.array([1.0, 0.0]), 1.0: np.array([1.0, 0.0]), 2.0: np.array([0.0, 1.0])}
    assert tm.choose_delta(s1, np.arange(2)) == 0.0  # 0 and 1 tie on 0.5: smaller wins
    assert tm.choose_delta(s1, np.array([1])) == 2.0
    assert tm.choose_delta(s1, np.array([0])) == 0.0


def test_loqo_selection_cv_nested_and_fold_choices(tm: ModuleType) -> None:
    clusters = ["a", "a", "b", "b", "c", "c"]
    # margin 1 is right everywhere except in question c, where 0 is right
    s1 = {
        0.0: np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0]),
        1.0: np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0]),
    }
    res = tm.loqo_selection(s1, clusters)
    assert res["cv_s1"] == {0.0: pytest.approx(1 / 3), 1.0: pytest.approx(2 / 3)}
    assert res["delta_hat"] == 1.0
    assert res["zero_s1"] == pytest.approx(1 / 3)
    # folds a and b are chosen with {1 on the other two}: the other pair holds 1-vs-0 in c, so
    # margin 0 and 1 tie at 0.5 -> 0 wins; fold c trains on a, b -> margin 1
    assert res["fold_choices"] == {"0.0": 2, "1.0": 1}
    assert res["nested_s1"] == pytest.approx((0 + 0 + 0 + 0 + 0 + 0) / 6)
    assert res["folds"] == 3


def test_val_items_agreement_changes_with_margin(tm: ModuleType) -> None:
    rows = [
        _row("q1", [("h1", "tie")]),
        _row("q1", [("h1", "A")]),
        _row("q2", [("h1", "B")]),
        _row("q2", [("h2", "B")]),
    ]
    scores = [(5.0, 5.0), (6.0, 5.0), (4.0, 5.0), (3.0, 7.0)]
    s1 = {}
    for d in (0.0, 1.0, 5.0):
        data = AgreementData(tm.val_items(rows, scores, d))
        s1[d] = data.statistics(np.ones(data.n))["jh_s1"]
    # delta 0: all four verdicts match; delta 1: rows 2 and 3 (|diff| = 1) become ties, so only
    # rows 1 and 4 match; delta 5: everything is a tie, only row 1 matches
    assert s1 == {0.0: 1.0, 1.0: 0.5, 5.0: 0.25}


def test_rule_outcome_truth_table(tm: ModuleType) -> None:
    def e(lo: float, hi: float) -> Estimate:
        return Estimate((lo + hi) / 2, lo, hi)

    assert tm.rule_outcome(e(0.01, 0.05), e(-0.02, 0.0)) == (True, True, True)
    assert tm.rule_outcome(e(0.0, 0.05), e(-0.02, 0.0)) == (False, True, False)  # lo must be > 0
    assert tm.rule_outcome(e(0.01, 0.05), e(-0.05, -0.001)) == (True, False, False)
    assert tm.rule_outcome(e(-0.01, 0.05), e(-0.05, -0.001)) == (False, False, False)


def test_paired_stat_difference_and_mask(tm: ModuleType) -> None:
    rows = [_row(f"q{i // 2}", [("h1", "A"), ("h2", "A")]) for i in range(8)]
    scores = [(6.0, 5.0)] * 4 + [(5.0, 5.0)] * 4
    base = AgreementData(tm.val_items(rows, scores, 0.0))
    arm = AgreementData(tm.val_items(rows, scores, 1.0))
    out = tm.paired_stat(base, arm)(np.ones(8))
    assert out["a_jh_s1"] == pytest.approx(0.5)  # 4 A verdicts match the votes, 4 ties do not
    assert out["b_jh_s1"] == 0.0
    assert out["d_s1"] == pytest.approx(-0.5)
    # a mask that drops the last four items leaves the first four, all correct at delta 0
    mask = np.array([1.0] * 4 + [0.0] * 4)
    masked = tm.paired_stat(base, base, mask)(np.ones(8))
    assert masked["b_jh_s1"] == pytest.approx(1.0) and masked["d_s1"] == pytest.approx(0.5)
    est = cluster_bootstrap(tm.paired_stat(base, arm), base.cluster, n_boot=50, seed=0)
    assert est["d_s1"].value == pytest.approx(-0.5)


def test_committed_dev_selection_replays_from_saved_scores(tm: ModuleType) -> None:
    """Recompute the dev selection from the committed per-item scores and test.jsonl."""
    saved = [
        json.loads(line)
        for line in (ROOT / "data" / "mtbench" / "tie-margin-scores.jsonl").read_text().splitlines()
    ]
    dev_json = json.loads((ROOT / "docs/results/judge-mtbench-tie-margin-dev.json").read_text())
    pairs = {
        r["id"]: r
        for r in map(json.loads, (ROOT / "data/mtbench/test.jsonl").read_text().splitlines())
    }
    dev_q, conf_q = tm.split_questions([s["question"] for s in saved])
    assert {s["question"] for s in saved if s["portion"] == "dev"} == set(dev_q)
    assert {s["question"] for s in saved if s["portion"] == "confirm"} == set(conf_q)
    dev_rows = [s for s in saved if s["portion"] == "dev"]
    rows = [pairs[s["id"]] for s in dev_rows]
    scores = [(s["score_a"], s["score_b"]) for s in dev_rows]
    per_s1 = {d: AgreementData(tm.val_items(rows, scores, d)).judge.a1.copy() for d in tm.GRID}
    res = tm.loqo_selection(per_s1, [s["question"] for s in dev_rows])
    assert res["delta_hat"] == dev_json["delta_hat"]
    assert res["cv_s1"] == {float(k): v for k, v in dev_json["cv_s1"].items()}
    assert len(dev_rows) == dev_json["dev_items"]
