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
- **The HaluBench cut does not transfer.** The 0.5 / 0.8 setting, which gives the best accuracy on HaluBench, scores 60.1% here. On a set where hallucinations are subtle, the lenient cut for long answers lets them through.
- **FaithJudge is far ahead** (84.0%) because it shows the judge annotated summaries of the same article. That is a different method, not a better prompt.

## Limits

- **Not the same item set as the published rows.** 575 of the paper's 599 scored summaries are available with the authors' label. The 24 missing ones could move our figure by a point or two in either direction.
- **One run, one model.** Sonnet and Opus were not run.
- **Haiku judges summaries written by a Claude model** for 72 of the 720 items (Claude 3.5 Sonnet). It flags 6 of that model's 33 Unwanted summaries. Self-preference was not tested.
- **The label is a majority over 2 to 5 annotators**, and the FaithBench authors report imperfect agreement.
