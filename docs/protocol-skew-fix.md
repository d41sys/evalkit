# Protocol: fixing the type-I inflation of the randomisation test on skewed differences

Committed before any candidate is scored. Candidates, gate, selection rule, pass criteria and predictions below are fixed; results are reported whatever they show.

## Diagnosis (from reading the code and the round-2 report, no new run)

`evalkit stats-check` (`runs/stats-check/report.md`, seed 0) shows the **randomisation test** (`rand_p`, the p-value that decides `resolved` in `compare --all-pairs`, Holm-adjusted) rejecting a true null in 9 of the 12 skewed H0 cells at 0.056 to 0.089 (nominal 0.05). Findings:

1. It is the **sign-flip test**, not a bootstrap CI. The percentile / BCa / bootstrap-t choice (`--ci-method`) only changes the CI column, which is a separate (and also imperfect at tie rates 0.5 and 0.8) object; the p-value never sees it.
2. **Studentising the sign-flip statistic cannot help.** Under sign flips `s_i d_i`, the sum of squares `sum d_i^2` is invariant, so the one-sample t statistic is a monotone function of `|sum s_i d_i|`: the studentised flip test and the plain sum flip test give the same p-value (Fisher's classic equivalence). A fix must replace the *reference distribution*, not the statistic. A unit test pins this equivalence.
3. The flip distribution assumes each difference is symmetric around 0 (stronger than "mean 0"). The skewed generator has mean 0 and an `Exp(1) - 1` shape, so the assumption fails and the test is only asymptotically valid for the mean.
4. The sign test in the same table is a median test and is *meant* to reject skewed mean-zero data; it is not part of this fix (it is a reported column, not the decision).
5. Binary scores: every nonzero `|d|` is equal, the flip test is the exact conditional McNemar test (the exact power formulas rely on it), and it stays.

## Candidate tests (two-sided, alpha 0.05, H0: mean of the per-example differences is 0; `d` over all n examples, ties included)

* `signflip`: the shipped test (baseline).
* `boott`: bootstrap-t test. `t = mean / (sd / sqrt(n))` (ddof 1). Resample `B = draws` times from the mean-centred differences `d - mean`, `t*` from each resample (resamples with `sd* = 0` dropped), `p = (1 + #{|t*| >= |t|}) / (B_eff + 1)`. Constant nonzero differences (sd 0) fall back to `signflip`; all zeros give 1.
* `johnson`: closed-form skewness-corrected t (Johnson 1978; Hall 1992, Edgeworth: `P(T <= x) ~ Phi(x) + n^-1/2 (g/6)(2x^2 + 1) phi(x)`). With `g` the sample skewness, `a = g / (3 sqrt(n))`, `G(x) = ((1 + a x)^3 - 1) / (3a) + a / 2` (monotone), `F(t) = Phi(G(t))`, `p = min(1, 2 min(F, 1 - F))`. `a = 0` is the normal-theory t.
* `auto` (gated): `signflip` unless the **asymmetry gate** fires, then the fallback (`boott` or `johnson`). Gate: scores not binary (all nonzero `|d|` equal) **and** `k < 25 g_nz^2`, `k` the number of nonzero differences, `g_nz` their sample skewness (Cochran's rule with the ties removed; the all-differences version already shipped as `skewness_warning` fires on tie-heavy symmetric data because zero inflation looks like skew, and the fire rate on binary and continuous H0 cells was the round-2 failure). The constant 25 is not tuned.

Not candidates: BCa/bootstrap percentile *p-values* (percentile-t is the studentised one and is the better-behaved known method), permuting model labels (identical to sign flips), the Wilcoxon signed-rank test (tests symmetry/median, not the mean).

## Selection (development seed 1 only; seed 0 is the final run and is scored once)

Run the full stats-check grid, replications and decision rules of round 2, seed 1, for: `signflip` (baseline), `boott`, `johnson`, `auto --rand-fallback boott`, `auto --rand-fallback johnson`. Winner = the candidate with the most skewed H0 cells (of 12) whose point-estimate rejection rate is in **[0.035, 0.065]**, subject to:

* binary H0 cells identical to the baseline (guaranteed by construction; verified),
* the number of continuous H0 cells with a point estimate outside [0.035, 0.065] not higher than the baseline's, and no continuous H0 cell newly flagged `anti-conservative`,
* no continuous or binary Holm FWER cell newly flagged `anti-conservative`.

Ties: smaller sum over the 12 skewed cells of `|rate - 0.05|`, then the gated variant, then `johnson` (closed form, no resampling noise). Power is reported for all candidates (skewed and continuous H1 cells) and is **not** part of the rule; a power drop is disclosed.

## Final run (seed 0, identical grid, replications and decision rules to round 2)

```bash
uv run evalkit stats-check --out runs/stats-check/report-skewfix.md   # winner as the default
uv run python scripts/stats_check_compare.py runs/stats-check/report.md runs/stats-check/report-skewfix.md
```

Same seed, so the H0 data are identical cell by cell (the cell ids do not change) and the before/after difference is the test.

**Pass:** all 12 skewed H0 point estimates in [0.035, 0.065] at seed 0, and the continuous / binary conditions above on seed 0. **Partial** otherwise; the cells outside the band are listed with the reason.

## Predictions (written before scoring)

1. Baseline seed 1 reproduces the pattern of seed 0: at least 8 of 12 skewed cells above 0.065 or flagged anti-conservative.
2. `boott` and `johnson` bring the cells with tie rate 0 and n >= 50 and the tie-rate 0.5 n >= 115 cells into the band. Both leave at least one small-n cell outside the band: with n = 20 and tie rate 0.8 there are about 4 nonzero differences; the sign-flip test cannot reject at all with at most 5 (`2 / 2^k > 0.05`; baseline 0.015), and a bootstrap or Edgeworth correction estimated from 4 points is unlikely to land in the band. I expect that cell to fail the band under every candidate, so the full "all 12 in band" pass is unlikely. [PREDICTION, not tested]
3. The gated variants cost no power on continuous H1 cells (the gate rarely fires on symmetric nonzero differences with k >= 25) and the ungated ones lose some.
4. `johnson` and `boott` rank within 2 cells of each other.
