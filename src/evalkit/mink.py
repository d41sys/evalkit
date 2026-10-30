"""Min-K% Prob (Shi et al. 2023, arXiv 2310.16789) and the statistics around it.

Numpy-only. The per-token log-probabilities come from elsewhere (``scripts/mink_demo.py
score`` runs a local model); this module only turns them into scores and compares two groups.
Protocol: ``docs/protocol-mink.md``.

A DEMO of the method on a tiny model, not a contamination audit of any model or benchmark.
"""

from __future__ import annotations

import re
import zlib
from collections import Counter
from collections.abc import Callable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

_NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")

FloatArray = NDArray[np.float64]


def min_k_prob(token_logprobs: ArrayLike, k: float = 20.0) -> float:
    """Mean of the lowest ``k`` percent of the token log-probabilities.

    ``k`` is a percentage in ``(0, 100]``. The number of tokens averaged is
    ``max(1, floor(n * k / 100))`` (the ``int(len * ratio)`` rule of the reference code, with a
    floor of one token). A higher value means the text is more likely a training member.
    """
    if not 0.0 < k <= 100.0:
        raise ValueError(f"k must be in (0, 100], got {k}")
    lp = np.asarray(token_logprobs, dtype=np.float64)
    if lp.ndim != 1 or lp.size == 0:
        raise ValueError("token_logprobs must be a non-empty 1-D sequence")
    n_low = max(1, int(lp.size * k / 100.0))
    return float(np.partition(lp, n_low - 1)[:n_low].mean())


def mean_logprob(token_logprobs: ArrayLike) -> float:
    """Mean token log-probability (negative log-perplexity): the plain likelihood baseline."""
    lp = np.asarray(token_logprobs, dtype=np.float64)
    if lp.ndim != 1 or lp.size == 0:
        raise ValueError("token_logprobs must be a non-empty 1-D sequence")
    return float(lp.mean())


def zlib_length(text: str) -> int:
    """Bytes of the zlib (level 9) compression of ``text``: the complexity reference."""
    return len(zlib.compress(text.encode("utf-8"), 9))


def zlib_ratio(token_logprobs: ArrayLike, text: str) -> float:
    """``sum(logprob) / zlib_len``: likelihood relative to compressibility (Carlini et al. 2021).

    The sum is negative, so a higher (less negative) value means the text is more probable than
    its compressed size suggests.
    """
    lp = np.asarray(token_logprobs, dtype=np.float64)
    return float(lp.sum() / zlib_length(text))


def numbers_multiset(text: str) -> Counter[str]:
    """Multiset of the numbers in ``text`` (digit tokens, thousands commas removed)."""
    return Counter(m.replace(",", "") for m in _NUMBER.findall(text))


def same_numbers(a: str, b: str) -> bool:
    """True when ``a`` and ``b`` contain the same multiset of numbers."""
    return numbers_multiset(a) == numbers_multiset(b)


def _average_ranks(x: FloatArray) -> FloatArray:
    order = np.argsort(x, kind="mergesort")
    sorted_x = x[order]
    ranks = np.empty(x.size, dtype=np.float64)
    start = 0
    while start < x.size:
        end = start
        while end + 1 < x.size and sorted_x[end + 1] == sorted_x[start]:
            end += 1
        ranks[order[start : end + 1]] = (start + end) / 2.0 + 1.0
        start = end + 1
    return ranks


def auroc(pos: ArrayLike, neg: ArrayLike) -> float:
    """P(score_pos > score_neg) + 0.5 P(tie): the Mann-Whitney AUROC with average-rank ties."""
    p = np.asarray(pos, dtype=np.float64)
    q = np.asarray(neg, dtype=np.float64)
    if p.ndim != 1 or q.ndim != 1 or p.size == 0 or q.size == 0:
        raise ValueError("pos and neg must be non-empty 1-D sequences")
    ranks = _average_ranks(np.concatenate([p, q]))
    u = ranks[: p.size].sum() - p.size * (p.size + 1) / 2.0
    return float(u / (p.size * q.size))


def pair_wins(pos: ArrayLike, neg: ArrayLike) -> FloatArray:
    """Matrix ``W[i, j] = 1[pos_i > neg_j] + 0.5 * 1[pos_i == neg_j]``."""
    p = np.asarray(pos, dtype=np.float64)[:, None]
    q = np.asarray(neg, dtype=np.float64)[None, :]
    out: FloatArray = (p > q).astype(np.float64) + 0.5 * (p == q)
    return out


def length_matched_mask(len_pos: ArrayLike, len_neg: ArrayLike, max_diff: float) -> FloatArray:
    """Matrix ``M[i, j] = 1`` when ``|len_pos_i - len_neg_j| <= max_diff``."""
    a = np.asarray(len_pos, dtype=np.float64)[:, None]
    b = np.asarray(len_neg, dtype=np.float64)[None, :]
    return (np.abs(a - b) <= max_diff).astype(np.float64)


def masked_auroc(
    wins: FloatArray, mask: FloatArray, rows: NDArray[np.intp], cols: NDArray[np.intp]
) -> float:
    """AUROC over the masked pairs of ``wins[rows][:, cols]``; NaN when no pair is allowed."""
    m = mask[np.ix_(rows, cols)]
    total = float(m.sum())
    if total == 0.0:
        return float("nan")
    return float((wins[np.ix_(rows, cols)] * m).sum() / total)


def residualize(score: ArrayLike, length: ArrayLike) -> FloatArray:
    """Residuals of an ordinary least squares fit of ``score`` on ``length`` (with intercept)."""
    y = np.asarray(score, dtype=np.float64)
    x = np.asarray(length, dtype=np.float64)
    design = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    out: FloatArray = y - design @ beta
    return out


def paired_bootstrap(
    stat: Callable[[NDArray[np.intp]], float],
    n: int,
    *,
    n_boot: int = 2000,
    seed: int = 0,
) -> FloatArray:
    """Statistic over ``n_boot`` resamples of ``n`` source units drawn with replacement.

    ``stat`` receives the resampled unit indices; the caller indexes the original and the
    paraphrase arrays with the same indices, so a pair is resampled together. The draws depend
    only on ``(n, n_boot, seed)``, so two statistics bootstrapped with the same arguments see
    identical resamples and their difference is a paired difference.
    """
    if n < 1:
        raise ValueError("n must be positive")
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        out[b] = stat(rng.integers(0, n, size=n))
    return out


def percentile_ci(samples: ArrayLike, alpha: float = 0.05) -> tuple[float, float]:
    """Percentile interval of the finite bootstrap samples (NaNs are ignored)."""
    s = np.asarray(samples, dtype=np.float64)
    s = s[np.isfinite(s)]
    if s.size == 0:
        raise ValueError("no finite bootstrap samples")
    lo, hi = np.quantile(s, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(lo), float(hi)


def classify_auroc(lo: float, hi: float) -> str:
    """The protocol's decision rule for an AUROC CI against 0.5."""
    if lo > 0.5:
        return "separates"
    if hi < 0.5:
        return "reversed"
    return "no detectable effect"


def paired_auroc_ci(
    pos: Sequence[float],
    neg: Sequence[float],
    *,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """AUROC of ``pos[i]`` vs ``neg[i]`` groups and its paired-bootstrap percentile CI.

    Unit of resampling: the index ``i`` (original and paraphrase of one source question move
    together). Returns ``(point, lo, hi)``.
    """
    p = np.asarray(pos, dtype=np.float64)
    q = np.asarray(neg, dtype=np.float64)
    if p.shape != q.shape or p.ndim != 1:
        raise ValueError("pos and neg must be 1-D and the same length")
    samples = paired_bootstrap(lambda idx: auroc(p[idx], q[idx]), p.size, n_boot=n_boot, seed=seed)
    lo, hi = percentile_ci(samples, alpha)
    return auroc(p, q), lo, hi
