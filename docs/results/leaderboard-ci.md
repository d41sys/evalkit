# Coverage of the leaderboard confidence interval at small n

Protocol and decision rules: `docs/protocol-leaderboard-ci.md`, committed in `b9fa373` before the harness existed. Harness: `scripts/leaderboard_ci_check.py` (`d23a219`, post-hoc section added in `9693479` before the final run). Development seeds 1 and 2 (`runs/stats-check/leaderboard-ci-dev.md`) selected the macro alternative; the final scoring used fresh seeds 4001, 4002, 4003 (`runs/stats-check/leaderboard-ci.md`):

```bash
uv run --offline python scripts/leaderboard_ci_check.py --seeds 1,2 --out runs/stats-check/leaderboard-ci-dev.md
uv run --offline python scripts/leaderboard_ci_check.py --seeds 4001,4002,4003 --winner strat-bootstrap-t \
  --out runs/stats-check/leaderboard-ci.md        # 43 s wall, 2 workers
```

Bernoulli(p) task scores, nominal 95%, 2000 replications per cell and seed (6000 pooled), 1000 bootstrap resamples. A cell is flagged (**U**) when the Wilson 99% interval of its coverage lies entirely below 0.95. The shipped `percentile` column is `bootstrap_macro_ci` as the leaderboard calls it; `bootstrap-t` is `bootstrap_mean_ci(method="studentized")`; `wilson` is `statscheck.wilson_interval`.

## Pre-registered rule

"Switch the leaderboard's interval for a single task of 0/1 scores to Wilson if `F_pct >= 3` and `F_wil <= 1` (flagged cells of the 12 per-task cells). Macro: switch to the development winner if `G_pct >= 2` and `G_alt <= 1` (flagged cells of the 4 macro cells). Otherwise leave unchanged and document."

## Result: per-task cells (12), coverage of the true accuracy

| n | p | percentile | bootstrap-t | Wilson |
|---|---|---|---|---|
| 10 | 0.5 | 0.972 | 0.894 **U** | 0.980 |
| 10 | 0.7 | 0.960 | 0.840 **U** | 0.925 **U** |
| 10 | 0.9 | 0.650 **U** | 0.650 **U** | 0.931 **U** |
| 10 | 0.97 | 0.262 **U** | 0.262 **U** | 0.963 |
| 35 | 0.5 | 0.939 **U** | 0.958 | 0.957 |
| 35 | 0.7 | 0.942 **U** | 0.969 | 0.939 **U** |
| 35 | 0.9 | 0.864 **U** | 0.670 **U** | 0.917 **U** |
| 35 | 0.97 | 0.654 **U** | 0.278 **U** | 0.980 |
| 240 | 0.5 | 0.958 | 0.956 | 0.956 |
| 240 | 0.7 | 0.955 | 0.954 | 0.946 |
| 240 | 0.9 | 0.958 | 0.959 | 0.962 |
| 240 | 0.97 | 0.922 **U** | 0.903 **U** | 0.945 |

Every rate and its Wilson 99% interval is in `runs/stats-check/leaderboard-ci.md`. Flagged cells of 12: **percentile 7, bootstrap-t 7, Wilson 4**, consistent across the seeds (per seed: percentile 5, 5, 6; Wilson 5, 3, 3).

Intervals that collapse to a point (`lo = hi`) are the main failure: the share of percentile intervals with `lo = hi` is 0.348 at n = 10, p = 0.9, 0.737 at n = 10, p = 0.97 and 0.345 at n = 35, p = 0.97. The bootstrap-t falls back to percentile on such samples and so fails identically there.

## Result: macro mean of tasks (35, 35, 10, 35), coverage of the true accuracy

| p | percentile | mover-wilson | neff-wilson | strat-bootstrap-t |
|---|---|---|---|---|
| 0.5 | 0.943 | 0.945 | 0.938 **U** | 0.967 |
| 0.7 | 0.944 | 0.942 **U** | 0.944 | 0.967 (above 0.96) |
| 0.9 | 0.917 **U** | 0.923 **U** | 0.914 **U** | 0.938 **U** |
| 0.97 | 0.866 **U** | 0.915 **U** | 0.970 (above 0.96) | 0.696 **U** |

Flagged cells of 4: percentile 2, mover-wilson 3, neff-wilson 2, strat-bootstrap-t 2. The development seeds selected **strat-bootstrap-t** (2 flagged cells against 3 to 4 for the others, then the smaller shortfall); that is the candidate scored by the rule. (On the final data `neff-wilson` has the smallest shortfall; that is not the pre-registered selection and is descriptive only.)

## Decision

1. **Per-task: unchanged.** F_pct = 7 >= 3 holds, F_wil = 4 > 1 fails the rule's second condition. The percentile interval stays the leaderboard interval, and its coverage is as above.
2. **Macro: unchanged.** G_pct = 2 >= 2 holds, G_alt = 2 > 1 fails. The percentile macro interval stays.

No code in `src/` changed.

## Predictions vs outcome (written before any run)

1. "The percentile interval is flagged in most n = 10 cells and in the p = 0.9 and 0.97 cells at n = 35; not at n = 240 except possibly p = 0.97": **partly held.** n = 10: flagged only at p = 0.9 and 0.97 (2 of 4; at p = 0.5 it overcovers at 0.972); n = 35: flagged at p = 0.9 and 0.97 as predicted, and also at p = 0.5 and 0.7 (0.939, 0.942, mild); n = 240: only p = 0.97 (0.922).
2. "Wilson is flagged in at most one per-task cell": **failed** (4 cells, and not the predicted p = 0.97 ones: n = 10 at p = 0.7 and 0.9, n = 35 at p = 0.7 and 0.9, coverage 0.917 to 0.939).
3. "Bootstrap-t undercovers at p = 0.9 and 0.97 as well": **held**, and it is worse than percentile at n = 35 for those p and at n = 10 for p = 0.5 and 0.7 (0.894, 0.840).
4. "Rule 1 switches; macro percentile flagged in >= 2 cells": rule 1 **did not switch** (prediction failed); the macro percentile was flagged in 2 cells (held).

## Post-hoc (descriptive; not part of the rule)

* Wilson's coverage oscillates with `n` and `p` (Brown, Cai and DasGupta 2001), so a cell-wise 99% test flags it at 0.917 to 0.939 even though its mean coverage over the 12 cells is 0.950 (mean of the point rates in the table); the "Wilson flagged in <= 1 of 12 cells" condition was not met by Wilson, and was already unmet on the development seeds (5 flagged). The rule was not amended after seeing the development result.
* Lowest point coverage over the 12 per-task cells: percentile 0.262, bootstrap-t 0.262, Wilson 0.917. Cells below 0.90: percentile 4, bootstrap-t 6, Wilson 0. Wilson's coverage exceeds the percentile interval's in 8 of 12 cells (the other four are n = 10 and n = 35 at p = 0.7, and n = 240 at p = 0.5 and 0.7, each lower by at most 0.035). Mean width over the 12 cells: percentile 0.222, Wilson 0.246.
* Macro: lowest point coverage percentile 0.866, mover-wilson 0.915, neff-wilson 0.914, strat-bootstrap-t 0.696. No candidate reaches 0.95 at p = 0.9. The stratified bootstrap-t is the worst at p = 0.97 (0.696; the cause was not diagnosed, the degenerate samples at p = 0.97 are the likely place).
* The rule judges "flagged cells", so it cannot separate a 0.26 coverage from a 0.94 one. Whether the leaderboard should print Wilson for 0/1 tasks anyway is a judgment call the pre-registered rule does not make; the table above is the evidence for it.
* Truth is p for every task, so the macro cells have equal task accuracy; unequal accuracies across tasks were not simulated.
