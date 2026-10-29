"""Bradley-Terry ranking: maximum-likelihood strengths with bootstrap intervals (numpy only).

Elo (``evalkit.aggregate.compute_elo_ratings``) is an online update: its ratings depend on the
order of the games and have no uncertainty. The Bradley-Terry model (Bradley & Terry 1952) fits all
games at once. Model ``i`` beats model ``j`` with probability ``p_i / (p_i + p_j)``; with
``theta = log p`` the log-likelihood of the win counts ``W_ij`` is concave and has one maximum
(when the comparison graph is strongly connected; Zermelo 1929, Ford 1957), found here by damped
Newton steps. This is the estimator the Chatbot Arena leaderboard moved to from online Elo
(Chiang et al. 2024, arXiv 2403.04132).

Conventions:

* A game is one item on which two models were both scored: the higher score wins, equal scores
  split the game (half a win each, as in the Elo path of ``build_pairwise_matches``).
* Ratings are on the Elo scale: ``r = base + (scale / ln 10) * theta``, centred so that the
  mean rating of the fitted models is ``base``; 400 points are a factor 10 in the odds.
* Intervals are percentile intervals of a bootstrap over *items* (the same resampled items for
  every model). With a cluster map the bootstrap resamples whole clusters, as
  :func:`evalkit.clustered.cluster_bootstrap_ci` does for a mean, so that leaderboard and
  ``compare`` make the same independence assumption.
* ``ridge > 0`` adds a Gaussian prior ``ridge * |theta|^2 / 2`` for data where the MLE does not
  exist (a model without a win or a loss against the rest); with ``ridge = 0`` such data raise.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from .clustered import encode_clusters

_NEWTON_ITERS = 200
_MAX_TENSOR_BYTES = 600_000_000


def _elo_factor(scale: float) -> float:
    return scale / math.log(10.0)


def _strongly_connected(wins: np.ndarray) -> bool:
    """Whether the digraph with an edge i -> j for ``wins[i, j] > 0`` is strongly connected."""
    m = wins.shape[0]
    adj = wins > 0
    for graph in (adj, adj.T):
        seen = np.zeros(m, dtype=bool)
        seen[0] = True
        frontier = np.array([0])
        while frontier.size:
            nxt = np.flatnonzero(graph[frontier].any(axis=0) & ~seen)
            seen[nxt] = True
            frontier = nxt
        if not seen.all():
            return False
    return True


def _log_likelihood(wins: np.ndarray, theta: np.ndarray, ridge: float) -> float:
    diff = theta[:, None] - theta[None, :]
    return float((wins * -np.logaddexp(0.0, -diff)).sum()) - 0.5 * ridge * float(theta @ theta)


def fit_theta(
    wins: np.ndarray, ridge: float = 0.0, start: np.ndarray | None = None, tol: float = 1e-10
) -> np.ndarray:
    """Maximum-likelihood (penalised if ``ridge > 0``) log-strengths from the win matrix.

    ``wins[i, j]`` is the number of games ``i`` won against ``j`` (half a win per tie), zero
    diagonal. Returns ``theta`` with mean 0. Raises ``ValueError`` if the MLE does not exist
    (comparison graph not strongly connected) and ``ridge`` is 0.
    """
    m = wins.shape[0]
    games = wins + wins.T
    if ridge == 0.0 and not _strongly_connected(wins):
        raise ValueError(
            "the Bradley-Terry MLE does not exist: some model has no win (or no loss) against "
            "the rest of its connected group; pass ridge > 0 for a penalised fit"
        )
    theta = np.zeros(m) if start is None else start - start.mean()
    wsum = wins.sum(axis=1)
    ll = _log_likelihood(wins, theta, ridge)
    eye = np.eye(m)
    for _ in range(_NEWTON_ITERS):
        diff = theta[:, None] - theta[None, :]
        sigma = 1.0 / (1.0 + np.exp(-diff))
        grad = wsum - (games * sigma).sum(axis=1) - ridge * theta
        curv = games * sigma * (1.0 - sigma)
        neg_hess = np.diag(curv.sum(axis=1)) - curv + (ridge if ridge > 0.0 else 1e-9) * eye
        step = np.linalg.solve(neg_hess, grad)
        scale = 1.0
        for _ in range(40):
            cand = theta + scale * step
            cand_ll = _log_likelihood(wins, cand, ridge)
            if cand_ll >= ll - 1e-12:
                break
            scale *= 0.5
        else:
            break
        done = float(np.max(np.abs(cand - theta))) < tol
        theta, ll = cand - cand.mean(), cand_ll
        if done:
            break
    return theta


def win_matrix(matches: Sequence[tuple[str, str, float]]) -> tuple[list[str], np.ndarray]:
    """(sorted model names, win matrix) from ``(model_a, model_b, score_a)`` triples.

    ``score_a`` is 1.0 (A won), 0.5 (tie) or 0.0 (B won), as for ``compute_elo_ratings``; any
    value in [0, 1] is accepted and splits the game proportionally.
    """
    names = sorted({m for a, b, _ in matches for m in (a, b)})
    index = {n: i for i, n in enumerate(names)}
    wins = np.zeros((len(names), len(names)))
    for a, b, s in matches:
        wins[index[a], index[b]] += s
        wins[index[b], index[a]] += 1.0 - s
    return names, wins


def bradley_terry_ratings(
    matches: Sequence[tuple[str, str, float]],
    base_rating: float = 1000.0,
    scale: float = 400.0,
    ridge: float = 0.0,
) -> dict[str, float]:
    """Bradley-Terry ratings on the Elo scale; same input as ``compute_elo_ratings``."""
    if not matches:
        return {}
    names, wins = win_matrix(matches)
    theta = fit_theta(wins, ridge)
    return {
        n: base_rating + _elo_factor(scale) * float(t) for n, t in zip(names, theta, strict=True)
    }


@dataclass(frozen=True)
class BradleyTerry:
    """Bradley-Terry fit with bootstrap intervals; arrays follow ``models``."""

    models: list[str]
    ratings: np.ndarray
    ci_lo: np.ndarray
    ci_hi: np.ndarray
    rank_lo: np.ndarray  # 2.5th percentile of the model's rank (1 = strongest) over resamples
    rank_hi: np.ndarray
    games: np.ndarray  # games played per model (items with a score for it and another model)
    resamples: int
    failed: int  # resamples without a MLE (counted out of the intervals)
    clustered: bool
    # (resamples, models) rating draws, kept for P(model i above model j)
    draws: np.ndarray

    def rating(self, model: str) -> float:
        return float(self.ratings[self.models.index(model)])

    def prob_above(self, a: str, b: str) -> float:
        """Share of bootstrap resamples in which ``a`` is rated above ``b`` (ties count half)."""
        i, j = self.models.index(a), self.models.index(b)
        ok = ~np.isnan(self.draws[:, i]) & ~np.isnan(self.draws[:, j])
        if not ok.any():
            return math.nan
        d = self.draws[ok, i] - self.draws[ok, j]
        return float(np.mean((d > 0) + 0.5 * (d == 0)))


def _comparison_tensor(values: np.ndarray) -> np.ndarray:
    """int8 tensor ``c[k, i, j]`` = 2 if model i scored higher than j on item k, 1 if equal."""
    n, m = values.shape
    if n * m * m > _MAX_TENSOR_BYTES:
        raise ValueError(
            f"{n} items x {m} models is too large for the item-level bootstrap "
            f"({n * m * m / 1e6:.0f} MB tensor); restrict to fewer models or items"
        )
    out = np.zeros((n, m, m), dtype=np.int8)
    for k in range(n):
        row = values[k]
        ok = ~np.isnan(row)
        both = ok[:, None] & ok[None, :]
        greater = row[:, None] > row[None, :]
        equal = row[:, None] == row[None, :]
        out[k] = np.where(both, np.where(greater, 2, np.where(equal, 1, 0)), 0)
        np.fill_diagonal(out[k], 0)
    return out


def _weighted_wins(tensor: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """``sum_k weights[b, k] * tensor[k] / 2`` for every row ``b`` of ``weights``: (B, M, M)."""
    n, m, _ = tensor.shape
    flat = tensor.reshape(n, m * m)
    out = np.zeros((weights.shape[0], m * m))
    step = max(1, 50_000_000 // (m * m))
    for lo in range(0, n, step):
        chunk = flat[lo : lo + step].astype(np.float32)
        out += weights[:, lo : lo + step].astype(np.float32) @ chunk
    return (out / 2.0).reshape(weights.shape[0], m, m)


def bradley_terry_bootstrap(
    scores: Mapping[str, Mapping[Hashable, float]],
    clusters: Mapping[Any, Hashable] | None = None,
    resamples: int = 200,
    seed: int = 0,
    ridge: float = 0.0,
    confidence_level: float = 0.95,
    base_rating: float = 1000.0,
    scale: float = 400.0,
) -> BradleyTerry:
    """Fit Bradley-Terry to per-item scores and bootstrap the items (or whole clusters).

    ``scores[model][item]`` is the score of the model on the item; an item that a model was not
    scored on does not enter its games. ``clusters`` maps an item to its cluster label (an item
    without an entry is its own cluster); when the items fall into at least two clusters each
    resample draws whole clusters with replacement. Every resample refits from the point
    estimate; resamples whose comparison graph is not strongly connected (``ridge = 0``) are
    dropped and counted in ``failed``.
    """
    models = list(scores)
    if len(models) < 2:
        raise ValueError("need at least two models")
    items = sorted({k for s in scores.values() for k in s}, key=repr)
    index = {k: i for i, k in enumerate(items)}
    values = np.full((len(items), len(models)), np.nan)
    for j, m in enumerate(models):
        for k, v in scores[m].items():
            values[index[k], j] = float(v)
    tensor = _comparison_tensor(values)
    n = len(items)
    ones = np.ones((1, n))
    wins = _weighted_wins(tensor, ones)[0]
    played = (wins + wins.T).sum(axis=1)
    if (played == 0).any():
        bad = [m for m, p in zip(models, played, strict=True) if p == 0]
        raise ValueError(f"models without any shared item: {bad}")
    factor = _elo_factor(scale)
    theta = fit_theta(wins, ridge)
    ratings = base_rating + factor * theta

    codes: np.ndarray | None = None
    if clusters is not None:
        labels = [clusters.get(k, ("\0singleton", k)) for k in items]
        codes_all = encode_clusters(labels)
        if int(codes_all.max()) >= 1:
            codes = codes_all
    rng = np.random.default_rng(seed)
    draws = np.full((resamples, len(models)), np.nan)
    failed = 0
    batch = max(1, min(resamples, 20))
    for lo in range(0, resamples, batch):
        b = min(batch, resamples - lo)
        if codes is None:
            weights = np.stack([np.bincount(rng.integers(0, n, n), minlength=n) for _ in range(b)])
        else:
            c = int(codes.max()) + 1
            mult = np.stack([np.bincount(rng.integers(0, c, c), minlength=c) for _ in range(b)])
            weights = mult[:, codes]
        boot = _weighted_wins(tensor, weights.astype(np.float64))
        for r in range(b):
            try:
                t = fit_theta(boot[r], ridge, start=theta)
            except ValueError:
                failed += 1
                continue
            draws[lo + r] = base_rating + factor * t
    ok = ~np.isnan(draws[:, 0])
    alpha = 1.0 - confidence_level
    if ok.any():
        ci_lo = np.percentile(draws[ok], 100.0 * alpha / 2.0, axis=0)
        ci_hi = np.percentile(draws[ok], 100.0 * (1.0 - alpha / 2.0), axis=0)
        ranks = (-draws[ok]).argsort(axis=1).argsort(axis=1) + 1
        rank_lo = np.percentile(ranks, 100.0 * alpha / 2.0, axis=0)
        rank_hi = np.percentile(ranks, 100.0 * (1.0 - alpha / 2.0), axis=0)
    else:
        ci_lo = ci_hi = rank_lo = rank_hi = np.full(len(models), np.nan)
    return BradleyTerry(
        models=models,
        ratings=ratings,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        rank_lo=rank_lo,
        rank_hi=rank_hi,
        games=played,
        resamples=resamples,
        failed=failed,
        clustered=codes is not None,
        draws=draws,
    )


def render_bradley_terry(bt: BradleyTerry, elo: Mapping[str, float] | None = None) -> str:
    """Markdown table of ratings (strongest first), interval, rank interval and optional Elo."""
    order = np.argsort(-bt.ratings, kind="stable")
    head = "| rank | model | Bradley-Terry | 95% CI | rank 95% interval | games |"
    sep = "|---|---|---|---|---|---|"
    if elo is not None:
        head += " Elo (online, order-dependent) |"
        sep += "---|"
    lines = [head, sep]
    for rank, i in enumerate(order, start=1):
        row = (
            f"| {rank} | {bt.models[i]} | {bt.ratings[i]:.1f} | "
            f"[{bt.ci_lo[i]:.1f}, {bt.ci_hi[i]:.1f}] | "
            f"{bt.rank_lo[i]:.0f}-{bt.rank_hi[i]:.0f} | {int(bt.games[i])} |"
        )
        if elo is not None:
            row += f" {elo.get(bt.models[i], float('nan')):.1f} |"
        lines.append(row)
    note = (
        f"{bt.resamples - bt.failed} of {bt.resamples} bootstrap resamples fitted"
        + (", whole clusters resampled" if bt.clustered else ", items resampled")
        + ". Ratings are centred on their mean; ties count half a win."
    )
    return "\n".join([*lines, "", note])
