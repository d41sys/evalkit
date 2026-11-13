from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections.abc import Hashable, Mapping, Sequence
from pathlib import Path

import numpy as np

from .aggregate import (
    ASYMMETRIC_METHOD,
    ASYMMETRIC_METHODS,
    CI_METHODS,
    RAND_METHODS,
    TIE_FALLBACK,
    TIE_FALLBACKS,
    TIE_GATE,
    PairResolution,
    build_pairwise_matches,
    compare_pairs,
    compute_elo_ratings,
    paired_comparison,
)
from .audit import audit, render_audit
from .clustered import cluster_bootstrap_ci, encode_clusters
from .helm import import_helm_lite
from .helm_metrics import run_metric_check
from .helm_study import GAPS, run_study
from .irt_subset import (
    N_FOLDS,
    N_REFERENCE_DRAWS,
    N_SPLITS,
    N_TEST,
)
from .irt_subset import (
    render_markdown as render_irt_markdown,
)
from .irt_subset import (
    run_study as run_irt_study,
)
from .judge import (
    DEFAULT_RUBRIC,
    Judge,
    PointItem,
    Rubric,
    length_bias,
    pair_item_from_row,
    pairwise_rows,
    point_verdict,
    pointwise_row,
    position_flip_rate,
    verdict_score,
)
from .llmcache import CachedCompleter, CacheMiss, CallBudgetExceeded
from .metrics.helm_compat import helm_metric_name
from .models import DEFAULT_ANTHROPIC_MODEL, Completer, Model, get_model
from .ranking import bradley_terry_bootstrap, render_bradley_terry
from .results import ClusterLabel, ItemKey, load_results, merge_clusters
from .review import failure_mode_counts, render_failure_modes, write_review_sheet
from .runner import EceBinning, EvalRecord, generate_leaderboard, run
from .samples import pass_hat_k
from .spec import SpecError, TaskSpec
from .statscheck import (
    StatsCheckConfig,
    check_args,
    default_workers,
    parse_floats,
    parse_ints,
    render_markdown,
    run_stats_check,
)
from .statscheck_cluster import (
    ClusterCheckConfig,
    render_cluster_markdown,
    run_cluster_check,
)
from .trajectory import load_trajectory_rows, render_trajectory, trajectory_table


def find_task_specs(tasks_dir: Path) -> list[TaskSpec]:
    """Find all TaskSpec yaml files in a directory or its subdirectories."""
    if not tasks_dir.exists():
        raise SpecError(f"Tasks directory not found: {tasks_dir}")

    specs: list[TaskSpec] = []
    if tasks_dir.is_file() and tasks_dir.suffix.lower() in (".yaml", ".yml"):
        specs.append(TaskSpec.from_yaml(tasks_dir))
        return specs

    # Look for spec.yaml in immediate child directories or any .yaml files
    yaml_files = sorted(list(tasks_dir.glob("*/spec.yaml")) + list(tasks_dir.glob("*.yaml")))
    if not yaml_files:
        yaml_files = sorted(tasks_dir.glob("**/*.yaml"))

    seen_paths: set[Path] = set()
    for yf in yaml_files:
        resolved = yf.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        try:
            spec = TaskSpec.from_yaml(resolved)
            specs.append(spec)
        except Exception as exc:
            sys.stderr.write(f"Warning: Failed to load spec from {yf}: {exc}\n")

    if not specs:
        raise SpecError(f"No valid task specs found in {tasks_dir}")

    return specs


def parse_models(models_str: str, hf_batch_size: int = 1) -> list[Model]:
    model_names = [m.strip() for m in models_str.split(",") if m.strip()]
    return [
        get_model(name, batch_size=hf_batch_size) if name.startswith("hf:") else get_model(name)
        for name in model_names
    ]


def _ece_binning(metric_mode: str) -> EceBinning:
    return "equal_mass" if metric_mode == "helm" else "equal_width"


def _helm_metrics(names: Sequence[str]) -> list[str]:
    """The same metric list in HELM mode (``helm:`` prefix; ValueError if HELM has no such one)."""
    return [n if n.startswith("helm:") else f"helm:{helm_metric_name(n)}" for n in names]


def run_command(args: argparse.Namespace) -> int:
    tasks_path = Path(args.tasks)
    specs = find_task_specs(tasks_path)
    models = parse_models(args.models, args.hf_batch_size)
    out_dir = Path(args.out)

    print(f"Loaded {len(specs)} task specs from {tasks_path}")
    print(f"Loaded {len(models)} models: {[m.name for m in models]}")
    for m in models:
        revision = getattr(m, "revision", None)
        if revision:
            print(f"  {m.name}: resolved revision {revision}")
    print(f"Executing evaluations -> {out_dir}")

    if args.metric_mode == "helm":
        specs = [s.model_copy(update={"metrics": _helm_metrics(s.metrics)}) for s in specs]
    summary = run(
        specs,
        models,
        out_dir,
        max_workers=args.workers,
        samples=args.samples,
        ece_binning=_ece_binning(args.metric_mode),
    )

    print(f"\nDone! Evaluated: {summary.total_evaluated}, Skipped: {summary.total_skipped}")
    print(f"Results written to: {summary.results_path}")
    print(f"Leaderboard written to: {summary.leaderboard_path}\n")
    print(summary.leaderboard.to_markdown())
    return 0


def leaderboard_command(args: argparse.Namespace) -> int:
    target_dir = Path(args.dir)
    board_file = target_dir / "leaderboard.md"
    results_file = target_dir / "results.jsonl"

    if board_file.is_file() and not args.recompute:
        print(board_file.read_text(encoding="utf-8"))
        return 0

    if not results_file.is_file():
        sys.stderr.write(f"Error: Neither leaderboard.md nor results.jsonl found in {target_dir}\n")
        return 1

    records: list[EvalRecord] = []
    with open(results_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(EvalRecord.from_dict(json.loads(line)))
            except Exception:
                continue

    leaderboard = generate_leaderboard(
        records, ece_binning=_ece_binning(args.metric_mode), bradley_terry=args.bt
    )
    md = leaderboard.to_markdown()
    with open(board_file, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    print(md)
    return 0


def _item_labels(
    keys: Sequence[ItemKey], clusters: Mapping[ItemKey, ClusterLabel] | None
) -> list[Hashable] | None:
    """Cluster label per item (an item without a cluster id is its own cluster).

    None when there is no cluster map or the items fall into fewer than two clusters.
    """
    if not clusters:
        return None
    labels: list[Hashable] = [clusters.get(k, ("\0singleton", k)) for k in keys]
    return labels if len(set(labels)) >= 2 else None


def _ratio(r: float) -> str:
    return "n/a" if math.isnan(r) else f"{r:.2f}"


def _verdict(r: PairResolution) -> str:
    if r.resolved:
        return "resolved"
    if r.n_needed is None:
        return "unresolved (observed diff = 0)"
    return f"unresolved (needs n≈{r.n_needed})"


def _print_pass_k(
    entries: Sequence[tuple[str, dict[ItemKey, list[float]]]],
    clusters: Mapping[ItemKey, ClusterLabel] | None,
    k: int | None,
    seed: int,
) -> int:
    """pass^k table for models whose items have several samples; 0 on success.

    Printed when some item has more than one sample or ``k`` is given. ``k`` defaults to the
    fewest samples any item has.
    """
    counts = [len(v) for _, items in entries for v in items.values()]
    if not counts or (k is None and max(counts) < 2):
        return 0
    k_eff = k if k is not None else min(counts)
    if k_eff < 1 or k_eff > min(counts):
        sys.stderr.write(
            f"Error: --pass-k {k_eff} needs at least that many samples for every item "
            f"(fewest found: {min(counts)})\n"
        )
        return 1
    print(
        f"\n### Multi-sample: item averages and pass^{k_eff} "
        f"(samples per item {min(counts)} to {max(counts)})\n"
    )
    print(f"| model | items | pass^1 (mean over samples) | pass^{k_eff} | 95% CI of pass^{k_eff} |")
    print("|---|---|---|---|---|")
    for name, items in entries:
        keys = list(items)
        try:
            per_item = pass_hat_k(items, k_eff)
            first = pass_hat_k(items, 1)
        except ValueError:
            print(f"| {name} | {len(keys)} | n/a | n/a | scores are not 0/1, pass^k undefined |")
            continue
        vals = np.array([per_item[key] for key in keys])
        labels = _item_labels(keys, clusters)
        if labels is None:
            labels = [("\0singleton", key) for key in keys]
        if len(set(labels)) < 2:
            ci = "n/a"
            point = float(vals.mean())
        else:
            point, lo, hi = cluster_bootstrap_ci(vals, encode_clusters(labels), 10000, seed=seed)
            ci = f"[{lo:.3f}, {hi:.3f}]"
        print(
            f"| {name} | {len(keys)} | {float(np.mean(list(first.values()))):.3f} | "
            f"{point:.3f} | {ci} |"
        )
    print(
        f"\nItem score = mean of the item's samples. pass^{k_eff} = mean over items of "
        f"C(c, {k_eff}) / C(n, {k_eff}) for c correct of n samples, an unbiased estimate of "
        "P(all samples of an item correct) (Yao et al. 2024, tau-bench, arXiv 2406.12045). "
        "CI: bootstrap over items" + (" (whole clusters)" if clusters else "") + ".\n"
    )
    return 0


def compare_all_pairs_command(args: argparse.Namespace) -> int:
    """All model pairs on shared examples, Holm-corrected over the whole family."""
    if args.a or args.b or args.results_b:
        sys.stderr.write("Error: --all-pairs cannot be combined with --a/--b/--results-b\n")
        return 1
    try:
        table = load_results(Path(args.results))
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    all_scores = table.all_item_scores()
    if args.models:
        names = [m.strip() for m in args.models.split(",") if m.strip()]
        missing = [m for m in names if m not in all_scores]
        if missing:
            sys.stderr.write(f"Error: models not in results: {missing}\n")
            return 1
    else:
        names = list(all_scores)
    if len(names) < 2:
        sys.stderr.write("Error: --all-pairs needs at least two models\n")
        return 1
    pairs = [(names[i], names[j]) for i in range(len(names)) for j in range(i + 1, len(names))]
    for a_name, b_name in pairs:
        if not set(all_scores[a_name]) & set(all_scores[b_name]):
            sys.stderr.write(f"Error: no shared (task, example_id) for {a_name!r} and {b_name!r}\n")
            return 1
    rows = compare_pairs(
        all_scores,
        pairs,
        effect=args.effect,
        seed=args.seed,
        ci_method=args.ci_method,
        clusters=table.clusters or None,
        rand_tie_fallback=args.tie_fallback,
    )
    clustered = any(r.clustering is not None for r in rows)
    print(f"\n### All pairs ({len(pairs)} comparisons, pooled over tasks, A - B)\n")
    ci_head = "cluster bootstrap" if clustered else "paired bootstrap"
    rand_head = "cluster randomisation p" if clustered else "randomisation p"
    cluster_head = " clusters | naive SE | clustered SE (ratio) | ICC | DEFF |" if clustered else ""
    print(
        f"| A vs B | n |{cluster_head} A - B | 95% CI ({ci_head}) | W / L / T | sign p | "
        f"{rand_head} | Holm p | MDE (80%) | n for 80% power | verdict |"
    )
    print("|---|---|" + ("---|" * 5 if clustered else "") + "---|" * 9)
    for r in rows:
        needed = "n/a" if r.n_needed is None else str(r.n_needed)
        mde = "unattainable" if math.isinf(r.mde) else f"{r.mde:.3f}"
        cl = r.clustering
        cells = ""
        if clustered:
            cells = (
                " n/a | n/a | n/a | n/a | n/a |"
                if cl is None
                else f" {cl.n_clusters} | {cl.naive_se:.4f} | {cl.cluster_se:.4f} "
                f"({_ratio(cl.se_ratio)}x) | {cl.icc:.2f} | {cl.deff:.2f} |"
            )
        print(
            f"| {r.model_a} vs {r.model_b} | {r.n} |{cells} {r.diff:+.3f} | "
            f"[{r.diff_ci_lo:+.3f}, {r.diff_ci_hi:+.3f}] | {r.wins} / {r.losses} / {r.ties} | "
            f"{r.sign_p:.3g} | {r.rand_p:.3g} | {r.holm_p:.3g} | {mde} | {needed} | "
            f"{_verdict(r)} |"
        )
    target = "the observed |A - B|" if args.effect is None else f"|A - B| = {args.effect}"
    methods = sorted({r.ci_method for r in rows})
    kinds = {r.binary for r in rows}
    power_note = {
        frozenset({True}): "exact McNemar power (Duffy 1984) at the observed discordant rate",
        frozenset({False}): "normal approximation with the observed SD of the differences",
        frozenset({True, False}): (
            "exact McNemar power (Duffy 1984) at the observed discordant rate for 0/1 "
            "scores, normal approximation with the observed SD of the differences otherwise"
        ),
    }[frozenset(kinds)]
    flip = (
        "cluster sign-flip test (whole clusters change sign together; exact for <= 20 nonzero "
        "cluster sums, else 10,000 seeded Monte Carlo draws)"
        if clustered
        else "paired sign-flip test (exact for <= 20 nonzero differences, else 10,000 seeded "
        "Monte Carlo draws; pairs with asymmetric nonzero differences use the "
        f"{ASYMMETRIC_METHOD} test instead, see below)"
    )
    print(
        f"\nrandomisation p: two-sided {flip}. Holm p: Holm-Bonferroni over "
        f"these {len(pairs)} pairs; resolved = Holm p < 0.05. MDE and n use alpha = 0.05, "
        f"power 0.8, {power_note}; n is for {target}; MDE `unattainable` means that even "
        "every discordant pair favouring one model would not be detected at this n. "
        f"CI method: {', '.join(methods)}. The sign test is shown for reference only.\n"
    )
    if clustered:
        finite = [
            r.clustering.se_ratio
            for r in rows
            if r.clustering is not None and not math.isnan(r.clustering.se_ratio)
        ]
        spread = f"{min(finite):.2f}x to {max(finite):.2f}x" if finite else "n/a"
        print(
            "Clustered: items sharing a `cluster_id` are one resampling unit. Naive SE = "
            "s / sqrt(n); clustered SE = Miller (2024, arXiv 2411.00640, sec. 3.2) times "
            "sqrt(C / (C - 1)); ratio = "
            f"clustered / naive (here {spread}). ICC: one-way ANOVA estimate on the paired "
            "differences, clipped at 0. DEFF = 1 + (m - 1) ICC with m = sum of squared cluster "
            "sizes / n; MDE and n for power are inflated by it (n is a count of items). Items "
            "without a cluster id are their own cluster.\n"
        )
    switched = [r for r in rows if r.p_method not in ("signflip", "cluster-signflip")]
    if switched:
        switched_pairs = "; ".join(
            f"{r.model_a} vs {r.model_b} ({r.p_method}; n = {r.n}, skewness {r.skewness:+.2f})"
            for r in switched
        )
        print(
            "Asymmetric differences (the nonzero differences satisfy k < 25 * skewness^2, "
            "Cochran's rule): the sign-flip test assumes each difference is symmetric around 0 "
            "and is anti-conservative otherwise (`evalkit stats-check`), so the randomisation "
            "p column for these pairs is the test of the mean named in parentheses "
            f"(default {ASYMMETRIC_METHOD}) instead: {switched_pairs}.\n"
        )
    return _print_pass_k(
        [(m, table.samples[m]) for m in names], table.clusters or None, args.pass_k, args.seed
    )


def compare_command(args: argparse.Namespace) -> int:
    """Paired comparison of two models on the examples both were scored on."""
    if args.all_pairs:
        return compare_all_pairs_command(args)
    if not (args.a and args.b):
        sys.stderr.write("Error: give --a and --b, or --all-pairs\n")
        return 1
    file_a = Path(args.results)
    file_b = Path(args.results_b) if args.results_b else file_a
    try:
        table_a = load_results(file_a)
        table_b = table_a if file_b == file_a else load_results(file_b)
        clusters = merge_clusters(table_a, table_b) or None
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    a = table_a.item_scores(args.a)
    b = table_b.item_scores(args.b)
    shared = sorted(set(a) & set(b))
    if not shared:
        sys.stderr.write(f"Error: no shared (task, example_id) for {args.a!r} and {args.b!r}\n")
        return 1

    tasks = sorted({task for task, _ in shared})
    print(f"\n### {args.a} (A) vs {args.b} (B), paired on {len(shared)} examples\n")
    results = []
    for task in [*tasks, "ALL"]:
        keys = shared if task == "ALL" else [k for k in shared if k[0] == task]
        c = paired_comparison(
            [a[k] for k in keys],
            [b[k] for k in keys],
            seed=args.seed,
            ci_method=args.ci_method,
            clusters=_item_labels(keys, clusters),
        )
        results.append((task, c))
    clustered = any(c.clustering is not None for _, c in results)
    if clustered:
        print(
            "| Task | n | clusters | A | B | A - B | 95% CI | naive SE | clustered SE | "
            "SE ratio | W / L / T | sign p |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    else:
        print("| Task | n | A | B | A - B | 95% CI (paired bootstrap) | W / L / T | sign p |")
        print("|---|---|---|---|---|---|---|---|")
    for task, c in results:
        cl = c.clustering
        parts = [task, str(c.n)]
        if clustered:
            parts.append("n/a" if cl is None else str(cl.n_clusters))
        parts += [
            f"{c.mean_a:.3f}",
            f"{c.mean_b:.3f}",
            f"{c.diff:+.3f}",
            f"[{c.diff_ci_lo:+.3f}, {c.diff_ci_hi:+.3f}]",
        ]
        if clustered:
            parts += (
                ["n/a"] * 3
                if cl is None
                else [f"{cl.naive_se:.4f}", f"{cl.cluster_se:.4f}", f"{_ratio(cl.se_ratio)}x"]
            )
        parts += [f"{c.wins} / {c.losses} / {c.ties}", f"{c.sign_p:.3g}"]
        print("| " + " | ".join(parts) + " |")
    print(
        "\nALL pools examples across tasks (micro average). "
        "p-values are not corrected for the number of tasks.\n"
    )
    if clustered:
        print(
            "95% CI: cluster bootstrap (whole clusters resampled; rows with fewer than two "
            "clusters fall back to the item bootstrap and show n/a). Naive SE = s / sqrt(n) of "
            "the per-item differences; clustered SE = Miller (2024, arXiv 2411.00640, sec. 3.2) "
            "times sqrt(C / (C - 1)); SE ratio = clustered / naive. The sign test is item-level "
            "and ignores clusters. "
            "Items without a cluster id are their own cluster.\n"
        )
    return _print_pass_k(
        [(args.a, table_a.samples.get(args.a, {})), (args.b, table_b.samples.get(args.b, {}))],
        clusters,
        args.pass_k,
        args.seed,
    )


def stats_check_command(args: argparse.Namespace) -> int:
    """Monte Carlo validation of the shipped statistics (type-I, coverage, power, Holm FWER)."""
    config = StatsCheckConfig(
        seed=args.seed,
        reps_h0=args.reps_h0,
        reps_power=args.reps_power,
        reps_fwer=args.reps_fwer,
        resamples=args.resamples,
        draws=args.draws,
        ns=parse_ints(args.ns),
        ties=parse_floats(args.ties),
        fwer_ns=parse_ints(args.fwer_ns),
        fixed_effects=parse_floats(args.fixed_effects),
        workers=args.workers if args.workers > 0 else default_workers(),
        ci_method=args.ci_method,
        rand_method=args.rand_method,
        rand_fallback=args.rand_fallback,
        rand_tie_fallback=args.rand_tie_fallback,
        rand_tie_gate=args.rand_tie_gate,
    )
    try:
        check_args(config.ns + config.fwer_ns, config.ties)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    started = time.perf_counter()
    text = ""
    if not args.only_clustered:
        text += render_markdown(run_stats_check(config))
    if args.clustered or args.only_clustered:
        text += render_cluster_markdown(
            run_cluster_check(
                ClusterCheckConfig(
                    seed=args.seed,
                    reps=args.cluster_reps,
                    power_reps=args.cluster_power_reps,
                    resamples=args.cluster_resamples,
                    draws=args.draws,
                    iccs=parse_floats(args.cluster_iccs),
                    counts=parse_ints(args.cluster_counts),
                    workers=config.workers,
                )
            )
        )
    text += f"\nWall time {time.perf_counter() - started:.0f} s on {config.workers} worker(s).\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


def import_helm_command(args: argparse.Namespace) -> int:
    """Write an evalkit results.jsonl from compact HELM Lite per-instance files."""
    root = Path(args.dir)
    if not (root / "core_scenarios.json").is_file():
        sys.stderr.write(
            f"Error: {root}/core_scenarios.json not found; run scripts/fetch_helm_lite.py first\n"
        )
        return 1
    models = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else None
    try:
        stats = import_helm_lite(root, Path(args.out), models)
    except KeyError as exc:
        sys.stderr.write(f"Error: {exc.args[0]}\n")
        return 1
    print(
        f"Imported {stats.models} models, {stats.rows} rows over {len(stats.tasks)} tasks "
        f"({', '.join(stats.tasks)}) -> {args.out}"
    )
    if stats.skipped:
        print(f"Skipped (missing run files): {', '.join(stats.skipped)}")
    return 0


def helm_study_command(args: argparse.Namespace) -> int:
    """Rank-gap resolution study on an imported HELM Lite results.jsonl."""
    results = Path(args.results)
    if not results.is_file():
        sys.stderr.write(f"Error: {results} not found; run `evalkit import-helm` first\n")
        return 1
    started = time.perf_counter()
    text = run_study(
        results,
        Path(args.dir),
        seed=args.seed,
        resamples=args.resamples,
        gaps=parse_ints(args.gaps),
        cluster_modes=[c.strip() for c in args.cluster_modes.split(",") if c.strip()],
        cluster_resamples=args.cluster_resamples,
        bt_resamples=args.bt_resamples,
    )
    text += f"\nWall time {time.perf_counter() - started:.0f} s.\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


def irt_subset_command(args: argparse.Namespace) -> int:
    """TinyBenchmarks-style IRT subset selection on HELM Lite."""
    results = Path(args.results)
    if not results.is_file():
        sys.stderr.write(f"Error: {results} not found; run `evalkit import-helm` first\n")
        return 1
    started = time.perf_counter()
    study = run_irt_study(
        results,
        n_splits=args.splits,
        test_size=args.test_size,
        n_folds=args.folds,
        draws=args.draws,
        seed=args.seed,
        sweeps=args.sweeps,
        tol=args.tol,
    )
    text = render_irt_markdown(study)
    text += f"\nWall time {time.perf_counter() - started:.0f} s.\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


def metric_check_command(args: argparse.Namespace) -> int:
    """Re-score HELM Lite predictions with evalkit's metrics and compare with HELM's values."""
    root = Path(args.dir)
    if not (root / "core_scenarios.json").is_file():
        sys.stderr.write(f"Error: {root}/core_scenarios.json not found\n")
        return 1
    text = run_metric_check(root, stride=args.stride)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


def review_command(args: argparse.Namespace) -> int:
    n = write_review_sheet(args.results, args.out, model=args.model, include_passes=args.all)
    print(f"wrote {n} rows to {args.out}")
    return 0


def failure_modes_command(args: argparse.Namespace) -> int:
    try:
        counts = failure_mode_counts(args.sheet)
    except (OSError, ValueError) as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    print(render_failure_modes(counts))
    return 0


def rank_command(args: argparse.Namespace) -> int:
    """Bradley-Terry ratings with bootstrap intervals and online Elo from a results file."""
    try:
        table = load_results(args.results)
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    scores = table.all_item_scores()
    if len(scores) < 2:
        sys.stderr.write("Error: need at least two models\n")
        return 1
    clusters = None if args.ignore_clusters or not table.has_clusters else dict(table.clusters)
    try:
        bt = bradley_terry_bootstrap(
            {m: dict(s) for m, s in scores.items()},
            clusters=clusters,
            resamples=args.resamples,
            seed=args.seed,
            ridge=args.ridge,
        )
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    by_item: dict[str, dict[str, float]] = {}
    for model, items in scores.items():
        for key, value in items.items():
            by_item.setdefault(repr(key), {})[model] = float(value)
    elo = compute_elo_ratings(build_pairwise_matches(by_item))
    text = (
        f"# Bradley-Terry ranking of {len(bt.models)} models, {args.results}\n\n"
        + render_bradley_terry(bt, elo)
        + "\n"
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


def audit_command(args: argparse.Namespace) -> int:
    """List items that look broken, saturated, trivially passable or unstable across trials."""
    try:
        table = load_results(args.results)
        report = audit(table, args.baseline, args.oracle, args.disagreement)
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    print(render_audit(report, args.disagreement))

def trajectory_command(args: argparse.Namespace) -> int:
    """Trajectory diagnostics (Vertex metrics) per model, next to the pass rate."""
    try:
        loaded = load_trajectory_rows(args.results, args.model)
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    if not loaded.rows:
        sys.stderr.write(
            f"Error: no rows with `tool_calls` and `expected_tools` ({loaded.skipped} skipped)\n"
        )
        return 1
    table = trajectory_table(loaded.rows, args.by, args.tool)
    print(render_trajectory(table, loaded.skipped))
    return 0


def _read_pairs(path: Path, limit: int | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows[:limit] if limit else rows


def _make_completer(args: argparse.Namespace) -> CachedCompleter:
    """The cached completer for ``--judge anthropic:<model id>`` (cache-only needs no key)."""
    kind, _, model_id = args.judge.partition(":")
    if kind != "anthropic":
        raise ValueError(f"--judge must be anthropic:<model id>, got {args.judge!r}")
    model_id = model_id or DEFAULT_ANTHROPIC_MODEL
    cache = Path(args.cache) if args.cache else Path(args.out) / "judge-cache.jsonl"
    if args.cache_only:
        return CachedCompleter(None, cache, model_id=model_id, max_calls=args.max_calls)
    backend = get_model(f"anthropic:{model_id}")
    if not isinstance(backend, Completer):
        raise ValueError(f"{args.judge!r} cannot complete chat prompts")
    return CachedCompleter(backend, cache, model_id=model_id, max_calls=args.max_calls)


def judge_command(args: argparse.Namespace) -> int:
    """LLM-as-judge over a pairs file; writes results.jsonl for compare / leaderboard."""
    try:
        rows = _read_pairs(Path(args.pairs), args.limit)
        completer = _make_completer(args)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    rubric = Rubric(args.rubric_name, args.rubric_criteria, args.scale_low, args.scale_high)
    judge = Judge(completer, rubric=rubric, both_orders=not args.no_swap, workers=args.workers)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = [str(r.get("id", i)) for i, r in enumerate(rows)]
    tasks = [str(args.task or r.get("task", "judge")) for r in rows]
    clusters = [None if r.get("cluster_id") is None else str(r["cluster_id"]) for r in rows]
    names_a = [str(r.get("model_a", "A")) for r in rows]
    names_b = [str(r.get("model_b", "B")) for r in rows]
    result_rows: list[dict[str, object]] = []
    matches: list[tuple[str, str, float]] = []
    judgments: list[dict[str, object]] = []
    notes: list[str] = []
    try:
        if args.mode == "pairwise":
            items = [pair_item_from_row(r) for r in rows]
            verdicts = judge.compare_many(items)
            for i, v in enumerate(verdicts):
                result_rows += pairwise_rows(
                    task=tasks[i],
                    example_id=ids[i],
                    model_a=names_a[i],
                    model_b=names_b[i],
                    resolved=v.resolved,
                    cluster_id=clusters[i],
                )
                matches.append((names_a[i], names_b[i], verdict_score(v.resolved)))
                judgments.append(
                    {
                        "id": ids[i],
                        "first": v.first,
                        "second": v.second,
                        "resolved": v.resolved,
                        "flipped": v.flipped,
                    }
                )
            rate, n_valid, n_invalid = position_flip_rate(verdicts)
            if args.no_swap:
                notes.append("Position control off (--no-swap): each pair judged in one order.")
            else:
                notes.append(
                    f"Position-flip rate {rate:.1%} over {n_valid} items with both replies "
                    f"parsed; inconsistent verdicts were resolved to tie. {n_invalid} items had "
                    "an unparsable reply (counted as tie)."
                )
            lb = length_bias([v.resolved for v in verdicts], [it.length_diff for it in items])
            notes.append(
                f"Length diagnostic: Spearman rho of verdict with length difference "
                f"{_ratio(lb.rho)}; longer response wins {_ratio(lb.longer_wins)} of decided "
                "pairs. Longer answers can be better; compare with a human baseline before "
                "calling it bias."
            )
        else:
            point_items: list[PointItem] = []
            for r in rows:
                for key in ("response_a", "response_b"):
                    ref = r.get("reference")
                    ins = r.get("instruction")
                    point_items.append(
                        PointItem(
                            str(r["prompt"]),
                            str(r[key]),
                            None if ref is None else str(ref),
                            None if ins is None else str(ins),
                        )
                    )
            scored = judge.score_many(point_items)
            missing = 0
            for i in range(len(rows)):
                sa, sb = scored[2 * i].score, scored[2 * i + 1].score
                for model, s in ((names_a[i], sa), (names_b[i], sb)):
                    if s is None:
                        missing += 1
                        continue
                    result_rows.append(
                        pointwise_row(
                            task=tasks[i],
                            example_id=ids[i],
                            model=model,
                            score=s,
                            cluster_id=clusters[i],
                        )
                    )
                if sa is not None and sb is not None:
                    matches.append((names_a[i], names_b[i], verdict_score(point_verdict(sa, sb))))
                judgments.append({"id": ids[i], "score_a": sa, "score_b": sb})
            notes.append(
                f"Pointwise scale {rubric.low}-{rubric.high}; scores are rubric points, so "
                f"`compare` differences are in points. {missing} unparsable scores were dropped."
            )
    except (CacheMiss, CallBudgetExceeded) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    with open(out_dir / "results.jsonl", "w", encoding="utf-8") as f:
        for row in result_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(out_dir / "judgments.jsonl", "w", encoding="utf-8") as f:
        for j in judgments:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    stats = completer.stats
    elo = compute_elo_ratings(matches)
    by_model: dict[str, list[float]] = {}
    for row in result_rows:
        by_model.setdefault(str(row["model"]), []).append(float(str(row["score"])))
    print(f"\n### Judge `{args.judge}`, {args.mode}, {len(rows)} items\n")
    print("| Model | Items | Mean judge score | Elo |")
    print("|---|---|---|---|")
    for model in sorted(by_model, key=lambda m: -elo.get(m, 0.0)):
        mean = sum(by_model[model]) / len(by_model[model])
        print(f"| {model} | {len(by_model[model])} | {mean:.3f} | {elo.get(model, 1000.0):.1f} |")
    print()
    for note in notes:
        print(note + "\n")
    print(
        f"Elo: processed in file order, K = 32, from the resolved verdicts. API calls this run: "
        f"{stats.live_calls} live, {stats.hits} cache hits; tokens in/out "
        f"{stats.input_tokens}/{stats.output_tokens}. Self-preference is not controlled: do not "
        "rank answers from the judge's own model family without a human check. No logprobs.\n"
    )
    print(
        f"Next: `evalkit compare {out_dir / 'results.jsonl'} --all-pairs` (clustered SE where "
        "rows carry a cluster_id).\n"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evalkit",
        description="Evaluation runner and benchmark harness from first principles",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run evaluation benchmark")
    run_parser.add_argument(
        "--tasks",
        type=str,
        required=True,
        help="Path to tasks directory containing spec.yaml files",
    )
    run_parser.add_argument(
        "--models",
        type=str,
        default="oracle,noisy:0.3,random",
        help="Comma-separated list of models (e.g. oracle,noisy:0.3,random)",
    )
    run_parser.add_argument(
        "--out",
        type=str,
        default="runs/demo",
        help="Output directory for results and leaderboard",
    )
    run_parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker threads (default 4)",
    )
    run_parser.add_argument(
        "--hf-batch-size",
        type=int,
        default=1,
        help="hf: models decode up to this many free-generation prompts together (default 1)",
    )
    run_parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help="query every item this many times (rows get a `sample` index; default 1)",
    )
    run_parser.add_argument(
        "--metric-mode",
        choices=["evalkit", "helm"],
        default="evalkit",
        help="helm: score with HELM's metric definitions (exact_match is HELM's strict strip "
        "equality; use quasi_exact_match, f1_score, final_number_exact_match) and report ECE "
        "with HELM's equal-mass 10 bins. Use a fresh --out: resumed rows keep their old scores",
    )

    # leaderboard command
    board_parser = subparsers.add_parser("leaderboard", help="View or recompute leaderboard")
    board_parser.add_argument(
        "dir",
        type=str,
        help="Directory containing results.jsonl / leaderboard.md",
    )
    board_parser.add_argument(
        "--recompute",
        action="store_true",
        help="Recompute leaderboard from results.jsonl",
    )
    board_parser.add_argument(
        "--metric-mode",
        choices=["evalkit", "helm"],
        default="evalkit",
        help="helm: ECE with HELM's equal-mass 10 bins (ece_10_bin) instead of 15 equal-width",
    )
    board_parser.add_argument(
        "--bt",
        action="store_true",
        help="add Bradley-Terry ratings with bootstrap intervals next to Elo (recompute only)",
    )

    # compare command
    cmp_parser = subparsers.add_parser("compare", help="Paired comparison of two models")
    cmp_parser.add_argument("results", type=str, help="results.jsonl containing model A")
    cmp_parser.add_argument("--a", default=None, help="Model A name as stored in results")
    cmp_parser.add_argument("--b", default=None, help="Model B name as stored in results")
    cmp_parser.add_argument(
        "--all-pairs",
        action="store_true",
        help="Compare every model pair with randomisation p, Holm correction, MDE and power",
    )
    cmp_parser.add_argument(
        "--models", default=None, help="With --all-pairs: comma-separated model subset"
    )
    cmp_parser.add_argument(
        "--effect",
        type=float,
        default=None,
        help="With --all-pairs: target |A - B| for 'n for 80%% power' (default: observed)",
    )
    cmp_parser.add_argument(
        "--results-b", default=None, help="results.jsonl for model B (default: same file)"
    )
    cmp_parser.add_argument("--seed", type=int, default=0)
    cmp_parser.add_argument(
        "--ci-method",
        choices=CI_METHODS,
        default="auto",
        help="paired bootstrap CI: auto (studentized below 400 examples, else percentile), "
        "percentile, bca or studentized (ignored where cluster ids exist: cluster bootstrap)",
    )
    cmp_parser.add_argument(
        "--tie-fallback",
        choices=TIE_FALLBACKS,
        default=TIE_FALLBACK,
        help="With --all-pairs: test for asymmetric differences when more than "
        f"{TIE_GATE:g} of the pairs tie (none: the {ASYMMETRIC_METHOD} test on all pairs)",
    )
    cmp_parser.add_argument(
        "--pass-k",
        type=int,
        default=None,
        help="pass^k for items with several samples (default: the fewest samples per item)",
    )

    # stats-check command
    sc_parser = subparsers.add_parser(
        "stats-check",
        help="Monte Carlo check of the shipped statistics (type-I error, coverage, power, Holm)",
    )
    sc_parser.add_argument("--seed", type=int, default=0)
    sc_parser.add_argument(
        "--ci-method", choices=CI_METHODS, default="auto", help="bootstrap CI method under test"
    )
    sc_parser.add_argument(
        "--rand-method",
        choices=RAND_METHODS,
        default="auto",
        help="randomisation-test method under test (auto: sign-flip unless asymmetric)",
    )
    sc_parser.add_argument(
        "--rand-fallback",
        choices=ASYMMETRIC_METHODS,
        default=ASYMMETRIC_METHOD,
        help="test that auto switches to for asymmetric differences",
    )
    sc_parser.add_argument(
        "--rand-tie-fallback",
        choices=TIE_FALLBACKS,
        default=TIE_FALLBACK,
        help="test that auto uses instead of the fallback when asymmetric and mostly tied",
    )
    sc_parser.add_argument(
        "--rand-tie-gate",
        type=float,
        default=TIE_GATE,
        help="share of zero differences above which --rand-tie-fallback applies",
    )
    sc_parser.add_argument("--reps-h0", type=int, default=8000, help="replications per H0 cell")
    sc_parser.add_argument(
        "--reps-power", type=int, default=3000, help="replications per power/coverage cell"
    )
    sc_parser.add_argument("--reps-fwer", type=int, default=3000, help="replications per FWER cell")
    sc_parser.add_argument("--resamples", type=int, default=2000, help="bootstrap resamples")
    sc_parser.add_argument(
        "--draws", type=int, default=2000, help="randomisation Monte Carlo draws"
    )
    sc_parser.add_argument("--ns", default="20,50,115,240", help="comma-separated sample sizes")
    sc_parser.add_argument("--ties", default="0,0.5,0.8", help="comma-separated tie rates")
    sc_parser.add_argument(
        "--fwer-ns", default="50,115", help="sample sizes for the Holm FWER cells"
    )
    sc_parser.add_argument(
        "--fixed-effects", default="0.05,0.10,0.20", help="fixed-effect power cells (empty: none)"
    )
    sc_parser.add_argument(
        "--workers", type=int, default=0, help="worker processes (0: min(4, cpu count))"
    )
    sc_parser.add_argument("--out", default=None, help="also write the markdown report here")
    sc_parser.add_argument(
        "--clustered",
        action="store_true",
        help="also run the clustered-data grid (ICC 0, 0.1, 0.3; docs/protocol-clustered-se.md)",
    )
    sc_parser.add_argument(
        "--only-clustered", action="store_true", help="run only the clustered-data grid"
    )
    sc_parser.add_argument("--cluster-iccs", default="0,0.1,0.3", help="ICC values (clustered)")
    sc_parser.add_argument(
        "--cluster-counts", default="20,50,100", help="numbers of clusters (clustered)"
    )
    sc_parser.add_argument(
        "--cluster-reps", type=int, default=2000, help="replications per clustered cell"
    )
    sc_parser.add_argument(
        "--cluster-power-reps", type=int, default=2000, help="replications per clustered power cell"
    )
    sc_parser.add_argument(
        "--cluster-resamples", type=int, default=1000, help="bootstrap resamples (clustered)"
    )

    # import-helm command
    ih = subparsers.add_parser(
        "import-helm", help="Convert HELM Lite per-instance results to results.jsonl"
    )
    ih.add_argument("--dir", default="data/raw/helm-lite", help="compact HELM Lite files")
    ih.add_argument("--out", default="runs/helm-lite/results.jsonl")
    ih.add_argument("--models", default=None, help="comma-separated HELM display names")

    # helm-study command
    hs = subparsers.add_parser(
        "helm-study", help="Are the published HELM Lite rank gaps resolved by its per-item data?"
    )
    hs.add_argument("--dir", default="data/raw/helm-lite", help="compact HELM Lite files")
    hs.add_argument("--results", default="runs/helm-lite/results.jsonl")
    hs.add_argument("--seed", type=int, default=0)
    hs.add_argument("--resamples", type=int, default=1000, help="rank bootstrap resamples")
    hs.add_argument(
        "--gaps", default=",".join(str(g) for g in GAPS), help="published rank distances to test"
    )
    hs.add_argument("--out", default=None, help="also write the markdown report here")
    hs.add_argument(
        "--cluster-modes",
        default="passage,subset",
        help="comma-separated clusterings for the clustered pair families (passage, subset); "
        "empty to skip",
    )
    hs.add_argument(
        "--cluster-resamples", type=int, default=2000, help="cluster bootstrap resamples per pair"
    )
    hs.add_argument(
        "--bt-resamples",
        type=int,
        default=200,
        help="Bradley-Terry bootstrap resamples (0 skips the section)",
    )
    # irt-subset command
    ir = subparsers.add_parser(
        "irt-subset",
        help="TinyBenchmarks-style IRT subset selection on HELM Lite (~100 anchor items)",
    )
    ir.add_argument("--results", default="runs/helm-lite/results.jsonl")
    ir.add_argument("--seed", type=int, default=0)
    ir.add_argument("--splits", type=int, default=N_SPLITS, help="number of 70/21 model splits")
    ir.add_argument("--test-size", type=int, default=N_TEST, help="test models per split")
    ir.add_argument(
        "--folds", type=int, default=N_FOLDS, help="cross-fitting folds over all models"
    )
    ir.add_argument(
        "--draws",
        type=int,
        default=N_REFERENCE_DRAWS,
        help="reference random-subset draws over all models",
    )
    ir.add_argument("--sweeps", type=int, default=60, help="IRT fitting sweeps (maximum)")
    ir.add_argument(
        "--tol",
        type=float,
        default=None,
        help="stop an IRT fit once the penalised log-lik. changes by less than this per sweep",
    )
    ir.add_argument("--out", default=None, help="write the markdown report here")

    # judge command
    jd = subparsers.add_parser(
        "judge", help="LLM-as-judge over a pairs file (pairwise A/B/tie or pointwise rubric)"
    )
    jd.add_argument("--pairs", required=True, help="JSONL: prompt, response_a, response_b, ...")
    jd.add_argument("--mode", choices=["pairwise", "pointwise"], default="pairwise")
    jd.add_argument("--judge", default=f"anthropic:{DEFAULT_ANTHROPIC_MODEL}")
    jd.add_argument("--out", default="runs/judge", help="writes results.jsonl, judgments.jsonl")
    jd.add_argument("--cache", default=None, help="call cache (default: <out>/judge-cache.jsonl)")
    jd.add_argument(
        "--cache-only", action="store_true", help="never call the API; a cache miss is an error"
    )
    jd.add_argument("--max-calls", type=int, default=4000, help="cap on live API calls")
    jd.add_argument("--workers", type=int, default=8, help="concurrent calls (at most 8)")
    jd.add_argument("--limit", type=int, default=0, help="judge only the first N rows")
    jd.add_argument(
        "--task",
        default=None,
        help="task name for every row (default: the row's `task`, else 'judge'); rows that "
        "share a task and a cluster_id are one cluster in `compare`",
    )
    jd.add_argument(
        "--no-swap", action="store_true", help="pairwise: one order only (no position control)"
    )
    jd.add_argument("--rubric-name", default=DEFAULT_RUBRIC.name)
    jd.add_argument("--rubric-criteria", default=DEFAULT_RUBRIC.criteria)
    jd.add_argument("--scale-low", type=int, default=DEFAULT_RUBRIC.low)
    jd.add_argument("--scale-high", type=int, default=DEFAULT_RUBRIC.high)

    # metric-check command
    mc = subparsers.add_parser(
        "metric-check", help="evalkit metrics vs HELM's per-instance values on the same predictions"
    )
    mc.add_argument("--dir", default="data/raw/helm-lite", help="compact HELM Lite files")
    mc.add_argument("--stride", type=int, default=8, help="use every Nth model of the ranking")
    mc.add_argument("--out", default=None, help="also write the markdown report here")

    # rank command
    rk = subparsers.add_parser(
        "rank", help="Bradley-Terry ranking with bootstrap intervals, next to online Elo"
    )
    rk.add_argument("results", help="results.jsonl (rows with a cluster_id are resampled whole)")
    rk.add_argument("--resamples", type=int, default=200, help="bootstrap resamples")
    rk.add_argument("--seed", type=int, default=0)
    rk.add_argument(
        "--ridge",
        type=float,
        default=0.0,
        help="Gaussian prior on the log-strengths, for data where the MLE does not exist",
    )
    rk.add_argument(
        "--ignore-clusters", action="store_true", help="resample items even if rows have clusters"
    )
    rk.add_argument("--out", default=None, help="also write the markdown report here")

    rv = subparsers.add_parser("review", help="Write a CSV annotation sheet of failing items")
    rv.add_argument("results", help="results.jsonl")
    rv.add_argument("--out", required=True, help="sheet.csv to write")
    rv.add_argument("--model", default=None, help="only this model")
    rv.add_argument("--all", action="store_true", help="include passing items")

    fm = subparsers.add_parser(
        "failure-modes", help="Count the failure_mode labels filled into a review sheet"
    )
    fm.add_argument("sheet", help="sheet.csv from `evalkit review`, annotated")

    # audit command
    au = subparsers.add_parser(
        "audit", help="flag items that look broken, saturated, trivially passable or unstable"
    )
    au.add_argument("results", help="results.jsonl; a sample passes when its score is >= 1")
    au.add_argument("--baseline", nargs="+", default=[], help="trivial-baseline models")
    au.add_argument("--oracle", default=None, help="reference model that must pass saturated items")
    au.add_argument(
        "--disagreement", type=float, default=0.3, help="flag min(p, 1-p) above this over samples"

    # trajectory command
    tj = subparsers.add_parser(
        "trajectory",
        help="Tool-call trajectory diagnostics (Vertex metrics); never part of the score",
    )
    tj.add_argument("results", help="results.jsonl with tool_calls and expected_tools per row")
    tj.add_argument("--model", default=None, help="only this model")
    tj.add_argument("--tool", default=None, help="also report whether this tool was used")
    tj.add_argument(
        "--by",
        choices=["task", "category"],
        default=None,
        help="one table per model and task, or per model and the row's category field",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "run":
        return run_command(args)
    elif args.subcommand == "leaderboard":
        return leaderboard_command(args)
    elif args.subcommand == "compare":
        return compare_command(args)
    elif args.subcommand == "stats-check":
        return stats_check_command(args)
    elif args.subcommand == "import-helm":
        return import_helm_command(args)
    elif args.subcommand == "helm-study":
        return helm_study_command(args)
    elif args.subcommand == "irt-subset":
        return irt_subset_command(args)
    elif args.subcommand == "metric-check":
        return metric_check_command(args)
    elif args.subcommand == "rank":
        return rank_command(args)
    elif args.subcommand == "review":
        return review_command(args)
    elif args.subcommand == "failure-modes":
        return failure_modes_command(args)
    elif args.subcommand == "audit":
        return audit_command(args)
    elif args.subcommand == "trajectory":
        return trajectory_command(args)
    elif args.subcommand == "judge":
        return judge_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
