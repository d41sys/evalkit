# Haiku 5.5 on FaithBench, zero-shot, run once

[FaithBench](https://github.com/vectara/FaithBench) (Bao et al., NAACL 2025, CC BY-NC-SA 4.0) holds summaries of 75 articles by ten LLMs, with hallucination spans marked by human annotators. The articles were chosen because hallucination detectors disagreed on them, so the set is hard by construction. It was picked as a benchmark that nothing in this repo was tuned on.

**Result: Haiku 5.5 does not beat the best published zero-shot judge here.** Balanced accuracy is 66.3% [62.9, 69.4] against 68.8% for o3-mini-high; the interval contains 68.8.

## Protocol

- **Data.** The 720 summaries (72 articles) that the [FaithJudge repo](https://github.com/vectara/FaithJudge) publishes with the authors' majority label, revision `69cdd25`: 379 Unwanted, 196 Consistent, 83 Benign, 62 Questionable. No text is committed, only ids and our verdicts.
- **Task and metrics.** As in Tamber et al. 2025 ([arXiv 2505.04847](https://arxiv.org/abs/2505.04847), Table 1): Unwanted against Consistent, with Benign and Questionable left out, scored by balanced accuracy and macro F1. That leaves 575 summaries here; the paper scores 599 of all 750.
- **Judge.** Haiku 5.5 through omp, zero-shot. The prompt is the Lynx paper prompt used for [HaluBench](../halubench/README.md), with the question fixed to the summarisation request of Vectara's leaderboard.
- **Frozen first.** Script and configurations were committed in [`21dab05`](https://github.com/d41sys/evalkit/commit/21dab05) before any model call on FaithBench. Nothing was tuned on it and each configuration ran once. The primary configuration is HaluBench rule v5 at cuts 0.5 / 0.6, the setting picked on HaluBench dev for balanced accuracy.

```
uv run --extra llm python scripts/faithbench_judge.py --rule data/halubench/rule-v5.md --cut 0.5 --cut-long 0.6 --out runs/faithbench/haiku-v5
```

## Result

| Unwanted vs Consistent | n | balanced accuracy [95% CI] | macro F1 [95% CI] | hallucinated caught | consistent passed |
|---|---|---|---|---|---|
| **Haiku 5.5, rule v5, cuts 0.5 / 0.6 (primary)** | 575 | **66.3** [62.9, 69.4] | **56.8** [51.2, 61.8] | 37.2 | 95.4 |
| Haiku 5.5, rule v5, cuts 0.5 / 0.8 | 575 | 60.1 [57.1, 63.1] | 46.4 [40.4, 52.2] | 22.7 | 97.4 |
| Haiku 5.5, paper prompt | 575 | 64.0 [59.2, 68.6] | 54.2 [48.2, 59.9] | 34.6 | 93.4 |
| o3-mini-high, FACTS Grounding prompt (published) | 599 | 68.8 | 60.7 | | |
| GPT-4o, FACTS Grounding prompt (published) | 599 | 65.9 | 56.2 | | |
| HHEM-2.1-Open, claim-wise (published) | 599 | 66.7 | 63.7 | | |
| FaithJudge with o3-mini-high (published, not zero-shot) | 599 | 84.0 | 82.1 | | |

Intervals bootstrap over the 72 articles. Published rows are from Tamber et al. 2025, Tables 1 and 2, which give no intervals. Verdicts: [`haiku-5-5-rule-v5-recall.jsonl`](haiku-5-5-rule-v5-recall.jsonl), [`haiku-5-5-rule-v5.jsonl`](haiku-5-5-rule-v5.jsonl), [`haiku-5-5-paper.jsonl`](haiku-5-5-paper.jsonl).

- **The judge misses most hallucinations.** It catches 37.2% of the Unwanted summaries and passes 95.4% of the Consistent ones. [INFERENCE, replies not read] FaithBench's annotated spans are often a single changed or added word, which a judge told to tolerate rewording would pass.
- **Rule v5 adds 2.3 points over the paper prompt**, well inside both intervals; the paired difference was not computed.
- **The HaluBench cut does not transfer.** The 0.5 / 0.8 setting, which gives the best accuracy on HaluBench, scores 60.1% here: it flags 22.7% of the Unwanted summaries, against 37.2% at 0.5 / 0.6.
- **FaithJudge is far ahead** (84.0%) because it shows the judge annotated summaries of the same article. That is a different method, not a better prompt.

## Limits

- **Not the same item set as the published rows.** 575 of the paper's 599 scored summaries are available with the authors' label. The 24 missing ones could move our figure by a point or two in either direction.
- **One run, one model.** Sonnet and Opus were not run.
- **Haiku judges summaries written by a Claude model** for 72 of the 720 items (Claude 3.5 Sonnet). It flags 6 of that model's 33 Unwanted summaries. Self-preference was not tested.
- **The label is a majority over 2 to 5 annotators**, and the FaithBench authors report imperfect agreement.

## Rule s1: a rule written for summaries (2026-11-25)

The first runs above pass most hallucinated summaries. To fix that, the 72 articles were split by a seeded hash into 19 tuning articles (190 summaries) and 53 held articles (530 summaries, 417 scored); `--split dev|held` selects them. [`rule-s1.md`](rule-s1.md) was written from 14 tuning-article misses of rule v5: it tells the judge to check phrase by phrase and to count any changed or added detail, however small. A second draft did not help on the tuning articles and was dropped. Rule s1 with one cut (P_FAIL >= 0.5) was frozen in `765f7d7`, then the held articles were run once.

```
uv run --extra llm python scripts/faithbench_judge.py --rule data/faithbench/rule-s1.md --cut 0.5 --split held --out runs/faithbench/haiku-s1-held
```

| Held articles, Unwanted vs Consistent (n = 417) | balanced accuracy [95% CI] | macro F1 [95% CI] | hallucinated caught | consistent passed |
|---|---|---|---|---|
| **Haiku 5.5, rule s1, cut 0.5** | **77.7** [72.8, 81.7] | **77.5** [72.7, 81.6] | 86.0 | 69.4 |
| Haiku 5.5, rule v5, cuts 0.5 / 0.6 | 66.3 [62.7, 69.7] | 53.1 [46.0, 59.6] | 34.1 | 98.4 |
| Haiku 5.5, paper prompt | 65.9 [61.9, 69.8] | 52.6 [45.5, 59.5] | 33.4 | 98.4 |

Rule s1 minus rule v5, paired over held articles: +11.4 points of balanced accuracy [6.3, 16.6]. On the tuning articles the same step was 69.0 to 73.2. Verdicts: [`haiku-5-5-rule-s1-held.jsonl`](haiku-5-5-rule-s1-held.jsonl).

- **Above the published zero-shot rows** (best: o3-mini-high 68.8 / 60.7), below FaithJudge (84.0 / 82.1). The published rows are on 599 summaries, ours on 417 from 53 articles, so the comparison is indicative.
- **The cost is false alarms.** Rule s1 flags 30.6% of the Consistent summaries (rule v5: 1.6%), 66.7% of the Benign ones and 70.5% of the Questionable ones. In the 12 tuning-article false alarms that were read, several point at a real mismatch the annotators did not mark and several at a dropped hedge; the share of each was not counted.
- **The split was made after the full-set scores above were known**, so it was not planned in advance. No held summary and no held reply was read before the run.
- **Rule s1 is not zero-shot in the strict sense**: it was tuned on 19 FaithBench articles. It was not tried on HaluBench or RAGTruth and is likely too strict for them.
