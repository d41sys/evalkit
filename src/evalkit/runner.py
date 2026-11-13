from __future__ import annotations

import json
import threading
from collections import defaultdict
from collections.abc import Callable, Hashable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Literal

from .aggregate import (
    LeaderboardReport,
    ModelSummary,
    build_pairwise_matches,
    compare_pairs,
    compute_elo_ratings,
    leaderboard_ci,
    pareto_frontier,
)
from .metrics.calibration import (
    brier_score,
    expected_calibration_error,
    expected_calibration_error_equal_mass,
)
from .metrics.classical import score_classical
from .metrics.code_exec import run_code_exec
from .models import BatchModel, Model, Prediction
from .ranking import bradley_terry_bootstrap
from .spec import TaskSpec

EceBinning = Literal["equal_width", "equal_mass"]
# equal_width: evalkit default (15 equal-width bins); equal_mass: HELM ece_10_bin (10 bins).


@dataclass
class EvalRecord:
    task: str
    model: str
    example_id: str
    score: float
    metrics: dict[str, float]
    prediction: str
    targets: list[str]
    confidence: float
    correct: int
    token_nll: float = 0.0
    token_count: int = 1
    cluster_id: str | None = None
    sample: int = 0
    cost_usd: float | None = None
    latency_s: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "model": self.model,
            "example_id": self.example_id,
            "score": self.score,
            "metrics": self.metrics,
            "prediction": self.prediction,
            "targets": self.targets,
            "confidence": self.confidence,
            "correct": self.correct,
            "token_nll": self.token_nll,
            "token_count": self.token_count,
            **({"cluster_id": self.cluster_id} if self.cluster_id is not None else {}),
            **({"sample": self.sample} if self.sample else {}),
            **({"cost_usd": self.cost_usd} if self.cost_usd is not None else {}),
            **({"latency_s": self.latency_s} if self.latency_s is not None else {}),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EvalRecord:
        return cls(
            task=str(d["task"]),
            model=str(d["model"]),
            example_id=str(d["example_id"]),
            score=float(d["score"]),
            metrics={k: float(v) for k, v in d.get("metrics", {}).items()},
            prediction=str(d.get("prediction", "")),
            targets=[str(t) for t in d.get("targets", [])],
            confidence=float(d.get("confidence", 0.5)),
            correct=int(d.get("correct", 0)),
            token_nll=float(d.get("token_nll", 0.0)),
            token_count=int(d.get("token_count", 1)),
            cluster_id=None if d.get("cluster_id") is None else str(d["cluster_id"]),
            sample=int(d.get("sample", 0)),
            cost_usd=None if d.get("cost_usd") is None else float(d["cost_usd"]),
            latency_s=None if d.get("latency_s") is None else float(d["latency_s"]),
        )


@dataclass
class EvalSummary:
    records: list[EvalRecord]
    leaderboard: LeaderboardReport
    out_dir: Path
    total_evaluated: int
    total_skipped: int
    results_path: Path
    leaderboard_path: Path


def _extract_targets(example: dict[str, Any]) -> list[str]:
    if "targets" in example and isinstance(example["targets"], list):
        return [str(t) for t in example["targets"]]
    if "target" in example and example["target"] is not None:
        return [str(example["target"])]
    if "answer" in example and example["answer"] is not None:
        return [str(example["answer"])]
    if "canonical_solution" in example and example["canonical_solution"] is not None:
        return [str(example["canonical_solution"])]
    return []


# Task types answered by free generation, which a BatchModel may decode several at a time.
_BATCHABLE_TYPES = frozenset({"generation", "reasoning"})


def _evaluate_single(
    spec: TaskSpec,
    model: Model,
    example: dict[str, Any],
    example_id: str,
    labels: Sequence[str] | None = None,
    sample: int = 0,
) -> EvalRecord:
    prompt = spec.render_prompt(example)
    choices = example.get("choices") or labels

    # Sample 0 calls the model exactly as a single-sample run does; later samples add
    # ``sample=`` so a stochastic model can draw independently (greedy models repeat sample 0).
    extra: dict[str, Any] = {"sample": sample} if sample else {}
    pred = model.predict(
        prompt,
        task_type=spec.type,
        choices=choices,
        example=example,
        **extra,
    )
    return _score_prediction(spec, model.name, example, example_id, pred, sample)


def _evaluate_one(
    spec: TaskSpec,
    model: Model,
    example: dict[str, Any],
    example_id: str,
    labels: Sequence[str] | None,
    sample: int = 0,
) -> list[EvalRecord]:
    return [_evaluate_single(spec, model, example, example_id, labels, sample)]


def _evaluate_batch(
    spec: TaskSpec, model: BatchModel, batch: Sequence[tuple[dict[str, Any], str]]
) -> list[EvalRecord]:
    prompts = [spec.render_prompt(row) for row, _ in batch]
    preds = model.predict_batch(prompts, spec.type)
    return [
        _score_prediction(spec, model.name, row, ex_id, pred)
        for (row, ex_id), pred in zip(batch, preds, strict=True)
    ]


def _score_prediction(
    spec: TaskSpec,
    model_name: str,
    example: dict[str, Any],
    example_id: str,
    pred: Prediction,
    sample: int = 0,
) -> EvalRecord:
    targets = _extract_targets(example)
    metrics_dict: dict[str, float] = {}

    if spec.type == "code":
        tests = example.get("tests", [])
        code_result = run_code_exec(pred.text, tests, timeout_s=10.0)
        primary_score = 1.0 if code_result.status == "pass" else 0.0
        correct_flag = 1 if code_result.status == "pass" else 0
        metrics_dict["code_exec"] = primary_score
        for m in spec.metrics:
            if m != "code_exec":
                try:
                    metrics_dict[m] = score_classical(m, pred.text, targets)
                except ValueError:
                    metrics_dict[m] = primary_score
    else:
        for m in spec.metrics:
            metrics_dict[m] = score_classical(m, pred.text, targets)
        primary_metric = spec.metrics[0] if spec.metrics else "exact_match"
        primary_score = metrics_dict.get(primary_metric, 0.0)
        correct_flag = 1 if primary_score >= 0.99 else 0

    return EvalRecord(
        task=spec.name,
        model=model_name,
        example_id=example_id,
        score=primary_score,
        metrics=metrics_dict,
        prediction=pred.text,
        targets=targets,
        confidence=pred.confidence,
        correct=correct_flag,
        token_nll=pred.token_nll,
        token_count=pred.token_count,
        cluster_id=spec.cluster_of(example),
        sample=sample,
    )


def _mean_or_none(vals: Sequence[float | None]) -> float | None:
    """Mean over the rows that carry the field; None when none do."""
    present = [v for v in vals if v is not None]
    return float(sum(present) / len(present)) if present else None


def generate_leaderboard(
    records: Sequence[EvalRecord],
    ece_binning: EceBinning = "equal_width",
    bradley_terry: bool = False,
    bt_resamples: int = 200,
) -> LeaderboardReport:
    """Build LeaderboardReport from all evaluation records."""
    if not records:
        return LeaderboardReport(models=[])

    # Group records by model and by (example_id, task); several samples of one item are
    # averaged first, so the item (not the sample) is the unit of every statistic below.
    by_model: dict[str, list[EvalRecord]] = defaultdict(list)
    item_samples: dict[str, dict[tuple[str, str], list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    by_example: dict[str, dict[str, float]] = defaultdict(dict)
    all_tasks: set[str] = set()

    for r in records:
        by_model[r.model].append(r)
        item_samples[r.model][(r.task, r.example_id)].append(r.score)
        by_example[f"{r.task}::{r.example_id}"].setdefault(r.model, 0.0)  # fixes Elo game order
        all_tasks.add(r.task)
    for model_name, items in item_samples.items():
        for (task, example_id), vals in items.items():
            by_example[f"{task}::{example_id}"][model_name] = float(sum(vals) / len(vals))

    # Cluster ids (items that share a source): ``(task, cluster_id)`` per item, and per Elo key
    item_cluster: dict[tuple[str, str], Hashable] = {}
    for r in records:
        if r.cluster_id is not None:
            item_cluster[(r.task, r.example_id)] = (r.task, r.cluster_id)
    clustered_tasks = {task for task, _ in item_cluster}
    cluster_of: dict[str, Hashable] = {f"{t}::{e}": lab for (t, e), lab in item_cluster.items()}

    # Compute pairwise Elo ratings
    matches = build_pairwise_matches(by_example)
    elo_ratings = compute_elo_ratings(matches, base_rating=1000.0, k_factor=32.0)

    # Compute win rates
    win_counts: dict[str, float] = defaultdict(float)
    total_comparisons: dict[str, int] = defaultdict(int)
    for ma, mb, sa in matches:
        total_comparisons[ma] += 1
        total_comparisons[mb] += 1
        win_counts[ma] += sa
        win_counts[mb] += 1.0 - sa

    model_summaries: list[ModelSummary] = []

    for model_name, recs in by_model.items():
        # Per-task means
        task_scores: dict[str, list[float]] = defaultdict(list)
        for (task, _), vals in item_samples[model_name].items():
            task_scores[task].append(float(sum(vals) / len(vals)))

        per_task_means: dict[str, float] = {
            t: float(sum(scores) / len(scores)) for t, scores in task_scores.items()
        }

        # Macro average with a stratified bootstrap CI over the same statistic; tasks whose rows
        # carry a cluster_id resample whole clusters
        task_labels: dict[str, list[Hashable]] = defaultdict(list)
        for task, example_id in item_samples[model_name]:
            task_labels[task].append(
                item_cluster.get((task, example_id), ("\0singleton", example_id))
            )
        clustered_scores = {t: task_labels[t] for t in task_scores if t in clustered_tasks}
        macro_mean, ci_lo, ci_hi, ci_method = leaderboard_ci(
            task_scores, num_resamples=1000, seed=0, task_clusters=clustered_scores or None
        )

        # Calibration
        confs = [r.confidence for r in recs]
        corrs = [r.correct for r in recs]
        if ece_binning == "equal_mass":
            ece = expected_calibration_error_equal_mass(confs, corrs, n_bins=10)
        else:
            ece = expected_calibration_error(confs, corrs, n_bins=15)
        brier = brier_score(confs, corrs)

        # Win rate
        comps = total_comparisons.get(model_name, 0)
        win_rate = (win_counts.get(model_name, 0.0) / comps) if comps > 0 else 0.0

        elo = elo_ratings.get(model_name, 1000.0)

        model_summaries.append(
            ModelSummary(
                model_name=model_name,
                macro_mean=macro_mean,
                ci_lower=ci_lo,
                ci_upper=ci_hi,
                win_rate=win_rate,
                elo_rating=elo,
                ece=ece,
                brier=brier,
                total_examples=len(recs),
                per_task_means=per_task_means,
                clustered_tasks=sum(len(set(lab)) >= 2 for lab in clustered_scores.values()),
                mean_cost=_mean_or_none([r.cost_usd for r in recs]),
                mean_latency=_mean_or_none([r.latency_s for r in recs]),
                ci_method=ci_method,
            )
        )

    # Sort descending by macro_mean then elo_rating
    model_summaries.sort(key=lambda m: (-m.macro_mean, -m.elo_rating, m.model_name))
    assign_tie_groups(model_summaries, by_example, clusters=cluster_of or None)
    for name in pareto_frontier(model_summaries):
        name.pareto = True
    if bradley_terry:
        _attach_bradley_terry(model_summaries, by_example, cluster_of or None, bt_resamples)
    return LeaderboardReport(
        models=model_summaries,
        ece_label="10 equal-mass bins" if ece_binning == "equal_mass" else "15 bins",
    )


def _attach_bradley_terry(
    summaries: Sequence[ModelSummary],
    by_example: Mapping[str, Mapping[str, float]],
    clusters: Mapping[Any, Hashable] | None,
    resamples: int,
) -> None:
    """Fill the Bradley-Terry columns (needs at least two models sharing items)."""
    if len(summaries) < 2:
        return
    scores: dict[str, dict[Hashable, float]] = {m.model_name: {} for m in summaries}
    for key, per_model in by_example.items():
        for model, score in per_model.items():
            scores[model][key] = score
    try:
        bt = bradley_terry_bootstrap(scores, clusters=clusters, resamples=resamples, seed=0)
    except ValueError:  # no shared items or a disconnected comparison graph: no BT column
        return
    for m in summaries:
        i = bt.models.index(m.model_name)
        m.bt_rating = float(bt.ratings[i])
        m.bt_ci_lower = float(bt.ci_lo[i])
        m.bt_ci_upper = float(bt.ci_hi[i])


def assign_tie_groups(
    ranked: Sequence[ModelSummary],
    by_example: Mapping[str, Mapping[str, float]],
    clusters: Mapping[Any, Hashable] | None = None,
) -> None:
    """Set ``tie_group`` on ranked models: a model starts a new group only when it is
    resolved from the model ranked directly above it (Holm over the adjacent pairs).

    ``clusters`` maps an example key (``task::example_id``) to its cluster label; as in
    ``evalkit compare`` the test then flips whole clusters."""
    if len(ranked) < 2:
        for m in ranked:
            m.tie_group = 1
        return
    scores: dict[str, dict[object, float]] = {m.model_name: {} for m in ranked}
    for key, per_model in by_example.items():
        for model, score in per_model.items():
            scores[model][key] = score
    pairs = [(ranked[i].model_name, ranked[i + 1].model_name) for i in range(len(ranked) - 1)]
    group = 1
    ranked[0].tie_group = group
    resolutions = compare_pairs(scores, pairs, with_power=False, clusters=clusters)
    for nxt, res in zip(ranked[1:], resolutions, strict=True):
        if res.resolved:
            group += 1
        nxt.tie_group = group


def run(
    specs: Sequence[TaskSpec],
    models: Sequence[Model],
    out_dir: str | Path,
    max_workers: int = 4,
    samples: int = 1,
    ece_binning: EceBinning = "equal_width",
) -> EvalSummary:
    """Run evaluation benchmark across specs and models.

    Resumable: skips (task, model, example_id, sample) already stored in
    out_dir/results.jsonl. Multi-threaded: uses ThreadPoolExecutor(max_workers).
    Outputs results.jsonl and leaderboard.md.

    ``samples`` > 1 queries every item that many times (rows carry a ``sample`` index from 1;
    sample 0 is the plain single-sample call). Models that read the ``sample`` keyword
    (the mock ``noisy`` and ``random`` models) draw independently per sample; a greedy model
    repeats its answer. Statistics average the samples per item (see :mod:`evalkit.samples`).
    """
    if samples < 1:
        raise ValueError("samples must be at least 1")
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    results_file = output_path / "results.jsonl"
    leaderboard_file = output_path / "leaderboard.md"

    existing_records: list[EvalRecord] = []
    completed_keys: set[tuple[str, str, str, int]] = set()

    if results_file.is_file():
        with open(results_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    rec = EvalRecord.from_dict(data)
                    existing_records.append(rec)
                    completed_keys.add((rec.task, rec.model, rec.example_id, rec.sample))
                except Exception:
                    continue

    work_items: list[tuple[TaskSpec, Model, dict[str, Any], str, list[str] | None, int]] = []
    total_skipped = 0

    for spec in specs:
        rows = spec.load_dataset()
        # Classification: the label set is every distinct target in the dataset.
        labels = (
            sorted({t for row in rows for t in _extract_targets(row)})
            if spec.type == "classification"
            else None
        )
        for idx, row in enumerate(rows):
            ex_id = str(row.get("id", row.get("task_id", f"ex_{idx:04d}")))
            for model in models:
                for sample in range(samples):
                    key = (spec.name, model.name, ex_id, sample)
                    if key in completed_keys:
                        total_skipped += 1
                    else:
                        work_items.append((spec, model, row, ex_id, labels, sample))

    newly_evaluated = 0
    new_records: list[EvalRecord] = []
    file_lock = threading.Lock()

    if work_items:
        # Batch-capable models decode free-generation items together; everything else runs
        # one item per task.
        jobs: list[Callable[[], list[EvalRecord]]] = []
        grouped: dict[tuple[str, str], list[tuple[dict[str, Any], str]]] = {}
        batch_models: dict[tuple[str, str], tuple[TaskSpec, BatchModel]] = {}
        for spec, model, row, ex_id, labels, sample in work_items:
            if (
                sample == 0
                and isinstance(model, BatchModel)
                and model.batch_size > 1
                and spec.type in _BATCHABLE_TYPES
            ):
                group_key = (spec.name, model.name)
                batch_models[group_key] = (spec, model)
                grouped.setdefault(group_key, []).append((row, ex_id))
            else:
                jobs.append(partial(_evaluate_one, spec, model, row, ex_id, labels, sample))
        for group_key, group in grouped.items():
            spec, batch_model = batch_models[group_key]
            for start in range(0, len(group), batch_model.batch_size):
                chunk = group[start : start + batch_model.batch_size]
                jobs.append(partial(_evaluate_batch, spec, batch_model, chunk))

        workers = max(1, min(max_workers, len(jobs)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(job) for job in jobs]

            with open(results_file, "a", encoding="utf-8") as out_f:
                for future in as_completed(futures):
                    for rec in future.result():
                        new_records.append(rec)
                        newly_evaluated += 1
                        with file_lock:
                            out_f.write(json.dumps(rec.to_dict()) + "\n")
                            out_f.flush()

    all_records = existing_records + new_records
    leaderboard = generate_leaderboard(all_records, ece_binning=ece_binning)

    with open(leaderboard_file, "w", encoding="utf-8") as f:
        f.write(leaderboard.to_markdown() + "\n")

    return EvalSummary(
        records=all_records,
        leaderboard=leaderboard,
        out_dir=output_path,
        total_evaluated=newly_evaluated,
        total_skipped=total_skipped,
        results_path=results_file,
        leaderboard_path=leaderboard_file,
    )
