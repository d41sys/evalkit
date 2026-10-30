# SOTA review: evalkit against the evaluation harnesses and methodology papers of 2023-2026

Snapshot 2026-10-26. evalkit is a model-free evaluation harness (statistics layer over per-item results), so "head-to-head on the same public benchmark" means: feed a public leaderboard's own per-item results through evalkit and compare what comes out with what the leaderboard published. No model was run for this review. The protocol was committed before the final scoring run: [protocol-helm-lite.md](protocol-helm-lite.md).

**Update after this snapshot:** evalkit now has clustered standard errors (Miller 2024 formula), a cluster bootstrap, a cluster sign-flip test, a design effect in the power functions, multi-sample averaging and pass^k; see the README section "Clustered standard errors, multi-sample runs, pass^k" and [protocol-clustered-se.md](protocol-clustered-se.md). Statements below that evalkit has no clustered SE or no repeat variance describe the snapshot, not the current code (repeat samples are now averaged per item; seed-to-seed variance of a model is still not modelled).

**Update after this snapshot (judge):** evalkit now has an LLM-as-judge scorer, `evalkit judge` ([judge.py](../src/evalkit/judge.py)): pointwise rubric (1-10 or custom) and pairwise A/B/tie, both presentation orders with inconsistent verdicts resolved to tie and a position-flip rate, an optional reference answer, a length-bias diagnostic, and a disk call cache. It was validated against MT-Bench human judgments (1,000 test items, 72 questions, cluster-bootstrap CIs): agreement with humans 67.8% (S1) / 86.0% (S2), level with the released GPT-4 verdicts on the same items (+2.5 pp [-0.2, +5.3] / +0.6 pp [-1.5, +2.8]); see the README section "LLM-as-judge with bias controls" and [protocol-judge-mtbench.md](protocol-judge-mtbench.md). Self-preference is not controlled, and there is still no PPI-style correction of judge bias (PPR, StratPPI, Lee et al.). Statements below that evalkit has no judge describe the snapshot, not the current code, except row 9g, which is updated.

**Judge reference (audit 2026-10-30).** The reference stays GPT-4 (Zheng et al. 2023 Table 5: 66% S1 / 85% S2). The judge's 67.8% / 86.0% against GPT-4's 65.2% / 85.4% on the same 1,000 items is within noise, so nothing here claims "above GPT-4". D3 ([arXiv 2410.04663](https://arxiv.org/html/2410.04663v4)) reports 86.3% (SAMRE) / 85.1% (MORE) "accuracy" on MT-Bench, but on a different protocol (single-judge baseline 72.5% on a 120-question set): not comparable with S1/S2. Prometheus 2 ([arXiv 2405.01535](https://arxiv.org/html/2405.01535), Table 4: Prometheus-2-8x7B 55.07 with ties / 71.96 without; GPT-4-1106 60.38 / 79.90) and the Self-Taught Evaluator ([arXiv 2408.02666](https://arxiv.org/html/2408.02666): 78.9 on non-tie examples averaged over both orders, GPT4-0125 79.1) are not on S1/S2 (own tie handling, order averaging).

Sections: 1 summary, 2 empirical replication on HELM Lite, 3 numbers that are not comparable, 4 release state, 5 feature matrix, 6 Miller 2024, 7 papers and systems, 8 what the SOTA does that evalkit does not, 9 notes, sources and weak spots.

## 1. Summary

1. **Replication works.** Per-item HELM Lite v1.13.0 results pushed through `evalkit import-helm` reproduce all 909 published model x scenario scores (max difference 1e-15) and the published mean-win-rate order.
2. **evalkit adds what HELM's table lacks.** The published table has one point value per cell and 91 distinct ranks. evalkit's paired test with Holm resolves 41 of the 90 adjacent pairs, and only 25 of those in the published direction (16 are resolved the other way under pooled-item weighting); the data supports 42 tie groups, not 91. HELM's own statistic, bootstrapped, holds its adjacent order in at least 95% of resamples for 9 of 90 pairs.
3. **evalkit loses on default metric fidelity, and now has a mode that matches.** In its default mode exact match is 99.7-100% item-identical to HELM (the article-stripping bug, `'The'` credited for gold `A`, is fixed), token F1 only 59-80%, GSM8K numeric match is more lenient; pooled model means differ by at most 0.013 and the model order agrees (Kendall tau 0.89-1.00). **Update (Phase K):** `--metric-mode helm` ([helm_compat.py][ek-hc]) is 100.0000% item-identical on all 81,543 instances of the 8 text scenarios and equal to HELM's `ece_10_bin` on 6 of 6 runs; MATH (LaTeX equivalence) and WMT (BLEU) are not covered. See 2.2.
4. **evalkit's feature gaps, after Phase K and Phase M.** Added since the snapshot: clustered SE, multi-sample averaging and pass^k, an LLM-as-judge scorer (with a judge panel and a self-preference estimate), Bradley-Terry with bootstrap CIs, a contamination probe, a Min-K% Prob demo, and **1PL/2PL IRT anchor-item subset selection** (tinyBenchmarks style on HELM Lite; 100 anchors reproduce the 91-model ranking at Kendall tau ~0.84-0.85). Still missing: judge-aware inference (PPI-style), adaptive testing (online item generation), label audit, agent evals, seed/run variance (section 8). The matrix (section 5) cites what was checked for the other tools; rows 13 to 15 were not checked for them.
5. **Rerun with clusters and Bradley-Terry (Phase K, [protocol](protocol-rankings.md)).** HELM Lite has almost no shared sources (8 passage clusters, 17 items), so passage-clustered verdicts are unchanged (0 of 90 adjacent verdicts differ). Treating the 22 benchmark subsets as clusters (a sensitivity analysis, an upper bound) cuts the resolved adjacent pairs from 41 to 8. Bradley-Terry on the pooled items agrees with the published order at Kendall tau 0.866 (predicted at least 0.9: wrong) and holds the adjacent order in at least 97.5% of resamples for 41 of 90 pairs, against 5 of 90 for HELM's own statistic; the two do not measure the same thing (section 2.3).
6. **Two things were not done.** The Open LLM Leaderboard per-item `details` datasets are gated (HTTP 401 without a Hugging Face login) so there is no `import-openllm`; the Chatbot Arena Elo-vs-Bradley-Terry comparison was not attempted (reasons in section 3; a Bradley-Terry fit now exists, `evalkit rank`, but was not run on Arena votes).

## 2. Empirical replication on HELM Lite v1.13.0

Data: 91 models, 10 scenarios, 10,200 instances per model (release `summary.json` date 2025-01-10; published table [core_scenarios.json](https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/groups/core_scenarios.json), columns "Mean win rate" and the 10 scenario scores; schema [schema.json](https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/schema.json)). Per-instance values and predictions come from each run's `display_predictions.json` in the same bucket. Full generated reports: [helm-lite-study.md](results/helm-lite-study.md), [helm-lite-metric-check.md](results/helm-lite-metric-check.md), [top-8 all-pairs](results/helm-lite-top8-all-pairs.md), [top-8 leaderboard](results/helm-lite-top8-leaderboard.md). Reproduce with the commands in the README.

**Latest release.** v1.13.0 is the latest HELM Lite release: the [bucket listing](https://storage.googleapis.com/storage/v1/b/crfm-helm-public/o?prefix=lite/benchmark_output/releases/&delimiter=/) shows 14 releases (v1.0.0 to v1.13.0), the last dated 2025-01-10 (`summary.json`). No newer Lite release exists, so the ranks are unchanged. HELM Capabilities has newer releases, but it is a different benchmark, not a Lite replacement. HELM's maintenance-mode notice is in section 4.

### 2.1 Same numbers: evalkit recomputation vs HELM's published table

| Check | evalkit (from per-item data) | HELM published | Match |
|---|---|---|---|
| Per-scenario score, 909 model x scenario cells | recomputed (mean of subset means) | table cells | max abs diff 6e-16 (NQ closed), 1e-15 (NQ open), 0 for 7 scenarios, 2e-16 (WMT) |
| Mean win rate (HELM's rule, ties half) | recomputed from published columns | column "Mean win rate" | max abs diff 1.1e-16; order recomputed from instances identical |
| `pass@k` estimator | `estimate_pass_at_k` | `pass_at_k_estimator` (`code_metrics.py`) | identical on the unit-test grid and against exhaustive enumeration; HELM Lite has no code scenario, so no leaderboard value |
| ECE, 1 bin (OpenbookQA and MedQA runs, 3 models with log-probs) | `expected_calibration_error(n_bins=1)` | `ece_1_bin` in `stats.json` | 6 of 6 runs equal to 4 decimals |
| ECE, 10 bins | equal-width (default); `--metric-mode helm` equal-mass (Phase K) | `ece_10_bin` (equal-mass, external `calibration` package) | default: 4 of 6 equal to 4 decimals, two differ by 0.002 and 0.0034; helm mode: 6 of 6 equal to 1e-9 |

### 2.2 Same items, different metric implementation (12 models, 81,543 scored instances)

Predictions re-scored with evalkit's metric and compared with the value HELM stored for the same instance ([report](results/helm-lite-metric-check.md); HELM definitions from [evaluate_reference_metrics.py](https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/evaluate_reference_metrics.py)). evalkit's metric code was not changed.

| Scenario | evalkit metric | Instances | Identical to HELM | evalkit higher / lower | Mean abs diff | Kendall tau of model means |
|---|---|---|---|---|---|---|
| OpenbookQA | exact_match | 6,000 | 99.93% | 4 / 0 | 0.0007 | 0.98 |
| MMLU | exact_match | 6,168 | 99.72% | 17 / 0 | 0.0028 | 0.92 |
| MedQA | exact_match | 6,036 | 99.97% | 2 / 0 | 0.0003 | 1.00 |
| LegalBench | exact_match | 24,079 | 100.00% | 0 / 0 | 0.0000 | 1.00 |
| NarrativeQA | f1_score | 4,260 | 58.85% | 692 / 1,061 | 0.0321 | 0.97 |
| NQ open-book | f1_score | 12,000 | 74.95% | 936 / 2,070 | 0.0220 | 0.97 |
| NQ closed-book | f1_score | 12,000 | 79.87% | 1,059 / 1,357 | 0.0209 | 1.00 |
| GSM8K | numeric_match | 11,000 | 98.60% | 146 / 8 | 0.0140 | 0.89 |

Causes, from the disagreeing items:

- **Exact match: article stripping collided (fixed after this review; metric-check now 100% identical).** All 23 MC disagreements are prediction `The` against gold letter `A`: evalkit's `normalize_text` removes articles, so "A" and "The" both normalise to the empty string and match. HELM scores 0. HELM normalises lower, punctuation, articles, whitespace; evalkit lower, articles, punctuation, whitespace (HELM's `normalize_text` order is from the same file). This is a bug class for letter-answer tasks.
- **F1.** evalkit counts a `\w+` multiset with no article removal; HELM runs nltk `f_measure` on sets of normalised whitespace tokens. Item values differ in 20-41% of instances (mean absolute item difference 0.02-0.03), but the pooled means differ by at most 0.008 and keep the model order (tau 0.97-1.00). Aggregate agreement does not imply item-level agreement, which is what paired tests consume.
- **GSM8K.** evalkit treats numerically equal strings as equal (`7.00` equals `7`); HELM compares the last number as a string. evalkit is higher on 146 items and lower on 8.
- Not compared: MATH (needs LaTeX equivalence, evalkit has none) and WMT (BLEU; predictions not kept).

### 2.3 Resolvability of the published ranking

Pooled paired tests over the items both models share (`compare --all-pairs` logic, `compare_pairs`: sign-flip randomisation, 10,000 draws, seed 0, Holm within each rank-distance family). Full table, all 90 adjacent pairs, in [helm-lite-study.md](results/helm-lite-study.md).

| Rank distance | Pairs | Resolved (Holm p < 0.05) | of which pooled mean favours the lower-ranked model | Median n for 80% power (unresolved pairs) |
|---|---|---|---|---|
| 1 (adjacent) | 90 | 41 (46%) | 16 | 35,576 |
| 2 | 89 | 49 (55%) | 16 | 26,543 |
| 3 | 88 | 52 (59%) | 11 | 35,125 |
| 5 | 86 | 56 (65%) | 6 | 40,961 |
| 10 | 81 | 68 (84%) | 2 | 35,293 |

- HELM publishes 91 distinct ranks; evalkit's tie groups (a new group only when resolved from the model above) number 42.
- The pooled test weights a scenario by its instance count. HELM's mean win rate is scenario-balanced and rank-based. The two can disagree about the order, which is why 16 resolved adjacent pairs point the other way (for example Claude 3.5 Sonnet 20241022 at published rank 9 versus Gemini 1.5 Pro (002) at rank 10, pooled difference -1.8 points, Holm p = 0.009). Neither weighting is "the truth"; the published ranking depends on a weighting choice that the table does not show.
- HELM's own statistic, with a stratified item bootstrap (1,000 resamples, no multiplicity correction): the published order of an adjacent pair holds in at least 97.5% of resamples for 5 of 90 pairs, 95% for 9, 90% for 19; median 95% rank interval is 6 ranks wide and 2 of 91 models have a single-rank interval.
- Top of the table (published mean win rate): GPT-4o 2024-05-13 0.938, GPT-4o 2024-08-06 0.928, DeepSeek v3 0.908, Claude 3.5 Sonnet 20240620 0.885, Amazon Nova Pro 0.885. Among the top 8 published models, 28 pairs: 11 resolved, 17 unresolved ([all-pairs table](results/helm-lite-top8-all-pairs.md)); in `evalkit leaderboard` (macro mean order) the first six models form one tie group ([top-8 leaderboard](results/helm-lite-top8-leaderboard.md)).

### 2.4 Limits of this replication

- One leaderboard, one release, one weighting of scenarios. Pooled micro-averaging is evalkit's weighting; HELM's is macro and rank-based, so the "resolved" counts answer "is the mean item-score gap resolved", not "is HELM's statistic's order resolved" (that is the bootstrap line).
- Items within a scenario subset are treated as independent in the tables of 2.2 and 2.3 (computed at the snapshot). The Phase K rerun with clusters is in 2.5: HELM Lite has almost no shared sources, so passage clusters change nothing, and a subset-cluster sensitivity analysis changes a lot but is an upper bound.
- Imported rows carry no confidence, so the ECE and Brier columns of `evalkit leaderboard` show constants (0.500 / 0.250) and must be ignored for imported runs. The Elo column is O(items x models^2) and was only run on the top-8 subset.
- Data budget: the first fetch downloaded about 0.7 GB of raw JSON before compaction, above the 300 MB guidance (the per-run files were larger than estimated). About 37 MB remain on disk, gitignored.

### 2.5 Phase K: item-identical metrics, clusters and Bradley-Terry

Protocol before the scored runs: [protocol-rankings.md](protocol-rankings.md) (predictions and outcome included). Same data and seed.

- **Metric fidelity.** In `--metric-mode helm` the 8 text scenarios are 100.0000% item-identical to HELM (81,543 of 81,543); the default mode is unchanged and still 58.85-100% by scenario. ECE equals `ece_10_bin` on 6 of 6 runs. Not covered: MATH, WMT, models without log-probs. ([report](results/helm-lite-metric-check.md))
- **Clusters.** Passage clusters (NarrativeQA 355 distinct passages, NQ open-book 991 for 1,000 questions, no other scenario carries a source id): 0 of 90 adjacent verdicts change, other rank distances 2, 1, 1, 0 of 89, 88, 86, 81. Subset clusters (22 subsets of MMLU, LegalBench, MATH, WMT as clusters; the subsets are fixed strata, so this is a sensitivity bound): 8 of 90 adjacent pairs resolved (from 41), 9 tie groups (from 42), design effect about 40. ([study, sections 5](results/helm-lite-study.md))
- **Bradley-Terry.** Pooled-item MLE, 200 bootstrap resamples, Kendall tau against the published order 0.866 (prediction of at least 0.9 was wrong); adjacent order holds in at least 97.5% of resamples for 41 of 90 pairs (item bootstrap; 42 with passage clusters), against 5 of 90 for HELM's mean-win-rate bootstrap; median 95% rank interval 4 ranks (HELM statistic: 6). The statistics differ (pooled item wins against scenario-balanced rank-based mean win rate), and the coverage of the BT bootstrap with item-model interaction was not simulated. DeepSeek v3 is published 3rd and BT 10th (8-12). ([study, section 6](results/helm-lite-study.md))
- **Not done here.** No Arena votes, no Open LLM Leaderboard per-item data, no HELM scenarios with source clusters; so cluster-aware ranking is exercised on HELM Lite only as a (null) passage check and a sensitivity bound.

## 3. Published numbers that are not comparable

| Number | Source | Why it is not in the comparison |
|---|---|---|
| Open LLM Leaderboard v2 per-item scores | [open-llm-leaderboard/*-details](https://huggingface.co/open-llm-leaderboard) datasets | Gated (`gated: auto`); data files return HTTP 401 without a Hugging Face login (checked 2026-10-26). The format could not be verified against real files, so there is no importer. |
| Chatbot Arena: Bradley-Terry ranking vs Elo | [Chiang et al. 2024, arXiv 2403.04132](https://arxiv.org/abs/2403.04132) | Not attempted: the public 55k battles CSV is 184 MB, evalkit has no Bradley-Terry fit, and the published ranking comes from a larger private vote set. A fair test needs both. |
| Clustered SE vs naive SE: 1.34 vs 0.44 on DROP, 1.62 vs 0.86 on MGSM, 0.51 vs 0.46 on RACE-H (Table 4) | [Miller 2024, arXiv 2411.00640](https://arxiv.org/html/2411.00640) | Anthropic-model data not public; evalkit has no clustered SE to compare. |
| CLT interval covers 92.5% at N = 100 (Fig. 2) | [Bowyer et al. 2025, arXiv 2503.01747](https://arxiv.org/abs/2503.01747) | Different simulation design from evalkit's `stats-check`; evalkit's coverage figures in the README are for its own intervals and generators. |
| Rank-location CIs on HELM data | [HELM efficient_benchmarking.md](https://github.com/stanford-crfm/helm/blob/main/docs/efficient_benchmarking.md) (credited to Perlitz et al. 2023) | HELM Classic data and a different resampling unit; numbers not extracted for this review. |
| tinyBenchmarks 1.9% error at 100 items; metabench 1.24% RMSE at 858 items | [2402.14992](https://arxiv.org/abs/2402.14992), [2407.12844](https://arxiv.org/abs/2407.12844) | IRT-based benchmark compression; evalkit has no IRT. |

## 4. Release and maintenance state

| Tool | Latest release seen (date) | Maintenance state seen |
|---|---|---|
| evalkit | local repo, no release opened | n/a |
| lm-eval | [v0.4.13, 2026-08-31][lm-rel] | `main` is `0.4.14.dev0` ([commit 2026-08-31][lm-commits]); latest commit I saw is 2026-09-14 ([commits][lm-commits]). Active. |
| HELM (crfm-helm) | [v0.5.16, 2026-04-30][helm-rel] | "HELM entered maintenance mode on June 1, 2026"; "no new features will be added" ([policy][helm-maint]). |
| inspect_ai | [0.3.285, 2026-10-25][in-rel] | Releases every few days (0.3.276 on 2026-10-02 to 0.3.285 on 2026-10-25) ([releases][in-rel]). Active. |
| OpenAI evals | [tag 3.0.1, 2024-05-01][oa-tags] | Latest commit I saw is 2026-04-14 (pin pre-commit hooks) ([commits][oa-commits]); README points to the Dashboard and says "not accepting evals with custom code" ([README][oa-readme]). Low activity. |
| promptfoo | [0.125.1, 2026-10-25][pf-rel] | Active. README: "Promptfoo is now part of OpenAI. Promptfoo remains open source and MIT licensed" ([README][pf-readme]). |
| DeepEval | [python-v4.3.1, 2026-10-16][de-rel] | Active ([releases][de-rel]; 10,444 commits on [repo page][de-readme]). |

## 5. Feature matrix

Legend: ✓ present · partial · ✗ not present (a ✗ cites what was checked) · unverified. Cell = verdict + link.

| # | Feature | evalkit | lm-eval | HELM | inspect_ai | OpenAI evals | promptfoo | DeepEval |
|---|---|---|---|---|---|---|---|---|
| 1 | Per-item results saved | [✓ `results.jsonl`][ek-rec] | [✓ `--log_samples`][lm-iface] | [✓ `per_instance_stats.json`][helm-tut] | [✓ `EvalSample` per sample][in-logs] | [✓ `LocalRecorder` events][oa-record] | [✓ `-o` json/jsonl/csv][pf-cli] | [✓ `results_folder` `test_run_*.json`][de-flags] |
| 2 | SE / CI for one model's score | [partial: bootstrap CI (percentile/BCa/studentized), no CLT SE; Wilson in README][ek-ci] | [partial: SE only, no CI; CLT for `mean`, bootstrap for F1/perplexity/BLEU][lm-stderr] | [✗ `Stat` has mean + population stddev only][helm-stat] | [✓ `stderr()` CLT, `bootstrap_stderr()`, `ci()`, `ci_wilson()`][in-std] | [partial: "bootstrap" std from half-size subsamples][oa-metrics] | [✗ no CI/SE in docs checked][pf-cli] | [✗ no CI/SE in docs checked][de-intro] |
| 3 | Paired comparison, same items | [✓ paired bootstrap CI][ek-paired] | [✗ checked `metrics.py`, `evaluator_utils.py`][lm-metrics] | [✗ checked `summarize.py`][helm-sum] | [✗ checked llms-full.txt][in-full] | [✗ checked `metrics.py`][oa-metrics] | [✗ checked CLI/config docs][pf-cli] | [✗ checked 4 docs pages][de-intro] |
| 4 | Significance test / p-value | [✓ sign-flip randomisation + exact sign; auto-switch to bootstrap-t on asymmetric differences (`evalkit stats-check` M-E1 fix)][ek-rand] | [✗ same files as row 3][lm-metrics] | [✗][helm-sum] | [✗][in-full] | [✗][oa-metrics] | [✗][pf-cli] | [✗][de-intro] |
| 5 | Multiple-comparison correction | [✓ Holm][ek-holm] | [✗][lm-metrics] | [✗][helm-sum] | [✗][in-full] | [✗][oa-metrics] | [✗][pf-cli] | [✗][de-intro] |
| 6 | Power / MDE / sample size | [✓ MDE + n, exact McNemar for 0/1][ek-mde] | [✗][lm-metrics] | [✗][helm-sum] | [✗][in-full] | [✗][oa-metrics] | [✗][pf-cli] | [✗][de-intro] |
| 7 | Clustered SE | [✓ clustered SE, cluster bootstrap, cluster sign-flip test, design effect in power (added after the snapshot; the leaderboard CI and tie groups use it too)][ek-agg] | [✗ `acc_all_stderr` groups by question, not a cluster SE][lm-stderr] | [✗][helm-stat] | [✓ `stderr/ci/ci_wilson(cluster=)`][in-cluster] | [✗][oa-metrics] | [✗][pf-cli] | [✗][de-intro] |
| 8 | Repeats / epochs, SE-aware | [partial: repeat samples are averaged per item and enter the clustered statistics (added after the snapshot); seed-to-seed variance of a model is not modelled][ek-runner] | [partial: `repeats` + filters; SE combination unverified][lm-repeats] | [partial: `--num-train-trials`; SE combination unverified][helm-trials] | [✓ `epochs` + reducers; metrics see reduced scores][in-epochs] | [✗ checked `metrics.py`][oa-metrics] | [partial: `--repeat`, no SE][pf-cli] | [partial: `-r` repeats, no SE][de-flags] |
| 9a | Exact match (normalisation) | [✓ default `exact_match` is SQuAD-style `normalize_text` (HELM's step order differs; 99.7-100% item-identical); `--metric-mode helm` is HELM's definition, 100.0000% item-identical on 81,543 instances of 8 text scenarios][ek-hc] | [partial: HF-evaluate EM, flags for case/punct/digits][lm-em] | [✓ QuAC/SQuAD-style `normalize_text`][helm-ref] | [✓ `exact()` "normalize"; details unverified][in-scorers] | [✓ `normalize` + `fuzzy_match`][oa-utils] | [partial: `equals`; optional Unicode normalisation only][pf-det] | [✗ not in metric list][de-intro] |
| 9b | Token F1 | [✓ default `f1_score` is a `\w+` multiset (59-80% item-identical to HELM); `--metric-mode helm` is HELM's set-based F1, item-identical in the metric check][ek-hc] | [partial: corpus-level sklearn F1][lm-metrics] | [✓ set-based token F1][helm-ref] | [✓ `f1()`][in-scorers] | [✓ `f1_score`][oa-utils] | [partial: `tool-call-f1`, user-defined F-score][pf-det] | [✗ custom only][de-intro] |
| 9c | BLEU / ROUGE / chrF | [✓ own BLEU-4, ROUGE-L, chrF][ek-cls] | [partial: BLEU, chrF, chrF++, TER; ROUGE not in `metrics.py`][lm-metrics] | [✓ BLEU-1/4, ROUGE-1/2/L][helm-ref] | [✗ no hit for bleu/rouge/chrf in guide][in-guide] | [✗ checked `metrics.py`][oa-metrics] | [✓ BLEU, ROUGE-N/L/S][pf-det] | [partial: custom via `scorer` module][de-intro] |
| 9d | pass@k (estimator) | [✓ Chen 2021 unbiased; identical to HELM's estimator in `tests/test_evalkit_helm.py`][ek-pass] | [partial: `pass_at_k` in humaneval utils; estimator unread][lm-he] | [✓ `pass_at_k_estimator`][helm-ref] | [✓ `pass_at` reducer, cites Chen 2021][in-red] | [✗][oa-metrics] | [✗ not in deterministic page][pf-det] | [✓ HumanEval benchmark, `1 - C(n-c,k)/C(n,k)`][de-he] |
| 9e | ECE / Brier / calibration | [✓ ECE (15 equal-width bins), Brier; `--metric-mode helm` adds HELM's equal-mass `ece_10_bin`, equal to HELM on 6 of 6 runs (1e-9)][ek-hc] | [partial: Brier yes, ECE no][lm-metrics] | [partial: ECE 10-bin (equal-mass), selective, Platt; no Brier][helm-cal] | [✗ no ECE/Brier hit in guide][in-guide] | [✗][oa-metrics] | [✗][pf-det] | [✗ not in metric list][de-readme] |
| 9f | Perplexity / log-likelihood scoring | [✓ perplexity; logprob MCQ options][ek-ppl] | [✓ perplexity, bits/byte, loglikelihood MCQ `acc`][lm-metrics] | [✓ perplexity, bits/byte][helm-ppl] | [✓ `perplexity()`, needs `prompt_logprobs`][in-ppl] | [✗][oa-metrics] | [partial: `perplexity` assertion on model's own output][pf-det] | [✗][de-readme] |
| 9g | LLM-as-judge | [✓ pointwise + pairwise judge, position / reference / length controls, validated on MT-Bench; a Haiku+Sonnet+Opus panel and a self-preference estimate (no detectable effect, 160-item subsample); added after the snapshot][ek-judge] | [unverified: none in `metrics.py`; tasks not scanned][lm-metrics] | [✓ `llm_jury_metrics.py`, judges in Omni-MATH/WildBench][helm-jury] | [✓ `model_graded_qa/fact`][in-judge] | [✓ model-graded evals][oa-readme] | [✓ `llm-rubric`, g-eval, etc.][pf-idx] | [✓ G-Eval, DAG][de-intro] |
| 9h | pass^k | [✓ `pass^k` and multi-sample averaging (added after the snapshot)][ek-pass] | [✗ checked `metrics.py`][lm-metrics] | [✗ grep `code_metrics.py`, `evaluate_reference_metrics.py`][helm-ref] | [✓ `pass_k` reducer][in-red] | [✗][oa-metrics] | [✗][pf-det] | [✗][de-he] |
| 10 | Leaderboard tie groups / rank uncertainty | [✓ `assign_tie_groups`][ek-ties] | [✗ checked `evaluator_utils.py`][lm-evu] | [✗ mean win rate only; rank CI table is from a cited IBM paper][helm-eff] | [✗][in-full] | [✗][oa-metrics] | [✗][pf-cli] | [✗][de-intro] |
| 11 | Self-validation of stats (MC coverage / type-I) | [✓ `stats-check`][ek-sc] | [✗ none found in repo listing][lm-repo] | [✗ none found in repo listing][helm-repo] | [✗ none found; not exhaustively searched][in-repo] | [✗ none found][oa-readme] | [✗ none found][pf-readme] | [✗ none found][de-readme] |
| 12 | Bradley-Terry / Elo | [✓ Bradley-Terry MLE with item or cluster bootstrap CIs and rank intervals (`evalkit rank`, `leaderboard --bt`), plus interleaved Elo; added after the snapshot][ek-rank] | [✗ no hit for elo/bradley in `metrics.py`][lm-metrics] | [✗ win rate only][helm-sum] | [✗ no hit in guide][in-guide] | [✗][oa-metrics] | [✗][pf-cli] | [✗ "Arena G-Eval" is an LLM pairwise judge, not BT/Elo][de-intro] |
| 13 | Contamination probe (perturbed-number variants, deterministic gold) | [✓ GSM-Symbolic-style number-only probe with cluster-bootstrap drop CI; n=140, no detectable drop above about 3.5 pp for 2 Claude models; added after the snapshot][ek-cont] | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) |
| 14 | Min-K% Prob membership score | [partial: demo with a 0.5B local model (optional extra), AUROC 0.535 [0.477, 0.594] on 132 GSM8K questions vs paraphrases, no detectable effect; a method demo, not an audit][ek-mink] | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) |
| 15 | IRT anchor-item subset selection (tinyBenchmarks style) | [✓ 1PL / 2PL IRT in numpy, ~100-item anchor subset selection evaluated on HELM Lite with 50 70/21 model splits; added after Phase K][ek-irt] | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) | unverified (not checked in this update) |

## 6. Miller 2024 recommendations vs. evalkit

Paper: [arXiv 2411.00640 abs][miller-abs] (v1, 2024-11-01), [HTML][miller-html]. Section numbers below are from the HTML.

| Recommendation | Miller § | evalkit | Link |
|---|---|---|---|
| SE of the mean from the CLT; report SE next to the mean; CI = mean ± 1.96·SE | §2.1 (eq. 1-3) | partial: bootstrap CIs, no CLT SE. Miller calls bootstrap "unnecessary" outside complex schemes | [ek-ci] |
| Clustered SE when questions share a passage | §2.2 (eq. 4), App. A | ✗ | [ek-agg] |
| Resample answers K times, average per question, SE over question means | §3.1 | ✗ no epochs | [ek-runner] |
| Use next-token probabilities to remove conditional variance | §3.2 | partial: log-prob option scoring exists, but the argmax is scored 0/1, not the probability | [ek-readme-hf] |
| Do not lower temperature to cut variance | §3.3 | n/a: greedy decoding for HF models | [ek-readme-hf] |
| Unpaired difference: SE = sqrt(SE_A² + SE_B²) | §4.1 | ✗ `compare` needs shared examples | [ek-paired] |
| Paired differences, paired SE, report correlation | §4.2 (eq. 7-8) | partial: paired bootstrap CI + randomisation test; correlation not reported (unverified) | [ek-paired] |
| Power analysis: n for (α, power, δ), MDE | §5 (eq. 9-10), App. B | ✓ MDE and n; exact McNemar for 0/1, normal approx otherwise | [ek-mde] |
| Cluster-adjusted sample size | App. C | ✗ | [ek-agg] |

## 7. Papers and systems, 2022-2026

Compiled 2026-10-26. Every number below was read on the linked page; "(HTML)" = arXiv HTML render, which gives section/table anchors. Dates are arXiv v1 unless stated; blog dates come from the page URL or HF API as noted. Items I could not verify say `unverified`.

evalkit baseline used for the "Difference" column (checked in `src/evalkit/aggregate.py`, `statscheck.py`, `README.md`): per-model bootstrap CI (percentile / BCa / studentized, `auto` = studentized for n < 400 and ≤ 50% tied pairs) and Wilson intervals; paired bootstrap CI + exact sign test + sign-flip randomisation test; Holm over model pairs; MDE / sample size (continuous z-formula, exact McNemar for 0/1); tie groups; `stats-check` Monte-Carlo validation; ECE/Brier/perplexity; Elo; unbiased pass@k. A source grep for `cluster|bradley|judge|irt|contamin` in `src/evalkit` returns nothing.

| System / paper | Date | What it does | Headline result (location) | Difference from evalkit | Link |
|---|---|---|---|---|---|
| **Miller, "Adding Error Bars to Evals"** | 2024-11-01 ([abs](https://arxiv.org/abs/2411.00640)) | Treats eval questions as a draw from a super-population. Gives CLT standard errors, **clustered SEs**, resampling K answers per question, paired question-level differences with score correlation, and a sample-size / MDE formula. Recommends reporting pairwise differences, SEs and correlations. | **Table 4 (§2.2, real Anthropic-model data):** clustered SE vs naive SE = 1.34 vs 0.44 on DROP (3.05×), 1.62% vs 0.86% on MGSM (1.88×), 0.51% vs 0.46% on RACE-H (1.10×). **§5:** detecting δ = 3 pts at α = 0.05, 80% power, ω² = 1/9 needs n ≈ 969; with σ²ₐ = σ²ᵦ = 1/6, ω² = 1/9, n = 198, raising K from 1 to 10 cuts MDE from 13.2% to 7.5%. | evalkit has the paired CI and a paired MDE / n formula of the same z-sum form. It has **no clustered SE** (examples are treated as independent), no per-question repeat-sampling variance term (σ²/K), and no correlation reporting. Miller's HTML has no mention of Holm, Wilson, permutation, McNemar or sign tests (0 hits each), all of which evalkit ships. | [HTML](https://arxiv.org/html/2411.00640) |
| **Bowyer, Aitchison, Ivanova, "Don't use the CLT in LLM evals with fewer than a few hundred datapoints"** (ICML 2025 spotlight position paper) | 2025-03-03 ([abs](https://arxiv.org/abs/2503.01747)) | Simulates interval coverage for single models, independent and paired comparisons, clustered questions, and non-mean metrics (F1). Recommends Wilson / Clopper-Pearson (frequentist) or Beta-Bernoulli and paired/clustered Bayesian credible intervals; code in `bayes_evals`. | **§3.1, Fig. 2:** at N = 100 a nominal 95% CLT interval covers only 92.5% (z 1.96 vs 1.78); CLT and percentile bootstrap both under-cover and are wider than needed for their coverage; only Wilson and Bayesian intervals are calibrated at small N. **Fig. 1:** at N = 20 CLT intervals leave [0, 1] or collapse to zero width. **§3.4:** non-Bayesian paired methods "severely underperform" at small N. | evalkit already has Wilson and second-order bootstrap (BCa, studentized) and tests its own coverage in `stats-check`; the paper never tests BCa, studentized, Holm, McNemar or permutation (0 mentions in the HTML). evalkit lacks the Bayesian paired / clustered / F1 intervals; its only small-n rule is the switch to studentized intervals below n = 400. | [HTML v3](https://arxiv.org/html/2503.01747v3) |
| **Madaan et al., "Quantifying Variance in Evaluation Benchmarks"** | 2024-06-14 ([abs](https://arxiv.org/abs/2406.10229)) | Measures seed variance, monotonicity during training, continuous vs discrete metrics, item analysis and IRT, over ~70 models. | **Table 1 (7B seed models):** MMLU seed std 0.57 pts, monotonicity 0.09; MMLU-Cloze std 0.22, monotonicity 0.95. **Table 7:** IRT / IRT++ tiny subsets drop Kendall τ to 0.76 (about 12% of model pairs flip); the 100-point ARC-C subset over-estimates the mean by 7%. | evalkit's CIs cover **item-sampling variance only**. It has no seed / run variance, no monotonicity, no continuous-vs-discrete metric analysis. Its power module answers "how many items", which this paper treats as the main lever, but not "how many seeds". | [HTML](https://arxiv.org/html/2406.10229v1) |
| **Biderman et al., "Lessons from the Trenches on Reproducible Evaluation of Language Models"** (lm-eval-harness) | 2024-05-23 ([abs](https://arxiv.org/abs/2405.14782); text read from v3, 2026-05-31) | Guidance from three years of lm-eval: prompt / format sensitivity, reproducibility checklist (Appendix D incl. "perform statistical significance testing"), bootstrapped standard errors on by default. | **§4.1 Benchmark Lottery, Table 1:** GPT-NeoX-20B on ARC-Easy scores 72.4 ± 1.80% with cloze prompting and 26.5 ± 1.78% with MMLU-style prompting. **§4.3:** bootstrap SE reported by default; it measures question-sampling variation, not run-to-run variation. | evalkit offers more inference (paired tests, Holm, power, tie groups) than lm-eval's default bootstrap SE. lm-eval offers breadth (hundreds of tasks), prompt / format variants and log-prob MCQ scoring (App. B.2); evalkit has log-prob MCQ scoring but no prompt-format sensitivity study. | [HTML v3](https://arxiv.org/html/2405.14782v3) |
| **HELM family:** HELM (Liang et al.), HELM Lite, HELM Instruct, HELM Capabilities | HELM 2022-11-16 ([abs](https://arxiv.org/abs/2211.09110)); Lite 2023-12-19; Instruct 2024-02-18; Capabilities 2025-03-20 (blog dates from URLs) | Multi-metric, scenario-level evaluation (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency). Lite drops to 1 seed, ≤ 1000 instances per scenario, no calibration or perplexity, ranks by **mean win rate**. Instruct uses absolute 1-5 ratings from humans and LM judges. Capabilities uses 5 scenarios, 3 LLM judges for WildBench, and a plain mean score instead of mean win rate. | **HELM abstract:** 30 models × 42 scenarios, 7 metrics; core-scenario coverage per model rises from 17.9% to 96.0%. **Lite blog:** "HELM Classic performed 3 random seeds; HELM Lite uses only 1". **Instruct, Table 4:** instance-level Pearson correlation between evaluator pairs (2 human, 2 LM) is 0.48 to 0.72. **Capabilities, Results:** top scores 0.679 (Gemini 2.0 Flash) vs 0.674 (Claude 3.7 Sonnet) across 22 models; the switch from mean win rate is justified because win rate depends on the model set and is "sensitive to small variations in scenario scores that invert ranks". | evalkit shares ECE/Brier/perplexity (which Lite dropped) and can read HELM Lite per-item data (`src/evalkit/helm.py`) to apply paired tests and tie groups; the pages I read (Lite, Capabilities) report no intervals or tests on the rankings (searched for confidence / bootstrap / standard error / significance: only unrelated hits). evalkit lacks LM-judge scoring, evaluator-agreement analysis, robustness and fairness perturbations. | [HELM](https://arxiv.org/abs/2211.09110), [Lite](https://crfm.stanford.edu/2023/12/19/helm-lite.html), [Instruct](https://crfm.stanford.edu/2024/02/18/helm-instruct.html), [Capabilities](https://crfm.stanford.edu/2025/03/20/helm-capabilities.html) |
| **Inspect AI** (UK AISI) | docs only, undated; read 2026-10-26 | Eval framework with built-in `stderr()` (CLT) incl. **`cluster=` clustered SE**, `bootstrap_stderr()` (1000 resamples default), `ci()` (Student-t default, optional percentile bootstrap, cluster-aware), `ci_wilson()`, `krippendorff_alpha()` for multi-judge agreement, epoch reducers `pass_at_{k}`, `pass_k_{k}`, `at_least_{k}`. | No published numbers (docs). Feature list read on the [Scoring Metrics page](https://inspect.aisi.org.uk/metrics.html). | Inspect has clustered SE, model-graded scorers with judge-agreement metrics, and agent sandboxes, all absent in evalkit. In the scorer reference page I found **no paired test, MDE, or multiple-comparison correction** (0 hits for paired / McNemar / sign test / permutation / randomisation / Holm / Bonferroni), which evalkit provides. | [Metrics](https://inspect.aisi.org.uk/metrics.html), [scorer ref](https://inspect.aisi.org.uk/reference/inspect_ai.scorer.html) |
| **Chiang et al., Chatbot Arena** | 2024-03-07 ([abs](https://arxiv.org/abs/2403.04132)) | Pairwise human votes; **Bradley-Terry MLE** (replaced Elo "because the BT coefficients are better for statistical estimation", §4). CIs by pivot bootstrap and sandwich robust SEs; sandwich deployed. Multiplicity-corrected simultaneous intervals for ranking; active pair sampling. | **Abstract:** > 240K votes. **§6.3:** crowd-vs-expert agreement 72% to 83% (expert-vs-expert 79.4% and 89.8%). **§7.1, Fig. 7:** to reach precision 0.2 on the win matrix, random sampling needs 6,800 votes vs 4,400 adaptive (54% more); for score precision 0.3, 17,200 vs 16,400 (5% more). **App. A:** simulation compares bootstrap and sandwich coverage. | evalkit's Elo is a sequential update with interleaved match order; it has no BT likelihood, no sandwich / bootstrap CIs on ratings, no simultaneous rank intervals, no active sampling, no human-preference data. evalkit's Holm + tie groups are the nearest analogue to the multiplicity-corrected ranking. | [HTML v1](https://arxiv.org/html/2403.04132v1) |
| **Chatzi et al., "Prediction-Powered Ranking of LLMs"** (NeurIPS 2024) | 2024-02-27 ([abs](https://arxiv.org/abs/2402.17826), v3 2024-12-04) | PPI confidence region over pairwise win-probabilities from a small human set + a large LLM-judge set; outputs **rank-sets** with asymptotic coverage guarantee. | **§5 setup:** 14,947 instances, 12 LLMs, 3 judge LLMs. **App. D.2:** baseline coverage of rank-sets built from judge-only comparisons is "close to (or exactly) zero". **§5:** with n = 990 human labels, α = 0.05, PPR with GPT-4 or Claude-3 judges gives a better rank-set-size / intersection trade-off than human-only. | evalkit has no judge and no PPI. Its tie groups are heuristic adjacent-pair groups; PPR gives rank-sets with guaranteed coverage. | [HTML v3](https://arxiv.org/html/2402.17826v3) |
| **Fisch et al., "Stratified Prediction-Powered Inference for Hybrid LM Evaluation"** (NeurIPS 2024) | 2024-06-06 ([abs](https://arxiv.org/abs/2406.04291), v2 2024-12-03) | StratPPI: stratifies autorater data so PPI confidence intervals for mean model performance are tighter; valid with no assumption on the autorater. | **Fig. 2** (K = 10 strata, α = 0.05; Seahorse and other real data): CI width, % reduction vs classical, and effective sample size, with all StratPPI variants beating classical and PPI++. **Fig. 3:** Chatbot Arena win rate with Gemini Ultra as judge; the paper notes judge confidences are poorly calibrated. The numeric values are only in the figures: `unverified` (not extractable as text). | No judge, no human-label + autorater combination, no effective-sample-size accounting in evalkit. | [HTML v2](https://arxiv.org/html/2406.04291v2) |
| **Lee et al., "How to Correctly Report LLM-as-a-Judge Evaluations"** (ICML 2026) | 2025-11-26 ([abs](https://arxiv.org/abs/2511.21140); v4 2026-05-31) | Plug-in correction of judge bias from judge sensitivity / specificity estimated on a human-labelled calibration set; CIs include calibration uncertainty; adaptive calibration allocation; regimes where judge beats human-only. States that error-bar frameworks such as Miller's "assume that LLM evaluators provide ground-truth labels" (v2 related work). | **§7.1, Fig. 5:** judge sensitivity / specificity (0.7, 0.9), calibration m = 200, 10,000 replications, 21 values of θ: naive estimate biased, corrected estimate unbiased with coverage close to 95%. | No judge; evalkit's CIs assume the scorer is exact (true for exact match / pass@k, false for any LM-scored task). | [HTML v4](https://arxiv.org/html/2511.21140v4), [v2](https://arxiv.org/html/2511.21140v2) |
| **Polo et al., tinyBenchmarks** (ICML 2024) | 2024-02-22 ([abs](https://arxiv.org/abs/2402.14992), v2 2024-05-26) | Selects ~100 curated examples per scenario and estimates full-benchmark accuracy with IRT / IRT++; releases tiny Open LLM Leaderboard, MMLU, HELM, AlpacaEval 2.0. | **Fig. 1:** MMLU accuracy from 100 curated items within 1.9% of full (14K). **Fig. 3 / §5:** ≈ 2% average error with 100 items per scenario; MMLU cost down 140× (14K to 100); Open LLM Leaderboard 29K to 180 items (30 per scenario, 160×). | evalkit has no IRT, anchor selection, or adaptive evaluation; its sample-size tool says how many items a *comparison* needs, not how to shrink a benchmark. Madaan et al. (row 3) found these tiny sets raise seed variance. | [HTML v2](https://arxiv.org/html/2402.14992v2) |
| **Kipnis et al., metabench** (ICLR 2025) | 2024-07-04 ([abs](https://arxiv.org/abs/2407.12844), v2 2025-02-20) | Distils ARC, GSM8K, HellaSwag, MMLU, TruthfulQA, WinoGrande (28,632 items) into a sparse benchmark using IRT on > 5000 LLMs; provides ability estimators and non-parametric CIs from local test RMSE. | **Abstract / Fig. 1:** 858 items (< 3% of original); reconstructs each benchmark score with 1.24% RMSE and the total with 0.58% RMSE; one common factor with Spearman r = 0.94 to total score. **§3.2:** four variants "to mitigate contamination and memorization". | No IRT, factor analysis, or contamination-aware item variants in evalkit. | [HTML v2](https://arxiv.org/html/2407.12844v2) |
| **Truong et al., "Reliable and Efficient Amortized Model-based Evaluation"** | 2025-03-17 ([abs](https://arxiv.org/abs/2503.13335)) | IRT over 22 datasets and 172 LMs; a model predicts question difficulty from text (amortised calibration) and a conditional generator writes questions at a target difficulty for adaptive testing. | **§5.3, Fig. 5:** adaptive testing cuts questions by up to 86% vs random testing, 53% on average, at 95% reliability (budget K = 400, 5 repeats). **§5.2:** amortised calibration closely tracks traditional calibration. | evalkit has no adaptive item selection or difficulty model; items are scored identically and the fixed-n power formula is the only efficiency tool. | [HTML v1](https://arxiv.org/html/2503.13335v1) |
| **Vendrow et al., "Do LLM Benchmarks Test Reliability?" (platinum benchmarks)** | 2025-02-05 ([abs](https://arxiv.org/abs/2502.03461)) | Audits 15 saturated benchmarks for label errors and ambiguity, re-labels subsets, then evaluates models on the cleaned "platinum" sets. | **Table 2:** 352 bad questions flagged across the 15 subsets. **§2.2:** up to 30% of examples problematic in SQuAD2.0, HotpotQA, DROP (open-ended answers). **§3.3 / App. C.1:** three models fail > 85% of 100 order-flipped examples where median DROP error is < 3%. | evalkit assumes labels are right: no label-error audit and no per-item flagging. Its strict SQuAD-style exact match is exposed to the multi-reference ambiguity the paper counts. | [HTML v1](https://arxiv.org/html/2502.03461v1) |
| **Open LLM Leaderboard v2** (HF blog) and **BenchScope** | Blog: space last modified 2024-07-01 (HF [API](https://huggingface.co/api/spaces/open-llm-leaderboard/blog)); exact publication date `unverified`. BenchScope 2026-03-31 ([abs](https://arxiv.org/abs/2603.29357)) | Replaces saturated / contaminated benchmarks with IFEval, BBH, MATH lvl 5, GPQA, MuSR, MMLU-Pro; normalises each score so the random baseline is 0 and the max is 100 before averaging and ranking; no benchmark that needs an LLM judge. BenchScope computes "effective dimensionality" of score matrices. | **Blog:** HellaSwag, MMLU, ARC reached human baseline ("saturation"); "signs of contamination"; > 7500 models evaluated in the year. No error bars or confidence intervals appear in the blog (searched). **BenchScope abstract:** the six-score leaderboard behaves like ≈ 2 axes (ED = 1.7); BBH vs MMLU-Pro ρ = 0.96. | evalkit has tie groups to warn against over-reading ranks (the blog has none) but no chance-level normalisation (`macro_average` is a raw unweighted mean), no contamination check, no redundancy diagnostic. | [Blog](https://open-llm-leaderboard-blog.static.hf.space/index.html), [BenchScope](https://arxiv.org/abs/2603.29357) |
| **Rank confidence intervals:** Neuhof & Benjamini, "Quantifying Ranking Uncertainty in LLM Benchmarks"; Sälevä et al., "Beyond statistical significance" | 2026-06-28 ([2607.16259](https://arxiv.org/abs/2607.16259)); 2025-09-26 ([2509.22612](https://arxiv.org/abs/2509.22612), IJCNLP-AACL 2025) | 2607.16259: rank CIs built from directional paired tests (cites Holm), applied to MMLU with subject, question and prompt-variant units. 2509.22612: resampling for model- and data-side variance components, rankings and pairwise differences in multilingual QA / MT / NER. | **2607.16259 §3.1 vs §3.2 (Figs. 1, 2):** treating every (subject, question, prompt) triple as an independent unit gives clearly separated models with non-overlapping CIs; using subjects (N = 57) as the unit makes intervals overlap, e.g. "3 models can be ranked as the fourth from the top"; subject-level variability dominates prompt-level (N_V = 100 variants). **2509.22612 abstract:** ignoring either model-side or data-side variance "substantially" underestimates variability; Table 2 gives per-language pairwise differences ± SE with non-significant ones starred (specific numbers `unverified` for headline use). | evalkit's tie groups are adjacent-pair only, non-transitive (README), and its pairwise test uses the pooled per-example difference, i.e. exactly the "all units independent" analysis that §3.1 says understates uncertainty. evalkit does have Holm and a stratified item bootstrap of mean-win-rate rank (`rank_bootstrap` in `src/evalkit/helm_study.py`). It has no all-pairs simultaneous rank CIs, no subject / language clustering, no variance components. | [2607.16259 HTML](https://arxiv.org/html/2607.16259v1), [2509.22612 HTML](https://arxiv.org/html/2509.22612v2) |

## 8. What the SOTA does that evalkit does not

1. **Clustered / hierarchical uncertainty.** Miller's Table 4 shows clustered SEs up to 3.05× naive (DROP), and the rank-CI paper shows that treating questions as independent turns overlapping ranks into "clearly distinguishable" ones. evalkit treats every example, and pooled tasks, as independent.
2. **Small-n intervals beyond Wilson.** Bowyer (§3) finds CLT and percentile bootstrap under-cover at N ≈ 100 and recommends Bayesian paired and clustered intervals; evalkit stops at Wilson (single model) and studentized / BCa bootstrap (paired).
3. **Bradley-Terry with sandwich or bootstrap CIs and simultaneous rank intervals** (Arena §4, §7.1, App. A), plus active pair sampling (Fig. 7); evalkit's interleaved Elo has no uncertainty.
4. **Judge-aware inference** (PPR, StratPPI, Lee et al.): small human set + large LLM-judge set gives valid CIs and rank-sets. evalkit now has a judge and a human-agreement check on MT-Bench (see the update note), but it does not use the human labels to correct the judge's bias or to build rank-sets, so none of this is implemented yet.
5. **Model-based efficient evaluation (IRT, adaptive testing):** tinyBenchmarks, metabench, amortised evaluation (53% average question saving at 95% reliability). **Update (Phase M):** evalkit implements 1PL and 2PL IRT fitting in numpy and anchor-subset selection (`evalkit irt-subset`; `anchor-correct` + `blend` reproduces the 91-model HELM Lite ranking at Kendall tau ~0.84-0.85 from 100 anchors, beating random subsets). Online adaptive item generation (Truong et al.) remains absent.
6. **Non-item variance:** seed / run variance and monotonicity (Madaan Table 1), K repeated samples per question (Miller §5, MDE 13.2% to 7.5%), and prompt-format sensitivity (lm-eval Table 1: 72.4% vs 26.5%). evalkit's CIs cover item sampling only.
7. **Data-quality and contamination layers:** label-error audit (Platinum Table 2: 352 bad questions), contamination-resistant variants (metabench §3.2), redundancy diagnostics (BenchScope ED = 1.7).
8. **Where evalkit is ahead of what I read:** exact McNemar power / MDE, Holm over pairs, a randomisation test, tie groups, and `stats-check`, a coverage / type-I / power simulation of the harness's own statistics. Only Bowyer §3 and Arena App. A run comparable coverage simulations, and neither covers these tests.

### Not verified or not found (papers)

- HELM Lite and Capabilities pages read as blog text; whether the HELM leaderboard UI shows any intervals: `unverified` (the leaderboard pages are JS-rendered and returned no text).
- Inspect AI first-release date and any paired-comparison tooling outside the scorer reference page: `unverified`.
- StratPPI headline CI-width numbers (figure-only), Open LLM Leaderboard v2 blog publication date, 2509.22612 specific per-pair numbers: `unverified`.
- The abstract page of lm-eval Lessons shows v3 dated 2026-05-31; the section and table cited are from v3 and may differ from v1.
- Papers dated after 2026-03 (BenchScope, 2607.16259) are recent single-source preprints; I did not look for replications.

## 9. Notes, sources and weak spots

### Notes on non-obvious matrix cells

- **lm-eval row 2.** `stderr_for_metric`: "If the metric has a closed-form SE (e.g. `mean`, `acc_all`), use it." Bootstrap list: median, MCC, F1, perplexity, BLEU, chrF, TER, nanmean ([metrics.py][lm-stderr]). `bootstrap_iters` default 100000 ([evaluator.py L67][lm-eval-py]); BLEU/chrF/chrF++/TER capped at 100 ([evaluator_utils.py][lm-evu]). SE is `N/A` when `len(items) <= 1`.
- **lm-eval row 7.** `acc_all_stderr` builds one 0/1 per question by `all(...)` over sub-answers, then takes `mean_stderr`. That makes the question the unit; it is not a cluster-robust SE.
- **lm-eval row 8.** Docs: "`repeats` … Number of repeated runs through model for each sample. Can be used for cases such as self-consistency." ([task_guide.md L56][lm-repeats]). The evaluator clones each request `req.repeats` times ([evaluator.py L587-590][lm-eval-py]). I did not read how filters collapse repeats into the per-doc score, so SE combination is unverified.
- **lm-eval row 1.** `--log_samples` "Save all model inputs/outputs for post-hoc analysis" ([interface.md L100][lm-iface]).
- **HELM row 2.** `Stat.stddev` docstring: "This is the population standard deviation, not the sample standard deviation." ([statistic.py][helm-stat]). No SE or CI field. Aggregation is by `Stat.merge`.
- **HELM row 8.** `--num-train-trials` appears in the reproduction recipes (3 for Classic, 1 elsewhere) ([reproducing_leaderboards.md][helm-trials]). I did not open the code that combines trials.
- **HELM row 10.** `compute_aggregate_row_win_rates` ranks by mean win rate ([summarize.py L214][helm-sum]). The "CI 95% of Rank Location" table in [efficient_benchmarking.md][helm-eff] is credited to Perlitz et al. 2023, not computed by HELM.
- **HELM row 9b.** `f1_score` calls `f_measure(set(normalize_text(gold).split()), set(normalize_text(pred).split()))` ([evaluate_reference_metrics.py L114][helm-ref]): set-based, so repeated tokens count once. This differs from the multiset SQuAD F1.
- **HELM row 9e.** `compute_calibration_metrics`: "We need at least about 300 examples to compute ece_10_bin reliably." Uses `cal.get_ece_em` (equal-mass bins) ([basic_metrics.py L572-600][helm-cal]).
- **inspect row 7.** `_clustered_stderr`: "The version here uses a finite cluster correction (unlike the paper)", multiplying variance by C/(C−1) ([std.py L83][in-std]). `ci(cluster=)` uses t with clusters−1 df; `ci_wilson(cluster=)` uses a Korn-Graubard effective n.
- **inspect row 2.** `stderr`: "Standard error of the mean using Central Limit Theorem." `ci` default method is Student-t ([std.py L118, L167][in-std]). Miller §2.1 says "The Inspect framework correctly computes SE_C.L.T. with its built-in stderr() metric" ([paper][miller-html]).
- **inspect row 8.** "`scores="auto"` | Reduced scores, unless epoch reducers are explicitly disabled." Default reducer is `mean` ([metrics docs][in-epochs]). So `stderr` runs over per-question reduced scores, which is Miller §3.1. `frequency()` is the exception: it gets raw epoch scores.
- **inspect rows 3-6.** I grepped `llms-full.txt` (guide + API + CLI reference) for paired, McNemar, p-value, significan, Bonferroni, Holm, power analysis, Bradley, minimum detectable. Only unrelated hits ("significantly lower costs"). Third-party packages (inspect_evals, extensions) were not checked.
- **inspect row 9h.** `pass_k`: "Probability that all `k` epoch attempts succeed", estimator `C(correct, k) / C(total, k)` ([reducer.py L202][in-red]).
- **OpenAI evals row 2.** `get_bootstrap_accuracy_std`: `np.std([np.mean(random.sample(vals, len(vals) // 2)) for _ in range(num_samples)])`, default 1000 ([metrics.py][oa-metrics]). Half-size subsamples without replacement, not a with-replacement bootstrap. Used as `"boostrap_std"` (sic) in [match.py L62-63][oa-match]. [INFERENCE, untested] By the finite-population factor (1 − ½) this is about σ/√n, i.e. close to the CLT SE of the full sample.
- **OpenAI evals row 1.** `LocalRecorder`: "A recorder which logs events to the specified JSON file. This is the default recorder used by `oaieval`." ([record.py L309][oa-record]).
- **OpenAI evals rows 3-12 `✗`.** Only `evals/metrics.py` was checked (accuracy, bootstrap std, confusion matrix, MCC, precision/recall/F). Other modules (`evals/elsuite/*`) were not scanned.
- **promptfoo rows 2-7.** Grepped `configuration/reference`, `configuration/outputs`, `configuration/expected-outputs`, `usage/command-line`, `faq` for confidence interval, p-value, statistical, standard error, stderr, stddev, significan, bootstrap: no matches. Pass/fail is a threshold: "pass rate is below the threshold set by `PROMPTFOO_PASS_RATE_THRESHOLD`" ([CLI L188][pf-cli]).
- **promptfoo row 9f.** `perplexity` "is calculated from the log probabilities of tokens" of the model's own output and passes when below a threshold ([deterministic docs][pf-det]). It is a per-output gate, not corpus perplexity.
- **DeepEval rows 2-7.** Grepped `evaluation-introduction`, `metrics-introduction`, `evaluation-flags-and-configs`, `evaluation-end-to-end-llm-evals` for confidence interval, p-value, statistical, standard error, stderr, significan, bootstrap. Only hit: "statistical scorers like ROUGE/BLEU" ([intro][de-intro]).
- **DeepEval row 9d.** HumanEval default `n=200`: "your LLM is being invoked 200 times on the same prompt by default" ([docs][de-he]).
- **DeepEval row 9c.** "If you're looking to use something like ROUGE, BLEU, or BLEURT … create a custom metric" ([intro][de-intro]).
- **evalkit row 2.** CLT SE is not a shipped function: `aggregate.py` defs are `bootstrap_mean_ci`, `_bca_interval`, `_studentized_interval`, etc. ([aggregate.py][ek-agg]). The `wilson_interval` function is in `statscheck.py` for MC rates ([L74][ek-wilson]); README applies Wilson to per-task pass rates.
- **evalkit row 9f / Miller §3.2.** README: each option is scored by summed token log-probs and "the argmax is returned" ([README L203][ek-readme-hf]), so the per-item score is 0/1, not the probability of the right answer.
- **evalkit row 12.** `compute_elo_ratings` ([L193][ek-elo]); README line 14: "deterministic Elo ratings (interleaved match order)". No BT fit.
- **Rows 11 `✗` in other tools.** Based on repo file listings and doc greps only; not an exhaustive code search.

### Sources opened (all on 2026-10-26)

- Paper: [arXiv abs 2411.00640][miller-abs]; [HTML][miller-html].
- lm-eval: [repo][lm-repo]; [releases][lm-rel]; [commits][lm-commits]; [metrics.py][lm-metrics]; [evaluator.py][lm-eval-py]; [evaluator_utils.py][lm-evu]; [interface.md][lm-iface]; [task_guide.md][lm-repeats]; [new_task_guide.md](https://raw.githubusercontent.com/EleutherAI/lm-evaluation-harness/main/docs/new_task_guide.md) (no `repeats` hit); [humaneval utils.py][lm-he]; [humaneval.yaml](https://raw.githubusercontent.com/EleutherAI/lm-evaluation-harness/main/lm_eval/tasks/humaneval/humaneval.yaml); [footguns.md](https://raw.githubusercontent.com/EleutherAI/lm-evaluation-harness/main/docs/footguns.md).
- HELM: [repo][helm-repo]; [releases][helm-rel]; [maintenance_mode.md][helm-maint]; [tutorial.md][helm-tut]; [runner.py](https://raw.githubusercontent.com/stanford-crfm/helm/main/src/helm/benchmark/runner.py); [statistic.py][helm-stat]; [summarize.py][helm-sum]; [evaluate_reference_metrics.py][helm-ref]; [basic_metrics.py][helm-cal]; [code_metrics.py](https://raw.githubusercontent.com/stanford-crfm/helm/main/src/helm/benchmark/metrics/code_metrics.py); [metrics dir listing](https://github.com/stanford-crfm/helm/tree/main/src/helm/benchmark/metrics); [efficient_benchmarking.md][helm-eff]; [reproducing_leaderboards.md][helm-trials]; [schemas.md](https://raw.githubusercontent.com/stanford-crfm/helm/main/docs/schemas.md) (no CI hits); [metrics.md](https://raw.githubusercontent.com/stanford-crfm/helm/main/docs/metrics.md) (autodoc stub only).
- inspect_ai: [repo](https://github.com/UKGovernmentBEIS/inspect_ai); [releases][in-rel]; [std.py][in-std]; [reducer.py][in-red]; [llms-guide.txt][in-guide]; [llms-full.txt][in-full]; [eval-logs doc][in-logs].
- OpenAI evals: [repo/README][oa-readme]; [commits][oa-commits]; [tags][oa-tags]; [metrics.py][oa-metrics]; [match.py][oa-match]; [record.py][oa-record]; [elsuite/utils.py][oa-utils].
- promptfoo: [repo/README][pf-readme]; [releases][pf-rel]; [llms.txt][pf-idx]; [command-line docs][pf-cli]; [deterministic metrics docs][pf-det]; greps of [reference](https://www.promptfoo.dev/docs/configuration/reference/), [outputs](https://www.promptfoo.dev/docs/configuration/outputs/), [expected-outputs](https://www.promptfoo.dev/docs/configuration/expected-outputs/), [faq](https://www.promptfoo.dev/docs/faq/).
- DeepEval: [repo/README][de-readme]; [releases][de-rel]; [metrics intro][de-intro]; [flags and configs][de-flags]; [HumanEval benchmark][de-he]; greps of [evaluation-introduction](https://deepeval.com/docs/evaluation-introduction), [end-to-end evals](https://deepeval.com/docs/evaluation-end-to-end-llm-evals).
- evalkit (local): [README](../README.md); [aggregate.py][ek-agg]; [statscheck.py][ek-sc]; [runner.py][ek-runner]; [classical.py][ek-cls]; [code_exec.py][ek-pass]; [calibration.py][ek-cal]; [models.py][ek-models].

### Unverifiable or weak spots (matrix)

- lm-eval LLM-as-judge (9g): `metrics.py` has none; I did not enumerate `lm_eval/tasks/`. `unverified`.
- lm-eval and HELM repeat/trial SE combination (row 8): code that collapses repeats/trials not opened. `unverified`.
- OpenAI evals, promptfoo, DeepEval "✗" cells: based on one metrics module (OpenAI) or docs-page greps (others), not a full source search. promptfoo/DeepEval source repos were not grepped; GitHub code search needs a login.
- Exact normalisation inside inspect `exact()` and promptfoo `equals`: function bodies not read.
- Every link to `main` is a moving target. Re-pin to commit SHAs before publishing.

## Link index

[ek-rec]: ../src/evalkit/runner.py#L29
[ek-ci]: ../src/evalkit/aggregate.py#L103
[ek-agg]: ../src/evalkit/aggregate.py
[ek-paired]: ../src/evalkit/aggregate.py#L366
[ek-rand]: ../src/evalkit/aggregate.py#L408
[ek-holm]: ../src/evalkit/aggregate.py#L460
[ek-mde]: ../src/evalkit/aggregate.py#L481
[ek-elo]: ../src/evalkit/aggregate.py#L193
[ek-ties]: ../src/evalkit/runner.py#L258
[ek-runner]: ../src/evalkit/runner.py
[ek-sc]: ../src/evalkit/statscheck.py
[ek-wilson]: ../src/evalkit/statscheck.py#L74
[ek-cls]: ../src/evalkit/metrics/classical.py#L12
[ek-mc]: results/helm-lite-metric-check.md
[ek-pass]: ../src/evalkit/metrics/code_exec.py#L183
[ek-cal]: ../src/evalkit/metrics/calibration.py#L54
[ek-ppl]: ../src/evalkit/metrics/calibration.py#L10
[ek-models]: ../src/evalkit/models.py
[ek-judge]: ../src/evalkit/judge.py
[ek-hc]: ../src/evalkit/metrics/helm_compat.py
[ek-rank]: ../src/evalkit/ranking.py
[ek-cont]: ../src/evalkit/contamination.py
[ek-mink]: ../src/evalkit/mink.py
[ek-readme-hf]: ../README.md#L203
[ek-irt]: ../results/helm-lite-irt-subset.md
[lm-repo]: https://github.com/EleutherAI/lm-evaluation-harness
[lm-rel]: https://github.com/EleutherAI/lm-evaluation-harness/releases
[lm-commits]: https://github.com/EleutherAI/lm-evaluation-harness/commits/main
[lm-metrics]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/api/metrics.py
[lm-stderr]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/api/metrics.py#L539
[lm-em]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/api/metrics.py#L212
[lm-eval-py]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/evaluator.py#L67
[lm-evu]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/evaluator_utils.py#L205
[lm-iface]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md#L100
[lm-repeats]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md#L56
[lm-he]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/humaneval/utils.py#L11
[helm-repo]: https://github.com/stanford-crfm/helm
[helm-rel]: https://github.com/stanford-crfm/helm/releases
[helm-maint]: https://github.com/stanford-crfm/helm/blob/main/docs/maintenance_mode.md
[helm-tut]: https://github.com/stanford-crfm/helm/blob/main/docs/tutorial.md#L37
[helm-stat]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/statistic.py
[helm-sum]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/presentation/summarize.py#L214
[helm-ref]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/evaluate_reference_metrics.py#L30
[helm-cal]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/basic_metrics.py#L572
[helm-ppl]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/basic_metrics.py#L87
[helm-jury]: https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/metrics/llm_jury_metrics.py
[helm-eff]: https://github.com/stanford-crfm/helm/blob/main/docs/efficient_benchmarking.md
[helm-trials]: https://github.com/stanford-crfm/helm/blob/main/docs/reproducing_leaderboards.md#L102
[in-rel]: https://github.com/UKGovernmentBEIS/inspect_ai/releases
[in-repo]: https://github.com/UKGovernmentBEIS/inspect_ai
[in-std]: https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/scorer/_metrics/std.py#L118
[in-cluster]: https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/scorer/_metrics/std.py#L83
[in-red]: https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/scorer/_reducer/reducer.py#L158
[in-guide]: https://inspect.aisi.org.uk/llms-guide.txt
[in-full]: https://inspect.aisi.org.uk/llms-full.txt
[in-logs]: https://inspect.aisi.org.uk/eval-logs.html
[in-epochs]: https://inspect.aisi.org.uk/metrics.html#reducing-epochs
[in-scorers]: https://inspect.aisi.org.uk/scorers.html
[in-judge]: https://inspect.aisi.org.uk/model-graded.html
[in-ppl]: https://inspect.aisi.org.uk/perplexity.html
[oa-readme]: https://github.com/openai/evals
[oa-commits]: https://github.com/openai/evals/commits/main
[oa-tags]: https://github.com/openai/evals/tags
[oa-metrics]: https://github.com/openai/evals/blob/main/evals/metrics.py
[oa-match]: https://github.com/openai/evals/blob/main/evals/elsuite/basic/match.py#L62
[oa-record]: https://github.com/openai/evals/blob/main/evals/record.py#L309
[oa-utils]: https://github.com/openai/evals/blob/main/evals/elsuite/utils.py#L33
[pf-readme]: https://github.com/promptfoo/promptfoo
[pf-rel]: https://github.com/promptfoo/promptfoo/releases
[pf-idx]: https://www.promptfoo.dev/llms.txt
[pf-cli]: https://www.promptfoo.dev/docs/usage/command-line/
[pf-det]: https://www.promptfoo.dev/docs/configuration/expected-outputs/deterministic/
[de-readme]: https://github.com/confident-ai/deepeval
[de-rel]: https://github.com/confident-ai/deepeval/releases
[de-intro]: https://deepeval.com/docs/metrics-introduction
[de-flags]: https://deepeval.com/docs/evaluation-flags-and-configs
[de-he]: https://deepeval.com/docs/benchmarks-human-eval
[miller-abs]: https://arxiv.org/abs/2411.00640
[miller-html]: https://arxiv.org/html/2411.00640
