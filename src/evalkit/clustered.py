"""Clustered standard errors, cluster bootstrap, ICC and design effect (numpy only).

Eval items often share a source (questions about one passage, items from one document), so
their scores are correlated and ``s / sqrt(n)`` understates the uncertainty of a mean.
Miller (2024, "Adding Error Bars to Evals", arXiv 2411.00640, sec. 3.2) gives the clustered
standard error of a mean

    SE_clustered = sqrt( SE_CLT^2 + (1/n^2) sum_c sum_i sum_{j != i} (s_ic - s_bar)(s_jc - s_bar) )

with ``SE_CLT^2 = Var(s) / n`` (unbiased variance), ``s_ic`` the score of item ``i`` in cluster
``c``, ``s_bar`` the grand mean and the double sum over ordered pairs of distinct items in the
same cluster. :func:`clustered_se` computes exactly this; for a mean of per-item *differences*
it is the SE of a paired difference.

With few clusters that SE is slightly low and a normal interval undercovers. The CR1-style
small-sample correction (Cameron & Miller 2015) multiplies the SE by ``sqrt(C / (C - 1))`` and
uses ``t(C - 1)`` instead of the normal quantile in :func:`clustered_normal_ci`. It is the
default (``small_sample=True``; ``small_sample=False`` gives Miller's formula exactly):
``docs/protocol-cluster-small-sample.md`` pre-registered the test and its adoption rule, met on
all three fresh seeds.

Clusters are given as one label per item (any hashable). An item without a cluster is the
caller's to turn into a singleton label; with every item its own cluster the clustered SE
equals the naive one.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from statistics import NormalDist

import numpy as np


def encode_clusters(labels: Sequence[Hashable]) -> np.ndarray:
    """Dense integer codes 0..C-1 for ``labels``, in order of first appearance."""
    seen: dict[Hashable, int] = {}
    return np.fromiter(
        (seen.setdefault(label, len(seen)) for label in labels), dtype=np.int64, count=len(labels)
    )


def cluster_sums(
    values: Sequence[float] | np.ndarray, codes: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(sum of ``values``, number of items) per cluster code."""
    x = np.asarray(values, dtype=np.float64)
    return np.bincount(codes, weights=x), np.bincount(codes).astype(np.float64)


def naive_se(values: Sequence[float] | np.ndarray) -> float:
    """``s / sqrt(n)`` with the unbiased SD; 0 for fewer than two values."""
    x = np.asarray(values, dtype=np.float64)
    if x.size < 2:
        return 0.0
    return float(x.std(ddof=1)) / math.sqrt(x.size)


def clustered_se(
    values: Sequence[float] | np.ndarray, codes: np.ndarray, small_sample: bool = True
) -> float:
    """Clustered SE of the mean of ``values`` (Miller 2024, formula in the module docstring).

    Uses ``sum_{i != j in c} e_i e_j = (sum_i e_i)^2 - sum_i e_i^2`` with ``e = s - s_bar``.
    Clipped at 0 (the cross term can be negative when scores within clusters are negatively
    correlated). ``small_sample`` (default) multiplies the SE by ``sqrt(C / (C - 1))`` (CR1);
    ``False`` is Miller's formula as published. Needs at least two clusters.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size != codes.size:
        raise ValueError("values and cluster codes must have the same length")
    c = int(codes.max(initial=-1)) + 1
    if c < 2:
        raise ValueError("clustered SE needs at least two clusters")
    n = x.size
    e = x - x.mean()
    sq = float(e @ e)
    by_cluster = np.bincount(codes, weights=e)
    cross = float(by_cluster @ by_cluster) - sq
    var = sq / (n * (n - 1)) + cross / (n * n)
    if small_sample:
        var *= c / (c - 1.0)
    return math.sqrt(max(var, 0.0))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction of the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function ``I_x(a, b)`` for ``0 <= x <= 1``."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


@lru_cache(maxsize=256)
def t_critical(df: int, confidence_level: float = 0.95) -> float:
    """Two-sided critical value of Student's t with ``df`` degrees of freedom.

    ``P(|T| <= t) = confidence_level``, by bisection on the incomplete beta function
    (``P(|T| > t) = I_x(df / 2, 1 / 2)`` with ``x = df / (df + t^2)``). Accurate to about 1e-12.
    """
    if df < 1:
        raise ValueError("degrees of freedom must be at least 1")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    alpha = 1.0 - confidence_level
    lo, hi = 0.0, max(2.0, NormalDist().inv_cdf(1.0 - alpha / 2.0))
    while _betainc(df / 2.0, 0.5, df / (df + hi * hi)) > alpha:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _betainc(df / 2.0, 0.5, df / (df + mid * mid)) > alpha:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13 * hi:
            break
    return 0.5 * (lo + hi)


def clustered_normal_ci(
    values: Sequence[float] | np.ndarray,
    codes: np.ndarray,
    confidence_level: float = 0.95,
    small_sample: bool = True,
) -> tuple[float, float, float]:
    """Mean and the interval ``mean +/- crit * SE_clustered``.

    ``small_sample`` (default, CR1-style): the SE times ``sqrt(C / (C - 1))`` and the
    ``t(C - 1)`` quantile. ``False``: Miller's SE and the normal quantile. Needs at least two
    clusters.
    """
    x = np.asarray(values, dtype=np.float64)
    se = clustered_se(x, codes, small_sample=small_sample)
    c = int(codes.max()) + 1
    crit = (
        t_critical(c - 1, confidence_level)
        if small_sample
        else NormalDist().inv_cdf(0.5 + confidence_level / 2.0)
    )
    mean = float(x.mean())
    return (mean, mean - crit * se, mean + crit * se)


def cluster_bootstrap_means(
    sums: np.ndarray, sizes: np.ndarray, num_resamples: int, rng: np.random.Generator
) -> np.ndarray:
    """Means of ``num_resamples`` cluster-bootstrap resamples (total score / total items).

    Each resample draws ``C`` clusters with replacement from the per-cluster ``sums`` and
    ``sizes`` (see :func:`cluster_sums`). Draws are made in chunks that bound the index matrix
    to about 16 MB; the stream of random numbers depends only on ``rng``, ``C`` and
    ``num_resamples``.
    """
    c = sums.size
    means = np.empty(num_resamples, dtype=np.float64)
    chunk = max(1, 2_000_000 // c)
    for start in range(0, num_resamples, chunk):
        m = min(chunk, num_resamples - start)
        idx = rng.integers(0, c, size=(m, c))
        means[start : start + m] = sums[idx].sum(axis=1) / sizes[idx].sum(axis=1)
    return means


def cluster_bootstrap_ci(
    values: Sequence[float] | np.ndarray,
    codes: np.ndarray,
    num_resamples: int = 10000,
    confidence_level: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Mean and percentile CI from resampling whole clusters with replacement.

    Each resample draws ``C`` clusters (``C`` = number of clusters) and recomputes the mean
    as total score over total items, so unequal cluster sizes are handled. With every item
    its own cluster this is the ordinary item bootstrap. Needs at least two clusters.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size != codes.size:
        raise ValueError("values and cluster codes must have the same length")
    sums, sizes = cluster_sums(x, codes)
    c = sums.size
    if c < 2:
        raise ValueError("cluster bootstrap needs at least two clusters")
    mean = float(x.mean())
    if num_resamples <= 0:
        return (mean, mean, mean)
    means = cluster_bootstrap_means(sums, sizes, num_resamples, np.random.default_rng(seed))
    alpha = 1.0 - confidence_level
    lo = float(np.percentile(means, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(means, 100.0 * (1.0 - alpha / 2.0)))
    return (mean, lo, hi)


def effective_cluster_size(codes: np.ndarray) -> float:
    """``sum_c m_c^2 / N``: the cluster size that enters the design effect.

    Equals ``m`` for equal clusters and ``mean(m) (1 + cv^2)`` for unequal ones (Eldridge,
    Ashby & Kerry 2006, the design effect for unequal cluster sizes). 1 for singletons.
    """
    sizes = np.bincount(codes).astype(np.float64)
    return float((sizes * sizes).sum() / sizes.sum())


def estimate_icc(values: Sequence[float] | np.ndarray, codes: np.ndarray) -> float:
    """One-way ANOVA estimator of the intra-cluster correlation (Searle 1971; Donner 1986).

    ``ICC = (MSB - MSW) / (MSB + (n0 - 1) MSW)`` with ``n0 = (N - sum m_c^2 / N) / (C - 1)``.
    Negative estimates are clipped to 0 (a design effect below 1 is never used for planning);
    0 when there is one cluster, only singletons, or no variation.
    """
    x = np.asarray(values, dtype=np.float64)
    sums, sizes = cluster_sums(x, codes)
    c, n = sums.size, x.size
    if c < 2 or c == n:
        return 0.0
    grand = float(x.mean())
    means = sums / sizes
    msb = float((sizes * (means - grand) ** 2).sum()) / (c - 1)
    msw = float(((x - means[codes]) ** 2).sum()) / (n - c)
    n0 = (n - float((sizes * sizes).sum()) / n) / (c - 1)
    denom = msb + (n0 - 1.0) * msw
    if denom <= 0.0:
        return 0.0
    return min(1.0, max(0.0, (msb - msw) / denom))


def design_effect(m: float, icc: float) -> float:
    """``DEFF = 1 + (m - 1) * ICC``: the factor by which clustering inflates the variance of a
    mean (Kish 1965). ``m`` is the (effective) cluster size, ``icc`` is clipped to [0, 1]
    and ``m`` to at least 1, so the result is at least 1.
    """
    return 1.0 + (max(m, 1.0) - 1.0) * min(1.0, max(0.0, icc))


@dataclass(frozen=True)
class ClusterStats:
    """Naive and clustered SE of a mean (of scores or of paired differences) plus the ICC."""

    n_clusters: int
    naive_se: float
    cluster_se: float
    icc: float
    deff: float

    @property
    def se_ratio(self) -> float:
        """Clustered over naive SE (NaN when the naive SE is 0)."""
        return self.cluster_se / self.naive_se if self.naive_se > 0.0 else math.nan


def cluster_stats(
    values: Sequence[float] | np.ndarray, codes: np.ndarray, small_sample: bool = True
) -> ClusterStats:
    """:class:`ClusterStats` of ``values`` (``small_sample``: CR1 clustered SE); needs at least
    two clusters."""
    icc = estimate_icc(values, codes)
    return ClusterStats(
        n_clusters=int(codes.max()) + 1,
        naive_se=naive_se(values),
        cluster_se=clustered_se(values, codes, small_sample),
        icc=icc,
        deff=design_effect(effective_cluster_size(codes), icc),
    )
