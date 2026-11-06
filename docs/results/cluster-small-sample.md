# Small-cluster correction for the clustered SE (CR1 + t critical values)

Protocol and decision rule: `docs/protocol-cluster-small-sample.md`, committed in `82407bb` before any scoring run. Estimator: `mean +/- t(0.975, C - 1) * sqrt(C / (C - 1)) * SE_clustered`, compared with the uncorrected `mean +/- 1.96 * SE_clustered` on the same replications. Grid: the 72 clustered coverage cells of `docs/protocol-clustered-se.md` (2 designs x 2 kinds x ICC 0, 0.1, 0.3 x 20, 50, 100 clusters x equal, unequal sizes), 2000 replications per cell, 1000 bootstrap resamples, fresh seeds 2001, 2002, 2003 (seed 0 and seed 1 were used before and are not reused). Reports: `runs/stats-check/cluster-cr1-seed<S>.md`, produced by

```bash
uv run --offline evalkit stats-check --only-clustered --seed <S> --out runs/stats-check/cluster-cr1-seed<S>.md
```

(seeds 2001 to 2003, run one after another; each report's wall time was about 80 s on 8 workers; the results do not depend on the worker count). A flag is `undercovers` / `overcovers` by the existing Wilson 99% rule (`classify_coverage`).

## Pre-registered rule

"On every one of the three final seeds: (1) F1 <= 16 (half of the 32 flagged cells in the seed-0 report) and F1 <= F0 / 2, and (2) O1 = 0." Adopt as default if met on all three; otherwise opt-in. F0 / F1 = cells flagged `undercovers` for the uncorrected / corrected interval, O1 = cells flagged `overcovers` for the corrected one.

## Result

| seed | F0 (uncorrected) | F1 (CR1) | O1 | C = 20: flagged, uncorrected -> CR1 (of 24) | C >= 50: flagged (of 48) | ICC 0: flagged (of 24) | rule |
|---|---|---|---|---|---|---|---|
| 2001 | 29 | 1 | 0 | 23 -> 1 | 6 -> 0 | 10 -> 0 | met |
| 2002 | 34 | 2 | 0 | 21 -> 1 | 13 -> 1 | 10 -> 1 | met |
| 2003 | 29 | 1 | 0 | 23 -> 1 | 6 -> 0 | 9 -> 0 | met |

Point coverage over the 72 cells (descriptive): uncorrected 0.908 to 0.959 (2001), 0.911 to 0.950 (2002), 0.912 to 0.956 (2003); CR1 0.931 to 0.964, 0.934 to 0.962, 0.934 to 0.959. The cells still flagged under CR1: binary mean, ICC 0.3, 20 clusters, unequal sizes on all three seeds (0.931, 0.934, 0.934) and continuous mean, ICC 0, 50 clusters, unequal sizes on seed 2002 (0.935). Each corrected interval is wider than the uncorrected one on every replication, so the correction can only raise coverage; per-cell gains (post-hoc, point coverage, 72 cells x 3 seeds): 0.013 to 0.029 at 20 clusters and 0.001 to 0.014 at 50 or 100 clusters.

**Decision: adopted as the default.** The rule is met on all three seeds with large margins (F1 of 1 to 2 against a limit of 14 to 16: the smaller of 16 and half of F0), and no cell overcovers.

## Predictions vs outcome

1. "`F1` is at most 16 on all three seeds": **held** (1, 2, 1).
2. "`O1 = 0` is the uncertain part": **held**, O1 = 0 on all three seeds; the highest corrected point coverage is 0.964 (a cell at 50 or 100 clusters, seed 2001), whose Wilson interval still includes 0.96.
3. "Cells with `C >= 50` change by at most about 0.01 in coverage": **held roughly**: per-cell gains 0.001 to 0.014, so the largest (0.014, seed 2001) is above "about 0.01".

## What the check also shows (descriptive, post-hoc)

* The uncorrected interval is flagged more often on these fresh seeds at 50 or more clusters (6, 13, 6 of 48) than in the seed-0 report (8 of 48 for the clustered normal, 0 of 16 at ICC 0 and 50 or more clusters; on the fresh seeds 2, 3, 2 of those 16 are flagged). With 72 cells per seed and a 99% interval, a few flags per seed are within what Monte Carlo noise produces, so the seed-0 control of "0 of 16" was somewhat lucky. This is a caution about the flag counts, not about the correction.
* The correction does not touch the cluster bootstrap (flagged in 17 to 20 of the 24 cells with 20 clusters on these seeds) or the sign-flip tests; those are unchanged.
* Limits: simple generators (clusters of about 5, equal ICC, 20 or more clusters); the SE is still Miller's two-term estimator with a global `C / (C - 1)` factor, not a leave-one-cluster-out (CR3) estimate; with fewer than 20 clusters the t quantile and factor matter more and were not simulated.
