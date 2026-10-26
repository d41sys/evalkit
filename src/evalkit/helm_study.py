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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .aggregate import PairResolution, compare_pairs
from .helm import HelmTable, read_table

GAPS = (1, 2, 3, 5, 10)


@dataclass(frozen=True)
class ScoreMatrix:
    """Scores ``values[model, item]`` (NaN where a model has no score) in published order."""

    models: list[str]
    keys: list[tuple[str, str]]  # (task, example_id)
    values: np.ndarray

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
    """Read results.jsonl into a matrix whose rows follow ``order`` (models absent are dropped)."""
    scores: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    with open(results_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                scores[row["model"]][(row["task"], str(row["example_id"]))] = float(row["score"])
    models = [m for m in order if m in scores]
    keys = sorted({k for m in models for k in scores[m]})
    index = {k: i for i, k in enumerate(keys)}
    values = np.full((len(models), len(keys)), np.nan)
    for r, m in enumerate(models):
        for k, v in scores[m].items():
            values[r, index[k]] = v
    return ScoreMatrix(models, keys, values)


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


def pair_family(m: ScoreMatrix, gap: int, seed: int, num_draws: int = 10000) -> GapResult:
    scores = m.as_dict()
    pairs = [(m.models[i], m.models[i + gap]) for i in range(len(m.models) - gap)]
    rows = compare_pairs(scores, pairs, seed=seed, num_draws=num_draws)
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


def run_study(
    results_file: Path,
    root: Path,
    seed: int = 0,
    resamples: int = 1000,
    gaps: Sequence[int] = GAPS,
    num_draws: int = 10000,
) -> str:
    table = read_table(root)
    m = load_matrix(results_file, table.models)
    if len(m.models) < 3:
        raise ValueError("need at least 3 models")
    rep = replicate(m, table)
    results = [pair_family(m, g, seed, num_draws) for g in gaps if g < len(m.models) and g >= 1]
    if not results or results[0].gap != 1:
        raise ValueError("gaps must start with 1")
    boot = rank_bootstrap(m, resamples, seed)
    return render_report(m, table, rep, results, boot, seed)


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
