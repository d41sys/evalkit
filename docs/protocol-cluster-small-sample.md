# Protocol: small-cluster correction for the clustered standard error (CR1 + t critical values)

Committed before any scoring run of the corrected interval. The estimator, grid, seeds, metric and decision rule are fixed here; results are reported whatever they show.

## Question

`docs/results/clustered-se-stats-check.md` (seed 0) shows the clustered normal interval `mean +/- 1.96 * SE_clustered` (Miller 2024) undercovers at few clusters: the mean clustered / naive SE ratio is 0.982 of `sqrt(DEFF)`, and the README noted that a finite-cluster factor `sqrt(C / (C - 1))` "was not tried, because the estimator was frozen by the protocol". Cameron & Miller (2015, "A Practitioner's Guide to Cluster-Robust Inference") recommend the CR1 factor with `t(C - 1)` critical values for few clusters. Does it fix the undercoverage without overcorrecting?

## The estimator

With `C` clusters, `SE_CR1 = sqrt(C / (C - 1)) * SE_clustered` and the interval `mean +/- t(0.975, C - 1) * SE_CR1`. Everything else (SE formula, data, truth) is as in `docs/protocol-clustered-se.md`. The uncorrected interval stays in the harness as a paired control: on every replication both intervals use the same data.

## Reference counts (seed 0 report, `docs/results/clustered-se-stats-check.md`, 72 coverage cells = 2 designs x 2 kinds x 3 ICC x 3 cluster counts x 2 size schemes)

The clustered normal interval is flagged `undercovers` (`classify_coverage`: Wilson 99% upper bound below 0.95) in **32 of 72 cells**: all 24 cells with `C = 20` and 8 of the 48 cells with `C >= 50`. The cluster bootstrap is flagged in 31 (not changed by this protocol). No cell of that report is flagged `overcovers`.

## Grid and seeds

The same 72-cell clustered coverage grid, 2000 replications per cell, 1000 bootstrap resamples, via `uv run --offline evalkit stats-check --only-clustered --seed S --out runs/stats-check/cluster-cr1-seed<S>.md`. Seeds are fresh: seed 1001 is a debug run only (the code runs, columns exist; no choice is made from it) and is not scored; **final seeds 2001, 2002 and 2003**. Seed 0 and seed 1 were used by earlier clustered runs and are not reused.

## Metric and decision rule

For each final seed let `F0` = number of the 72 cells where the uncorrected clustered normal interval is flagged `undercovers`, `F1` = the same for the CR1 interval, `O1` = number of cells where the CR1 interval is flagged `overcovers` (Wilson 99% lower bound above 0.96).

The CR1 correction is **adopted as the default** (clustered SE and clustered normal interval apply it unless switched off) if, on **every** one of the three final seeds:

1. `F1 <= 16` (half of the 32 flagged cells in the seed-0 report) **and** `F1 <= F0 / 2` (a substantial drop on this seed's own paired control), and
2. `O1 = 0` (no cell overcovers beyond its flag rule).

Otherwise it ships **opt-in** (off by default, selectable by a keyword and a CLI flag) and the result is reported as is. Whichever happens, the report gives per seed: `F0`, `F1`, `O1`, the split by `C = 20` vs `C >= 50`, the lowest and highest point coverage of both intervals, and the `C >= 50` and `ICC 0` subsets (descriptive, no pass or fail). Any further breakdown is labelled post-hoc. The cluster bootstrap and the sign-flip tests are not changed.

## Predictions (written before scoring)

1. `F1` is at most 16 on all three seeds: at `C = 20` the factor widens the interval by about 9.5% (`1.026 * 2.093 / 1.96`), which is what the 0.93 point coverage needs.
2. `O1 = 0` is the uncertain part: at ICC 0 and `C = 20` the corrected interval may reach about 0.96.
3. Cells with `C >= 50` change by at most about 0.01 in coverage (factor 1.036 at `C = 50`, 1.012 at `C = 100`).

## What changes in the code, by outcome

* `clustered_se(values, codes, small_sample=...)`, a new `clustered_normal_ci(values, codes, confidence_level, small_sample=...)` and a numpy-only `t_critical(df, confidence_level)`; `cluster_stats` passes the switch through; the harness reports the corrected and uncorrected clustered normal interval side by side.
* Adopted: the default of `small_sample` is `True` everywhere (including the clustered SE printed by `compare`), with `small_sample=False` giving Miller's SE exactly.
* Opt-in: the default stays `False`; `compare` gets a flag to switch the correction on for the printed clustered SE.
