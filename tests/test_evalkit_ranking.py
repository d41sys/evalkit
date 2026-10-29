"""Bradley-Terry ranking and cluster-aware leaderboard intervals."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from evalkit.aggregate import bootstrap_macro_ci, build_pairwise_matches, compare_pairs
from evalkit.clustered import cluster_bootstrap_ci, encode_clusters
from evalkit.helm import compact_clusters
from evalkit.ranking import (
    _comparison_tensor,
    _weighted_wins,
    bradley_terry_bootstrap,
    bradley_terry_ratings,
    fit_theta,
    render_bradley_terry,
    win_matrix,
)
from evalkit.runner import EvalRecord, generate_leaderboard


def _score_equations_hold(wins: np.ndarray, theta: np.ndarray) -> bool:
    games = wins + wins.T
    sigma = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
    return bool(np.allclose((games * sigma).sum(axis=1), wins.sum(axis=1), atol=1e-7))


def test_two_models_closed_form() -> None:
    matches = [("a", "b", 1.0)] * 30 + [("a", "b", 0.0)] * 10
    r = bradley_terry_ratings(matches)
    # p_a / p_b = 30 / 10, so the rating gap is 400 log10(3)
    assert r["a"] - r["b"] == pytest.approx(400 * math.log10(3.0), abs=1e-6)
    assert (r["a"] + r["b"]) / 2 == pytest.approx(1000.0)


def test_mle_satisfies_score_equations_and_ignores_game_order() -> None:
    rng = np.random.default_rng(0)
    strengths = np.array([0.0, 0.6, -0.4, 1.1, 0.2])
    matches: list[tuple[str, str, float]] = []
    for _ in range(600):
        i, j = rng.choice(5, size=2, replace=False)
        p = 1.0 / (1.0 + math.exp(strengths[j] - strengths[i]))
        outcome = 1.0 if rng.random() < p else (0.5 if rng.random() < 0.1 else 0.0)
        matches.append((f"m{i}", f"m{j}", outcome))
    names, wins = win_matrix(matches)
    theta = fit_theta(wins)
    assert _score_equations_hold(wins, theta)
    assert float(theta.mean()) == pytest.approx(0.0, abs=1e-9)
    shuffled = list(matches)
    rng.shuffle(shuffled)  # type: ignore[arg-type]
    a = bradley_terry_ratings(matches)
    b = bradley_terry_ratings(shuffled)
    assert all(a[k] == pytest.approx(b[k], abs=1e-6) for k in a)
    # the fit recovers the order of the generating strengths
    order = sorted(names, key=lambda n: -a[n])
    assert order[0] == "m3" and order[-1] == "m2"


def test_missing_mle_raises_and_ridge_repairs() -> None:
    # c never wins: its strength diverges to -inf without a prior
    matches = [("a", "b", 1.0), ("b", "a", 1.0), ("a", "c", 1.0), ("b", "c", 1.0)]
    with pytest.raises(ValueError, match="does not exist"):
        bradley_terry_ratings(matches)
    r = bradley_terry_ratings(matches, ridge=0.1)
    assert r["c"] < r["a"] and r["c"] < r["b"]


def test_ties_split_games() -> None:
    matches = [("a", "b", 0.5)] * 10 + [("a", "b", 1.0), ("b", "a", 1.0)]
    r = bradley_terry_ratings(matches)
    assert r["a"] == pytest.approx(r["b"], abs=1e-6)


def test_weighted_wins_matches_pairwise_matches() -> None:
    rng = np.random.default_rng(1)
    values = rng.integers(0, 3, size=(40, 4)).astype(float)
    values[rng.random(values.shape) < 0.15] = np.nan
    tensor = _comparison_tensor(values)
    got = _weighted_wins(tensor, np.ones((1, 40)))[0]
    scores = {
        f"i{k}": {f"m{j}": float(values[k, j]) for j in range(4) if not np.isnan(values[k, j])}
        for k in range(40)
    }
    _, want = win_matrix(build_pairwise_matches(scores))
    # win_matrix sorts model names; here m0..m3 sort the same way
    assert np.allclose(got, want)


def _item_scores(n: int = 200, models: int = 4, seed: int = 0) -> dict[str, dict[object, float]]:
    rng = np.random.default_rng(seed)
    ability = np.linspace(1.0, -1.0, models)
    out: dict[str, dict[object, float]] = {f"m{j}": {} for j in range(models)}
    for k in range(n):
        difficulty = rng.normal()
        for j in range(models):
            p = 1.0 / (1.0 + math.exp(-(ability[j] - difficulty)))
            out[f"m{j}"][f"i{k}"] = float(rng.random() < p)
    return out


def test_bootstrap_is_deterministic_and_brackets_the_point() -> None:
    scores = _item_scores()
    a = bradley_terry_bootstrap(scores, resamples=60, seed=3)
    b = bradley_terry_bootstrap(scores, resamples=60, seed=3)
    assert np.array_equal(a.ci_lo, b.ci_lo) and np.array_equal(a.draws, b.draws)
    assert a.failed == 0 and not a.clustered
    assert np.all(a.ci_lo < a.ratings) and np.all(a.ratings < a.ci_hi)
    assert float(a.ratings.mean()) == pytest.approx(1000.0)
    # strongest model first by construction
    assert a.models[int(np.argmax(a.ratings))] == "m0"
    assert a.prob_above("m0", "m3") > 0.99
    assert a.prob_above("m0", "m0") == pytest.approx(0.5)
    assert a.rank_lo[0] == 1.0


def test_cluster_bootstrap_is_wider_when_clusters_are_correlated() -> None:
    rng = np.random.default_rng(2)
    n_clusters, size = 25, 8
    scores: dict[str, dict[object, float]] = {"a": {}, "b": {}, "c": {}}
    clusters: dict[object, object] = {}
    for c in range(n_clusters):
        shift = rng.normal(scale=1.5)  # shared by the cluster's items: one model benefits
        for i in range(size):
            key = f"c{c}-{i}"
            clusters[key] = f"c{c}"
            scores["a"][key] = float(rng.random() < 1.0 / (1.0 + math.exp(-(0.3 + shift))))
            scores["b"][key] = float(rng.random() < 1.0 / (1.0 + math.exp(-(0.0 - shift))))
            scores["c"][key] = float(rng.random() < 0.4)
    plain = bradley_terry_bootstrap(scores, resamples=120, seed=0)
    clus = bradley_terry_bootstrap(scores, clusters=clusters, resamples=120, seed=0)
    assert clus.clustered and not plain.clustered
    assert np.array_equal(plain.ratings, clus.ratings)
    assert float(np.mean(clus.ci_hi - clus.ci_lo)) > float(np.mean(plain.ci_hi - plain.ci_lo))


def test_one_cluster_per_item_equals_item_bootstrap_interval_scale() -> None:
    scores = _item_scores(n=120)
    singles = {k: ("s", k) for k in scores["m0"]}
    a = bradley_terry_bootstrap(scores, resamples=40, seed=0)
    b = bradley_terry_bootstrap(scores, clusters=singles, resamples=40, seed=0)
    assert b.clustered
    assert np.array_equal(a.ratings, b.ratings)  # same point estimate; the resamples are drawn
    # in cluster units, so only compare scale
    assert float(np.mean(b.ci_hi - b.ci_lo)) == pytest.approx(
        float(np.mean(a.ci_hi - a.ci_lo)), rel=0.5
    )


def test_bootstrap_input_errors() -> None:
    with pytest.raises(ValueError, match="at least two"):
        bradley_terry_bootstrap({"a": {"x": 1.0}})
    with pytest.raises(ValueError, match="without any shared item"):
        bradley_terry_bootstrap({"a": {"x": 1.0}, "b": {"y": 0.0}})


def test_render_table() -> None:
    bt = bradley_terry_bootstrap(_item_scores(n=80), resamples=20, seed=0)
    text = render_bradley_terry(bt, {"m0": 1010.0})
    assert "| 1 | m0 |" in text and "Elo (online, order-dependent)" in text
    assert "20 of 20 bootstrap resamples fitted" in text


# --- cluster-aware leaderboard ----------------------------------------------------------------


def _records(
    n_clusters: int = 30, size: int = 6, seed: int = 0, with_clusters: bool = True
) -> list[EvalRecord]:
    rng = np.random.default_rng(seed)
    recs: list[EvalRecord] = []
    for c in range(n_clusters):
        shifts = {"a": rng.normal(scale=1.2), "b": rng.normal(scale=1.2)}  # model x cluster
        for i in range(size):
            for model, base in (("a", 0.4), ("b", 0.0)):
                s = float(rng.random() < 1.0 / (1.0 + math.exp(-(base + shifts[model]))))
                recs.append(
                    EvalRecord(
                        task="t",
                        model=model,
                        example_id=f"c{c}-{i}",
                        score=s,
                        metrics={},
                        prediction="",
                        targets=[],
                        confidence=0.5,
                        correct=int(s),
                        cluster_id=f"c{c}" if with_clusters else None,
                    )
                )
    return recs


def test_leaderboard_ci_without_clusters_is_unchanged() -> None:
    recs = _records(with_clusters=False)
    board = generate_leaderboard(recs)
    scores = [r.score for r in recs if r.model == "a"]
    point, lo, hi = bootstrap_macro_ci({"t": scores}, num_resamples=1000, seed=0)
    m = next(x for x in board.models if x.model_name == "a")
    assert (m.macro_mean, m.ci_lower, m.ci_upper) == (point, lo, hi)
    assert m.clustered_tasks == 0
    assert "whole clusters" not in board.to_markdown()


def test_leaderboard_ci_equals_compare_cluster_bootstrap_for_one_task() -> None:
    recs = _records()
    board = generate_leaderboard(recs)
    for name in ("a", "b"):
        mine = sorted((r.example_id, r.score, r.cluster_id) for r in recs if r.model == name)
        values = [s for _, s, _ in mine]
        codes = encode_clusters([c for _, _, c in mine])
        point, lo, hi = cluster_bootstrap_ci(values, codes, num_resamples=1000, seed=0)
        m = next(x for x in board.models if x.model_name == name)
        assert m.clustered_tasks == 1
        assert m.macro_mean == pytest.approx(point)
        # the leaderboard sorts scores within a cluster, compare keeps item order: same
        # resampling scheme, so the intervals agree up to the order inside clusters
        assert m.ci_lower == pytest.approx(lo, abs=0.02)
        assert m.ci_upper == pytest.approx(hi, abs=0.02)
    plain = generate_leaderboard(_records(with_clusters=False))
    wide = next(x for x in board.models if x.model_name == "a")
    narrow = next(x for x in plain.models if x.model_name == "a")
    assert wide.ci_upper - wide.ci_lower > narrow.ci_upper - narrow.ci_lower
    assert "whole clusters" in board.to_markdown()


def test_leaderboard_tie_group_agrees_with_clustered_compare() -> None:
    recs = _records(n_clusters=40, size=8, seed=4)
    by_model: dict[str, dict[object, float]] = {"a": {}, "b": {}}
    clusters: dict[object, object] = {}
    for r in recs:
        key = f"t::{r.example_id}"
        by_model[r.model][key] = r.score
        clusters[key] = ("t", r.cluster_id)
    pair = compare_pairs(by_model, [("a", "b")], with_power=False, clusters=clusters)[0]
    item = compare_pairs(by_model, [("a", "b")], with_power=False)[0]
    board = generate_leaderboard(recs)
    ranked = sorted(board.models, key=lambda m: (-m.macro_mean, m.model_name))
    groups = {m.model_name: m.tie_group for m in ranked}
    top, bottom = ranked[0].model_name, ranked[1].model_name
    assert (groups[bottom] != groups[top]) == pair.resolved
    # clustering matters on this data: it widens the p-value
    assert pair.rand_p >= item.rand_p


def test_leaderboard_bradley_terry_column() -> None:
    board = generate_leaderboard(_records(), bradley_terry=True, bt_resamples=30)
    assert all(m.bt_rating is not None for m in board.models)
    text = board.to_markdown()
    assert "Bradley-Terry [95% CI]" in text
    top = max(board.models, key=lambda m: m.bt_rating or 0.0)
    assert top.model_name == "a"
    plain = generate_leaderboard(_records())
    assert "Bradley-Terry" not in plain.to_markdown()


# --- CLI and HELM clusters ---------------------------------------------------------------------


def test_rank_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from evalkit.cli import main

    scores = _item_scores(n=60, models=3)
    path = tmp_path / "results.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for model, items in scores.items():
            for k, v in items.items():
                f.write(
                    json.dumps(
                        {
                            "task": "t",
                            "model": model,
                            "example_id": k,
                            "score": v,
                            "cluster_id": k[:2],
                        }
                    )
                    + "\n"
                )
    assert main(["rank", str(path), "--resamples", "20", "--out", str(tmp_path / "r.md")]) == 0
    out = capsys.readouterr().out
    assert "Bradley-Terry ranking of 3 models" in out and "whole clusters resampled" in out
    assert (tmp_path / "r.md").read_text().startswith("# Bradley-Terry")
    assert main(["rank", str(path), "--resamples", "10", "--ignore-clusters"]) == 0
    assert "items resampled" in capsys.readouterr().out


def test_compact_clusters_hashes_passages() -> None:
    def inst(i: str, text: str, split: str = "valid") -> dict[str, object]:
        return {"id": i, "split": split, "input": {"text": text}, "references": []}

    got = compact_clusters(
        [
            inst("q1", "Passage: P\nQuestion: who?"),
            inst("q2", "Passage: P\nQuestion: where?"),
            inst("q3", "Passage: Other\nQuestion: why?"),
            inst("q4", "no passage here"),
            inst("q5", "Passage: P\nQuestion: x", split="train"),
        ],
        "valid",
    )
    assert set(got) == {"q1", "q2", "q3"}
    assert got["q1"] == got["q2"] != got["q3"]
