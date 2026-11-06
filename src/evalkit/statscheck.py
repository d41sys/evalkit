"""Monte Carlo validation of the statistics in :mod:`evalkit.aggregate`.

``evalkit stats-check`` simulates paired per-example scores whose true difference is
known, runs the *shipped* functions on them (``paired_comparison``,
``randomization_test_p``, ``sign_test_p``, ``compare_pairs``/``holm_bonferroni``,
``minimum_detectable_effect``, ``required_sample_size``) and compares the empirical
behaviour with what the functions promise.

Decision rules (fixed before any scoring run; the README repeats them). Every rate
carries a Wilson interval at ``MC_LEVEL`` = 99 % over the Monte Carlo replications:

* type-I error at alpha = 0.05: ``anti-conservative`` if the interval lies entirely
  above 0.05 (a failure); ``conservative`` if it lies entirely below 0.04 (valid but
  wastes power); otherwise ``ok``.
* 95 % bootstrap CI coverage of the true difference: ``undercovers`` if the interval
  lies entirely below 0.95 (a failure); ``overcovers`` if entirely above 0.96;
  otherwise ``ok``.
* power at the n the formula computes for 80 % power: ``optimistic`` if the interval
  lies entirely below 0.80 (the formula promises power it does not deliver; a
  failure); ``pessimistic`` if entirely above 0.85; otherwise ``ok``.
* Holm family-wise error rate over m true nulls: ``anti-conservative`` if the interval
  lies entirely above 0.05 (a failure); ``conservative`` if entirely below 0.04;
  otherwise ``ok``.
"""

from __future__ import annotations

import itertools
import math
import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from statistics import NormalDist

import numpy as np

from .aggregate import (
    ASYMMETRIC_METHOD,
    TIE_FALLBACK,
    TIE_GATE,
    compare_pairs,
    mean_test_p,
    minimum_detectable_effect,
    minimum_detectable_effect_binary,
    paired_comparison,
    required_sample_size,
    required_sample_size_binary,
    skewness_warning,
)

ALPHA = 0.05
MC_LEVEL = 0.99
CONSERVATIVE_BELOW = 0.04
OVERCOVER_ABOVE = 0.96
POWER_TARGET = 0.80
POWER_PESSIMISTIC_ABOVE = 0.85
COVERAGE_TARGET = 0.95

KINDS = ("binary", "continuous", "skewed")
SIGMA = 0.25  # SD of the nonzero differences for the continuous kinds
_EPS = 1e-12

DEFAULT_NS = (20, 50, 115, 240)
DEFAULT_TIES = (0.0, 0.5, 0.8)
FIXED_EFFECTS = (0.05, 0.10, 0.20)
FIXED_EFFECT_TIE = 0.6
FWER_KINDS = ("binary", "continuous")
FWER_NS = (50, 115)
FWER_INDEPENDENT_M = (3, 5, 10)
FWER_ALL_PAIRS_K = (3, 4, 5)


# --------------------------------------------------------------------------- rules


def wilson_interval(successes: int, trials: int, level: float = MC_LEVEL) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        return (0.0, 1.0)
    z = NormalDist().inv_cdf(0.5 + level / 2.0)
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denom
    half = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass(frozen=True)
class Rate:
    """A Monte Carlo proportion with its Wilson interval."""

    successes: int
    trials: int

    @property
    def value(self) -> float:
        return self.successes / self.trials if self.trials else math.nan

    @property
    def ci(self) -> tuple[float, float]:
        return wilson_interval(self.successes, self.trials)

    def fmt(self) -> str:
        lo, hi = self.ci
        return f"{self.value:.3f} [{lo:.3f}, {hi:.3f}]"


def classify_error_rate(rate: Rate) -> str:
    """Type-I error or FWER against alpha: ok / conservative / anti-conservative."""
    lo, hi = rate.ci
    if lo > ALPHA:
        return "anti-conservative"
    if hi < CONSERVATIVE_BELOW:
        return "conservative"
    return "ok"


def classify_coverage(rate: Rate) -> str:
    """Coverage of the 95% CI: ok / undercovers / overcovers."""
    lo, hi = rate.ci
    if hi < COVERAGE_TARGET:
        return "undercovers"
    if lo > OVERCOVER_ABOVE:
        return "overcovers"
    return "ok"


def classify_power(rate: Rate) -> str:
    """Empirical power against the formula's 0.80: ok / optimistic / pessimistic."""
    lo, hi = rate.ci
    if hi < POWER_TARGET:
        return "optimistic"
    if lo > POWER_PESSIMISTIC_ABOVE:
        return "pessimistic"
    return "ok"


FAILURES = frozenset({"anti-conservative", "undercovers", "optimistic"})


# ------------------------------------------------------------------- data generation


@dataclass(frozen=True)
class Scenario:
    """Paired scores with a known true mean difference ``effect`` = E[A - B].

    ``tie_rate`` is P(A_i == B_i). Kinds:

    * ``binary``: both 0/1; wins/losses have probabilities (1 - t +/- effect) / 2 and
      tied pairs are both-right or both-wrong with equal probability.
    * ``continuous``: B ~ U(0.25, 0.75); with probability 1 - t, A - B ~ N(mu, SIGMA)
      where mu = effect / (1 - t), otherwise A = B exactly.
    * ``skewed``: as continuous but A - B = mu + SIGMA * (Exp(1) - 1), so the
      differences are right-skewed (under the null: mean zero but asymmetric).
    """

    kind: str
    n: int
    tie_rate: float
    effect: float

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind {self.kind!r}")
        if not 0.0 <= self.tie_rate < 1.0:
            raise ValueError("tie_rate must be in [0, 1)")
        if self.kind == "binary" and abs(self.effect) > 1.0 - self.tie_rate + _EPS:
            raise ValueError("binary |effect| cannot exceed 1 - tie_rate")

    @property
    def true_sd(self) -> float:
        """Exact SD of the per-example difference A - B."""
        t, d = self.tie_rate, self.effect
        if self.kind == "binary":
            return math.sqrt(max(0.0, (1.0 - t) - d * d))
        mu = d / (1.0 - t)
        return math.sqrt(max(0.0, (1.0 - t) * (SIGMA * SIGMA + mu * mu) - d * d))


def simulate_pairs(
    scenario: Scenario, reps: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Draw ``reps`` independent datasets of ``n`` pairs; returns (A, B), each (reps, n)."""
    shape = (reps, scenario.n)
    t, d = scenario.tie_rate, scenario.effect
    if scenario.kind == "binary":
        u = rng.random(shape)
        p_win = (1.0 - t + d) / 2.0
        p_loss = (1.0 - t - d) / 2.0
        both = rng.integers(0, 2, size=shape).astype(np.float64)
        win = u < p_win
        loss = (u >= p_win) & (u < p_win + p_loss)
        a = np.where(win, 1.0, np.where(loss, 0.0, both))
        b = np.where(win, 0.0, np.where(loss, 1.0, both))
        return a, b
    mu = d / (1.0 - t)
    nonzero = rng.random(shape) >= t
    if scenario.kind == "continuous":
        diff = mu + SIGMA * rng.standard_normal(shape)
    else:
        diff = mu + SIGMA * (rng.standard_exponential(shape) - 1.0)
    b = rng.uniform(0.25, 0.75, size=shape)
    a = np.where(nonzero, b + diff, b)
    return a, b


def mde_scenario(kind: str, n: int, tie_rate: float) -> Scenario | None:
    """Scenario whose true effect is the formula's MDE at ``n``.

    Binary: the discordant rate is known (``1 - tie_rate``), so the effect is
    :func:`minimum_detectable_effect_binary` (exact conditional power; the shipped
    formula was a normal approximation, then Connor's 1987, see the README) at that rate. Continuous
    kinds: effect = MDE(sd(effect), n) with the SD depending on the effect, solved in
    closed form as d^2 = c^2 (1 - t) SIGMA^2 / (n - c^2 t / (1 - t)), with
    c = z_{1-a/2} + z_{power}. Returns None when the formula's promise is unattainable
    at this n (no finite effect satisfies it).
    """
    t = tie_rate
    if kind == "binary":
        d = minimum_detectable_effect_binary(1.0 - t, n)
        return Scenario(kind, n, t, d) if math.isfinite(d) else None
    c = minimum_detectable_effect(1.0, 1)
    denom = n - c * c * t / (1.0 - t)
    if denom <= 0:
        return None
    d = math.sqrt(c * c * (1.0 - t) * SIGMA * SIGMA / denom)
    return Scenario(kind, n, t, d)


def n_star(kind: str, tie_rate: float, effect: float) -> int:
    """The formula's n for 80% power at the scenario's true discordant rate / SD and effect.

    Binary scores: :func:`required_sample_size_binary` (exact power search) at
    psi = 1 - tie_rate; the continuous kinds: :func:`required_sample_size` at the true SD.
    """
    if kind == "binary":
        return required_sample_size_binary(1.0 - tie_rate, effect)
    sd = Scenario(kind, 2, tie_rate, effect).true_sd
    return required_sample_size(sd, effect)


# ----------------------------------------------------------------------- cell runners


@dataclass(frozen=True)
class CellJob:
    """One (scenario, reps) cell; ``cell_id`` keys its RNG stream."""

    cell_id: int
    scenario: Scenario
    reps: int
    seed: int
    resamples: int
    draws: int
    group: str  # "h0", "mde" or "fixed"
    ci_method: str = "auto"
    rand_method: str = "auto"
    rand_fallback: str = ASYMMETRIC_METHOD
    rand_tie_fallback: str = TIE_FALLBACK
    rand_tie_gate: float = TIE_GATE


@dataclass(frozen=True)
class CellResult:
    job: CellJob
    rand_reject: Rate
    sign_reject: Rate
    ci_excludes_zero: Rate
    coverage: Rate
    mean_ci_width: float
    predicted_power: float | None  # 0.80 where n was computed by the formula
    skew_warn: Rate  # share of replications where skewness_warning fires


def run_cell(job: CellJob) -> CellResult:
    rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id]))
    a, b = simulate_pairs(job.scenario, job.reps, rng)
    seeds = rng.integers(0, 2**31 - 1, size=job.reps)
    truth = job.scenario.effect
    rand_rej = sign_rej = excl = cov = warned = 0
    width = 0.0
    for i in range(job.reps):
        s = int(seeds[i])
        cmp = paired_comparison(
            a[i].tolist(),
            b[i].tolist(),
            num_resamples=job.resamples,
            seed=s,
            ci_method=job.ci_method,
        )
        p_rand, _ = mean_test_p(
            a[i] - b[i],
            job.rand_method,
            num_draws=job.draws,
            seed=s,
            fallback=job.rand_fallback,
            tie_fallback=job.rand_tie_fallback,
            tie_gate=job.rand_tie_gate,
        )
        rand_rej += p_rand < ALPHA
        sign_rej += cmp.sign_p < ALPHA
        excl += not (cmp.diff_ci_lo <= 0.0 <= cmp.diff_ci_hi)
        cov += cmp.diff_ci_lo - _EPS <= truth <= cmp.diff_ci_hi + _EPS
        width += cmp.diff_ci_hi - cmp.diff_ci_lo
        warned += skewness_warning(a[i] - b[i])[1]
    return CellResult(
        job=job,
        rand_reject=Rate(int(rand_rej), job.reps),
        sign_reject=Rate(int(sign_rej), job.reps),
        ci_excludes_zero=Rate(int(excl), job.reps),
        coverage=Rate(int(cov), job.reps),
        mean_ci_width=width / job.reps,
        predicted_power=POWER_TARGET if job.group != "h0" else None,
        skew_warn=Rate(int(warned), job.reps),
    )


@dataclass(frozen=True)
class FwerJob:
    """``m`` true nulls analysed through ``compare_pairs`` (Holm over the family)."""

    cell_id: int
    kind: str  # "binary" or "continuous"
    design: str  # "independent" (m separate A/B datasets) or "all-pairs" (k models)
    size: int  # m for independent, k models for all-pairs
    n: int
    reps: int
    seed: int
    draws: int
    rand_method: str = "auto"
    rand_fallback: str = ASYMMETRIC_METHOD
    rand_tie_fallback: str = TIE_FALLBACK
    rand_tie_gate: float = TIE_GATE

    @property
    def m(self) -> int:
        return self.size if self.design == "independent" else self.size * (self.size - 1) // 2


@dataclass(frozen=True)
class FwerResult:
    job: FwerJob
    raw_fwer: Rate  # any unadjusted randomisation p < alpha
    holm_fwer: Rate  # any Holm-adjusted p < alpha (any pair "resolved")


def _all_pairs_scores(
    kind: str, k: int, n: int, rng: np.random.Generator
) -> dict[str, dict[object, float]]:
    """k exchangeable models sharing per-example difficulty, so every pair is a true null."""
    q = rng.beta(2.0, 2.0, size=n)
    if kind == "binary":
        s = (rng.random((k, n)) < q).astype(np.float64)
    else:
        s = q + 0.2 * rng.standard_normal((k, n))
    return {f"m{j}": {i: float(s[j, i]) for i in range(n)} for j in range(k)}


def _independent_scores(
    kind: str, m: int, n: int, rng: np.random.Generator
) -> dict[str, dict[object, float]]:
    a, b = simulate_pairs(Scenario(kind, n, 0.5, 0.0), m, rng)
    out: dict[str, dict[object, float]] = {}
    for j in range(m):
        out[f"a{j}"] = {i: float(a[j, i]) for i in range(n)}
        out[f"b{j}"] = {i: float(b[j, i]) for i in range(n)}
    return out


def run_fwer(job: FwerJob) -> FwerResult:
    rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id]))
    raw = holm = 0
    for _ in range(job.reps):
        s = int(rng.integers(0, 2**31 - 1))
        if job.design == "independent":
            scores = _independent_scores(job.kind, job.size, job.n, rng)
            pairs = [(f"a{j}", f"b{j}") for j in range(job.size)]
        else:
            scores = _all_pairs_scores(job.kind, job.size, job.n, rng)
            pairs = list(itertools.combinations(scores, 2))
        res = compare_pairs(
            scores,
            pairs,
            num_resamples=0,
            num_draws=job.draws,
            seed=s,
            with_power=False,
            rand_method=job.rand_method,
            rand_fallback=job.rand_fallback,
            rand_tie_fallback=job.rand_tie_fallback,
            rand_tie_gate=job.rand_tie_gate,
        )
        raw += any(r.rand_p < ALPHA for r in res)
        holm += any(r.resolved for r in res)
    return FwerResult(job, Rate(int(raw), job.reps), Rate(int(holm), job.reps))


# ------------------------------------------------------------------------ orchestration


@dataclass(frozen=True)
class StatsCheckConfig:
    seed: int = 0
    reps_h0: int = 8000
    reps_power: int = 3000
    reps_fwer: int = 3000
    resamples: int = 2000
    draws: int = 2000
    ns: tuple[int, ...] = DEFAULT_NS
    ties: tuple[float, ...] = DEFAULT_TIES
    fwer_ns: tuple[int, ...] = FWER_NS
    fixed_effects: tuple[float, ...] = FIXED_EFFECTS
    workers: int = 1
    ci_method: str = "auto"
    rand_method: str = "auto"
    rand_fallback: str = ASYMMETRIC_METHOD
    rand_tie_fallback: str = TIE_FALLBACK
    rand_tie_gate: float = TIE_GATE


@dataclass(frozen=True)
class SkippedMde:
    kind: str
    n: int
    tie_rate: float


@dataclass(frozen=True)
class StatsCheckReport:
    config: StatsCheckConfig
    h0: list[CellResult]
    h1: list[CellResult]
    skipped: list[SkippedMde]
    fwer: list[FwerResult]


def plan(
    config: StatsCheckConfig,
) -> tuple[list[CellJob], list[CellJob], list[SkippedMde], list[FwerJob]]:
    """The full grid as jobs; ``cell_id`` is the position, so streams are stable."""
    cid = itertools.count()
    h0: list[CellJob] = []
    for kind in KINDS:
        for tie in config.ties:
            for n in config.ns:
                h0.append(
                    CellJob(
                        next(cid),
                        Scenario(kind, n, tie, 0.0),
                        config.reps_h0,
                        config.seed,
                        config.resamples,
                        config.draws,
                        "h0",
                        config.ci_method,
                    )
                )
    h1: list[CellJob] = []
    skipped: list[SkippedMde] = []
    for kind in KINDS:
        for tie in config.ties:
            for n in config.ns:
                base = mde_scenario(kind, n, tie)
                if base is None:
                    skipped.append(SkippedMde(kind, n, tie))
                    continue
                sc = Scenario(kind, n_star(kind, tie, base.effect), tie, base.effect)
                h1.append(
                    CellJob(
                        next(cid),
                        sc,
                        config.reps_power,
                        config.seed,
                        config.resamples,
                        config.draws,
                        "mde",
                        config.ci_method,
                    )
                )
    for kind in KINDS:
        for effect in config.fixed_effects:
            sc = Scenario(kind, n_star(kind, FIXED_EFFECT_TIE, effect), FIXED_EFFECT_TIE, effect)
            h1.append(
                CellJob(
                    next(cid),
                    sc,
                    config.reps_power,
                    config.seed,
                    config.resamples,
                    config.draws,
                    "fixed",
                    config.ci_method,
                )
            )
    fwer: list[FwerJob] = []
    for kind in FWER_KINDS:
        for n in config.fwer_ns:
            for design, sizes in (
                ("independent", FWER_INDEPENDENT_M),
                ("all-pairs", FWER_ALL_PAIRS_K),
            ):
                for size in sizes:
                    fwer.append(
                        FwerJob(
                            next(cid),
                            kind,
                            design,
                            size,
                            n,
                            config.reps_fwer,
                            config.seed,
                            config.draws,
                        )
                    )
    h0 = [
        replace(
            j,
            rand_method=config.rand_method,
            rand_fallback=config.rand_fallback,
            rand_tie_fallback=config.rand_tie_fallback,
            rand_tie_gate=config.rand_tie_gate,
        )
        for j in h0
    ]
    h1 = [
        replace(
            j,
            rand_method=config.rand_method,
            rand_fallback=config.rand_fallback,
            rand_tie_fallback=config.rand_tie_fallback,
            rand_tie_gate=config.rand_tie_gate,
        )
        for j in h1
    ]
    fwer = [
        replace(
            j,
            rand_method=config.rand_method,
            rand_fallback=config.rand_fallback,
            rand_tie_fallback=config.rand_tie_fallback,
            rand_tie_gate=config.rand_tie_gate,
        )
        for j in fwer
    ]
    return h0, h1, skipped, fwer


def _dispatch(job: CellJob | FwerJob) -> CellResult | FwerResult:
    return run_cell(job) if isinstance(job, CellJob) else run_fwer(job)


def run_stats_check(config: StatsCheckConfig) -> StatsCheckReport:
    h0_jobs, h1_jobs, skipped, fwer_jobs = plan(config)
    jobs: list[CellJob | FwerJob] = [*h0_jobs, *h1_jobs, *fwer_jobs]
    # Slowest first so the pool does not end on one long straggler.
    order = sorted(range(len(jobs)), key=lambda i: -_cost(jobs[i]))
    ordered = [jobs[i] for i in order]
    if config.workers > 1:
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            done = list(pool.map(_dispatch, ordered, chunksize=1))
    else:
        done = [_dispatch(j) for j in ordered]
    by_index = dict(zip(order, done, strict=True))
    results = [by_index[i] for i in range(len(jobs))]
    n0, n1 = len(h0_jobs), len(h0_jobs) + len(h1_jobs)
    h0 = [r for r in results[:n0] if isinstance(r, CellResult)]
    h1 = [r for r in results[n0:n1] if isinstance(r, CellResult)]
    fw = [r for r in results[n1:] if isinstance(r, FwerResult)]
    return StatsCheckReport(config, h0, h1, skipped, fw)


def _cost(job: CellJob | FwerJob) -> float:
    if isinstance(job, CellJob):
        return job.reps * job.scenario.n
    return job.reps * job.m * job.n


def default_workers() -> int:
    return max(1, min(8, (os.cpu_count() or 1)))


# ---------------------------------------------------------------------------- report


def _flag(status: str) -> str:
    return "" if status == "ok" else f" **{status}**"


def collect_findings(report: StatsCheckReport) -> list[str]:
    """Every non-ok verdict under the decision rules, one line each (failures first)."""
    fails: list[str] = []
    notes: list[str] = []

    def add(status: str, line: str) -> None:
        if status == "ok":
            return
        (fails if status in FAILURES else notes).append(f"{status}: {line}")

    for r in report.h0:
        s = r.job.scenario
        tag = f"{s.kind} n={s.n} ties={s.tie_rate:g} (H0)"
        add(
            classify_error_rate(r.rand_reject), f"randomisation type-I {tag}: {r.rand_reject.fmt()}"
        )
        add(classify_error_rate(r.sign_reject), f"sign test type-I {tag}: {r.sign_reject.fmt()}")
        add(classify_coverage(r.coverage), f"bootstrap CI coverage {tag}: {r.coverage.fmt()}")
    for r in report.h1:
        s = r.job.scenario
        tag = f"{s.kind} n*={s.n} ties={s.tie_rate:g} effect={s.effect:.3f} ({r.job.group})"
        add(classify_power(r.rand_reject), f"randomisation power {tag}: {r.rand_reject.fmt()}")
        add(classify_coverage(r.coverage), f"bootstrap CI coverage {tag}: {r.coverage.fmt()}")
    for f in report.fwer:
        tag = f"{f.job.kind} {f.job.design} m={f.job.m} n={f.job.n}"
        add(classify_error_rate(f.holm_fwer), f"Holm FWER {tag}: {f.holm_fwer.fmt()}")
    return [*fails, *notes]


def render_markdown(report: StatsCheckReport) -> str:
    cfg = report.config
    lines: list[str] = []
    lines.append(
        f"seed {cfg.seed}; replications: H0 {cfg.reps_h0}, power {cfg.reps_power}, "
        f"FWER {cfg.reps_fwer}; bootstrap resamples {cfg.resamples}; randomisation draws "
        f"{cfg.draws} (exact enumeration up to 20 nonzero differences); CI method "
        f"`{cfg.ci_method}`. Intervals are Wilson {MC_LEVEL:.0%} over replications.\n"
    )
    lines.append(
        f"randomisation-test method `{cfg.rand_method}` (fallback `{cfg.rand_fallback}`; tie "
        f"path `{cfg.rand_tie_fallback}` above a tie share of {cfg.rand_tie_gate:g}).\n"
    )
    lines.append("### Type-I error at alpha = 0.05 (H0: true difference 0)\n")
    lines.append("| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in report.h0:
        s = r.job.scenario
        lines.append(
            f"| {s.kind} | {s.tie_rate:g} | {s.n} "
            f"| {r.rand_reject.fmt()}{_flag(classify_error_rate(r.rand_reject))} "
            f"| {r.sign_reject.fmt()}{_flag(classify_error_rate(r.sign_reject))} "
            f"| {r.ci_excludes_zero.fmt()} | {r.skew_warn.fmt()} |"
        )
    lines.append("\n### Bootstrap CI coverage of the true difference (nominal 0.95)\n")
    lines.append("| group | kind | tie rate | n | effect | coverage | mean CI width |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in [*report.h0, *report.h1]:
        s = r.job.scenario
        lines.append(
            f"| {r.job.group} | {s.kind} | {s.tie_rate:g} | {s.n} | {s.effect:.3f} "
            f"| {r.coverage.fmt()}{_flag(classify_coverage(r.coverage))} "
            f"| {r.mean_ci_width:.3f} |"
        )
    lines.append("\n### Power at the n the formula computes for 80% power\n")
    lines.append(
        "| group | kind | tie rate | true effect | true SD | n* | predicted | "
        "randomisation | sign test | CI excludes 0 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in report.h1:
        s = r.job.scenario
        lines.append(
            f"| {r.job.group} | {s.kind} | {s.tie_rate:g} | {s.effect:.3f} | {s.true_sd:.3f} "
            f"| {s.n} | {POWER_TARGET:.2f} "
            f"| {r.rand_reject.fmt()}{_flag(classify_power(r.rand_reject))} "
            f"| {r.sign_reject.fmt()} | {r.ci_excludes_zero.fmt()} |"
        )
    if report.skipped:
        lines.append(
            "\nMDE cells with no attainable effect (binary: even every discordant pair "
            "favouring one model is not detectable at this n; continuous: the formula's "
            "fixed point does not exist): "
            + "; ".join(f"{k.kind} n={k.n} ties={k.tie_rate:g}" for k in report.skipped)
            + "."
        )
    lines.append("\n### Holm family-wise error rate (all nulls true)\n")
    lines.append("| kind | design | comparisons m | n | unadjusted FWER | Holm FWER |")
    lines.append("|---|---|---|---|---|---|")
    for f in report.fwer:
        lines.append(
            f"| {f.job.kind} | {f.job.design} | {f.job.m} | {f.job.n} "
            f"| {f.raw_fwer.fmt()} "
            f"| {f.holm_fwer.fmt()}{_flag(classify_error_rate(f.holm_fwer))} |"
        )
    findings = collect_findings(report)
    lines.append("\n### Findings under the decision rules\n")
    if findings:
        lines.extend(f"- {f}" for f in findings)
    else:
        lines.append("None: every cell is ok.")
    return "\n".join(lines) + "\n"


def parse_ints(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in text.split(",") if x.strip())


def parse_floats(text: str) -> tuple[float, ...]:
    return tuple(float(x) for x in text.split(",") if x.strip())


def check_args(ns: Sequence[int], ties: Sequence[float]) -> None:
    if any(n < 2 for n in ns):
        raise ValueError("every n must be at least 2")
    if any(not 0.0 <= t < 1.0 for t in ties):
        raise ValueError("every tie rate must be in [0, 1)")
