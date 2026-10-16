from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .aggregate import PairResolution, compare_pairs, paired_comparison
from .models import Model, get_model
from .runner import EvalRecord, generate_leaderboard, run
from .spec import SpecError, TaskSpec


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

    summary = run(specs, models, out_dir, max_workers=args.workers)

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

    leaderboard = generate_leaderboard(records)
    md = leaderboard.to_markdown()
    with open(board_file, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    print(md)
    return 0


def _read_scores(path: Path, model: str) -> dict[tuple[str, str], float]:
    """(task, example_id) -> score for one model in a results.jsonl file."""
    scores: dict[tuple[str, str], float] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["model"] == model:
                scores[(str(row["task"]), str(row["example_id"]))] = float(row["score"])
    return scores


def _read_all_scores(path: Path) -> dict[str, dict[object, float]]:
    """model -> {(task, example_id): score}, models in order of first appearance."""
    scores: dict[str, dict[object, float]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            scores.setdefault(row["model"], {})[(str(row["task"]), str(row["example_id"]))] = float(
                row["score"]
            )
    return scores


def _verdict(r: PairResolution) -> str:
    if r.resolved:
        return "resolved"
    if r.n_needed is None:
        return "unresolved (observed diff = 0)"
    return f"unresolved (needs n≈{r.n_needed})"


def compare_all_pairs_command(args: argparse.Namespace) -> int:
    """All model pairs on shared examples, Holm-corrected over the whole family."""
    if args.a or args.b or args.results_b:
        sys.stderr.write("Error: --all-pairs cannot be combined with --a/--b/--results-b\n")
        return 1
    all_scores = _read_all_scores(Path(args.results))
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
    rows = compare_pairs(all_scores, pairs, effect=args.effect, seed=args.seed)
    print(f"\n### All pairs ({len(pairs)} comparisons, pooled over tasks, A - B)\n")
    print(
        "| A vs B | n | A - B | 95% CI (paired bootstrap) | W / L / T | sign p | "
        "randomisation p | Holm p | MDE (80%) | n for 80% power | verdict |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        needed = "n/a" if r.n_needed is None else str(r.n_needed)
        print(
            f"| {r.model_a} vs {r.model_b} | {r.n} | {r.diff:+.3f} | "
            f"[{r.diff_ci_lo:+.3f}, {r.diff_ci_hi:+.3f}] | {r.wins} / {r.losses} / {r.ties} | "
            f"{r.sign_p:.3g} | {r.rand_p:.3g} | {r.holm_p:.3g} | {r.mde:.3f} | {needed} | "
            f"{_verdict(r)} |"
        )
    target = "the observed |A - B|" if args.effect is None else f"|A - B| = {args.effect}"
    print(
        "\nrandomisation p: two-sided paired sign-flip test (exact for <= 20 nonzero "
        "differences, else 10,000 seeded Monte Carlo draws). Holm p: Holm-Bonferroni over "
        f"these {len(pairs)} pairs; resolved = Holm p < 0.05. MDE and n use alpha = 0.05, "
        f"power 0.8, normal approximation with the observed SD of the differences; n is for "
        f"{target}. The sign test is shown for reference only.\n"
    )
    return 0


def compare_command(args: argparse.Namespace) -> int:
    """Paired comparison of two models on the examples both were scored on."""
    if args.all_pairs:
        return compare_all_pairs_command(args)
    if not (args.a and args.b):
        sys.stderr.write("Error: give --a and --b, or --all-pairs\n")
        return 1
    file_a = Path(args.results)
    file_b = Path(args.results_b) if args.results_b else file_a
    a = _read_scores(file_a, args.a)
    b = _read_scores(file_b, args.b)
    shared = sorted(set(a) & set(b))
    if not shared:
        sys.stderr.write(f"Error: no shared (task, example_id) for {args.a!r} and {args.b!r}\n")
        return 1

    tasks = sorted({task for task, _ in shared})
    print(f"\n### {args.a} (A) vs {args.b} (B), paired on {len(shared)} examples\n")
    print("| Task | n | A | B | A - B | 95% CI (paired bootstrap) | W / L / T | sign p |")
    print("|---|---|---|---|---|---|---|---|")
    for task in [*tasks, "ALL"]:
        keys = shared if task == "ALL" else [k for k in shared if k[0] == task]
        c = paired_comparison([a[k] for k in keys], [b[k] for k in keys], seed=args.seed)
        print(
            f"| {task} | {c.n} | {c.mean_a:.3f} | {c.mean_b:.3f} | {c.diff:+.3f} | "
            f"[{c.diff_ci_lo:+.3f}, {c.diff_ci_hi:+.3f}] | {c.wins} / {c.losses} / {c.ties} | "
            f"{c.sign_p:.3g} |"
        )
    print(
        "\nALL pools examples across tasks (micro average). "
        "p-values are not corrected for the number of tasks.\n"
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

    args = parser.parse_args(argv)

    if args.subcommand == "run":
        return run_command(args)
    elif args.subcommand == "leaderboard":
        return leaderboard_command(args)
    elif args.subcommand == "compare":
        return compare_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
