"""Tests for the skewed-data type-I fix and the alternative mean tests."""

from __future__ import annotations

import numpy as np
import pytest

from evalkit.aggregate import (
    ASYMMETRIC_METHOD,
    asymmetry_gate,
    bootstrap_t_test_p,
    compare_pairs,
    johnson_test_p,
    mean_test_p,
    randomization_test_p,
)


def test_studentized_sign_flip_is_mathematically_equivalent_to_plain_sign_flip() -> None:
    """Fisher's equivalence: studentising under sign flips cannot change the p-value.

    ``sum s_i^2 d_i^2 = sum d_i^2`` is invariant, so the one-sample t-statistic is a
    monotone function of |sum s_i d_i|.
    """
    rng = np.random.default_rng(42)
    for _ in range(5):
        diffs = rng.standard_exponential(10) - 1.0
        n = diffs.size
        signs = np.array(
            [[(-1 if (i >> b) & 1 else 1) for b in range(n)] for i in range(1 << n)],
            dtype=np.float64,
        )
        mean_star = (signs @ diffs) / n
        var_star = (np.sum(diffs**2) - n * mean_star**2) / (n - 1)
        t_star = np.where(var_star > 1e-12, np.abs(mean_star) / np.sqrt(var_star / n), 0.0)

        # Rankings are identical up to machine-precision ties
        p_plain = randomization_test_p(diffs)
        t_obs = t_star[0]
        p_t = float(np.count_nonzero(t_star >= t_obs - 1e-9)) / (1 << n)
        assert p_plain == pytest.approx(p_t, abs=1e-6)


def test_asymmetry_gate_detects_skew_and_ignores_symmetric_and_binary() -> None:
    rng = np.random.default_rng(0)
    # Skewed continuous: should fire
    skewed = rng.standard_exponential(40) - 1.0
    _, _, fires = asymmetry_gate(skewed)
    assert fires

    # Symmetric continuous: should not fire
    symmetric = rng.standard_normal(200)
    _, _, fires_sym = asymmetry_gate(symmetric)
    assert not fires_sym

    # Binary/equal-magnitude differences (0/1 scores): never fires
    binary = [-1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 1.0]
    _, _, fires_bin = asymmetry_gate(binary)
    assert not fires_bin

    # Mostly-zero symmetric continuous: gate ignores zeros and looks at nonzeros
    mostly_zero_sym = np.concatenate([np.zeros(100), rng.standard_normal(40)])
    _, _, fires_zero_sym = asymmetry_gate(mostly_zero_sym)
    assert not fires_zero_sym


def test_bootstrap_t_test_p_null_behavior() -> None:
    rng = np.random.default_rng(1)
    diffs = rng.standard_normal(30)
    p = bootstrap_t_test_p(diffs, num_draws=2000, seed=0)
    assert 0.0 < p <= 1.0
    # Degenerate: all zeros
    assert bootstrap_t_test_p([0.0] * 10) == 1.0
    # Degenerate: constant nonzero
    assert 0.0 < bootstrap_t_test_p([2.0] * 10) <= 1.0


def test_johnson_test_p_properties() -> None:
    rng = np.random.default_rng(2)
    # Normal data: close to standard t
    diffs = rng.standard_normal(100)
    p = johnson_test_p(diffs)
    assert 0.0 < p <= 1.0
    # Obvious effect rejects
    assert johnson_test_p(diffs + 5.0) < 1e-4
    # All zeros gives 1
    assert johnson_test_p([0.0] * 10) == 1.0


def test_mean_test_p_auto_dispatch() -> None:
    rng = np.random.default_rng(3)
    skewed = rng.standard_exponential(20) - 1.0
    _, method_skewed = mean_test_p(skewed, "auto")
    assert method_skewed == ASYMMETRIC_METHOD

    sym = rng.standard_normal(200)
    _, method_sym = mean_test_p(sym, "auto")
    assert method_sym == "signflip"


def test_compare_pairs_reports_p_method() -> None:
    keys = list(range(30))
    a = {k: 1.0 if k < 15 else 0.0 for k in keys}
    b = {k: 0.0 for k in keys}
    rows = compare_pairs({"a": a, "b": b}, [("a", "b")])
    assert rows[0].p_method == "signflip"
