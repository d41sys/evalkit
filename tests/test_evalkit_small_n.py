from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from evalkit.cli import main
from evalkit.small_n_ci import JEFFREYS, UNIFORM, beta_interval, dirichlet_diff_interval
from evalkit.statscheck import Rate, wilson_interval
from evalkit.statscheck_small_n import (
    PAIRED_CANDIDATES,
    SINGLE_CANDIDATES,
    CellResult,
    SmallNConfig,
    band_status,
    failing_n,
    plan,
    run_cell,
    select_winner,
)

TINY = SmallNConfig(seed=3, reps=25, resamples=60, draws=60, ns=(20,), workers=1)


def test_beta_interval_known_answers() -> None:
    # uniform prior, no data: Beta(1, 1), the quantiles are the levels themselves
    lo, hi = beta_interval(0, 0, UNIFORM)
    assert math.isclose(lo, 0.025, abs_tol=1e-9) and math.isclose(hi, 0.975, abs_tol=1e-9)
    # uniform prior, one success: Beta(2, 1) has CDF x^2
    lo, hi = beta_interval(1, 1, UNIFORM)
    assert math.isclose(lo, math.sqrt(0.025), abs_tol=1e-9)
    assert math.isclose(hi, math.sqrt(0.975), abs_tol=1e-9)
    # Jeffreys, 0 of 10: Beta(1/2, 10.5); lower endpoint is tiny but positive, upper 0.2 to 0.3
    lo, hi = beta_interval(0, 10, JEFFREYS)
    assert 0.0 < lo < 1e-3 and 0.2 < hi < 0.3
    # mirror symmetry under the symmetric prior
    lo, hi = beta_interval(3, 20, JEFFREYS)
    lo2, hi2 = beta_interval(17, 20, JEFFREYS)
    assert math.isclose(lo, 1.0 - hi2, abs_tol=1e-9) and math.isclose(hi, 1.0 - lo2, abs_tol=1e-9)


def test_dirichlet_diff_interval_matches_normal_approximation() -> None:
    w, l_, t = 60, 20, 120  # n = 200, difference 0.2
    lo, hi = dirichlet_diff_interval(w, l_, t, JEFFREYS, draws=40000, seed=1)
    n = w + l_ + t
    d = (w - l_) / n
    sd = math.sqrt(((w + l_) / n - d * d) / n)
    assert math.isclose((lo + hi) / 2, d, abs_tol=0.01)
    assert math.isclose(hi - lo, 2 * 1.96 * sd, rel_tol=0.05)
    # symmetric counts: the interval is centred on 0
    lo, hi = dirichlet_diff_interval(5, 5, 10, UNIFORM, draws=40000, seed=2)
    assert abs(lo + hi) < 0.01 and lo < 0 < hi


def test_plan_grid_size_and_ids() -> None:
    cells = plan(SmallNConfig())
    assert [c.kind for c in cells].count("single") == 12
    assert [c.kind for c in cells].count("paired") == 18
    assert [c.cell_id for c in cells] == list(range(30))
    assert {c.n for c in cells} == {20, 50, 100}


def test_single_cell_matches_independent_recomputation() -> None:
    cell = plan(TINY)[2]  # n = 20, p = 0.9
    assert cell.kind == "single" and cell.rate == 0.9
    res = run_cell((cell, TINY))
    rng = np.random.default_rng(np.random.SeedSequence([TINY.seed, cell.cell_id]))
    ks = rng.binomial(cell.n, cell.rate, size=TINY.reps).tolist()
    wil = sum(wilson_interval(k, 20, 0.95)[0] <= 0.9 <= wilson_interval(k, 20, 0.95)[1] for k in ks)
    jef = sum(
        beta_interval(k, 20, JEFFREYS)[0] <= 0.9 <= beta_interval(k, 20, JEFFREYS)[1] for k in ks
    )
    assert res.covered["wilson"] == wil and res.covered["jeffreys"] == jef
    assert run_cell((cell, TINY)) == res  # deterministic for a fixed seed


def test_paired_cell_null_and_effect() -> None:
    cells = plan(TINY)
    null = next(c for c in cells if c.kind == "paired" and c.rate == 0.6 and c.effect == 0.0)
    res = run_cell((null, TINY))
    assert res.reps == TINY.reps and res.rand_rejects <= res.reps
    assert all(0 <= v <= res.reps for v in res.covered.values())
    assert res.width["dirichlet-jeffreys"] > 0
    alt = next(c for c in cells if c.kind == "paired" and c.rate == 0.6 and c.effect == 0.3)
    assert run_cell((alt, TINY)).rand_rejects == 0  # tests are only run at a true difference 0


def _result(method_cov: dict[str, int], n: int = 20, kind: str = "single") -> CellResult:
    from evalkit.statscheck_small_n import Cell

    return CellResult(Cell(0, kind, n, 0.9), 100, method_cov, dict.fromkeys(method_cov, 0.1))


def test_band_and_selection_rules() -> None:
    assert band_status(Rate(92, 100)) == "under"
    assert band_status(Rate(93, 100)) == "ok"
    assert band_status(Rate(97, 100)) == "ok"
    assert band_status(Rate(98, 100)) == "over"
    rows = [
        _result({"percentile": 60, "jeffreys": 95, "wilson": 92, "uniform": 94}, n=20),
        _result({"percentile": 96, "jeffreys": 91, "wilson": 90, "uniform": 96}, n=50),
    ]
    assert failing_n(rows, "percentile") == 20
    assert failing_n(rows, "uniform") is None
    # uniform has no failing cell; jeffreys and wilson one or two
    assert select_winner(rows, SINGLE_CANDIDATES) == "uniform"
    # a tie on failing cells goes to the smaller total shortfall, then to the candidate order
    tie = [_result({"dirichlet-jeffreys": 95, "dirichlet-uniform": 95})]
    assert select_winner(tie, PAIRED_CANDIDATES) == "dirichlet-jeffreys"


def test_cli_only_small_n(tmp_path: Path, capsys: object) -> None:
    out = tmp_path / "sn.md"
    code = main(
        [
            "stats-check",
            "--only-small-n",
            "--small-n-ns",
            "20",
            "--small-n-reps",
            "6",
            "--resamples",
            "40",
            "--draws",
            "40",
            "--workers",
            "1",
            "--out",
            str(out),
        ]
    )
    text = out.read_text()
    assert code == 0
    assert "Single model: coverage" in text and "Paired tests: type-I" in text
    assert "Type-I error at alpha = 0.05 (H0" not in text  # the main grid did not run
