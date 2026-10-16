from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from evalkit.aggregate import (
    bootstrap_macro_ci,
    bootstrap_mean_ci,
    build_pairwise_matches,
    compare_pairs,
    compute_elo_ratings,
    holm_bonferroni,
    macro_average,
    minimum_detectable_effect,
    paired_comparison,
    randomization_test_p,
    required_sample_size,
    sign_test_p,
)


def test_bootstrap_mean_ci_deterministic() -> None:
    scores = [1.0, 1.0, 0.5, 0.0, 1.0, 0.8, 0.2, 0.9]
    mean1, lo1, hi1 = bootstrap_mean_ci(scores, num_resamples=1000, seed=0)
    mean2, lo2, hi2 = bootstrap_mean_ci(scores, num_resamples=1000, seed=0)

    # Deterministic output with seed 0
    assert math.isclose(mean1, float(np.mean(scores)), rel_tol=1e-9)
    assert mean1 == mean2
    assert lo1 == lo2
    assert hi1 == hi2
    assert lo1 <= mean1 <= hi1


def test_macro_average() -> None:
    task_scores = {"arithmetic": 0.9, "mcq": 0.8, "code": 0.7}
    avg = macro_average(task_scores)
    assert math.isclose(avg, 0.8, rel_tol=1e-9)
    assert macro_average([]) == 0.0


def test_compute_elo_ratings() -> None:
    # A beats B, B beats C
    matches = [
        ("model_a", "model_b", 1.0),
        ("model_a", "model_b", 1.0),
        ("model_b", "model_c", 1.0),
        ("model_b", "model_c", 1.0),
    ]
    ratings = compute_elo_ratings(matches, base_rating=1000.0, k_factor=32.0)
    assert ratings["model_a"] > ratings["model_b"]
    assert ratings["model_b"] > ratings["model_c"]
    # Total points conserved
    total = sum(ratings.values())
    assert math.isclose(total, 3000.0, rel_tol=1e-5)


def test_elo_dominant_model_ranks_first_regardless_of_pair_grouping() -> None:
    # oracle >= noisy > random on every example; noisy beats random far more often
    # than it ties oracle. Grouping matches by pair used to rank noisy above oracle.
    example_scores = {
        f"ex{i:02d}": {"oracle": 1.0, "noisy": 1.0 if i % 3 else 0.0, "random": 0.0}
        for i in range(30)
    }
    ratings = compute_elo_ratings(build_pairwise_matches(example_scores))
    assert ratings["oracle"] > ratings["noisy"] > ratings["random"]


def test_bootstrap_macro_ci_brackets_macro_mean() -> None:
    # Unequal task sizes: macro mean (0.6) differs from the pooled micro mean (0.8).
    task_scores = {"big": [1.0] * 30, "small": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]}
    point, lo, hi = bootstrap_macro_ci(task_scores, num_resamples=1000, seed=0)
    assert math.isclose(point, (1.0 + 0.2) / 2)
    assert lo <= point <= hi
    assert bootstrap_macro_ci(task_scores, seed=0) == (point, lo, hi)


def test_build_pairwise_matches() -> None:
    example_scores = {
        "ex1": {"oracle": 1.0, "noisy": 0.5, "random": 0.0},
        "ex2": {"oracle": 1.0, "noisy": 1.0, "random": 0.0},
    }
    matches = build_pairwise_matches(example_scores)
    # ex1: (noisy, oracle, 0.0), (noisy, random, 1.0), (oracle, random, 1.0)
    # ex2: (noisy, oracle, 0.5), (noisy, random, 1.0), (oracle, random, 1.0)
    assert len(matches) == 6


def test_sign_test_hand_computed() -> None:
    assert sign_test_p(8, 0) == pytest.approx(2 / 2**8)  # 0.0078125
    assert sign_test_p(3, 3) == 1.0
    assert sign_test_p(0, 0) == 1.0
    # n = 10, k = 2: P(X <= 2) = (1 + 10 + 45) / 1024
    assert sign_test_p(8, 2) == pytest.approx(2 * 56 / 1024)


def test_paired_comparison_counts_and_degenerate_ci() -> None:
    c = paired_comparison([1, 1, 0, 1], [0, 1, 0, 0])
    assert (c.wins, c.losses, c.ties) == (2, 0, 2)
    assert c.diff == pytest.approx(0.5)
    assert c.diff_ci_lo <= 0.5 <= c.diff_ci_hi

    same = paired_comparison([1.0] * 5, [0.0] * 5)
    assert (same.diff_ci_lo, same.diff_ci_hi) == (1.0, 1.0)


def test_paired_comparison_pairing_shrinks_ci() -> None:
    # B = A - 0.1 on every example: unpaired spread is large, paired difference is constant.
    rng = np.random.default_rng(1)
    a = rng.uniform(0.2, 1.0, size=50).tolist()
    b = [x - 0.1 for x in a]
    c = paired_comparison(a, b)
    assert c.diff == pytest.approx(0.1)
    assert c.diff_ci_hi - c.diff_ci_lo < 1e-9


def test_paired_comparison_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        paired_comparison([1.0], [1.0, 0.0])


def _exhaustive_p(diffs: list[float]) -> float:
    observed = abs(sum(diffs))
    hits = 0
    total = 0
    for signs in itertools.product((1, -1), repeat=len(diffs)):
        total += 1
        if abs(sum(s * d for s, d in zip(signs, diffs, strict=True))) >= observed - 1e-9:
            hits += 1
    return hits / total


def test_randomization_p_matches_exhaustive_enumeration() -> None:
    diffs = [1.0, 1.0, 1.0, 1.0, 1.0, -1.0, 0.5, 0.5, -0.5, 1.0, 0.0, 0.0]  # n = 12, 10 nonzero
    assert randomization_test_p(diffs) == pytest.approx(_exhaustive_p(diffs), abs=1e-12)
    # hand case: 6 positive unit differences -> only all-plus / all-minus reach |sum| = 6
    assert randomization_test_p([1.0] * 6) == pytest.approx(2 / 2**6)
    # 5 positive, 1 negative: |sum| >= 4 needs <= 1 minus sign: 2 * (1 + 6) of 64
    assert randomization_test_p([1, 1, 1, 1, 1, -1]) == pytest.approx(14 / 64)
    assert randomization_test_p([0.0, 0.0]) == 1.0


def test_randomization_p_monte_carlo_close_to_exact_and_seeded() -> None:
    rng = np.random.default_rng(1)
    diffs = rng.choice([-1.0, 0.0, 1.0, 1.0], size=16).tolist()
    exact = randomization_test_p(diffs)
    mc = randomization_test_p(diffs, num_draws=20000, seed=3, exact_max_nonzero=0)
    assert mc == randomization_test_p(diffs, num_draws=20000, seed=3, exact_max_nonzero=0)
    assert abs(mc - exact) < 0.02


def test_randomization_p_switches_to_monte_carlo_above_20_nonzero() -> None:
    p = randomization_test_p([1.0] * 25, num_draws=10000, seed=0)
    assert p == pytest.approx(1 / 10001)  # never exactly 0, (hits + 1) / (draws + 1)


def test_holm_textbook_example() -> None:
    # p = 0.01, 0.04, 0.03, 0.005 (m = 4): sorted 0.005, 0.01, 0.03, 0.04
    # adj = 4*0.005, 3*0.01, 2*0.03, 1*0.04 = 0.02, 0.03, 0.06, 0.04; running max -> last is 0.06
    assert holm_bonferroni([0.01, 0.04, 0.03, 0.005]) == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert holm_bonferroni([0.5, 0.9]) == pytest.approx(
        [1.0, 1.0]
    )  # 0.9 is raised to 1.0 (monotone)
    assert holm_bonferroni([]) == []


def test_power_and_mde_hand_computed() -> None:
    # z_{0.975} + z_{0.8} = 1.959964 + 0.841621 = 2.801585
    # sd = 0.5, effect = 0.1: n = (2.801585 * 0.5 / 0.1)^2 = 196.22 -> 197
    assert required_sample_size(0.5, 0.1) == 197
    assert required_sample_size(0.5, -0.1) == 197
    # n = 100: MDE = 2.801585 * 0.5 / 10 = 0.14008
    assert minimum_detectable_effect(0.5, 100) == pytest.approx(0.140079, abs=1e-5)
    # round trip: the MDE at n needs about n examples
    assert required_sample_size(0.5, minimum_detectable_effect(0.5, 100)) == 100
    with pytest.raises(ValueError):
        required_sample_size(0.5, 0.0)


def test_compare_pairs_holm_and_verdict() -> None:
    keys = list(range(40))
    scores = {
        "hi": dict.fromkeys(keys, 1.0),
        "same": {k: 1.0 if k != 0 else 0.0 for k in keys},
        "lo": dict.fromkeys(keys, 0.0),
    }
    rows = {
        (r.model_a, r.model_b): r
        for r in compare_pairs(scores, [("hi", "same"), ("hi", "lo"), ("same", "lo")])
    }
    assert rows[("hi", "lo")].resolved
    assert rows[("hi", "lo")].n == 40
    assert not rows[("hi", "same")].resolved  # one win in 40
    assert rows[("hi", "same")].n_needed is not None
    assert rows[("hi", "same")].holm_p >= rows[("hi", "same")].rand_p
    assert rows[("hi", "lo")].holm_p <= 1.0
    assert compare_pairs({"a": {1: 1.0}, "b": {1: 1.0}}, [("a", "b")])[0].n_needed is None
