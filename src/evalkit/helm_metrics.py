"""Cross-check evalkit's metric implementations against HELM's reference outputs, item by item.

HELM Lite stores, for every instance, the model's prediction and the metric value HELM computed
for it. For the models whose prediction text was kept by ``scripts/fetch_helm_lite.py`` this module
re-scores the same (prediction, reference) pairs with evalkit's metrics and compares them with
HELM's value: exact match normalisation (MedQA/LegalBench ``quasi_exact_match``, MMLU/OpenbookQA
``exact_match`` on the answer letter), token F1 (NarrativeQA, NaturalQuestions) and the final-number
metric (GSM8K). MATH (LaTeX equivalence) and WMT (BLEU) are not compared: evalkit has no LaTeX
normaliser, and WMT predictions are not kept.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .helm import HelmTable, read_table, reference_file, run_file
from .metrics.classical import exact_match, f1_score, numeric_match

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
    root: Path, table: HelmTable, task: str, models: Sequence[str], max_examples: int = 3
) -> TaskCheck:
    metric_name, scorer = CHECKS[task]
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


def render_metric_check(checks: Sequence[TaskCheck], n_models: int) -> str:
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
    return "\n".join(lines)


def run_metric_check(root: Path, stride: int = 8) -> str:
    table = read_table(root)
    models = table.models[::stride]
    checks = [check_task_runs(root, table, task, models) for task in CHECKS]
    return render_metric_check(checks, len(models))
