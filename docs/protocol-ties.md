# Protocol: holding size when most paired differences tie (Phase N)

Committed before any candidate is scored, on development or final seeds. Candidates, gate, development selection rule, final decision rule, replication counts and predictions below are fixed. Results are reported against the rule whatever they show, negative results included.

## Problem (from `docs/protocol-skew-fix.md` and README "Round 3", no new run)

After Round 3, `mean_test_p` (`method="auto"`) switches from the sign-flip test to the bootstrap-t test of the mean (`boott`) when the asymmetry gate fires (`k < 25 g_nz^2` on the `k` nonzero differences). On the skewed generator (H0: mean 0, `Exp(1) - 1` shape on the nonzero differences) the high-tie cells are still anti-conservative at seed 0 (`runs/stats-check/report-skewfix.md`, nominal 0.05, 99% Wilson):

| tie rate | n | type-I |
|---|---|---|
| 0.5 | 50 | 0.074 [0.067, 0.082] |
| 0.8 | 50 | 0.074 [0.067, 0.082] |
| 0.8 | 115 | 0.075 [0.068, 0.083] |
| 0.8 | 240 | 0.058 [0.052, 0.065] |

Also above 0.06 at seed 0 and **outside the scope of any tie-specific path**: skewed tie 0 n = 20 (0.062) and skewed tie 0.5 n = 20 (0.084).

## Diagnosis questions (answered from development seeds only, by `scripts/ties_dev.py`)

Under H0 the mean of all `n` differences is `P(nonzero) * E[d | nonzero]`, so H0 is equivalent to "the mean of the nonzero differences is 0". Zeros carry no information about it; only the `k` nonzero differences do, and `k ~ Bin(n, 1 - t)` is about 23 at (t = 0.8, n = 115). Hypotheses:

* **H-a (effective sample size).** The failure is the small-`k` skewness error of the studentised mean (relative error `O(k^-1)`, as in the tie-free cells at n = 20), not something specific to ties. Prediction: the rejection rate of `boott` conditional on `k` matches the tie-free rate at `n = k`.
* **H-b (zero resampling).** Resampling the zeros adds noise (the resampled `k*` varies, the zero-inflated population has heavy kurtosis) on top of H-a. Prediction: `boott` on the nonzero differences only (`boott_nz`) is closer to 0.05 than `boott` on all `n` differences at the same `(t, n)`.

Reported diagnosis table: type-I of `signflip`, `boott` (all differences), `boott_nz` and each other candidate at tie rate 0.8, skewed, n in {50, 115, 240}, split by `k` in {<10, 10-19, 20-29, 30-49, >=50}, pooled over the two development seeds, next to the tie-free rate of the same test at the same `k`.

## Candidate tie paths (two-sided, alpha 0.05, H0: mean of the per-example differences is 0)

All except `none` use only the non-tied pairs (`|d| > 1e-12`), `k` of them. With `k < 2` they use `signflip`.

* `none`: Phase M behaviour (the asymmetry fallback `boott` on all differences). Baseline.
* `signflip`: the exact sign-flip randomisation test on the non-tied differences (zeros never changed it, so this is the existing test; exact for `k <= 20`, else 2000 Monte Carlo draws). Control: its exchangeability null is "each difference symmetric around 0".
* `signtest`: exact conditional two-sided sign test on the non-tied pairs (`sign_test_p(wins, losses)`). Control: it tests the median, so it is expected to reject mean-zero skewed data.
* `boott_nz`: bootstrap-t test of the mean (`bootstrap_t_test_p`) on the non-tied differences, 2000 draws.
* `johnson_nz`: Johnson (1978) skewness-corrected t (`johnson_test_p`) on the non-tied differences.
* `boott_nz_cal`: double (calibrated, prepivoted) bootstrap-t on the non-tied differences (Beran 1987; Efron & Tibshirani 1993, ch. 18). `t*` from `B1` resamples of the mean-centred differences; for each outer resample `b`, `B2` inner resamples (from the outer sample, re-centred) give `p*_b = (1 + #{|t**| >= |t*_b|}) / (B2 + 1)`; `p_obs` is the single-bootstrap p; `p = (1 + #{p*_b <= p_obs}) / (B1 + 1)`. `B1 = B2 = min(draws, 399)`.

**Path rule (`auto`).** `signflip` unless the asymmetry gate fires (unchanged, so binary cells and symmetric differences are unchanged by construction); when it fires: the tie path if the share of exactly-zero differences is **> tau**, else `boott` on all differences as in Phase M. `tau` in {0.5, 0.7}. The two values bracket the grid's tie rates (0, 0.5, 0.8): `tau = 0.5` also catches about half of the tie-0.5 replications, `tau = 0.7` leaves the tie-0.5 cells on `boott`. No other value is tried.

## Development selection (seeds 1 and 2 only; never the final seed)

Replications per seed: H0 4000 per cell, power 2000 per cell, same grid, scenario generator, cell ids, randomisation draws (2000) and decision constants as `evalkit stats-check`. The p-values are computed by `scripts/ties_dev.py`, which replays the exact data stream of `stats-check` (same `SeedSequence([seed, cell_id])`) so every candidate sees the same data as the baseline and as a later `stats-check` run at that seed. For a configuration `(path, tau)`, the rate of a cell is the mean of its two seed rates.

**Eligible** iff (all measured on development data):

1. binary H0 cells identical to `none` (guaranteed by the gate; verified), and
2. no continuous H0 cell more than 0.01 above its `none` rate, and
3. mean power loss over the 42 power cells (the `mde` and `fixed` cells of `stats-check`, `none` minus the configuration, signed mean) <= 0.03.

**Winner** among eligible: the fewest H0 cells (of 36) with rate > 0.06; ties: the smaller `sum max(0, rate - 0.05)` over the 36 cells; then the smaller mean power loss; then the order `signflip`, `signtest`, `johnson_nz`, `boott_nz`, `boott_nz_cal`; then `tau = 0.7`. If no configuration is eligible, or the winner has more H0 cells above 0.06 than `none` on the development seeds, there is no winner and the final run still scores `boott_nz` at `tau = 0.5` (the most direct fix) so the outcome is reported, then not adopted.

## Final run (fresh seed 101, never used before; 10 000 replications)

```bash
uv run --offline evalkit stats-check --seed 101 --reps-h0 10000 --reps-power 10000 --rand-tie-fallback none \
    --out runs/stats-check/ties-before-seed101.md
uv run --offline evalkit stats-check --seed 101 --reps-h0 10000 --reps-power 10000 --rand-tie-fallback <winner> \
    --out runs/stats-check/ties-after-seed101.md
uv run --offline python scripts/ties_rule.py runs/stats-check/ties-before-seed101.md \
    runs/stats-check/ties-after-seed101.md
```

Every other option at its default (grid 4 n x 3 tie rates, 2000 bootstrap resamples, 2000 randomisation draws, `--reps-fwer 3000`). **Monte Carlo error:** H0 cells use 10 000 replications (MC SE of a rate at 0.05 is 0.0022); power cells use 10 000 replications (MC SE <= 0.005 for any power, worst case at 0.5). FWER cells (3000 replications, SE up to 0.009) are reported for completeness and are not part of the decision. `--tau` is whatever the development selection chose and is the shipped constant. Same seed means the "before" and "after" runs see identical data cell by cell, so the difference is the test.

## Decision rule (final run, applied to the "after" report; written before any scoring)

**Adopt as the default if both hold:**

1. every one of the 36 H0 cells has randomisation Type-I point estimate **<= 0.06**, and
2. the mean power loss over the 42 power cells (`power(none) - power(after)`, randomisation column, signed mean over cells) is **<= 0.03** absolute.

**Otherwise** the path stays implemented and opt-in (`--rand-tie-fallback <winner>`; default `none`, Phase M behaviour, unchanged) and the README says so.

Reported with the rule, not part of it: the full before/after table (36 H0 cells with 99% Wilson intervals, 42 power cells), the number of H0 cells above 0.06 before and after, the largest single-cell power loss, the mean power loss with an approximate 99% interval (`+/- 2.576 * sqrt(sum_c (se_before_c^2 + se_after_c^2)) / 42` with `se = sqrt(p (1 - p) / 10000)`; it ignores that both arms use the same data, so it overstates the uncertainty), and whether binary cells are identical. If an interval for a difference includes 0 the text says "no detectable effect". Anything computed after seeing the final numbers is labelled post-hoc.

## Predictions (written before scoring)

1. H-a holds: `boott` conditional on `k` is close to the tie-free rate at `n = k` (within 0.01), so the heavy-tie failure is a small-`k` problem. [PREDICTION, not tested]
2. `boott_nz` helps modestly at (t = 0.8, n = 115) (about 0.06 rather than 0.075) and does not reach 0.05 at (t = 0.8, n = 50), where `k` is about 10. [PREDICTION, not tested]
3. `signtest` rejects mean-zero skewed data far above 0.06 (as the `sign test` column does) and `signflip` stays anti-conservative like `none`; neither wins. [PREDICTION, not tested]
4. `boott_nz_cal` has the lowest type-I of the five on the heavy-tie cells at a power cost of a few points. [PREDICTION, not tested]
5. The full rule fails: skewed tie 0 n = 20 (0.062 at seed 0) and tie 0.5 n = 20 (0.084) are untouched by a tie path at `tau >= 0.5` (tie 0.5 n = 20 partly touched at `tau = 0.5`), and several cells sit within MC noise of 0.06, so condition 1 over all 36 cells is unlikely to hold; the expected outcome is opt-in. [PREDICTION, not tested]

## Not candidates

BCa or percentile bootstrap p-values (the studentised one is the better-behaved known method), the Wilcoxon signed-rank test (tests symmetry or the median, not the mean), bounded-score betting or Hoeffding tests (valid at any n, but the skewed generator's scores are unbounded, so the bound would be data-dependent and the validity claim would not hold in this simulation).
