"""Judge-human agreement with cluster-bootstrap intervals (numpy only).

The unit of data is an *item*: one question, one pair of responses, one turn, judged by the LLM
(verdict ``A``/``B``/``tie``) and by one or more humans (votes in the same labels).

Agreement follows Zheng et al. 2023 (arXiv 2306.05685, sec. 4.1 and App. D.3): the probability
that a randomly chosen judge pair of the two types agrees on a randomly chosen item.

* judge-human: per item the share of the item's human votes the judge matches, averaged over
  items (every item counts once, however many humans voted);
* human-human: per item the share of agreeing pairs of votes from different humans, averaged
  over items that have at least two such votes;
* **S1** counts ties as a label; **S2** drops every vote pair in which either side is a tie
  (items left with no pair drop out);
* Cohen's kappa pools all (item, human vote) rows: 3 labels for S1, the 2 non-tie labels for S2.

Intervals are percentile intervals of a **cluster bootstrap**: whole clusters (questions) are
resampled with replacement, so the several judged pairs and turns of one question are one
resampling unit. Each resample is a weight vector over items, so one resample feeds every
statistic and the differences between them keep their pairing. Rank correlations rank the
original sample once and reweight, which is the usual shortcut and treats a duplicated item as a
tie with itself.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

Label = Literal["A", "B", "tie"]
_CODE: dict[str, int] = {"A": 1, "B": -1, "tie": 0}


@dataclass(frozen=True)
class ValItem:
    """One judged pair. ``votes`` are ``(human id, label)``; ``other`` is a second automatic
    judge's verdict on the same item (e.g. the published GPT-4 verdict), if any."""

    cluster: str
    verdict: Label
    votes: tuple[tuple[str, Label], ...]
    length_diff: float
    flipped: bool = False
    same_slot: bool = False
    both_valid: bool = True
    other: Label | None = None


@dataclass(frozen=True)
class Estimate:
    value: float
    lo: float
    hi: float


def _wmean(x: np.ndarray, w: np.ndarray, mask: np.ndarray | None = None) -> float:
    m = ~np.isnan(x) if mask is None else mask & ~np.isnan(x)
    den = float(w[m].sum())
    return float((x[m] * w[m]).sum() / den) if den > 0 else float("nan")


def _wcorr(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    m = ~(np.isnan(x) | np.isnan(y)) & (w > 0)
    if m.sum() < 2:
        return float("nan")
    ws = w[m] / w[m].sum()
    xm, ym = (ws * x[m]).sum(), (ws * y[m]).sum()
    cov = (ws * (x[m] - xm) * (y[m] - ym)).sum()
    vx, vy = (ws * (x[m] - xm) ** 2).sum(), (ws * (y[m] - ym) ** 2).sum()
    return float(cov / np.sqrt(vx * vy)) if vx > 0 and vy > 0 else float("nan")


def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    out = np.empty(x.size, dtype=np.float64)
    xs = x[order]
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and xs[j + 1] == xs[i]:
            j += 1
        out[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return out


def _kappa(a: np.ndarray, b: np.ndarray, w: np.ndarray, labels: Sequence[int]) -> float:
    """Weighted Cohen's kappa of two label vectors over ``labels``."""
    k = len(labels)
    if a.size == 0:
        return float("nan")
    lut = np.zeros(3, dtype=np.int64)  # code -1, 0, 1 -> position in ``labels``
    for pos, lab in enumerate(labels):
        lut[lab + 1] = pos
    ai = lut[a + 1]
    bi = lut[b + 1]
    conf = np.bincount(ai * k + bi, weights=w, minlength=k * k).reshape(k, k)
    total = conf.sum()
    if total <= 0:
        return float("nan")
    po = np.trace(conf) / total
    pe = float((conf.sum(1) * conf.sum(0)).sum() / total**2)
    return float((po - pe) / (1.0 - pe)) if pe < 1.0 else float("nan")


class _Votes:
    """Vote-level and item-level arrays of one automatic judge against the humans."""

    def __init__(self, verdicts: np.ndarray, vote_item: np.ndarray, vote_code: np.ndarray) -> None:
        n = verdicts.size
        self.vote_item = vote_item
        self.vote_code = vote_code
        self.vote_judge = verdicts[vote_item]
        eq = (self.vote_judge == vote_code).astype(np.float64)
        nontie = (self.vote_judge != 0) & (vote_code != 0)
        self.nontie = nontie
        self.a1 = np.full(n, np.nan)
        self.a2 = np.full(n, np.nan)
        cnt1 = np.bincount(vote_item, minlength=n)
        s1 = np.bincount(vote_item, weights=eq, minlength=n)
        cnt2 = np.bincount(vote_item, weights=nontie.astype(np.float64), minlength=n)
        s2 = np.bincount(vote_item, weights=eq * nontie, minlength=n)
        self.a1[cnt1 > 0] = s1[cnt1 > 0] / cnt1[cnt1 > 0]
        self.a2[cnt2 > 0] = s2[cnt2 > 0] / cnt2[cnt2 > 0]

    def stats(self, w: np.ndarray, prefix: str, mask: np.ndarray | None = None) -> dict[str, float]:
        wv = w[self.vote_item]
        keep = np.ones(self.vote_item.size, dtype=bool) if mask is None else mask[self.vote_item]
        k2 = keep & self.nontie
        return {
            f"{prefix}s1": _wmean(self.a1, w, mask),
            f"{prefix}s2": _wmean(self.a2, w, mask),
            f"{prefix}kappa_s1": _kappa(
                self.vote_judge[keep], self.vote_code[keep], wv[keep], (1, 0, -1)
            ),
            f"{prefix}kappa_s2": _kappa(self.vote_judge[k2], self.vote_code[k2], wv[k2], (1, -1)),
        }


class AgreementData:
    """Arrays for one set of items; :meth:`statistics` evaluates every metric under item
    weights (all ones for the point estimate, resampled counts for the bootstrap)."""

    def __init__(self, items: Sequence[ValItem]) -> None:
        if not items:
            raise ValueError("no items")
        self.items = list(items)
        n = len(self.items)
        self.n = n
        labels = sorted({it.cluster for it in self.items})
        lab_idx = {c: i for i, c in enumerate(labels)}
        self.cluster = np.array([lab_idx[it.cluster] for it in self.items])
        self.n_clusters = len(labels)
        verdict = np.array([_CODE[it.verdict] for it in self.items])
        v_item: list[int] = []
        v_code: list[int] = []
        hh1 = np.full(n, np.nan)
        hh2 = np.full(n, np.nan)
        for i, it in enumerate(self.items):
            agree = pairs = agree2 = pairs2 = 0
            for p, (jp, lp) in enumerate(it.votes):
                v_item.append(i)
                v_code.append(_CODE[lp])
                for jq, lq in it.votes[p + 1 :]:
                    if jq == jp:
                        continue
                    pairs += 1
                    agree += lp == lq
                    if lp != "tie" and lq != "tie":
                        pairs2 += 1
                        agree2 += lp == lq
            if pairs:
                hh1[i] = agree / pairs
            if pairs2:
                hh2[i] = agree2 / pairs2
        self.hh1, self.hh2 = hh1, hh2
        vote_item = np.array(v_item, dtype=np.int64)
        vote_code = np.array(v_code, dtype=np.int64)
        self.vote_code = vote_code
        self.vote_item = vote_item
        self.verdict = verdict
        self.judge = _Votes(verdict, vote_item, vote_code)
        self.has_other = any(it.other is not None for it in self.items)
        if self.has_other:
            other = np.array([_CODE[it.other or "tie"] for it in self.items])
            self.other_mask = np.array([it.other is not None for it in self.items])
            self.other = _Votes(other, vote_item, vote_code)
        self.len_diff = np.array([it.length_diff for it in self.items])
        self.flipped = np.array([it.flipped for it in self.items], dtype=np.float64)
        self.same_slot = np.array([it.same_slot for it in self.items], dtype=np.float64)
        self.valid = np.array([it.both_valid for it in self.items])
        mean_human = np.full(n, np.nan)
        cnt = np.bincount(vote_item, minlength=n)
        sums = np.bincount(vote_item, weights=vote_code.astype(np.float64), minlength=n)
        mean_human[cnt > 0] = sums[cnt > 0] / cnt[cnt > 0]
        self.r_len = _ranks(self.len_diff)
        self.r_judge = _ranks(verdict.astype(np.float64))
        self.r_human = np.full(n, np.nan)
        ok = ~np.isnan(mean_human)
        self.r_human[ok] = _ranks(mean_human[ok])
        sign_d = np.sign(self.len_diff)
        self.judge_longer = np.where(
            (verdict != 0) & (sign_d != 0), (np.sign(verdict) == sign_d).astype(np.float64), np.nan
        )
        v_sd = sign_d[vote_item]
        self.vote_longer = np.where(
            (vote_code != 0) & (v_sd != 0), (np.sign(vote_code) == v_sd).astype(np.float64), np.nan
        )
        self.judge_tie = (verdict == 0).astype(np.float64)
        self.vote_tie = (vote_code == 0).astype(np.float64)

    def statistics(self, w: np.ndarray) -> dict[str, float]:
        out: dict[str, float] = {}
        out.update(self.judge.stats(w, "jh_"))
        out["hh_s1"] = _wmean(self.hh1, w)
        out["hh_s2"] = _wmean(self.hh2, w)
        # judge-human agreement on exactly the items where human-human agreement is defined
        m1 = ~np.isnan(self.hh1) & ~np.isnan(self.judge.a1)
        m2 = ~np.isnan(self.hh2) & ~np.isnan(self.judge.a2)
        out["jh_s1_matched"] = _wmean(self.judge.a1, w, m1)
        out["hh_s1_matched"] = _wmean(self.hh1, w, m1)
        out["jh_s2_matched"] = _wmean(self.judge.a2, w, m2)
        out["hh_s2_matched"] = _wmean(self.hh2, w, m2)
        out["diff_s1_vs_human"] = out["jh_s1_matched"] - out["hh_s1_matched"]
        out["diff_s2_vs_human"] = out["jh_s2_matched"] - out["hh_s2_matched"]
        if self.has_other:
            m = self.other_mask
            out["judge_on_other_items_s1"] = _wmean(self.judge.a1, w, m)
            out["judge_on_other_items_s2"] = _wmean(self.judge.a2, w, m)
            out.update(self.other.stats(w, "other_", m))
            out["diff_s1_vs_other"] = out["judge_on_other_items_s1"] - out["other_s1"]
            out["diff_s2_vs_other"] = out["judge_on_other_items_s2"] - out["other_s2"]
        out["flip_rate"] = _wmean(self.flipped, w, self.valid)
        out["same_slot_rate"] = _wmean(self.same_slot, w, self.valid)
        out["judge_tie_rate"] = _wmean(self.judge_tie, w)
        wv = w[self.vote_item]
        out["human_tie_rate"] = (
            float((self.vote_tie * wv).sum() / wv.sum()) if wv.sum() else float("nan")
        )
        out["len_rho_judge"] = _wcorr(self.r_judge, self.r_len, w)
        out["len_rho_human"] = _wcorr(self.r_human, self.r_len, w)
        out["len_rho_diff"] = out["len_rho_judge"] - out["len_rho_human"]
        out["longer_wins_judge"] = _wmean(self.judge_longer, w)
        m = ~np.isnan(self.vote_longer)
        out["longer_wins_human"] = (
            float((self.vote_longer[m] * wv[m]).sum() / wv[m].sum())
            if wv[m].sum()
            else float("nan")
        )
        return out

    def counts(self) -> dict[str, int]:
        return {
            "items": self.n,
            "clusters": self.n_clusters,
            "votes": int(self.vote_item.size),
            "items_s2": int((~np.isnan(self.judge.a2)).sum()),
            "items_hh_s1": int((~np.isnan(self.hh1)).sum()),
            "items_hh_s2": int((~np.isnan(self.hh2)).sum()),
        }


def cluster_bootstrap(
    stat: Callable[[np.ndarray], Mapping[str, float]],
    item_cluster: np.ndarray,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict[str, Estimate]:
    """Point estimate (unit weights) and percentile CI of every statistic over resampled clusters.

    ``item_cluster`` gives each item's cluster code 0..C-1. A resample draws C clusters with
    replacement and weights each item by how often its cluster was drawn. ``nan`` resamples
    (an undefined statistic) are skipped for the interval.
    """
    n_items = item_cluster.size
    n_clusters = int(item_cluster.max()) + 1
    point = dict(stat(np.ones(n_items)))
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {k: [] for k in point}
    for _ in range(n_boot):
        counts = np.bincount(rng.integers(0, n_clusters, size=n_clusters), minlength=n_clusters)
        for k, v in stat(counts[item_cluster].astype(np.float64)).items():
            draws[k].append(v)
    out: dict[str, Estimate] = {}
    for k, v in point.items():
        arr = np.asarray(draws[k], dtype=np.float64)
        arr = arr[~np.isnan(arr)]
        if arr.size < 2:
            out[k] = Estimate(v, float("nan"), float("nan"))
        else:
            lo, hi = np.percentile(arr, [100 * alpha / 2, 100 * (1 - alpha / 2)])
            out[k] = Estimate(v, float(lo), float(hi))
    return out


def evaluate(items: Sequence[ValItem], n_boot: int = 2000, seed: int = 0) -> dict[str, Estimate]:
    """Every agreement, kappa, flip and length statistic of ``items`` with cluster-bootstrap CIs."""
    data = AgreementData(items)
    return cluster_bootstrap(data.statistics, data.cluster, n_boot=n_boot, seed=seed)
