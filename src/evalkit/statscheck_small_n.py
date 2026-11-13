"""Coverage and test size at n = 20 / 50 / 100 for 0/1 outcomes (``evalkit stats-check --small-n``).

Protocol, grid, band and switch rules: ``docs/protocol-small-n.md`` (committed before the first
scoring run). Runs the *shipped* functions and the candidate Bayesian intervals of
:mod:`evalkit.small_n_ci` on simulated data and reports

* single-model 95% interval coverage (12 cells: n x accuracy p), for the leaderboard interval
  (``bootstrap_macro_ci`` on one task), bootstrap-t, Wilson, Jeffreys and uniform Beta intervals;
* paired-difference 95% interval coverage (18 cells: n x disagreement rate psi x true
  difference 0 or psi / 2) for ``paired_comparison`` ``auto``, the percentile bootstrap and
  two Dirichlet-multinomial intervals;
* type-I error of the randomisation and sign tests in the paired cells with a true difference 0.

A cell passes the band at coverage >= 0.93 (point estimate; above 0.97 is reported as ``over``,
never a failure) and type-I error <= 0.06.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

from .aggregate import bootstrap_macro_ci, bootstrap_mean_ci, mean_test_p, paired_comparison
from .small_n_ci import JEFFREYS, UNIFORM, beta_interval, dirichlet_diff_interval
from .statscheck import (
    ALPHA,
    Rate,
    Scenario,
    simulate_pairs,
    wilson_interval,
    worker_pool,
)

SMALL_NS = (20, 50, 100)
SINGLE_PS = (0.5, 0.7, 0.9, 0.95)
PAIRED_PSIS = (0.1, 0.3, 0.6)
BAND_LO = 0.93
BAND_HI = 0.97
TYPE1_MAX = 0.06
BORDERLINE = 0.005
LEAD_RESAMPLES = 1000  # the leaderboard's (runner.py) bootstrap size
_EPS = 1e-9

SINGLE_METHODS = ("percentile", "bootstrap-t", "wilson", "jeffreys", "uniform")
SINGLE_CANDIDATES = ("jeffreys", "wilson", "uniform")
PAIRED_METHODS = ("auto", "percentile", "dirichlet-jeffreys", "dirichlet-uniform")
PAIRED_CANDIDATES = ("dirichlet-jeffreys", "dirichlet-uniform")
_PRIORS = {
    "jeffreys": JEFFREYS,
    "uniform": UNIFORM,
    "dirichlet-jeffreys": JEFFREYS,
    "dirichlet-uniform": UNIFORM,
}


@dataclass(frozen=True)
class SmallNConfig:
    seed: int = 0
    reps: int = 10000
    resamples: int = 2000
    draws: int = 2000
    ns: tuple[int, ...] = SMALL_NS
    workers: int = 1


@dataclass(frozen=True)
class Cell:
    """One grid cell. ``rate`` is the accuracy ``p`` (single) or the disagreement rate (paired)."""

    cell_id: int
    kind: str  # "single" or "paired"
    n: int
    rate: float
    effect: float = 0.0

    @property
    def methods(self) -> tuple[str, ...]:
        return SINGLE_METHODS if self.kind == "single" else PAIRED_METHODS


@dataclass(frozen=True)
class CellResult:
    cell: Cell
    reps: int
    covered: dict[str, int]
    width: dict[str, float]  # mean width
    rand_rejects: int = 0  # paired, effect 0 only
    sign_rejects: int = 0

    def coverage(self, method: str) -> Rate:
        return Rate(self.covered[method], self.reps)


def plan(config: SmallNConfig) -> list[Cell]:
    """Single cells (n outer, p inner), then paired (n, psi, effect); ``cell_id`` = position."""
    ids = itertools.count()
    cells = [Cell(next(ids), "single", n, p) for n in config.ns for p in SINGLE_PS]
    for n, psi in itertools.product(config.ns, PAIRED_PSIS):
        for effect in (0.0, psi / 2.0):
            cells.append(Cell(next(ids), "paired", n, psi, effect))
    return cells


def _run_single(cell: Cell, reps: int, rng: np.random.Generator) -> CellResult:
    ks = rng.binomial(cell.n, cell.rate, size=reps)
    seeds = rng.integers(0, 2**31 - 1, size=reps)
    covered = dict.fromkeys(SINGLE_METHODS, 0)
    width = dict.fromkeys(SINGLE_METHODS, 0.0)
    for k, s in zip(ks.tolist(), seeds.tolist(), strict=True):
        scores = [1.0] * k + [0.0] * (cell.n - k)
        ivs = {
            "percentile": bootstrap_macro_ci({"t": scores}, LEAD_RESAMPLES, seed=s)[1:],
            "bootstrap-t": bootstrap_mean_ci(scores, LEAD_RESAMPLES, seed=s, method="studentized")[
                1:
            ],
            "wilson": wilson_interval(k, cell.n, 0.95),
            "jeffreys": beta_interval(k, cell.n, JEFFREYS),
            "uniform": beta_interval(k, cell.n, UNIFORM),
        }
        for name, (lo, hi) in ivs.items():
            covered[name] += lo - _EPS <= cell.rate <= hi + _EPS
            width[name] += hi - lo
    return CellResult(cell, reps, covered, {m: w / reps for m, w in width.items()})


def _run_paired(
    cell: Cell, reps: int, resamples: int, draws: int, rng: np.random.Generator
) -> CellResult:
    a, b = simulate_pairs(Scenario("binary", cell.n, 1.0 - cell.rate, cell.effect), reps, rng)
    seeds = rng.integers(0, 2**31 - 1, size=reps)
    covered = dict.fromkeys(PAIRED_METHODS, 0)
    width = dict.fromkeys(PAIRED_METHODS, 0.0)
    rand_rej = sign_rej = 0
    for i in range(reps):
        s = int(seeds[i])
        diffs = a[i] - b[i]
        cmp = paired_comparison(a[i].tolist(), b[i].tolist(), num_resamples=resamples, seed=s)
        wins, losses = int((diffs > 0).sum()), int((diffs < 0).sum())
        ties = cell.n - wins - losses
        ivs = {
            "auto": (cmp.diff_ci_lo, cmp.diff_ci_hi),
            "percentile": bootstrap_mean_ci(diffs.tolist(), resamples, seed=s, method="percentile")[
                1:
            ],
            "dirichlet-jeffreys": dirichlet_diff_interval(wins, losses, ties, JEFFREYS, seed=s),
            "dirichlet-uniform": dirichlet_diff_interval(wins, losses, ties, UNIFORM, seed=s),
        }
        for name, (lo, hi) in ivs.items():
            covered[name] += lo - _EPS <= cell.effect <= hi + _EPS
            width[name] += hi - lo
        if cell.effect == 0.0:
            rand_rej += mean_test_p(diffs, "auto", num_draws=draws, seed=s)[0] < ALPHA
            sign_rej += cmp.sign_p < ALPHA
    return CellResult(
        cell, reps, covered, {m: w / reps for m, w in width.items()}, int(rand_rej), int(sign_rej)
    )


def run_cell(job: tuple[Cell, SmallNConfig]) -> CellResult:
    cell, cfg = job
    rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, cell.cell_id]))
    if cell.kind == "single":
        return _run_single(cell, cfg.reps, rng)
    return _run_paired(cell, cfg.reps, cfg.resamples, cfg.draws, rng)


def run_small_n(config: SmallNConfig) -> list[CellResult]:
    cells = plan(config)
    jobs = [(c, config) for c in cells]
    # paired cells dominate the cost; submit them first so the pool does not end on a straggler
    order = sorted(range(len(jobs)), key=lambda i: (cells[i].kind == "single", -cells[i].n))
    if config.workers > 1:
        with worker_pool(config.workers) as pool:
            done = list(pool.map(run_cell, [jobs[i] for i in order], chunksize=1))
    else:
        done = [run_cell(jobs[i]) for i in order]
    by_index = dict(zip(order, done, strict=True))
    return [by_index[i] for i in range(len(jobs))]


# ------------------------------------------------------------------------- rules


def band_status(rate: Rate) -> str:
    """``under`` below 0.93 (a failure), ``over`` above 0.97 (reported only), else ``ok``."""
    v = rate.value
    return "under" if v < BAND_LO else "over" if v > BAND_HI else "ok"


def is_failure(result: CellResult, method: str) -> bool:
    return band_status(result.coverage(method)) == "under"


def shortfall(results: list[CellResult], method: str) -> float:
    return sum(max(0.0, BAND_LO - r.coverage(method).value) for r in results)


def failing_cells(results: list[CellResult], method: str, max_n: int | None = None) -> int:
    return sum(is_failure(r, method) for r in results if max_n is None or r.cell.n <= max_n)


def failing_n(results: list[CellResult], method: str) -> int | None:
    """``N_fail``: the largest grid ``n`` with a failing cell for ``method`` (None: no failure)."""
    ns = [r.cell.n for r in results if is_failure(r, method)]
    return max(ns) if ns else None


def select_winner(results: list[CellResult], candidates: tuple[str, ...]) -> str:
    """Fewest failing cells; ties: smaller total shortfall; then the order of ``candidates``."""
    return min(
        candidates,
        key=lambda m: (
            failing_cells(results, m),
            round(shortfall(results, m), 12),
            candidates.index(m),
        ),
    )


def _mark(rate: Rate) -> str:
    status = band_status(rate)
    near = min(abs(rate.value - BAND_LO), abs(rate.value - BAND_HI)) <= BORDERLINE
    flag = {"under": " **under**", "over": " over", "ok": ""}[status]
    return f"{rate.fmt()}{flag}{' borderline' if near and status != 'over' else ''}"


def _type1(rate: Rate) -> str:
    return f"{rate.fmt()}{' **fail**' if rate.value > TYPE1_MAX else ''}"


# ------------------------------------------------------------------------ report


def _table(results: list[CellResult], methods: tuple[str, ...], lead: list[str]) -> list[str]:
    head = [*lead, *methods, *[f"width {m}" for m in methods]]
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in results:
        c = r.cell
        first = [str(c.n), f"{c.rate:g}"] + ([f"{c.effect:.3f}"] if c.kind == "paired" else [])
        cols = [_mark(r.coverage(m)) for m in methods] + [f"{r.width[m]:.3f}" for m in methods]
        lines.append("| " + " | ".join([*first, *cols]) + " |")
    return lines


def _decision(
    results: list[CellResult], default: str, candidates: tuple[str, ...], label: str
) -> list[str]:
    n_fail = failing_n(results, default)
    lines = [
        f"{label}: `{default}` has {failing_cells(results, default)} of {len(results)} cells "
        f"below {BAND_LO}; `N_fail` = {n_fail if n_fail is not None else 'none'}."
    ]
    if n_fail is None:
        return [*lines, "No failing cell: no switch."]
    base = failing_cells(results, default, n_fail)
    for m in candidates:
        mine = failing_cells(results, m, n_fail)
        lines.append(
            f"* `{m}`: {failing_cells(results, m)} failing cells in all, {mine} among the cells "
            f"with n <= {n_fail} against {base} for `{default}`: "
            f"**{'switch' if mine < base else 'no switch'}** if it is the development winner."
        )
    lines.append(
        f"Selection rule applied to this run's data: winner `{select_winner(results, candidates)}`."
    )
    return lines


def render_markdown(config: SmallNConfig, results: list[CellResult]) -> str:
    single = [r for r in results if r.cell.kind == "single"]
    paired = [r for r in results if r.cell.kind == "paired"]
    h0 = [r for r in paired if r.cell.effect == 0.0]
    lines = [
        "## Small-n coverage and test size (`docs/protocol-small-n.md`)\n",
        f"Seed {config.seed}; {config.reps} replications per cell; bootstrap resamples: "
        f"leaderboard interval and bootstrap-t {LEAD_RESAMPLES}, paired {config.resamples}; "
        f"randomisation draws {config.draws}; Dirichlet posterior draws 4000. Coverage carries "
        f"its Wilson 99% interval over replications; **under** = below {BAND_LO} (a failure), "
        f"over = above {BAND_HI} (reported, not a failure), borderline = within "
        f"{BORDERLINE} of a band edge (counted by the point estimate). Width is the mean "
        "interval width.\n",
        "### Single model: coverage of the true accuracy (nominal 0.95)\n",
        *_table(single, SINGLE_METHODS, ["n", "p"]),
        "",
        "### Paired difference: coverage of the true difference (nominal 0.95)\n",
        *_table(paired, PAIRED_METHODS, ["n", "psi", "true diff"]),
        "",
        f"### Paired tests: type-I error at alpha {ALPHA} "
        f"(true difference 0; fail above {TYPE1_MAX})\n",
        "| n | psi | randomisation | sign test |",
        "|---|---|---|---|",
    ]
    for r in h0:
        lines.append(
            f"| {r.cell.n} | {r.cell.rate:g} | {_type1(Rate(r.rand_rejects, r.reps))} "
            f"| {_type1(Rate(r.sign_rejects, r.reps))} |"
        )
    lines += ["", "### Failing cells and decision (protocol rules)\n"]
    lines += [
        f"- single-model `{m}`: {failing_cells(single, m)} of {len(single)}" for m in SINGLE_METHODS
    ]
    lines += [
        f"- paired `{m}`: {failing_cells(paired, m)} of {len(paired)}" for m in PAIRED_METHODS
    ]
    bad_tests = sum(
        Rate(r.rand_rejects, r.reps).value > TYPE1_MAX
        or Rate(r.sign_rejects, r.reps).value > TYPE1_MAX
        for r in h0
    )
    lines += [
        f"- paired tests: {bad_tests} of {len(h0)} type-I cells above {TYPE1_MAX}",
        "",
        *_decision(single, "percentile", SINGLE_CANDIDATES, "1. Single model"),
        "",
        *_decision(paired, "auto", PAIRED_CANDIDATES, "2. Paired interval"),
        "",
        "3. Paired tests: "
        + (
            "all type-I cells pass: no change." if bad_tests == 0 else "failing cells are findings."
        ),
    ]
    return "\n".join(lines) + "\n"
