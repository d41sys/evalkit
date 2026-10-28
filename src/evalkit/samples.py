"""Several samples per item: pass^k.

An item sampled ``k`` times is one observation of the model, not ``k``: the samples share
the item's difficulty. The unit of analysis stays the item, so sample scores are averaged per
item before any statistic (:class:`evalkit.results.ResultsTable.item_scores`, then
``evalkit compare`` and :mod:`evalkit.clustered`).

``pass^k`` (tau-bench, Yao et al. 2024, arXiv 2406.12045) is the probability that *all* ``k``
independent samples of an item are correct, averaged over items: ``E_i[p_i^k]``. From ``n_i``
samples with ``c_i`` correct the unbiased estimate per item is ``C(c_i, k) / C(n_i, k)``
(drawing ``k`` of the ``n_i`` samples without replacement; the analogue of the unbiased
pass@k of Chen et al. 2021).
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Mapping, Sequence

import numpy as np


def pass_hat_k_item(correct: int, n: int, k: int) -> float:
    """Unbiased estimate of ``p^k`` from ``correct`` of ``n`` samples: ``C(c, k) / C(n, k)``."""
    if k < 1:
        raise ValueError("k must be at least 1")
    if n < k:
        raise ValueError(f"need at least k = {k} samples per item, got {n}")
    return math.comb(correct, k) / math.comb(n, k)


def pass_hat_k[K: Hashable](samples: Mapping[K, Sequence[float]], k: int) -> dict[K, float]:
    """Per-item unbiased ``pass^k`` estimates; their mean is the model's ``pass^k``.

    Samples must be 0/1 correctness scores and every item needs at least ``k`` of them.
    """
    out: dict[K, float] = {}
    for key, vals in samples.items():
        arr = np.asarray(vals, dtype=np.float64)
        if not np.all((arr == 0.0) | (arr == 1.0)):
            raise ValueError("pass^k needs 0/1 scores")
        out[key] = pass_hat_k_item(int(arr.sum()), arr.size, k)
    return out
