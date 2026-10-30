# Protocol: Bradley-Terry ranking and cluster-aware statistics on HELM Lite

Written and committed before the scored run whose output replaces `docs/results/helm-lite-study.md`. The earlier item-level numbers in that file (91 models, adjacent pairs, seed 0) must be reproduced exactly by the new run; if they are not, the new code is wrong and nothing else is reported.

## Questions

1. Does the Bradley-Terry (BT) maximum-likelihood ranking, which fits all pairwise item outcomes at once, reproduce the published HELM Lite order, and how many adjacent published pairs does it separate, compared with HELM's own mean win rate (the bootstrap of section 3 of the earlier study) and the pooled paired test (section 2)?
2. When the pair tests use clustered statistics (cluster sign-flip test, cluster bootstrap CI, design effect in the power figures) wherever items share a source, do the verdicts of the adjacent-rank study change?
3. Do `evalkit compare` and `evalkit leaderboard` now use the same independence assumption? (A unit-test property, not a scored result: with `cluster_id` rows the leaderboard CI of a single-task model equals the cluster bootstrap CI of `compare`'s machinery, and tie groups come from the cluster sign-flip test.)

## Data

Same as `docs/protocol-helm-lite.md` (HELM Lite release v1.13.0, 91 models, 10 scenarios, 10,200 evaluation instances), re-fetched with `scripts/fetch_helm_lite.py` (the raw downloads are compacted on the fly and not kept; the extract is about 40 MB for the metric check and a few MB more for everything else). One addition: for scenarios whose input is `<passage>\nQuestion: <question>` (NarrativeQA, NaturalQuestions open-book) the fetch stores a passage hash per instance (`clusters/`), and `evalkit import-helm` writes it as `cluster_id`.

Which items share a source, measured on the release (checked 2026-10-30 on `instances.json`, evaluation split): NarrativeQA 355 instances, 355 distinct passages (no shared source); NaturalQuestions open-book 1,000 instances, 991 distinct passages (8 passages shared by 2 or 3 questions, 9 extra items); no other scenario's instances carry a source identifier (MMLU, MedQA, OpenbookQA, GSM8K, MATH, LegalBench, WMT). **So HELM Lite has almost no source clusters.** The primary clustered analysis (`passage`) therefore touches 8 clusters.

## Analyses, fixed in advance

* **A. Item-level** (reproduction): section 2 and 3 of the earlier study (paired sign-flip randomisation test, 10,000 draws, seed 0, Holm per rank-distance family for d in {1, 2, 3, 5, 10}; stratified bootstrap of the mean win rate, 1,000 resamples).
* **B. Clustered, primary (`passage`)**: the same families with `compare_pairs(clusters=...)` where the cluster label is (scenario, passage hash); an item without a passage label is its own cluster. Cluster bootstrap with 2,000 resamples (the CI is not used for resolution), cluster sign-flip test with 10,000 draws.
* **C. Clustered, sensitivity (`subset`)**: every subset (MMLU subject, LegalBench task, MATH subject, WMT language pair) is a cluster; scenarios without subsets keep single-item clusters. This is a post-hoc sensitivity analysis, **not** a claim that subsets are the right unit: it asks how fragile the verdicts are if difficulty or model quality is correlated within a subset. It is run with the same settings as B.
* **D. Bradley-Terry**: all 10,200 items, a game for every item and every pair of models scored on it (higher score wins, equal scores split the game), maximum-likelihood strengths (damped Newton, no prior), Elo scale (400 points per factor 10 in the odds, mean 1000). Bootstrap over items (200 resamples, seed 0, the same draw for every model), and again with passage clusters resampled whole. Reported: Kendall tau between the published order and the BT order; for each adjacent published pair the share of resamples in which the published order holds; the number of adjacent pairs at least 97.5%, 95% and 90%; the 95% rank interval widths. Ties are common (most items are 0/1 and agree), and count half, so they carry no information about order but do enter the game counts.

## Predictions (written before the run)

1. A reproduces the earlier numbers exactly: 41 of 90 adjacent pairs resolved, 42 tie groups; 5, 9 and 19 of 90 adjacent pairs at the 97.5%, 95% and 90% bootstrap levels.
2. B changes at most 1 of the 90 adjacent verdicts and at most 2 of the pairs in any other family: 9 items in 8 clusters cannot move 10,200-item sums.
3. C reduces the number of resolved adjacent pairs below 41 (any positive intraclass correlation of the paired differences inside a 1,000-item subset gives a design effect well above 1). If C leaves it at 41, the data show no subset-level dependence in the paired differences.
4. D: Kendall tau between the published and the BT order is at least 0.9, and fewer than half of the 90 adjacent pairs are held in at least 97.5% of BT resamples.

## What would count as a finding

* "The clustered analysis changes nothing" is reported as such for B, with the cluster counts; it is a statement about HELM Lite's design (almost no shared sources), not about clustering in general.
* BT and the mean win rate rank different statistics (pooled item wins vs scenario-balanced mean win rate); disagreements are reported, neither is called the truth.
* Ranks and verdicts are reported with their uncertainty. No hypothesis test is run on the comparison between methods.

## Scope limits

* HELM Lite items are not exchangeable draws from one population; the pooled analyses weigh scenarios by instance count.
* BT ignores scenario structure and any item-model interaction; the bootstrap treats items as independent (or whole clusters as independent), nothing more.
* The metric check (K-E1) is separate: `docs/results/helm-lite-metric-check.md`.

## Outcome (scored run, seed 0, `docs/results/helm-lite-study.md`, 1,354 s)

Predictions against what happened. The protocol above was committed in `f54d9d2` before this run.

| # | Prediction | Result | Verdict |
|---|---|---|---|
| 1 | A reproduces 41 of 90 / 42 tie groups; 5, 9, 19 at 97.5/95/90% | 41 of 90, 42 tie groups; 5, 9, 19 | held |
| 2 | B changes at most 1 adjacent verdict, at most 2 in any family | adjacent 0; distance 2: 2 (49 to 47 resolved), 3: 1, 5: 1, 10: 0; median design effect 1.00, SE ratio 1.00 | held. The data have 8 clusters (17 of 10,200 items), so this says HELM Lite barely has source clusters, not that clustering is harmless |
| 3 | C resolves fewer adjacent pairs than 41 | 8 of 90 resolved (distance 2, 3, 5, 10: 9, 12, 15, 27); 42 tie groups become 9; median design effect about 40, clustered SE about 3.8-4.1 times the naive one | held, by a wide margin |
| 4 | Kendall tau (published vs BT) at least 0.9, and fewer than half of adjacent pairs at 97.5% | tau = 0.866; 41 of 90 adjacent pairs at 97.5% (42 with passage clusters) | tau part **wrong** (0.866 < 0.9); second part held (41 < 45) |

Reading, stated with its limits:

* **C is an upper bound on dependence, not an estimate of it.** A subset is a fixed stratum of the benchmark, not a draw from a population of subsets. Treating the 22 subsets as sampled clusters asks "would the verdicts survive if the benchmark's subjects were a random sample of subjects"; the answer is mostly no (the models' relative strength changes from subject to subject, so paired differences are strongly correlated inside a subset). Whether that is the right question depends on what the leaderboard is meant to generalise to; the item-level analysis answers a narrower one (the same 22 subsets, new items).
* **BT separates far more adjacent pairs (41 of 90 at 97.5%) than HELM's own statistic (5 of 90).** The two do not measure the same thing: BT ranks pooled item wins and each rating borrows information from the other 90 models, so the interval of an adjacent pair is narrower than the direct paired comparison; the mean win rate is scenario-balanced and rank-based. The published pooled paired test resolves 25 of 90 adjacent pairs in the published direction (41 resolved, 16 reversed). I did not run a simulation that checks the coverage of the BT bootstrap on data with item-model interaction, so the 97.5% counts are descriptions of the resampling, not tested error rates. DeepSeek v3 (published rank 3) has BT rank 10 (8-12); that disagreement is a weighting effect, not noise.
* BT with passage clusters moves 1 adjacent count at 97.5% (41 to 42): consistent with prediction 2.
