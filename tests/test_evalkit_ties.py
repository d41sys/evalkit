"""Tests for the tie path of ``mean_test_p`` (docs/protocol-ties.md)."""

from __future__ import annotations

import numpy as np
import pytest

from evalkit.aggregate import (
    TIE_FALLBACKS,
    asymmetry_gate,
    bootstrap_t_calibrated_p,
    bootstrap_t_test_p,
    compare_pairs,
    johnson_test_p,
    mean_test_p,
    sign_test_p,
    tie_share,
)


def _skewed_with_ties(n: int, k: int, seed: int) -> np.ndarray:
    """``k`` right-skewed nonzero differences among ``n``; the rest are exact ties."""
    rng = np.random.default_rng(seed)
    d = np.zeros(n)
    d[rng.choice(n, k, replace=False)] = 0.25 * (rng.standard_exponential(k) - 1.0)
    return d


def test_tie_path_needs_the_asymmetry_gate_and_a_tie_share_above_the_gate() -> None:
    skewed = _skewed_with_ties(100, 20, seed=1)  # tie share 0.8, asymmetric
    assert asymmetry_gate(skewed)[2]
    assert tie_share(skewed) == pytest.approx(0.8)

    _, hit = mean_test_p(skewed, "auto", tie_fallback="boott_nz", tie_gate=0.7)
    assert hit == "boott_nz"
    # the gate is strict: a share equal to tie_gate stays on the Phase M test
    _, edge = mean_test_p(skewed, "auto", tie_fallback="boott_nz", tie_gate=0.8)
    assert edge == "boott"
    # tie_fallback "none" is Phase M whatever the tie share
    _, none = mean_test_p(skewed, "auto", tie_fallback="none", tie_gate=0.0)
    assert none == "boott"

    # symmetric, heavily tied differences never reach the tie path
    rng = np.random.default_rng(2)
    sym = np.zeros(100)
    sym[:20] = rng.standard_normal(20)
    assert not asymmetry_gate(sym)[2]
    _, sym_method = mean_test_p(sym, "auto", tie_fallback="boott_nz", tie_gate=0.5)
    assert sym_method == "signflip"

    # 0/1 scores: every nonzero |d| is equal, the gate cannot fire, p identical to Phase M
    binary = np.array([1.0] * 12 + [-1.0] * 5 + [0.0] * 83)
    assert mean_test_p(binary, "auto", tie_fallback="boott_nz_cal", tie_gate=0.5) == mean_test_p(
        binary, "auto"
    )


def test_nonzero_tests_ignore_the_zeros() -> None:
    d = _skewed_with_ties(100, 20, seed=3)
    nz = d[d != 0.0]
    p_boott, _ = mean_test_p(d, "boott_nz", num_draws=500, seed=4)
    assert p_boott == bootstrap_t_test_p(nz, num_draws=500, seed=4)
    assert mean_test_p(d, "johnson_nz")[0] == johnson_test_p(nz)
    wins, losses = int((nz > 0).sum()), int((nz < 0).sum())
    assert mean_test_p(d, "signtest")[0] == sign_test_p(wins, losses)
    p_cal, _ = mean_test_p(d, "boott_nz_cal", num_draws=99, seed=4)
    assert p_cal == bootstrap_t_calibrated_p(nz, num_draws=99, seed=4)
    # the tie path is the same call as the explicit method
    assert mean_test_p(d, "auto", num_draws=99, seed=4, tie_fallback="boott_nz_cal", tie_gate=0.5)[
        0
    ] == pytest.approx(p_cal)


def test_calibrated_bootstrap_t_p_value_properties() -> None:
    rng = np.random.default_rng(5)
    null = rng.standard_exponential(25) - 1.0
    p = bootstrap_t_calibrated_p(null, num_draws=99, seed=0)
    assert 0.0 < p <= 1.0
    assert p == bootstrap_t_calibrated_p(null, num_draws=99, seed=0)
    assert bootstrap_t_calibrated_p(null + 3.0, num_draws=99, seed=0) < 0.05
    assert bootstrap_t_calibrated_p([0.0] * 10) == 1.0
    assert 0.0 < bootstrap_t_calibrated_p([2.0] * 10) <= 1.0  # constant: sign-flip fallback


def test_fewer_than_two_nonzero_differences_use_the_sign_flip_test() -> None:
    d = np.zeros(50)
    d[7] = 0.4
    for method in ("signtest", "boott_nz", "johnson_nz", "boott_nz_cal"):
        assert mean_test_p(d, method)[0] == 1.0
    assert mean_test_p(np.zeros(10), "boott_nz_cal")[0] == 1.0


def test_unknown_tie_fallback_is_rejected_and_compare_pairs_reports_the_path() -> None:
    with pytest.raises(ValueError, match="tie fallback"):
        mean_test_p([0.1, -0.2, 0.3], "auto", tie_fallback="nope")
    assert "none" in TIE_FALLBACKS
    d = _skewed_with_ties(100, 20, seed=1)
    keys = list(range(100))
    scores = {"a": {k: float(0.5 + d[k]) for k in keys}, "b": {k: 0.5 for k in keys}}
    rows = compare_pairs(
        scores,
        [("a", "b")],
        num_resamples=50,
        num_draws=200,
        with_power=False,
        rand_tie_fallback="boott_nz",
        rand_tie_gate=0.5,
    )
    assert rows[0].p_method == "boott_nz"
