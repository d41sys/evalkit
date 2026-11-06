"""Item response theory (1PL / 2PL) in numpy, and anchor-item selection (tinyBenchmarks style).

``P(y_ij) = sigmoid(a_i theta_j - c_i)`` for model ``j`` on item ``i``; the 1PL fixes
``a_i = 1``. Scores in [0, 1] are soft labels in the Bernoulli cross-entropy (a
quasi-likelihood: fractional F1 / BLEU scores are read as success probabilities). Fitting is
MAP with ``theta ~ N(0, 1)`` (which fixes the scale), ``c ~ N(0, c_sd^2)`` and
``a ~ N(1, a_sd^2)``, by alternating damped Fisher scoring: abilities given items, then items
given abilities. Missing scores are masked. ``docs/protocol-irt-subset.md`` has the study this
module serves; Polo et al. (2024, arXiv 2402.14992) is the method it re-implements.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

A_MIN, A_MAX = 0.05, 5.0
IRT_MODELS = ("1pl", "2pl")
_STEP = 2.0
CONVERGENCE_TOL = 1e-4  # |change in the penalised log-likelihood over the last sweep| below this


def sigmoid(z: np.ndarray) -> np.ndarray:
    return np.asarray(0.5 * (1.0 + np.tanh(0.5 * z)), dtype=np.float64)


@dataclass(frozen=True)
class IrtFit:
    theta: np.ndarray  # (models,)
    a: np.ndarray  # (items,)
    c: np.ndarray  # (items,); the item difficulty is c / a
    model: str
    objective: float  # penalised log-likelihood after the last sweep
    last_change: float  # change of the objective over the last sweep (convergence)
    sweeps: int  # sweeps actually run

    @property
    def converged(self) -> bool:
        return abs(self.last_change) < CONVERGENCE_TOL


def _objective(
    y: np.ndarray,
    mask: np.ndarray,
    theta: np.ndarray,
    a: np.ndarray,
    c: np.ndarray,
    theta_sd: float,
    c_sd: float,
    a_sd: float,
) -> float:
    p = np.clip(sigmoid(a[None, :] * theta[:, None] - c[None, :]), 1e-12, 1.0 - 1e-12)
    ll = float(np.sum(mask * (y * np.log(p) + (1.0 - y) * np.log1p(-p))))
    pen = 0.5 * float(np.sum((theta / theta_sd) ** 2) + np.sum((c / c_sd) ** 2))
    pen += 0.5 * float(np.sum(((a - 1.0) / a_sd) ** 2))
    return ll - pen


def estimate_theta(
    a: np.ndarray,
    c: np.ndarray,
    y: np.ndarray,
    mask: np.ndarray,
    theta_sd: float = 1.0,
    iters: int = 30,
) -> np.ndarray:
    """MAP ability of each row of ``y`` (shape (models, items)) given item parameters.

    ``a`` and ``c`` are the parameters of exactly those items (length = columns of ``y``);
    entries with ``mask`` False are ignored. A row with no scores gets the prior mean 0.
    """
    m = mask.astype(np.float64)
    theta = np.zeros(y.shape[0])
    prec = 1.0 / (theta_sd * theta_sd)
    for _ in range(iters):
        p = sigmoid(a[None, :] * theta[:, None] - c[None, :])
        grad = np.sum(m * (y - p) * a[None, :], axis=1) - prec * theta
        hess = np.sum(m * p * (1.0 - p) * (a * a)[None, :], axis=1) + prec
        step = np.clip(grad / hess, -_STEP, _STEP)
        theta = theta + step
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return theta


def fit_irt(
    y: np.ndarray,
    mask: np.ndarray | None = None,
    model: str = "2pl",
    sweeps: int = 60,
    tol: float | None = None,
    theta_sd: float = 1.0,
    c_sd: float = 3.0,
    a_sd: float = 0.5,
) -> IrtFit:
    """MAP fit of a 1PL or 2PL model to scores ``y[model, item]`` in [0, 1].

    ``mask`` marks the observed entries (default: all finite). Runs ``sweeps`` sweeps, or
    stops at the first sweep whose absolute change in the objective is below ``tol`` when
    ``tol`` is given. ``IrtFit.converged`` says whether the last change is below
    ``CONVERGENCE_TOL``, ``IrtFit.sweeps`` how many sweeps ran. Returns abilities, item
    slopes ``a`` (all 1 for the 1PL) and intercepts ``c``.
    """
    if model not in IRT_MODELS:
        raise ValueError(f"unknown IRT model {model!r}; choose from {IRT_MODELS}")
    raw = np.asarray(y, dtype=np.float64)
    obs = np.isfinite(raw) if mask is None else np.asarray(mask, dtype=bool) & np.isfinite(raw)
    y = np.nan_to_num(raw)
    m = obs.astype(np.float64)
    n_items = y.shape[1]
    seen = np.maximum(m.sum(axis=1), 1.0)
    mean_m = np.clip((m * y).sum(axis=1) / seen, 0.01, 0.99)
    logit_m = np.log(mean_m / (1.0 - mean_m))
    theta = (logit_m - logit_m.mean()) / max(float(logit_m.std()), 1e-6)
    seen_i = np.maximum(m.sum(axis=0), 1.0)
    mean_i = np.clip((m * y).sum(axis=0) / seen_i, 0.01, 0.99)
    c = -np.log(mean_i / (1.0 - mean_i))
    a = np.ones(n_items)
    prec_t, prec_c, prec_a = 1.0 / theta_sd**2, 1.0 / c_sd**2, 1.0 / a_sd**2
    previous = _objective(y, m, theta, a, c, theta_sd, c_sd, a_sd)
    change = float("inf")
    ran = 0
    for _ in range(sweeps):
        p = sigmoid(a[None, :] * theta[:, None] - c[None, :])
        grad = np.sum(m * (y - p) * a[None, :], axis=1) - prec_t * theta
        hess = np.sum(m * p * (1.0 - p) * (a * a)[None, :], axis=1) + prec_t
        theta = theta + np.clip(grad / hess, -_STEP, _STEP)

        p = sigmoid(a[None, :] * theta[:, None] - c[None, :])
        r = m * (y - p)
        w = m * p * (1.0 - p)
        g_c = -r.sum(axis=0) - prec_c * c
        h_cc = w.sum(axis=0) + prec_c
        if model == "1pl":
            c = c + np.clip(g_c / h_cc, -_STEP, _STEP)
        else:
            t = theta[:, None]
            g_a = (r * t).sum(axis=0) - prec_a * (a - 1.0)
            h_aa = (w * t * t).sum(axis=0) + prec_a
            h_ac = -(w * t).sum(axis=0)
            det = h_aa * h_cc - h_ac * h_ac
            d_a = (h_cc * g_a - h_ac * g_c) / det
            d_c = (h_aa * g_c - h_ac * g_a) / det
            a = np.clip(a + np.clip(d_a, -_STEP, _STEP), A_MIN, A_MAX)
            c = c + np.clip(d_c, -_STEP, _STEP)
        current = _objective(y, m, theta, a, c, theta_sd, c_sd, a_sd)
        change = current - previous
        previous = current
        ran += 1
        if tol is not None and abs(change) < tol:
            break
    return IrtFit(theta, a, c, model, previous, change, ran)


def kendall_tau_b(x: np.ndarray, y: np.ndarray) -> float:
    """Kendall tau-b (ties in either variable are corrected for); NaN if one is constant."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = x.size
    if n < 2:
        return float("nan")
    sx = np.sign(x[:, None] - x[None, :])
    sy = np.sign(y[:, None] - y[None, :])
    iu = np.triu_indices(n, k=1)
    sxu, syu = sx[iu], sy[iu]
    conc_minus_disc = float(np.sum(sxu * syu))
    n_x = float(np.count_nonzero(sxu))
    n_y = float(np.count_nonzero(syu))
    if n_x == 0 or n_y == 0:
        return float("nan")
    return conc_minus_disc / float(np.sqrt(n_x * n_y))


def kmeans(
    x: np.ndarray, k: int, rng: np.random.Generator, iters: int = 30, n_init: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """Lloyd's k-means with k-means++ starts; (labels, centroids) of the best of ``n_init``."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    k = min(k, n)
    sq = np.sum(x * x, axis=1)
    best: tuple[float, np.ndarray, np.ndarray] | None = None
    for _ in range(n_init):
        centres = np.empty((k, x.shape[1]))
        centres[0] = x[rng.integers(n)]
        d2 = np.maximum(sq - 2.0 * x @ centres[0] + float(centres[0] @ centres[0]), 0.0)
        for j in range(1, k):
            total = float(d2.sum())
            idx = int(rng.integers(n)) if total <= 0 else int(rng.choice(n, p=d2 / total))
            centres[j] = x[idx]
            d2 = np.minimum(
                d2, np.maximum(sq - 2.0 * x @ centres[j] + float(centres[j] @ centres[j]), 0.0)
            )
        labels = np.zeros(n, dtype=np.int64)
        inertia = float("inf")
        for it in range(iters):
            dist = sq[:, None] - 2.0 * x @ centres.T + np.sum(centres * centres, axis=1)[None, :]
            new = np.argmin(dist, axis=1)
            inertia = float(np.maximum(dist[np.arange(n), new], 0.0).sum())
            if it > 0 and np.array_equal(new, labels):
                break
            labels = new
            for j in range(k):
                members = x[labels == j]
                if members.size:
                    centres[j] = members.mean(axis=0)
        if best is None or inertia < best[0]:
            best = (inertia, labels.copy(), centres.copy())
    assert best is not None
    return best[1], best[2]


def cluster_anchors(
    features: np.ndarray, item_weight: np.ndarray, k: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """k-means anchors: (item index of the member nearest each centroid, cluster weight).

    The weight of a cluster is the sum of ``item_weight`` over its members, normalised to 1
    over the clusters. Empty clusters are dropped.
    """
    labels, centres = kmeans(features, k, rng)
    anchors: list[int] = []
    weights: list[float] = []
    for j in range(centres.shape[0]):
        members = np.flatnonzero(labels == j)
        if members.size == 0:
            continue
        d = np.sum((features[members] - centres[j]) ** 2, axis=1)
        anchors.append(int(members[int(np.argmin(d))]))
        weights.append(float(item_weight[members].sum()))
    w = np.asarray(weights)
    return np.asarray(anchors, dtype=np.int64), w / w.sum()


def info_anchors(fit: IrtFit, k: int) -> np.ndarray:
    """Greedy Fisher-information anchors.

    For each of ``k`` ability quantiles of the fitted abilities (evenly spaced), take the unused
    item with the largest ``a^2 p (1 - p)`` at that ability (lowest index on a tie).
    """
    qs = (np.arange(k) + 0.5) / k
    grid = np.quantile(fit.theta, qs)
    used = np.zeros(fit.a.size, dtype=bool)
    out: list[int] = []
    for th in grid:
        p = sigmoid(fit.a * th - fit.c)
        info = fit.a * fit.a * p * (1.0 - p)
        info[used] = -1.0
        i = int(np.argmax(info))
        used[i] = True
        out.append(i)
    return np.asarray(out, dtype=np.int64)
