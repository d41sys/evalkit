"""Judge panels and the self-preference excess (pure functions, numpy only).

Protocol: docs/protocol-judge-panel.md. Nothing here calls a model or reads a file; the callers
(``scripts/mtbench_panel.py``) feed per-order verdicts recorded in the call caches.

Vocabulary. A *verdict* is ``A``, ``B``, ``tie`` or ``invalid`` (an unparsable reply). Each judge
sees an item in both presentation orders; both verdicts are already mapped back to the item's A/B
labels (:class:`evalkit.judge.PairVerdict`). A judge's *resolved* verdict keeps the verdict when
both orders agree and is ``tie`` otherwise (:func:`evalkit.judge.resolve`).

Two panel aggregations, both fixed in advance:

* **majority** (:func:`majority_vote`): the panel verdict is the side that more than half of the
  judges' resolved verdicts name, else ``tie`` (a 3-way split, or a side with only one vote, is a
  tie);
* **mean** (:func:`mean_vote`): the mean of every per-order signed verdict (A = +1, B = -1,
  tie and invalid = 0), mapped to ``A``/``B`` when its absolute value exceeds ``band``, else
  ``tie``.

Self-preference excess: for an item that includes a reference model (``claude-v1``), the judge's
score for that model (+1 win, 0 tie, -1 loss, resolved over both orders) minus the mean human
vote score for it on the same item (same coding). Positive excess means the judge favours that
model more than the human votes do.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from .judge import Decision, Verdict, resolve

TIE_BAND = 0.2
"""Pre-registered tie band of :func:`mean_vote`: with six per-order verdicts the mean moves in
steps of 1/6, so ``|mean| <= 0.2`` is a net margin of at most one verdict (a tie)."""

_SIGN: dict[str, int] = {"A": 1, "B": -1, "tie": 0, "invalid": 0}


def signed(verdict: Verdict) -> int:
    """+1 for ``A``, -1 for ``B``; ``tie`` and ``invalid`` carry no vote (0)."""
    return _SIGN[verdict]


def resolved_verdict(first: Verdict, second: Verdict | None) -> Decision:
    """One judge's verdict over both orders: equal verdicts stand, anything else is a tie."""
    return resolve(first, second)


def majority_vote(verdicts: Sequence[Verdict]) -> Decision:
    """The side named by more than half of ``verdicts``; ``tie`` otherwise.

    With three judges: 2-1 and 3-0 decide; A/B/tie, A/tie/tie and A/B/tie splits are ties.
    ``invalid`` never counts for a side.
    """
    n = len(verdicts)
    if n == 0:
        raise ValueError("no verdicts")
    n_a = sum(v == "A" for v in verdicts)
    n_b = sum(v == "B" for v in verdicts)
    if 2 * n_a > n:
        return "A"
    if 2 * n_b > n:
        return "B"
    return "tie"


def mean_vote(verdicts: Sequence[Verdict], band: float = TIE_BAND) -> Decision:
    """Mean of the signed verdicts: ``A`` above ``band``, ``B`` below ``-band``, else ``tie``."""
    if not verdicts:
        raise ValueError("no verdicts")
    if band < 0:
        raise ValueError("band must be >= 0")
    mean = sum(_SIGN[v] for v in verdicts) / len(verdicts)
    if mean > band:
        return "A"
    if mean < -band:
        return "B"
    return "tie"


@dataclass(frozen=True)
class JudgeOrders:
    """One judge on one item: the verdict of each presentation order (item labels)."""

    first: Verdict
    second: Verdict | None

    @property
    def resolved(self) -> Decision:
        return resolved_verdict(self.first, self.second)

    @property
    def orders(self) -> tuple[Verdict, ...]:
        return (self.first,) if self.second is None else (self.first, self.second)

    @property
    def valid(self) -> bool:
        return self.second is not None and "invalid" not in (self.first, self.second)


@dataclass(frozen=True)
class PanelVerdict:
    """The panel's verdict on one item under one aggregation, with its two order halves.

    ``first`` / ``second`` aggregate the judges' first-order and second-order verdicts alone
    (the panel run once per presentation order); they give the position-flip rate of the panel.
    """

    resolved: Decision
    first: Decision
    second: Decision
    valid: bool

    @property
    def flipped(self) -> bool:
        return self.valid and self.first != self.second

    @property
    def same_slot(self) -> bool:
        return self.valid and {self.first, self.second} == {"A", "B"}


def panel_majority(judges: Sequence[JudgeOrders]) -> PanelVerdict:
    """Aggregation (a): majority over the judges' resolved verdicts."""
    if any(j.second is None for j in judges):
        raise ValueError("the panel needs both orders from every judge")
    firsts = [j.first for j in judges]
    seconds = [j.second for j in judges if j.second is not None]
    return PanelVerdict(
        resolved=majority_vote([j.resolved for j in judges]),
        first=majority_vote(firsts),
        second=majority_vote(seconds),
        valid=all(j.valid for j in judges),
    )


def panel_mean(judges: Sequence[JudgeOrders], band: float = TIE_BAND) -> PanelVerdict:
    """Aggregation (b): mean of all per-order signed verdicts, with a tie band."""
    if any(j.second is None for j in judges):
        raise ValueError("the panel needs both orders from every judge")
    firsts = [j.first for j in judges]
    seconds = [j.second for j in judges if j.second is not None]
    return PanelVerdict(
        resolved=mean_vote([*firsts, *seconds], band),
        first=mean_vote(firsts, band),
        second=mean_vote(seconds, band),
        valid=all(j.valid for j in judges),
    )


def decision_score(verdict: Decision, side: int) -> int:
    """Score of the side ``side`` (+1 = A, -1 = B): +1 win, 0 tie, -1 loss."""
    if side not in (1, -1):
        raise ValueError("side must be +1 (A) or -1 (B)")
    return side * _SIGN[verdict]


def reference_side(model_a: str, model_b: str, reference: str = "claude-v1") -> int:
    """+1 if ``model_a`` is the reference model, -1 if ``model_b`` is; error otherwise."""
    if model_a == reference and model_b != reference:
        return 1
    if model_b == reference and model_a != reference:
        return -1
    raise ValueError(f"{reference!r} is not exactly one of ({model_a!r}, {model_b!r})")


def human_score(votes: Sequence[Verdict], side: int) -> float:
    """Mean human score of ``side`` over the item's votes (nan when there are none)."""
    if not votes:
        return float("nan")
    return float(np.mean([decision_score(v, side) for v in votes if v != "invalid"]))


def excess(verdict: Decision, votes: Sequence[Verdict], side: int) -> float:
    """Self-preference excess of one item: judge score minus mean human score for ``side``.

    Both use +1 win / 0 tie / -1 loss for the side. Positive: the judge favours that side more
    than the humans do.
    """
    return decision_score(verdict, side) - human_score(votes, side)


def weighted_mean(x: np.ndarray, w: np.ndarray) -> float:
    """Weighted mean over entries where ``x`` is not nan (nan when the weight is zero)."""
    m = ~np.isnan(x)
    den = float(w[m].sum())
    return float((x[m] * w[m]).sum() / den) if den > 0 else float("nan")


def cohen_kappa(a: np.ndarray, b: np.ndarray, w: np.ndarray | None = None) -> float:
    """Weighted Cohen's kappa of two verdict-code vectors (codes -1, 0, 1); nan if undefined."""
    if a.shape != b.shape:
        raise ValueError("label vectors differ in length")
    if a.size == 0:
        return float("nan")
    wt = np.ones(a.size) if w is None else w
    conf = np.bincount((a + 1) * 3 + (b + 1), weights=wt, minlength=9).reshape(3, 3)
    total = conf.sum()
    if total <= 0:
        return float("nan")
    po = float(np.trace(conf) / total)
    pe = float((conf.sum(1) * conf.sum(0)).sum() / total**2)
    return (po - pe) / (1.0 - pe) if pe < 1.0 else float("nan")


def codes(verdicts: Sequence[Verdict]) -> np.ndarray:
    """Verdicts as the integer codes +1 / 0 / -1 (``invalid`` is 0)."""
    return np.array([_SIGN[v] for v in verdicts], dtype=np.int64)


@dataclass(frozen=True)
class Price:
    """List price in US dollars per million tokens (assumed unless read from the API)."""

    input: float
    output: float


def usage_cost(input_tokens: float, output_tokens: float, price: Price) -> float:
    """Dollar cost of a token count at ``price``."""
    return (input_tokens * price.input + output_tokens * price.output) / 1e6


def cost_per_1k(input_tokens: float, output_tokens: float, price: Price, n_verdicts: int) -> float:
    """Dollars per 1,000 resolved item verdicts (one verdict = both presentation orders)."""
    if n_verdicts <= 0:
        raise ValueError("n_verdicts must be positive")
    return usage_cost(input_tokens, output_tokens, price) / n_verdicts * 1000.0


def panel_cost_per_1k(per_judge: Sequence[float]) -> float:
    """A panel pays for every judge on every item: its cost is the sum of the judges' costs."""
    return float(sum(per_judge))


def _quotas(sizes: Mapping[Any, int], n: int) -> dict[Any, int]:
    """Largest-remainder allocation of ``n`` over cells in proportion to ``sizes`` (capped)."""
    total = sum(sizes.values())
    if n >= total:
        return dict(sizes)
    raw = {k: n * s / total for k, s in sizes.items()}
    quota = {k: int(v) for k, v in raw.items()}
    left = n - sum(quota.values())
    for k in sorted(sizes, key=lambda c: (-(raw[c] - quota[c]), str(c)))[:left]:
        quota[k] += 1
    return quota


def stratified_sample(keys: Sequence[tuple[Any, ...]], n: int, seed: int = 0) -> list[int]:
    """Indices of a seeded sample of ``n`` items, stratified by ``keys`` (one key per item).

    Cells get a largest-remainder share of ``n`` in proportion to their size; inside a cell the
    items are drawn with ``random.Random(seed)`` after sorting cells by key. The result is
    sorted by index. ``n >= len(keys)`` returns every index.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    cells: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        cells[k].append(i)
    quota = _quotas({k: len(v) for k, v in cells.items()}, n)
    rng = random.Random(seed)
    chosen: list[int] = []
    for k in sorted(cells, key=str):
        members = list(cells[k])
        rng.shuffle(members)
        chosen.extend(members[: quota[k]])
    return sorted(chosen)
