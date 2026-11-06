# Protocol: coverage of the leaderboard confidence interval at small n

Committed before any scoring run, and before the harness (`scripts/leaderboard_ci_check.py`) exists. Grid, methods, seeds, replication counts, selection rule and decision rules are fixed here; results are reported against them whatever they show.

## Problem

`evalkit stats-check` checks only paired intervals (`compare`). The interval printed in the leaderboard's "95% CI" column is `bootstrap_macro_ci` (`src/evalkit/aggregate.py`): a **percentile** bootstrap of the macro mean, resampling items within each task. For a model run on one task it is the plain percentile bootstrap of that task's mean; the "Per-Task Breakdown" table prints task means without an interval, so the per-task interval is the leaderboard interval of a one-task run. Percentile intervals are known to be too narrow at small n (Hesterberg 2015) and degenerate (`[1, 1]`) when every score is equal, which is likely at 0/1 scores with high accuracy and small n (at n = 10 and accuracy 0.97, all ten correct has probability 0.74). Their coverage on the leaderboard path is unchecked. `wilson_interval` exists only in `statscheck.py` (used for the Monte Carlo rates), not as a leaderboard interval.

## Data and truth

Binary tasks. A task of size `n` and true accuracy `p` has `k ~ Binomial(n, p)` correct, i.e. `n` i.i.d. Bernoulli(p) scores. Nominal level 95%. Truth for a single task is `p`; for the macro mean of several tasks each with accuracy `p` it is `p`.

Grid (16 cells, `p` in {0.5, 0.7, 0.9, 0.97}):

* **per-task cells (12):** `n` in {10, 35, 240}. 35 and 10 are task sizes in the bundled demo suite; 240 is the GSM8K subset.
* **macro cells (4):** four tasks of sizes (35, 35, 10, 35), equal weights (macro mean = unweighted mean of the four task means).

## Methods

Per-task cells (all at level 0.95, 1000 resamples where resampling is used, a fresh bootstrap seed per replication):

* `percentile`: the shipped `bootstrap_macro_ci` called with that single task. This is what the leaderboard prints.
* `bootstrap-t`: the shipped `bootstrap_mean_ci(..., method="studentized")` (falls back to percentile where the sample has no spread).
* `wilson`: `statscheck.wilson_interval(k, n, level=0.95)`.

Macro cells:

* `percentile`: the shipped `bootstrap_macro_ci` over the four tasks (stratified item bootstrap). Baseline.
* `mover-wilson`: Newcombe / Zou-Donner square-and-add of per-task Wilson intervals for the weighted sum `m = sum w_i p_i`, `w_i = 1/4`: `lo = m - sqrt(sum w_i^2 (p_i - l_i)^2)`, `hi = m + sqrt(sum w_i^2 (u_i - p_i)^2)`, with `(l_i, u_i)` the 95% Wilson interval of task `i`.
* `neff-wilson`: Wilson interval of the macro mean treated as a proportion on an effective sample size `n_eff = m (1 - m) / v`, `v = sum w_i^2 p_i (1 - p_i) / n_i` (the plug-in variance of the macro mean); if `v = 0`, `n_eff = 1 / sum(w_i^2 / n_i)`.
* `strat-bootstrap-t`: stratified bootstrap-t: resample each task, `t* = (m* - m) / se*` with `se*^2 = sum w_i^2 s*_i^2 / n_i` (`ddof = 1`), interval `[m - q_{0.975}(t*) se, m - q_{0.025}(t*) se]` with the original `se`, resamples with `se* = 0` dropped; percentile interval where `se = 0` or fewer than half of the resamples remain; endpoints clipped to `[0, 1]`.

## Decision rules for coverage (every rate carries a Wilson 99% interval over the replications)

* **flagged (`undercovers`):** the Wilson 99% interval of the cell's coverage lies entirely below 0.95 (`statscheck.classify_coverage`). `overcovers` (entirely above 0.96) is reported but not part of any switching rule.
* Coverage counts a replication when `lo - 1e-9 <= truth <= hi + 1e-9`. An interval with `lo = hi` can cover only if the truth equals it.

## Development selection of the macro alternative (seeds 1 and 2 only, 2000 replications per cell and seed, the 4 macro cells pooled over both seeds)

Among `mover-wilson`, `neff-wilson`, `strat-bootstrap-t`, the **macro winner** is the candidate with the fewest macro cells flagged on the development data; ties: the smaller `sum over the 4 cells of max(0, 0.95 - coverage)`; then the order `mover-wilson`, `neff-wilson`, `strat-bootstrap-t`. The development run also prints the per-task cells for orientation. Nothing about the per-task methods is selected: they are fixed above.

## Final scoring

Fresh seeds **4001, 4002, 4003** (none was used by an earlier run in this repository; seeds 1 and 2 are the development seeds), 2000 replications per cell and seed, so 6000 pooled per cell; one cell's data stream is `SeedSequence([seed, cell_id])`. Coverage, flags and widths are computed on the pooled replications of the three seeds. Mean width is descriptive.

### Decision rules (fixed here)

1. **Per-task interval (12 cells).** Let `F_pct` and `F_wil` be the numbers of the 12 per-task cells flagged for `percentile` and `wilson`. **Switch** the leaderboard's interval for a single task of 0/1 scores (without cluster labels) to Wilson if `F_pct >= 3` and `F_wil <= 1`. Otherwise leave the percentile interval unchanged and document its coverage.
2. **Macro interval (4 cells).** Let `G_pct` and `G_alt` be the numbers of the 4 macro cells flagged for `percentile` and for the macro winner. **Switch** the leaderboard's macro interval for tasks of 0/1 scores (without cluster labels) to the winner if `G_pct >= 2` and `G_alt <= 1`. Otherwise leave it unchanged and document its coverage.
3. Where a rule says "switch", tasks with non-binary scores or cluster labels keep the bootstrap, because Wilson and its macro versions assume independent Bernoulli scores. Where a rule says "unchanged", no code changes beyond the harness, the result document and the README.

"No detectable effect" is the wording for any comparison whose interval contains the null. Any analysis beyond the above (other breakdowns, bootstrap-t versus Wilson, BCa, widths by cell) is labelled post-hoc.

## Predictions (written before any run)

1. The percentile interval is flagged in most n = 10 cells and in the p = 0.9 and 0.97 cells at n = 35 (degenerate `[1, 1]` and `[0, 0]` intervals plus the `sqrt((n-1)/n)` narrowness); it is not flagged at n = 240 except possibly p = 0.97.
2. Wilson is flagged in at most one per-task cell, most likely n = 10, p = 0.97 or n = 35, p = 0.97 where its coverage oscillates with `n`.
3. Bootstrap-t falls back to percentile on every degenerate sample, so it undercovers at p = 0.9 and 0.97 as well.
4. Per-task rule 1 switches. The macro percentile interval is flagged in 2 or more of the 4 macro cells (the n = 10 task and p >= 0.9).

## What changes in the code, by outcome

* Switch (rule 1 and / or 2): `wilson_interval` moves to `aggregate.py` (statscheck imports it from there), `bootstrap_macro_ci` takes the Wilson-based path for binary, label-free tasks, the leaderboard note says so, a test covers the new path, and the README gets the result.
* Unchanged: harness, results file and README only.
