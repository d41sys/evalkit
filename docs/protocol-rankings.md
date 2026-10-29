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
