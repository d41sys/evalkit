from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from evalkit.aggregate import (
    bootstrap_mean_ci,
    cluster_randomization_test_p,
    compare_pairs,
    minimum_detectable_effect,
    minimum_detectable_effect_binary,
    paired_comparison,
    randomization_test_p,
    required_sample_size,
    required_sample_size_binary,
)
from evalkit.cli import main
from evalkit.clustered import (
    cluster_bootstrap_ci,
    cluster_stats,
    cluster_sums,
    clustered_se,
    design_effect,
    effective_cluster_size,
    encode_clusters,
    estimate_icc,
    naive_se,
)
from evalkit.models import NoisyModel, OracleModel
from evalkit.results import load_results, merge_clusters
from evalkit.runner import EvalRecord, generate_leaderboard, run
from evalkit.samples import pass_hat_k, pass_hat_k_item
from evalkit.spec import SpecError, TaskSpec


def _clustered_data(
    rho: float, clusters: int, size: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(clusters)
    e = rng.standard_normal((clusters, size))
    y = 0.5 + 0.25 * (math.sqrt(rho) * z[:, None] + math.sqrt(1.0 - rho) * e)
    return y.ravel(), np.repeat(np.arange(clusters), size)


# ---------------------------------------------------------------- clustered SE (Miller 2024)


def test_clustered_se_matches_miller_double_sum() -> None:
    values = np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    labels = ["p", "p", "p", "q", "q", "r", "r", "r", "r"]
    codes = encode_clusters(labels)
    n = values.size
    s_bar = values.mean()
    cross = 0.0
    for c in set(labels):
        idx = [i for i, label in enumerate(labels) if label == c]
        for i in idx:
            for j in idx:
                if i != j:
                    cross += (values[i] - s_bar) * (values[j] - s_bar)
    expected = math.sqrt(values.var(ddof=1) / n + cross / n**2)
    assert clustered_se(values, codes) == pytest.approx(expected, rel=1e-12)


def test_clustered_se_equals_naive_for_singletons() -> None:
    rng = np.random.default_rng(1)
    x = rng.random(40)
    assert clustered_se(x, np.arange(40)) == pytest.approx(naive_se(x), rel=1e-12)


def test_clustered_se_grows_with_intra_cluster_correlation() -> None:
    y, codes = _clustered_data(0.5, 60, 5, seed=2)
    stats = cluster_stats(y, codes)
    assert stats.se_ratio > 1.4  # theory sqrt(1 + 4 * 0.5) = 1.73
    assert stats.n_clusters == 60
    assert stats.deff == pytest.approx(1.0 + 4.0 * stats.icc)


def test_clustered_se_needs_two_clusters_and_matching_lengths() -> None:
    with pytest.raises(ValueError):
        clustered_se([1.0, 0.0], np.array([0, 0]))
    with pytest.raises(ValueError):
        clustered_se([1.0, 0.0], np.array([0, 1, 1]))


def test_clustered_se_is_unbiased_in_a_simulation() -> None:
    # true SD of the mean of 40 clusters x 5 items at rho = 0.3: 0.25 sqrt(DEFF / n)
    truth = 0.25 * math.sqrt((1 + 4 * 0.3) / 200)
    means, ses = [], []
    for seed in range(400):
        y, codes = _clustered_data(0.3, 40, 5, seed)
        means.append(float(y.mean()))
        ses.append(clustered_se(y, codes))
    assert float(np.std(means, ddof=1)) == pytest.approx(truth, rel=0.1)
    assert float(np.mean(ses)) == pytest.approx(truth, rel=0.1)


# ------------------------------------------------------------------ ICC and design effect


def test_icc_recovers_the_simulated_value() -> None:
    y, codes = _clustered_data(0.3, 400, 5, seed=3)
    assert estimate_icc(y, codes) == pytest.approx(0.3, abs=0.05)
    y0, c0 = _clustered_data(0.0, 400, 5, seed=4)
    assert estimate_icc(y0, c0) < 0.06


def test_icc_degenerate_cases_are_zero() -> None:
    assert estimate_icc([1.0, 0.0, 1.0], np.arange(3)) == 0.0
    assert estimate_icc([1.0, 0.0, 1.0], np.zeros(3, dtype=np.int64)) == 0.0
    assert estimate_icc([0.5] * 6, np.repeat(np.arange(3), 2)) == 0.0


def test_design_effect_formula_and_effective_cluster_size() -> None:
    assert design_effect(5, 0.1) == pytest.approx(1.4)
    assert design_effect(1, 0.9) == 1.0
    assert design_effect(10, -0.2) == 1.0  # clipped, never below 1
    equal = np.repeat(np.arange(4), 5)
    assert effective_cluster_size(equal) == pytest.approx(5.0)
    unequal = np.array([0, 0, 0, 0, 1, 2])  # sizes 4, 1, 1: (16 + 1 + 1) / 6
    assert effective_cluster_size(unequal) == pytest.approx(3.0)


def test_power_functions_scale_with_the_design_effect() -> None:
    assert required_sample_size(0.25, 0.1) == 50
    assert required_sample_size(0.25, 0.1, deff=1.4) == 69  # ceil(1.4 * 49.06)
    assert required_sample_size(0.25, 0.1, deff=1.0) == required_sample_size(0.25, 0.1)
    assert minimum_detectable_effect(0.25, 100, deff=2.0) == pytest.approx(
        math.sqrt(2.0) * minimum_detectable_effect(0.25, 100)
    )
    base = required_sample_size_binary(0.3, 0.1)
    assert required_sample_size_binary(0.3, 0.1, deff=2.0) == 2 * base
    assert required_sample_size_binary(0.3, 0.1, deff=1.0) == base
    wide = minimum_detectable_effect_binary(0.3, 400, deff=2.0)
    assert wide == pytest.approx(minimum_detectable_effect_binary(0.3, 200))
    assert wide > minimum_detectable_effect_binary(0.3, 400)


# ------------------------------------------------------------------------- cluster bootstrap


def test_cluster_bootstrap_with_singletons_matches_the_item_bootstrap() -> None:
    rng = np.random.default_rng(5)
    x = (rng.random(300) < 0.6).astype(float)
    mean, lo, hi = cluster_bootstrap_ci(x, np.arange(300), num_resamples=4000, seed=1)
    _, ilo, ihi = bootstrap_mean_ci(x.tolist(), num_resamples=4000, seed=1, method="percentile")
    assert mean == pytest.approx(x.mean())
    assert lo == pytest.approx(ilo, abs=0.01)
    assert hi == pytest.approx(ihi, abs=0.01)


def test_cluster_bootstrap_is_wider_than_the_item_bootstrap_on_clustered_data() -> None:
    y, codes = _clustered_data(0.5, 40, 5, seed=6)
    _, lo, hi = cluster_bootstrap_ci(y, codes, num_resamples=3000, seed=0)
    _, ilo, ihi = bootstrap_mean_ci(y.tolist(), num_resamples=3000, seed=0, method="percentile")
    assert (hi - lo) > 1.3 * (ihi - ilo)
    assert lo < y.mean() < hi


def test_cluster_bootstrap_handles_unequal_sizes_and_is_seeded() -> None:
    values = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    codes = np.array([0, 0, 0, 0, 1, 2])
    a = cluster_bootstrap_ci(values, codes, num_resamples=500, seed=3)
    assert a == cluster_bootstrap_ci(values, codes, num_resamples=500, seed=3)
    assert 0.0 <= a[1] <= a[0] <= a[2] <= 1.0
    with pytest.raises(ValueError):
        cluster_bootstrap_ci(values, np.zeros(6, dtype=np.int64))
    assert cluster_bootstrap_ci(values, codes, num_resamples=0) == (
        pytest.approx(4 / 6),
        pytest.approx(4 / 6),
        pytest.approx(4 / 6),
    )


def test_cluster_sums() -> None:
    sums, sizes = cluster_sums([1.0, 2.0, 3.0, 4.0], np.array([0, 1, 0, 1]))
    assert sums.tolist() == [4.0, 6.0]
    assert sizes.tolist() == [2.0, 2.0]


# ------------------------------------------------------------ paired tests and compare_pairs


def test_cluster_randomization_test_is_the_test_on_cluster_sums() -> None:
    diffs = [1, 1, 1, -1, 0, 1, 1, 1, 0, 1, -1, 1]
    labels = [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 4]
    p = cluster_randomization_test_p(diffs, labels)
    sums = [3, -1, 3, 0, 1]
    assert p == randomization_test_p(sums)
    # one cluster per item: the item-level test
    assert cluster_randomization_test_p(diffs, list(range(12))) == randomization_test_p(diffs)
    # whole-cluster flips are less extreme evidence than item flips on clustered differences
    assert p > randomization_test_p(diffs)
    with pytest.raises(ValueError):
        cluster_randomization_test_p(diffs, [0, 1])


def test_paired_comparison_clusters() -> None:
    rng = np.random.default_rng(7)
    shift = np.repeat(rng.standard_normal(30) * 0.3, 5)
    a = shift + rng.standard_normal(150) * 0.1 + 0.05
    b = np.zeros(150)
    codes = np.repeat(np.arange(30), 5)
    plain = paired_comparison(a, b, num_resamples=2000)
    clustered = paired_comparison(a, b, num_resamples=2000, clusters=codes.tolist())
    assert plain.clustering is None
    assert clustered.ci_method == "cluster-bootstrap"
    assert clustered.clustering is not None
    assert clustered.clustering.se_ratio > 2.0
    assert clustered.diff == pytest.approx(plain.diff)
    assert (clustered.diff_ci_hi - clustered.diff_ci_lo) > 2.0 * (
        plain.diff_ci_hi - plain.diff_ci_lo
    )
    one = paired_comparison(a, b, num_resamples=200, clusters=[0] * 150)
    assert one.clustering is None and one.ci_method != "cluster-bootstrap"
    with pytest.raises(ValueError):
        paired_comparison(a, b, clusters=[0, 1])


def _clustered_scores(n_clusters: int = 30, size: int = 5) -> dict[str, dict[object, float]]:
    rng = np.random.default_rng(8)
    shift = np.repeat(rng.standard_normal(n_clusters) * 0.3, size)
    keys = list(range(n_clusters * size))
    a = shift + rng.standard_normal(keys.__len__()) * 0.1 + 0.1
    return {
        "a": dict(zip(keys, a.tolist(), strict=True)),
        "b": dict.fromkeys(keys, 0.0),
    }


def test_compare_pairs_with_clusters_inflates_power_and_uses_cluster_tests() -> None:
    scores = _clustered_scores()
    clusters = {k: k // 5 for k in scores["a"]}
    plain = compare_pairs(scores, [("a", "b")], num_resamples=500)[0]
    clustered = compare_pairs(scores, [("a", "b")], num_resamples=500, clusters=clusters)[0]
    assert plain.clustering is None
    assert clustered.clustering is not None and clustered.ci_method == "cluster-bootstrap"
    assert clustered.clustering.deff > 2.0
    assert clustered.mde == pytest.approx(
        minimum_detectable_effect(clustered.sd_diff, clustered.n, deff=clustered.clustering.deff)
    )
    assert clustered.mde > 1.5 * plain.mde
    assert clustered.n_needed is not None and plain.n_needed is not None
    assert clustered.n_needed > 1.5 * plain.n_needed
    assert clustered.rand_p == cluster_randomization_test_p(
        [scores["a"][k] - scores["b"][k] for k in sorted(scores["a"], key=repr)],
        [clusters[k] for k in sorted(scores["a"], key=repr)],
        num_draws=10000,
    )
    assert clustered.rand_p > plain.rand_p


def test_compare_pairs_items_without_a_cluster_are_singletons() -> None:
    scores = _clustered_scores(10, 3)
    only_first = {k: "c" for k in range(3)}
    row = compare_pairs(scores, [("a", "b")], num_resamples=200, clusters=only_first)[0]
    assert row.clustering is not None
    assert row.clustering.n_clusters == 1 + 27
    all_one = compare_pairs(
        scores, [("a", "b")], num_resamples=200, clusters=dict.fromkeys(scores["a"], "c")
    )[0]
    assert all_one.clustering is None and all_one.ci_method != "cluster-bootstrap"


# ------------------------------------------------------------------------------ pass^k


def test_pass_hat_k_item_values() -> None:
    assert pass_hat_k_item(4, 4, 4) == 1.0
    assert pass_hat_k_item(3, 4, 4) == 0.0
    assert pass_hat_k_item(3, 4, 2) == pytest.approx(3 / 6)
    assert pass_hat_k_item(2, 5, 1) == pytest.approx(0.4)
    with pytest.raises(ValueError):
        pass_hat_k_item(1, 2, 3)
    with pytest.raises(ValueError):
        pass_hat_k_item(1, 2, 0)


def test_pass_hat_k_is_unbiased_for_p_to_the_k() -> None:
    rng = np.random.default_rng(9)
    p, k, n = 0.7, 3, 6
    est = [pass_hat_k_item(int(rng.binomial(n, p)), n, k) for _ in range(40000)]
    assert float(np.mean(est)) == pytest.approx(p**k, abs=0.01)


def test_pass_hat_k_maps_items_and_rejects_non_binary() -> None:
    got = pass_hat_k({"x": [1.0, 1.0, 0.0], "y": [1.0, 1.0, 1.0]}, 2)
    assert got == {"x": pytest.approx(1 / 3), "y": 1.0}
    with pytest.raises(ValueError):
        pass_hat_k({"x": [0.5, 1.0]}, 2)


# ------------------------------------------------------------ files, runner and the CLI


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _cluster_rows(n_clusters: int = 12, size: int = 4) -> list[dict[str, object]]:
    rng = np.random.default_rng(10)
    rows: list[dict[str, object]] = []
    for c in range(n_clusters):
        base = rng.random()
        for i in range(size):
            ex = f"e{c}_{i}"
            for model, bump in (("A", 0.25), ("B", 0.0)):
                score = float(rng.random() < min(0.95, base + bump))
                rows.append(
                    {
                        "task": "t",
                        "model": model,
                        "example_id": ex,
                        "score": score,
                        "cluster_id": f"doc{c}",
                    }
                )
    return rows


def test_load_results_samples_clusters_and_conflicts(tmp_path: Path) -> None:
    rows = [
        {"task": "t", "model": "m", "example_id": "e1", "score": 1.0, "cluster_id": "d1"},
        {"task": "t", "model": "m", "example_id": "e1", "score": 0.0, "cluster_id": "d1"},
        {"task": "t", "model": "m", "example_id": "e2", "score": 1.0},
    ]
    p = tmp_path / "r.jsonl"
    _write_results(p, rows)
    table = load_results(p)
    assert table.item_scores("m") == {("t", "e1"): 0.5, ("t", "e2"): 1.0}
    assert table.clusters == {("t", "e1"): ("t", "d1")}
    assert table.has_clusters and table.sample_counts() == (1, 2)
    rows.append({"task": "t", "model": "n", "example_id": "e1", "score": 1.0, "cluster_id": "x"})
    _write_results(p, rows)
    with pytest.raises(ValueError, match="two cluster ids"):
        load_results(p)
    other = tmp_path / "o.jsonl"
    _write_results(other, rows[:1])
    q = tmp_path / "q.jsonl"
    _write_results(q, [{**rows[0], "cluster_id": "other"}])
    with pytest.raises(ValueError, match="different cluster ids"):
        merge_clusters(load_results(other), load_results(q))


def test_cli_compare_pairwise_prints_naive_vs_clustered(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "results.jsonl"
    _write_results(p, _cluster_rows())
    assert main(["compare", str(p), "--a", "A", "--b", "B"]) == 0
    out = capsys.readouterr().out
    assert "naive SE" in out and "clustered SE" in out and "SE ratio" in out
    assert "| ALL | 48 | 12 |" in out
    assert "Miller (2024" in out


def test_cli_compare_without_clusters_keeps_the_old_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "results.jsonl"
    _write_results(p, [{k: v for k, v in r.items() if k != "cluster_id"} for r in _cluster_rows()])
    assert main(["compare", str(p), "--a", "A", "--b", "B"]) == 0
    out = capsys.readouterr().out
    assert "95% CI (paired bootstrap)" in out and "clustered" not in out


def test_cli_all_pairs_clustered_columns_and_cluster_conflict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "results.jsonl"
    _write_results(p, _cluster_rows())
    assert main(["compare", str(p), "--all-pairs"]) == 0
    out = capsys.readouterr().out
    assert "cluster randomisation p" in out and "DEFF" in out and "cluster bootstrap" in out
    assert "cluster sign-flip test" in out
    rows = _cluster_rows()
    rows[1]["cluster_id"] = "somewhere-else"
    _write_results(p, rows)
    assert main(["compare", str(p), "--all-pairs"]) == 1
    assert "two cluster ids" in capsys.readouterr().err


def test_cli_compare_prints_pass_k_for_multi_sample_results(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows: list[dict[str, object]] = []
    for ex in range(10):
        for model, wins in (("A", 3), ("B", 1)):
            for s in range(3):
                rows.append(
                    {
                        "task": "t",
                        "model": model,
                        "example_id": f"e{ex}",
                        "score": float(s < wins),
                        "sample": s,
                    }
                )
    p = tmp_path / "results.jsonl"
    _write_results(p, rows)
    assert main(["compare", str(p), "--a", "A", "--b", "B"]) == 0
    out = capsys.readouterr().out
    assert "pass^3" in out
    assert "| A | 10 | 1.000 | 1.000 |" in out  # always right
    assert "| B | 10 | 0.333 | 0.000 |" in out  # a third of samples right, never all three
    assert main(["compare", str(p), "--a", "A", "--b", "B", "--pass-k", "4"]) == 1


# ------------------------------------------------------------------------ spec and runner


def _spec(tmp_path: Path, rows: list[dict[str, object]], extra: str = "") -> TaskSpec:
    data = tmp_path / "data.jsonl"
    data.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(
        "name: t\ntype: generation\ndataset: data.jsonl\n"
        'prompt_template: "Q: {question}\\nA:"\nmetrics:\n  - exact_match\n' + extra,
        encoding="utf-8",
    )
    return TaskSpec.from_yaml(spec_file)


def test_spec_cluster_field_and_default(tmp_path: Path) -> None:
    rows = [
        {"id": f"q{i}", "question": "x", "target": "1", "passage": f"p{i // 2}", "cluster_id": "z"}
        for i in range(4)
    ]
    by_field = _spec(tmp_path, rows, "cluster_field: passage\n")
    assert [by_field.cluster_of(r) for r in rows] == ["p0", "p0", "p1", "p1"]
    default = _spec(tmp_path, rows)
    assert default.cluster_of(rows[0]) == "z"
    assert default.cluster_of({"id": "q"}) is None
    with pytest.raises(SpecError, match="cluster_field"):
        _spec(tmp_path, [{"id": "q", "question": "x", "target": "1"}], "cluster_field: passage\n")


def test_runner_writes_cluster_ids_and_resumes_samples(tmp_path: Path) -> None:
    rows = [
        {"id": f"q{i}", "question": f"{i}+{i}", "target": str(2 * i), "cluster_id": f"d{i // 3}"}
        for i in range(6)
    ]
    spec = _spec(tmp_path, rows)
    models = [OracleModel(), NoisyModel(noise_rate=0.5, seed=1)]
    out = tmp_path / "out"
    first = run([spec], models, out, max_workers=2)
    assert first.total_evaluated == 12
    stored = [json.loads(x) for x in (out / "results.jsonl").read_text().splitlines()]
    assert {r["cluster_id"] for r in stored} == {"d0", "d1"}
    assert all("sample" not in r for r in stored)  # a plain run writes the old row format
    more = run([spec], models, out, max_workers=2, samples=3)
    assert more.total_evaluated == 24 and more.total_skipped == 12
    table = load_results(out / "results.jsonl")
    assert table.sample_counts() == (3, 3)
    assert run([spec], models, out, max_workers=2, samples=3).total_evaluated == 0
    noisy = table.samples[models[1].name]
    assert any(len(set(v)) > 1 for v in noisy.values())  # samples vary for a stochastic model
    assert all(len(set(v)) == 1 for v in table.samples["oracle"].values())
    with pytest.raises(ValueError):
        run([spec], models, out, samples=0)


def test_eval_record_round_trip_keeps_cluster_and_sample() -> None:
    rec = EvalRecord("t", "m", "e", 1.0, {}, "", [], 0.5, 1, cluster_id="d", sample=2)
    assert EvalRecord.from_dict(rec.to_dict()) == rec
    plain = EvalRecord("t", "m", "e", 1.0, {}, "", [], 0.5, 1)
    assert "cluster_id" not in plain.to_dict() and "sample" not in plain.to_dict()


def test_leaderboard_averages_samples_per_item() -> None:
    recs = [
        EvalRecord("t", m, f"e{i}", float(s < k), {}, "", [], 0.5, int(s < k), sample=s)
        for m, k in (("hi", 3), ("lo", 1))
        for i in range(10)
        for s in range(3)
    ]
    board = generate_leaderboard(recs)
    by_name = {m.model_name: m for m in board.models}
    assert by_name["hi"].macro_mean == pytest.approx(1.0)
    assert by_name["lo"].macro_mean == pytest.approx(1 / 3)
    assert board.models[0].model_name == "hi"
