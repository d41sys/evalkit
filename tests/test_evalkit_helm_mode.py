"""HELM-compatible metric mode: definitions copied from HELM / verified_calibration as oracles."""

from __future__ import annotations

import bisect
import re
import string

import numpy as np
import pytest

from evalkit.cli import _helm_metrics
from evalkit.metrics.calibration import (
    expected_calibration_error,
    expected_calibration_error_equal_mass,
)
from evalkit.metrics.classical import f1_score, numeric_match, score_classical
from evalkit.metrics.helm_compat import (
    f_measure,
    helm_f1_score,
    helm_final_number_exact_match,
    helm_metric_name,
    helm_normalize_text,
    helm_quasi_exact_match,
    score_helm,
    score_helm_multiple_choice,
)
from evalkit.runner import EvalRecord, generate_leaderboard

# --- oracles: verbatim from stanford-crfm/helm (evaluate_reference_metrics.py), nltk inlined -----


def _oracle_normalize(text: str, should_remove_articles: bool = True) -> str:
    def remove_articles(t: str) -> str:
        return re.sub(r"\b(a|an|the)\b", " ", t)

    def white_space_fix(t: str) -> str:
        return " ".join(t.split())

    def remove_punc(t: str) -> str:
        exclude = set(string.punctuation)
        return "".join(ch for ch in t if ch not in exclude)

    normalized = remove_punc(text.lower())
    if should_remove_articles:
        normalized = remove_articles(normalized)
    return white_space_fix(normalized)


def _oracle_nltk_f_measure(reference: set[str], test: set[str], alpha: float = 0.5) -> float | None:
    # nltk.metrics.scores: precision/recall return None on an empty set; f_measure follows.
    p = None if len(test) == 0 else len(reference.intersection(test)) / len(test)
    r = None if len(reference) == 0 else len(reference.intersection(test)) / len(reference)
    if p is None or r is None:
        return None
    if p == 0 or r == 0:
        return 0.0
    return float(1.0 / (alpha / p + (1 - alpha) / r))


def _oracle_final_number(gold: str, pred: str) -> float:
    def get_final_number(x: str) -> str:
        matches = re.findall(r"-?[\d,]+(?:.\d+)?", x)
        if not matches:
            return ""
        return matches[-1].replace(",", "")

    g, p = get_final_number(gold), get_final_number(pred)
    if not p:
        return 0
    return 1 if g.strip() == p.strip() else 0


# --- oracle: verified_calibration (get_ece_em: equal-mass bins, p=1, no debiasing) --------------


def _oracle_ece_em(probs: list[float], labels: list[int], num_bins: int = 10) -> float:
    sorted_probs = sorted(probs)
    nb = min(num_bins, len(sorted_probs))
    parts = [list(x) for x in np.array_split(sorted_probs, nb)]
    bins = [(parts[i][-1] + parts[i + 1][0]) / 2.0 for i in range(len(parts) - 1)]
    bins.append(1.0)
    bins = sorted(set(bins))
    groups: list[list[tuple[float, int]]] = [[] for _ in bins]
    for p, y in zip(probs, labels, strict=True):
        groups[bisect.bisect_left(bins, p)].append((p, y))
    n = len(probs)
    total = 0.0
    for g in groups:
        if g:
            total += len(g) / n * abs(np.mean([p for p, _ in g]) - np.mean([y for _, y in g]))
    return float(total)


def test_normalize_order_differs_from_evalkit() -> None:
    for text in ["The cat's hat", "A.", "an 'apple'", "  The  END. ", "the"]:
        assert helm_normalize_text(text) == _oracle_normalize(text)
    # HELM removes punctuation first, so "a-b" becomes "ab"; articles inside stay words
    assert helm_normalize_text("The") == ""  # no fallback, unlike evalkit's normalize_text
    assert helm_quasi_exact_match("A", "The") == 1.0


def test_f1_is_set_based_and_matches_nltk_f_measure() -> None:
    cases = [
        ("the cat sat on the mat", "a cat sat"),
        ("Crystal ship", "A crystal ship."),
        ("", "x"),
        ("x", ""),
        ("the", "a"),  # both empty after normalisation
        ("1 2 3 4", "5 6"),
        ("new york new york", "new york"),
    ]
    for gold, pred in cases:
        want = _oracle_nltk_f_measure(
            set(_oracle_normalize(gold).split()), set(_oracle_normalize(pred).split())
        )
        assert helm_f1_score(gold, pred) == (0.0 if want is None else want)
    # set semantics: repeated tokens do not count twice (evalkit's multiset F1 does)
    assert helm_f1_score("new york new york", "new york") == 1.0
    assert f1_score("new york new york", ["new york"]) < 1.0
    assert f_measure(set(), {"a"}) is None


def test_final_number_exact_match_is_helm_string_equality() -> None:
    cases = [
        ("so 15 eggs. #### 15", "The answer is 15 eggs"),
        ("#### 1,234", "total 1234"),
        ("#### 18", "18.0"),  # string equality: HELM says no, evalkit's float compare says yes
        ("#### 5", "no digits here"),
        ("#### 3", "range 3-4"),  # unescaped "." in the pattern: "3-4" is one match
        ("#### 0.5", "0.50"),
    ]
    for gold, pred in cases:
        assert helm_final_number_exact_match(gold, pred) == _oracle_final_number(gold, pred)
    assert numeric_match("18.0", ["18"]) == 1.0
    assert helm_final_number_exact_match("18", "18.0") == 0.0


def test_score_helm_strips_and_maximises() -> None:
    assert score_helm("exact_match", "  yes \n", ["no", "yes"]) == 1.0
    assert score_helm("exact_match", "Yes", ["yes"]) == 0.0  # strict, unlike evalkit
    assert score_helm("quasi_exact_match", "Yes.", ["yes"]) == 1.0
    assert score_helm("f1", "cat", ["dog", "big cat"]) == pytest.approx(2 / 3)
    assert score_helm("exact_match", "", ["x"]) == 0.0
    assert score_helm("exact_match", "x", []) == 0.0


def test_dispatcher_modes() -> None:
    assert score_classical("exact_match", "Yes", ["yes"]) == 1.0
    assert score_classical("exact_match", "Yes", ["yes"], mode="helm") == 0.0
    assert score_classical("helm:exact_match", "Yes", ["yes"]) == 0.0
    assert score_classical("helm:f1_score", "new york", ["new york new york"]) == 1.0
    assert score_classical("numeric_match", "18.0", ["18"], mode="helm") == 0.0
    with pytest.raises(ValueError, match="No HELM-compatible"):
        score_classical("bleu_4", "a", ["a"], mode="helm")
    with pytest.raises(ValueError, match="Unknown metric mode"):
        score_classical("exact_match", "a", ["a"], mode="nope")  # type: ignore[arg-type]


def test_helm_metric_names_and_cli_rewrite() -> None:
    assert helm_metric_name("f1") == "f1_score"
    assert helm_metric_name("numeric_match") == "final_number_exact_match"
    assert _helm_metrics(["exact_match", "f1", "helm:quasi_exact_match"]) == [
        "helm:exact_match",
        "helm:f1_score",
        "helm:quasi_exact_match",
    ]


def test_multiple_choice_output_mapping() -> None:
    choices = ["Aspirin", "Heparin", "Warfarin"]
    ok = [False, True, False]
    assert score_helm_multiple_choice("quasi_exact_match", "B", choices, ok) == 1.0
    assert score_helm_multiple_choice("quasi_exact_match", " B\n", choices, ok) == 1.0
    assert score_helm_multiple_choice("quasi_exact_match", "A", choices, ok) == 0.0
    # not a letter -> unmapped -> 0, even though "The" and gold "A" both normalise to ""
    assert score_helm_multiple_choice("quasi_exact_match", "The", ["x", "y"], [True, False]) == 0.0
    assert score_helm_multiple_choice("exact_match", "Heparin", choices, ok) == 0.0


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("n", [1, 7, 10, 11, 99, 503])
def test_equal_mass_ece_matches_verified_calibration(seed: int, n: int) -> None:
    rng = np.random.default_rng(seed)
    conf = rng.random(n)
    if seed % 3 == 0:  # ties, including at the top
        conf = np.round(conf * 4) / 4
    conf[: min(2, n)] = 1.0
    correct = (rng.random(n) < conf * 0.8).astype(int)
    got = expected_calibration_error_equal_mass(list(conf), list(correct), n_bins=10)
    want = _oracle_ece_em(list(conf), list(correct), 10)
    assert got == pytest.approx(want, abs=1e-12)


def test_equal_mass_ece_edges() -> None:
    assert expected_calibration_error_equal_mass([], []) == 0.0
    with pytest.raises(ValueError):
        expected_calibration_error_equal_mass([0.5], [1], n_bins=0)
    conf = [0.1, 0.4, 0.8, 0.9]
    correct = [0, 1, 1, 1]
    # one bin = |mean conf - accuracy| for both estimators
    assert expected_calibration_error_equal_mass(conf, correct, n_bins=1) == pytest.approx(
        expected_calibration_error(conf, correct, n_bins=1)
    )
    # more bins than points: every point its own bin -> mean |conf - correct|
    assert expected_calibration_error_equal_mass(conf, correct, n_bins=50) == pytest.approx(
        float(np.mean(np.abs(np.array(conf) - np.array(correct))))
    )


def test_leaderboard_ece_binning_switch() -> None:
    rng = np.random.default_rng(3)
    recs = [
        EvalRecord(
            task="t",
            model="m",
            example_id=f"e{i}",
            score=float(i % 2),
            metrics={},
            prediction="",
            targets=[],
            confidence=float(c),
            correct=int(i % 2),
        )
        for i, c in enumerate(rng.random(60))
    ]
    width = generate_leaderboard(recs).models[0].ece
    mass = generate_leaderboard(recs, ece_binning="equal_mass").models[0].ece
    assert width != mass
    assert mass == pytest.approx(
        expected_calibration_error_equal_mass(
            [r.confidence for r in recs], [r.correct for r in recs]
        )
    )


def test_cli_parser_accepts_metric_mode() -> None:
    from evalkit.cli import main

    with pytest.raises(SystemExit):
        main(["run", "--tasks", "x", "--metric-mode", "bogus"])
