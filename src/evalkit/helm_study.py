"""Are a public leaderboard's rank gaps resolved by its own per-item data?

Reads the ``results.jsonl`` written by :func:`evalkit.helm.import_helm_lite` (HELM Lite, one row
per model x scenario x instance) and the published table, and reports

1. a replication check: the published per-scenario scores and mean win rates recomputed from the
   per-item data (no model is run);
2. for models adjacent in the published ranking (and at rank gaps 2, 3, 5, 10) the paired
   randomisation test pooled over all shared items with Holm correction over the family of pairs
   (``evalkit.aggregate.compare_pairs``), the tie groups this gives, and the sample size needed;
3. a stratified item bootstrap of HELM's own statistic (mean win rate over scenarios, scenario
   score = mean of the subset means) giving a rank interval per model and the probability that the
   published order of each adjacent pair holds.
"""

from __future__ import annotations

import json
import warnings
from collections import defaultdict
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .aggregate import PairResolution, compare_pairs
from .helm import HelmTable, read_table
from .helm_metrics import kendall_tau
from .ranking import BradleyTerry, bradley_terry_bootstrap

GAPS = (1, 2, 3, 5, 10)


@dataclass(frozen=True)
class ScoreMatrix:
    """Scores ``values[model, item]`` (NaN where a model has no score) in published order."""

    models: list[str]
    keys: list[tuple[str, str]]  # (task, example_id)
    values: np.ndarray
    # item -> cluster label, for items whose rows carried a cluster_id (shared passage)
    clusters: dict[tuple[str, str], tuple[str, str]] = field(default_factory=dict)

    def subset_clusters(self) -> dict[tuple[str, str], tuple[str, str]]:
        """Sensitivity clustering: items of one subset (example id up to the last '/') of a task
        that has subsets form a cluster; items of tasks without subsets stay singletons."""
        return {(task, ex): (task, ex.rpartition("/")[0]) for task, ex in self.keys if "/" in ex}

    def strata(self) -> list[tuple[str, np.ndarray]]:
        """(task, item indices) per task x subset; a subset is the example id up to the last '/'."""
        groups: dict[tuple[str, str], list[int]] = defaultdict(list)
        for i, (task, ex) in enumerate(self.keys):
            groups[(task, ex.rpartition("/")[0])].append(i)
        return [(task, np.asarray(ix)) for (task, _), ix in sorted(groups.items())]

    def task_table(self, picks: list[np.ndarray] | None = None) -> tuple[list[str], np.ndarray]:
        """Per model x task score, HELM's rule: mean over the task's subsets of the subset mean.

        Items a model was not scored on are skipped (a model with no item in a subset skips the
        subset). ``picks`` gives one array of item indices per stratum (a bootstrap draw, the same
        for every model); None uses every item.
        """
        tasks = sorted({t for t, _ in self.keys})
        filled = np.nan_to_num(self.values)
        seen = (~np.isnan(self.values)).astype(float)
        cols: dict[str, list[np.ndarray]] = defaultdict(list)
        for k, (task, ix) in enumerate(self.strata()):
            use = ix if picks is None else picks[k]
            with np.errstate(all="ignore"):
                cols[task].append(filled[:, use].sum(axis=1) / seen[:, use].sum(axis=1))
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)  # nanmean of an all-NaN row
            table = np.stack([np.nanmean(np.stack(cols[t], axis=1), axis=1) for t in tasks], axis=1)
        return tasks, table

    def as_dict(self) -> dict[str, dict[object, float]]:
        out: dict[str, dict[object, float]] = {}
        for m, name in enumerate(self.models):
            row = self.values[m]
            ok = ~np.isnan(row)
            out[name] = {self.keys[i]: float(row[i]) for i in np.flatnonzero(ok)}
        return out


def load_matrix(results_file: Path, order: Sequence[str]) -> ScoreMatrix:
    """Read results.jsonl into a matrix whose rows follow ``order`` (models absent are dropped).

    Rows with a ``cluster_id`` fill ``ScoreMatrix.clusters`` (label = (task, cluster_id))."""
    scores: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    clusters: dict[tuple[str, str], tuple[str, str]] = {}
    with open(results_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                key = (row["task"], str(row["example_id"]))
                scores[row["model"]][key] = float(row["score"])
                if row.get("cluster_id") is not None:
                    clusters[key] = (row["task"], str(row["cluster_id"]))
    models = [m for m in order if m in scores]
    keys = sorted({k for m in models for k in scores[m]})
    index = {k: i for i, k in enumerate(keys)}
    values = np.full((len(models), len(keys)), np.nan)
    for r, m in enumerate(models):
        for k, v in scores[m].items():
            values[r, index[k]] = v
    return ScoreMatrix(models, keys, values, clusters)


def win_rates(column: np.ndarray) -> np.ndarray:
    """HELM's per-column win rate (``summarize.compute_aggregate_row_win_rates``).

    For a value v: (number of other valid rows strictly below v + half the other rows tied with
    v) / (number of valid rows - 1); NaN stays NaN.
    """
    valid = ~np.isnan(column)
    n = int(valid.sum())
    out = np.full(column.shape, np.nan)
    if n < 2:
        return out
    v = column[valid]
    less = (v[:, None] > v[None, :]).sum(axis=1)
    tied = (v[:, None] == v[None, :]).sum(axis=1) - 1
    out[valid] = (less + tied / 2.0) / (n - 1)
    return out


def mean_win_rate(table: np.ndarray) -> np.ndarray:
    """Mean over columns of :func:`win_rates` for a ``models x scenarios`` table (NaN = missing)."""
    rates = np.stack([win_rates(table[:, j]) for j in range(table.shape[1])], axis=1)
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)  # a model with no scenario at all
        return np.nanmean(rates, axis=1)


@dataclass(frozen=True)
class Replication:
    max_abs_diff: dict[str, float]  # task -> max |recomputed - published| over models
    cells: int
    mwr_max_abs_diff: float
    order_identical: bool


def replicate(m: ScoreMatrix, table: HelmTable) -> Replication:
    """Recompute the published per-scenario scores and mean win rates from the per-item data."""
    tasks, scores = m.task_table()
    diffs: dict[str, float] = {}
    cells = 0
    published = np.full_like(scores, np.nan)
    for r, model in enumerate(m.models):
        for c, task in enumerate(tasks):
            if task in table.published[model]:
                published[r, c] = table.published[model][task]
    for c, task in enumerate(tasks):
        ok = ~np.isnan(published[:, c])
        cells += int(ok.sum())
        diffs[task] = float(np.abs(scores[ok, c] - published[ok, c]).max())
    mwr = mean_win_rate(published)
    ref = np.asarray([table.mean_win_rate[x] for x in m.models])
    recomputed = mean_win_rate(np.where(np.isnan(published), np.nan, scores))
    return Replication(
        diffs,
        cells,
        float(np.abs(mwr - ref).max()),
        bool(np.array_equal(np.argsort(-recomputed, kind="stable"), np.arange(len(m.models)))),
    )


@dataclass(frozen=True)
class GapResult:
    gap: int
    rows: list[PairResolution]

    @property
    def resolved(self) -> int:
        return sum(r.resolved for r in self.rows)

    @property
    def reversed(self) -> int:
        """Resolved pairs whose pooled mean difference favours the lower-ranked model."""
        return sum(r.resolved and r.diff < 0 for r in self.rows)


def pair_family(
    m: ScoreMatrix,
    gap: int,
    seed: int,
    num_draws: int = 10000,
    clusters: Mapping[Any, Hashable] | None = None,
    num_resamples: int = 10000,
) -> GapResult:
    scores = m.as_dict()
    pairs = [(m.models[i], m.models[i + gap]) for i in range(len(m.models) - gap)]
    rows = compare_pairs(
        scores,
        pairs,
        seed=seed,
        num_draws=num_draws,
        num_resamples=num_resamples,
        clusters=clusters,
    )
    return GapResult(gap, rows)


def tie_groups(rows: Sequence[PairResolution]) -> int:
    """Number of tie groups when ranks follow the published order (new group iff resolved)."""
    return 1 + sum(r.resolved for r in rows)


@dataclass(frozen=True)
class RankBootstrap:
    resamples: int
    rank_lo: np.ndarray  # 2.5th percentile of each model's rank
    rank_hi: np.ndarray  # 97.5th percentile
    p_adjacent: np.ndarray  # P(mean win rate of model i beats model i+1)


def rank_bootstrap(m: ScoreMatrix, resamples: int, seed: int) -> RankBootstrap:
    """Stratified item bootstrap of the mean win rate ranking (same draw for every model)."""
    rng = np.random.default_rng(seed)
    strata = m.strata()
    n_models = len(m.models)
    ranks = np.empty((resamples, n_models))
    beats = np.zeros(n_models - 1)
    for b in range(resamples):
        picks = [ix[rng.integers(0, len(ix), len(ix))] for _, ix in strata]
        _, table = m.task_table(picks)
        mwr = mean_win_rate(table)
        order = np.argsort(-mwr, kind="stable")
        ranks[b, order] = np.arange(1, n_models + 1)
        beats += (mwr[:-1] > mwr[1:]) + 0.5 * (mwr[:-1] == mwr[1:])
    return RankBootstrap(
        resamples,
        np.percentile(ranks, 2.5, axis=0),
        np.percentile(ranks, 97.5, axis=0),
        beats / resamples,
    )


def _fmt_p(p: float) -> str:
    return f"{p:.3g}"


def render_report(
    m: ScoreMatrix,
    table: HelmTable,
    rep: Replication,
    gaps: Sequence[GapResult],
    boot: RankBootstrap,
    seed: int,
) -> str:
    n_items = len(m.keys)
    tasks = sorted({t for t, _ in m.keys})
    lines = [
        "# HELM Lite: are the published rank gaps resolved by the per-item data?",
        "",
        f"{len(m.models)} models, {n_items} instances over {len(tasks)} scenarios "
        f"({', '.join(tasks)}); seed {seed}. Generated by `evalkit helm-study`.",
        "",
        "## 1. Replication of the published numbers from per-item results",
        "",
        "Per-scenario scores recomputed from the instances (mean over the scenario's subsets of "
        f"the subset mean) against the published table, {rep.cells} model x scenario cells: "
        "max |difference| per scenario below. Mean win rate recomputed from the *published* "
        "scenario scores with HELM's rule: max |difference| to the published value "
        f"{rep.mwr_max_abs_diff:.2e}. Order by the mean win rate recomputed from the instances "
        f"is identical to the published order: {'yes' if rep.order_identical else 'no'}.",
        "",
        "| scenario | max abs diff |",
        "|---|---|",
        *[f"| {t} | {d:.2e} |" for t, d in sorted(rep.max_abs_diff.items())],
        "",
        "## 2. Paired randomisation test between models at a given published rank distance",
        "",
        "Each pair is tested on all instances both models were scored on (pooled over scenarios, "
        "so a scenario weighs by its instance count, not as in HELM's mean win rate). p is the "
        "paired sign-flip randomisation test; Holm correction runs within each row's family of "
        "pairs. Tie groups: walking down the published ranking a model starts a new group only if "
        "it is resolved from the model directly above (rank distance 1).",
        "",
        "| rank distance | pairs | resolved (Holm p < 0.05) | share resolved | "
        "of which the lower-ranked model has the higher pooled mean | median n for 80% power |",
        "|---|---|---|---|---|---|",
    ]
    for g in gaps:
        needed = [r.n_needed for r in g.rows if r.n_needed is not None and not r.resolved]
        med = f"{int(np.median(needed))}" if needed else "n/a"
        lines.append(
            f"| {g.gap} | {len(g.rows)} | {g.resolved} | {g.resolved / len(g.rows):.0%} | "
            f"{g.reversed} | {med} |"
        )
    adj = next(g for g in gaps if g.gap == 1)
    lines += [
        "",
        f"Adjacent pairs: {adj.resolved} of {len(adj.rows)} resolved, i.e. "
        f"{len(adj.rows) - adj.resolved} unresolved; the published list shows {len(m.models)} "
        f"distinct ranks, the data supports {tie_groups(adj.rows)} tie groups.",
        "",
        "## 3. Rank uncertainty of HELM's own statistic (stratified item bootstrap)",
        "",
        f"{boot.resamples} resamples of the instances within each scenario subset (same draw for "
        "every model), mean win rate recomputed each time with HELM's rule.",
        "",
    ]
    width = boot.rank_hi - boot.rank_lo
    for thr in (0.975, 0.95, 0.9):
        lines.append(
            f"- adjacent pairs whose published order holds in at least {thr:.1%} of resamples: "
            f"{int((boot.p_adjacent >= thr).sum())} of {len(boot.p_adjacent)}"
        )
    lines += [
        f"- median 95% rank interval width: {float(np.median(width)):.0f} ranks "
        f"(min {float(width.min()):.0f}, max {float(width.max()):.0f})",
        f"- models whose 95% rank interval is a single rank: {int((width == 0).sum())} of "
        f"{len(m.models)}",
        "",
        "## 4. Adjacent pairs in published order",
        "",
        "| rank | A vs B | published mean win rate A / B | A - B (pooled) | 95% CI | W / L / T | "
        "randomisation p | Holm p | n for 80% power | P(order holds) bootstrap | verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(adj.rows):
        n_text = "n/a" if r.n_needed is None else str(r.n_needed)
        verdict = "resolved" if r.resolved else "unresolved"
        lines.append(
            f"| {i + 1}-{i + 2} | {r.model_a} vs {r.model_b} | "
            f"{table.mean_win_rate[r.model_a]:.3f} / {table.mean_win_rate[r.model_b]:.3f} | "
            f"{r.diff:+.4f} | [{r.diff_ci_lo:+.4f}, {r.diff_ci_hi:+.4f}] | "
            f"{r.wins} / {r.losses} / {r.ties} | {_fmt_p(r.rand_p)} | {_fmt_p(r.holm_p)} | "
            f"{n_text} | {boot.p_adjacent[i]:.2f} | {verdict} |"
        )
    lines.append("")
    return "\n".join(lines)


CLUSTER_MODES = ("passage", "subset")


def cluster_labels(m: ScoreMatrix, mode: str) -> dict[tuple[str, str], tuple[str, str]]:
    """Item -> cluster label for a clustering mode: ``passage`` (shared source passage, from the
    results file) or ``subset`` (sensitivity: items of one subset of a task)."""
    if mode == "passage":
        return dict(m.clusters)
    if mode == "subset":
        return m.subset_clusters()
    raise ValueError(f"unknown cluster mode {mode!r} (use one of {CLUSTER_MODES})")


def _cluster_shape(labels: Mapping[Any, Hashable]) -> tuple[int, int, int]:
    """(clusters with at least two items, items in them, largest cluster)."""
    sizes: dict[Hashable, int] = defaultdict(int)
    for lab in labels.values():
        sizes[lab] += 1
    multi = [s for s in sizes.values() if s >= 2]
    return len(multi), sum(multi), max(multi, default=1)


def render_clustered(
    m: ScoreMatrix,
    item_level: Sequence[GapResult],
    clustered: Mapping[str, Sequence[GapResult]],
) -> list[str]:
    """Section 5: the pair families again with clusters, against the item-level verdicts."""
    lines = [
        "## 5. The same pairs with clustered statistics",
        "",
        "Where items share a source their scores are correlated, and the item-level test "
        "overstates the evidence. With a cluster map `compare_pairs` replaces the sign-flip test "
        "by the cluster sign-flip test (whole clusters change sign together), the bootstrap CI by "
        "the cluster bootstrap, and plans power with the design effect `1 + (m - 1) ICC` of the "
        "paired differences. Holm runs over the same families as section 2.",
        "",
    ]
    for mode, results in clustered.items():
        labels = cluster_labels(m, mode)
        n_multi, n_in, biggest = _cluster_shape(labels)
        what = (
            "items that share a source passage (`cluster_id` of the imported rows)"
            if mode == "passage"
            else "sensitivity analysis: every subset (MMLU subject, LegalBench task, MATH subject, "
            "WMT language pair) is one cluster; tasks without subsets keep single-item clusters"
        )
        lines += [
            f"### Clusters: {mode}",
            "",
            f"{what}. {n_multi} clusters hold two or more items ({n_in} of {len(m.keys)} items; "
            f"largest cluster {biggest} items).",
            "",
            "| rank distance | pairs | resolved, item-level | resolved, clustered | "
            "pairs whose verdict differs | median design effect | median clustered / naive SE |",
            "|---|---|---|---|---|---|---|",
        ]
        for base, g in zip(item_level, results, strict=True):
            differs = sum(a.resolved != b.resolved for a, b in zip(base.rows, g.rows, strict=True))
            stats = [r.clustering for r in g.rows if r.clustering is not None]
            deff = f"{float(np.median([s.deff for s in stats])):.2f}" if stats else "n/a"
            ratio = f"{float(np.nanmedian([s.se_ratio for s in stats])):.2f}" if stats else "n/a"
            lines.append(
                f"| {g.gap} | {len(g.rows)} | {base.resolved} | {g.resolved} | {differs} | "
                f"{deff} | {ratio} |"
            )
        adj0, adj1 = item_level[0], results[0]
        flips = [
            f"{a.model_a} vs {a.model_b} ({'resolved' if a.resolved else 'unresolved'} -> "
            f"{'resolved' if b.resolved else 'unresolved'}, Holm p {_fmt_p(a.holm_p)} -> "
            f"{_fmt_p(b.holm_p)})"
            for a, b in zip(adj0.rows, adj1.rows, strict=True)
            if a.resolved != b.resolved
        ]
        lines += ["", f"Adjacent pairs whose verdict changes ({len(flips)}):", ""]
        lines += [f"- {f}" for f in flips[:10]] or ["- none"]
        if len(flips) > 10:
            lines.append(f"- ... and {len(flips) - 10} more")
        lines += [
            "",
            f"Tie groups on the adjacent pairs: item-level {tie_groups(adj0.rows)}, clustered "
            f"{tie_groups(adj1.rows)}.",
            "",
        ]
    return lines


def render_bradley_terry_section(
    m: ScoreMatrix, bt: BradleyTerry, bt_clustered: BradleyTerry | None, boot: RankBootstrap
) -> list[str]:
    """Section 6: Bradley-Terry ratings of the pooled item outcomes against the published order."""
    order = np.argsort(-bt.ratings, kind="stable")
    bt_rank = np.empty(len(order), dtype=int)
    bt_rank[order] = np.arange(1, len(order) + 1)
    tau = kendall_tau([-float(i) for i in range(len(m.models))], [float(x) for x in bt.ratings])
    n_pairs = len(m.models) - 1
    p_item = np.asarray([bt.prob_above(m.models[i], m.models[i + 1]) for i in range(n_pairs)])
    p_cl = (
        np.asarray([bt_clustered.prob_above(m.models[i], m.models[i + 1]) for i in range(n_pairs)])
        if bt_clustered is not None
        else None
    )
    fitted = f"{bt.resamples - bt.failed} of {bt.resamples} item-bootstrap resamples"
    if bt_clustered is not None:
        fitted += (
            f"; passage clusters resampled whole: {bt_clustered.resamples - bt_clustered.failed} "
            f"of {bt_clustered.resamples}"
        )
    lines = [
        "## 6. Bradley-Terry ranking of the same data",
        "",
        "Maximum-likelihood Bradley-Terry strengths from the pooled per-item outcomes (each item "
        "both models were scored on is a game, the higher score wins, equal scores split it; "
        f"{len(m.keys)} items), on the Elo scale. Intervals: {fitted}. This ranks by pooled item "
        "wins, not by HELM's scenario-balanced mean win rate, so the two orders can differ.",
        "",
        f"Kendall tau between the published order and the Bradley-Terry order: {tau:.3f}.",
        "",
        "Adjacent pairs of the published order in which the higher-ranked model is rated above "
        "the lower-ranked one in at least the given share of the resamples (section 3 has the "
        "same count for HELM's own statistic):",
        "",
    ]
    head = ["share of resamples", "Bradley-Terry (items)"]
    if p_cl is not None:
        head.append("Bradley-Terry (passage clusters)")
    head.append("mean win rate bootstrap (section 3)")
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for thr in (0.975, 0.95, 0.9):
        cells = [f"{int((p_item >= thr).sum())} of {n_pairs}"]
        if p_cl is not None:
            cells.append(f"{int((p_cl >= thr).sum())} of {n_pairs}")
        cells.append(f"{int((boot.p_adjacent >= thr).sum())} of {len(boot.p_adjacent)}")
        lines.append(f"| {thr:.1%} | " + " | ".join(cells) + " |")
    width = bt.rank_hi - bt.rank_lo
    lines += [
        "",
        f"Median 95% rank interval width under Bradley-Terry: {float(np.median(width)):.0f} "
        f"ranks (min {float(width.min()):.0f}, max {float(width.max()):.0f}); models whose "
        f"interval is one rank: {int((width == 0).sum())} of {len(m.models)}.",
        "",
        "| published rank | model | Bradley-Terry [95% CI] | Bradley-Terry rank (95% interval) |",
        "|---|---|---|---|",
    ]
    for i in range(min(15, len(m.models))):
        lines.append(
            f"| {i + 1} | {m.models[i]} | {bt.ratings[i]:.1f} "
            f"[{bt.ci_lo[i]:.1f}, {bt.ci_hi[i]:.1f}] | {bt_rank[i]} "
            f"({bt.rank_lo[i]:.0f}-{bt.rank_hi[i]:.0f}) |"
        )
    lines.append("")
    return lines


def run_study(
    results_file: Path,
    root: Path,
    seed: int = 0,
    resamples: int = 1000,
    gaps: Sequence[int] = GAPS,
    num_draws: int = 10000,
    cluster_modes: Sequence[str] = CLUSTER_MODES,
    cluster_resamples: int = 2000,
    bt_resamples: int = 200,
) -> str:
    """The full report. ``cluster_modes`` (see :data:`CLUSTER_MODES`) repeat the pair families
    with clustered statistics; a mode with no multi-item cluster is skipped. ``bt_resamples`` 0
    omits the Bradley-Terry section."""
    table = read_table(root)
    m = load_matrix(results_file, table.models)
    if len(m.models) < 3:
        raise ValueError("need at least 3 models")
    rep = replicate(m, table)
    results = [pair_family(m, g, seed, num_draws) for g in gaps if g < len(m.models) and g >= 1]
    if not results or results[0].gap != 1:
        raise ValueError("gaps must start with 1")
    boot = rank_bootstrap(m, resamples, seed)
    text = render_report(m, table, rep, results, boot, seed)
    lines: list[str] = []
    clustered: dict[str, list[GapResult]] = {}
    for mode in cluster_modes:
        labels = cluster_labels(m, mode)
        if _cluster_shape(labels)[0] == 0:
            continue
        clustered[mode] = [
            pair_family(m, g.gap, seed, num_draws, clusters=labels, num_resamples=cluster_resamples)
            for g in results
        ]
    if clustered:
        lines += render_clustered(m, results, clustered)
    if bt_resamples > 0:
        scores = m.as_dict()
        bt = bradley_terry_bootstrap(scores, resamples=bt_resamples, seed=seed)
        passage = cluster_labels(m, "passage")
        bt_cl = (
            bradley_terry_bootstrap(scores, clusters=passage, resamples=bt_resamples, seed=seed)
            if _cluster_shape(passage)[0] > 0
            else None
        )
        lines += render_bradley_terry_section(m, bt, bt_cl, boot)
    return text + ("\n".join(lines) + "\n" if lines else "")


__all__ = [
    "GAPS",
    "RankBootstrap",
    "Replication",
    "ScoreMatrix",
    "load_matrix",
    "mean_win_rate",
    "rank_bootstrap",
    "replicate",
    "run_study",
    "tie_groups",
    "win_rates",
]
