# Leaderboard CI coverage (`scripts/leaderboard_ci_check.py`)

Protocol: `docs/protocol-leaderboard-ci.md`. Seeds 1, 2, 2000 replications per cell and seed (4000 pooled), 1000 bootstrap resamples, nominal level 95%, 2 worker process(es). Coverage is shown with its Wilson 99% interval; **U** = flagged `undercovers` (interval entirely below 0.95), O = `overcovers` (entirely above 0.96). Width is the mean interval width; `lo=hi` is the share of degenerate intervals.

## Per-task cells (`bootstrap_macro_ci` on one task = the leaderboard interval)

| cell | p | reps | percentile | bootstrap-t | wilson | width percentile | width bootstrap-t | width wilson | lo=hi percentile | lo=hi bootstrap-t |
|---|---|---|---|---|---|---|---|---|---|---|
| task n=10 | 0.5 | 4000 | 0.970 [0.962, 0.976] O | 0.892 [0.879, 0.904] **U** | 0.978 [0.971, 0.983] O | 0.576 | 0.685 | 0.506 | 0.002 | 0.002 |
| task n=10 | 0.7 | 4000 | 0.956 [0.947, 0.964] | 0.844 [0.829, 0.858] **U** | 0.919 [0.907, 0.929] **U** | 0.513 | 0.522 | 0.475 | 0.033 | 0.033 |
| task n=10 | 0.9 | 4000 | 0.647 [0.627, 0.666] **U** | 0.647 [0.627, 0.666] **U** | 0.921 [0.910, 0.932] **U** | 0.253 | 0.150 | 0.370 | 0.351 | 0.351 |
| task n=10 | 0.97 | 4000 | 0.263 [0.245, 0.281] **U** | 0.264 [0.246, 0.282] **U** | 0.957 [0.948, 0.965] | 0.088 | 0.037 | 0.309 | 0.736 | 0.736 |
| task n=35 | 0.5 | 4000 | 0.943 [0.932, 0.951] | 0.962 [0.953, 0.969] | 0.961 [0.952, 0.968] | 0.327 | 0.348 | 0.310 | 0.000 | 0.000 |
| task n=35 | 0.7 | 4000 | 0.933 [0.922, 0.943] **U** | 0.961 [0.953, 0.968] | 0.932 [0.921, 0.942] **U** | 0.293 | 0.322 | 0.286 | 0.000 | 0.000 |
| task n=35 | 0.9 | 4000 | 0.870 [0.855, 0.883] **U** | 0.674 [0.655, 0.693] **U** | 0.931 [0.920, 0.941] **U** | 0.183 | 0.188 | 0.199 | 0.019 | 0.019 |
| task n=35 | 0.97 | 4000 | 0.656 [0.636, 0.675] **U** | 0.278 [0.260, 0.297] **U** | 0.980 [0.974, 0.985] O | 0.077 | 0.046 | 0.137 | 0.344 | 0.344 |
| task n=240 | 0.5 | 4000 | 0.956 [0.947, 0.964] | 0.952 [0.943, 0.960] | 0.956 [0.946, 0.963] | 0.126 | 0.126 | 0.125 | 0.000 | 0.000 |
| task n=240 | 0.7 | 4000 | 0.952 [0.942, 0.960] | 0.949 [0.940, 0.957] | 0.940 [0.929, 0.949] **U** | 0.115 | 0.116 | 0.115 | 0.000 | 0.000 |
| task n=240 | 0.9 | 4000 | 0.957 [0.948, 0.965] | 0.958 [0.949, 0.965] | 0.963 [0.954, 0.970] | 0.075 | 0.078 | 0.076 | 0.000 | 0.000 |
| task n=240 | 0.97 | 4000 | 0.921 [0.909, 0.931] **U** | 0.899 [0.886, 0.910] **U** | 0.943 [0.932, 0.951] | 0.042 | 0.048 | 0.045 | 0.001 | 0.001 |

Flagged cells of 12: percentile 6, bootstrap-t 7, wilson 5.

## Macro cells (tasks sized 35, 35, 10, 35)

| cell | p | reps | percentile | mover-wilson | neff-wilson | strat-bootstrap-t | width percentile | width mover-wilson | width neff-wilson | width strat-bootstrap-t | lo=hi percentile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| macro 35/35/10/35 | 0.5 | 4000 | 0.936 [0.926, 0.946] **U** | 0.939 [0.929, 0.948] **U** | 0.932 [0.921, 0.942] **U** | 0.963 [0.955, 0.970] | 0.202 | 0.186 | 0.200 | 0.222 | 0.000 |
| macro 35/35/10/35 | 0.7 | 4000 | 0.937 [0.927, 0.946] **U** | 0.938 [0.927, 0.947] **U** | 0.934 [0.924, 0.944] **U** | 0.960 [0.952, 0.967] | 0.184 | 0.173 | 0.183 | 0.205 | 0.000 |
| macro 35/35/10/35 | 0.9 | 4000 | 0.912 [0.900, 0.923] **U** | 0.931 [0.920, 0.940] **U** | 0.911 [0.899, 0.922] **U** | 0.936 [0.926, 0.945] **U** | 0.117 | 0.131 | 0.121 | 0.150 | 0.000 |
| macro 35/35/10/35 | 0.97 | 4000 | 0.872 [0.857, 0.885] **U** | 0.920 [0.909, 0.931] **U** | 0.972 [0.965, 0.978] O | 0.703 [0.684, 0.721] **U** | 0.060 | 0.103 | 0.071 | 0.080 | 0.026 |

Flagged cells of 4: percentile 4, mover-wilson 4, neff-wilson 3, strat-bootstrap-t 2.

Macro winner on these data by the protocol's selection rule: `strat-bootstrap-t`.

## Per-seed flagged cells (descriptive)

| seed | task percentile | task bootstrap-t | task wilson | macro percentile | macro mover-wilson | macro neff-wilson | macro strat-bootstrap-t |
|---|---|---|---|---|---|---|---|
| 1 | 6 | 7 | 4 | 2 | 2 | 3 | 2 |
| 2 | 6 | 7 | 4 | 4 | 4 | 3 | 2 |

## Post-hoc (descriptive, not part of any rule)

Coverage across the per-task cells (12): lowest point coverage, cells below 0.90, mean width.

| method | lowest | cells < 0.90 | mean width |
|---|---|---|---|
| percentile | 0.263 | 4 | 0.222 |
| bootstrap-t | 0.264 | 7 | 0.222 |
| wilson | 0.919 | 0 | 0.246 |

Coverage across the macro cells (4): lowest point coverage, cells below 0.90, mean width.

| method | lowest | cells < 0.90 | mean width |
|---|---|---|---|
| percentile | 0.872 | 1 | 0.141 |
| mover-wilson | 0.920 | 0 | 0.148 |
| neff-wilson | 0.911 | 0 | 0.143 |
| strat-bootstrap-t | 0.703 | 1 | 0.164 |

Wilson's point coverage exceeds the percentile interval's in 8 of 12 per-task cells.
