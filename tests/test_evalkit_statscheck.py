from __future__ import annotations

import dataclasses
import math
from pathlib import Path

import numpy as np
import pytest

from evalkit.aggregate import (
    minimum_detectable_effect,
    minimum_detectable_effect_binary,
    paired_binary_power_exact,
    required_sample_size,
    required_sample_size_binary,
)
from evalkit.cli import main
from evalkit.statscheck import (
    CellJob,
    FwerJob,
    Rate,
    Scenario,
    StatsCheckConfig,
    classify_coverage,
    classify_error_rate,
    classify_power,
    collect_findings,
    mde_scenario,
    n_star,
    plan,
    render_markdown,
    run_cell,
    run_fwer,
    run_stats_check,
    simulate_pairs,
    wilson_interval,
)

TINY = StatsCheckConfig(
    reps_h0=8,
    reps_power=6,
    reps_fwer=4,
    resamples=50,
    draws=100,
    ns=(20,),
    ties=(0.5,),
    fwer_ns=(20,),
    fixed_effects=(0.2,),
)


def test_wilson_interval_known_values() -> None:
    lo, hi = wilson_interval(50, 100, level=0.95)
    assert lo == pytest.approx(0.4038, abs=1e-3)
    assert hi == pytest.approx(0.5962, abs=1e-3)
    assert wilson_interval(0, 100)[0] == pytest.approx(0.0)
    assert wilson_interval(100, 100)[1] == pytest.approx(1.0)
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_decision_rules() -> None:
    n = 10000
    assert classify_error_rate(Rate(500, n)) == "ok"
    assert classify_error_rate(Rate(620, n)) == "anti-conservative"
    assert classify_error_rate(Rate(200, n)) == "conservative"
    assert classify_error_rate(Rate(420, n)) == "ok"  # between 0.04 and 0.05
    assert classify_coverage(Rate(9500, n)) == "ok"
    assert classify_coverage(Rate(9300, n)) == "undercovers"
    assert classify_coverage(Rate(9800, n)) == "overcovers"
    assert classify_power(Rate(8000, n)) == "ok"
    assert classify_power(Rate(7500, n)) == "optimistic"
    assert classify_power(Rate(9000, n)) == "pessimistic"


@pytest.mark.parametrize("kind", ["binary", "continuous", "skewed"])
@pytest.mark.parametrize("effect", [0.0, 0.15])
def test_simulation_matches_stated_moments(kind: str, effect: float) -> None:
    sc = Scenario(kind, 400, 0.4, effect)
    a, b = simulate_pairs(sc, 400, np.random.default_rng(3))
    d = a - b
    se = sc.true_sd / math.sqrt(d.size)
    assert abs(d.mean() - effect) < 5 * se
    assert d.std() == pytest.approx(sc.true_sd, rel=0.03)
    assert (d == 0).mean() == pytest.approx(0.4, abs=0.02)
    if kind == "binary":
        assert set(np.unique(np.concatenate((a.ravel(), b.ravel())))) == {0.0, 1.0}


def test_skewed_differences_are_asymmetric_under_h0() -> None:
    a, b = simulate_pairs(Scenario("skewed", 500, 0.0, 0.0), 200, np.random.default_rng(0))
    d = (a - b).ravel()
    assert abs(d.mean()) < 0.01
    assert ((d - d.mean()) ** 3).mean() / d.std() ** 3 > 1.5


def test_scenario_validation() -> None:
    with pytest.raises(ValueError):
        Scenario("nope", 10, 0.0, 0.0)
    with pytest.raises(ValueError):
        Scenario("binary", 10, 0.8, 0.5)  # effect beyond 1 - tie rate
    with pytest.raises(ValueError):
        Scenario("binary", 10, 1.0, 0.0)


@pytest.mark.parametrize("kind", ["continuous", "skewed"])
@pytest.mark.parametrize("n", [20, 50, 115, 240])
@pytest.mark.parametrize("tie", [0.0, 0.5])
def test_mde_scenario_is_formula_fixed_point(kind: str, n: int, tie: float) -> None:
    sc = mde_scenario(kind, n, tie)
    assert sc is not None
    assert minimum_detectable_effect(sc.true_sd, n) == pytest.approx(sc.effect, rel=1e-9)
    assert abs(required_sample_size(sc.true_sd, sc.effect) - n) <= 1


@pytest.mark.parametrize("n", [20, 50, 115, 240])
@pytest.mark.parametrize("tie", [0.0, 0.5])
def test_binary_mde_scenario_is_exact_power_fixed_point(n: int, tie: float) -> None:
    sc = mde_scenario("binary", n, tie)
    assert sc is not None
    psi = 1.0 - tie
    assert minimum_detectable_effect_binary(psi, n) == pytest.approx(sc.effect, rel=1e-9)
    assert paired_binary_power_exact(n, sc.effect, psi) == pytest.approx(0.8, abs=1e-6)
    star = n_star("binary", tie, sc.effect)
    assert star == required_sample_size_binary(psi, sc.effect)
    assert star <= n  # first crossing: exact power's sawtooth can reach 0.8 a pair or two early
    assert paired_binary_power_exact(star, sc.effect, psi) >= 0.8


def test_mde_scenario_none_when_unattainable() -> None:
    assert mde_scenario("binary", 20, 0.8) is None  # even d = psi = 0.2 is not detectable
    assert mde_scenario("continuous", 20, 0.8) is None  # no finite fixed point


def test_run_cell_reports_skew_warning_rate() -> None:
    skewed = run_cell(CellJob(0, Scenario("skewed", 20, 0.0, 0.0), 60, 0, 50, 100, "h0"))
    sym = run_cell(CellJob(0, Scenario("continuous", 115, 0.0, 0.0), 60, 0, 50, 100, "h0"))
    assert skewed.skew_warn.value > 0.5
    assert sym.skew_warn.value < 0.2


def test_ci_method_reaches_the_cell_runner() -> None:
    def cell(method: str) -> CellJob:
        return CellJob(0, Scenario("skewed", 30, 0.0, 0.0), 40, 0, 200, 100, "h0", method)

    assert run_cell(cell("bca")).mean_ci_width != run_cell(cell("percentile")).mean_ci_width
    assert run_cell(cell("bca")) == run_cell(cell("bca"))
    assert StatsCheckConfig().ci_method == "auto"


def test_run_cell_is_deterministic_and_seed_sensitive() -> None:
    def job(seed: int) -> CellJob:
        return CellJob(0, Scenario("binary", 20, 0.5, 0.0), 12, seed, 50, 100, "h0")

    r1, r2, r3 = run_cell(job(1)), run_cell(job(1)), run_cell(job(2))
    assert r1 == r2
    assert r1.job.seed != r3.job.seed
    assert r1.coverage.trials == 12


def test_h0_rejection_is_rare_and_coverage_high_on_a_small_run() -> None:
    job = CellJob(0, Scenario("continuous", 50, 0.0, 0.0), 150, 0, 200, 500, "h0")
    r = run_cell(job)
    assert r.rand_reject.value < 0.15
    assert r.sign_reject.value < 0.15
    assert r.coverage.value > 0.85
    assert r.predicted_power is None


def test_power_cell_near_target_on_a_small_run() -> None:
    sc = mde_scenario("continuous", 50, 0.0)
    assert sc is not None
    r = run_cell(CellJob(0, sc, 200, 0, 200, 500, "mde"))
    assert r.predicted_power == 0.8
    assert 0.6 < r.rand_reject.value < 0.95


@pytest.mark.parametrize("design", ["independent", "all-pairs"])
def test_fwer_cell_runs_and_holm_never_exceeds_raw(design: str) -> None:
    job = FwerJob(0, "binary", design, 3, 20, 10, 0, 100)
    assert job.m == 3
    r = run_fwer(job)
    assert r.holm_fwer.successes <= r.raw_fwer.successes
    assert r.holm_fwer.trials == 10


def test_all_pairs_family_size() -> None:
    assert FwerJob(0, "binary", "all-pairs", 5, 20, 1, 0, 10).m == 10
    assert FwerJob(0, "binary", "independent", 5, 20, 1, 0, 10).m == 5


def test_plan_is_stable_and_cells_have_unique_streams() -> None:
    h0, h1, skipped, fwer = plan(StatsCheckConfig())
    ids = [j.cell_id for j in h0 + h1] + [j.cell_id for j in fwer]
    assert ids == list(range(len(ids)))
    assert len(h0) == 3 * 3 * 4
    assert {(s.kind, s.n, s.tie_rate) for s in skipped} >= {("binary", 20, 0.8)}
    assert plan(StatsCheckConfig()) == (h0, h1, skipped, fwer)


def test_run_stats_check_end_to_end_and_report() -> None:
    report = run_stats_check(TINY)
    assert len(report.h0) == 3
    assert len(report.fwer) == 2 * 1 * (3 + 3)
    text = render_markdown(report)
    for heading in ("Type-I error", "coverage", "Power at the n", "Holm family-wise", "Findings"):
        assert heading in text
    assert isinstance(collect_findings(report), list)


def test_pool_matches_serial() -> None:
    serial = run_stats_check(TINY)
    pooled = run_stats_check(dataclasses.replace(TINY, workers=2))
    assert serial.h0 == pooled.h0
    assert serial.h1 == pooled.h1
    assert serial.fwer == pooled.fwer


def test_cli_stats_check_writes_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "report.md"
    code = main(
        [
            "stats-check", "--ns", "20", "--ties", "0.5", "--fwer-ns", "20",
            "--reps-h0", "6", "--reps-power", "4", "--reps-fwer", "3",
            "--resamples", "40", "--draws", "80", "--workers", "1", "--out", str(out),
        ]
    )  # fmt: skip
    assert code == 0
    assert "Type-I error" in capsys.readouterr().out
    assert "Holm family-wise" in out.read_text(encoding="utf-8")


def test_cli_stats_check_rejects_bad_tie_rate(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats-check", "--ties", "1.0"]) == 2
    assert "tie rate" in capsys.readouterr().err
