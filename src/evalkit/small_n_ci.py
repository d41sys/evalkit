"""Bayesian intervals for 0/1 outcomes (Bowyer, Aitchison & Ivanova 2025, arXiv 2503.01747).

* :func:`beta_interval`: equal-tailed credible interval of a single accuracy under a
  ``Beta(prior + k, prior + n - k)`` posterior (``prior`` 1/2 is Jeffreys, 1 is uniform).
* :func:`dirichlet_diff_interval`: equal-tailed credible interval of the paired difference
  ``P(A only right) - P(B only right)`` under a symmetric ``Dirichlet(prior)`` prior on the 2 x 2
  table (both right, A only, B only, both wrong); aggregated to (win, loss, tie) that is
  ``Dirichlet(prior, prior, 2 prior)`` on the posterior counts.

Protocol and coverage: ``docs/protocol-small-n.md``. Numpy only; the Beta quantile reuses the
incomplete beta function of :mod:`evalkit.clustered`.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from .clustered import _betainc

JEFFREYS = 0.5
UNIFORM = 1.0
DIRICHLET_DRAWS = 4000


def _beta_quantile(a: float, b: float, q: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if _betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    return 0.5 * (lo + hi)


@lru_cache(maxsize=4096)
def beta_interval(
    successes: int, trials: int, prior: float = JEFFREYS, level: float = 0.95
) -> tuple[float, float]:
    """Equal-tailed credible interval of a binomial proportion (no endpoint adjustment)."""
    if trials < 0 or not 0 <= successes <= trials:
        raise ValueError("need 0 <= successes <= trials")
    a, b = prior + successes, prior + trials - successes
    tail = (1.0 - level) / 2.0
    return (_beta_quantile(a, b, tail), _beta_quantile(a, b, 1.0 - tail))


def dirichlet_diff_interval(
    wins: int,
    losses: int,
    ties: int,
    prior: float = JEFFREYS,
    level: float = 0.95,
    draws: int = DIRICHLET_DRAWS,
    seed: int = 0,
) -> tuple[float, float]:
    """Credible interval of ``P(win) - P(loss)`` from the posterior's quantiles.

    ``draws`` posterior samples (Gamma variates normalised to Dirichlet draws); the endpoints
    carry Monte Carlo noise of about ``1 / sqrt(draws)`` of the interval width."""
    if min(wins, losses, ties) < 0:
        raise ValueError("counts must be non-negative")
    g = np.random.default_rng(seed).gamma(
        [prior + wins, prior + losses, 2.0 * prior + ties], size=(draws, 3)
    )
    diff = (g[:, 0] - g[:, 1]) / g.sum(axis=1)
    tail = 100.0 * (1.0 - level) / 2.0
    lo, hi = np.percentile(diff, [tail, 100.0 - tail])
    return (float(lo), float(hi))
