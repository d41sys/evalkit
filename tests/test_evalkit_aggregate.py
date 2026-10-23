from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from evalkit.aggregate import (
    EXACT_POWER_MAX_N,
    SMALL_N_CI,
    SMALL_N_METHOD,
    _sign_test_cutoff,
    bootstrap_macro_ci,
    bootstrap_mean_ci,
    build_pairwise_matches,
    compare_pairs,
    compute_elo_ratings,
    holm_bonferroni,
    is_binary,
    jackknife_acceleration,
    macro_average,
    minimum_detectable_effect,
    minimum_detectable_effect_binary,
    paired_binary_power,
    paired_binary_power_exact,
    paired_comparison,
    randomization_test_p,
    required_sample_size,
    required_sample_size_binary,
    resolve_ci_method,
    sample_skewness,
    sign_test_p,
    skewness_warning,
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


# ------------------------------------------------- binary power: Connor (1987) / McNemar


def test_binary_sample_size_published_examples() -> None:
    # Machin, Campbell, Tan & Tan (2009), as worked in the MedCalc manual: 20% of cases shift
    # positive -> negative, 10% negative -> positive, alpha 0.05, power 0.8: n = 234.
    # psi = 0.3, delta = 0.1: ((1.95996 sqrt(.3) + 0.84162 sqrt(.29)) / .1)^2 = 233.1 -> 234
    assert required_sample_size_binary(0.3, 0.1, exact=False) == 234
    assert required_sample_size_binary(0.3, -0.1, exact=False) == 234
    # Stata `power pairedproportions 0.105 0.004` (Connor 1987): n = 82 (81.5 before rounding up)
    assert required_sample_size_binary(0.109, 0.101, exact=False) == 82
    # ... and its power at n = 100 is 0.8759
    assert paired_binary_power(100, 0.101, 0.109) == pytest.approx(0.8759, abs=5e-5)


def test_binary_power_is_consistent_with_sample_size() -> None:
    for psi, delta in [(0.3, 0.1), (0.109, 0.101), (0.5, 0.2), (0.2, 0.05)]:
        n = required_sample_size_binary(psi, delta, exact=False)
        assert paired_binary_power(n, delta, psi) >= 0.8 - 1e-9
        assert paired_binary_power(n - 3, delta, psi) < 0.8
    assert paired_binary_power(0, 0.1, 0.3) == 0.0
    with pytest.raises(ValueError):
        paired_binary_power(10, 0.5, 0.3)  # more wins than discordant pairs


def test_binary_mde_inverts_the_sample_size_formula() -> None:
    for psi, n in [(0.3, 234), (0.5, 100), (0.2, 400)]:
        d = minimum_detectable_effect_binary(psi, n, exact=False)
        assert 0.0 < d <= psi
        assert abs(required_sample_size_binary(psi, d, exact=False) - n) <= 1
    # n = 234, psi = 0.3 -> the published effect 0.1 (to the rounding of n)
    assert minimum_detectable_effect_binary(0.3, 234, exact=False) == pytest.approx(0.1, abs=1e-3)
    # even every discordant pair favouring one model is invisible: 2 of 115 discordant
    for exact in (False, True):
        assert math.isinf(minimum_detectable_effect_binary(2 / 115, 115, exact=exact))
        assert minimum_detectable_effect_binary(0.0, 100, exact=exact) == 0.0
        assert math.isinf(minimum_detectable_effect_binary(0.3, 0, exact=exact))


def _brute_force_power(n: int, p_win: float, p_loss: float, alpha: float) -> float:
    """Sum the trinomial pmf over every (wins, losses) outcome the sign test rejects."""
    total = 0.0
    for w in range(n + 1):
        for lo in range(n + 1 - w):
            if sign_test_p(w, lo) < alpha:
                ties = n - w - lo
                coef = math.factorial(n) / (
                    math.factorial(w) * math.factorial(lo) * math.factorial(ties)
                )
                total += coef * p_win**w * p_loss**lo * (1 - p_win - p_loss) ** ties
    return total


def test_exact_binary_power_matches_brute_force_enumeration() -> None:
    for n, p_win, p_loss in [(12, 0.4, 0.1), (25, 0.25, 0.05), (30, 0.1, 0.1), (18, 0.5, 0.0)]:
        brute = _brute_force_power(n, p_win, p_loss, 0.05)
        exact = paired_binary_power_exact(n, p_win - p_loss, p_win + p_loss)
        assert exact == pytest.approx(brute, abs=1e-12)


def test_exact_binary_power_is_below_connor_at_connors_n() -> None:
    # discrete exact test is conservative: the closed form is optimistic at its own n
    n = required_sample_size_binary(0.3, 0.1, exact=False)
    assert paired_binary_power(n, 0.1, 0.3) >= 0.8
    assert paired_binary_power_exact(n, 0.1, 0.3) < paired_binary_power(n, 0.1, 0.3)
    exact_n = required_sample_size_binary(0.3, 0.1)
    assert exact_n >= n - 3
    assert paired_binary_power_exact(exact_n, 0.1, 0.3) >= 0.8
    assert paired_binary_power_exact(exact_n - 1, 0.1, 0.3) < 0.8
    # the exact minimum detectable effect reproduces 0.8 power at that n
    d = minimum_detectable_effect_binary(0.3, exact_n)
    assert paired_binary_power_exact(exact_n, d, 0.3) == pytest.approx(0.8, abs=1e-6)


def test_exact_binary_power_edge_cases() -> None:
    assert paired_binary_power_exact(0, 0.1, 0.3) == 0.0
    assert paired_binary_power_exact(50, 0.0, 0.0) == 0.0
    with pytest.raises(ValueError):
        paired_binary_power_exact(10, 0.5, 0.3)
    # under H1 with no wins by the other model and many discordant pairs: near certain
    assert paired_binary_power_exact(200, 0.5, 0.5) == pytest.approx(1.0, abs=1e-12)
    # at the null (d = 0) the exact test rejects at most alpha
    assert paired_binary_power_exact(60, 0.0, 0.4) <= 0.05


def test_resolve_ci_method_tie_guard() -> None:
    assert resolve_ci_method("auto", 100, 0.0) == SMALL_N_METHOD
    assert resolve_ci_method("auto", 100, 0.5) == SMALL_N_METHOD
    assert resolve_ci_method("auto", 100, 0.51) == "percentile"
    assert resolve_ci_method("auto", 400, 0.0) == "percentile"
    assert resolve_ci_method("bca", 400, 0.9) == "bca"


def test_sign_test_cutoff_matches_sign_test_p_on_both_code_paths() -> None:
    for m in (60, 400, 401, 900):  # integer path up to 400, log-space floats above
        c = _sign_test_cutoff(m, 0.05)
        assert sign_test_p(c, m - c) < 0.05
        assert sign_test_p(c + 1, m - c - 1) >= 0.05


def test_exact_binary_search_is_fast_and_falls_back_to_connor_for_huge_n() -> None:
    # target effect 0.001 would need ~4 million pairs: closed form, not a million-step search
    assert required_sample_size_binary(0.5, 0.001) == required_sample_size_binary(
        0.5, 0.001, exact=False
    )
    assert required_sample_size_binary(0.5, 0.001) > EXACT_POWER_MAX_N
    # inside the exact range the sawtooth search lands on a crossing whose predecessor window fails
    n = required_sample_size_binary(0.4, 0.1)
    assert paired_binary_power_exact(n, 0.1, 0.4) >= 0.8
    assert all(paired_binary_power_exact(m, 0.1, 0.4) < 0.8 for m in range(max(2, n - 60), n))


def test_compare_pairs_without_power_skips_mde_and_n_needed() -> None:
    scores = {"a": {i: float(i % 2) for i in range(30)}, "b": {i: 0.0 for i in range(30)}}
    rows = compare_pairs(scores, [("a", "b")], num_resamples=50, with_power=False)
    assert math.isnan(rows[0].mde) and rows[0].n_needed is None
    full = compare_pairs(scores, [("a", "b")], num_resamples=50)
    assert full[0].n_needed is not None and full[0].rand_p == rows[0].rand_p


def test_binary_sample_size_edge_cases() -> None:
    with pytest.raises(ValueError):
        required_sample_size_binary(0.3, 0.0)
    with pytest.raises(ValueError):
        required_sample_size_binary(0.3, 1.5)
    # an effect larger than the discordant rate raises psi to the effect
    assert required_sample_size_binary(0.01, 0.2, exact=False) == required_sample_size_binary(
        0.2, 0.2, exact=False
    )


def test_binary_formula_differs_from_normal_approximation() -> None:
    # old formula: SD of the differences = sqrt(psi - delta^2) on both sides
    psi, delta = 0.3, 0.1
    old = required_sample_size(math.sqrt(psi - delta**2), delta)
    assert old == 228
    assert required_sample_size_binary(psi, delta, exact=False) == 234 > old


def test_is_binary() -> None:
    assert is_binary([0, 1, 1.0, 0.0])
    assert not is_binary([0, 1, 0.5])
    assert not is_binary([])


def test_compare_pairs_uses_binary_formula_only_for_binary_scores() -> None:
    keys = list(range(100))
    rng = np.random.default_rng(3)
    a = (rng.random(100) < 0.6).astype(float)
    b = (rng.random(100) < 0.5).astype(float)
    scores = {"a": dict(zip(keys, a, strict=True)), "b": dict(zip(keys, b, strict=True))}
    row = compare_pairs(scores, [("a", "b")])[0]
    psi = (row.wins + row.losses) / row.n
    assert row.binary
    assert row.mde == pytest.approx(minimum_detectable_effect_binary(psi, 100))
    assert row.n_needed == required_sample_size_binary(psi, abs(row.diff))

    scaled = {"a": dict(zip(keys, a * 0.9, strict=True)), "b": scores["b"]}
    cont = compare_pairs(scaled, [("a", "b")])[0]
    assert not cont.binary
    assert cont.mde == pytest.approx(minimum_detectable_effect(cont.sd_diff, 100))
    assert cont.n_needed == required_sample_size(cont.sd_diff, abs(cont.diff))


# ------------------------------------------------------------------ BCa / studentized CIs


def test_jackknife_acceleration_is_skewness_over_six_root_n() -> None:
    # Efron (1987): for the sample mean the jackknife acceleration equals skew / (6 sqrt(n)).
    x = np.array([0.1, 0.4, 0.2, 3.0, 0.3, 0.2, 1.1, 0.5, 0.9, 7.5])
    assert jackknife_acceleration(x) == pytest.approx(sample_skewness(x) / (6 * math.sqrt(x.size)))
    sym = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    assert jackknife_acceleration(sym) == pytest.approx(0.0, abs=1e-12)
    assert jackknife_acceleration(np.ones(6)) == 0.0


def test_bca_matches_percentile_on_symmetric_data_and_shifts_up_on_right_skew() -> None:
    rng = np.random.default_rng(1)
    sym = rng.standard_normal(60).tolist()
    _, plo, phi = bootstrap_mean_ci(sym, 20000, seed=2, method="percentile")
    _, blo, bhi = bootstrap_mean_ci(sym, 20000, seed=2, method="bca")
    assert blo == pytest.approx(plo, abs=0.03)
    assert bhi == pytest.approx(phi, abs=0.03)
    # right-skewed sample: the mean's sampling distribution is right-skewed, so BCa moves
    # the interval up relative to the percentile interval (Efron 1987)
    skewed = (rng.exponential(1.0, size=25)).tolist()
    _, plo, phi = bootstrap_mean_ci(skewed, 20000, seed=2, method="percentile")
    _, blo, bhi = bootstrap_mean_ci(skewed, 20000, seed=2, method="bca")
    assert bhi > phi
    assert blo > plo


def test_bca_hand_computed_acceleration_and_levels() -> None:
    # n = 4, x = (0, 0, 0, 4): mean 1; c = (-1, -1, -1, 3): sum c^3 = 24, sum c^2 = 12
    # a = 24 / (6 * 12^1.5) = 0.09623 = skew / (6 sqrt 4) with skew = 1.1547
    x = np.array([0.0, 0.0, 0.0, 4.0])
    assert jackknife_acceleration(x) == pytest.approx(24 / (6 * 12**1.5))
    assert sample_skewness(x) == pytest.approx(2 / math.sqrt(3))


def test_studentized_is_close_to_the_t_interval_on_normal_data() -> None:
    rng = np.random.default_rng(5)
    x = rng.standard_normal(40)
    mean, lo, hi = bootstrap_mean_ci(x.tolist(), 20000, seed=0, method="studentized")
    half_t = 2.0227 * x.std(ddof=1) / math.sqrt(40)  # t_{0.975, 39}
    assert lo == pytest.approx(mean - half_t, abs=0.08 * half_t)
    assert hi == pytest.approx(mean + half_t, abs=0.08 * half_t)


def test_bootstrap_methods_degenerate_and_dispatch() -> None:
    for method in ("percentile", "bca", "studentized"):
        assert bootstrap_mean_ci([0.5] * 10, 200, method=method) == (0.5, 0.5, 0.5)
        mean, lo, hi = bootstrap_mean_ci(
            [0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0], 500, method=method
        )
        assert lo <= mean <= hi
        # reproducible
        assert bootstrap_mean_ci([0.0, 2.0, 1.0, 5.0], 300, seed=4, method=method) == (
            bootstrap_mean_ci([0.0, 2.0, 1.0, 5.0], 300, seed=4, method=method)
        )
    small = np.random.default_rng(0).standard_normal(SMALL_N_CI - 1).tolist()
    large = np.random.default_rng(0).standard_normal(SMALL_N_CI).tolist()
    assert SMALL_N_METHOD in ("bca", "studentized")
    assert bootstrap_mean_ci(small, 300) == bootstrap_mean_ci(small, 300, method=SMALL_N_METHOD)
    assert bootstrap_mean_ci(large, 300) == bootstrap_mean_ci(large, 300, method="percentile")
    assert resolve_ci_method("auto", SMALL_N_CI - 1) == SMALL_N_METHOD
    assert resolve_ci_method("auto", SMALL_N_CI) == "percentile"
    assert resolve_ci_method("studentized", 10) == "studentized"
    with pytest.raises(ValueError):
        bootstrap_mean_ci([1.0, 2.0], 10, method="nope")
    assert paired_comparison([1, 0, 1, 1], [0, 0, 1, 0]).ci_method == SMALL_N_METHOD
    assert paired_comparison([1, 0, 1, 1], [0, 0, 1, 0], ci_method="percentile").ci_method == (
        "percentile"
    )


# ------------------------------------------------------------------------ skew warning


def test_skewness_warning_rule() -> None:
    # one large outlier among 5: skew = (n - 2) / sqrt(n - 1) = 1.5, 25 * 2.25 = 56 > 5
    g, warn = skewness_warning([0.0, 0.0, 0.0, 0.0, 10.0])
    assert g == pytest.approx(1.5)
    assert warn
    # symmetric differences never warn; large n with the same skew does not warn
    assert skewness_warning([-1.0, 1.0] * 20) == (0.0, False)
    assert not skewness_warning(np.random.default_rng(0).standard_normal(1000))[1]
    assert skewness_warning([0.0] * 599 + [10.0])[1]  # skew 24: needs n > 14000
    assert skewness_warning([0.5] * 10) == (0.0, False)


def test_compare_pairs_flags_skewed_differences() -> None:
    keys = list(range(30))
    skewed_b = {k: 0.0 for k in keys}
    skewed_a = {k: (3.0 if k == 0 else 0.0) for k in keys}
    row = compare_pairs({"a": skewed_a, "b": skewed_b}, [("a", "b")])[0]
    assert row.skew_warning
    assert row.skewness > 4
    flat = compare_pairs(
        {"a": {k: float(k % 2) for k in keys}, "b": dict.fromkeys(keys, 0.5)}, [("a", "b")]
    )[0]
    assert not flat.skew_warning
