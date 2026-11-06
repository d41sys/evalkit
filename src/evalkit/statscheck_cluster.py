"""Monte Carlo check of the clustered statistics (``evalkit stats-check --clustered``).

Protocol, grid and decision rules: ``docs/protocol-clustered-se.md`` (committed before the
first scoring run). Items come in clusters with a known intra-cluster correlation (ICC 0, 0.1,
0.3). For each cell the check runs the *shipped* functions and measures

* coverage of the true value by four 95% intervals: the naive normal interval
  (``mean +/- 1.96 s / sqrt(n)``), the item bootstrap that ``compare`` used before clusters
  (``bootstrap_mean_ci`` / ``paired_comparison``), the clustered-SE normal interval
  (``clustered_normal_ci``, Miller 2024), the same with the CR1 small-cluster correction
  (``sqrt(C / (C - 1))`` and ``t(C - 1)``; ``docs/protocol-cluster-small-sample.md``) and the
  cluster bootstrap (``cluster_bootstrap_ci`` / ``paired_comparison(clusters=...)``);
* in the paired design (true difference 0) the type-I error of the item-level sign-flip test
  and of the cluster sign-flip test;
* power at the sample size the design-effect formula returns.

Rates carry the Wilson 99% intervals and verdicts of :mod:`evalkit.statscheck`.
"""

from __future__ import annotations

import itertools
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

from .aggregate import (
    bootstrap_mean_ci,
    cluster_randomization_test_p,
    paired_comparison,
    randomization_test_p,
    required_sample_size,
)
from .clustered import (
    cluster_bootstrap_ci,
    clustered_normal_ci,
    clustered_se,
    design_effect,
    estimate_icc,
    naive_se,
)
from .statscheck import (
    ALPHA,
    FAILURES,
    Rate,
    classify_coverage,
    classify_error_rate,
    classify_power,
)

Z95 = NormalDist().inv_cdf(0.975)
_EPS = 1e-12
CLUSTER_SIZE = 5
UNEQUAL_M_EFF = 29.0 / 5.0
"""``E m^2 / E m`` for ``m = 1 + Poisson(4)``: the effective cluster size of the unequal cells."""
BINDING_MIN_CLUSTERS = 50
"""Cells with fewer clusters are reported, not binding (protocol, claim 2)."""
CLAIM_SHARE = 0.9
APPROX_COVERAGE = 0.93
POWER_EFFECT = 0.10
POWER_SD = 0.25
DEFAULT_ICCS = (0.0, 0.1, 0.3)
DEFAULT_COUNTS = (20, 50, 100)
DESIGNS = ("mean", "paired")
KINDS = ("binary", "continuous")
SIZES = ("equal", "unequal")
ESTIMATORS = (
    "naive",
    "item_bootstrap",
    "cluster_normal",
    "cluster_normal_cr1",
    "cluster_bootstrap",
)
CR1_GRID_CELLS = 72
"""Cells of the pre-registered grid (``docs/protocol-cluster-small-sample.md``)."""
CR1_MAX_FLAGGED = 16
"""Half of the 32 flagged cells of the seed-0 clustered report: the adoption threshold."""


# ------------------------------------------------------------------ data generation


@dataclass(frozen=True)
class ClusterScenario:
    """One data-generating process; see the protocol for the formulas.

    ``design`` ``mean``: one model's scores, truth is the population mean. ``paired``: scores
    of A and B on the same items, analysed through ``d = A - B``, truth 0.
    """

    design: str
    kind: str
    icc: float
    clusters: int
    sizes: str

    def __post_init__(self) -> None:
        if self.design not in DESIGNS or self.kind not in KINDS or self.sizes not in SIZES:
            raise ValueError(f"unknown scenario {self}")
        if not 0.0 <= self.icc < 1.0:
            raise ValueError("icc must be in [0, 1)")
        if self.clusters < 2:
            raise ValueError("need at least two clusters")

    @property
    def truth(self) -> float:
        if self.design == "paired":
            return 0.0
        return 0.6 if self.kind == "binary" else 0.5

    @property
    def m_eff(self) -> float:
        return float(CLUSTER_SIZE) if self.sizes == "equal" else UNEQUAL_M_EFF

    @property
    def theory_ratio(self) -> float:
        """``sqrt(DEFF)``: the clustered / naive SE ratio the design predicts."""
        return math.sqrt(design_effect(self.m_eff, self.icc))


def draw_clustered(
    sc: ClusterScenario, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One dataset: ``(a, b, codes)``. The analysed score is ``a - b`` (``b`` is 0 for ``mean``)."""
    c = sc.clusters
    sizes = np.full(c, CLUSTER_SIZE) if sc.sizes == "equal" else 1 + rng.poisson(4, size=c)
    codes = np.repeat(np.arange(c), sizes)
    n = codes.size
    rho = sc.icc
    if sc.kind == "continuous":
        z = rng.standard_normal(c)
        e = rng.standard_normal(n)
        d = 0.25 * (math.sqrt(rho) * z[codes] + math.sqrt(1.0 - rho) * e)
        if sc.design == "mean":
            return d + 0.5, np.zeros(n), codes
        return d, np.zeros(n), codes
    if sc.design == "mean":
        mu = 0.6
        if rho > 0.0:
            k = 1.0 / rho - 1.0
            p = rng.beta(mu * k, (1.0 - mu) * k, size=c)
        else:
            p = np.full(c, mu)
        return (rng.random(n) < p[codes]).astype(np.float64), np.zeros(n), codes
    w = math.sqrt(3.0 * rho / (8.0 - 4.0 * rho))
    s = rng.uniform(-w, w, size=c)
    a = (rng.random(n) < 0.5 + s[codes]).astype(np.float64)
    b = (rng.random(n) < 0.5 - s[codes]).astype(np.float64)
    return a, b, codes


# ------------------------------------------------------------------ cell runners


@dataclass(frozen=True)
class ClusterJob:
    cell_id: int
    scenario: ClusterScenario
    reps: int
    seed: int
    resamples: int
    draws: int


@dataclass(frozen=True)
class ClusterCellResult:
    job: ClusterJob
    coverage: dict[str, Rate]  # by estimator id
    se_ratio: float  # mean clustered SE / naive SE
    icc_hat: float  # mean one-way ANOVA estimate
    p_item: Rate | None  # item sign-flip rejection rate (paired design, H0)
    p_cluster: Rate | None  # cluster sign-flip rejection rate


def run_cluster_cell(job: ClusterJob) -> ClusterCellResult:
    sc = job.scenario
    rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id]))
    seeds = rng.integers(0, 2**31 - 1, size=job.reps)
    hits = dict.fromkeys(ESTIMATORS, 0)
    rej_item = rej_cluster = 0
    ratio = icc = 0.0
    for i in range(job.reps):
        s = int(seeds[i])
        a, b, codes = draw_clustered(sc, rng)
        d = a - b
        mean = float(d.mean())
        nse, cse = naive_se(d), clustered_se(d, codes, small_sample=False)
        _, n_lo, n_hi = clustered_normal_ci(d, codes, small_sample=False)
        _, c_lo, c_hi = clustered_normal_ci(d, codes, small_sample=True)
        ratio += cse / nse if nse > 0.0 else 1.0
        icc += estimate_icc(d, codes)
        ivs: dict[str, tuple[float, float]] = {
            "naive": (mean - Z95 * nse, mean + Z95 * nse),
            "cluster_normal": (n_lo, n_hi),
            "cluster_normal_cr1": (c_lo, c_hi),
        }
        if sc.design == "mean":
            _, lo, hi = bootstrap_mean_ci(d.tolist(), num_resamples=job.resamples, seed=s)
            ivs["item_bootstrap"] = (lo, hi)
            _, lo, hi = cluster_bootstrap_ci(d, codes, num_resamples=job.resamples, seed=s)
            ivs["cluster_bootstrap"] = (lo, hi)
        else:
            plain = paired_comparison(a.tolist(), b.tolist(), num_resamples=job.resamples, seed=s)
            ivs["item_bootstrap"] = (plain.diff_ci_lo, plain.diff_ci_hi)
            clus = paired_comparison(
                a.tolist(), b.tolist(), num_resamples=job.resamples, seed=s, clusters=codes.tolist()
            )
            ivs["cluster_bootstrap"] = (clus.diff_ci_lo, clus.diff_ci_hi)
            rej_item += randomization_test_p(d, num_draws=job.draws, seed=s) < ALPHA
            rej_cluster += (
                cluster_randomization_test_p(d, codes.tolist(), num_draws=job.draws, seed=s) < ALPHA
            )
        for name, (lo, hi) in ivs.items():
            hits[name] += lo - _EPS <= sc.truth <= hi + _EPS
    paired = sc.design == "paired"
    return ClusterCellResult(
        job=job,
        coverage={k: Rate(int(v), job.reps) for k, v in hits.items()},
        se_ratio=ratio / job.reps,
        icc_hat=icc / job.reps,
        p_item=Rate(int(rej_item), job.reps) if paired else None,
        p_cluster=Rate(int(rej_cluster), job.reps) if paired else None,
    )


@dataclass(frozen=True)
class ClusterPowerJob:
    """Paired continuous scores, clusters of 5, true effect 0.10, SD of ``d`` 0.25."""

    cell_id: int
    icc: float
    rule: str  # "deff": n from the design-effect formula; "naive": n ignoring clustering
    reps: int
    seed: int
    resamples: int
    draws: int

    @property
    def deff(self) -> float:
        return design_effect(CLUSTER_SIZE, self.icc)

    @property
    def n_items(self) -> int:
        """Items: the formula's n rounded up to whole clusters of 5."""
        n = required_sample_size(
            POWER_SD, POWER_EFFECT, deff=self.deff if self.rule == "deff" else 1.0
        )
        return CLUSTER_SIZE * math.ceil(n / CLUSTER_SIZE)


@dataclass(frozen=True)
class ClusterPowerResult:
    job: ClusterPowerJob
    cluster_flip: Rate
    cluster_ci_excludes_zero: Rate


def run_cluster_power(job: ClusterPowerJob) -> ClusterPowerResult:
    rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id]))
    seeds = rng.integers(0, 2**31 - 1, size=job.reps)
    c = job.n_items // CLUSTER_SIZE
    codes = np.repeat(np.arange(c), CLUSTER_SIZE)
    rho = job.icc
    flip = excl = 0
    zeros = np.zeros(codes.size)
    for i in range(job.reps):
        s = int(seeds[i])
        z = rng.standard_normal(c)
        e = rng.standard_normal(codes.size)
        d = POWER_EFFECT + POWER_SD * (math.sqrt(rho) * z[codes] + math.sqrt(1.0 - rho) * e)
        flip += cluster_randomization_test_p(d, codes.tolist(), num_draws=job.draws, seed=s) < ALPHA
        cmp = paired_comparison(
            d.tolist(), zeros.tolist(), num_resamples=job.resamples, seed=s, clusters=codes.tolist()
        )
        excl += not (cmp.diff_ci_lo <= 0.0 <= cmp.diff_ci_hi)
    return ClusterPowerResult(job, Rate(int(flip), job.reps), Rate(int(excl), job.reps))


# ------------------------------------------------------------------ orchestration


@dataclass(frozen=True)
class ClusterCheckConfig:
    seed: int = 0
    reps: int = 2000
    power_reps: int = 2000
    resamples: int = 1000
    draws: int = 2000
    iccs: tuple[float, ...] = DEFAULT_ICCS
    counts: tuple[int, ...] = DEFAULT_COUNTS
    workers: int = 1


@dataclass(frozen=True)
class ClusterCheckReport:
    config: ClusterCheckConfig
    cells: list[ClusterCellResult]
    power: list[ClusterPowerResult]


def plan_cluster(config: ClusterCheckConfig) -> tuple[list[ClusterJob], list[ClusterPowerJob]]:
    """The grid as jobs; ``cell_id`` is the position, so random streams are stable."""
    cid = itertools.count()
    cells = [
        ClusterJob(
            next(cid),
            ClusterScenario(design, kind, icc, c, sizes),
            config.reps,
            config.seed,
            config.resamples,
            config.draws,
        )
        for design in DESIGNS
        for kind in KINDS
        for icc in config.iccs
        for c in config.counts
        for sizes in SIZES
    ]
    power = [
        ClusterPowerJob(
            next(cid),
            icc,
            rule,
            config.power_reps,
            config.seed,
            config.resamples,
            config.draws,
        )
        for icc in config.iccs
        for rule in ("deff", "naive")
    ]
    return cells, power


def _dispatch(job: ClusterJob | ClusterPowerJob) -> ClusterCellResult | ClusterPowerResult:
    return run_cluster_cell(job) if isinstance(job, ClusterJob) else run_cluster_power(job)


def _cost(job: ClusterJob | ClusterPowerJob) -> float:
    if isinstance(job, ClusterJob):
        return job.reps * job.scenario.clusters * (1 + job.scenario.clusters / 100.0)
    return job.reps * job.n_items


def run_cluster_check(config: ClusterCheckConfig) -> ClusterCheckReport:
    cells, power = plan_cluster(config)
    jobs: list[ClusterJob | ClusterPowerJob] = [*cells, *power]
    order = sorted(range(len(jobs)), key=lambda i: -_cost(jobs[i]))  # slowest first
    ordered = [jobs[i] for i in order]
    if config.workers > 1:
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            done = list(pool.map(_dispatch, ordered, chunksize=1))
    else:
        done = [_dispatch(j) for j in ordered]
    by_index = dict(zip(order, done, strict=True))
    results = [by_index[i] for i in range(len(jobs))]
    return ClusterCheckReport(
        config,
        [r for r in results if isinstance(r, ClusterCellResult)],
        [r for r in results if isinstance(r, ClusterPowerResult)],
    )


# ------------------------------------------------------------------ verdicts and report


def _flagged(r: ClusterCellResult, estimator: str) -> bool:
    return classify_coverage(r.coverage[estimator]) == "undercovers"


def evaluate_claims(report: ClusterCheckReport) -> list[str]:
    """The four claims of the protocol, one line each, plus the control and the SE ratio."""
    cells = report.cells
    lines: list[str] = []

    pos = [r for r in cells if r.job.scenario.icc > 0.0]
    if pos:
        counts = {e: sum(_flagged(r, e) for r in pos) for e in ("naive", "item_bootstrap")}
        ok = all(v >= CLAIM_SHARE * len(pos) for v in counts.values())
        lines.append(
            f"Claim 1 (naive undercovers), {'supported' if ok else 'not supported'}: the naive "
            f"normal interval is flagged `undercovers` in {counts['naive']} of {len(pos)} cells "
            f"with ICC > 0, the item bootstrap in {counts['item_bootstrap']} (rule: at least "
            f"{CLAIM_SHARE:.0%} of cells for both)."
        )

    binding = [r for r in cells if r.job.scenario.clusters >= BINDING_MIN_CLUSTERS]
    for est, label in (
        ("cluster_normal", "clustered-SE normal"),
        ("cluster_bootstrap", "cluster bootstrap"),
    ):
        if not binding:
            break
        bad = [r for r in binding if _flagged(r, est)]
        if not bad:
            verdict = "supported"
        elif all(r.coverage[est].value >= APPROX_COVERAGE for r in bad):
            verdict = "approximately supported"
        else:
            verdict = "not supported"
        worst = min((r.coverage[est].value for r in binding), default=math.nan)
        lines.append(
            f"Claim 2 (clustered is calibrated), {label}: {verdict}. Flagged `undercovers` in "
            f"{len(bad)} of {len(binding)} cells with at least {BINDING_MIN_CLUSTERS} clusters "
            f"(lowest point coverage {worst:.3f})."
        )
        small = [r for r in cells if r.job.scenario.clusters < BINDING_MIN_CLUSTERS]
        if small:
            lines.append(
                f"  Not binding, fewer than {BINDING_MIN_CLUSTERS} clusters: {label} flagged in "
                f"{sum(_flagged(r, est) for r in small)} of {len(small)} cells (lowest point "
                f"coverage {min(r.coverage[est].value for r in small):.3f})."
            )
        control = [r for r in binding if r.job.scenario.icc == 0.0]
        if control:
            lines.append(
                f"  Control (ICC 0, at least {BINDING_MIN_CLUSTERS} clusters): {label} flagged in "
                f"{sum(_flagged(r, est) for r in control)} of {len(control)} cells."
            )

    paired = [r for r in cells if r.p_item is not None and r.p_cluster is not None]
    paired_pos = [r for r in paired if r.job.scenario.icc > 0.0]
    if paired_pos:
        anti = sum(
            classify_error_rate(r.p_item) == "anti-conservative"
            for r in paired_pos
            if r.p_item is not None
        )
        lines.append(
            f"Claim 3a (item sign-flip is anti-conservative under clustering), "
            f"{'supported' if anti >= CLAIM_SHARE * len(paired_pos) else 'not supported'}: "
            f"flagged in {anti} of {len(paired_pos)} paired cells with ICC > 0."
        )
    if paired:
        bad_c = [
            r
            for r in paired
            if r.p_cluster is not None and classify_error_rate(r.p_cluster) == "anti-conservative"
        ]
        verdict = "supported" if not bad_c else "not supported"
        lines.append(
            f"Claim 3b (cluster sign-flip is valid), {verdict}: "
            f"anti-conservative in {len(bad_c)} of {len(paired)} paired cells."
        )

    for p in report.power:
        if p.job.rule != "deff":
            continue
        verdict = classify_power(p.cluster_flip)
        lines.append(
            f"Claim 4 (power at the design-effect n), ICC {p.job.icc:g}, n = {p.job.n_items} "
            f"items ({p.job.n_items // CLUSTER_SIZE} clusters): cluster sign-flip power "
            f"{p.cluster_flip.fmt()}, {verdict}."
        )

    finite = [r for r in cells if r.job.scenario.theory_ratio > 0.0]
    if finite:
        rel = [r.se_ratio / r.job.scenario.theory_ratio for r in finite]
        lines.append(
            "SE ratio (descriptive): mean clustered/naive SE over sqrt(DEFF) is "
            f"{np.mean(rel):.3f} (range {min(rel):.3f} to {max(rel):.3f}) over {len(finite)} cells."
        )
    return lines


def evaluate_small_sample(report: ClusterCheckReport) -> list[str]:
    """The decision-rule quantities of ``docs/protocol-cluster-small-sample.md`` for one run."""
    cells = report.cells
    if not cells:
        return []
    f0 = sum(_flagged(r, "cluster_normal") for r in cells)
    f1 = sum(_flagged(r, "cluster_normal_cr1") for r in cells)
    o1 = sum(classify_coverage(r.coverage["cluster_normal_cr1"]) == "overcovers" for r in cells)
    lines = [
        f"CR1 small-cluster correction: flagged `undercovers` in {f1} of {len(cells)} cells "
        f"against {f0} for the uncorrected clustered normal interval on the same replications; "
        f"flagged `overcovers` in {o1}."
    ]
    for label, subset in (
        (f"fewer than {BINDING_MIN_CLUSTERS} clusters", [r for r in cells if _few(r)]),
        (f"at least {BINDING_MIN_CLUSTERS} clusters", [r for r in cells if not _few(r)]),
        ("ICC 0", [r for r in cells if r.job.scenario.icc == 0.0]),
    ):
        if not subset:
            continue
        cr1 = [r.coverage["cluster_normal_cr1"].value for r in subset]
        plain = [r.coverage["cluster_normal"].value for r in subset]
        lines.append(
            f"  {label} ({len(subset)} cells): flagged "
            f"{sum(_flagged(r, 'cluster_normal_cr1') for r in subset)} corrected vs "
            f"{sum(_flagged(r, 'cluster_normal') for r in subset)} uncorrected; point coverage "
            f"{min(cr1):.3f} to {max(cr1):.3f} corrected, {min(plain):.3f} to {max(plain):.3f} "
            "uncorrected."
        )
    if len(cells) == CR1_GRID_CELLS:
        ok = f1 <= CR1_MAX_FLAGGED and 2 * f1 <= f0 and o1 == 0
        lines.append(
            f"Rule for this seed (F1 <= {CR1_MAX_FLAGGED}, F1 <= F0 / 2, no `overcovers`): "
            f"{'met' if ok else 'not met'} (F0 = {f0}, F1 = {f1}, O1 = {o1}). Adoption needs "
            "'met' on all three final seeds."
        )
    else:
        lines.append(
            f"The grid has {len(cells)} cells, not the pre-registered {CR1_GRID_CELLS}: counts "
            "only, no verdict against the rule."
        )
    return lines


def _few(r: ClusterCellResult) -> bool:
    return r.job.scenario.clusters < BINDING_MIN_CLUSTERS


def collect_cluster_findings(report: ClusterCheckReport) -> list[str]:
    """Every non-ok coverage / error-rate / power verdict, failures first."""
    fails: list[str] = []
    notes: list[str] = []

    def add(status: str, line: str) -> None:
        if status != "ok":
            (fails if status in FAILURES else notes).append(f"{status}: {line}")

    for r in report.cells:
        sc = r.job.scenario
        tag = f"{sc.design} {sc.kind} ICC={sc.icc:g} C={sc.clusters} {sc.sizes}"
        for est in ESTIMATORS:
            add(
                classify_coverage(r.coverage[est]), f"{est} coverage {tag}: {r.coverage[est].fmt()}"
            )
        if r.p_item is not None and r.p_cluster is not None:
            add(classify_error_rate(r.p_item), f"item sign-flip type-I {tag}: {r.p_item.fmt()}")
            add(
                classify_error_rate(r.p_cluster),
                f"cluster sign-flip type-I {tag}: {r.p_cluster.fmt()}",
            )
    for p in report.power:
        add(
            classify_power(p.cluster_flip),
            f"cluster sign-flip power ICC={p.job.icc:g} n={p.job.n_items} ({p.job.rule}): "
            f"{p.cluster_flip.fmt()}",
        )
    return [*fails, *notes]


def _flag(status: str) -> str:
    return "" if status == "ok" else f" **{status}**"


def render_cluster_markdown(report: ClusterCheckReport) -> str:
    cfg = report.config
    lines = [
        "## Clustered data (protocol: `docs/protocol-clustered-se.md`)\n",
        f"seed {cfg.seed}; replications {cfg.reps} per coverage cell, {cfg.power_reps} per power "
        f"cell; bootstrap resamples {cfg.resamples}; randomisation draws {cfg.draws} (exact "
        "enumeration up to 20 nonzero differences or clusters). Intervals are Wilson 99% over "
        "replications. Estimators: naive = mean +/- 1.96 s/sqrt(n); item bootstrap = the CI "
        "`compare` printed before clusters; clustered normal = mean +/- 1.96 SE_clustered "
        "(Miller 2024); clustered normal CR1 = mean +/- t(C - 1) sqrt(C / (C - 1)) SE_clustered "
        "(`docs/protocol-cluster-small-sample.md`); cluster bootstrap = percentile interval "
        "from resampling clusters. "
        "ICC^ is the mean ANOVA estimate; SE ratio is mean clustered/naive SE next to "
        "sqrt(DEFF) of the design.\n",
    ]
    for design in DESIGNS:
        rows = [r for r in report.cells if r.job.scenario.design == design]
        if not rows:
            continue
        what = (
            "mean of one model's scores"
            if design == "mean"
            else "paired difference A - B (truth 0)"
        )
        lines.append(f"### Coverage of the true value, design `{design}` ({what}), nominal 0.95\n")
        lines.append(
            "| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal "
            "| clustered normal CR1 | cluster bootstrap | SE ratio | sqrt(DEFF) |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            sc = r.job.scenario
            cov = "".join(
                f" {r.coverage[e].fmt()}{_flag(classify_coverage(r.coverage[e]))} |"
                for e in ESTIMATORS
            )
            lines.append(
                f"| {sc.kind} | {sc.icc:g} | {r.icc_hat:.2f} | {sc.clusters} | {sc.sizes} |{cov} "
                f"{r.se_ratio:.2f} | {sc.theory_ratio:.2f} |"
            )
        lines.append("")
    paired = [r for r in report.cells if r.p_item is not None and r.p_cluster is not None]
    if paired:
        lines.append("### Type-I error at alpha = 0.05, paired design (true difference 0)\n")
        lines.append("| kind | ICC | clusters | sizes | item sign-flip | cluster sign-flip |")
        lines.append("|---|---|---|---|---|---|")
        for r in paired:
            if r.p_item is None or r.p_cluster is None:
                continue
            sc = r.job.scenario
            lines.append(
                f"| {sc.kind} | {sc.icc:g} | {sc.clusters} | {sc.sizes} "
                f"| {r.p_item.fmt()}{_flag(classify_error_rate(r.p_item))} "
                f"| {r.p_cluster.fmt()}{_flag(classify_error_rate(r.p_cluster))} |"
            )
        lines.append("")
    if report.power:
        lines.append(
            f"### Power with the design effect (paired continuous, clusters of {CLUSTER_SIZE}, "
            f"effect {POWER_EFFECT}, SD {POWER_SD})\n"
        )
        lines.append(
            "| ICC | n rule | DEFF | items | clusters | predicted | cluster sign-flip | "
            "cluster CI excludes 0 |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for p in report.power:
            j = p.job
            flag = _flag(classify_power(p.cluster_flip)) if j.rule == "deff" else ""
            pred = "0.80" if j.rule == "deff" else "-"
            lines.append(
                f"| {j.icc:g} | {'DEFF-inflated' if j.rule == 'deff' else 'naive (no DEFF)'} "
                f"| {j.deff:.2f} | {j.n_items} | {j.n_items // CLUSTER_SIZE} | {pred} "
                f"| {p.cluster_flip.fmt()}{flag} | {p.cluster_ci_excludes_zero.fmt()} |"
            )
        lines.append("")
    lines.append("### Claims under the pre-registered rules\n")
    lines.extend(f"- {c}" for c in evaluate_claims(report))
    lines.append("\n### Small-cluster correction (`docs/protocol-cluster-small-sample.md`)\n")
    lines.extend(f"- {c}" for c in evaluate_small_sample(report))
    findings = collect_cluster_findings(report)
    lines.append("\n### Every flagged cell\n")
    if findings:
        lines.extend(f"- {f}" for f in findings)
    else:
        lines.append("None: every cell is ok.")
    return "\n".join(lines) + "\n"
