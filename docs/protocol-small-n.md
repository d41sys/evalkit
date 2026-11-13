# Protocol: interval coverage and test size at n = 20, 50, 100 (0/1 outcomes)

Committed before any scoring run and before the harness (`src/evalkit/statscheck_small_n.py`, `evalkit stats-check --small-n`) exists. Grid, methods, band, seeds, replication counts, selection rule and decision rules are fixed here; results are reported against them whatever they show, negative results included.

## Problem (issue #11)

The ezcross-ems forecasting set has 20 cases today and 50 to 200 are planned. `docs/protocol-leaderboard-ci.md` (README Round 5) scored the single-model interval at n = 10, 35 and 240 and the paired intervals and tests were scored by `stats-check` (README rounds 1 to 4) at n in {20, 50, 115, 240}, tie rates 0, 0.5 and 0.8, a true difference of 0 and the effects at the formula's n*. Nothing was scored at n = 20 / 50 / 100 with extreme accuracies (0.9, 0.95), disagreement rates down to 0.1 and a true difference that is a fixed share of the disagreement rate, and no band was set for coverage. Bowyer, Aitchison and Ivanova (arXiv 2503.01747, sec. 3.1, 3.4) report that CLT and percentile-bootstrap intervals under-cover at small N (95% CLT interval at N = 100: 92.5%) and that Wilson and Beta-Bernoulli (single model) and Bayesian (paired) intervals stay calibrated. This protocol measures what `evalkit` ships, then switches a default only where it falls outside the band.

## What is under test

* **Single-model interval (the default).** What the leaderboard prints for a model run on one task of 0/1 scores: `bootstrap_macro_ci` with that one task, 1000 resamples (the runner's fixed setting), percentile interval. Round 5 left it unchanged.
* **Paired interval (the default).** `paired_comparison(..., ci_method="auto")`: bootstrap-t below 400 examples unless more than half of the pairs tie, else percentile; 2000 resamples (the `stats-check` setting).
* **Paired tests (the default).** The sign-flip randomisation test `mean_test_p(..., "auto")` (2000 draws, exact enumeration up to 20 nonzero differences) and the exact sign test `PairedComparison.sign_p`.

## Data and truth

* **Single model, 12 cells:** `n` in {20, 50, 100}, true accuracy `p` in {0.5, 0.7, 0.9, 0.95}; `k ~ Binomial(n, p)` (the law of `n` i.i.d. Bernoulli(p) scores); truth is `p`.
* **Paired, 18 cells:** `n` in {20, 50, 100}, disagreement rate `psi` = P(A != B) in {0.1, 0.3, 0.6} (tie rate 1 - psi, as `Scenario("binary", n, 1 - psi, effect)` in `statscheck.py`), true difference `d = E[A - B]` in {0, psi / 2}. So `d = 0` is the type-I cell and the coverage-at-the-null cell; `d = psi / 2` has wins and losses with probabilities 3 psi / 4 and psi / 4 (psi = 0.1, d = 0.05 is "A at 0.95, B at 0.90" in the small-disagreement regime). Truth is `d`. Pairs enter every method only through the counts (wins, losses, ties), so the both-right / both-wrong split of the tied pairs does not matter.

Nominal level 95%, alpha 0.05. A replication covers when `lo - 1e-9 <= truth <= hi + 1e-9`; an interval with `lo = hi` covers only if the truth equals it.

## Band and flags (fixed here)

* Coverage **passes** at 0.93 or above, measured by the point estimate. Coverage above 0.97 is reported as `over` (conservative: valid, wider than needed); it never triggers a switch, the same as the `overcovers` flag in `stats-check`. **Failure ("under"):** point estimate below 0.93.
* Type-I error of a test **passes** at 0.06 or below (point estimate), **fails** above.
* Point estimates are used (not an interval) because the issue states the band that way. Every rate also prints its Wilson 99% interval over replications; a cell within 0.005 of a band edge is printed as `borderline` and counts by its point estimate. Monte Carlo SE at 10 000 replications: 0.0022 near 0.95, 0.003 near 0.9, 0.005 at 0.5.

## Methods

Single model (each on the same `k` and, where bootstrap, the same seed):

* `percentile`: the default above.
* `bootstrap-t`: `bootstrap_mean_ci(..., method="studentized")`, 1000 resamples. Reported, not a candidate.
* `wilson`: `statscheck.wilson_interval(k, n, level=0.95)`. Candidate.
* `jeffreys`: equal-tailed 95% interval of the Beta(k + 1/2, n - k + 1/2) posterior (Jeffreys prior). Candidate. Jeffreys is the prior with the best-known frequentist behaviour for a binomial (Brown, Cai and DasGupta 2001: its equal-tailed interval is nearly unbiased in coverage and is comparable with Wilson), and unlike the uniform prior it is invariant to reparametrisation.
* `uniform`: equal-tailed 95% interval of the Beta(k + 1, n - k + 1) posterior, the paper's snippet 1 (their "Bayes"). Candidate.

No endpoint adjustment at `k = 0` or `k = n` is made for the Beta intervals (the paper's quantile intervals are used as they are). Quantiles are found by bisection on the incomplete beta function already in `clustered.py`; no new dependency.

Paired (each on the same data and, where it resamples, the same seed):

* `auto`: the default above. `percentile`: `ci_method="percentile"`, reported, not a candidate.
* `dirichlet-jeffreys`, `dirichlet-uniform`: candidates. The 2 x 2 table (both right, A only, B only, both wrong) is Multinomial, with a symmetric Dirichlet(a) prior, `a` = 1/2 or 1. The posterior of `d = p_{A only} - p_{B only}` is sampled (4000 Dirichlet draws, drawn as Gamma variates with a fixed per-replication seed); the interval is the 2.5% and 97.5% quantiles. Aggregated to (win, loss, tie) this is Dirichlet(a, a, 2a) with the posterior counts. **Departure from the paper, stated:** Bowyer et al.'s paired Bayes (sec. 3.4, appendix E.2) uses a latent bivariate-Gaussian model with a prior on the correlation and importance sampling from the prior with a bivariate-normal orthant likelihood; it needs a bivariate normal CDF evaluated 10 000 times per dataset and is not conjugate. The Dirichlet-multinomial is its conjugate analogue on the same sufficient statistics (the paper itself uses Dirichlet(1 + counts) for its confusion-matrix metrics, sec. 3.5). If the Dirichlet intervals fail the band, the importance-sampling model is not added by this issue.

Tests (paired, `d = 0` cells only, 9 cells): rejection rate at alpha 0.05 of the randomisation test and of the sign test. Both are reported; the rule below applies to both.

## Selection and decision (fixed here)

Each quantity is scored on every cell; the unit of a rule is a count of failing cells.

1. **Single-model interval.** `F_def` = number of the 12 cells below 0.93 for `percentile`. `N_fail` = the largest grid `n` at which `percentile` has at least one failing cell (none: no switch).
   * The **winner** among `wilson`, `jeffreys`, `uniform` is chosen on the development run (seed 1) as the one with the fewest failing cells over the 12 cells; ties: the smaller `sum max(0, 0.93 - coverage)`; then the order `jeffreys`, `wilson`, `uniform`.
   * On the final run, **switch** `auto` for single-task 0/1 scores without cluster labels and `n <= N_fail` to the winner if its number of failing cells among the cells with `n <= N_fail` is strictly smaller than the default's. Otherwise nothing changes. Sizes above `N_fail` keep the percentile interval. If the winner still has failing cells, they are listed in the README; the rule does not require zero.
2. **Paired interval.** `G_def` = number of the 18 cells below 0.93 for `auto`; `N_fail` as above. Winner among `dirichlet-jeffreys`, `dirichlet-uniform` by the same development rule (order: `dirichlet-jeffreys` first). **Switch** `paired_comparison` `auto` for two 0/1 score lists without cluster labels and `n <= N_fail` to the winner under the same condition as rule 1 (strictly fewer failing cells than `auto` among the cells with `n <= N_fail`). Otherwise nothing changes.
3. **Paired tests.** If every one of the 9 type-I cells is at or below 0.06 for both tests, nothing changes. Otherwise the failing cells are listed as findings; no replacement test is pre-registered here.
4. **No default method fails the band:** if the `percentile` single-model default has no failing cell, `auto` has none and both tests pass, no default changes, the candidates are not added to the package, and the README says so.

Any analysis beyond these rules (other `n` or `p`, per-`k` breakdowns, widths, the Round 5 sizes) is labelled post-hoc.

## Runs

```bash
# development (seed 1, 4000 replications per cell)
uv run --offline evalkit stats-check --only-small-n --seed 1 --small-n-reps 4000 --out runs/stats-check/small-n-dev.md
# final (fresh seed 5001, 10 000 replications per cell)
uv run --offline evalkit stats-check --only-small-n --seed 5001 --small-n-reps 10000 --out runs/stats-check/small-n.md
```

Every other option at its default (`--resamples 2000`, `--draws 2000`, `--small-n-ns 20,50,100`). A cell's data stream is `SeedSequence([seed, cell_id])`, `cell_id` the position in the single-model then paired grid, so the same seed gives the same data for every method. Seeds 0, 1, 2, 101, 1001, 2001 to 2003 and 4001 to 4003 were used by earlier runs; seed 1 is the development seed of earlier phases, 5001 is new. The final seed is never used for selection.

## Predictions (written before any scoring; from Round 5 and the paper, not tested)

1. The `percentile` single-model interval fails at every `n` in the cells with `p >= 0.9` (Round 5: 0.864 at n = 35, p = 0.9; 0.654 at p = 0.97) and is the worst of the five methods; `bootstrap-t` fails alike (it falls back to percentile on a sample without spread).
2. `wilson`, `jeffreys` and `uniform` pass the band at `p` in {0.5, 0.7} for every `n` (coverage oscillates with `n` by a point or two but stays above 0.93). At `p = 0.9` Wilson dips below 0.93 in one or more cells (Round 5: 0.917 at n = 35).
3. `auto` for the paired difference fails in the small-disagreement cells (psi = 0.1, `n` = 20 and 50), where tie share is 0.9, `auto` uses the percentile interval and few discordant pairs make it narrow or degenerate (`[0, 0]` when every pair ties, which covers only if `d = 0`).
4. All 9 type-I cells of the randomisation and sign tests are at or below 0.06 (earlier binary cells were 0.005 to 0.044).
5. The Dirichlet intervals have no cell below 0.93 and over-cover (above 0.97) in several `d = 0` cells with psi = 0.1.

## Development outcome (seed 1, 4000 replications per cell; recorded before the final run)

```bash
uv run --offline evalkit stats-check --only-small-n --seed 1 --small-n-reps 4000 --workers 4 --out runs/stats-check/small-n-dev.md   # 45 s
```

Numbers are copied from `runs/stats-check/small-n-dev.md` (coverage below 0.93 is a failing cell).

| method | failing cells |
|---|---|
| single model `percentile` (default) | 3 of 12 (n = 20, p = 0.9: 0.876; n = 20, p = 0.95: 0.627; n = 50, p = 0.95: 0.908) |
| single model `bootstrap-t` | 5 of 12 |
| single model `wilson` | 1 of 12 (n = 20, p = 0.95: 0.919) |
| single model `jeffreys` | 1 of 12 (n = 50, p = 0.95: 0.879) |
| single model `uniform` | 1 of 12 (n = 20, p = 0.95: 0.919) |
| paired `auto` (default) | 2 of 18 (n = 20, psi = 0.1, d = 0.05: 0.780; n = 50, psi = 0.1, d = 0.05: 0.922) |
| paired `percentile` | 2 of 18 (the same two) |
| paired `dirichlet-jeffreys` | 0 of 18 |
| paired `dirichlet-uniform` | 0 of 18 |
| paired tests, type-I cells above 0.06 | 0 of 9 (largest 0.033) |

`N_fail` = 50 for both defaults. **Selection by the rule above:** single model, `wilson` (one failing cell, shortfall 0.011, against `uniform` with the same count and a shortfall that is not smaller, and `jeffreys` with 0.051; `wilson` precedes `uniform` in the tie order); paired, `dirichlet-jeffreys` (zero failing cells, ahead of `dirichlet-uniform` by the order). On the development data both would switch for `n <= 50` (single: 1 failing cell against 3; paired: 0 against 2). The final run decides.

Predictions against development data: 1 partly wrong (`percentile` fails 3 cells, not "every n with p >= 0.9": at n = 50 and 100 with p = 0.9 it covers 0.961; `bootstrap-t` fails 5 cells and is worse). 2 holds for p in {0.5, 0.7} (all four closed-form intervals at or above 0.931; `borderline` at n = 50, p = 0.5); Wilson does not dip below 0.93 at p = 0.9 here (0.955, 0.973, 0.938). 3 holds (psi = 0.1, d = 0.05 at n = 20 and 50; `auto` is the percentile interval there). 4 holds. 5 holds for coverage (no Dirichlet cell below 0.93; over-coverage at psi = 0.1, n = 20: 0.972 and 0.996, and 0.996 for `dirichlet-uniform` at d = 0).

## Final result (fresh seed 5001, 10 000 replications per cell; written after scoring)

```bash
uv run --offline evalkit stats-check --only-small-n --seed 5001 --small-n-reps 10000 --workers 4 --out runs/stats-check/small-n.md   # 101 s
```

Full tables: `docs/results/small-n-coverage.md`. In that file the paired column `bootstrap-auto` is the `auto` of this protocol (the bootstrap default: bootstrap-t below 400 examples unless more than half the pairs tie, else percentile); the harness computes it explicitly so it stays the pre-switch default after the switch below. The run was repeated after the harness was changed to compute it explicitly: every number is identical.

| method | failing cells (coverage < 0.93) |
|---|---|
| single model `percentile` (default) | 3 of 12: n = 20, p = 0.9 (0.882); n = 20, p = 0.95 (0.647); n = 50, p = 0.95 (0.910) |
| single model `bootstrap-t` | 5 of 12 |
| single model `wilson` | 1 of 12: n = 20, p = 0.95 (0.923) |
| single model `jeffreys` | 1 of 12: n = 50, p = 0.95 (0.882) |
| single model `uniform` | 1 of 12: n = 20, p = 0.95 (0.923) |
| paired `bootstrap-auto` (default) | 2 of 18: psi = 0.1, d = 0.05 at n = 20 (0.779) and n = 50 (0.919) |
| paired `percentile` | 2 of 18 (the same two) |
| paired `dirichlet-jeffreys` | 0 of 18 (lowest 0.940, over-coverage 0.971 and 0.988 at psi = 0.1, n = 20) |
| paired `dirichlet-uniform` | 0 of 18 (0.999 at psi = 0.1, n = 20, d = 0) |
| paired tests, type-I cells above 0.06 | 0 of 9 (randomisation 0.000 to 0.037, sign test 0.000 to 0.038) |

**Rule outcome.** `N_fail` = 50 for both defaults. Rule 1: the development winner `wilson` has 1 failing cell among those with n <= 50 against 3 for `percentile`: **switch** (single-task 0/1 scores, no cluster labels, n <= 50). Rule 2: the development winner `dirichlet-jeffreys` has 0 against 2: **switch** (paired 0/1 scores, no cluster labels, n <= 50). Rule 3: all type-I cells pass, no change to the tests. Rule 1 leaves one failing cell (Wilson, n = 20, p = 0.95, 0.923); the rule does not require zero, and no candidate passes every cell (`jeffreys` passes that cell at 0.985 and fails n = 50, p = 0.95 at 0.882).

Predictions against the final run: 1 partly wrong (as in development: `percentile` fails 3 cells). 2 holds (all closed-form intervals at p in {0.5, 0.7} are at or above 0.935). 3 holds. 4 holds. 5 holds.

**Post-hoc (not part of any rule).** (a) Closed-form intervals for a binomial proportion oscillate in coverage with `n` and `p` (Brown, Cai and DasGupta 2001), which is why the failing cell moves between Wilson and Jeffreys. (b) Sizes between 50 and 100 and above 100 keep the bootstrap by the rule's wording: the grid has no cell there. Round 5's n = 240, p = 0.97 cell (percentile 0.922, Wilson 0.945) is outside this protocol.

## Amendment 1 (2026-11-13, after the scored run; not pre-registered)

Change: the shipped Dirichlet-Jeffreys paired interval is the hull of the 95% credible interval and the observed difference `(wins - losses) / n` (PR #21). Reason: at a boundary split such as 20 / 0 / 0 the credible interval excludes the observed `+1.000` (`[+0.723, +0.994]`), which reads as a bug. The hull only widens, so coverage can only rise. It changes the interval only when every non-tied pair goes one way.

Order: the seed-5001 grid was rerun with the hull before this amendment was written. Every printed number came out identical, so no decision changed. The original pre-registration order is preserved in PR #20's commits (author times): this protocol `1c26ed7` 00:39, harness `23581cc` 00:41, development outcome `b452680` 00:42, scored results `dc95a8e` 00:49 UTC. The squash merge to `main` (`b5e62cb`) collapses them.
