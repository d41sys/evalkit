"""HELM-compatible metric definitions (``metric mode = helm``).

evalkit's default metrics are its own (see ``classical.py``). This module re-implements, with no
dependency on nltk or HELM, the per-instance metrics of Stanford HELM so that the same
(prediction, reference) pair gets the same value as in HELM's published per-instance results.
Source: ``src/helm/benchmark/metrics/evaluate_reference_metrics.py`` (stanford-crfm/helm).

HELM compares ``gold`` against ``pred = completion.text.strip()`` and takes the maximum over the
instance's correct references. Differences from evalkit's defaults (all deliberate there):

- ``exact_match``: HELM is ``gold.strip() == pred.strip()`` (empty pred scores 0); evalkit's is
  equality after lowercasing, removing punctuation and articles.
- ``quasi_exact_match``: HELM lowercases, *then* removes punctuation, *then* articles, then fixes
  whitespace; evalkit's ``exact_match`` removes articles first and keeps them when stripping
  would leave nothing.
- ``f1_score``: HELM is nltk's ``f_measure`` of the *sets* of normalised whitespace tokens (0 if
  either side is empty); evalkit's is multiset (Counter) overlap on ``\\w+`` tokens.
- ``final_number_exact_match``: HELM is string equality of the last ``-?[\\d,]+(.\\d+)?`` match
  with commas dropped; evalkit's ``numeric_match`` takes the number after the last answer marker
  (else the last number) and compares floats.
- multiple choice: HELM maps a letter completion to the choice text before scoring and scores 0
  for anything else (see :func:`score_helm_multiple_choice`).
"""

from __future__ import annotations

import re
import string
from collections.abc import Callable, Sequence

HelmScorer = Callable[[str, str], float]


def helm_normalize_text(text: str, should_remove_articles: bool = True) -> str:
    """HELM ``normalize_text``: lower, remove punctuation, remove articles, fix whitespace."""
    exclude = set(string.punctuation)
    out = "".join(ch for ch in text.lower() if ch not in exclude)
    if should_remove_articles:
        out = re.sub(r"\b(a|an|the)\b", " ", out)
    return " ".join(out.split())


def f_measure(reference: set[str], test: set[str], alpha: float = 0.5) -> float | None:
    """``nltk.metrics.scores.f_measure`` on sets; ``None`` when either set is empty."""
    if not test or not reference:
        return None
    overlap = len(reference & test)
    precision = overlap / len(test)
    recall = overlap / len(reference)
    if precision == 0 or recall == 0:
        return 0.0
    return 1.0 / (alpha / precision + (1 - alpha) / recall)


def helm_exact_match(gold: str, pred: str) -> float:
    if not pred:
        return 0.0
    return 1.0 if gold.strip() == pred.strip() else 0.0


def helm_quasi_exact_match(gold: str, pred: str) -> float:
    if not pred:
        return 0.0
    return 1.0 if helm_normalize_text(gold) == helm_normalize_text(pred) else 0.0


def helm_f1_score(gold: str, pred: str) -> float:
    """Set-based token F1; 0.0 when either side is empty after normalisation (as in HELM)."""
    ret = f_measure(set(helm_normalize_text(gold).split()), set(helm_normalize_text(pred).split()))
    return 0.0 if ret is None else ret


# The "." is unescaped in HELM's pattern (any character), reproduced on purpose.
_FINAL_NUMBER_RE = re.compile(r"-?[\d,]+(?:.\d+)?")


def _helm_final_number(text: str) -> str:
    matches = _FINAL_NUMBER_RE.findall(text)
    return matches[-1].replace(",", "") if matches else ""


def helm_final_number_exact_match(gold: str, pred: str) -> float:
    """1.0 iff the final number of gold and pred are the same string (HELM's GSM8K metric)."""
    return helm_exact_match(_helm_final_number(gold), _helm_final_number(pred))


HELM_METRICS: dict[str, HelmScorer] = {
    "exact_match": helm_exact_match,
    "quasi_exact_match": helm_quasi_exact_match,
    "f1_score": helm_f1_score,
    "final_number_exact_match": helm_final_number_exact_match,
}

# evalkit metric names accepted in helm mode -> HELM metric. ``exact_match`` is HELM's *strict*
# one; ask for ``quasi_exact_match`` for the normalised comparison.
_ALIASES = {
    "em": "exact_match",
    "accuracy": "exact_match",
    "acc": "exact_match",
    "f1": "f1_score",
    "token_f1": "f1_score",
    "numeric_match": "final_number_exact_match",
    "numeric": "final_number_exact_match",
}


def helm_metric_name(name: str) -> str:
    """Canonical HELM metric name for an evalkit metric name; ValueError if HELM mode lacks it."""
    key = name.lower().strip()
    key = _ALIASES.get(key, key)
    if key not in HELM_METRICS:
        raise ValueError(
            f"No HELM-compatible definition of metric {name!r} (available: "
            f"{', '.join(sorted(HELM_METRICS))})"
        )
    return key


def score_helm(metric_name: str, prediction: str, targets: Sequence[str] | str) -> float:
    """HELM's value of ``metric_name`` for one prediction: max over the correct references."""
    fn = HELM_METRICS[helm_metric_name(metric_name)]
    target_list = [targets] if isinstance(targets, str) else list(targets)
    if not target_list:
        return 0.0
    pred = prediction.strip()
    return max(fn(gold, pred) for gold in target_list)


def score_helm_multiple_choice(
    metric_name: str, prediction: str, choices: Sequence[str], correct: Sequence[bool]
) -> float:
    """HELM's value for a multiple-choice instance shown with lettered options.

    HELM maps the stripped completion through ``output_mapping`` (``"A"`` -> text of the first
    choice, ...) *before* scoring it against the text of the correct choices. A completion that is
    not exactly a letter maps to ``None`` and scores 0, whatever the metric: scoring letters
    instead would let ``"The"`` equal gold ``"A"`` under article stripping.
    """
    letters = {chr(ord("A") + i): text for i, text in enumerate(choices)}
    mapped = letters.get(prediction.strip())
    if mapped is None:
        return 0.0
    golds = [text for text, ok in zip(choices, correct, strict=True) if ok]
    return score_helm(metric_name, mapped, golds)
