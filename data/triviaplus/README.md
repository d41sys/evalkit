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
| **evalkit judge, Sonnet 5.5, rule v1**, flag score = 0 (as run) | **0.851** [0.820, 0.879] | 73.2 [68.0, 77.7] | 76.6 | 70.1 | 82.2 |
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
- **Ahead of every method in the paper on ROC-AUC:** 0.851 [0.820, 0.879] vs 0.766 for the paper's Claude-3.5 judge and 0.795 for its best method, with no threshold involved; our lower bound is above both (the paper gives no intervals). On F1 and accuracy it is level or ahead under either cut, without the paper's test-tuned threshold.
- **Long contexts are the weak spot:** F1 55.1 above 5K characters, below the paper's judge there (62.1), while it is ahead on short and medium contexts.
- **Answers written by Claude separate worst** (ROC-AUC 0.778 vs 0.863). The main difference is recall: the judge catches 64% of Claude's unfaithful answers vs 84% for the other two, while its false-positive rate is similar (27% vs 23%). Claude's low F1 (50.0) is mostly its low hallucination rate (22%), which pulls precision down. Missed items read include short arithmetic answers on DROP that the judge accepts as "direct inference". Lower recall on Claude text fits self-preference but is not proof of it; harder items or label noise were not ruled out.
- One model, one sample, no tuning (v1). Rule v2 below uses train and valid.

## Rule v2: graded probability, tuned on train

[`rule-v2.md`](rule-v2.md) keeps v1's guideline and adds two things: (a) the score is the judge's probability, 0 to 1, that the annotators labelled the answer faithful, using the whole range; (b) arithmetic the article supports up to rounding, and spans counted inclusively or exclusively, count as supported.
- **Data:** errors read on a seeded sample of 300 train answers (`--split train --sample 300`); checked on all 316 valid answers; frozen in `b4b622c`; run once on test. Train, valid and test share no article (7 of 456 test questions also appear in train).
- **Discarded on train:** a version that forced 0/1 and called non-answers unfaithful. ROC-AUC on train fell from 0.883 to 0.784: forcing 0/1 removed the ranking signal, and the non-answer clause made 23 wrong new flags for 8 right ones.
- **Leak found and removed before freezing:** one rounding example ("about 1,100 for 1,123") came from a test item read while writing up v1. It was replaced by a made-up one and train/valid were rerun. The other examples are train items, so the train numbers are optimistic; the valid numbers are the check.

| split | v1 ROC-AUC | v2 ROC-AUC | paired difference [95% CI] | v1 / v2 balanced acc. |
|---|---|---|---|---|
| train sample (300, tuning) | 0.883 | 0.901 | | 79.1 / 82.0 |
| valid (316, check) | 0.836 | 0.879 | +0.042 [0.024, 0.062] | 79.9 / 80.6 |
| **test (645, once)** | 0.851 | **0.865** [0.837, 0.893] | **+0.015 [0.003, 0.026]** | 77.9 / 79.3 |

**The gain is in ranking only.** At a fixed cut v2 is level with v1 as it was run (flag only score = 0):

| test, fixed cut | F1 | balanced acc. | accuracy |
|---|---|---|---|
| v1, flag score = 0 (as run) | 73.2 | 79.3 | 82.2 |
| v1, flag < 0.5 | 71.0 | 77.9 | 77.2 |
| v2, flag < 0.5 | 72.7 | 79.3 | 79.4 |
| v2, flag < 0.15 (cut with the best balanced accuracy on train sample + valid) | 73.5 | 79.6 | 82.3 |

On train + valid, balanced accuracy is flat from cut 0.15 to 0.5 (80.9-81.5), so the 0.15 choice is noise-level. Against the paper (Table 7 ROC-AUC 0.766 for its Claude-3.5 judge, 0.795 for its best method), v2's lower bound 0.837 is above both. Verdicts: [`sonnet-5-5-v2-test.jsonl`](sonnet-5-5-v2-test.jsonl).

### Why v2 is better

1. **The graded probability does almost all of it.** An ablation, v1 plus only the probability instruction ([`ablation-v1-graded.md`](ablation-v1-graded.md)), ran on the items the API credit covered:

   | items (paired) | v1 | v1 + probability only | v2 |
   |---|---|---|---|
   | valid, 297 of 316 | 0.853 | 0.883 | 0.886 |
   | test, 322 of 645 | 0.853 | 0.872 | 0.866 |

   The arithmetic clause adds 0.003 on valid and nothing on test.
2. **Mechanism: it breaks v1's ties.** v1 put 61% of test answers at exactly 0 or 1 (21 score levels); v2 put none there (39 levels). Inside v1's "clearly faithful" group (186 answers, 6% hallucinated), v2 ranks the hallucinated ones higher (ROC-AUC 0.748 within the group, where v1 has no ranking at all, 0.5). Inside v1's "clearly unfaithful" group (205, 77% hallucinated) it is 0.616. Among answers v1 already scored in between, nothing changes (0.641 vs 0.642).
3. **At the 0.5 cut v2 mostly removes false alarms compared with v1 at 0.5:** 19 answers v1 wrongly flagged are now passed, 0 new hallucinations are caught, and 5 answers got worse (2 new false alarms, 3 new misses). 18 of the 19 fixes are on questions other than "how many", so the arithmetic clause is not what moved the cut either. v1's as-run rule (score = 0) already passed most of those answers, which is why the fixed-cut numbers end level.
4. **Unchanged weak spots:** articles over 5K characters (ROC-AUC 0.775 → 0.791) and answers written by Claude (0.778 → 0.782).

The test gain (+0.015) is a third of the valid gain (+0.042): part of the valid result did not carry over. Single run, one judge model; the ablation covers about half the test set because the API credit ran out.
