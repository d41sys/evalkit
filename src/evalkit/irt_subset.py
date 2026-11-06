"""IRT anchor subsets on HELM Lite: can ~100 instances reproduce the model ranking?

The protocol (selections, estimators, splits, metrics, decision rule) is
``docs/protocol-irt-subset.md``, committed before the first scoring run. numpy only; the
IRT fitter is :mod:`evalkit.irt`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .helm_study import ScoreMatrix, load_matrix
from .irt import (
    IrtFit,
    cluster_anchors,
    estimate_theta,
    fit_irt,
    info_anchors,
    kendall_tau_b,
    sigmoid,
)

N_ANCHORS = 100
N_TEST = 21
N_SPLITS = 50
N_FOLDS = 4
N_REFERENCE_DRAWS = 1000
N_BOOT = 2000
BLEND = 0.5
SWEEPS = 60
SELECTIONS = ("random", "stratified", "anchor-correct", "anchor-irt", "info")
BASELINE = ("stratified", "anchor-mean", "-")
HEADLINE = ("anchor-correct", "blend", "2pl")
SEED = 0


@dataclass(frozen=True)
class Anchors:
    """Anchor items with their estimator weights.

    The anchor-mean estimate of a model is ``sum_g mass_g * (weighted mean of the model's
    scores on the anchors of group g)``, over the anchors the model has (weights and group
    masses renormalised over what is available).
    """

    idx: np.ndarray  # (k,) item indices
    omega: np.ndarray  # (k,) weights inside the group
    group: np.ndarray  # (k,) group id (0 for one group)
    mass: np.ndarray  # (groups,) group masses (sum 1)


@dataclass(frozen=True)
class Problem:
    """Scores, observation mask, scenario codes and the macro item weights."""

    values: np.ndarray  # (models, items), NaN where missing
    mask: np.ndarray
    scenario: np.ndarray  # (items,) codes 0..S-1
    n_scenarios: int
    item_weight: np.ndarray  # (items,) 1 / (S n_s)

    @classmethod
    def from_matrix(cls, m: ScoreMatrix) -> Problem:
        tasks = sorted({t for t, _ in m.keys})
        code = {t: i for i, t in enumerate(tasks)}
        scen = np.asarray([code[t] for t, _ in m.keys], dtype=np.int64)
        counts = np.bincount(scen, minlength=len(tasks))
        return cls(
            values=m.values,
            mask=~np.isnan(m.values),
            scenario=scen,
            n_scenarios=len(tasks),
            item_weight=1.0 / (len(tasks) * counts[scen]),
        )

    def macro(self, scores: np.ndarray, models: np.ndarray) -> np.ndarray:
        """Macro score per model: mean over scenarios of the scenario mean over observed items.

        ``scores`` has shape (len(models), items) (observed or predicted); the observation
        mask of the corresponding rows of ``values`` decides which items count.
        """
        obs = self.mask[models]
        total = np.zeros(len(models))
        seen = np.zeros(len(models))
        for s in range(self.n_scenarios):
            cols = np.flatnonzero(self.scenario == s)
            n = obs[:, cols].sum(axis=1)
            ok = n > 0
            mean = np.where(ok, (scores[:, cols] * obs[:, cols]).sum(axis=1) / np.maximum(n, 1), 0)
            total += mean
            seen += ok
        return total / np.maximum(seen, 1)

    def truth(self, models: np.ndarray) -> np.ndarray:
        return self.macro(np.nan_to_num(self.values[models]), models)


def anchor_mean(problem: Problem, models: np.ndarray, anchors: Anchors) -> np.ndarray:
    """Anchor-mean estimate of the macro score for ``models`` (see :class:`Anchors`)."""
    y = np.nan_to_num(problem.values[np.ix_(models, anchors.idx)])
    avail = problem.mask[np.ix_(models, anchors.idx)]
    total = np.zeros(len(models))
    mass_seen = np.zeros(len(models))
    for g in range(anchors.mass.size):
        cols = np.flatnonzero(anchors.group == g)
        if cols.size == 0:
            continue
        w = anchors.omega[cols][None, :] * avail[:, cols]
        den = w.sum(axis=1)
        ok = den > 0
        est = np.where(ok, (w * y[:, cols]).sum(axis=1) / np.where(ok, den, 1.0), 0.0)
        total += anchors.mass[g] * est
        mass_seen += anchors.mass[g] * ok
    return total / np.maximum(mass_seen, 1e-12)


def random_anchors(problem: Problem, rng: np.random.Generator, k: int = N_ANCHORS) -> Anchors:
    idx = np.sort(rng.choice(problem.scenario.size, size=k, replace=False))
    return Anchors(idx, problem.item_weight[idx], np.zeros(k, dtype=np.int64), np.ones(1))


def stratified_anchors(problem: Problem, rng: np.random.Generator, k: int = N_ANCHORS) -> Anchors:
    per = k // problem.n_scenarios
    parts = []
    for s in range(problem.n_scenarios):
        cols = np.flatnonzero(problem.scenario == s)
        parts.append(np.sort(rng.choice(cols, size=min(per, cols.size), replace=False)))
    idx = np.concatenate(parts)
    group = problem.scenario[idx]
    return Anchors(
        idx, np.ones(idx.size), group, np.full(problem.n_scenarios, 1.0 / problem.n_scenarios)
    )


def _impute_train(problem: Problem, train: np.ndarray) -> np.ndarray:
    """(items, train models) score vectors; a missing score is the item's training mean."""
    v = problem.values[train]
    obs = problem.mask[train]
    n = obs.sum(axis=0)
    mean = np.where(n > 0, np.nansum(v, axis=0) / np.maximum(n, 1), 0.0)
    return np.where(obs, np.nan_to_num(v), mean[None, :]).T


def cluster_selection(
    features: np.ndarray, problem: Problem, rng: np.random.Generator, k: int = N_ANCHORS
) -> Anchors:
    idx, w = cluster_anchors(features, problem.item_weight, k, rng)
    return Anchors(idx, w, np.zeros(idx.size, dtype=np.int64), np.ones(1))


def irt_embedding(fit: IrtFit) -> np.ndarray:
    """Standardised (slope, difficulty) of every item: tinyBenchmarks' IRT embedding, 1-D."""
    b = np.clip(fit.c / fit.a, -10.0, 10.0)
    emb = np.stack([fit.a, b], axis=1)
    sd = np.where(emb.std(axis=0) > 0, emb.std(axis=0), 1.0)
    return (emb - emb.mean(axis=0)) / sd


def info_selection(fit: IrtFit, k: int = N_ANCHORS) -> Anchors:
    idx = info_anchors(fit, k)
    return Anchors(idx, np.ones(idx.size), np.zeros(idx.size, dtype=np.int64), np.ones(1))


def p_irt(
    problem: Problem, models: np.ndarray, fit: IrtFit, anchors: Anchors
) -> tuple[np.ndarray, np.ndarray]:
    """(p-IRT macro-score estimate, ability estimate) of ``models`` from their anchor scores."""
    idx = anchors.idx
    theta = estimate_theta(
        fit.a[idx],
        fit.c[idx],
        np.nan_to_num(problem.values[np.ix_(models, idx)]),
        problem.mask[np.ix_(models, idx)],
    )
    pred = sigmoid(fit.a[None, :] * theta[:, None] - fit.c[None, :])
    return problem.macro(pred, models), theta


Key = tuple[str, str, str]  # (selection, estimator, IRT model)


def estimate_all(
    problem: Problem,
    train: np.ndarray,
    test: np.ndarray,
    split_rng: np.random.SeedSequence,
    fits: dict[str, IrtFit] | None = None,
    sweeps: int = SWEEPS,
    tol: float | None = None,
) -> dict[Key, np.ndarray]:
    """Every (selection, estimator, IRT model) estimate of the macro score of ``test``."""
    rng_pick = np.random.default_rng(split_rng.spawn(1)[0])
    if fits is None:
        fits = {
            name: fit_irt(problem.values[train], problem.mask[train], name, sweeps, tol)
            for name in ("1pl", "2pl")
        }
    kmeans_seed = np.random.SeedSequence(split_rng.entropy, spawn_key=(*split_rng.spawn_key, 7))
    rng_cluster = np.random.default_rng(kmeans_seed)
    sets: dict[str, Anchors] = {
        "random": random_anchors(problem, rng_pick),
        "stratified": stratified_anchors(problem, rng_pick),
        "anchor-correct": cluster_selection(_impute_train(problem, train), problem, rng_cluster),
        "anchor-irt": cluster_selection(irt_embedding(fits["2pl"]), problem, rng_cluster),
        "info": info_selection(fits["2pl"]),
    }
    out: dict[Key, np.ndarray] = {}
    for sel, anchors in sets.items():
        mean_est = anchor_mean(problem, test, anchors)
        out[(sel, "anchor-mean", "-")] = mean_est
        for name, fit in fits.items():
            est, _ = p_irt(problem, test, fit, anchors)
            out[(sel, "p-irt", name)] = est
            out[(sel, "blend", name)] = BLEND * mean_est + (1.0 - BLEND) * est
    return out


@dataclass(frozen=True)
class SplitMetrics:
    tau: float
    mae: float
    rmse: float


def metrics(est: np.ndarray, truth: np.ndarray) -> SplitMetrics:
    err = est - truth
    return SplitMetrics(
        kendall_tau_b(est, truth), float(np.mean(np.abs(err))), float(np.sqrt(np.mean(err**2)))
    )


@dataclass
class IrtStudy:
    n_models: int
    n_items: int
    scenarios: list[str]
    splits: dict[Key, list[SplitMetrics]] = field(default_factory=dict)
    fold: dict[Key, SplitMetrics] = field(default_factory=dict)
    reference: dict[str, list[SplitMetrics]] = field(default_factory=dict)
    fit_change: dict[str, list[float]] = field(default_factory=dict)
    fit_converged: dict[str, list[bool]] = field(default_factory=dict)
    sweeps: int = 60
    tol: float | None = None
    theta_corr: dict[str, list[float]] = field(default_factory=dict)
    test_size: int = N_TEST
    n_splits: int = N_SPLITS


def reference_draws(problem: Problem, draws: int, seed: int) -> dict[str, list[SplitMetrics]]:
    """Random and stratified subsets against the true scores of all models (no model split)."""
    models = np.arange(problem.values.shape[0])
    truth = problem.truth(models)
    out: dict[str, list[SplitMetrics]] = {"random": [], "stratified": []}
    for r in range(draws):
        rng = np.random.default_rng(np.random.SeedSequence([seed, 10_000, r]))
        out["random"].append(
            metrics(anchor_mean(problem, models, random_anchors(problem, rng)), truth)
        )
        out["stratified"].append(
            metrics(anchor_mean(problem, models, stratified_anchors(problem, rng)), truth)
        )
    return out


def run_study(
    results_file: Path,
    n_splits: int = N_SPLITS,
    test_size: int = N_TEST,
    n_folds: int = N_FOLDS,
    draws: int = N_REFERENCE_DRAWS,
    seed: int = SEED,
    sweeps: int = SWEEPS,
    tol: float | None = None,
) -> IrtStudy:
    names = _model_order(results_file)
    problem = Problem.from_matrix(load_matrix(results_file, names))
    n_models, n_items = problem.values.shape
    tasks = sorted({t for t in _task_names(results_file)})
    study = IrtStudy(
        n_models, n_items, tasks, test_size=test_size, n_splits=n_splits, sweeps=sweeps, tol=tol
    )
    everyone = np.arange(n_models)
    truth_all = problem.truth(everyone)
    for r in range(n_splits):
        ss = np.random.SeedSequence([seed, r])
        perm = np.random.default_rng(ss).permutation(n_models)
        test, train = np.sort(perm[:test_size]), np.sort(perm[test_size:])
        fits = {
            name: fit_irt(problem.values[train], problem.mask[train], name, sweeps, tol)
            for name in ("1pl", "2pl")
        }
        for key, est in estimate_all(problem, train, test, ss, fits=fits).items():
            study.splits.setdefault(key, []).append(metrics(est, problem.truth(test)))
        macro_train = problem.truth(train)
        for name, fit in fits.items():
            study.fit_change.setdefault(name, []).append(abs(fit.last_change))
            study.fit_converged.setdefault(name, []).append(fit.converged)
            study.theta_corr.setdefault(name, []).append(
                float(np.corrcoef(fit.theta, macro_train)[0, 1])
            )
    perm = np.random.default_rng(np.random.SeedSequence([seed, 9999])).permutation(n_models)
    oof: dict[Key, np.ndarray] = {}
    for f, held in enumerate(np.array_split(perm, n_folds)):
        test = np.sort(held)
        train = np.sort(np.setdiff1d(everyone, held))
        ss = np.random.SeedSequence([seed, 9998, f])
        for key, est in estimate_all(problem, train, test, ss, sweeps=sweeps, tol=tol).items():
            oof.setdefault(key, np.zeros(n_models))[test] = est
    study.fold = {key: metrics(est, truth_all) for key, est in oof.items()}
    study.reference = reference_draws(problem, draws, seed)
    return study


def _model_order(results_file: Path) -> list[str]:
    seen: dict[str, None] = {}
    with open(results_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                seen.setdefault(json.loads(line)["model"], None)
    return list(seen)


def _task_names(results_file: Path) -> set[str]:
    out: set[str] = set()
    with open(results_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.add(json.loads(line)["task"])
    return out


# ---------------------------------------------------------------------------------- report


def _interval(values: Sequence[float]) -> tuple[float, float, float]:
    a = np.asarray(values, dtype=np.float64)
    return float(np.nanmean(a)), float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5))


def paired_ci(
    diff: Sequence[float], boot: int = N_BOOT, seed: int = SEED
) -> tuple[float, float, float]:
    """Mean of per-split paired differences with a percentile bootstrap CI over splits."""
    d = np.asarray(diff, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, d.size, size=(boot, d.size))].mean(axis=1)
    return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def verdict(tau_ci: tuple[float, float, float], mae_ci: tuple[float, float, float]) -> str:
    """Decision rule: beats / loses / no detectable difference / mixed (both statistics)."""
    tau_up, tau_down = tau_ci[1] > 0, tau_ci[2] < 0
    mae_up, mae_down = mae_ci[1] > 0, mae_ci[2] < 0
    if tau_up and mae_up:
        return "beats"
    if tau_down and mae_down:
        return "loses"
    if (tau_up or mae_up) and (tau_down or mae_down):
        return "mixed"
    if tau_up or mae_up or tau_down or mae_down:
        return "one statistic only"
    return "no detectable difference"


def paired_vs_baseline(study: IrtStudy, key: Key) -> tuple[tuple[float, float, float], ...]:
    base = study.splits[BASELINE]
    cur = study.splits[key]
    d_tau = [c.tau - b.tau for c, b in zip(cur, base, strict=True)]
    d_mae = [b.mae - c.mae for c, b in zip(cur, base, strict=True)]
    return paired_ci(d_tau), paired_ci(d_mae)


def _ordered(keys: Sequence[Key]) -> list[Key]:
    est_rank = {"anchor-mean": 0, "p-irt": 1, "blend": 2}
    return sorted(keys, key=lambda k: (SELECTIONS.index(k[0]), est_rank[k[1]], k[2]))


def render_markdown(study: IrtStudy) -> str:
    lines: list[str] = []
    lines.append("# IRT anchor subsets on HELM Lite (tinyBenchmarks-style)\n")
    lines.append(
        f"{study.n_models} models x {study.n_items} instances over {len(study.scenarios)} "
        f"scenarios ({', '.join(study.scenarios)}); {N_ANCHORS} anchors; target = macro average "
        "of the per-scenario mean scores. Generated by `evalkit irt-subset`; the protocol "
        "(`docs/protocol-irt-subset.md`) was committed before the first run.\n"
    )
    rule = f"{study.sweeps} sweeps" + (f", stopping below {study.tol:g}" if study.tol else "")
    lines.append(f"## Fit diagnostics ({rule})\n")
    lines.append(
        "| IRT model | median abs change in the penalised log-lik. over the last sweep | "
        "max | fits converged (change < 1e-4) | mean corr(theta, macro score) of the "
        "training models |"
    )
    lines.append("|---|---|---|---|---|")
    for name in ("1pl", "2pl"):
        ch = study.fit_change[name]
        conv = study.fit_converged[name]
        lines.append(
            f"| {name} | {float(np.median(ch)):.3g} | {max(ch):.3g} "
            f"| {sum(conv)}/{len(conv)} "
            f"| {float(np.mean(study.theta_corr[name])):.3f} |"
        )
    lines.append(
        f"\n## 1. Model-level cross-validation: {study.n_splits} random splits, fit on "
        f"{study.n_models - study.test_size} models, test on {study.test_size}\n"
    )
    lines.append(
        "Mean over splits (2.5th to 97.5th percentile over splits). tau = Kendall tau-b "
        "between estimated and true macro score on the test models; MAE / RMSE in score "
        "points (0-1 scale). Paired columns: mean per-split difference to `stratified` + "
        "`anchor-mean` with a 95% bootstrap CI over splits (tau: row minus baseline; MAE: "
        "baseline minus row, so positive is better).\n"
    )
    lines.append(
        "| selection | estimator | IRT | tau | MAE | RMSE | paired d tau | paired d MAE | verdict |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for key in _ordered(list(study.splits)):
        ms = study.splits[key]
        tau = _interval([m.tau for m in ms])
        mae = _interval([m.mae for m in ms])
        rmse = _interval([m.rmse for m in ms])
        if key == BASELINE:
            pair = ("baseline", "baseline", "-")
        else:
            t_ci, m_ci = paired_vs_baseline(study, key)
            pair = (
                f"{t_ci[0]:+.3f} [{t_ci[1]:+.3f}, {t_ci[2]:+.3f}]",
                f"{m_ci[0]:+.4f} [{m_ci[1]:+.4f}, {m_ci[2]:+.4f}]",
                verdict(t_ci, m_ci),
            )
        lines.append(
            f"| {key[0]} | {key[1]} | {key[2]} "
            f"| {tau[0]:.3f} ({tau[1]:.2f} to {tau[2]:.2f}) "
            f"| {mae[0]:.4f} ({mae[1]:.4f} to {mae[2]:.4f}) "
            f"| {rmse[0]:.4f} | {pair[0]} | {pair[1]} | {pair[2]} |"
        )
    lines.append(
        f"\nPre-named headline: `{HEADLINE[0]}` + `{HEADLINE[1]}` ({HEADLINE[2]}); baseline: "
        f"`{BASELINE[0]}` + `{BASELINE[1]}`. The 50 splits overlap, so the CI describes "
        "variation over the choice of test models at these 91 models, not an independent "
        "sample.\n"
    )
    lines.append(f"## 2. Cross-fitted ranking of all {study.n_models} models ({N_FOLDS} folds)\n")
    lines.append(
        "Every model gets one estimate from a fit that never saw it (about "
        f"{study.n_models - study.n_models // N_FOLDS} training models per fold). tau and MAE over "
        f"all {study.n_models} pooled held-out estimates.\n"
    )
    lines.append("| selection | estimator | IRT | tau | MAE | RMSE |")
    lines.append("|---|---|---|---|---|---|")
    for key in _ordered(list(study.fold)):
        m = study.fold[key]
        lines.append(
            f"| {key[0]} | {key[1]} | {key[2]} | {m.tau:.3f} | {m.mae:.4f} | {m.rmse:.4f} |"
        )
    lines.append(f"\n## 3. Reference: random subsets against all {study.n_models} true scores\n")
    lines.append(
        f"{N_REFERENCE_DRAWS} random draws each (no model split: a random subset uses no "
        "training data); mean (2.5th to 97.5th percentile over draws).\n"
    )
    lines.append("| subset | tau | MAE |")
    lines.append("|---|---|---|")
    for name, ms in study.reference.items():
        tau = _interval([m.tau for m in ms])
        mae = _interval([m.mae for m in ms])
        lines.append(
            f"| {name} (anchor-mean) | {tau[0]:.3f} ({tau[1]:.3f} to {tau[2]:.3f}) "
            f"| {mae[0]:.4f} ({mae[1]:.4f} to {mae[2]:.4f}) |"
        )
    return "\n".join(lines) + "\n"
