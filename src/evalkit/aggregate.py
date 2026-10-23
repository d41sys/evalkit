from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np

CI_METHODS = ("auto", "percentile", "bca", "studentized")
SMALL_N_CI = 400
"""``method="auto"`` uses :data:`SMALL_N_METHOD` below this many examples, else percentile.

At n = 400 the percentile interval's normal-theory coverage shortfall (Hesterberg 2015:
narrowness factor sqrt((n-1)/n) and z instead of t) is 0.1 percentage point."""
SMALL_N_METHOD = "bca"


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


def resolve_ci_method(method: str, n: int) -> str:
    """The concrete interval method ``method`` means for ``n`` examples (``auto`` resolved)."""
    if method not in CI_METHODS:
        raise ValueError(f"unknown CI method {method!r}; choose from {CI_METHODS}")
    if method == "auto":
        return SMALL_N_METHOD if n < SMALL_N_CI else "percentile"
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
) -> tuple[float, float, float]:
    """Macro mean with a stratified bootstrap CI: resample examples within each task,
    then average the per-task means, so the interval matches the macro statistic.

    Scores are sorted per task first, so the result does not depend on the order
    records arrived in (e.g. thread completion order)."""
    tasks = [np.sort(np.asarray(task_scores[t], dtype=np.float64)) for t in sorted(task_scores)]
    tasks = [a for a in tasks if a.size > 0]
    if not tasks:
        return (0.0, 0.0, 0.0)
    point = float(np.mean([a.mean() for a in tasks]))
    if num_resamples <= 0:
        return (point, point, point)
    rng = np.random.default_rng(seed)
    per_task = np.stack(
        [rng.choice(a, size=(num_resamples, a.size), replace=True).mean(axis=1) for a in tasks]
    )
    macro = per_task.mean(axis=0)
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


@dataclass
class LeaderboardReport:
    models: list[ModelSummary]

    def to_markdown(self) -> str:
        # Sort models descending by macro_mean then elo_rating
        ranked = sorted(self.models, key=lambda m: (-m.macro_mean, -m.elo_rating, m.model_name))
        grouped = any(m.tie_group is not None for m in ranked)
        lines: list[str] = [
            "# Evaluation Leaderboard",
            "",
            (
                "| Rank | Model | Macro Mean | 95% CI | Win Rate | Elo Rating | "
                "ECE (15 bins) | Brier | Tasks Evaluated |" + (" Tie group |" if grouped else "")
            ),
            (
                "|------|-------|------------|--------|----------|------------|"
                "---------------|-------|-----------------|" + ("------------|" if grouped else "")
            ),
        ]
        for rank, m in enumerate(ranked, start=1):
            ci_str = f"[{m.ci_lower:.3f}, {m.ci_upper:.3f}]"
            tasks_count = len(m.per_task_means)
            group_cell = f" {m.tie_group if m.tie_group is not None else '-'} |" if grouped else ""
            lines.append(
                f"| {rank} | {m.model_name} | {m.macro_mean:.3f} | {ci_str} | {m.win_rate:.3f} | "
                f"{m.elo_rating:.1f} | {m.ece:.3f} | {m.brier:.3f} | {tasks_count} |" + group_cell
            )
        if grouped:
            lines.extend(
                [
                    "",
                    "Tie group: a model joins the group of the model ranked directly "
                    "above it unless the paired randomisation test on their per-example "
                    "differences is resolved (Holm-adjusted p < 0.05 over the adjacent pairs). "
                    "Models sharing a group are not separated by this data.",
                ]
            )

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
    """Model A vs model B on the same examples."""

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


def paired_comparison(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    num_resamples: int = 10000,
    seed: int = 0,
    ci_method: str = "auto",
) -> PairedComparison:
    """Paired bootstrap CI on mean(A - B) plus an exact sign test.

    Resampling the per-example differences keeps the pairing, so example difficulty
    cancels out instead of widening the interval. ``ci_method`` is passed to
    :func:`bootstrap_mean_ci` (default ``auto``: BCa below 400 examples).
    """
    if len(scores_a) != len(scores_b):
        raise ValueError("paired scores must have the same length")
    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)
    diffs = a - b
    diff, lo, hi = bootstrap_mean_ci(
        diffs.tolist(), num_resamples=num_resamples, seed=seed, method=ci_method
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
        ci_method=resolve_ci_method(ci_method, int(a.size)),
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
    sd_diff: float, n: int, alpha: float = 0.05, power: float = 0.8
) -> float:
    """Smallest true mean paired difference detectable with the given power.

    Normal approximation for a two-sided paired test with the SD of the
    per-example differences ``sd_diff``:

        MDE = (z_{1 - alpha/2} + z_{power}) * sd_diff / sqrt(n)

    (power analysis for paired model comparisons as recommended by Miller 2024,
    "Adding Error Bars to Evals", arXiv 2411.00640, sec. 4; standard result, see
    e.g. Cohen 1988.) With alpha = 0.05, power = 0.8 the multiplier is 2.8016.
    """
    if n <= 0:
        return math.inf
    return _z_sum(alpha, power) * sd_diff / math.sqrt(n)


def required_sample_size(
    sd_diff: float, effect: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Examples needed to detect a mean paired difference of ``effect``.

    Same normal approximation as :func:`minimum_detectable_effect`, solved for n:

        n = ceil(((z_{1 - alpha/2} + z_{power}) * sd_diff / effect)^2)

    (Miller 2024, arXiv 2411.00640.) At least 2, since a paired SD needs two
    examples. ``effect`` must be nonzero.
    """
    if effect == 0:
        raise ValueError("effect must be nonzero")
    n = math.ceil((_z_sum(alpha, power) * sd_diff / abs(effect)) ** 2)
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


def required_sample_size_binary(
    p_disc: float, effect: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Pairs needed for the McNemar test to detect ``effect`` with the given power.

    Connor (1987, Biometrics 43:207-211), eq. for the paired-sample design:

        n = ceil((z_{1 - alpha/2} sqrt(psi) + z_{power} sqrt(psi - d^2))^2 / d^2)

    ``psi`` = ``p_disc``, the discordant-pair rate P(A != B); ``d`` = ``effect`` =
    P(A=1, B=0) - P(A=0, B=1). Worked example (Machin et al. 2009, via MedCalc):
    shifts of 20% and 10%, so psi = 0.3, d = 0.1: n = 234. Fewer discordant pairs than
    the effect is impossible, so psi is raised to |d| if smaller. At least 2.
    """
    delta = abs(effect)
    if delta == 0:
        raise ValueError("effect must be nonzero")
    if delta > 1.0:
        raise ValueError("a difference of 0/1 scores cannot exceed 1")
    psi = max(p_disc, delta)
    nd = NormalDist()
    num = nd.inv_cdf(1.0 - alpha / 2.0) * math.sqrt(psi) + nd.inv_cdf(power) * math.sqrt(
        max(0.0, psi - delta * delta)
    )
    return max(2, math.ceil((num / delta) ** 2))


def minimum_detectable_effect_binary(
    p_disc: float, n: int, alpha: float = 0.05, power: float = 0.8
) -> float:
    """Smallest difference of 0/1 scores the McNemar test detects with the given power.

    Solves Connor's relation ``sqrt(n) d = z sqrt(psi) + z_power sqrt(psi - d^2)`` for
    ``d`` at the discordant rate ``psi = p_disc`` (the left side minus the right is
    increasing in ``d``, so bisection finds the unique root). ``inf`` when even
    ``d = psi`` (every discordant pair favouring one model) is not detectable at this
    ``n``; 0 when there are no discordant pairs (nothing to resolve either way).
    """
    if n <= 0:
        return math.inf
    psi = min(max(p_disc, 0.0), 1.0)
    if psi == 0.0:
        return 0.0
    nd = NormalDist()
    z_a = nd.inv_cdf(1.0 - alpha / 2.0) * math.sqrt(psi)
    z_b = nd.inv_cdf(power)
    root_n = math.sqrt(n)

    def gap(d: float) -> float:
        return root_n * d - z_a - z_b * math.sqrt(max(0.0, psi - d * d))

    if gap(psi) < 0.0:
        return math.inf
    lo, hi = 0.0, psi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if gap(mid) < 0.0:
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


@dataclass(frozen=True)
class _PairStats:
    comparison: PairedComparison
    rand_p: float
    sd: float
    binary: bool
    skewness: float
    skew_warning: bool


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
) -> list[PairResolution]:
    """Paired resolvability analysis for ``pairs`` (A, B) of models.

    ``scores[model][example_key]`` is the per-example score. Each pair is analysed on
    the examples both models were scored on (micro average over those examples).
    Holm-Bonferroni runs over exactly the pairs passed in, so the family is the
    caller's choice. ``effect`` is the target difference for ``n_needed`` (default:
    the observed |mean difference|; None result when that is 0). A pair is
    ``resolved`` when its Holm-adjusted randomisation p < ``alpha``.

    MDE and ``n_needed``: for pairs where both models' scores are all 0/1, Connor's
    McNemar formulas at the observed discordant rate; otherwise the normal
    approximation with the SD of the differences. ``ci_method`` is the bootstrap CI
    method (see :func:`bootstrap_mean_ci`).
    """
    stats: list[_PairStats] = []
    for a_name, b_name in pairs:
        sa, sb = scores[a_name], scores[b_name]
        keys = sorted((k for k in sa if k in sb), key=repr)
        va = [sa[k] for k in keys]
        vb = [sb[k] for k in keys]
        c = paired_comparison(va, vb, num_resamples=num_resamples, seed=seed, ci_method=ci_method)
        diffs = np.asarray(va, dtype=np.float64) - np.asarray(vb, dtype=np.float64)
        p = randomization_test_p(diffs, num_draws=num_draws, seed=seed)
        sd = float(diffs.std(ddof=1)) if diffs.size > 1 else 0.0
        skew, warn = skewness_warning(diffs)
        stats.append(_PairStats(c, p, sd, is_binary(va) and is_binary(vb), skew, warn))
    holm = holm_bonferroni([s.rand_p for s in stats])
    out: list[PairResolution] = []
    for (a_name, b_name), s, hp in zip(pairs, stats, holm, strict=True):
        c = s.comparison
        target = abs(c.diff) if effect is None else abs(effect)
        if s.binary:
            psi = (c.wins + c.losses) / c.n
            mde = minimum_detectable_effect_binary(psi, c.n, alpha, power)
            needed = (
                required_sample_size_binary(psi, target, alpha, power) if target > 1e-12 else None
            )
        else:
            mde = minimum_detectable_effect(s.sd, c.n, alpha, power)
            needed = required_sample_size(s.sd, target, alpha, power) if target > 1e-12 else None
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
            )
        )
    return out
