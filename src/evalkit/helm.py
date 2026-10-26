"""Import HELM Lite per-instance results as an evalkit ``results.jsonl``.

HELM Lite (Stanford CRFM, https://crfm.stanford.edu/helm/lite/) publishes, for every model and
scenario, the prediction and the metric value of every evaluation instance in a public bucket
(``gs://crfm-helm-public/lite/benchmark_output``). ``scripts/fetch_helm_lite.py`` downloads the
subset this module needs into a compact layout:

``<root>/core_scenarios.json``      the release's leaderboard table (win rate, scenario scores)
``<root>/runs/<run>.json``          ``{"metric", "scores": {instance_id: value}, "predictions"?}``
``<root>/references/<family>.json`` ``{instance_id: [[reference_text, is_correct], ...]}``

``import_helm_lite`` turns that into one row per (scenario, model, instance) with the scenario's
headline metric as ``score``; ``evalkit compare --all-pairs`` and ``evalkit leaderboard`` then
work on it unchanged.
"""

from __future__ import annotations

import json
import urllib.parse
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Scenario:
    """One column of HELM Lite's ``core_scenarios`` table."""

    column: str  # header prefix, e.g. "GSM8K" for "GSM8K - EM"
    task: str  # evalkit task name
    metric: str  # per-instance metric behind the headline number (schema.json ``main_name``)
    split: str  # schema.json ``main_split``


# main_name / main_split per run group, from the release's schema.json (run_groups).
SCENARIOS: tuple[Scenario, ...] = (
    Scenario("NarrativeQA", "narrativeqa", "f1_score", "test"),
    Scenario("NaturalQuestions (open-book)", "naturalquestions_open", "f1_score", "valid"),
    Scenario("NaturalQuestions (closed-book)", "naturalquestions_closed", "f1_score", "valid"),
    Scenario("OpenbookQA", "openbookqa", "exact_match", "test"),
    Scenario("MMLU", "mmlu", "exact_match", "test"),
    Scenario("MATH", "math", "math_equiv_chain_of_thought", "test"),
    Scenario("GSM8K", "gsm8k", "final_number_exact_match", "test"),
    Scenario("LegalBench", "legalbench", "quasi_exact_match", "test"),
    Scenario("MedQA", "medqa", "quasi_exact_match", "test"),
    Scenario("WMT 2014", "wmt14", "bleu_4", "test"),
)
SCENARIO_BY_COLUMN = {s.column: s for s in SCENARIOS}


def run_file(root: Path, run_name: str) -> Path:
    return root / "runs" / f"{urllib.parse.quote(run_name, safe='')}.json"


def family_of(run_name: str) -> str:
    """Run name without the ``model=`` key, shared by all models: ``mmlu:subject=x,method=y``."""
    name, _, params = run_name.partition(":")
    kept = [p for p in params.split(",") if p and not p.startswith("model=")]
    return name + (":" + ",".join(kept) if kept else "")


def reference_file(root: Path, run_name: str) -> Path:
    return root / "references" / f"{urllib.parse.quote(family_of(run_name), safe='')}.json"


def compact_run(
    predictions: Sequence[Mapping[str, Any]],
    metric: str,
    keep_ids: set[str] | None,
    keep_text: bool,
) -> dict[str, Any]:
    """Reduce HELM's ``display_predictions.json`` to the scores of the instances in ``keep_ids``."""
    scores: dict[str, float] = {}
    texts: dict[str, str] = {}
    for row in predictions:
        iid = str(row["instance_id"])
        if keep_ids is not None and iid not in keep_ids:
            continue
        scores[iid] = float(row["stats"][metric])
        if keep_text:
            texts[iid] = str(row["predicted_text"])
    out: dict[str, Any] = {"metric": metric, "scores": scores}
    if keep_text:
        out["predictions"] = texts
    return out


def compact_references(
    instances: Sequence[Mapping[str, Any]], split: str
) -> dict[str, list[list[Any]]]:
    """Reduce HELM's ``instances.json`` to ``{id: [[reference_text, is_correct], ...]}``."""
    return {
        str(inst["id"]): [
            [str(ref["output"]["text"]), "correct" in ref.get("tags", [])]
            for ref in inst["references"]
        ]
        for inst in instances
        if inst.get("split") == split
    }


@dataclass(frozen=True)
class HelmTable:
    """HELM's published leaderboard: models in the published (mean win rate) order."""

    models: list[str]
    mean_win_rate: dict[str, float]
    published: dict[str, dict[str, float]]  # model -> task -> published scenario score
    runs: dict[str, dict[str, list[str]]]  # model -> task -> run names


def read_table(root: Path) -> HelmTable:
    """Parse ``core_scenarios.json``; models keep the published row order (sorted by win rate)."""
    table = json.loads((root / "core_scenarios.json").read_text(encoding="utf-8"))[0]
    header = [str(h["value"]) for h in table["header"]]
    models: list[str] = []
    mwr: dict[str, float] = {}
    published: dict[str, dict[str, float]] = {}
    runs: dict[str, dict[str, list[str]]] = {}
    for row in table["rows"]:
        name = str(row[0]["value"])
        models.append(name)
        mwr[name] = float(row[1]["value"])
        published[name] = {}
        runs[name] = {}
        for head, cell in zip(header[2:], row[2:], strict=True):
            scenario = SCENARIO_BY_COLUMN.get(head.split(" - ")[0])
            if scenario is None or cell.get("value") is None:
                continue
            published[name][scenario.task] = float(cell["value"])
            runs[name][scenario.task] = list(cell.get("run_spec_names") or [])
    if len(set(models)) != len(models):
        raise ValueError("duplicate model display names in the HELM table")
    order = sorted(range(len(models)), key=lambda i: -mwr[models[i]])
    return HelmTable([models[i] for i in order], mwr, published, runs)


def _example_ids(runs_by_task: Mapping[str, Iterable[str]]) -> dict[str, dict[str, str]]:
    """Per task, run name -> short key made of the run parameters that differ between runs."""
    out: dict[str, dict[str, str]] = {}
    for task, names in runs_by_task.items():
        params = {
            n: dict(p.split("=", 1) for p in family_of(n).partition(":")[2].split(",") if p)
            for n in names
        }
        keys = {k for p in params.values() for k in p}
        varying = sorted(k for k in keys if len({p.get(k) for p in params.values()}) > 1)
        out[task] = {n: "/".join(params[n][k] for k in varying if k in params[n]) for n in names}
    return out


def read_scores(root: Path, table: HelmTable, model: str) -> dict[str, dict[str, float]]:
    """task -> example_id -> score for one model; raises FileNotFoundError on a missing run."""
    ids = _example_ids({t: names for t, names in table.runs[model].items()})
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for task, names in table.runs[model].items():
        for name in names:
            data = json.loads(run_file(root, name).read_text(encoding="utf-8"))
            prefix = ids[task][name]
            for iid, value in data["scores"].items():
                out[task][f"{prefix}/{iid}" if prefix else iid] = float(value)
    return dict(out)


@dataclass(frozen=True)
class ImportStats:
    models: int
    tasks: list[str]
    rows: int
    skipped: list[str]


def import_helm_lite(
    root: Path, out_file: Path, models: Sequence[str] | None = None
) -> ImportStats:
    """Write ``out_file`` (results.jsonl) for the models of ``core_scenarios.json``.

    A model is skipped (and named in ``ImportStats.skipped``) when any run file is missing.
    ``models`` restricts the import to those display names.
    """
    table = read_table(root)
    wanted = list(table.models) if models is None else list(models)
    unknown = [m for m in wanted if m not in table.published]
    if unknown:
        raise KeyError(f"models not in the HELM table: {unknown}")
    metric_of = {s.task: s.metric for s in SCENARIOS}
    rows = 0
    done: list[str] = []
    skipped: list[str] = []
    tasks: set[str] = set()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        for model in wanted:
            try:
                per_task = read_scores(root, table, model)
            except FileNotFoundError:
                skipped.append(model)
                continue
            done.append(model)
            for task in sorted(per_task):
                tasks.add(task)
                for iid, score in sorted(per_task[task].items()):
                    f.write(
                        json.dumps(
                            {
                                "task": task,
                                "model": model,
                                "example_id": iid,
                                "score": score,
                                "metrics": {metric_of[task]: score},
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    rows += 1
    return ImportStats(len(done), sorted(tasks), rows, skipped)
