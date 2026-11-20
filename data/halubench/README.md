# Sonnet 5.5 on HaluBench (Lynx paper protocol)

[`scripts/halubench_judge.py`](../../scripts/halubench_judge.py) runs the [HaluBench](https://huggingface.co/datasets/PatronusAI/HaluBench) test set (Ravi et al., [Lynx, arXiv 2407.08488](https://arxiv.org/abs/2407.08488); revision `5966a87`, CC BY-NC 2.0). It has 14,900 (question, passage, answer) triples from six sources, labelled PASS (faithful) or FAIL. This is the RAG-faithfulness benchmark we ran instead of LLM-AggreFact, which is gated and was not accessible.
- **Setup:** `anthropic/claude-sonnet-5-5`, 1 sample, zero-shot, with the paper's own evaluation prompt (Appendix A.2, verbatim from the Lynx-8B model card). The judge writes its reasoning and then a JSON `SCORE` of PASS or FAIL. All 14,900 replies had a parsable SCORE. No evalkit rubric was used and nothing was tuned: HaluBench has no train split.
- **Route:** the calls went through omp's `smol` completion, which serves `anthropic/claude-sonnet-5-5`. Every cache record has `model_returned` = `omp:anthropic/claude-sonnet-5-5`, and the script then scored from that cache. omp exposes no temperature setting, so the run used the provider default. The paper ran its baselines at temperature 0 (Appendix A).
- **Metric:** accuracy per source, as in the paper's Table 3. "Mean of sources" is the plain mean of the six, which reproduces the paper's Overall column for every row except the two Claude-3 rows (see below). Intervals are a 95% bootstrap over passages within each source.
- **Licence:** NonCommercial, so only ids and our verdicts are committed: [`sonnet-5-5-verdicts.jsonl`](sonnet-5-5-verdicts.jsonl) (`id`, `source`, `verdict`). Texts and labels come from the dataset.

| model | HaluEval | RAGTruth | FinanceBench | DROP | CovidQA | PubMedQA | mean of sources |
|---|---|---|---|---|---|---|---|
| LYNX 70B (paper) | 88.4 | 80.2 | 81.4 | **86.4** | **97.5** | **90.4** | **87.4** |
| GPT-4o (paper) | 87.9 | 84.3 | 85.3 | 84.3 | 95.0 | 82.1 | 86.5 |
| GPT-4-Turbo (paper) | 86.0 | **85.0** | 82.2 | 84.8 | 90.6 | 83.5 | 85.4 (printed 85.0) |
| **Sonnet 5.5, this run** | **89.1** [88.5, 89.7] | 73.0 [69.4, 76.4] | **91.5** [89.6, 93.2] | 83.1 [80.9, 85.4] | 96.7 [95.5, 97.9] | 77.1 [74.4, 79.7] | 85.1 [84.2, 86.0] |
| LYNX 8B (paper) | 85.7 | 80.0 | 72.5 | 77.8 | 96.3 | 85.2 | 82.9 |
| Claude-3-Sonnet (paper) | 84.5 | 79.1 | 69.7 | 84.3 | 95.0 | 82.9 | 82.6 (printed 78.8) |
| Llama-3-Instruct-70B (paper) | 87.0 | 83.8 | 72.7 | 69.4 | 85.0 | 82.6 | 80.1 |

Pooled over all 14,900 items, accuracy is 87.6%. HaluEval contributes 10,000 of the items. The paper's printed Overall for Claude-3-Sonnet (78.8) and Claude-3-Haiku (69.0) matches neither the mean (82.6, 78.1) nor the pooled value of its own per-source numbers, so we compare per source and on the recomputed mean.

**Result:** Sonnet 5.5 is level with GPT-4-Turbo on the mean of sources (85.1 vs 85.4; their interval is not reported), below GPT-4o (86.5) and LYNX 70B (87.4). It has the best score on HaluEval and FinanceBench. Its average is pulled down by PubMedQA, RAGTruth and DROP, and on those three almost every error is a false alarm:

| source | false alarms (PASS judged FAIL) | misses (FAIL judged PASS) |
|---|---|---|
| PubMedQA | 222 / 500 | 7 / 500 |
| RAGTruth | 227 / 740 | 16 / 160 |
| DROP | 141 / 500 | 28 / 500 |
| FinanceBench | 62 / 500 | 23 / 500 |
| CovidQA | 9 / 500 | 24 / 500 |
| HaluEval | 222 / 4,990 | 869 / 5,010 |

Why:
1. **PubMedQA (hypothesis, not separated by the data):** a PASS answer is the abstract's own conclusion, and the passage given to the judge is the abstract without it. In none of the 500 PASS answers do the first 60 characters after "Yes." / "No." appear in the passage. A judge told that "the ANSWER must not offer new information beyond the DOCUMENT" may read such a conclusion as new claims. This check does not explain why 222 were flagged and 278 passed, since all 500 are equally absent from the passage [INFERENCE].
2. **DROP (checked):** 379 of 500 PASS answers are comma lists such as "3, 1" or "1, 1" (DROP's multi-span answer format). The judge flags 33.8% of those against 10.7% of single answers.
3. **RAGTruth:** this subset is 82% PASS, and the judge flags 31% of the PASS answers. Balanced accuracy is 79.7% against 73.0% accuracy. Our RAGTruth check found that 30 of 40 train-split false positives contained a quotable error the annotators missed ([`../ragtruth/README.md`](../ragtruth/README.md)), so part of this gap may be the same annotation misses [INFERENCE: not re-checked on these items].
4. **HaluEval:** here the errors are misses: the judge accepts 869 of 5,010 hallucinated answers (17%). Not analysed further.

Point 2 is a format effect of how HaluBench builds PASS answers; point 1 may be one. A rule that allowed them would be tuned on the test set, because HaluBench has no other split, so we did not write one.

Single run, one judge model, provider-default temperature (not 0 as in the paper), and the Claude-3 rows of the paper's table are internally inconsistent.
