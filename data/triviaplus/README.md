# evalkit judge on TRIVIA+ (ACL 2026, long-context RAG QA)

[`scripts/triviaplus_judge.py`](../../scripts/triviaplus_judge.py) runs evalkit's pointwise `Judge` on the [TRIVIA+](https://github.com/amazon-science/hallucination-benchmark-trivialplus) test split (Chen et al., [ACL 2026](https://aclanthology.org/2026.acl-long.680/); commit `c133bbf`, CC BY-NC-ND 4.0): 645 answers by Mixtral 8x7B, Gemma 7B and Claude to questions over articles of 71 to 95,213 characters (median 1,699). Each answer sentence was labelled by 2-6 annotators. An answer is unfaithful when any sentence is "contradicts" or "not-mentioned"; gold is `response_level_label_binary` (not the noisy or LLM-made label columns).
- **Setup:** `claude-sonnet-5-5`, 1 sample, zero-shot. The rubric is the annotators' guideline (paper appendix A.5), written before the run and not tuned (v1).
- **Cut:** the rubric did not say "0 or 1 only", and 254 of 645 replies gave an in-between score (0.1, 0.9, ...). The script as run flagged only a score of exactly 0; that treats 0.2 as faithful, so the table also shows the scale's midpoint (below 0.5 = unfaithful), chosen after seeing the score values but not tuned on accuracy. ROC-AUC needs no cut and is the cleanest comparison. (The RAGTruth runs had no in-between scores.)
- **Interval:** 95% bootstrap over articles.
- **Licence:** NoDerivatives, so only our verdicts are committed: [`sonnet-5-5-v1-test.jsonl`](sonnet-5-5-v1-test.jsonl) (`id` = the parquet's `__index_level_0__`, `score` = the judge's raw 0-1 score). Gold labels and texts come from the parquet.

| method (unfaithful = positive) | ROC-AUC | F1 | precision | recall | accuracy |
|---|---|---|---|---|---|
| LLM-as-judge, Claude-3.5 Sonnet (paper, Tables 4 and 7) | 0.766 | 69.4 | 60.1 | 82.1 | 74.9 |
| few-shot judge (paper) | 0.764 | 69.2 | 58.5 | 84.8 | 73.8 |
| SelfCheckGPT, Claude (paper) | 0.795 | 67.5 | 62.9 | 72.8 | 75.7 |
| fine-tuned detector (paper) | 0.777 | 66.3 | 58.1 | 77.2 | 72.7 |
| **evalkit judge, Sonnet 5.5, rule v1**, flag score = 0 (as run) | **0.851** | 73.2 [68.0, 77.7] | 76.6 | 70.1 | 82.2 |
| same verdicts, flag score < 0.5 | 0.851 | 71.0 [66.0, 75.6] | 63.6 | 80.4 | 77.2 |

ROC-AUC uses 1 − score as the unfaithfulness score (many ties at 0 and 1). Balanced accuracy is 79.3% (score = 0) and 77.9% (< 0.5). The paper picks each method's threshold to maximise F1 on the test set; ours are fixed, so the F1 and accuracy columns favour the paper's rows. The breakdowns below use the < 0.5 cut.

| context length | paper LLM-as-judge F1 | evalkit F1 | evalkit balanced acc. |
|---|---|---|---|
| < 1K chars (166) | 71.2 | 77.3 | 83.0 |
| 1K-5K (283) | 72.2 | 75.9 | 79.2 |
| > 5K (196) | 62.1 | 55.1 [43.7, 64.8] | 69.4 |

| generating model | n | hallucinated | ROC-AUC | recall | false-positive rate | balanced acc. |
|---|---|---|---|---|---|---|
| Mixtral 8x7B | 333 | 41% | 0.863 | 83.9 | 23.5 | 80.2 |
| Gemma 7B | 124 | 36% | 0.863 | 84.4 | 22.8 | 80.8 |
| Claude | 188 | 22% | 0.778 | 64.3 | 26.7 | 68.8 |

**Reading.**
- **Ahead of every method in the paper on ROC-AUC:** 0.851 vs 0.766 for the paper's Claude-3.5 judge and 0.795 for its best method, with no threshold involved. On F1 and accuracy it is level or ahead under either cut, without the paper's test-tuned threshold.
- **Long contexts are the weak spot:** F1 55.1 above 5K characters, below the paper's judge there (62.1), while it is ahead on short and medium contexts.
- **Answers written by Claude separate worst** (ROC-AUC 0.778 vs 0.863). The main difference is recall: the judge catches 64% of Claude's unfaithful answers vs 84% for the other two, while its false-positive rate is similar (27% vs 23%). Claude's low F1 (50.0) is mostly its low hallucination rate (22%), which pulls precision down. Missed items read include short arithmetic answers on DROP that the judge accepts as "direct inference". Lower recall on Claude text fits self-preference but is not proof of it; harder items or label noise were not ruled out.
- One model, one sample, no tuning; train (2,263) and valid (316) are unused so far.
