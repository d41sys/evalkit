"""Bias-corrected pass rate of an LLM judge from a small human-labelled subset.

A judge that is wrong in a known way gives a biased pass rate. Let *positive* mean
**pass = 1** (judge verdict 1, human label 1). On the labelled subset

* TPR (sensitivity) = P(judge = 1 | human = 1),
* TNR (specificity) = P(judge = 0 | human = 0).

With p the judge's raw pass rate on all items, the Rogan-Gladen estimate of the true pass rate is

    theta = (p + TNR - 1) / (TPR + TNR - 1),   clipped to [0, 1].

It needs TPR + TNR > 1 (the judge is better than a coin); otherwise it is undefined and
:func:`correct_pass_rate` raises ``ValueError``. This is the correction of Lee et al. 2025,
"How to Correctly Report LLM-as-a-Judge Evaluations" (arXiv 2511.21140).

**Interval: delta method, not bootstrap.** Treat p (N items), TPR (n1 human-positive items) and
TNR (n0 human-negative items) as independent binomial proportions. The first-order variance of
theta is

    [p(1-p)/N + theta^2 TPR(1-TPR)/n1 + (1-theta)^2 TNR(1-TNR)/n0] / (TPR + TNR - 1)^2

and the interval is theta +- z sqrt(var), clipped to [0, 1]. It carries the calibration
uncertainty (the last two terms), which the naive interval for p ignores. Reasons for the
delta method: it is the method of Lee et al., it is closed-form (the Monte Carlo check below
runs thousands of intervals in a second), and a bootstrap would need the same independence
assumption between the two sets anyway. Limits: the labelled subset is assumed to be a random
sample of the judged items and independent of them (when it is a subset of the judged items the
covariance of p and TPR/TNR is ignored); the interval is symmetric, so near theta = 0 or 1 or
for a TPR + TNR just above 1 it is only approximate.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

from .results import load_results
from .statscheck import Rate, wilson_interval

LEVEL = 0.95
LEE_SENSITIVITY = 0.7
LEE_SPECIFICITY = 0.9
LEE_CALIBRATION_M = 200
LEE_THETAS = (0.1, 0.3, 0.5, 0.7, 0.9)
LEE_N_TEST = 1000


@dataclass(frozen=True)
class JudgeCorrection:
    n_items: int
    n_labelled: int
    n_pos: int  # labelled items with human label 1
    n_neg: int
    tpr: float
    tnr: float
    tpr_ci: tuple[float, float]
    tnr_ci: tuple[float, float]
    raw_rate: float
    raw_ci: tuple[float, float]  # Wilson interval of the raw rate (ignores judge error)
    theta: float
    ci: tuple[float, float]


def _clip(x: float) -> float:
    return min(1.0, max(0.0, x))


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _ci(t: tuple[float, float]) -> str:
    return f"[{_pct(t[0])}, {_pct(t[1])}]"


def _correct(
    p: float, n_items: int, tp: int, n_pos: int, tn: int, n_neg: int, level: float
) -> tuple[float, tuple[float, float], float, float]:
    """(theta, CI, tpr, tnr). ValueError when a class is empty or TPR + TNR <= 1."""
    if n_pos == 0 or n_neg == 0:
        raise ValueError(
            f"need labelled items of both classes (human label 1: {n_pos}, 0: {n_neg}) "
            "to estimate TPR and TNR"
        )
    tpr, tnr = tp / n_pos, tn / n_neg
    j = tpr + tnr - 1.0
    if j <= 0.0:
        raise ValueError(
            f"TPR + TNR = {tpr + tnr:.3f} <= 1 (TPR {tpr:.3f}, TNR {tnr:.3f}): the judge is no "
            "better than chance on the labelled set, so its pass rate cannot be corrected"
        )
    raw = (p + tnr - 1.0) / j
    var = (
        p * (1 - p) / n_items
        + raw**2 * tpr * (1 - tpr) / n_pos
        + (1 - raw) ** 2 * tnr * (1 - tnr) / n_neg
    ) / j**2
    half = NormalDist().inv_cdf(0.5 + level / 2.0) * math.sqrt(var)
    return _clip(raw), (_clip(raw - half), _clip(raw + half)), tpr, tnr


def correct_pass_rate(
    verdicts: Sequence[int],
    cal_judge: Sequence[int],
    cal_human: Sequence[int],
    level: float = LEVEL,
) -> JudgeCorrection:
    """Corrected pass rate from the judge's 0/1 verdicts on all items and its verdicts
    (``cal_judge``) next to human labels (``cal_human``) on the labelled subset."""
    v, cj, ch = np.asarray(verdicts), np.asarray(cal_judge), np.asarray(cal_human)
    if v.size == 0:
        raise ValueError("no judge verdicts")
    if cj.shape != ch.shape:
        raise ValueError("calibration judge verdicts and human labels differ in length")
    for name, a in (("verdicts", v), ("calibration verdicts", cj), ("labels", ch)):
        if not np.isin(a, (0, 1)).all():
            raise ValueError(f"{name} must be 0 or 1")
    n_pos, n_neg = int((ch == 1).sum()), int((ch == 0).sum())
    tp, tn = int(((cj == 1) & (ch == 1)).sum()), int(((cj == 0) & (ch == 0)).sum())
    n_pass = int((v == 1).sum())
    theta, ci, tpr, tnr = _correct(n_pass / v.size, v.size, tp, n_pos, tn, n_neg, level)
    return JudgeCorrection(
        n_items=int(v.size),
        n_labelled=int(ch.size),
        n_pos=n_pos,
        n_neg=n_neg,
        tpr=tpr,
        tnr=tnr,
        tpr_ci=wilson_interval(tp, n_pos, level),
        tnr_ci=wilson_interval(tn, n_neg, level),
        raw_rate=n_pass / v.size,
        raw_ci=wilson_interval(n_pass, v.size, level),
        theta=theta,
        ci=ci,
    )


def correction_from_files(
    judge_path: str, labels: Sequence[Mapping[str, object]], model: str | None = None
) -> JudgeCorrection:
    """Read a judge ``results.jsonl`` (score = verdict) and label rows ``{example_id, label}``
    (``task`` optional). ValueError on anything that cannot be matched or is not 0/1."""
    table = load_results(judge_path)
    models = table.models()
    if model is None:
        if len(models) != 1:
            raise ValueError(f"{judge_path} has models {models}; pick one with --model")
        model = models[0]
    elif model not in table.samples:
        raise ValueError(f"model {model!r} not in {judge_path} (has {models})")
    verdicts = table.item_scores(model)
    if not all(s in (0.0, 1.0) for s in verdicts.values()):
        raise ValueError(
            "judge scores must be 0/1 verdicts, one row per item "
            "(an item with several samples averaged to a non-binary score)"
        )
    by_id: dict[str, list[tuple[str, str]]] = {}
    for key in verdicts:
        by_id.setdefault(key[1], []).append(key)
    cal_judge: list[int] = []
    cal_human: list[int] = []
    seen: set[tuple[str, str]] = set()
    for row in labels:
        eid = str(row["example_id"])
        if row.get("task") is not None:
            key = (str(row["task"]), eid)
        elif len(by_id.get(eid, [])) == 1:
            key = by_id[eid][0]
        else:
            raise ValueError(
                f"label for example_id {eid!r} "
                + ("matches several tasks; add `task`" if eid in by_id else "has no judge verdict")
            )
        if key not in verdicts:
            raise ValueError(f"label for {key} has no judge verdict")
        if key in seen:
            raise ValueError(f"item {key} is labelled twice")
        seen.add(key)
        cal_judge.append(int(verdicts[key]))
        cal_human.append(int(row["label"]))  # type: ignore[call-overload]
    return correct_pass_rate([int(s) for s in verdicts.values()], cal_judge, cal_human)


def render(c: JudgeCorrection) -> str:
    return "\n".join(
        [
            "positive = pass (judge verdict 1, human label 1)",
            f"items judged: {c.n_items}; labelled: {c.n_labelled} "
            f"({c.n_pos} human-pass, {c.n_neg} human-fail)",
            f"TPR (judge pass | human pass): {_pct(c.tpr)} {_ci(c.tpr_ci)} (Wilson 95%)",
            f"TNR (judge fail | human fail): {_pct(c.tnr)} {_ci(c.tnr_ci)} (Wilson 95%)",
            f"raw judge pass rate:  {_pct(c.raw_rate)} {_ci(c.raw_ci)} (ignores judge error)",
            f"corrected pass rate:  {_pct(c.theta)} {_ci(c.ci)} (delta method, includes "
            "calibration uncertainty)",
        ]
    )


# ------------------------------------------------------------------ Monte Carlo check


@dataclass(frozen=True)
class CoverageRow:
    theta: float
    corrected: Rate  # corrected CI covers the true theta
    naive: Rate  # Wilson CI of the raw judge rate covers the true theta
    undefined: int  # replications with an empty class or TPR + TNR <= 1 (counted as misses)


def coverage_check(
    reps: int = 2000,
    seed: int = 0,
    thetas: Sequence[float] = LEE_THETAS,
    n_test: int = LEE_N_TEST,
    m: int = LEE_CALIBRATION_M,
    sensitivity: float = LEE_SENSITIVITY,
    specificity: float = LEE_SPECIFICITY,
) -> list[CoverageRow]:
    """Coverage of the 95% intervals in the setup of Lee et al.: a test set of ``n_test`` items
    with true pass rate theta and a separate calibration set of ``m`` human-labelled items from
    the same population; the judge has the given TPR and TNR."""
    rng = np.random.default_rng(seed)
    rows = []
    for theta in thetas:
        p_judge = theta * sensitivity + (1 - theta) * (1 - specificity)
        hits = naive_hits = undefined = 0
        for _ in range(reps):
            n_pos = int(rng.binomial(m, theta))
            tp = int(rng.binomial(n_pos, sensitivity))
            tn = int(rng.binomial(m - n_pos, specificity))
            n_pass = int(rng.binomial(n_test, p_judge))
            lo, hi = wilson_interval(n_pass, n_test, LEVEL)
            naive_hits += lo <= theta <= hi
            try:
                _, (clo, chi), _, _ = _correct(
                    n_pass / n_test, n_test, tp, n_pos, tn, m - n_pos, LEVEL
                )
            except ValueError:
                undefined += 1
                continue
            hits += clo <= theta <= chi
        rows.append(CoverageRow(theta, Rate(hits, reps), Rate(naive_hits, reps), undefined))
    return rows


def render_coverage(rows: Sequence[CoverageRow], reps: int, seed: int) -> str:
    head = (
        f"Coverage of 95% intervals for the true pass rate theta; judge TPR {LEE_SENSITIVITY}, "
        f"TNR {LEE_SPECIFICITY}, {LEE_N_TEST} judged items, {LEE_CALIBRATION_M} labelled items, "
        f"{reps} replications per row, seed {seed} (Wilson 99% interval over replications).\n\n"
        "| true theta | corrected CI | naive judge-rate CI | undefined reps |\n|---|---|---|---|\n"
    )
    return head + "\n".join(
        f"| {r.theta:.2f} | {r.corrected.fmt()} | {r.naive.fmt()} | {r.undefined} |" for r in rows
    )
