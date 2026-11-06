"""Coverage of the leaderboard confidence interval at small n (``docs/protocol-leaderboard-ci.md``).

    uv run --offline python scripts/leaderboard_ci_check.py --seeds 1,2 \\
        --out runs/stats-check/leaderboard-ci-dev.md                       # development seeds
    uv run --offline python scripts/leaderboard_ci_check.py --seeds 4001,4002,4003 \\
        --winner <name> --out runs/stats-check/leaderboard-ci.md           # final scoring

Simulates Bernoulli(p) task scores and scores the 95% intervals of the shipped
``bootstrap_macro_ci`` (percentile, what the leaderboard prints), ``bootstrap_mean_ci``
(bootstrap-t) and ``statscheck.wilson_interval`` for single tasks, and the macro mean of tasks
sized (35, 35, 10, 35) for the shipped percentile interval and three candidate alternatives.
Coverage rates are classified with the ``stats-check`` rule (Wilson 99% interval entirely below
0.95 means ``undercovers``). At most 2 worker processes.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

import numpy as np

from evalkit.aggregate import bootstrap_macro_ci, bootstrap_mean_ci
from evalkit.statscheck import Rate, classify_coverage, wilson_interval, worker_pool

LEVEL = 0.95
RESAMPLES = 1000
REPS = 2000
PS = (0.5, 0.7, 0.9, 0.97)
TASK_NS = (10, 35, 240)
MACRO_SIZES = (35, 35, 10, 35)
TOL = 1e-9
MAX_WORKERS = 2

TASK_METHODS = ("percentile", "bootstrap-t", "wilson")
MACRO_ALTERNATIVES = ("mover-wilson", "neff-wilson", "strat-bootstrap-t")
MACRO_METHODS = ("percentile", *MACRO_ALTERNATIVES)
DEGENERATE_COLUMNS = ("percentile", "bootstrap-t")  # intervals that can collapse to a point

Interval = tuple[float, float]


@dataclass(frozen=True)
class Cell:
    cell_id: int
    kind: str  # "task" or "macro"
    sizes: tuple[int, ...]
    p: float

    @property
    def label(self) -> str:
        if self.kind == "macro":
            return f"macro {'/'.join(map(str, self.sizes))}"
        return f"task n={self.sizes[0]}"

    @property
    def methods(self) -> tuple[str, ...]:
        return MACRO_METHODS if self.kind == "macro" else TASK_METHODS


def build_cells() -> list[Cell]:
    cells: list[Cell] = []
    for n in TASK_NS:
        for p in PS:
            cells.append(Cell(len(cells), "task", (n,), p))
    for p in PS:
        cells.append(Cell(len(cells), "macro", MACRO_SIZES, p))
    return cells


# ----------------------------------------------------------------- candidate intervals


def wilson_bounds(p_hat: float, n: float, level: float = LEVEL) -> Interval:
    """Wilson score interval from a proportion and a (possibly fractional) sample size."""
    z = NormalDist().inv_cdf(0.5 + level / 2.0)
    denom = 1.0 + z * z / n
    centre = (p_hat + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z * z / (4.0 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mover_wilson(ks: Sequence[int], ns: Sequence[int], level: float = LEVEL) -> Interval:
    """Newcombe square-and-add of the per-task Wilson intervals for the unweighted mean."""
    w = 1.0 / len(ns)
    m = sum(w * k / n for k, n in zip(ks, ns, strict=True))
    lo_sq = hi_sq = 0.0
    for k, n in zip(ks, ns, strict=True):
        lo, hi = wilson_interval(k, n, level)
        lo_sq += (w * (k / n - lo)) ** 2
        hi_sq += (w * (hi - k / n)) ** 2
    return (m - math.sqrt(lo_sq), m + math.sqrt(hi_sq))


def neff_wilson(ks: Sequence[int], ns: Sequence[int], level: float = LEVEL) -> Interval:
    """Wilson interval of the macro mean on the sample size matching its plug-in variance."""
    w = 1.0 / len(ns)
    props = [k / n for k, n in zip(ks, ns, strict=True)]
    m = sum(w * q for q in props)
    var = sum(w * w * q * (1.0 - q) / n for q, n in zip(props, ns, strict=True))
    n_eff = m * (1.0 - m) / var if var > 0.0 else 1.0 / sum(w * w / n for n in ns)
    return wilson_bounds(m, n_eff, level)


def strat_bootstrap_t(
    ks: Sequence[int],
    ns: Sequence[int],
    rng: np.random.Generator,
    level: float = LEVEL,
    resamples: int = RESAMPLES,
) -> Interval:
    """Stratified bootstrap-t of the unweighted mean of per-task proportions.

    A resample of a 0/1 task is ``Binomial(n, k / n)`` successes, the same law as resampling
    the items. Falls back to the percentile interval when the original ``se`` is 0 or fewer
    than half of the resamples have a nonzero ``se*``."""
    w = 1.0 / len(ns)
    m = sum(w * k / n for k, n in zip(ks, ns, strict=True))
    boot_m = np.zeros(resamples)
    boot_var = np.zeros(resamples)
    var = 0.0
    for k, n in zip(ks, ns, strict=True):
        q = k / n
        var += w * w * (q * (1.0 - q) * n / (n - 1)) / n
        kb = rng.binomial(n, q, size=resamples)
        qb = kb / n
        boot_m += w * qb
        boot_var += w * w * (qb * (1.0 - qb) * n / (n - 1)) / n
    alpha = 1.0 - level
    se = math.sqrt(var)
    ok = boot_var > 1e-24
    if se > 0.0 and int(ok.sum()) >= 0.5 * resamples:
        t = (boot_m[ok] - m) / np.sqrt(boot_var[ok])
        q_lo, q_hi = np.quantile(t, [alpha / 2.0, 1.0 - alpha / 2.0])
        return (max(0.0, m - float(q_hi) * se), min(1.0, m - float(q_lo) * se))
    lo, hi = np.percentile(boot_m, [100.0 * alpha / 2.0, 100.0 * (1.0 - alpha / 2.0)])
    return (float(lo), float(hi))


# ------------------------------------------------------------------------- simulation


def scores_of(k: int, n: int) -> list[float]:
    return [1.0] * k + [0.0] * (n - k)


def intervals(
    cell: Cell, ks: Sequence[int], seed: int, rng: np.random.Generator
) -> dict[str, Interval]:
    ns = cell.sizes
    out: dict[str, Interval] = {}
    task_scores = {f"t{i}": scores_of(k, n) for i, (k, n) in enumerate(zip(ks, ns, strict=True))}
    _, lo, hi = bootstrap_macro_ci(task_scores, num_resamples=RESAMPLES, seed=seed)
    out["percentile"] = (lo, hi)
    if cell.kind == "task":
        _, lo, hi = bootstrap_mean_ci(
            scores_of(ks[0], ns[0]), num_resamples=RESAMPLES, seed=seed, method="studentized"
        )
        out["bootstrap-t"] = (lo, hi)
        out["wilson"] = wilson_interval(ks[0], ns[0], LEVEL)
    else:
        out["mover-wilson"] = mover_wilson(ks, ns)
        out["neff-wilson"] = neff_wilson(ks, ns)
        out["strat-bootstrap-t"] = strat_bootstrap_t(ks, ns, rng)
    return out


@dataclass
class CellResult:
    cell: Cell
    reps: int
    covered: dict[str, int]
    width: dict[str, float]  # sum of widths
    degenerate: dict[str, int]  # intervals with lo == hi


def run_cell(args: tuple[Cell, int, int]) -> CellResult:
    cell, seed, reps = args
    rng = np.random.default_rng(np.random.SeedSequence([seed, cell.cell_id]))
    boot_seeds = rng.integers(0, 2**31 - 1, size=reps)
    covered = dict.fromkeys(cell.methods, 0)
    width = dict.fromkeys(cell.methods, 0.0)
    degenerate = dict.fromkeys(cell.methods, 0)
    for r in range(reps):
        ks = [int(rng.binomial(n, cell.p)) for n in cell.sizes]
        for name, (lo, hi) in intervals(cell, ks, int(boot_seeds[r]), rng).items():
            covered[name] += lo - TOL <= cell.p <= hi + TOL
            width[name] += hi - lo
            degenerate[name] += hi - lo < TOL
    return CellResult(cell, reps, covered, width, degenerate)


def pooled(results: list[CellResult]) -> CellResult:
    first = results[0]
    return CellResult(
        first.cell,
        sum(r.reps for r in results),
        {m: sum(r.covered[m] for r in results) for m in first.covered},
        {m: sum(r.width[m] for r in results) for m in first.width},
        {m: sum(r.degenerate[m] for r in results) for m in first.degenerate},
    )


# ---------------------------------------------------------------------------- report


def rate(res: CellResult, method: str) -> Rate:
    return Rate(res.covered[method], res.reps)


def flagged(res: CellResult, method: str) -> bool:
    return classify_coverage(rate(res, method)) == "undercovers"


def macro_winner(macro: list[CellResult]) -> str:
    def key(m: str) -> tuple[int, float, int]:
        f = sum(flagged(r, m) for r in macro)
        short = sum(max(0.0, 0.95 - rate(r, m).value) for r in macro)
        return (f, round(short, 12), MACRO_ALTERNATIVES.index(m))

    return min(MACRO_ALTERNATIVES, key=key)


def fmt_cell(res: CellResult, method: str) -> str:
    r = rate(res, method)
    mark = {"undercovers": " **U**", "overcovers": " O", "ok": ""}[classify_coverage(r)]
    return f"{r.fmt()}{mark}"


def table(results: list[CellResult], methods: tuple[str, ...], first_col: str) -> list[str]:
    head = [first_col, "p", "reps", *methods, *[f"width {m}" for m in methods]]
    head += [f"lo=hi {m}" for m in methods if m in DEGENERATE_COLUMNS]
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for res in results:
        cells = [res.cell.label, f"{res.cell.p}", str(res.reps)]
        cells += [fmt_cell(res, m) for m in methods]
        cells += [f"{res.width[m] / res.reps:.3f}" for m in methods]
        cells += [f"{res.degenerate[m] / res.reps:.3f}" for m in methods if m in DEGENERATE_COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def report(
    per_seed: dict[int, list[CellResult]], reps: int, winner: str | None, workers: int
) -> str:
    seeds = sorted(per_seed)
    n_cells = len(per_seed[seeds[0]])
    total = [pooled([per_seed[s][i] for s in seeds]) for i in range(n_cells)]
    task = [r for r in total if r.cell.kind == "task"]
    macro = [r for r in total if r.cell.kind == "macro"]
    dev_winner = macro_winner(macro)
    f = {m: sum(flagged(r, m) for r in task) for m in TASK_METHODS}
    g = {m: sum(flagged(r, m) for r in macro) for m in MACRO_METHODS}
    lines = [
        "# Leaderboard CI coverage (`scripts/leaderboard_ci_check.py`)",
        "",
        f"Protocol: `docs/protocol-leaderboard-ci.md`. Seeds {', '.join(map(str, seeds))}, "
        f"{reps} replications per cell and seed ({reps * len(seeds)} pooled), {RESAMPLES} "
        f"bootstrap resamples, nominal level {LEVEL:.0%}, {workers} worker process(es). "
        "Coverage is shown with its Wilson 99% interval; **U** = flagged `undercovers` (interval "
        "entirely below 0.95), O = `overcovers` (entirely above 0.96). Width is the mean "
        "interval width; `lo=hi` is the share of degenerate intervals.",
        "",
        "## Per-task cells (`bootstrap_macro_ci` on one task = the leaderboard interval)",
        "",
        *table(task, TASK_METHODS, "cell"),
        "",
        "Flagged cells of 12: " + ", ".join(f"{m} {f[m]}" for m in TASK_METHODS) + ".",
        "",
        "## Macro cells (tasks sized 35, 35, 10, 35)",
        "",
        *table(macro, MACRO_METHODS, "cell"),
        "",
        "Flagged cells of 4: " + ", ".join(f"{m} {g[m]}" for m in MACRO_METHODS) + ".",
        "",
        f"Macro winner on these data by the protocol's selection rule: `{dev_winner}`.",
    ]
    if len(seeds) > 1:
        lines += ["", "## Per-seed flagged cells (descriptive)", ""]
        lines += [
            "| seed | "
            + " | ".join(f"task {m}" for m in TASK_METHODS)
            + " | "
            + " | ".join(f"macro {m}" for m in MACRO_METHODS)
            + " |"
        ]
        lines += [
            "|" + "|".join("---" for _ in range(1 + len(TASK_METHODS) + len(MACRO_METHODS))) + "|"
        ]
        for s in seeds:
            t = [r for r in per_seed[s] if r.cell.kind == "task"]
            mm = [r for r in per_seed[s] if r.cell.kind == "macro"]
            lines.append(
                f"| {s} | "
                + " | ".join(str(sum(flagged(r, m) for r in t)) for m in TASK_METHODS)
                + " | "
                + " | ".join(str(sum(flagged(r, m) for r in mm)) for m in MACRO_METHODS)
                + " |"
            )
    if winner is not None:
        sw1 = f["percentile"] >= 3 and f["wilson"] <= 1
        sw2 = g["percentile"] >= 2 and g[winner] <= 1
        lines += [
            "",
            "## Decision rules (protocol)",
            "",
            f"1. Per-task: F_pct = {f['percentile']}, F_wil = {f['wilson']}. Switch if "
            f"F_pct >= 3 and F_wil <= 1: **{'switch' if sw1 else 'unchanged'}**.",
            f"2. Macro (winner `{winner}`): G_pct = {g['percentile']}, G_alt = {g[winner]}. "
            f"Switch if G_pct >= 2 and G_alt <= 1: **{'switch' if sw2 else 'unchanged'}**.",
        ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", required=True, help="comma-separated seeds")
    ap.add_argument("--reps", type=int, default=REPS, help="replications per cell and seed")
    ap.add_argument("--workers", type=int, default=2, help=f"at most {MAX_WORKERS}")
    ap.add_argument("--winner", choices=MACRO_ALTERNATIVES, help="macro alternative to score")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    workers = max(1, min(MAX_WORKERS, args.workers))
    seeds = [int(s) for s in args.seeds.split(",")]
    cells = build_cells()
    per_seed: dict[int, list[CellResult]] = {}
    with worker_pool(workers) if workers > 1 else ProcessPoolExecutor(max_workers=1) as pool:
        for seed in seeds:
            jobs = [(c, seed, args.reps) for c in cells]
            per_seed[seed] = list(pool.map(run_cell, jobs))
            print(f"seed {seed} done", file=sys.stderr, flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report(per_seed, args.reps, args.winner, workers))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
