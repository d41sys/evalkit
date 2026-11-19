# evalkit judge on TRIVIA+ (ACL 2026, long-context RAG QA)

[`scripts/triviaplus_judge.py`](../../scripts/triviaplus_judge.py) runs evalkit's pointwise `Judge` on the [TRIVIA+](https://github.com/amazon-science/hallucination-benchmark-trivialplus) test split (Chen et al., [ACL 2026](https://aclanthology.org/2026.acl-long.680/); commit `c133bbf`, CC BY-NC-ND 4.0): 645 answers by Mixtral 8x7B, Gemma 7B and Claude to questions over articles of 71 to 95,213 characters (median 1,699). Each answer sentence was labelled by 2-6 annotators. An answer is unfaithful when any sentence is "contradicts" or "not-mentioned"; gold is `response_level_label_binary` (not the noisy or LLM-made label columns).
- **Setup:** `claude-sonnet-5-5`, 1 sample, zero-shot. The rubric is the annotators' guideline (paper appendix A.5), written before the run and not tuned (v1).
- **Cut:** the rubric did not say "0 or 1 only", and 254 of 645 replies gave an in-between score (0.1, 0.9, ...). A score below 0.5, the scale's midpoint, counts as unfaithful. This cut was fixed after seeing the score values but not tuned on accuracy. (The RAGTruth runs had no in-between scores.)
- **Interval:** 95% bootstrap over articles.
- **Licence:** NoDerivatives, so only our verdicts are committed: [`sonnet-5-5-v1-test.jsonl`](sonnet-5-5-v1-test.jsonl) (`id` = the parquet's `__index_level_0__`, `score` = the judge's raw 0-1 score). Gold labels and texts come from the parquet.

| method (unfaithful = positive) | F1 | precision | recall | accuracy |
|---|---|---|---|---|
| LLM-as-judge, Claude-3.5 Sonnet (paper, Table 4) | 69.4 | 60.1 | 82.1 | 74.9 |
| few-shot judge (paper) | 69.2 | 58.5 | 84.8 | 73.8 |
| SelfCheckGPT, Claude (paper) | 67.5 | 62.9 | 72.8 | 75.7 |
| fine-tuned detector (paper) | 66.3 | 58.1 | 77.2 | 72.7 |
| **evalkit judge, Sonnet 5.5, rule v1** | **71.0** [66.0, 75.6] | 63.6 | 80.4 | **77.2** |

Balanced accuracy 77.9%. The paper picks each method's threshold to maximise F1 on the test set; ours is fixed at 0.5, so the comparison favours the paper's rows.

| context length | paper LLM-as-judge F1 | evalkit F1 | evalkit balanced acc. |
|---|---|---|---|
| < 1K chars (166) | 71.2 | 77.3 | 83.0 |
| 1K-5K (283) | 72.2 | 75.9 | 79.2 |
| > 5K (196) | 62.1 | 55.1 [43.7, 64.8] | 69.4 |

| generating model | n | F1 | recall | balanced acc. |
|---|---|---|---|---|
| Mixtral 8x7B | 333 | 77.2 | 83.9 | 80.2 |
| Gemma 7B | 124 | 75.2 | 84.4 | 80.8 |
| Claude | 188 | 50.0 [38.3, 60.7] | 64.3 | 68.8 |

**Reading.**
- Zero-shot with a fixed cut, the judge is level with the best method in the paper: F1 71.0 vs 69.4 (inside our interval) and accuracy 77.2 vs 74.9.
- **Long contexts are the weak spot:** F1 55.1 above 5K characters, below the paper's judge there (62.1), while it is ahead on short and medium contexts.
- **Answers written by Claude are judged worst** (balanced accuracy 68.8 vs about 80 for the other two). Misses read include short arithmetic answers on DROP that the judge accepts as "direct inference". Whether this is self-preference (a Claude judge on Claude text), harder items, or label noise was not tested.
- One model, one sample, no tuning; train (2,263) and valid (316) are unused so far.
