from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from evalkit.cli import main
from evalkit.clustered import estimate_icc
from evalkit.statscheck import Rate
from evalkit.statscheck_cluster import (
    ClusterCheckConfig,
    ClusterJob,
    ClusterPowerJob,
    ClusterScenario,
    draw_clustered,
    evaluate_claims,
    plan_cluster,
    render_cluster_markdown,
    run_cluster_cell,
    run_cluster_check,
    run_cluster_power,
)

TINY = ClusterCheckConfig(
    reps=6, power_reps=6, resamples=40, draws=60, iccs=(0.0, 0.3), counts=(20,), workers=1
)


@pytest.mark.parametrize("design", ["mean", "paired"])
@pytest.mark.parametrize("kind", ["binary", "continuous"])
@pytest.mark.parametrize("rho", [0.0, 0.1, 0.3])
def test_generators_hit_the_stated_icc_and_truth(design: str, kind: str, rho: float) -> None:
    sc = ClusterScenario(design, kind, rho, 400, "equal")
    a, b, codes = draw_clustered(sc, np.random.default_rng(1))
    d = a - b
    assert codes.size == 2000
    assert abs(d.mean() - sc.truth) < 5 * d.std() * math.sqrt(1 + 4 * rho) / math.sqrt(d.size)
    assert estimate_icc(d, codes) == pytest.approx(rho, abs=0.05)
    if kind == "binary":
        assert set(np.unique(np.concatenate((a, b)))) <= {0.0, 1.0}


def test_unequal_sizes_average_five_and_vary() -> None:
    sc = ClusterScenario("mean", "continuous", 0.1, 500, "unequal")
    _, _, codes = draw_clustered(sc, np.random.default_rng(2))
    sizes = np.bincount(codes)
    assert sizes.mean() == pytest.approx(5.0, abs=0.3) and sizes.min() >= 1 and sizes.max() > 9
    assert (sizes**2).sum() / sizes.sum() == pytest.approx(5.8, abs=0.4)


def test_scenario_validation_and_theory_ratio() -> None:
    with pytest.raises(ValueError):
        ClusterScenario("nope", "binary", 0.1, 20, "equal")
    with pytest.raises(ValueError):
        ClusterScenario("mean", "binary", 1.0, 20, "equal")
    with pytest.raises(ValueError):
        ClusterScenario("mean", "binary", 0.1, 1, "equal")
    assert ClusterScenario("mean", "binary", 0.3, 20, "equal").theory_ratio == pytest.approx(
        math.sqrt(2.2)
    )


def test_plan_matches_the_protocol_grid() -> None:
    cells, power = plan_cluster(ClusterCheckConfig())
    assert len(cells) == 72 and len(power) == 6
    assert len({j.cell_id for j in [*cells, *power]}) == 78
    assert sum(1 for j in cells if j.scenario.clusters >= 50) == 48
    assert sum(1 for j in cells if j.scenario.icc > 0.0) == 48
    assert plan_cluster(ClusterCheckConfig()) == (cells, power)


def test_power_job_sample_sizes() -> None:
    naive = ClusterPowerJob(0, 0.1, "naive", 1, 0, 10, 10)
    deff = ClusterPowerJob(0, 0.1, "deff", 1, 0, 10, 10)
    assert naive.n_items == 50 and deff.n_items == 70  # ceil(1.4 * 49.06) = 69 -> 14 clusters
    assert ClusterPowerJob(0, 0.3, "deff", 1, 0, 10, 10).n_items == 110  # ceil(2.2 * 49.06)


def test_naive_interval_undercovers_and_cluster_interval_does_not() -> None:
    sc = ClusterScenario("mean", "continuous", 0.3, 50, "equal")
    r = run_cluster_cell(ClusterJob(0, sc, 300, 1, 300, 100))
    assert r.coverage["naive"].value < 0.88  # theory: P(|Z| < 1.96 / 1.48) = 0.81
    assert r.coverage["item_bootstrap"].value < 0.9
    assert r.coverage["cluster_normal"].value > 0.91
    assert r.coverage["cluster_bootstrap"].value > 0.91
    assert r.se_ratio == pytest.approx(sc.theory_ratio, rel=0.1)
    assert r.p_item is None and r.p_cluster is None


def test_item_sign_flip_is_anticonservative_and_cluster_flip_valid() -> None:
    sc = ClusterScenario("paired", "continuous", 0.3, 50, "equal")
    r = run_cluster_cell(ClusterJob(0, sc, 400, 2, 50, 300))
    assert r.p_item is not None and r.p_cluster is not None
    assert r.p_item.value > 0.12  # theory: 2 * (1 - Phi(1.96 / 1.48)) = 0.19
    assert 0.02 < r.p_cluster.value < 0.09


def test_cell_is_deterministic_and_seed_sensitive() -> None:
    sc = ClusterScenario("paired", "binary", 0.1, 20, "unequal")
    job = ClusterJob(3, sc, 8, 0, 30, 50)
    assert run_cluster_cell(job) == run_cluster_cell(job)
    assert run_cluster_cell(job) != run_cluster_cell(ClusterJob(3, sc, 8, 1, 30, 50))


def test_power_cell_runs() -> None:
    r = run_cluster_power(ClusterPowerJob(0, 0.1, "deff", 12, 0, 40, 100))
    assert 0.0 <= r.cluster_flip.value <= 1.0 and r.cluster_flip.trials == 12


def test_run_check_report_and_pool_match_serial() -> None:
    serial = run_cluster_check(TINY)
    pooled = run_cluster_check(ClusterCheckConfig(**{**TINY.__dict__, "workers": 2}))
    assert pooled.cells == serial.cells and pooled.power == serial.power
    assert len(serial.cells) == 2 * 2 * 2 * 1 * 2 and len(serial.power) == 4
    text = render_cluster_markdown(serial)
    for header in (
        "### Coverage of the true value, design `mean`",
        "### Coverage of the true value, design `paired`",
        "### Type-I error at alpha = 0.05, paired design",
        "### Power with the design effect",
        "### Claims under the pre-registered rules",
        "### Every flagged cell",
    ):
        assert header in text
    claims = evaluate_claims(serial)
    assert any(c.startswith("Claim 1") for c in claims)
    assert any(c.startswith("Claim 4") for c in claims)
    assert not any(c.startswith("Claim 2") for c in claims)  # no cell with 50+ clusters


def test_claims_follow_the_decision_rules() -> None:
    base = run_cluster_check(
        ClusterCheckConfig(
            reps=4, power_reps=4, resamples=30, draws=50, iccs=(0.3,), counts=(50,), workers=1
        )
    )
    cells = []
    for r in base.cells:
        bad = {
            **r.coverage,
            "cluster_normal": Rate(9000, 10000),
            "cluster_bootstrap": Rate(9350, 10000),
        }
        cells.append(type(r)(r.job, bad, r.se_ratio, r.icc_hat, r.p_item, r.p_cluster))
    report = type(base)(base.config, cells, base.power)
    claims = [c for c in evaluate_claims(report) if c.startswith("Claim 2")]
    assert any("clustered-SE normal: not supported" in c for c in claims)  # 0.90 < 0.93
    assert any("cluster bootstrap: approximately supported" in c for c in claims)  # 0.935 >= 0.93


def test_cli_stats_check_only_clustered(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "c.md"
    code = main(
        [
            "stats-check",
            "--only-clustered",
            "--cluster-iccs",
            "0.1",
            "--cluster-counts",
            "20",
            "--cluster-reps",
            "4",
            "--cluster-power-reps",
            "4",
            "--cluster-resamples",
            "30",
            "--draws",
            "50",
            "--workers",
            "1",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "Clustered data" in text and "Type-I error at alpha = 0.05 (H0" not in text
    assert "Wall time" in capsys.readouterr().out
