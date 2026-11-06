"""Development-seed diagnosis and selection of the tie path (``docs/protocol-ties.md``).

    uv run --offline python scripts/ties_dev.py --seeds 1,2 --out runs/stats-check/ties-dev.md

Replays the exact data stream of ``evalkit stats-check`` (same ``SeedSequence([seed, cell_id])``,
same scenarios and draws) at the development seeds, but computes only the randomisation p-values,
so the five candidate tie paths and both ``tau`` values are scored on the same data as the
baseline (``none``: the Phase M behaviour). Writes: the diagnosis table (type-I by number of
non-tied pairs ``k``), the configuration table (eligibility and the selection rule) and the
36 H0 cells. Binary power cells are not simulated: the asymmetry gate cannot fire on 0/1 scores
(equal ``|d|``), so every configuration equals the baseline there by construction (the final
``stats-check`` runs verify it); they count as zero power loss.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from evalkit.aggregate import (
    TIE_METHODS,
    asymmetry_gate,
    bootstrap_t_test_p,
    mean_test_p,
    randomization_test_p,
    tie_share,
)
from evalkit.statscheck import ALPHA, SIGMA, CellJob, StatsCheckConfig, plan, simulate_pairs

TAUS = (0.5, 0.7)
BAND = 0.06
MAX_POWER_LOSS = 0.03
MAX_CONT_WORSEN = 0.01
K_BINS = ((0, 9), (10, 19), (20, 29), (30, 49), (50, 10**9))
TIE_PREFERENCE = ("signflip", "signtest", "johnson_nz", "boott_nz", "boott_nz_cal")
DIAG_TESTS = ("signflip", "boott", *TIE_METHODS[1:])

Config = tuple[str, float]  # (path, tau); ("none", 0.0) is the baseline
BASELINE: Config = ("none", 0.0)
CONFIGS: list[Config] = [BASELINE, *[(c, t) for c in TIE_PREFERENCE for t in TAUS]]


@dataclass
class Scan:
    cell_id: int
    seed: int
    fired: np.ndarray  # asymmetry gate fired
    share: np.ndarray  # share of zero differences
    p_base: np.ndarray  # Phase M p-value (auto, tie path none)
    p_cand: dict[str, np.ndarray]  # NaN unless fired and share > min(TAUS)
    diag: dict[str, np.ndarray] | None  # k, per-test p, tie-free boott p


def scan_cell(args: tuple[CellJob, bool]) -> Scan:
    job, diag = args
    rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id]))
    a, b = simulate_pairs(job.scenario, job.reps, rng)
    seeds = rng.integers(0, 2**31 - 1, size=job.reps)
    reps = job.reps
    fired = np.zeros(reps, dtype=bool)
    share = np.zeros(reps)
    p_base = np.zeros(reps)
    p_cand = {c: np.full(reps, np.nan) for c in TIE_PREFERENCE}
    dg: dict[str, np.ndarray] | None = None
    if diag:
        dg = {name: np.full(reps, np.nan) for name in ("k", "tiefree", *DIAG_TESTS)}
    free_rng = np.random.default_rng(np.random.SeedSequence([job.seed, job.cell_id, 7]))
    for i in range(reps):
        s = int(seeds[i])
        d = a[i] - b[i]
        p_base[i] = mean_test_p(d, "auto", num_draws=job.draws, seed=s)[0]
        fired[i] = asymmetry_gate(d)[2]
        share[i] = tie_share(d)
        if fired[i] and share[i] > min(TAUS):
            for c in TIE_PREFERENCE:
                p_cand[c][i] = mean_test_p(d, c, num_draws=job.draws, seed=s)[0]
        if dg is not None:
            k = int(np.count_nonzero(np.abs(d) > 1e-12))
            dg["k"][i] = k
            if k >= 3:
                dg["signflip"][i] = randomization_test_p(d, num_draws=job.draws, seed=s)
                dg["boott"][i] = bootstrap_t_test_p(d, num_draws=job.draws, seed=s)
                for c in TIE_METHODS[1:]:
                    dg[c][i] = mean_test_p(d, c, num_draws=job.draws, seed=s)[0]
                free = SIGMA * (free_rng.standard_exponential(k) - 1.0)
                dg["tiefree"][i] = bootstrap_t_test_p(free, num_draws=job.draws, seed=s)
    return Scan(job.cell_id, job.seed, fired, share, p_base, p_cand, dg)


def reject(scan: Scan, config: Config) -> np.ndarray:
    base = scan.p_base < ALPHA
    path, tau = config
    if path == "none":
        return base
    use = scan.fired & (scan.share > tau)
    return np.where(use, scan.p_cand[path] < ALPHA, base)


def rate(scans: list[Scan], config: Config) -> float:
    return float(np.mean([reject(s, config).mean() for s in scans]))


def label(job: CellJob) -> str:
    s = job.scenario
    return f"{job.group} {s.kind} t={s.tie_rate:g} n={s.n}"


def diagnosis(scans_by_cell: dict[int, list[Scan]], jobs: dict[int, CellJob]) -> list[str]:
    lines = [
        "### Diagnosis: type-I by number of non-tied pairs k (skewed, tie rate 0.8, development "
        "seeds pooled)\n",
        "`boott` is the Phase M test on all differences; `boott_nz` and the other `_nz` tests "
        "use only the k non-tied ones; `tie-free boott` is `boott` on a tie-free skewed sample "
        "of the same k.\n",
        "| n | k | reps | signflip | boott | tie-free boott | "
        + " | ".join(TIE_METHODS[1:])
        + " |",
        "|---|---|---|---|---|---|" + "---|" * len(TIE_METHODS[1:]),
    ]
    for cid, job in sorted(jobs.items(), key=lambda kv: kv[1].scenario.n):
        s = job.scenario
        if not (job.group == "h0" and s.kind == "skewed" and s.tie_rate == 0.8):
            continue
        scans = scans_by_cell[cid]
        k = np.concatenate([x.diag["k"] for x in scans if x.diag])
        cols = {
            name: np.concatenate([x.diag[name] for x in scans if x.diag])
            for name in ("tiefree", *DIAG_TESTS)
        }
        for lo, hi in K_BINS:
            sel = (k >= max(lo, 3)) & (k <= hi)
            if sel.sum() < 100:
                continue
            tag = f"{lo}-{hi}" if hi < 10**9 else f">={lo}"
            cells = [
                f"{np.mean(cols[name][sel] < ALPHA):.3f}"
                for name in ("signflip", "boott", "tiefree", *TIE_METHODS[1:])
            ]
            lines.append(f"| {s.n} | {tag} | {int(sel.sum())} | " + " | ".join(cells) + " |")
    return lines


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--reps-h0", type=int, default=4000)
    ap.add_argument("--reps-power", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    seeds = [int(x) for x in args.seeds.split(",")]

    work: list[tuple[CellJob, bool]] = []
    jobs: dict[int, CellJob] = {}
    for seed in seeds:
        sc_cfg = StatsCheckConfig(seed=seed, reps_h0=args.reps_h0, reps_power=args.reps_power)
        h0, h1, _, _ = plan(sc_cfg)
        for j in [*h0, *h1]:
            jobs[j.cell_id] = j
            if j.group != "h0" and j.scenario.kind == "binary":
                continue
            diag = j.group == "h0" and j.scenario.kind == "skewed" and j.scenario.tie_rate == 0.8
            work.append((j, diag))
    work.sort(key=lambda w: -(w[0].reps * w[0].scenario.n))
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        done = list(pool.map(scan_cell, work, chunksize=1))
    by_cell: dict[int, list[Scan]] = {}
    for sc in done:
        by_cell.setdefault(sc.cell_id, []).append(sc)

    h0_ids = sorted(c for c, j in jobs.items() if j.group == "h0")
    h1_ids = sorted(c for c, j in jobs.items() if j.group != "h0")
    n_power = len(h1_ids)
    out: list[str] = [
        f"development seeds {seeds}; replications H0 {args.reps_h0} per seed and cell, power "
        f"{args.reps_power}; randomisation draws 2000. Rates are means over the seeds.\n"
    ]
    out += diagnosis(by_cell, jobs)

    rows = []
    for cfg in CONFIGS:
        h0_rates = {c: rate(by_cell[c], cfg) for c in h0_ids}
        base_rates = {c: rate(by_cell[c], BASELINE) for c in h0_ids}
        above = sum(r > BAND for r in h0_rates.values())
        excess = sum(max(0.0, r - ALPHA) for r in h0_rates.values())
        worsen = max(
            (h0_rates[c] - base_rates[c] for c in h0_ids if jobs[c].scenario.kind == "continuous"),
            default=0.0,
        )
        binary_same = all(
            h0_rates[c] == base_rates[c] for c in h0_ids if jobs[c].scenario.kind == "binary"
        )
        loss = (
            sum(rate(by_cell[c], BASELINE) - rate(by_cell[c], cfg) for c in h1_ids if c in by_cell)
            / n_power
        )
        eligible = binary_same and worsen <= MAX_CONT_WORSEN and loss <= MAX_POWER_LOSS
        rows.append((cfg, above, excess, worsen, loss, binary_same, eligible))

    out += [
        "\n### Configurations (selection rule of `docs/protocol-ties.md`)\n",
        f"H0 cells above {BAND} (of {len(h0_ids)}), excess = sum of max(0, rate - 0.05), worst "
        f"continuous H0 worsening vs none, mean power loss over {n_power} power cells (binary "
        "cells counted as 0).\n",
        "| path | tau | H0 cells > 0.06 | excess | worst continuous worsening | "
        "mean power loss | binary identical | eligible |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cfg, above, excess, worsen, loss, same, ok in rows:
        out.append(
            f"| {cfg[0]} | {cfg[1] if cfg[0] != 'none' else '-'} | {above} | {excess:.4f} | "
            f"{worsen:+.4f} | {loss:+.4f} | {same} | {ok} |"
        )
    eligible_rows = [r for r in rows if r[0] != BASELINE and r[6]]
    base_above = rows[0][1]
    order = {c: i for i, c in enumerate(TIE_PREFERENCE)}
    eligible_rows.sort(key=lambda r: (r[1], r[2], r[4], order[r[0][0]], -r[0][1]))
    out.append("")
    if eligible_rows and eligible_rows[0][1] <= base_above:
        w = eligible_rows[0][0]
        out.append(
            f"**Winner: path `{w[0]}`, tau {w[1]}** (H0 cells > 0.06: {eligible_rows[0][1]} "
            f"vs {base_above} for none)."
        )
    else:
        out.append(
            "**No winner** (no eligible configuration, or the best one has more H0 cells above "
            "0.06 than none): the final run scores `boott_nz` at tau 0.5 as pre-registered."
        )

    out += [
        "\n### H0 cells, mean rate over the seeds\n",
        "| cell | none | " + " | ".join(f"{c} {t:g}" for c, t in CONFIGS[1:]) + " |",
        "|---|---|" + "---|" * (len(CONFIGS) - 1),
    ]
    for c in h0_ids:
        out.append(
            f"| {label(jobs[c])} | "
            + " | ".join(f"{rate(by_cell[c], cfg):.4f}" for cfg in CONFIGS)
            + " |"
        )
    out += [
        "\n### Power cells, mean rate over the seeds (binary cells not simulated)\n",
        "| cell | n* | none | " + " | ".join(f"{c} {t:g}" for c, t in CONFIGS[1:]) + " |",
        "|---|---|---|" + "---|" * (len(CONFIGS) - 1),
    ]
    for c in h1_ids:
        if c not in by_cell:
            continue
        s = jobs[c].scenario
        out.append(
            f"| {jobs[c].group} {s.kind} t={s.tie_rate:g} d={s.effect:.3f} | {s.n} | "
            + " | ".join(f"{rate(by_cell[c], cfg):.4f}" for cfg in CONFIGS)
            + " |"
        )
    text = "\n".join(out) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
