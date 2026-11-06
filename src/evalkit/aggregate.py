from __future__ import annotations

import math
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from statistics import NormalDist
from typing import Any

import numpy as np

from .clustered import (
    ClusterStats,
    cluster_bootstrap_ci,
    cluster_bootstrap_means,
    cluster_stats,
    cluster_sums,
    encode_clusters,
)

CI_METHODS = ("auto", "percentile", "bca", "studentized")
SMALL_N_CI = 400
"""``method="auto"`` uses :data:`SMALL_N_METHOD` below this many examples, else percentile.

At n = 400 the percentile interval's normal-theory coverage shortfall (Hesterberg 2015:
narrowness factor sqrt((n-1)/n) and z instead of t) is 0.1 percentage point."""
SMALL_N_METHOD = "studentized"
MAX_TIE_FRACTION_CI = 0.5
"""``auto`` falls back to percentile when more than this share of paired differences is 0.

Chosen from development seed 1 (bootstrap-t coverage equals or beats percentile at tie rates
0 and 0.5 but is clearly worse at 0.8), not from the final seed-0 test data."""


def jackknife_acceleration(arr: np.ndarray) -> float:
    """Acceleration ``a = sum(d^3) / (6 sum(d^2)^1.5)`` of the BCa interval for the mean.

    ``d_i = jack mean - jack_i`` over the leave-one-out means. For the mean this is
    exactly ``skewness / (6 sqrt(n))`` (Efron 1987); 0 when the data do not vary.
    """
    jack = (arr.sum() - arr) / (arr.size - 1)
    d = jack.mean() - jack
    denom = 6.0 * float((d * d).sum()) ** 1.5
    return float((d**3).sum()) / denom if denom > 0.0 else 0.0


def _bca_interval(arr: np.ndarray, boot_means: np.ndarray, alpha: float) -> tuple[float, float]:
    """BCa interval for the mean (Efron 1987, "Better bootstrap confidence intervals").

    Percentile levels are moved to ``Phi(z0 + (z0 + z_a) / (1 - a (z0 + z_a)))`` where
    ``z0`` is the bias correction (normal quantile of the bootstrap share below the
    estimate; ties count half, which matters for discrete scores) and ``a`` the
    jackknife acceleration ``sum(d^3) / (6 sum(d^2)^1.5)``, ``d = jack mean - jack_i``.
    """
    nd = NormalDist()
    theta = float(arr.mean())
    tol = 1e-12 * max(1.0, abs(theta))
    below = float(np.mean(boot_means < theta - tol)) + 0.5 * float(
        np.mean(np.abs(boot_means - theta) <= tol)
    )
    eps = 0.5 / boot_means.size
    z0 = nd.inv_cdf(min(max(below, eps), 1.0 - eps))
    accel = jackknife_acceleration(arr)
    out: list[float] = []
    for p in (alpha / 2.0, 1.0 - alpha / 2.0):
        zc = z0 + nd.inv_cdf(p)
        shrink = 1.0 - accel * zc
        adj = nd.cdf(z0 + zc / shrink) if shrink > 0.0 else (1.0 if zc > 0.0 else 0.0)
        out.append(float(np.quantile(boot_means, adj)))
    return (out[0], out[1])


def _studentized_interval(
    arr: np.ndarray, resamples: np.ndarray, alpha: float
) -> tuple[float, float] | None:
    """Bootstrap-t interval for the mean (Efron & Tibshirani 1993, ch. 12).

    ``t* = (mean* - mean) / (sd* / sqrt(n))`` over the resamples; the interval is
    ``mean - q_{1-a/2} se, mean - q_{a/2} se`` with ``se = sd / sqrt(n)``. Resamples
    with ``sd* = 0`` have no t value and are dropped; None if too few remain.
    """
    n = arr.size
    sd = float(arr.std(ddof=1))
    if sd <= 0.0:
        return None
    sd_star = resamples.std(axis=1, ddof=1)
    ok = sd_star > 1e-12 * sd
    if int(ok.sum()) < 0.5 * resamples.shape[0]:
        return None
    theta = float(arr.mean())
    t_star = (resamples.mean(axis=1)[ok] - theta) / (sd_star[ok] / math.sqrt(n))
    q_lo, q_hi = np.quantile(t_star, [alpha / 2.0, 1.0 - alpha / 2.0])
    se = sd / math.sqrt(n)
    return (theta - float(q_hi) * se, theta - float(q_lo) * se)


def resolve_ci_method(method: str, n: int, tie_fraction: float = 0.0) -> str:
    """The concrete interval method ``method`` means (``auto`` resolved).

    ``auto``: :data:`SMALL_N_METHOD` when ``n < SMALL_N_CI`` and at most
    :data:`MAX_TIE_FRACTION_CI` of the paired differences are exactly zero, else
    percentile. ``stats-check`` found the second-order methods worse than percentile when
    most pairs tie (few nonzero differences carry the resampled variance estimate).
    """
    if method not in CI_METHODS:
        raise ValueError(f"unknown CI method {method!r}; choose from {CI_METHODS}")
    if method == "auto":
        small = n < SMALL_N_CI and tie_fraction <= MAX_TIE_FRACTION_CI
        return SMALL_N_METHOD if small else "percentile"
    return method


def bootstrap_mean_ci(
    scores: Sequence[float],
    num_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 0,
    method: str = "auto",
) -> tuple[float, float, float]:
    """Compute mean and 95% bootstrap confidence interval (mean, ci_lo, ci_hi).

    Default: 1000 resamples, seed 0. ``method``:

    * ``percentile``: the plain percentile interval. Too narrow for small n
      (Hesterberg 2015), and for skewed scores.
    * ``bca``: bias-corrected and accelerated (Efron 1987), second-order accurate.
    * ``studentized``: bootstrap-t (Efron & Tibshirani 1993); falls back to the
      percentile interval when the data have no spread or most resamples do not.
      ``bca`` and ``studentized`` endpoints are clipped to the range of the scores.
    * ``auto`` (default): :data:`SMALL_N_METHOD` when ``n < SMALL_N_CI`` (400),
      percentile otherwise.
    """
    if method not in CI_METHODS:
        raise ValueError(f"unknown CI method {method!r}; choose from {CI_METHODS}")
    if len(scores) == 0:
        return (0.0, 0.0, 0.0)

    arr = np.asarray(scores, dtype=np.float64)
    n = arr.size
    mean_val = float(arr.mean())
    if n == 1 or num_resamples <= 0:
        return (mean_val, mean_val, mean_val)

    method = resolve_ci_method(method, n)
    rng = np.random.default_rng(seed)
    resamples = rng.choice(arr, size=(num_resamples, n), replace=True)
    resample_means = resamples.mean(axis=1)

    alpha = 1.0 - confidence_level
    if method == "bca":
        lo, hi = _bca_interval(arr, resample_means, alpha)
    else:
        stud = _studentized_interval(arr, resamples, alpha) if method == "studentized" else None
        if stud is not None:
            lo, hi = stud
        else:
            lo = float(np.percentile(resample_means, 100.0 * (alpha / 2.0)))
            hi = float(np.percentile(resample_means, 100.0 * (1.0 - alpha / 2.0)))
    if method != "percentile":
        # a second-order endpoint can leave the data's range (+1.04 for a 0/1 difference);
        # no resampled mean can, so clip to [min, max] of the scores
        lo, hi = max(lo, float(arr.min())), min(hi, float(arr.max()))
    return (mean_val, lo, hi)


def macro_average(task_scores: dict[str, float] | Sequence[float]) -> float:
    """Compute unweighted macro average over task scores."""
    scores = list(task_scores.values()) if isinstance(task_scores, dict) else list(task_scores)
    if not scores:
        return 0.0
    return float(np.mean(scores))


def bootstrap_macro_ci(
    task_scores: Mapping[str, Sequence[float]],
    num_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 0,
    task_clusters: Mapping[str, Sequence[Hashable]] | None = None,
) -> tuple[float, float, float]:
    """Macro mean with a stratified bootstrap CI: resample examples within each task,
    then average the per-task means, so the interval matches the macro statistic.

    ``task_clusters[task]`` gives one cluster label per score of that task (same order as
    ``task_scores[task]``). A task with at least two distinct labels resamples whole clusters
    (:func:`evalkit.clustered.cluster_bootstrap_means`), as ``compare`` does for a pair; a task
    without labels, or with a single one, resamples items. Without ``task_clusters`` the result
    is the plain item bootstrap.

    Scores are sorted per task first (by cluster label, then score), so the result does not
    depend on the order records arrived in (e.g. thread completion order)."""
    arrays: list[np.ndarray] = []
    codes_by_task: list[np.ndarray | None] = []
    for t in sorted(task_scores):
        scores = np.asarray(task_scores[t], dtype=np.float64)
        if scores.size == 0:
            continue
        labels = None if task_clusters is None else task_clusters.get(t)
        if labels is not None and len(labels) != scores.size:
            raise ValueError(f"task {t!r}: one cluster label per score is required")
        codes: np.ndarray | None = None
        if labels is not None and len(set(labels)) >= 2:
            order = sorted(range(scores.size), key=lambda i: (repr(labels[i]), scores[i]))
            scores = scores[order]
            codes = encode_clusters([labels[i] for i in order])
        else:
            scores = np.sort(scores)
        arrays.append(scores)
        codes_by_task.append(codes)
    if not arrays:
        return (0.0, 0.0, 0.0)
    point = float(np.mean([a.mean() for a in arrays]))
    if num_resamples <= 0:
        return (point, point, point)
    rng = np.random.default_rng(seed)
    rows = []
    for a, codes in zip(arrays, codes_by_task, strict=True):
        if codes is None:
            rows.append(rng.choice(a, size=(num_resamples, a.size), replace=True).mean(axis=1))
        else:
            sums, sizes = cluster_sums(a, codes)
            rows.append(cluster_bootstrap_means(sums, sizes, num_resamples, rng))
    macro = np.stack(rows).mean(axis=0)
    alpha = 1.0 - confidence_level
    lo = float(np.percentile(macro, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(macro, 100.0 * (1.0 - alpha / 2.0)))
    return (point, lo, hi)


def compute_elo_ratings(
    matches: Sequence[tuple[str, str, float]],
    base_rating: float = 1000.0,
    k_factor: float = 32.0,
) -> dict[str, float]:
    """Compute Elo ratings from pairwise matches.

    matches: list of (model_a, model_b, score_a) where score_a is:
        1.0: A won
        0.5: tie
        0.0: B won
    Matches are processed in the given order; pass them in a deterministic,
    interleaved order (``build_pairwise_matches`` orders by example). Sorting by
    model pair would play all games of one pair before the next and make the
    final ratings an artifact of that grouping.
    """
    if not matches:
        return {}

    sorted_matches = list(matches)

    # Initialize ratings
    all_models: set[str] = set()
    for m in sorted_matches:
        all_models.add(m[0])
        all_models.add(m[1])

    ratings: dict[str, float] = {model: base_rating for model in sorted(all_models)}

    for model_a, model_b, score_a in sorted_matches:
        ra = ratings[model_a]
        rb = ratings[model_b]

        ea = 1.0 / (1.0 + math.pow(10.0, (rb - ra) / 400.0))
        eb = 1.0 - ea

        score_b = 1.0 - score_a

        ratings[model_a] = ra + k_factor * (score_a - ea)
        ratings[model_b] = rb + k_factor * (score_b - eb)

    return ratings


def build_pairwise_matches(
    example_scores: dict[str, dict[str, float]],
) -> list[tuple[str, str, float]]:
    """Build pairwise matches from per-example model scores.

    example_scores: dict mapping example_id -> {model_id: score}
    Returns deterministically sorted matches.
    """
    matches: list[tuple[str, str, float]] = []

    for ex_id in sorted(example_scores.keys()):
        model_dict = example_scores[ex_id]
        models = sorted(model_dict.keys())
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                ma = models[i]
                mb = models[j]
                sa = model_dict[ma]
                sb = model_dict[mb]
                if math.isclose(sa, sb, abs_tol=1e-9):
                    score_a = 0.5
                elif sa > sb:
                    score_a = 1.0
                else:
                    score_a = 0.0
                matches.append((ma, mb, score_a))

    return matches


@dataclass
class ModelSummary:
    model_name: str
    macro_mean: float
    ci_lower: float
    ci_upper: float
    win_rate: float
    elo_rating: float
    ece: float = 0.0
    brier: float = 0.0
    total_examples: int = 0
    per_task_means: dict[str, float] = field(default_factory=dict)
    # 1-based; models in the same group are not resolved from their ranked neighbour.
    tie_group: int | None = None
    # number of tasks whose CI resampled whole clusters (rows carried a cluster_id)
    clustered_tasks: int = 0
    bt_rating: float | None = None
    bt_ci_lower: float | None = None
    bt_ci_upper: float | None = None


@dataclass
class LeaderboardReport:
    models: list[ModelSummary]
    ece_label: str = "15 bins"

    def to_markdown(self) -> str:
        # Sort models descending by macro_mean then elo_rating
        ranked = sorted(self.models, key=lambda m: (-m.macro_mean, -m.elo_rating, m.model_name))
        grouped = any(m.tie_group is not None for m in ranked)
        with_bt = any(m.bt_rating is not None for m in ranked)
        head = ["Rank", "Model", "Macro Mean", "95% CI", "Win Rate", "Elo Rating"]
        if with_bt:
            head.append("Bradley-Terry [95% CI]")
        head += ["ECE (" + self.ece_label + ")", "Brier", "Tasks Evaluated"]
        if grouped:
            head.append("Tie group")
        lines: list[str] = [
            "# Evaluation Leaderboard",
            "",
            "| " + " | ".join(head) + " |",
            "|" + "|".join("-" * (len(h) + 2) for h in head) + "|",
        ]
        for rank, m in enumerate(ranked, start=1):
            cells = [
                str(rank),
                m.model_name,
                f"{m.macro_mean:.3f}",
                f"[{m.ci_lower:.3f}, {m.ci_upper:.3f}]",
                f"{m.win_rate:.3f}",
                f"{m.elo_rating:.1f}",
            ]
            if with_bt:
                if m.bt_rating is None or m.bt_ci_lower is None or m.bt_ci_upper is None:
                    cells.append("-")
                else:
                    cells.append(f"{m.bt_rating:.1f} [{m.bt_ci_lower:.1f}, {m.bt_ci_upper:.1f}]")
            cells += [f"{m.ece:.3f}", f"{m.brier:.3f}", str(len(m.per_task_means))]
            if grouped:
                cells.append(str(m.tie_group) if m.tie_group is not None else "-")
            lines.append("| " + " | ".join(cells) + " |")
        notes: list[str] = []
        clustered = max((m.clustered_tasks for m in ranked), default=0)
        if clustered:
            notes.append(
                f"95% CI: stratified bootstrap over tasks; in the {clustered} task(s) whose rows "
                "carry a cluster_id whole clusters are resampled (the same cluster bootstrap "
                "`evalkit compare` uses), elsewhere single items."
            )
        if with_bt:
            notes.append(
                "Bradley-Terry: maximum-likelihood strengths from the per-item pairwise outcomes "
                "(ties count as half a win each), on the Elo scale (400 points per factor 10 in "
                "odds, mean rating 1000); the interval is a bootstrap over items"
                + (" (whole clusters where rows carry a cluster_id)." if clustered else ".")
            )
        if grouped:
            notes.append(
                "Tie group: a model joins the group of the model ranked directly "
                "above it unless the paired randomisation test on their per-example "
                "differences is resolved (Holm-adjusted p < 0.05 over the adjacent pairs"
                + (
                    "; whole clusters are flipped where rows carry a cluster_id"
                    if clustered
                    else ""
                )
                + "). Models sharing a group are not separated by this data."
            )
        for note in notes:
            lines.extend(["", note])

        if ranked and ranked[0].per_task_means:
            lines.extend(["", "## Per-Task Breakdown", ""])
            all_tasks = sorted({t for m in ranked for t in m.per_task_means})
            header = "| Model | " + " | ".join(all_tasks) + " |"
            sep = "|-------|" + "|".join(["-------" for _ in all_tasks]) + "|"
            lines.append(header)
            lines.append(sep)
            for m in ranked:
                task_cells = [f"{m.per_task_means.get(t, 0.0):.3f}" for t in all_tasks]
                lines.append(f"| {m.model_name} | " + " | ".join(task_cells) + " |")

        return "\n".join(lines)


def sign_test_p(wins: int, losses: int) -> float:
    """Two-sided exact sign test on paired outcomes; ties must be dropped by the caller.

    p = min(1, 2 * P(X <= min(wins, losses))) with X ~ Binomial(wins + losses, 0.5).
    """
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail: float = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2.0 * tail)


@dataclass(frozen=True)
class PairedComparison:
    """Model A vs model B on the same examples.

    ``clustering`` is set when the interval is the cluster bootstrap (``ci_method`` is then
    ``cluster-bootstrap``): naive and clustered SE of the mean difference, ICC and design effect.
    """

    n: int
    mean_a: float
    mean_b: float
    diff: float
    diff_ci_lo: float
    diff_ci_hi: float
    wins: int
    losses: int
    ties: int
    sign_p: float
    ci_method: str  # concrete method behind diff_ci_lo / diff_ci_hi
    clustering: ClusterStats | None = None


def paired_comparison(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    num_resamples: int = 10000,
    seed: int = 0,
    ci_method: str = "auto",
    clusters: Sequence[Hashable] | None = None,
) -> PairedComparison:
    """Paired bootstrap CI on mean(A - B) plus an exact sign test.

    Resampling the per-example differences keeps the pairing, so example difficulty
    cancels out instead of widening the interval. ``ci_method`` is resolved by
    :func:`resolve_ci_method` (default ``auto``: bootstrap-t below 400 examples unless
    more than half the pairs tie, else percentile) and passed to
    :func:`bootstrap_mean_ci`.

    ``clusters`` (one label per example) replaces the item bootstrap by the cluster bootstrap
    (:func:`evalkit.clustered.cluster_bootstrap_ci`; ``ci_method`` is ignored) and fills
    ``clustering``. Fewer than two distinct labels fall back to the item bootstrap. The sign
    test stays item-level.
    """
    if len(scores_a) != len(scores_b):
        raise ValueError("paired scores must have the same length")
    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)
    diffs = a - b
    codes = None
    if clusters is not None:
        if len(clusters) != len(scores_a):
            raise ValueError("one cluster label per example is required")
        codes = encode_clusters(clusters)
    clustering: ClusterStats | None = None
    if codes is not None and int(codes.max(initial=-1)) >= 1:
        method = "cluster-bootstrap"
        diff, lo, hi = cluster_bootstrap_ci(diffs, codes, num_resamples=num_resamples, seed=seed)
        clustering = cluster_stats(diffs, codes)
    else:
        tie_fraction = float(np.mean(diffs == 0.0)) if diffs.size else 0.0
        method = resolve_ci_method(ci_method, int(a.size), tie_fraction)
        diff, lo, hi = bootstrap_mean_ci(
            diffs.tolist(), num_resamples=num_resamples, seed=seed, method=method
        )
    wins = int((diffs > 0).sum())
    losses = int((diffs < 0).sum())
    return PairedComparison(
        n=int(a.size),
        mean_a=float(a.mean()) if a.size else 0.0,
        mean_b=float(b.mean()) if b.size else 0.0,
        diff=diff,
        diff_ci_lo=lo,
        diff_ci_hi=hi,
        wins=wins,
        losses=losses,
        ties=int(a.size) - wins - losses,
        sign_p=sign_test_p(wins, losses),
        ci_method=method,
        clustering=clustering,
    )


def randomization_test_p(
    diffs: Sequence[float] | np.ndarray,
    num_draws: int = 10000,
    seed: int = 0,
    exact_max_nonzero: int = 20,
) -> float:
    """Two-sided paired randomisation (sign-flip) test of mean(diffs) = 0.

    Under the null each per-example difference is equally likely to carry either
    sign, so the reference distribution of the sum is the sum over all 2^k sign
    assignments of the k nonzero differences (zeros never change the sum).
    p = P(|sum with random signs| >= |observed sum|).

    * k <= ``exact_max_nonzero`` (20): exact enumeration of all 2^k assignments.
    * k larger: Monte Carlo with ``num_draws`` seeded draws and the
      (count + 1) / (draws + 1) estimator, which is never 0 and is a valid p-value
      (Phipson & Smyth 2010).

    Smucker, Allan & Carterette (2007) recommend this test, or the bootstrap,
    over the sign and Wilcoxon tests for comparing retrieval/IR systems.

    Assumption: flipping the sign of a difference is the same as swapping the two
    models' scores in that example, so the reference distribution is exact only if
    each difference is symmetric around 0 under H0 (A_i, B_i exchangeable), which is
    stronger than "mean difference = 0". On skewed differences the test is
    anti-conservative (``evalkit stats-check``: type-I error 0.05 to 0.09 at nominal
    0.05 for n <= 240); :func:`skewness_warning` flags when to distrust it.
    """
    d = np.asarray(diffs, dtype=np.float64)
    d = d[np.abs(d) > 1e-12]
    k = int(d.size)
    if k == 0:
        return 1.0
    tol = 1e-9 * float(np.abs(d).sum())
    observed = abs(float(d.sum()))
    if k <= exact_max_nonzero:
        sums = np.zeros(1, dtype=np.float64)
        for x in d:
            sums = np.concatenate((sums + x, sums - x))
        return float(np.count_nonzero(np.abs(sums) >= observed - tol)) / sums.size
    rng = np.random.default_rng(seed)
    hits = 0
    done = 0
    chunk = max(1, 2_000_000 // k)  # bound the (draws x k) sign matrix to ~16 MB
    while done < num_draws:
        m = min(chunk, num_draws - done)
        signs = rng.integers(0, 2, size=(m, k)).astype(np.float64) * 2.0 - 1.0
        hits += int(np.count_nonzero(np.abs(signs @ d) >= observed - tol))
        done += m
    return (hits + 1) / (num_draws + 1)


def cluster_randomization_test_p(
    diffs: Sequence[float] | np.ndarray,
    clusters: Sequence[Hashable],
    num_draws: int = 10000,
    seed: int = 0,
    exact_max_nonzero: int = 20,
) -> float:
    """Two-sided paired randomisation test of mean(diffs) = 0 that flips whole clusters.

    Items in a cluster are correlated, so the exchangeable unit under H0 is the cluster:
    all differences in a cluster change sign together (swap A and B for the whole cluster).
    The sum over items is the sum of the cluster totals, so this is
    :func:`randomization_test_p` on the per-cluster sums (exact up to ``exact_max_nonzero``
    nonzero clusters, else Monte Carlo). With one cluster per item it equals the item-level
    test. The same symmetry assumption as there applies, at cluster level.
    """
    d = np.asarray(diffs, dtype=np.float64)
    if len(clusters) != d.size:
        raise ValueError("one cluster label per difference is required")
    sums, _ = cluster_sums(d, encode_clusters(clusters))
    return randomization_test_p(
        sums, num_draws=num_draws, seed=seed, exact_max_nonzero=exact_max_nonzero
    )


TIE_METHODS = ("signflip", "signtest", "boott_nz", "johnson_nz", "boott_nz_cal")
"""Tests of the mean that use only the non-tied pairs; candidates for the tie path of ``auto``
(``docs/protocol-ties.md``)."""
RAND_METHODS = ("auto", "signflip", "boott", "johnson", *TIE_METHODS[1:])
ASYMMETRIC_METHODS = ("boott", "johnson")
ASYMMETRIC_METHOD = "boott"
"""The test ``auto`` switches to when the asymmetry gate fires (chosen on development seed 1,
``docs/protocol-skew-fix.md``)."""
TIE_FALLBACKS = ("none", *TIE_METHODS)
TIE_FALLBACK = "none"
"""The test ``auto`` uses instead of :data:`ASYMMETRIC_METHOD` when the asymmetry gate fires and
more than :data:`TIE_GATE` of the differences are exactly zero; ``none`` keeps Phase M behaviour."""
TIE_GATE = 0.5
"""Share of exactly-zero differences above which the tie path applies."""
CAL_DRAWS = 399
"""Outer and inner resamples of :func:`bootstrap_t_calibrated_p` (at most)."""


def asymmetry_gate(diffs: Sequence[float] | np.ndarray) -> tuple[float, int, bool]:
    """(skewness of the nonzero differences, their count k, gate fires).

    The sign-flip test is exact for 0/1 scores (every nonzero ``|d|`` is equal, so it is the
    conditional McNemar test) and for symmetric differences. The gate fires when the scores
    are not of that equal-magnitude kind and ``k < 25 g^2`` (Cochran's rule for how many
    observations a mean needs at skewness ``g``), with ties removed first: zeros inflate the
    skewness of all differences, and a mostly-zero symmetric difference is still symmetric.
    """
    d = np.asarray(diffs, dtype=np.float64)
    d = d[np.abs(d) > 1e-12]
    k = int(d.size)
    if k < 3:
        return 0.0, k, False
    if float(np.ptp(np.abs(d))) <= 1e-9 * float(np.abs(d).max()):
        return 0.0, k, False
    g = sample_skewness(d)
    return g, k, bool(k < SKEW_RULE * g * g)


def bootstrap_t_test_p(
    diffs: Sequence[float] | np.ndarray, num_draws: int = 10000, seed: int = 0
) -> float:
    """Two-sided bootstrap-t test of mean(diffs) = 0 (Efron & Tibshirani 1993, ch. 16).

    ``t = mean / (sd / sqrt(n))``; the null distribution of ``t`` is that of the studentised
    mean of resamples from the mean-centred differences (so the resampling population has
    mean 0 and the observed skewness). ``p = (1 + #{|t*| >= |t|}) / (B + 1)`` over the
    resamples with a nonzero SD. Second-order accurate for the mean, which the sign-flip
    test is not when the differences are asymmetric. Constant nonzero differences have no
    spread to studentise and use the sign-flip test; all zeros give 1.
    """
    d = np.asarray(diffs, dtype=np.float64)
    n = int(d.size)
    if n == 0 or not np.any(np.abs(d) > 1e-12):
        return 1.0
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    if sd <= 1e-12 * float(np.abs(d).max()):
        return randomization_test_p(d, num_draws=num_draws, seed=seed)
    root_n = math.sqrt(n)
    mean = float(d.mean())
    t_obs = abs(mean) / (sd / root_n)
    centred = d - mean
    rng = np.random.default_rng(seed)
    chunk = max(1, 2_000_000 // n)
    hits = 0
    used = 0
    done = 0
    while done < num_draws:
        m = min(chunk, num_draws - done)
        res = centred[rng.integers(0, n, size=(m, n))]
        sd_star = res.std(axis=1, ddof=1)
        ok = sd_star > 1e-12 * sd
        t_star = np.abs(res.mean(axis=1)[ok]) / (sd_star[ok] / root_n)
        hits += int(np.count_nonzero(t_star >= t_obs - 1e-12))
        used += int(ok.sum())
        done += m
    if used == 0:
        return randomization_test_p(d, num_draws=num_draws, seed=seed)
    return (hits + 1) / (used + 1)


def johnson_test_p(diffs: Sequence[float] | np.ndarray) -> float:
    """Two-sided skewness-corrected t test of mean(diffs) = 0 (Johnson 1978; Hall 1992).

    The Edgeworth expansion ``P(T <= x) = Phi(x) + n^-1/2 (g/6)(2x^2 + 1) phi(x)`` is
    inverted by the monotone cubic ``G(x) = ((1 + a x)^3 - 1) / (3a) + a / 2`` with
    ``a = g / (3 sqrt(n))`` and ``g`` the sample skewness, so ``F(t) = Phi(G(t))`` and
    ``p = min(1, 2 min(F, 1 - F))``. Closed form, no resampling noise; ``g = 0`` is the
    normal-theory t test. Constant nonzero differences use the sign-flip test.
    """
    d = np.asarray(diffs, dtype=np.float64)
    n = int(d.size)
    if n == 0 or not np.any(np.abs(d) > 1e-12):
        return 1.0
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    if sd <= 1e-12 * float(np.abs(d).max()):
        return randomization_test_p(d)
    t = float(d.mean()) / (sd / math.sqrt(n))
    a = sample_skewness(d) / (3.0 * math.sqrt(n))
    g_t = t + a / 2.0 if abs(a) < 1e-12 else ((1.0 + a * t) ** 3 - 1.0) / (3.0 * a) + a / 2.0
    f = NormalDist().cdf(g_t)
    return float(min(1.0, 2.0 * min(f, 1.0 - f)))


def nonzero_differences(diffs: Sequence[float] | np.ndarray) -> np.ndarray:
    """The non-tied differences (``|d| > 1e-12``)."""
    d = np.asarray(diffs, dtype=np.float64)
    return d[np.abs(d) > 1e-12]


def tie_share(diffs: Sequence[float] | np.ndarray) -> float:
    """Share of the differences that are exactly zero (0 for an empty input)."""
    d = np.asarray(diffs, dtype=np.float64)
    return float(np.count_nonzero(np.abs(d) <= 1e-12)) / d.size if d.size else 0.0


def sign_test_nonzero_p(diffs: Sequence[float] | np.ndarray) -> float:
    """Exact two-sided sign test on the non-tied differences (:func:`sign_test_p`).

    Tests whether wins and losses are equally likely (the median), not whether the mean is
    zero, so it rejects mean-zero skewed differences.
    """
    nz = nonzero_differences(diffs)
    return sign_test_p(int(np.count_nonzero(nz > 0)), int(np.count_nonzero(nz < 0)))


def bootstrap_t_calibrated_p(
    diffs: Sequence[float] | np.ndarray, num_draws: int = 2000, seed: int = 0
) -> float:
    """Two-sided calibrated (double) bootstrap-t test of mean(diffs) = 0.

    Beran's (1987) prepivoting; Efron & Tibshirani (1993, ch. 18). ``t*`` comes from ``B``
    resamples of the mean-centred differences and ``p_obs = (1 + #{|t*| >= |t|}) / (B + 1)``
    is the single-bootstrap p. For each outer resample ``b`` another ``B`` resamples (from
    that sample, re-centred) give ``p*_b``; the calibrated p is
    ``(1 + #{p*_b <= p_obs}) / (B + 1)``, which removes the leading error term of ``p_obs``.
    ``B = min(num_draws, CAL_DRAWS)``. Constant nonzero differences use the sign-flip test.
    """
    d = np.asarray(diffs, dtype=np.float64)
    n = int(d.size)
    if n == 0 or not np.any(np.abs(d) > 1e-12):
        return 1.0
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    floor = 1e-12 * sd
    if sd <= 1e-12 * float(np.abs(d).max()):
        return randomization_test_p(d, num_draws=num_draws, seed=seed)
    b = max(99, min(num_draws, CAL_DRAWS))
    root_n = math.sqrt(n)
    mean = float(d.mean())
    t_obs = abs(mean) / (sd / root_n)
    rng = np.random.default_rng(seed)
    outer = (d - mean)[rng.integers(0, n, size=(b, n))]
    sd_o = outer.std(axis=1, ddof=1)
    ok = sd_o > floor
    outer, sd_o = outer[ok], sd_o[ok]
    m = int(outer.shape[0])
    if m == 0:
        return randomization_test_p(d, num_draws=num_draws, seed=seed)
    mean_o = outer.mean(axis=1)
    t_o = np.abs(mean_o) / (sd_o / root_n)
    p_obs = (int(np.count_nonzero(t_o >= t_obs - 1e-12)) + 1) / (m + 1)
    p_star = np.empty(m, dtype=np.float64)
    block = max(1, 4_000_000 // (b * n))  # bound the (block x b x n) inner array
    for lo in range(0, m, block):
        hi = min(m, lo + block)
        centred = outer[lo:hi] - mean_o[lo:hi, None]
        inner = centred[np.arange(hi - lo)[:, None, None], rng.integers(0, n, size=(hi - lo, b, n))]
        sd_i = inner.std(axis=2, ddof=1)
        t_i = np.where(
            sd_i > floor, np.abs(inner.mean(axis=2)) / (np.maximum(sd_i, floor) / root_n), 0.0
        )
        p_star[lo:hi] = (np.count_nonzero(t_i >= t_o[lo:hi, None] - 1e-12, axis=1) + 1) / (b + 1)
    return (int(np.count_nonzero(p_star <= p_obs + 1e-12)) + 1) / (m + 1)


def mean_test_p(
    diffs: Sequence[float] | np.ndarray,
    method: str = "auto",
    num_draws: int = 10000,
    seed: int = 0,
    fallback: str = ASYMMETRIC_METHOD,
    tie_fallback: str = TIE_FALLBACK,
    tie_gate: float = TIE_GATE,
) -> tuple[float, str]:
    """(two-sided p of mean(diffs) = 0, the concrete test used).

    ``signflip``: :func:`randomization_test_p` (exact for 0/1 and for symmetric
    differences, anti-conservative for skewed ones); ``boott``: :func:`bootstrap_t_test_p`;
    ``johnson``: :func:`johnson_test_p`. ``signtest``, ``boott_nz``, ``johnson_nz`` and
    ``boott_nz_cal`` use only the non-tied differences (H0 is equivalent to "the mean of the
    non-tied differences is 0", and the zeros only add noise to a studentised mean): the exact
    sign test, :func:`bootstrap_t_test_p`, :func:`johnson_test_p` and
    :func:`bootstrap_t_calibrated_p` on them. ``auto``: ``signflip`` unless
    :func:`asymmetry_gate` fires, then ``fallback`` (default :data:`ASYMMETRIC_METHOD`), or
    ``tie_fallback`` when it is not ``none`` and the share of zero differences exceeds
    ``tie_gate`` (:data:`TIE_FALLBACK`, :data:`TIE_GATE`).
    """
    if method not in RAND_METHODS:
        raise ValueError(f"unknown randomisation method {method!r}; choose from {RAND_METHODS}")
    if fallback not in ASYMMETRIC_METHODS:
        raise ValueError(f"unknown fallback {fallback!r}; choose from {ASYMMETRIC_METHODS}")
    if tie_fallback not in TIE_FALLBACKS:
        raise ValueError(f"unknown tie fallback {tie_fallback!r}; choose from {TIE_FALLBACKS}")
    if method == "auto":
        if not asymmetry_gate(diffs)[2]:
            method = "signflip"
        elif tie_fallback != "none" and tie_share(diffs) > tie_gate:
            method = tie_fallback
        else:
            method = fallback
    if method == "boott":
        return bootstrap_t_test_p(diffs, num_draws=num_draws, seed=seed), method
    if method == "johnson":
        return johnson_test_p(diffs), method
    if method in TIE_METHODS[1:]:
        nz = nonzero_differences(diffs)
        if nz.size < 2:
            return randomization_test_p(nz, num_draws=num_draws, seed=seed), method
        if method == "signtest":
            return sign_test_nonzero_p(nz), method
        if method == "boott_nz":
            return bootstrap_t_test_p(nz, num_draws=num_draws, seed=seed), method
        if method == "johnson_nz":
            return johnson_test_p(nz), method
        return bootstrap_t_calibrated_p(nz, num_draws=num_draws, seed=seed), method
    return randomization_test_p(diffs, num_draws=num_draws, seed=seed), method


def holm_bonferroni(p_values: Sequence[float]) -> list[float]:
    """Holm (1979) step-down adjusted p-values, returned in the input order.

    Sort ascending p_(1) <= ... <= p_(m); adj_(i) = max_{j<=i} min(1, (m - j + 1) p_(j)).
    Controls the family-wise error rate without any independence assumption.
    """
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[idx]))
        adjusted[idx] = running
    return adjusted


def _z_sum(alpha: float, power: float) -> float:
    nd = NormalDist()
    return nd.inv_cdf(1.0 - alpha / 2.0) + nd.inv_cdf(power)


def minimum_detectable_effect(
    sd_diff: float, n: int, alpha: float = 0.05, power: float = 0.8, deff: float = 1.0
) -> float:
    """Smallest true mean paired difference detectable with the given power.

    Normal approximation for a two-sided paired test with the SD of the
    per-example differences ``sd_diff``:

        MDE = (z_{1 - alpha/2} + z_{power}) * sd_diff / sqrt(n)

    (power analysis for paired model comparisons as recommended by Miller 2024,
    "Adding Error Bars to Evals", arXiv 2411.00640, sec. 4; standard result, see
    e.g. Cohen 1988.) With alpha = 0.05, power = 0.8 the multiplier is 2.8016. Clustered
    items (design effect
    ``deff = 1 + (m - 1) ICC``, :func:`evalkit.clustered.design_effect`) inflate the variance
    of the mean, so ``MDE = z * sd_diff * sqrt(deff / n)``. ``sd_diff`` is the total SD of
    the per-example differences (the naive one).
    """
    if n <= 0:
        return math.inf
    return _z_sum(alpha, power) * sd_diff * math.sqrt(deff / n)


def required_sample_size(
    sd_diff: float, effect: float, alpha: float = 0.05, power: float = 0.8, deff: float = 1.0
) -> int:
    """Examples needed to detect a mean paired difference of ``effect``.

    Same normal approximation as :func:`minimum_detectable_effect`, solved for n:

        n = ceil(((z_{1 - alpha/2} + z_{power}) * sd_diff / effect)^2)

    (Miller 2024, arXiv 2411.00640.) At least 2, since a paired SD needs two
    examples. ``effect`` must be nonzero. With clustered items the variance of the mean is
    inflated by the design effect ``deff = 1 + (m - 1) ICC`` (Kish 1965;
    :func:`evalkit.clustered.design_effect`), so the count is multiplied by it:
    ``n = ceil(deff * ((z_{1 - alpha/2} + z_{power}) * sd_diff / effect)^2)``.
    """
    if effect == 0:
        raise ValueError("effect must be nonzero")
    n = math.ceil(deff * (_z_sum(alpha, power) * sd_diff / abs(effect)) ** 2)
    return max(2, n)


def is_binary(values: Sequence[float] | np.ndarray) -> bool:
    """True when ``values`` is non-empty and every entry is exactly 0 or 1."""
    arr = np.asarray(values, dtype=np.float64)
    return bool(arr.size > 0 and np.all((arr == 0.0) | (arr == 1.0)))


def paired_binary_power(n: int, p_diff: float, p_disc: float, alpha: float = 0.05) -> float:
    """Power of the two-sided McNemar test for ``n`` pairs (Connor 1987).

    ``p_disc`` = P(A != B), the discordant-pair rate, ``p_diff`` = P(A=1, B=0) -
    P(A=0, B=1). Under H0 the difference of discordant counts has variance
    ``n * p_disc``, under H1 ``n * (p_disc - p_diff^2)``:

        power = Phi((sqrt(n)|d| - z sqrt(psi)) / s) + Phi((-sqrt(n)|d| - z sqrt(psi)) / s)

    with ``z = z_{1 - alpha/2}``, ``psi = p_disc``, ``s = sqrt(psi - d^2)``.
    """
    delta = abs(p_diff)
    if delta > p_disc + 1e-12:
        raise ValueError("|p_diff| cannot exceed p_disc")
    if n <= 0:
        return 0.0
    nd = NormalDist()
    z = nd.inv_cdf(1.0 - alpha / 2.0)
    shift = math.sqrt(n) * delta
    spread = math.sqrt(max(0.0, p_disc - delta * delta))
    if spread == 0.0:
        return 1.0 if shift > z * math.sqrt(p_disc) else 0.0
    top = z * math.sqrt(p_disc)
    return nd.cdf((shift - top) / spread) + nd.cdf((-shift - top) / spread)


EXACT_POWER_MAX_N = 5000
_SAWTOOTH_WINDOW = 60
_LOG_FACT: list[np.ndarray] = [np.zeros(1)]


def _log_factorials(n: int) -> np.ndarray:
    """``log(k!)`` for k = 0..n (a growing cache; the returned array may be longer)."""
    if _LOG_FACT[0].size <= n:
        size = max(n + 1, 2 * _LOG_FACT[0].size)
        out = np.zeros(size, dtype=np.float64)
        out[1:] = np.cumsum(np.log(np.arange(1, size, dtype=np.float64)))
        _LOG_FACT[0] = out
    return _LOG_FACT[0]


def _binom_pmf(n: int, p: float, log_fact: np.ndarray) -> np.ndarray:
    """Binomial(n, p) probabilities for k = 0..n (``log_fact`` covers at least n)."""
    out = np.zeros(n + 1, dtype=np.float64)
    if p <= 0.0:
        out[0] = 1.0
    elif p >= 1.0:
        out[n] = 1.0
    else:
        k = np.arange(n + 1)
        out = np.exp(
            log_fact[n] - log_fact[k] - log_fact[n - k] + k * math.log(p) + (n - k) * math.log1p(-p)
        )
    return out


@cache
def _sign_test_cutoff(m: int, alpha: float) -> int:
    """Largest c such that the exact two-sided sign test on ``m`` discordant pairs
    rejects whenever ``min(wins, losses) <= c`` (-1 when it never rejects).

    Same rule as :func:`sign_test_p`: reject when ``min(1, 2 P(Bin(m, 1/2) <= c)) < alpha``.
    Integer arithmetic up to 400 pairs, log-space floats above (same answer, no big ints).
    """
    if m > 400:
        log_fact = _log_factorials(m)
        ks = np.arange(m // 2 + 1)
        cdf = np.cumsum(np.exp(log_fact[m] - log_fact[ks] - log_fact[m - ks] - m * math.log(2.0)))
        return int(np.count_nonzero(np.minimum(1.0, 2.0 * cdf) < alpha)) - 1
    cum = 0
    term = 1  # C(m, 0)
    cutoff = -1
    for k in range(m // 2 + 1):
        cum += term
        if min(1.0, 2.0 * (cum / 2**m)) < alpha:
            cutoff = k
        else:
            break
        term = term * (m - k) // (k + 1)
    return cutoff


def paired_binary_power_exact(n: int, p_diff: float, p_disc: float, alpha: float = 0.05) -> float:
    """Exact power of the shipped test (exact two-sided sign test on the discordant pairs).

    For binary scores :func:`randomization_test_p` is the exact conditional McNemar
    test, so power is a binomial mixture (Duffy 1984, Biometrics 40:1005-1015): the
    number of discordant pairs is ``m ~ Bin(n, psi)`` with ``psi = p_disc``; given
    ``m``, the wins are ``Bin(m, (psi + d) / (2 psi))`` and the test rejects when
    ``min(wins, losses) <= c_m``, the sign-test cutoff for ``m`` pairs. Unlike
    :func:`paired_binary_power` it does not treat the discrete, conservative test as a
    continuous normal one.
    """
    delta = abs(p_diff)
    if delta > p_disc + 1e-12:
        raise ValueError("|p_diff| cannot exceed p_disc")
    if n <= 0 or p_disc <= 0.0:
        return 0.0
    psi = min(p_disc, 1.0)
    p_win = min(1.0, (psi + delta) / (2.0 * psi))
    log_fact = _log_factorials(n)
    weight = _binom_pmf(n, psi, log_fact)
    total = 0.0
    for m in np.nonzero(weight > 1e-16)[0]:
        cutoff = _sign_test_cutoff(int(m), alpha)
        if cutoff < 0:
            continue
        pmf = _binom_pmf(int(m), p_win, log_fact)
        total += float(weight[m]) * (
            float(pmf[: cutoff + 1].sum()) + float(pmf[m - cutoff :].sum())
        )
    return min(1.0, total)


def _connor_sample_size(psi: float, delta: float, alpha: float, power: float) -> int:
    nd = NormalDist()
    num = nd.inv_cdf(1.0 - alpha / 2.0) * math.sqrt(psi) + nd.inv_cdf(power) * math.sqrt(
        max(0.0, psi - delta * delta)
    )
    return max(2, math.ceil((num / delta) ** 2))


def required_sample_size_binary(
    p_disc: float,
    effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
    exact: bool = True,
    deff: float = 1.0,
) -> int:
    """Pairs needed to detect ``effect`` with the given power, for 0/1 scores.

    The independent-pairs answer of :func:`_required_pairs_binary` times the design effect
    ``deff`` (:func:`evalkit.clustered.design_effect`), rounded up: the number of *items*
    needed when they come in clusters. ``deff = 1`` (default) is the unclustered answer.
    See the helper for the formulas.
    """
    n = _required_pairs_binary(p_disc, effect, alpha, power, exact)
    return n if deff == 1.0 else max(2, math.ceil(n * deff))


def _required_pairs_binary(
    p_disc: float,
    effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
    exact: bool = True,
) -> int:
    """Independent pairs needed to detect ``effect`` with the given power, for 0/1 scores.

    ``psi`` = ``p_disc``, the discordant-pair rate P(A != B); ``d`` = ``effect`` =
    P(A=1, B=0) - P(A=0, B=1). Fewer discordant pairs than the effect is impossible,
    so psi is raised to |d| if smaller. At least 2.

    * ``exact=False``: Connor's (1987, Biometrics 43:207-211) closed form for the
      McNemar test, ``n = ceil((z_{1-a/2} sqrt(psi) + z_power sqrt(psi - d^2))^2 / d^2)``.
      Worked example (Machin et al. 2009, via MedCalc): shifts of 20% and 10%, so
      psi = 0.3, d = 0.1: n = 234.
    * ``exact=True`` (default): the smallest ``n`` whose exact power
      (:func:`paired_binary_power_exact`) reaches ``power``. ``evalkit stats-check`` found
      Connor's closed form optimistic for this discrete test (empirical power 0.74 to 0.79
      at its own n for 0.80). Exact power is not monotone in ``n`` (the rejection region
      jumps), so the search bisects to a crossing between 80% of Connor's n and above it,
      then returns the earliest n that reaches ``power`` within the 60 pairs below it
      (a larger n can dip back just below). Above ``EXACT_POWER_MAX_N`` = 5000 pairs
      the exact search is skipped and Connor's n is returned: there exact power is
      within 1 percentage point of the closed form (0.790 at n = 2614 for psi 0.3,
      d 0.03; 0.794 at n = 4359 for psi 0.5, d 0.03).
    """
    delta = abs(effect)
    if delta == 0:
        raise ValueError("effect must be nonzero")
    if delta > 1.0:
        raise ValueError("a difference of 0/1 scores cannot exceed 1")
    psi = max(p_disc, delta)
    n = _connor_sample_size(psi, delta, alpha, power)
    if not exact or n > EXACT_POWER_MAX_N:
        return n

    def reaches(m: int) -> bool:
        return paired_binary_power_exact(m, delta, psi, alpha) >= power

    lo = max(2, int(0.8 * n))
    if reaches(lo):
        while lo > 2 and reaches(lo - 1):
            lo -= 1
        return lo
    hi = n
    while not reaches(hi):  # lo fails; find some n that reaches
        lo, hi = hi, hi + max(2, n // 20)
    while hi - lo > 1:  # bisect to a crossing
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid
    # power is a sawtooth in n: take the earliest crossing in a window below the one found
    first = hi
    for m in range(max(2, hi - _SAWTOOTH_WINDOW), hi):
        if reaches(m):
            first = m
            break
    return first


def minimum_detectable_effect_binary(
    p_disc: float,
    n: int,
    alpha: float = 0.05,
    power: float = 0.8,
    exact: bool = True,
    deff: float = 1.0,
) -> float:
    """Smallest difference of 0/1 scores detected with the given power at ``n`` pairs.

    Solves, for ``d`` at the discordant rate ``psi = p_disc``, either Connor's relation
    ``sqrt(n) d = z sqrt(psi) + z_power sqrt(psi - d^2)`` (``exact=False``) or
    ``paired_binary_power_exact(n, d, psi) = power`` (default). Both sides increase
    with ``d``, so bisection finds the root. ``inf`` when even ``d = psi`` (every
    discordant pair favouring one model) is not detectable at this ``n``; 0 when there
    are no discordant pairs (nothing to resolve either way).

    ``deff`` > 1 is the design effect of clustered items: the formula is evaluated at the
    effective sample size ``round(n / deff)`` (at least 2). An approximation, not an exact
    clustered McNemar power.
    """
    if n <= 0:
        return math.inf
    if deff != 1.0:
        n = max(2, round(n / deff))
    psi = min(max(p_disc, 0.0), 1.0)
    if psi == 0.0:
        return 0.0
    exact = exact and n <= EXACT_POWER_MAX_N
    nd = NormalDist()
    z_a = nd.inv_cdf(1.0 - alpha / 2.0) * math.sqrt(psi)
    z_b = nd.inv_cdf(power)
    root_n = math.sqrt(n)

    def short(d: float) -> bool:
        """True when effect ``d`` is not yet detected with the target power."""
        if exact:
            return paired_binary_power_exact(n, d, psi, alpha) < power
        return root_n * d - z_a - z_b * math.sqrt(max(0.0, psi - d * d)) < 0.0

    if short(psi):
        return math.inf
    lo, hi = 0.0, psi
    for _ in range(50 if exact else 80):
        mid = 0.5 * (lo + hi)
        if short(mid):
            lo = mid
        else:
            hi = mid
    return hi


SKEW_RULE = 25.0


def sample_skewness(values: Sequence[float] | np.ndarray) -> float:
    """Moment skewness ``m3 / m2^1.5`` (0 when the values do not vary)."""
    x = np.asarray(values, dtype=np.float64)
    if x.size == 0:
        return 0.0
    c = x - x.mean()
    m2 = float(np.mean(c * c))
    if m2 <= 1e-24:
        return 0.0
    return float(np.mean(c**3)) / float(m2**1.5)


def skewness_warning(diffs: Sequence[float] | np.ndarray) -> tuple[float, bool]:
    """(skewness, warn) for the per-example differences behind a randomisation test.

    ``warn`` when ``n < 25 * skewness^2``: Cochran's (1977, Sampling Techniques, 3rd
    ed., p. 42; Sugden, Smith & Jones 2000) rule for the sample size at which a
    normal-theory inference on a mean survives skew. A heuristic: it was derived for
    the t interval, here it flags where the sign-flip test's symmetry assumption is
    likely to matter (``evalkit stats-check`` measures how well).
    """
    x = np.asarray(diffs, dtype=np.float64)
    g = sample_skewness(x)
    return g, bool(x.size < SKEW_RULE * g * g)


@dataclass(frozen=True)
class PairResolution:
    """One model pair: paired statistics, corrected p-value, power, verdict.

    ``binary`` marks pairs of 0/1 scores, for which ``mde`` and ``n_needed`` come from
    the McNemar design formula (Connor 1987) at the observed discordant rate
    (``wins + losses`` over ``n``) instead of the normal approximation with
    ``sd_diff``. ``skew_warning`` is :func:`skewness_warning` on the differences.
    """

    model_a: str
    model_b: str
    n: int
    mean_a: float
    mean_b: float
    diff: float
    diff_ci_lo: float
    diff_ci_hi: float
    wins: int
    losses: int
    ties: int
    sign_p: float
    rand_p: float
    holm_p: float
    sd_diff: float
    mde: float
    n_needed: int | None  # None when the target effect is 0
    resolved: bool
    binary: bool
    skewness: float
    skew_warning: bool
    ci_method: str
    clustering: ClusterStats | None = None
    p_method: str = "signflip"


@dataclass(frozen=True)
class _PairStats:
    comparison: PairedComparison
    rand_p: float
    sd: float
    binary: bool
    skewness: float
    skew_warning: bool
    p_method: str


def compare_pairs(
    scores: Mapping[str, Mapping[object, float]],
    pairs: Sequence[tuple[str, str]],
    alpha: float = 0.05,
    power: float = 0.8,
    effect: float | None = None,
    num_resamples: int = 10000,
    num_draws: int = 10000,
    seed: int = 0,
    ci_method: str = "auto",
    with_power: bool = True,
    clusters: Mapping[Any, Hashable] | None = None,
    rand_method: str = "auto",
    rand_fallback: str = ASYMMETRIC_METHOD,
    rand_tie_fallback: str = TIE_FALLBACK,
    rand_tie_gate: float = TIE_GATE,
) -> list[PairResolution]:
    """Paired resolvability analysis for ``pairs`` (A, B) of models.

    ``scores[model][example_key]`` is the per-example score. Each pair is analysed on
    the examples both models were scored on (micro average over those examples).
    Holm-Bonferroni runs over exactly the pairs passed in, so the family is the
    caller's choice. ``effect`` is the target difference for ``n_needed`` (default:
    the observed |mean difference|; None result when that is 0). A pair is
    ``resolved`` when its Holm-adjusted randomisation p < ``alpha``.

    MDE and ``n_needed``: for pairs where both models' scores are all 0/1, the exact
    conditional McNemar power (:func:`paired_binary_power_exact`, discordant rate
    observed); otherwise the normal approximation with the SD of the differences.
    ``with_power=False`` skips both (``mde`` is NaN, ``n_needed`` None) for callers that
    only need p-values. ``ci_method`` is the bootstrap CI method (see
    :func:`bootstrap_mean_ci`).

    ``clusters`` maps an example key to its cluster label (an example without an entry is its
    own cluster). When a pair's examples fall into at least two clusters the analysis is
    clustered: the CI is the cluster bootstrap, ``rand_p`` is the cluster sign-flip test
    (:func:`cluster_randomization_test_p`), and the power figures use the design effect
    ``1 + (m - 1) ICC`` estimated from the differences (:func:`evalkit.clustered.cluster_stats`).
    ``PairResolution.clustering`` then carries the naive and clustered SE. ``ci_method`` and
    the sign test stay item-level.
    """
    stats: list[_PairStats] = []
    for a_name, b_name in pairs:
        sa, sb = scores[a_name], scores[b_name]
        keys = sorted((k for k in sa if k in sb), key=repr)
        va = [sa[k] for k in keys]
        vb = [sb[k] for k in keys]
        labels: list[Hashable] | None = None
        if clusters is not None:
            labels = [clusters.get(k, ("\0singleton", k)) for k in keys]
        c = paired_comparison(
            va, vb, num_resamples=num_resamples, seed=seed, ci_method=ci_method, clusters=labels
        )
        diffs = np.asarray(va, dtype=np.float64) - np.asarray(vb, dtype=np.float64)
        if labels is not None and c.clustering is not None:
            p = cluster_randomization_test_p(diffs, labels, num_draws=num_draws, seed=seed)
            used = "cluster-signflip"
        else:
            p, used = mean_test_p(
                diffs,
                rand_method,
                num_draws=num_draws,
                seed=seed,
                fallback=rand_fallback,
                tie_fallback=rand_tie_fallback,
                tie_gate=rand_tie_gate,
            )
        sd = float(diffs.std(ddof=1)) if diffs.size > 1 else 0.0
        skew, warn = skewness_warning(diffs)
        stats.append(_PairStats(c, p, sd, is_binary(va) and is_binary(vb), skew, warn, used))
    holm = holm_bonferroni([s.rand_p for s in stats])
    out: list[PairResolution] = []
    for (a_name, b_name), s, hp in zip(pairs, stats, holm, strict=True):
        c = s.comparison
        deff = c.clustering.deff if c.clustering is not None else 1.0
        target = abs(c.diff) if effect is None else abs(effect)
        mde: float
        needed: int | None
        if not with_power:
            mde, needed = math.nan, None
        elif s.binary:
            psi = (c.wins + c.losses) / c.n
            mde = minimum_detectable_effect_binary(psi, c.n, alpha, power, deff=deff)
            needed = (
                required_sample_size_binary(psi, target, alpha, power, deff=deff)
                if target > 1e-12
                else None
            )
        else:
            mde = minimum_detectable_effect(s.sd, c.n, alpha, power, deff=deff)
            needed = (
                required_sample_size(s.sd, target, alpha, power, deff=deff)
                if target > 1e-12
                else None
            )
        out.append(
            PairResolution(
                model_a=a_name,
                model_b=b_name,
                n=c.n,
                mean_a=c.mean_a,
                mean_b=c.mean_b,
                diff=c.diff,
                diff_ci_lo=c.diff_ci_lo,
                diff_ci_hi=c.diff_ci_hi,
                wins=c.wins,
                losses=c.losses,
                ties=c.ties,
                sign_p=c.sign_p,
                rand_p=s.rand_p,
                holm_p=hp,
                sd_diff=s.sd,
                mde=mde,
                n_needed=needed,
                resolved=hp < alpha,
                binary=s.binary,
                skewness=s.skewness,
                skew_warning=s.skew_warning,
                ci_method=c.ci_method,
                clustering=c.clustering,
                p_method=s.p_method,
            )
        )
    return out
