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


# ------------------------------------------------------------- shipped defaults (switched)


def test_paired_auto_switches_to_dirichlet_only_for_small_binary() -> None:
    from evalkit.aggregate import SMALL_N_BINARY, paired_comparison, resolve_ci_method

    assert SMALL_N_BINARY == 50
    a = [1.0, 1.0, 0.0, 1.0] * 12 + [1.0, 0.0]  # 50 pairs
    b = [0.0, 1.0, 0.0, 0.0] * 12 + [1.0, 0.0]
    c = paired_comparison(a, b, num_resamples=50)
    assert c.ci_method == "dirichlet" and (c.wins, c.losses, c.ties) == (24, 0, 26)
    assert c.diff == 24 / 50 and c.diff_ci_lo < c.diff < c.diff_ci_hi < 1.0
    # one more pair: back to the bootstrap; non-binary scores: bootstrap
    assert paired_comparison([*a, 1.0], [*b, 0.0], num_resamples=50).ci_method != "dirichlet"
    assert paired_comparison([x * 0.9 for x in a], b, num_resamples=50).ci_method != "dirichlet"
    # a degenerate sample (all pairs tie) is a proper interval around 0, not [0, 0]
    tie = paired_comparison([1.0, 0.0] * 5, [1.0, 0.0] * 5)
    assert tie.diff_ci_lo < 0.0 < tie.diff_ci_hi
    assert resolve_ci_method("auto", 30, 0.9, binary=True) == "dirichlet"
    assert resolve_ci_method("auto", 30, 0.9) == "percentile"


def test_leaderboard_ci_wilson_only_for_one_small_binary_task() -> None:
    from evalkit.aggregate import bootstrap_macro_ci, leaderboard_ci

    ones = [1.0] * 19 + [0.0]
    mean, lo, hi, how = leaderboard_ci({"t": ones})
    wlo, whi = wilson_interval(19, 20, 0.95)
    assert how == "wilson" and mean == 0.95 and (lo, hi) == (wlo, whi) and lo > 0.75
    # the old default would print an interval that is too narrow here
    _, blo, bhi = bootstrap_macro_ci({"t": ones})
    assert bhi - blo < hi - lo
    # all correct: Wilson keeps an interval below 1, the bootstrap would collapse to [1, 1]
    _, lo, hi, how = leaderboard_ci({"t": [1.0] * 20})
    assert how == "wilson" and lo < 0.9 and hi == 1.0
    assert leaderboard_ci({"t": ones + [1.0] * 31})[3] == "bootstrap"  # 51 items
    assert leaderboard_ci({"t": ones, "u": ones})[3] == "bootstrap"  # macro mean of two tasks
    assert leaderboard_ci({"t": [0.5] * 19 + [1.0]})[3] == "bootstrap"  # not 0/1
    labels = {"t": [i // 2 for i in range(20)]}
    assert leaderboard_ci({"t": ones}, task_clusters=labels)[3] == "bootstrap"
    assert leaderboard_ci({"t": ones}, task_clusters={"t": ["a"] * 20})[3] == "wilson"
    # an empty task next to the one real task does not turn it into a macro mean
    assert leaderboard_ci({"t": ones, "empty": []})[3] == "wilson"


def test_leaderboard_markdown_notes_the_wilson_interval() -> None:
    from evalkit.aggregate import LeaderboardReport, ModelSummary

    def model(how: str) -> ModelSummary:
        return ModelSummary("m", 0.95, 0.77, 0.99, 0.5, 1000.0, ci_method=how)

    assert "Wilson score interval" in LeaderboardReport([model("wilson")]).to_markdown()
    assert "Wilson score interval" not in LeaderboardReport([model("bootstrap")]).to_markdown()
