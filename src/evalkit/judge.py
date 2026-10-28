"""LLM-as-judge scoring with bias controls.

Two modes:

* **Pointwise**: one response is scored against a rubric on an integer scale (default 1-10).
* **Pairwise**: two responses are compared and the verdict is ``A``, ``B`` or ``tie``.

Bias controls (Zheng et al. 2023, arXiv 2306.05685, sec. 3.3 and 4):

* **Position**: a pairwise item is judged twice, once per presentation order. When the two
  verdicts name different winners (or one is a tie) the resolved verdict is ``tie``, and the
  share of such items is reported as the position-flip rate (:func:`position_flip_rate`).
* **Reference answer**: an optional reference is shown to the judge (reference-guided grading).
* **Length**: :func:`length_bias` reports the rank correlation between the verdict and the length
  difference, and how often the longer response wins. Whether that is a bias or a real quality
  difference needs a human baseline (see :mod:`evalkit.judge_stats`).
* **Self-preference** is not controlled. A judge may favour answers written by its own model
  family (Zheng et al. 2023, sec. 3.3; Panickssery et al. 2024, arXiv 2404.13076). Do not use a
  judge to rank answers from its own model family without a human check.

Every call goes through :class:`~evalkit.llmcache.CachedCompleter`; the API exposes no logprobs,
so no confidence is derived from the judge.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from .llmcache import CachedCompleter

Decision = Literal["A", "B", "tie"]
Verdict = Literal["A", "B", "tie", "invalid"]

MAX_WORKERS = 8
PROMPT_VERSION = "judge-v1"

PAIRWISE_SYSTEM = (
    "You are an impartial evaluator of AI assistant responses. You judge the quality of the "
    "responses only, never who wrote them or in which order they are shown. Follow the "
    "requested output format exactly."
)

PAIRWISE_TEMPLATE = """\
Compare the two responses below and decide which one answers the user better.

Consider helpfulness, correctness, relevance, depth, clarity and level of detail. Do not prefer \
a response because it is longer or because of the position it is shown in. If the two are of \
similar quality, or you cannot tell, answer TIE.{instruction}

[User request]
{prompt}
[End of user request]
{reference}
[Response A]
{response_a}
[End of Response A]

[Response B]
{response_b}
[End of Response B]

Write a short explanation (at most four sentences), then finish with exactly one line: \
`VERDICT: A`, `VERDICT: B` or `VERDICT: TIE`."""

POINTWISE_SYSTEM = (
    "You are a strict, impartial evaluator of AI assistant responses. Follow the requested "
    "output format exactly."
)

POINTWISE_TEMPLATE = """\
Rate the response below on a scale from {low} (worst) to {high} (best) using this rubric.

Rubric - {name}: {criteria}{instruction}

[User request]
{prompt}
[End of user request]
{reference}
[Response]
{response}
[End of Response]

Write a short explanation (at most four sentences), then finish with exactly one line: \
`SCORE: <a number from {low} to {high}>`."""

REFERENCE_BLOCK = (
    "\n[Reference answer]\n{reference}\n[End of reference answer]\n"
    "(The reference is one correct answer; use it to check correctness.)\n"
)


def prompt_fingerprint() -> str:
    """Short hash of every prompt string; a protocol pins it so a prompt edit is visible."""
    blob = "\x1f".join(
        [
            PROMPT_VERSION,
            PAIRWISE_SYSTEM,
            PAIRWISE_TEMPLATE,
            POINTWISE_SYSTEM,
            POINTWISE_TEMPLATE,
            REFERENCE_BLOCK,
        ]
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Rubric:
    """What a pointwise judge scores and on which integer scale."""

    name: str
    criteria: str
    low: int = 1
    high: int = 10


DEFAULT_RUBRIC = Rubric(
    name="overall quality",
    criteria=(
        "how helpful, correct, relevant, clear and sufficiently detailed the response is for "
        "the user request. 1 is useless or wrong, 5 is mixed, 10 is excellent."
    ),
)


@dataclass(frozen=True)
class PairItem:
    """Two responses to one request. ``instruction`` is extra judging guidance;
    ``length_a``/``length_b`` override the word counts used by the length diagnostic."""

    prompt: str
    response_a: str
    response_b: str
    reference: str | None = None
    instruction: str | None = None
    length_a: float | None = None
    length_b: float | None = None

    @property
    def length_diff(self) -> float:
        a = self.length_a if self.length_a is not None else len(self.response_a.split())
        b = self.length_b if self.length_b is not None else len(self.response_b.split())
        return float(a - b)


@dataclass(frozen=True)
class PointItem:
    """One response to one request."""

    prompt: str
    response: str
    reference: str | None = None
    instruction: str | None = None


@dataclass(frozen=True)
class PairVerdict:
    """Both orders of one pair, with verdicts mapped back to the item's A/B labels.

    ``second`` is ``None`` when the pair was judged in one order only; the position-bias
    control is then off and ``resolved`` is just ``first``.
    """

    first: Verdict
    second: Verdict | None
    resolved: Decision

    @property
    def both_valid(self) -> bool:
        return self.second is not None and self.first != "invalid" and self.second != "invalid"

    @property
    def flipped(self) -> bool:
        """The two orders disagree (both verdicts parsed)."""
        return self.both_valid and self.first != self.second

    @property
    def same_slot(self) -> bool:
        """The judge picked the response shown first, or the one shown second, in both orders."""
        return self.both_valid and {self.first, self.second} == {"A", "B"}


@dataclass(frozen=True)
class PointVerdict:
    score: float | None
    text: str


_VERDICT_RE = re.compile(r"VERDICT\s*:\s*[\*`\[\s]*(A|B|TIE)\b", re.IGNORECASE)
_SCORE_RE = re.compile(r"SCORE\s*:\s*[\*`\[\s]*(\d+(?:\.\d+)?)", re.IGNORECASE)


def parse_verdict(text: str) -> Literal["A", "B", "tie", "invalid"]:
    """The last ``VERDICT: A|B|TIE`` line of a judge reply; ``invalid`` when there is none."""
    found = _VERDICT_RE.findall(text)
    if not found:
        return "invalid"
    last = found[-1].upper()
    return "tie" if last == "TIE" else ("A" if last == "A" else "B")


def parse_score(text: str, low: float, high: float) -> float | None:
    """The last ``SCORE: x`` of a reply when it lies in ``[low, high]``, else ``None``."""
    found = _SCORE_RE.findall(text)
    if not found:
        return None
    value = float(found[-1])
    return value if low <= value <= high else None


def _flip(v: Verdict) -> Verdict:
    if v == "A":
        return "B"
    return "A" if v == "B" else v


def resolve(first: Verdict, second: Verdict | None) -> Decision:
    """Agreeing verdicts stand; anything else (disagreement, an unparsable reply) is a tie."""
    if second is None:
        return "tie" if first == "invalid" else first
    if first == second and first != "invalid":
        return first
    return "tie"


def _instruction(text: str | None) -> str:
    return f" {text.strip()}" if text and text.strip() else ""


def _reference(text: str | None) -> str:
    return REFERENCE_BLOCK.format(reference=text) if text else ""


class Judge:
    """Pointwise and pairwise judging through a cached completer.

    ``both_orders=False`` judges each pair once (position control off). Concurrency is capped at
    :data:`MAX_WORKERS`.
    """

    def __init__(
        self,
        completer: CachedCompleter,
        *,
        rubric: Rubric = DEFAULT_RUBRIC,
        both_orders: bool = True,
        max_tokens: int = 1024,
        workers: int = MAX_WORKERS,
    ) -> None:
        self.completer = completer
        self.rubric = rubric
        self.both_orders = both_orders
        self.max_tokens = max_tokens
        self.workers = max(1, min(workers, MAX_WORKERS))

    def _pair_prompt(self, item: PairItem, swapped: bool) -> str:
        a, b = (item.response_b, item.response_a) if swapped else (item.response_a, item.response_b)
        return PAIRWISE_TEMPLATE.format(
            instruction=_instruction(item.instruction),
            prompt=item.prompt,
            reference=_reference(item.reference),
            response_a=a,
            response_b=b,
        )

    def _ask(self, system: str, prompt: str) -> str:
        return self.completer.complete(prompt, system=system, max_tokens=self.max_tokens).text

    def compare(self, item: PairItem) -> PairVerdict:
        first = parse_verdict(self._ask(PAIRWISE_SYSTEM, self._pair_prompt(item, swapped=False)))
        if not self.both_orders:
            return PairVerdict(first, None, resolve(first, None))
        second = _flip(
            parse_verdict(self._ask(PAIRWISE_SYSTEM, self._pair_prompt(item, swapped=True)))
        )
        return PairVerdict(first, second, resolve(first, second))

    def score(self, item: PointItem) -> PointVerdict:
        prompt = POINTWISE_TEMPLATE.format(
            low=self.rubric.low,
            high=self.rubric.high,
            name=self.rubric.name,
            criteria=self.rubric.criteria,
            instruction=_instruction(item.instruction),
            prompt=item.prompt,
            reference=_reference(item.reference),
            response=item.response,
        )
        text = self._ask(POINTWISE_SYSTEM, prompt)
        return PointVerdict(parse_score(text, self.rubric.low, self.rubric.high), text)

    def compare_many(self, items: Sequence[PairItem]) -> list[PairVerdict]:
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return list(pool.map(self.compare, items))

    def score_many(self, items: Sequence[PointItem]) -> list[PointVerdict]:
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return list(pool.map(self.score, items))


def verdict_score(resolved: Decision) -> float:
    """Score of response A: 1 win, 0.5 tie, 0 loss."""
    return {"A": 1.0, "B": 0.0}.get(resolved, 0.5)


def point_verdict(score_a: float | None, score_b: float | None) -> Decision:
    """Pairwise verdict implied by two pointwise scores (equal or missing scores: tie)."""
    if score_a is None or score_b is None or score_a == score_b:
        return "tie"
    return "A" if score_a > score_b else "B"


def position_flip_rate(verdicts: Sequence[PairVerdict]) -> tuple[float, int, int]:
    """(flip rate, items it is over, items with an unparsable reply).

    The rate is the share of items whose two orders disagree, over the items where both
    replies parsed; 0.0 when there are none or when pairs were judged in one order only.
    """
    both = [v for v in verdicts if v.both_valid]
    invalid = sum(1 for v in verdicts if "invalid" in (v.first, v.second))
    if not both:
        return 0.0, 0, invalid
    return sum(v.flipped for v in both) / len(both), len(both), invalid


def _avg_ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=np.float64)
    sorted_x = x[order]
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(x: Sequence[float] | np.ndarray, y: Sequence[float] | np.ndarray) -> float:
    """Spearman rank correlation (average ranks for ties); ``nan`` when either side is constant."""
    xa = np.asarray(x, dtype=np.float64)
    ya = np.asarray(y, dtype=np.float64)
    if xa.size < 2:
        return float("nan")
    rx, ry = _avg_ranks(xa), _avg_ranks(ya)
    sx, sy = rx.std(), ry.std()
    if sx == 0.0 or sy == 0.0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


@dataclass(frozen=True)
class LengthBias:
    """Rank correlation of the verdict with the length difference (A minus B) and the share of
    decided items won by the longer response (length ties excluded)."""

    rho: float
    longer_wins: float
    n: int


def length_bias(resolved: Sequence[Decision], length_diffs: Sequence[float]) -> LengthBias:
    """Length-bias diagnostic over resolved verdicts and ``length(A) - length(B)``."""
    if len(resolved) != len(length_diffs):
        raise ValueError("resolved and length_diffs must have the same length")
    pref = np.array([verdict_score(v) - 0.5 for v in resolved], dtype=np.float64) * 2.0
    diff = np.asarray(length_diffs, dtype=np.float64)
    decided = (pref != 0.0) & (diff != 0.0)
    longer = (
        float(np.mean(np.sign(pref[decided]) == np.sign(diff[decided])))
        if decided.any()
        else float("nan")
    )
    return LengthBias(spearman(pref, diff), longer, len(resolved))


def pairwise_rows(
    *,
    task: str,
    example_id: str,
    model_a: str,
    model_b: str,
    resolved: Decision,
    cluster_id: str | None,
) -> list[dict[str, Any]]:
    """Two ``results.jsonl`` rows (1 / 0.5 / 0 for A, the complement for B) for one pair."""
    s = verdict_score(resolved)
    rows: list[dict[str, Any]] = []
    for model, score in ((model_a, s), (model_b, 1.0 - s)):
        row: dict[str, Any] = {
            "task": task,
            "model": model,
            "example_id": example_id,
            "score": score,
        }
        if cluster_id is not None:
            row["cluster_id"] = cluster_id
        rows.append(row)
    return rows


def pointwise_row(
    *,
    task: str,
    example_id: str,
    model: str,
    score: float,
    cluster_id: str | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"task": task, "model": model, "example_id": example_id, "score": score}
    if cluster_id is not None:
        row["cluster_id"] = cluster_id
    return row


def pair_item_from_row(row: Mapping[str, Any]) -> PairItem:
    """A :class:`PairItem` from a pairs-file row (``prompt``, ``response_a``, ``response_b``,
    optional ``reference``, ``instruction``, ``length_a``, ``length_b``)."""
    return PairItem(
        prompt=str(row["prompt"]),
        response_a=str(row["response_a"]),
        response_b=str(row["response_b"]),
        reference=None if row.get("reference") is None else str(row["reference"]),
        instruction=None if row.get("instruction") is None else str(row["instruction"]),
        length_a=None if row.get("length_a") is None else float(row["length_a"]),
        length_b=None if row.get("length_b") is None else float(row["length_b"]),
    )
