# Leaderboard CI coverage (`scripts/leaderboard_ci_check.py`)

Protocol: `docs/protocol-leaderboard-ci.md`. Seeds 4001, 4002, 4003, 2000 replications per cell and seed (6000 pooled), 1000 bootstrap resamples, nominal level 95%, 2 worker process(es). Coverage is shown with its Wilson 99% interval; **U** = flagged `undercovers` (interval entirely below 0.95), O = `overcovers` (entirely above 0.96). Width is the mean interval width; `lo=hi` is the share of degenerate intervals.

## Per-task cells (`bootstrap_macro_ci` on one task = the leaderboard interval)

| cell | p | reps | percentile | bootstrap-t | wilson | width percentile | width bootstrap-t | width wilson | lo=hi percentile | lo=hi bootstrap-t |
|---|---|---|---|---|---|---|---|---|---|---|
| task n=10 | 0.5 | 6000 | 0.972 [0.966, 0.977] O | 0.894 [0.883, 0.903] **U** | 0.980 [0.974, 0.984] O | 0.576 | 0.687 | 0.507 | 0.003 | 0.003 |
| task n=10 | 0.7 | 6000 | 0.960 [0.953, 0.966] | 0.840 [0.827, 0.852] **U** | 0.925 [0.916, 0.934] **U** | 0.512 | 0.520 | 0.475 | 0.030 | 0.030 |
| task n=10 | 0.9 | 6000 | 0.650 [0.634, 0.666] **U** | 0.650 [0.634, 0.666] **U** | 0.931 [0.922, 0.939] **U** | 0.254 | 0.148 | 0.370 | 0.348 | 0.348 |
| task n=10 | 0.97 | 6000 | 0.262 [0.247, 0.277] **U** | 0.262 [0.247, 0.277] **U** | 0.963 [0.957, 0.969] | 0.086 | 0.036 | 0.309 | 0.737 | 0.737 |
| task n=35 | 0.5 | 6000 | 0.939 [0.930, 0.946] **U** | 0.958 [0.951, 0.964] | 0.957 [0.950, 0.963] | 0.326 | 0.347 | 0.310 | 0.000 | 0.000 |
| task n=35 | 0.7 | 6000 | 0.942 [0.934, 0.950] **U** | 0.969 [0.962, 0.974] O | 0.939 [0.931, 0.946] **U** | 0.294 | 0.322 | 0.286 | 0.000 | 0.000 |
| task n=35 | 0.9 | 6000 | 0.864 [0.852, 0.875] **U** | 0.670 [0.655, 0.686] **U** | 0.917 [0.907, 0.926] **U** | 0.182 | 0.187 | 0.199 | 0.027 | 0.027 |
| task n=35 | 0.97 | 6000 | 0.654 [0.638, 0.669] **U** | 0.278 [0.263, 0.293] **U** | 0.980 [0.975, 0.984] O | 0.077 | 0.046 | 0.137 | 0.345 | 0.345 |
| task n=240 | 0.5 | 6000 | 0.958 [0.950, 0.964] | 0.956 [0.948, 0.962] | 0.956 [0.949, 0.963] | 0.126 | 0.126 | 0.125 | 0.000 | 0.000 |
| task n=240 | 0.7 | 6000 | 0.955 [0.948, 0.962] | 0.954 [0.947, 0.960] | 0.946 [0.938, 0.953] | 0.115 | 0.116 | 0.115 | 0.000 | 0.000 |
| task n=240 | 0.9 | 6000 | 0.958 [0.950, 0.964] | 0.959 [0.952, 0.965] | 0.962 [0.955, 0.968] | 0.075 | 0.078 | 0.076 | 0.000 | 0.000 |
| task n=240 | 0.97 | 6000 | 0.922 [0.913, 0.931] **U** | 0.903 [0.893, 0.912] **U** | 0.945 [0.937, 0.952] | 0.042 | 0.048 | 0.045 | 0.001 | 0.001 |

Flagged cells of 12: percentile 7, bootstrap-t 7, wilson 4.

## Macro cells (tasks sized 35, 35, 10, 35)

| cell | p | reps | percentile | mover-wilson | neff-wilson | strat-bootstrap-t | width percentile | width mover-wilson | width neff-wilson | width strat-bootstrap-t | lo=hi percentile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| macro 35/35/10/35 | 0.5 | 6000 | 0.943 [0.935, 0.950] | 0.945 [0.937, 0.952] | 0.938 [0.929, 0.945] **U** | 0.967 [0.960, 0.972] | 0.203 | 0.186 | 0.200 | 0.222 | 0.000 |
| macro 35/35/10/35 | 0.7 | 6000 | 0.944 [0.936, 0.951] | 0.942 [0.934, 0.949] **U** | 0.944 [0.935, 0.951] | 0.967 [0.961, 0.973] O | 0.185 | 0.174 | 0.183 | 0.206 | 0.000 |
| macro 35/35/10/35 | 0.9 | 6000 | 0.917 [0.908, 0.926] **U** | 0.923 [0.914, 0.931] **U** | 0.914 [0.904, 0.923] **U** | 0.938 [0.929, 0.946] **U** | 0.117 | 0.131 | 0.120 | 0.149 | 0.000 |
| macro 35/35/10/35 | 0.97 | 6000 | 0.866 [0.854, 0.877] **U** | 0.915 [0.905, 0.924] **U** | 0.970 [0.964, 0.975] O | 0.696 [0.680, 0.711] **U** | 0.059 | 0.102 | 0.070 | 0.079 | 0.033 |

Flagged cells of 4: percentile 2, mover-wilson 3, neff-wilson 2, strat-bootstrap-t 2.

Macro winner on these data by the protocol's selection rule: `neff-wilson`.

## Per-seed flagged cells (descriptive)

| seed | task percentile | task bootstrap-t | task wilson | macro percentile | macro mover-wilson | macro neff-wilson | macro strat-bootstrap-t |
|---|---|---|---|---|---|---|---|
| 4001 | 5 | 7 | 5 | 2 | 2 | 1 | 2 |
| 4002 | 5 | 7 | 3 | 2 | 2 | 2 | 2 |
| 4003 | 6 | 7 | 3 | 2 | 2 | 1 | 1 |

## Decision rules (protocol)

1. Per-task: F_pct = 7, F_wil = 4. Switch if F_pct >= 3 and F_wil <= 1: **unchanged**.
2. Macro (winner `strat-bootstrap-t`): G_pct = 2, G_alt = 2. Switch if G_pct >= 2 and G_alt <= 1: **unchanged**.

## Post-hoc (descriptive, not part of any rule)

Coverage across the per-task cells (12): lowest point coverage, cells below 0.90, mean width.

| method | lowest | cells < 0.90 | mean width |
|---|---|---|---|
| percentile | 0.262 | 4 | 0.222 |
| bootstrap-t | 0.262 | 6 | 0.222 |
| wilson | 0.917 | 0 | 0.246 |

Coverage across the macro cells (4): lowest point coverage, cells below 0.90, mean width.

| method | lowest | cells < 0.90 | mean width |
|---|---|---|---|
| percentile | 0.866 | 1 | 0.141 |
| mover-wilson | 0.915 | 0 | 0.148 |
| neff-wilson | 0.914 | 0 | 0.143 |
| strat-bootstrap-t | 0.696 | 1 | 0.164 |

Wilson's point coverage exceeds the percentile interval's in 8 of 12 per-task cells.
