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

## Development outcome (seeds 1 and 2; recorded before the final run)

```bash
uv run --offline python scripts/ties_dev.py --seeds 1,2 --workers 10 --out runs/stats-check/ties-dev.md
```

(4000 H0 and 2000 power replications per seed and cell; 7 min 37 s; full output, including the 36 H0 cells and the power cells for all 11 configurations, in `runs/stats-check/ties-dev.md`.) Numbers below are copied from that file.

**Diagnosis.** Type-I of `boott` (Phase M, all differences) against `boott` on a tie-free skewed sample of the same `k`, and `boott_nz`, skewed, tie rate 0.8, pooled over the seeds:

| n | k | boott | tie-free boott | boott_nz | boott_nz_cal |
|---|---|---|---|---|---|
| 115 | 10-19 | 0.064 | 0.068 | 0.053 | 0.059 |
| 115 | 20-29 | 0.068 | 0.055 | 0.056 | 0.051 |
| 115 | 30-49 | 0.072 | 0.056 | 0.060 | 0.047 |
| 240 | 30-49 | 0.059 | 0.057 | 0.053 | 0.049 |
| 240 | >=50 | 0.062 | 0.058 | 0.058 | 0.052 |
| 50 | 10-19 | 0.078 | 0.071 | 0.073 | 0.074 |
| 50 | 0-9 | 0.035 | 0.071 | 0.071 | 0.071 |
| 20 | 0-9 | 0.015 | 0.072 | 0.072 | 0.021 |

* **H-b holds.** Zero resampling costs `boott` about 0.01 to 0.016 at k = 20 to 49 and n = 115 (0.068 and 0.072 against 0.055 and 0.056 for the same `k` without zeros); `boott_nz` removes it (0.056 and 0.060, equal to the tie-free rate within 0.005).
* **H-a holds only in part.** At n = 240 `boott` is within 0.005 of the tie-free rate; at n = 115 it is 0.013 to 0.016 above, and at k < 10 it is far below (0.015 to 0.035 against 0.071): with few nonzero differences and many resampled zeros the studentised statistic has a heavy right tail and the test turns conservative, by accident rather than design. The remaining inflation at `k` of about 10 (0.07 for every bootstrap-t variant, tie-free too) is the small-sample skewness error of bootstrap-t, which no tie rule removes (n = 50, k < 20: 0.071 to 0.074 for `boott_nz` and `boott_nz_cal`).
* Sign test: 0.083 to 0.445 at k >= 10, as expected (median, not mean). `signflip` stays at 0.065 to 0.096 for k >= 10. `johnson_nz` is 0.116 to 0.176 at k < 10.

**Configurations** (rule of the selection section; full table in the file): `none` has 6 H0 cells above 0.06 (mean of the two seeds); `signflip` 7 and 6, `signtest` 8 and 6, `johnson_nz` 5 and 5 (not eligible: continuous H0 cells worsen by 0.047 to 0.055, tie rate 0.8, n = 20), `boott_nz` 3 and 4, `boott_nz_cal` 3 and 4 (tau 0.5 and 0.7). Mean power loss (none minus configuration, binary counted 0) is between -0.053 and +0.004; `boott_nz_cal` +0.0010 at tau 0.5. **Winner: `boott_nz_cal`, tau 0.5** (3 H0 cells above 0.06, excess sum 0.1166, against `boott_nz` tau 0.5 with 3 cells and 0.1331). The shipped constants are `TIE_GATE = 0.5` and, if the final rule is not met, `TIE_FALLBACK = "none"`.

The 3 dev cells above 0.06 under the winner are skewed tie 0 n = 20 (0.0653, no tie path can touch it), skewed tie 0.5 n = 20 (0.0866) and skewed tie 0.8 n = 50 (0.0668). Prediction 5 therefore looks right on development data; the final run decides.

**Predictions against development data.** 1: partly (see H-a above). 2: yes (`boott_nz` 0.057 at tie 0.8, n = 115; 0.072 at n = 50). 3: yes (sign test 0.184 and 0.325 at tie 0.8, n = 115 and 240; `signflip` 0.073 and 0.068). 4: lowest type-I of the five on the heavy-tie cells at n = 115 and 240 (0.053, 0.055) and n = 50 (0.067); the power change (none minus `boott_nz_cal`, tau 0.5) ranges per cell from a gain of 0.044 to a loss of 0.106 (fixed skewed, tie 0.6, effect 0.2, n* = 17) and the mean over all 42 cells is a loss of 0.001, so "a few points" holds on average, not per cell.


## Final result (fresh seed 101, 10 000 replications per H0 and power cell; written after scoring)

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
uv run --offline evalkit stats-check --seed 101 --reps-h0 10000 --reps-power 10000 --workers 10 \
    --rand-tie-fallback none --out runs/stats-check/ties-before-seed101.md          # 231 s
uv run --offline evalkit stats-check --seed 101 --reps-h0 10000 --reps-power 10000 --workers 10 \
    --rand-tie-fallback boott_nz_cal --out runs/stats-check/ties-after-seed101.md   # 842 s
uv run --offline python scripts/ties_rule.py runs/stats-check/ties-before-seed101.md \
    runs/stats-check/ties-after-seed101.md > runs/stats-check/ties-rule-seed101.md
```

(`--workers` only sets the process count; the data stream is keyed by seed and cell id. `--rand-tie-gate` is its default 0.5. FWER cells ran at 3000 replications and are not part of the rule; the continuous Holm FWER cells that differ between the two reports differ by at most 0.001 in the Wilson bounds.) Monte Carlo SE: 0.0022 for an H0 rate near 0.05, at most 0.005 for a power cell.

**Rule, verbatim:** "Adopt as the default if both hold: 1. every one of the 36 H0 cells has randomisation Type-I point estimate **<= 0.06**, and 2. the mean power loss over the 42 power cells (`power(none) - power(after)`, randomisation column, signed mean over cells) is **<= 0.03** absolute. **Otherwise** the path stays implemented and opt-in (`--rand-tie-fallback <winner>`; default `none`, Phase M behaviour, unchanged) and the README says so."

**Outcome against the rule.**

* Condition 1: **fail**. 35 of 36 H0 cells are <= 0.06; the failing cell is skewed, tie rate 0.5, n = 20: 0.083 [0.076, 0.090] (before: 0.088 [0.081, 0.096]). The interval excludes 0.06, so this is not Monte Carlo noise.
* Condition 2: **pass**. Mean power loss +0.0009 (approximate 99% interval -0.0013 to +0.0032, which includes 0: no detectable mean power effect). Per cell it ranges from a gain of 0.047 to a loss of 0.107 (fixed, skewed, tie 0.6, effect 0.2, n* = 17: 0.672 to 0.565).
* Binary cells (H0 and power) are identical to the digit before and after.
* **Decision: not adopted as the default; the path stays opt-in.** `TIE_FALLBACK = "none"`.

H0 cells above 0.06, before to after: 5 to 1. Before: skewed tie 0.5 n = 20 (0.088), tie 0.5 n = 50 (0.067), tie 0.8 n = 50 (0.069), n = 115 (0.071), n = 240 (0.064). After: only tie 0.5 n = 20 (0.083). The target cell of this phase, skewed tie 0.8 n = 115, goes from 0.071 [0.065, 0.078] to 0.055 [0.050, 0.061]; the Round 3 seed-0 value was 0.075.

#### H0 cells: randomisation Type-I error (99% Wilson), before -> after

| kind | tie rate | n | before | after |
|---|---|---|---|---|
| binary | 0 | 20 | 0.041 [0.036, 0.046] | 0.041 [0.036, 0.046] |
| binary | 0 | 50 | 0.033 [0.028, 0.038] | 0.033 [0.028, 0.038] |
| binary | 0 | 115 | 0.037 [0.033, 0.042] | 0.037 [0.033, 0.042] |
| binary | 0 | 240 | 0.043 [0.038, 0.049] | 0.043 [0.038, 0.049] |
| binary | 0.5 | 20 | 0.022 [0.019, 0.026] | 0.022 [0.019, 0.026] |
| binary | 0.5 | 50 | 0.033 [0.028, 0.037] | 0.033 [0.028, 0.037] |
| binary | 0.5 | 115 | 0.039 [0.035, 0.045] | 0.039 [0.035, 0.045] |
| binary | 0.5 | 240 | 0.044 [0.039, 0.050] | 0.044 [0.039, 0.050] |
| binary | 0.8 | 20 | 0.005 [0.003, 0.007] | 0.005 [0.003, 0.007] |
| binary | 0.8 | 50 | 0.021 [0.018, 0.026] | 0.021 [0.018, 0.026] |
| binary | 0.8 | 115 | 0.034 [0.029, 0.039] | 0.034 [0.029, 0.039] |
| binary | 0.8 | 240 | 0.033 [0.029, 0.038] | 0.033 [0.029, 0.038] |
| continuous | 0 | 20 | 0.048 [0.043, 0.054] | 0.048 [0.043, 0.054] |
| continuous | 0 | 50 | 0.050 [0.045, 0.056] | 0.050 [0.045, 0.056] |
| continuous | 0 | 115 | 0.044 [0.039, 0.049] | 0.044 [0.039, 0.049] |
| continuous | 0 | 240 | 0.049 [0.044, 0.055] | 0.049 [0.044, 0.055] |
| continuous | 0.5 | 20 | 0.040 [0.035, 0.045] | 0.041 [0.036, 0.046] |
| continuous | 0.5 | 50 | 0.054 [0.048, 0.060] | 0.053 [0.048, 0.060] |
| continuous | 0.5 | 115 | 0.050 [0.045, 0.056] | 0.050 [0.045, 0.056] |
| continuous | 0.5 | 240 | 0.046 [0.041, 0.052] | 0.046 [0.041, 0.052] |
| continuous | 0.8 | 20 | 0.005 [0.003, 0.007] | 0.006 [0.004, 0.008] |
| continuous | 0.8 | 50 | 0.038 [0.034, 0.044] | 0.043 [0.038, 0.048] |
| continuous | 0.8 | 115 | 0.049 [0.044, 0.055] | 0.049 [0.043, 0.055] |
| continuous | 0.8 | 240 | 0.048 [0.043, 0.054] | 0.048 [0.043, 0.054] |
| skewed | 0 | 20 | 0.058 [0.052, 0.065] | 0.058 [0.052, 0.065] |
| skewed | 0 | 50 | 0.058 [0.052, 0.064] | 0.058 [0.052, 0.064] |
| skewed | 0 | 115 | 0.056 [0.051, 0.062] | 0.056 [0.051, 0.062] |
| skewed | 0 | 240 | 0.053 [0.047, 0.059] | 0.053 [0.047, 0.059] |
| skewed | 0.5 | 20 | 0.088 [0.081, 0.096] | 0.083 [0.076, 0.090] |
| skewed | 0.5 | 50 | 0.067 [0.061, 0.073] | 0.059 [0.054, 0.066] |
| skewed | 0.5 | 115 | 0.059 [0.053, 0.065] | 0.055 [0.049, 0.061] |
| skewed | 0.5 | 240 | 0.056 [0.051, 0.062] | 0.056 [0.050, 0.062] |
| skewed | 0.8 | 20 | 0.017 [0.014, 0.021] | 0.015 [0.013, 0.019] |
| skewed | 0.8 | 50 | 0.069 [0.062, 0.075] | 0.057 [0.051, 0.063] |
| skewed | 0.8 | 115 | 0.071 [0.065, 0.078] | 0.055 [0.050, 0.061] |
| skewed | 0.8 | 240 | 0.064 [0.058, 0.070] | 0.056 [0.050, 0.062] |

#### Power cells: randomisation power at n*, before -> after

| group | kind | tie rate | true effect | n* | before | after | loss |
|---|---|---|---|---|---|---|---|
| mde | binary | 0 | 0.597 | 20 | 0.803 | 0.803 | +0.000 |
| mde | binary | 0 | 0.408 | 49 | 0.809 | 0.809 | +0.000 |
| mde | binary | 0 | 0.267 | 112 | 0.789 | 0.789 | +0.000 |
| mde | binary | 0 | 0.183 | 240 | 0.803 | 0.803 | +0.000 |
| mde | binary | 0.5 | 0.431 | 20 | 0.800 | 0.800 | +0.000 |
| mde | binary | 0.5 | 0.287 | 50 | 0.805 | 0.805 | +0.000 |
| mde | binary | 0.5 | 0.189 | 115 | 0.802 | 0.802 | +0.000 |
| mde | binary | 0.5 | 0.131 | 240 | 0.803 | 0.803 | +0.000 |
| mde | binary | 0.8 | 0.176 | 50 | 0.800 | 0.800 | +0.000 |
| mde | binary | 0.8 | 0.120 | 115 | 0.806 | 0.806 | +0.000 |
| mde | binary | 0.8 | 0.083 | 240 | 0.799 | 0.799 | +0.000 |
| mde | continuous | 0 | 0.157 | 21 | 0.775 | 0.775 | +0.000 |
| mde | continuous | 0 | 0.099 | 51 | 0.800 | 0.800 | +0.000 |
| mde | continuous | 0 | 0.065 | 115 | 0.788 | 0.788 | +0.000 |
| mde | continuous | 0 | 0.045 | 241 | 0.799 | 0.799 | +0.000 |
| mde | continuous | 0.5 | 0.142 | 21 | 0.817 | 0.816 | +0.001 |
| mde | continuous | 0.5 | 0.076 | 50 | 0.818 | 0.818 | +0.000 |
| mde | continuous | 0.5 | 0.048 | 116 | 0.816 | 0.816 | +0.000 |
| mde | continuous | 0.5 | 0.033 | 241 | 0.809 | 0.809 | +0.000 |
| mde | continuous | 0.8 | 0.073 | 51 | 0.848 | 0.870 | -0.022 |
| mde | continuous | 0.8 | 0.034 | 116 | 0.857 | 0.856 | +0.001 |
| mde | continuous | 0.8 | 0.022 | 241 | 0.827 | 0.827 | +0.000 |
| mde | skewed | 0 | 0.157 | 21 | 0.729 | 0.729 | +0.000 |
| mde | skewed | 0 | 0.099 | 51 | 0.816 | 0.816 | +0.000 |
| mde | skewed | 0 | 0.065 | 115 | 0.829 | 0.829 | +0.000 |
| mde | skewed | 0 | 0.045 | 241 | 0.829 | 0.829 | +0.000 |
| mde | skewed | 0.5 | 0.142 | 21 | 0.681 | 0.707 | -0.026 |
| mde | skewed | 0.5 | 0.076 | 50 | 0.719 | 0.732 | -0.013 |
| mde | skewed | 0.5 | 0.048 | 116 | 0.822 | 0.806 | +0.016 |
| mde | skewed | 0.5 | 0.033 | 241 | 0.842 | 0.834 | +0.008 |
| mde | skewed | 0.8 | 0.073 | 51 | 0.708 | 0.714 | -0.006 |
| mde | skewed | 0.8 | 0.034 | 116 | 0.697 | 0.744 | -0.047 |
| mde | skewed | 0.8 | 0.022 | 241 | 0.793 | 0.780 | +0.013 |
| fixed | binary | 0.6 | 0.050 | 1291 | 0.794 | 0.794 | +0.000 |
| fixed | binary | 0.6 | 0.100 | 329 | 0.796 | 0.796 | +0.000 |
| fixed | binary | 0.6 | 0.200 | 84 | 0.811 | 0.811 | +0.000 |
| fixed | continuous | 0.6 | 0.050 | 91 | 0.829 | 0.829 | +0.000 |
| fixed | continuous | 0.6 | 0.100 | 32 | 0.845 | 0.848 | -0.003 |
| fixed | continuous | 0.6 | 0.200 | 17 | 0.695 | 0.662 | +0.033 |
| fixed | skewed | 0.6 | 0.050 | 91 | 0.777 | 0.760 | +0.017 |
| fixed | skewed | 0.6 | 0.100 | 32 | 0.662 | 0.702 | -0.040 |
| fixed | skewed | 0.6 | 0.200 | 17 | 0.672 | 0.565 | +0.107 |


**Predictions against the final run.** 5 (rule fails): the outcome is right, the reasoning is only partly: one cell fails, the tie-0.5 n = 20 cell that the path touches only in about half the replications (about 10 nonzero differences); skewed tie 0 n = 20 came out at 0.058 on this seed (0.065 on the development seeds, 0.062 at seed 0), inside the band by Monte Carlo luck.

**Post-hoc (not pre-registered).** (a) The one failing cell has about 10 nonzero differences. Development seeds show every bootstrap-t variant at 0.07 for tie-free skewed data at that size (diagnosis table above), so no tie rule is expected to bring it below 0.06; the cell is not a tie-path failure but the same small-`k` limit as skewed tie 0 n = 20 (0.058 here). (b) The calibrated test loses power where `k` is about 7 (fixed skewed n* = 17, tie 0.6) and gains it where Phase M's `boott` on all differences was conservative (skewed tie 0.8 n* = 116: 0.697 to 0.744), so the mean is near 0 while single cells move by up to 0.1 in either direction. (c) The calibrated bootstrap costs about 24 ms per call at `k` of about 23 (one timed call, 2000 draws); the "after" run took 842 s against 231 s, most of the difference being this test [INFERENCE, not profiled].
