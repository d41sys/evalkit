# Protocol: clustered standard errors in `evalkit stats-check`

Committed before the first scoring run of the clustered grid. The grid, estimators, replication counts and decision rules below are fixed; results are reported whatever they show.

## What is being tested

Eval items often come in groups (questions about one passage, items from one source document). Scores inside a group are correlated, so the usual SE `s / sqrt(n)` is too small. Miller (2024, "Adding Error Bars to Evals", arXiv [2411.00640](https://arxiv.org/abs/2411.00640)) gives the clustered standard error of a mean

    SE_clustered = sqrt( SE_CLT^2 + (1/n^2) * sum_c sum_i sum_{j != i} (s_ic - s_bar)(s_jc - s_bar) )

with `SE_CLT^2 = Var(s) / n` (unbiased variance), `s_ic` the score of item `i` in cluster `c`, `s_bar` the grand mean, and the double sum over ordered pairs of distinct items in the same cluster. `evalkit.clustered.clustered_se` implements exactly this. The design effect used for power is `DEFF = 1 + (m - 1) * ICC` (Kish 1965; for unequal cluster sizes `m` is `sum_c m_c^2 / N`, Eldridge, Ashby & Kerry 2006).

Claims under test:

1. The naive SE (`s / sqrt(n)`) and the item-level bootstrap of the shipped CI **undercover** when ICC > 0.
2. The clustered SE (normal CI) and the cluster bootstrap CI are **calibrated**.
3. The per-example sign-flip test is **anti-conservative** under clustering; the cluster sign-flip test (flip whole clusters) is valid.
4. The DEFF-inflated sample size reaches the 80% power it promises.

## Data-generating processes (all numpy, seeded, no models)

Common: `C` clusters; cluster sizes `m_c` are either **equal** (`m_c = 5`) or **unequal** (`m_c = 1 + Poisson(4)`, drawn per replication, mean 5). `rho` is the intra-cluster correlation of the analysed scores.

*Design `mean`* (one model's scores; truth is the population mean):

- `continuous`: `y_ic = 0.5 + 0.25 (sqrt(rho) z_c + sqrt(1 - rho) e_ic)`, `z_c, e_ic ~ N(0,1)`. Truth 0.5.
- `binary`: `p_c ~ Beta(mu k, (1 - mu) k)` with `mu = 0.6`, `k = 1/rho - 1` (`p_c = mu` when `rho = 0`), `y_ic ~ Bernoulli(p_c)`. Truth 0.6. This is the beta-binomial model, whose ICC is exactly `rho`.

*Design `paired`* (scores of A and B on the same items; the analysed score is `d = A - B`; truth is 0, so these are also the null cells for the tests):

- `continuous`: `d_ic = 0.25 (sqrt(rho) z_c + sqrt(1 - rho) e_ic)`, passed as `A = d`, `B = 0`.
- `binary`: `s_c ~ U(-w, w)` with `w^2 = 3 rho / (8 - 4 rho)`, `pA_c = 0.5 + s_c`, `pB_c = 0.5 - s_c`, `A_ic ~ Bernoulli(pA_c)`, `B_ic ~ Bernoulli(pB_c)` independent given the cluster, `d = A - B`. `E d = 0` and the ICC of `d` is exactly `rho` (between-cluster variance `4 w^2 / 3` over total variance `1/2 + 2 w^2 / 3`). Swapping A and B maps `s_c` to `-s_c`, so `A, B` are exchangeable by construction and the cluster sign-flip test is exact for these cells.

## Grid and replications

`rho` in {0, 0.1, 0.3} x `C` in {20, 50, 100} x sizes in {equal, unequal} x kind in {binary, continuous} x design in {mean, paired}: 72 cells, 2000 replications each, seed 0, 1000 bootstrap resamples, 2000 randomisation draws (exact enumeration up to 20 nonzero clusters / differences, as everywhere in evalkit).

Per replication, four 95% interval estimators:

| id | estimator | shipped function |
|---|---|---|
| E1 | `mean +/- 1.96 * s / sqrt(n)` | `naive_se` |
| E2 | the item-level bootstrap CI that `evalkit compare` printed before this change | `bootstrap_mean_ci` (design `mean`), `paired_comparison` without clusters (design `paired`), method `auto` |
| E3 | `mean +/- 1.96 * SE_clustered` | `clustered_se` |
| E4 | cluster bootstrap, percentile interval | `cluster_bootstrap_ci` / `paired_comparison(clusters=...)` |

Design `paired` also records the rejection rate at alpha 0.05 of P1 (per-example sign-flip, `randomization_test_p`) and P2 (cluster sign-flip, `cluster_randomization_test_p`). Reported for every cell: mean `SE_clustered / SE_naive` next to the theoretical `sqrt(DEFF)` (`DEFF = 1 + (m_w - 1) rho` with `m_w = 5` for equal sizes and `m_w = 29/5 = 5.8` for unequal ones, `E m^2 / E m` for `m = 1 + Poisson(4)`).

*Power with DEFF* (design `paired`, `continuous`, equal clusters of 5, true effect 0.10, SD of `d` 0.25, `rho` in {0, 0.1, 0.3}): `N = C * 5` with `C = ceil(required_sample_size(0.25, 0.10, deff=DEFF) / 5)`; 2000 replications; power of the cluster sign-flip test and of "cluster bootstrap CI excludes 0". A second row per `rho` shows the power at the naive `n = required_sample_size(0.25, 0.10)` (rounded up to a multiple of 5) to show what the design effect buys. Binary-score power with DEFF is not simulated; it uses the same `n / DEFF` scaling and is a formula, not a validated claim.

## Decision rules (fixed now)

Every proportion carries a Wilson 99% interval over replications; coverage and power are classified with the existing `classify_coverage`, `classify_error_rate` and `classify_power` (README, "Decision rule").

- **Claim 1, naive undercovers: supported** if E1 and E2 are each flagged `undercovers` in at least 90% of the 48 cells with `rho > 0` (counts reported). Otherwise reported as not supported, with the cells.
- **Claim 2, clustered is calibrated.** Binding on E3 and E4 in the cells with `C >= 50` (all `rho`, 48 cells):
  - *supported* if neither is flagged `undercovers` in any of those cells;
  - *approximately supported* if some are flagged but every such cell has point coverage >= 0.93;
  - otherwise *not supported*, with the cells listed.
  - Cells with `C = 20` are reported but not binding: a normal-quantile or percentile interval from 20 cluster-level observations is known to undercover (Cameron & Miller 2015, "A Practitioner's Guide to Cluster-Robust Inference"). No change to the estimators is made after seeing them.
- **Control:** at `rho = 0` the clustered estimators must not be flagged `undercovers` at `C >= 50`; E1/E2 flags at `rho = 0` are reported as they come.
- **Claim 3, tests.** In design `paired`: P1 *anti-conservative* in a cell if `classify_error_rate` says so; claim supported if that holds in at least 90% of the `rho > 0` cells. P2 is binding in all 36 paired cells: *supported* if no cell is `anti-conservative`.
- **Claim 4, power:** `classify_power` on the cluster sign-flip test at the DEFF-inflated `N`; `optimistic` is a failure and is reported. The naive-`n` rows are descriptive.
- SE ratio vs `sqrt(DEFF)`: descriptive, no pass or fail.

## Procedure

1. Implement; unit tests run on tiny replication counts only.
2. Debug runs may use seed 1 and a few replications; nothing about the estimators, grid, replication counts or rules is tuned from them.
3. One final run with seed 0 and the full grid: `uv run --offline evalkit stats-check --only-clustered --out docs/results/clustered-se-stats-check.md`.
4. A real bug found afterwards gets a fix and a regression test and a rerun is reported next to the first; a limitation of a method is a finding, not a patch.
