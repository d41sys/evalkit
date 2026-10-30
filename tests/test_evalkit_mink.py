"""Offline tests for evalkit.mink: numpy only, no model, no network."""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pytest

from evalkit.mink import (
    auroc,
    classify_auroc,
    length_matched_mask,
    masked_auroc,
    mean_logprob,
    min_k_prob,
    numbers_multiset,
    pair_wins,
    paired_auroc_ci,
    paired_bootstrap,
    percentile_ci,
    residualize,
    same_numbers,
    zlib_length,
    zlib_ratio,
)


def test_min_k_prob_hand_made_vectors() -> None:
    lp = [-1.0, -5.0, -2.0, -9.0, -3.0, -4.0, -0.5, -7.0, -6.0, -8.0]
    # K=20 of 10 tokens -> the 2 lowest: -9 and -8
    assert min_k_prob(lp, 20) == pytest.approx(-8.5)
    assert min_k_prob(lp, 10) == pytest.approx(-9.0)
    assert min_k_prob(lp, 50) == pytest.approx(np.mean([-9, -8, -7, -6, -5]))
    assert min_k_prob(lp, 100) == pytest.approx(mean_logprob(lp))
    # floor of one token for short texts
    assert min_k_prob([-1.0, -3.0, -2.0], 20) == -3.0
    # floor(7 * 0.3) = 2
    assert min_k_prob([-1, -2, -3, -4, -5, -6, -7], 30) == pytest.approx(-6.5)
    # input order is irrelevant
    assert min_k_prob(lp[::-1], 20) == min_k_prob(lp, 20)


def test_min_k_prob_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        min_k_prob([], 20)
    with pytest.raises(ValueError):
        min_k_prob([-1.0], 0)
    with pytest.raises(ValueError):
        min_k_prob([-1.0], 101)
    with pytest.raises(ValueError):
        min_k_prob([[-1.0]], 20)


def _brute_auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    wins = 0.0
    for a in pos:
        for b in neg:
            wins += 1.0 if a > b else 0.5 if a == b else 0.0
    return wins / (len(pos) * len(neg))


def test_auroc_matches_brute_force_with_ties() -> None:
    rng = np.random.default_rng(1)
    for _ in range(40):
        n, m = int(rng.integers(1, 15)), int(rng.integers(1, 15))
        pos = rng.integers(0, 6, size=n).astype(float)  # many ties
        neg = rng.integers(0, 6, size=m).astype(float)
        assert auroc(pos, neg) == pytest.approx(_brute_auroc(pos, neg))
        assert pair_wins(pos, neg).mean() == pytest.approx(_brute_auroc(pos, neg))
    assert auroc([3.0, 4.0], [1.0, 2.0]) == 1.0
    assert auroc([1.0, 2.0], [3.0, 4.0]) == 0.0
    assert auroc([1.0, 1.0], [1.0, 1.0]) == 0.5


def test_length_matched_and_masked_auroc() -> None:
    pos = np.array([1.0, 5.0, 3.0])
    neg = np.array([2.0, 2.0, 4.0])
    len_pos = np.array([10.0, 20.0, 30.0])
    len_neg = np.array([11.0, 40.0, 29.0])
    wins = pair_wins(pos, neg)
    mask = length_matched_mask(len_pos, len_neg, 5)
    idx = np.arange(3)
    # allowed pairs: (0,0), (2,2) -> 1<2 loses, 3<4 loses
    assert masked_auroc(wins, mask, idx, idx) == 0.0
    # an all-ones mask is the plain AUROC
    assert masked_auroc(wins, np.ones((3, 3)), idx, idx) == pytest.approx(auroc(pos, neg))
    # no allowed pair -> NaN
    assert np.isnan(masked_auroc(wins, length_matched_mask(len_pos, len_neg, -1), idx, idx))


def test_residualize_removes_linear_length_trend() -> None:
    length = np.arange(20, dtype=float)
    score = 3.0 - 0.25 * length
    assert np.allclose(residualize(score, length), 0.0, atol=1e-9)
    noisy = score + np.where(np.arange(20) % 2 == 0, 0.1, -0.1)
    res = residualize(noisy, length)
    assert abs(np.corrcoef(res, length)[0, 1]) < 1e-9


def test_bootstrap_is_deterministic_and_paired() -> None:
    rng = np.random.default_rng(0)
    pos = rng.normal(0.3, 1.0, size=40)
    neg = rng.normal(0.0, 1.0, size=40)
    a = paired_auroc_ci(pos, neg, n_boot=300, seed=0)
    b = paired_auroc_ci(pos, neg, n_boot=300, seed=0)
    c = paired_auroc_ci(pos, neg, n_boot=300, seed=1)
    assert a == b
    assert a != c
    point, lo, hi = a
    assert point == pytest.approx(auroc(pos, neg))
    assert lo <= point <= hi

    # identical draws for identical (n, n_boot, seed): the resampled indices are shared
    seen: list[list[int]] = []
    paired_bootstrap(lambda idx: float(seen.append(idx.tolist()) or 0.0), 5, n_boot=3, seed=7)
    again: list[list[int]] = []
    paired_bootstrap(lambda idx: float(again.append(idx.tolist()) or 0.0), 5, n_boot=3, seed=7)
    assert seen == again and all(len(s) == 5 and max(s) < 5 for s in seen)


def test_pair_resampling_keeps_original_and_paraphrase_together() -> None:
    # Row i: original score 10*i, paraphrase score 10*i - 1. If a pair moves together, every
    # resample has orig - para == 1 on each position.
    orig = np.arange(8, dtype=float) * 10
    para = orig - 1.0
    diffs: list[float] = []

    def stat(idx: np.ndarray) -> float:
        diffs.extend((orig[idx] - para[idx]).tolist())
        return 0.0

    paired_bootstrap(stat, 8, n_boot=20, seed=0)
    assert set(diffs) == {1.0}


def test_ci_and_decision_rule() -> None:
    assert percentile_ci([0.0, 1.0, 2.0, 3.0, 4.0], 0.5) == (1.0, 3.0)
    assert percentile_ci([float("nan"), 1.0, 3.0], 0.5) == (1.5, 2.5)
    assert classify_auroc(0.52, 0.7) == "separates"
    assert classify_auroc(0.3, 0.48) == "reversed"
    assert classify_auroc(0.45, 0.6) == "no detectable effect"
    # a perfectly separated sample has a CI above 0.5
    pos = np.arange(30, dtype=float) + 100
    neg = np.arange(30, dtype=float)
    _, lo, _ = paired_auroc_ci(pos, neg, n_boot=200)
    assert lo > 0.5


def test_number_multiset_check() -> None:
    assert numbers_multiset("5 apples and 5 pears cost $1,200.50") == {
        "5": 2,
        "1200.50": 1,
    }
    assert same_numbers("Tom has 3 cats and 12 dogs.", "12 dogs and 3 cats belong to Tom.")
    assert not same_numbers("5 cats, 5 dogs", "5 cats, 6 dogs")
    assert not same_numbers("5 cats and 5 dogs", "5 cats and dogs")  # multiset, not set
    assert same_numbers("It costs 1,000 dollars", "It costs 1000 dollars")
    assert same_numbers("no numbers here", "none at all")


def test_zlib_score() -> None:
    text = "a" * 200
    assert zlib_length(text) < zlib_length("".join(chr(33 + i % 90) for i in range(200)))
    lp = [-1.0, -2.0, -3.0]
    assert zlib_ratio(lp, text) == pytest.approx(-6.0 / zlib_length(text))


def test_module_import_pulls_in_no_model_library() -> None:
    code = (
        "import sys, evalkit.mink; "
        "bad = [m for m in ('torch', 'transformers') if m in sys.modules]; "
        "sys.exit(1 if bad else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0
