# Protocol: IRT anchor-item subsets on HELM Lite (tinyBenchmarks-style)

Committed before any scoring run. Estimators, selection methods, splits, metrics, decision rule and predictions are fixed; results are reported whatever they show. numpy only, no models, no network.

## Question

Can ~100 of the 10,200 HELM Lite instances reproduce the model ranking and the macro score of the full benchmark for models the item analysis has never seen? tinyBenchmarks (Polo et al. 2024, [arXiv 2402.14992](https://arxiv.org/abs/2402.14992)) answers yes for MMLU / Open LLM Leaderboard sized benchmarks, with anchor items chosen from clusters and scores estimated with an IRT model. This protocol re-implements that recipe with a numpy-only fitter and tests it against random subsets with a model-level split.

## Data

`runs/helm-lite/results.jsonl`: 91 models x 10,200 instances over 10 scenarios (gsm8k 1000, legalbench 2047, math 437, medqa 503, mmlu 514, narrativeqa 355, naturalquestions_closed 1000, naturalquestions_open 1000, openbookqa 500, wmt14 2844); `score` is HELM's main metric per scenario, in [0, 1] (0/1 for exact match, fractional for F1 / BLEU). 87 models have every instance; 4 miss one block (gsm8k 1000, legalbench 485 for two, wmt14 503). Instances missing for any model are excluded from the anchor pool; they stay in the target of the models that have them.

**Target score** of model j: `T_j = mean over scenarios s of (mean of j's scores on the scenario-s instances j has)`, the macro average with every scenario weighing 1/10. The item weight is `w_i = 1 / (10 n_s)`. This is not HELM's mean win rate (which needs the published per-scenario tables); it is the per-instance score aggregate. `helm-study` already reproduces the published per-scenario means from these data.

## Models of item response (fit by numpy, no new dependency)

`P(y_ij) = sigmoid(a_i theta_j - c_i)`; 1PL fixes `a_i = 1`, 2PL fits `a_i > 0`. Scores in [0, 1] enter the likelihood as soft labels: `y log p + (1 - y) log (1 - p)`, the same cross-entropy as a binary Bernoulli likelihood (fractional scores are treated as success probabilities; this is a quasi-likelihood, not a calibrated model of BLEU). MAP estimation: `theta_j ~ N(0, 1)`, `c_i ~ N(0, 3^2)`, `a_i ~ N(1, 0.5^2)` truncated to [0.05, 5]. Alternating damped Fisher scoring (60 sweeps over abilities then items); convergence is reported as the change in the penalised log-likelihood over the last sweep. A test model's `theta` is the MAP given only its anchor-item scores and the item parameters fitted on the training models.

## Subset selection (100 anchors; the item parameters and the clustering use the 70 training models only)

| name | how |
|---|---|
| `random` | 100 uniform random pool items; scores re-weighted by the self-normalised item weights `w_i` (Hajek estimator of the macro score) |
| `stratified` | 10 random pool items per scenario; the estimate is the mean of the 10 scenario means (equal allocation is optimal for the macro average, so this is the hard baseline) |
| `anchor-correct` | k-means (k = 100, k-means++ start, seeded) on the standardised training-model score vectors of each pool item; the anchor is the item nearest each centroid and carries the weight `sum of w_i` over its cluster (tinyBenchmarks' "correctness" anchors) |
| `anchor-irt` | the same on the 2D embedding `(a_i, b_i = c_i / a_i)` of the 2PL fit, standardised (tinyBenchmarks' "IRT" anchors, 1-D ability so a 2-D embedding) |
| `info` | greedy Fisher information: for 100 ability quantiles of the training abilities (evenly spaced), take the unused item with the largest `a_i^2 p (1 - p)` at that ability, ties by lower index; every anchor weighs `1 / 100` |

## Estimators of T_j for a test model from its anchor scores `y`

* `anchor-mean`: `sum_c W_c y_c` (weights as above; `stratified` and `random` use their own rule above, not an arbitrary one).
* `p-irt`: `sum_i w_i sigmoid(a_i theta_hat - c_i)` over **all** items the test model has, `theta_hat` from the anchors only.
* `blend`: `0.5 anchor-mean + 0.5 p-irt` (the simple average; tinyBenchmarks' gp-IRT uses a data-dependent weight that I do not claim to reproduce).

`p-irt` and `blend` are computed with both the 1PL and the 2PL fit. Reported: every (selection x estimator x model) cell.

## Evaluation (model-level cross-validation)

1. **Repeated 70/21 splits:** 50 random splits of the 91 models, seed 0 (split `r` uses `SeedSequence([0, r])`; the random subsets of `random` / `stratified` are drawn from the same stream, so every method sees the same splits). Per split, per method: Kendall tau-b between estimated and true `T_j` on the 21 test models, mean absolute error of the estimate (in score points), RMSE. Report the mean over splits with the 2.5 / 97.5 percentiles over splits.
2. **4-fold cross-fit on all 91:** models in a seeded random permutation, folds of 23/23/23/22, fit on the other ~68; every model gets one held-out estimate; Kendall tau and MAE over all 91 pooled held-out estimates. This is the "does it reproduce the 91-model ranking" figure.
3. **Reference:** the same two statistics for `stratified` repeated over 1000 random draws against the true scores (no model split needed, since a random subset uses no training data), so the random baseline's own spread is known.

## Decision rule

A method **beats** the baseline if the 95% percentile bootstrap CI over splits of the mean paired difference (tau: method minus baseline; MAE: baseline minus method) is entirely above 0 for both tau and MAE. Baseline for the headline comparison: `stratified` + `anchor-mean`. If the CI includes 0 on either statistic: "no detectable difference". The 50 splits overlap, so the CI describes variation over test-set choice at fixed 91 models, not an independent-sample guarantee. The pre-named headline method is `anchor-correct` + `blend` with the 2PL fit; the other rows are reported but are not a post-hoc selection.

## Predictions (written before scoring)

1. `stratified` achieves a mean tau of at least 0.85 and MAE below 0.03 on the 70/21 splits (the per-scenario means are close to unbiased and models differ by a lot).
2. Pooling the 10 scenarios into one ability dimension fits badly for BLEU / F1 scenarios, so `p-irt` alone is not better than `anchor-mean` for `anchor-correct`. [PREDICTION]
3. The headline method is within 0.03 tau of `stratified` in either direction; "no detectable difference" is the most likely outcome under the decision rule; I would not be surprised if it loses on MAE.
4. `random` (unstratified) is worse than `stratified` on MAE.
5. 1PL and 2PL give p-irt MAE within 0.005 of each other.
