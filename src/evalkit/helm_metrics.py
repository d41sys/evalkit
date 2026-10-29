"""Cross-check evalkit's metric implementations against HELM's reference outputs, item by item.

HELM Lite stores, for every instance, the model's prediction and the metric value HELM computed
for it. For the models whose prediction text was kept by ``scripts/fetch_helm_lite.py`` this module
re-scores the same (prediction, reference) pairs with evalkit's metrics and compares them with
HELM's value: exact match normalisation (MedQA/LegalBench ``quasi_exact_match``, MMLU/OpenbookQA
``exact_match`` on the answer letter), token F1 (NarrativeQA, NaturalQuestions), the final-number
metric (GSM8K) and ECE (OpenbookQA, MedQA runs of models with log-probs; HELM's ``ece_1_bin`` and
``ece_10_bin`` against evalkit's ``expected_calibration_error``). MATH (LaTeX equivalence) and WMT
(BLEU) are not compared: evalkit has no LaTeX normaliser, and WMT predictions are not kept.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .helm import CALIBRATION_TASKS, SCENARIOS, HelmTable, read_table, reference_file, run_file
from .metrics.calibration import expected_calibration_error, expected_calibration_error_equal_mass
from .metrics.classical import MetricMode, exact_match, f1_score, numeric_match
from .metrics.helm_compat import score_helm, score_helm_multiple_choice

HELM_METRIC = {s.task: s.metric for s in SCENARIOS}
MC_TASKS = frozenset({"openbookqa", "mmlu", "medqa"})
Scorer = Callable[[str, list[str]], float]

# task -> (evalkit metric name, scorer(prediction, gold_texts)); MC gold is the answer letter.
CHECKS: dict[str, tuple[str, Scorer]] = {
    "openbookqa": ("exact_match", exact_match),
    "mmlu": ("exact_match", exact_match),
    "medqa": ("exact_match", exact_match),
    "legalbench": ("exact_match", exact_match),
    "narrativeqa": ("f1_score", f1_score),
    "naturalquestions_open": ("f1_score", f1_score),
    "naturalquestions_closed": ("f1_score", f1_score),
    "gsm8k": ("numeric_match", numeric_match),
}


@dataclass
class TaskCheck:
    task: str
    evalkit_metric: str
    n: int = 0
    agree: int = 0
    evalkit_higher: int = 0
    evalkit_lower: int = 0
    sum_evalkit: float = 0.0
    sum_helm: float = 0.0
    sum_abs_diff: float = 0.0
    models: set[str] = field(default_factory=set)
    examples: list[tuple[str, str, float, float]] = field(default_factory=list)
    # per model: [sum evalkit, sum helm, n]
    per_model: dict[str, list[float]] = field(default_factory=dict)


def gold_texts(task: str, references: Sequence[Sequence[object]]) -> list[str]:
    """Gold strings for one instance: the answer letter for multiple choice, else correct texts."""
    if task in MC_TASKS:
        return [chr(ord("A") + i) for i, (_, ok) in enumerate(references) if ok]
    return [str(text) for text, ok in references if ok]


def check_task_runs(
    root: Path,
    table: HelmTable,
    task: str,
    models: Sequence[str],
    max_examples: int = 3,
    mode: MetricMode = "evalkit",
) -> TaskCheck:
    metric_name, scorer = CHECKS[task]
    if mode == "helm":
        helm_name = HELM_METRIC[task]
        metric_name = f"helm:{helm_name}"

        def scorer(pred: str, gold: list[str]) -> float:
            return score_helm(helm_name, pred, gold)

    out = TaskCheck(task, metric_name)
    for model in models:
        for run in table.runs[model].get(task, []):
            data = json.loads(run_file(root, run).read_text(encoding="utf-8"))
            preds = data.get("predictions")
            if preds is None:
                continue
            refs = json.loads(reference_file(root, run).read_text(encoding="utf-8"))
            for iid, helm_score in data["scores"].items():
                gold = gold_texts(task, refs[iid])
                pred = preds[iid]
                if mode == "helm" and task in MC_TASKS:
                    ours = score_helm_multiple_choice(
                        HELM_METRIC[task],
                        pred,
                        [str(text) for text, _ in refs[iid]],
                        [bool(ok) for _, ok in refs[iid]],
                    )
                else:
                    ours = scorer(pred, gold)
                out.n += 1
                out.sum_evalkit += ours
                out.sum_helm += helm_score
                out.sum_abs_diff += abs(ours - helm_score)
                out.models.add(model)
                acc = out.per_model.setdefault(model, [0.0, 0.0, 0.0])
                acc[0] += ours
                acc[1] += helm_score
                acc[2] += 1
                if abs(ours - helm_score) < 1e-9:
                    out.agree += 1
                else:
                    out.evalkit_higher += ours > helm_score
                    out.evalkit_lower += ours < helm_score
                    if len(out.examples) < max_examples:
                        out.examples.append((pred[-80:], " | ".join(gold)[:60], ours, helm_score))
    return out


def kendall_tau(a: Sequence[float], b: Sequence[float]) -> float:
    """Kendall tau-a between two score lists (ties count as neither concordant nor discordant)."""
    n = len(a)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (a[i] - a[j]) * (b[i] - b[j])
            conc += s > 0
            disc += s < 0
    return (conc - disc) / (n * (n - 1) / 2) if n > 1 else 1.0


@dataclass(frozen=True)
class CalibrationCheck:
    model: str
    task: str
    n: int
    helm_ece_1: float
    evalkit_ece_1: float
    helm_ece_10: float
    evalkit_ece_10: float
    evalkit_ece_10_mass: float


def check_calibration(
    root: Path, table: HelmTable, models: Sequence[str]
) -> list[CalibrationCheck]:
    """ECE of the runs whose calibration inputs were kept, HELM's value against evalkit's."""
    out: list[CalibrationCheck] = []
    for model in models:
        for task in sorted(CALIBRATION_TASKS):
            for run in table.runs[model].get(task, []):
                cal = json.loads(run_file(root, run).read_text(encoding="utf-8")).get("calibration")
                if not cal:
                    continue
                ids = sorted(cal["max_prob"])
                conf = [cal["max_prob"][i] for i in ids]
                correct = [cal["correct"][i] for i in ids]
                out.append(
                    CalibrationCheck(
                        model,
                        task,
                        len(ids),
                        float(cal["ece_1_bin"]),
                        expected_calibration_error(conf, correct, n_bins=1),
                        float(cal["ece_10_bin"]),
                        expected_calibration_error(conf, correct, n_bins=10),
                        expected_calibration_error_equal_mass(conf, correct, n_bins=10),
                    )
                )
    return out


def render_metric_check(
    checks: Sequence[TaskCheck],
    n_models: int,
    calibration: Sequence[CalibrationCheck] = (),
    helm_checks: Sequence[TaskCheck] = (),
) -> str:
    lines = [
        "# evalkit metrics vs HELM reference values, same predictions",
        "",
        f"Predictions of {n_models} HELM Lite models (every 8th model of the published ranking) "
        "re-scored with evalkit's metric and compared with the value HELM stored for the same "
        "instance. HELM definitions: `exact_match` = `gold.strip() == pred.strip()`; "
        "`quasi_exact_match` = lowercase, remove punctuation, remove articles, fix whitespace, "
        "then equality; `f1_score` = nltk `f_measure` on the *sets* of normalised whitespace "
        "tokens; `final_number_exact_match` = string equality of the last `-?[\\d,]+(.\\d+)?` "
        "match (source: `evaluate_reference_metrics.py` in stanford-crfm/helm).",
        "",
        "| scenario | evalkit metric | instances | identical to HELM | evalkit higher | "
        "evalkit lower | mean evalkit | mean HELM | mean abs diff | "
        "Kendall tau of the model means |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in checks:
        if c.n == 0:
            continue
        models = sorted(c.per_model)
        ours = [c.per_model[m][0] / c.per_model[m][2] for m in models]
        helm = [c.per_model[m][1] / c.per_model[m][2] for m in models]
        lines.append(
            f"| {c.task} | {c.evalkit_metric} | {c.n} | {c.agree / c.n:.2%} | "
            f"{c.evalkit_higher} | {c.evalkit_lower} | "
            f"{c.sum_evalkit / c.n:.4f} | {c.sum_helm / c.n:.4f} | {c.sum_abs_diff / c.n:.4f} | "
            f"{kendall_tau(ours, helm):.2f} |"
        )
    lines += ["", "First disagreements (prediction tail | evalkit gold | evalkit | HELM):", ""]
    for c in checks:
        for pred, gold, mine, ref in c.examples:
            lines.append(f"- {c.task}: `{pred!r}` | `{gold}` | {mine:.3f} | {ref:.3f}")
    lines.append("")
    if helm_checks:
        lines += _render_helm_mode(helm_checks, n_models)
    if calibration:
        lines += [
            "## ECE",
            "",
            "HELM computes `ece_1_bin` and `ece_10_bin` (equal-mass bins, `calibration` package, "
            "`basic_metrics.py`) from each instance's `max_prob` and `exact_match`. evalkit's "
            "default `expected_calibration_error` uses equal-width bins; with one bin both are "
            "|mean confidence - accuracy|. `expected_calibration_error_equal_mass` (helm mode, "
            "`--metric-mode helm`) is the equal-mass estimator. Runs of models without log-probs "
            "have no HELM ECE.",
            "",
            "| model | scenario | n | HELM ece_1_bin | evalkit ECE (1 bin) | HELM ece_10_bin "
            "(equal-mass) | evalkit default (10 equal-width bins) | evalkit helm mode "
            "(10 equal-mass bins) | helm mode identical to HELM (1e-9) |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        lines += [
            f"| {c.model} | {c.task} | {c.n} | {c.helm_ece_1:.4f} | {c.evalkit_ece_1:.4f} | "
            f"{c.helm_ece_10:.4f} | {c.evalkit_ece_10:.4f} | {c.evalkit_ece_10_mass:.4f} | "
            f"{'yes' if abs(c.evalkit_ece_10_mass - c.helm_ece_10) < 1e-9 else 'NO'} |"
            for c in calibration
        ]
        lines.append("")
    return "\n".join(lines)


def _render_helm_mode(helm_checks: Sequence[TaskCheck], n_models: int) -> list[str]:
    total = sum(c.n for c in helm_checks)
    same = sum(c.agree for c in helm_checks)
    lines = [
        "## helm mode (`evalkit.metrics.helm_compat`, `--metric-mode helm`)",
        "",
        "The same predictions scored with evalkit's HELM-compatible metrics (set-based token F1, "
        "HELM's `normalize_text` order, strict `exact_match`, `final_number_exact_match`), "
        f"{n_models} models. Total: {same} of {total} instances identical "
        f"({same / total:.4%}).",
        "",
        "| scenario | helm-mode metric | instances | identical to HELM | evalkit higher | "
        "evalkit lower | mean evalkit | mean HELM | mean abs diff | "
        "Kendall tau of the model means |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in helm_checks:
        if c.n == 0:
            continue
        models = sorted(c.per_model)
        ours = [c.per_model[m][0] / c.per_model[m][2] for m in models]
        helm = [c.per_model[m][1] / c.per_model[m][2] for m in models]
        lines.append(
            f"| {c.task} | {c.evalkit_metric} | {c.n} | {c.agree / c.n:.4%} | "
            f"{c.evalkit_higher} | {c.evalkit_lower} | "
            f"{c.sum_evalkit / c.n:.4f} | {c.sum_helm / c.n:.4f} | {c.sum_abs_diff / c.n:.4f} | "
            f"{kendall_tau(ours, helm):.2f} |"
        )
    unequal = [c for c in helm_checks if c.examples]
    if unequal:
        lines += ["", "Remaining disagreements (prediction tail | gold | helm mode | HELM):", ""]
        for c in unequal:
            for pred, gold, mine, ref in c.examples:
                lines.append(f"- {c.task}: `{pred!r}` | `{gold}` | {mine:.3f} | {ref:.3f}")
    lines.append("")
    return lines


def run_metric_check(root: Path, stride: int = 8) -> str:
    table = read_table(root)
    models = table.models[::stride]
    checks = [check_task_runs(root, table, task, models) for task in CHECKS]
    helm_checks = [check_task_runs(root, table, task, models, mode="helm") for task in CHECKS]
    return render_metric_check(
        checks, len(models), check_calibration(root, table, models), helm_checks
    )
