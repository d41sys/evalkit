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

Point 2 is a format effect of how HaluBench builds PASS answers; point 1 may be one.

Single run, one judge model, provider-default temperature (not 0 as in the paper), and the Claude-3 rows of the paper's table are internally inconsistent.

## Rule v2: four bullets added to the paper's prompt

HaluBench has no train split, so we made one: `--split dev` is a seeded 30% of each source, grouped by passage (4,383 items), and `--split held` is the other 70% (10,517). [`rule-v2.md`](rule-v2.md) is four bullets inserted after the prompt's "Show your reasoning.":
1. conclusions and hedged implications drawn from the document's findings are faithful, new facts are not;
2. the answer must answer the question with what the document says, not give a different related statement;
3. a comma list that repeats a value (`14, 14`) is one answer, so judge the values, not the format;
4. do not fail an answer for dropping a qualifier, slightly stronger or weaker wording, combining facts from different parts of the document, or a fair summary.

The bullets came from reading the judge's reasoning on dev errors: hedged conclusions flagged on PubMedQA, repeated lists flagged on DROP, small rewordings flagged on RAGTruth, and related-but-not-answering answers passed on HaluEval. Three drafts were scored on dev only and the best by mean of sources was committed ([`6cb174b`](https://github.com/d41sys/evalkit/commit/6cb174b)) before the held-out run, which ran once. Verdicts: [`sonnet-5-5-rule-v2-held.jsonl`](sonnet-5-5-rule-v2-held.jsonl).

| held-out 70% (10,517) | paper prompt | rule v2 | paired difference [95% CI] | false alarms | misses |
|---|---|---|---|---|---|
| HaluEval (6,953) | 89.3 | 92.2 | +2.9 [2.4, 3.4] | 152 → 131 | 592 → 413 |
| RAGTruth (636) | 72.6 | 78.6 | +6.0 [3.0, 8.8] | 164 → 123 | 10 → 13 |
| FinanceBench (734) | 91.4 | 92.6 | +1.2 [0.0, 2.4] | 44 → 34 | 19 → 20 |
| DROP (675) | 83.0 | 89.0 | +6.1 [4.0, 8.2] | 98 → 57 | 17 → 17 |
| CovidQA (785) | 96.4 | 95.5 | −0.9 [−1.7, −0.1] | 8 → 10 | 20 → 25 |
| PubMedQA (734) | 76.0 | 85.7 | +9.7 [7.4, 11.9] | 171 → 96 | 5 → 9 |
| **mean of sources** | 84.8 | **89.0** [87.9, 89.9] | **+4.2 [3.4, 4.9]** | | |

Pooled over the held-out items, accuracy goes from 87.6% to 91.0%; RAGTruth balanced accuracy goes from 79.9% to 82.4%. Rule v2's held-out mean (89.0) is above every row in the paper's table, including LYNX 70B (87.4), and its interval excludes 87.4. Two limits apply to that comparison:
- **Not the same items.** The paper's rows are on all 14,900 items, ours on the 70% holdout. With the paper prompt the holdout scores 84.8 against 85.1 on the full set, so the holdout is not easier.
- **Not an untouched test set.** Before the split, the analysis above already looked at all 500 PubMedQA PASS answers and measured the DROP list effect on the full DROP set, and those findings shaped bullets 1 and 3. The holdout compares frozen prompts fairly, but it is a retrospective holdout, not independent confirmation on unseen data.

Rule v2 also adapts the judge to HaluBench's own conventions (DROP's comma lists, PubMedQA's conclusions as answers). CovidQA is the one source that got worse (5 more misses); which bullet caused it was not tested. LYNX was fine-tuned on 2,400 examples from the train splits of RAGTruth, DROP, CovidQA and PubMedQA (paper section 3.3), so a prompt tuned on a dev split is closer to LYNX's setup than to the zero-shot rows. Calls went through omp's `smol` route as above.

## Rule v3: a graded probability and a cut, on Sonnet 5.5 and Opus 5.5

[`rule-v3.md`](rule-v3.md) changes three things, all chosen on the dev split:
1. Bullet 1 tells the judge to check a study-style conclusion by its stated findings (direction, significance, population, outcomes) and to allow the implications authors add. Bullet 2 says that "the document does not answer this" and accurate off-topic content are not unfaithful.
2. A new bullet: a short answer copied from the document must match it (term, number, name, scope, full definition). The leniency bullet now applies to longer, explanatory answers only.
3. The judge also returns `P_FAIL`, its probability that annotators labelled the answer unfaithful. `--cut` flags `P_FAIL >= cut` instead of the PASS/FAIL verdict.

On dev, Sonnet's PASS/FAIL verdict under rule v3 scores the same as rule v2 (89.2% mean of sources). Cutting `P_FAIL` at 0.65 scores 91.0%, so the gain comes from the cut, not from the new bullets. Opus 5.5 with the same rule scores 91.4% on dev at one cut (0.7) and 92.6% with two cuts: 0.5 for answers of up to 30 words and 0.8 for longer ones (`--cut 0.5 --cut-long 0.8`). Both configurations were committed before their holdout runs ([`7e02d53`](https://github.com/d41sys/evalkit/commit/7e02d53), [`a3eb4b9`](https://github.com/d41sys/evalkit/commit/a3eb4b9)), and each ran once. Verdicts: [`sonnet-5-5-rule-v3-held.jsonl`](sonnet-5-5-rule-v3-held.jsonl), [`opus-5-5-rule-v3-held.jsonl`](opus-5-5-rule-v3-held.jsonl).

| held-out 70% (10,517), accuracy | best published | paper prompt, Sonnet | rule v2, Sonnet | rule v3, Sonnet | rule v3, Opus 5.5 |
|---|---|---|---|---|---|
| HaluEval (6,953) | 88.4 (LYNX 70B) | 89.3 | 92.2 | 90.5 [89.8, 91.2] | **92.7** [92.1, 93.2] |
| RAGTruth (636) | 85.6 (HHEM) | 72.6 | 78.6 | 84.4 [81.0, 87.6] | **90.1** [87.9, 92.3] |
| FinanceBench (734) | 88.9 (o4-mini) | 91.4 | 92.6 | 91.4 [89.5, 93.3] | **93.1** [91.2, 94.7] |
| DROP (675) | 86.4 (LYNX 70B) | 83.0 | 89.0 | 88.3 [85.8, 90.7] | **89.5** [87.0, 92.0] |
| CovidQA (785) | **97.7** (Lynx 8B) | 96.4 | 95.5 | 95.4 [93.9, 96.8] | 96.1 [93.9, 97.6] |
| PubMedQA (734) | 90.4 (LYNX 70B) | 76.0 | 85.7 | **92.8** [90.7, 94.7] | 91.7 [89.6, 93.6] |
| **mean of sources** | 87.4 (LYNX 70B) | 84.8 | 89.0 | 90.5 [89.6, 91.4] | **92.2** [91.4, 92.9] |

"Best published" is the highest accuracy per source in two papers: the Lynx paper's Table 3 and Liu et al., [arXiv 2601.09734](https://arxiv.org/abs/2601.09734), Tables 7 and 8 (HHEM, o4-mini and Lynx 8B come from the second). Both score the full HaluBench test set, not our holdout. Later work was not searched beyond these two.

Paired on the same holdout items (95% passage bootstrap): rule v3 minus rule v2 on Sonnet is +1.5 [0.8, 2.3] on the mean, with RAGTruth +5.8 [2.8, 9.1] and PubMedQA +7.1 [4.9, 9.4] against HaluEval −1.7 [−2.1, −1.3]. Opus minus Sonnet under rule v3 is +1.7 [1.0, 2.4] on the mean, with RAGTruth +5.7 [3.1, 8.2] and HaluEval +2.1 [1.7, 2.6].

What the table does not show:
- **CovidQA is still below the best published result.** Opus scores 96.1% against 97.5% (LYNX 70B) and 97.7% (Lynx 8B). On dev the same configuration scored 98.6% on 215 items, so the dev figure was optimistic.
- **The RAGTruth gain is accuracy, not detection.** The holdout RAGTruth items are 82.7% PASS, so a judge that passes everything scores 82.7%. Recall of the hallucinated answers falls from 90.9% (paper prompt) to 70.9% (Sonnet, rule v3) and 69.1% (Opus). RAGTruth balanced accuracy is 79.9% (paper prompt), 82.4% (rule v2), 79.1% (Sonnet, rule v3) and 81.8% (Opus).
- **By balanced accuracy, rule v3 does not beat rule v2 on Sonnet.** The mean of sources is 89.6% for both. Opus under rule v3 reaches 90.8%; the paper prompt is 86.1%.
- **The holdout has now been used three times** (rule v2, rule v3 on Sonnet, rule v3 on Opus), on top of the limits listed for rule v2. Each further configuration picked by its holdout score would be fitted to it.
- **The Opus run mixes two effort settings.** omp's `default` alias served Opus 5.5 for 3,360 of the 10,508 distinct holdout prompts (all of DROP, FinanceBench, RAGTruth and PubMedQA, and 590 HaluEval items) and then began serving a different model. Nothing from that model was kept. The other 7,148 prompts (all of CovidQA and 6,363 HaluEval items) went to the `slow` alias, which is Opus 5.5 at high effort. On 240 dev items judged both ways, `P_FAIL` correlates at 0.996 and the verdicts at the frozen cuts agree on 99.6%. Cache records carry the route in `model_returned`.
- **Opus refused 16 holdout items** (8 CovidQA, 8 PubMedQA; 7 of 4,383 on dev). A refusal counts as FAIL, as fixed before the run. 12 of the 16 are PASS answers, so refusals cost 7 CovidQA items; on the 777 CovidQA items Opus answered, accuracy is 96.9%.

## Rule v4: an extract check in the prompt, on Opus 5.5

### What a string check alone scores

A rule with no model, "PASS if the answer is a word-for-word substring of the passage, else FAIL", was defined on the dev split and then scored on all 14,900 items:

| | HaluEval | RAGTruth | FinanceBench | DROP | CovidQA | PubMedQA | mean of sources |
|---|---|---|---|---|---|---|---|
| string check only | **97.5** | 17.8 | 49.8 | 45.6 | 96.2 | 50.0 | 59.5 |
| best published | 88.4 | 85.6 | 88.9 | 86.4 | 97.7 | 90.4 | 87.4 |

On HaluEval and CovidQA nearly all PASS answers are spans copied from the passage (4,758 of 4,990 and 500 of 500) and nearly all FAIL answers are not (4,987 of 5,010 and 462 of 500), so those two sources mostly measure whether an answer was copied. On HaluEval the string check is above every judge in this file and every published row we found.

### Fresh CovidQA tuning data

[`PatronusAI/lynx-train-v0.1`](https://huggingface.co/datasets/PatronusAI/lynx-train-v0.1) (revision `eeef166`, no licence stated, nothing from it is committed) holds 800 items whose question is in COVID-QA (`deepset/covid_qa_deepset`, revision `be51d91`): 600 train and 200 validation, half PASS. 370 remain after dropping every question that appears in HaluBench (185 PASS, 185 FAIL). 347 of them share a passage with a HaluBench item, 267 with a holdout item, each time with a different question. The frozen Opus rule v3 configuration scores 97.3% on these 370: 7 word-for-word fragments flagged as incomplete, and 3 one-word rewordings passed.

The same comparison shows an overlap between that training release and the HaluBench test set: 433 of the 1,000 CovidQA test questions also appear in it with a different answer string, as do 103 DROP questions (19 with the same answer and label) and 96 RAGTruth questions (17 with the same answer and label). The dataset card does not say whether v0.1 is the set that trained the paper's LYNX.

### Rule and result

[`rule-v4.md`](rule-v4.md) puts the string check's result into the prompt (`{extract_check}`, filled by the script) and adds two bullets: a short word-for-word extract is faithful even as a fragment unless the document clearly gives a different value for what is asked, and a short answer that closely follows a document phrase without matching it is judged on the difference, however small. One draft was written. On the tuning data (dev plus the 370 fresh items) the mean of sources goes from 92.5% (rule v3) to 93.3% with the cuts unchanged. The configuration was committed before the holdout run ([`ac379c0`](https://github.com/d41sys/evalkit/commit/ac379c0)): Opus 5.5 at high effort for every item (omp's `slow` alias), cuts 0.5 / 0.8 as before, and `--fallback` to the Sonnet rule v3 verdict where Opus refuses. Verdicts: [`opus-5-5-rule-v4-held.jsonl`](opus-5-5-rule-v4-held.jsonl).

| held-out 70% (10,517), accuracy | best published | rule v3, Opus | rule v4, Opus | v4 − v3, paired [95% CI] |
|---|---|---|---|---|
| HaluEval (6,953) | 88.4 | 92.7 | **93.7** [93.1, 94.3] | +1.0 [0.7, 1.3] |
| RAGTruth (636) | 85.6 | **90.1** | 89.3 [86.8, 91.7] | −0.8 [−1.6, 0.0] |
| FinanceBench (734) | 88.9 | **93.1** | 92.9 [91.1, 94.8] | −0.1 [−1.3, 1.0] |
| DROP (675) | 86.4 | 89.5 | **90.4** [87.9, 92.6] | +0.9 [−0.1, 2.0] |
| CovidQA (785) | 97.7 | 96.1 | **98.1** [97.1, 98.9] | +2.0 [0.7, 3.9] |
| PubMedQA (734) | 90.4 | 91.7 | **95.0** [93.5, 96.5] | +3.3 [1.5, 5.0] |
| **mean of sources** | 87.4 | 92.2 | **93.2** [92.5, 93.9] | +1.1 [0.5, 1.6] |

Rule v4 on Opus is above the best published accuracy on all six sources and on the mean; for CovidQA the first three points below weaken that. The mean of sources by balanced accuracy is 91.8% (rule v3 on Opus: 90.8%). What the table does not show:
- **The CovidQA result depends on the refusal fallback.** Opus refused 19 holdout items (12 PubMedQA, 7 CovidQA; 13 are PASS answers). The Sonnet verdict is right on 18 of them. Counting refusals as FAIL, as in rule v3, gives CovidQA 97.6% (below 97.7%), PubMedQA 93.9% and a mean of 93.0%. The fallback was added after the rule v3 run showed that refusals cost 7 CovidQA holdout items. The dev evidence for it is thin and has no CovidQA item: under rule v3 Opus gave no verdict on 8 dev items (7 refusals; 6 HaluEval, 2 PubMedQA), where the Sonnet verdict is right on 8 and counting them as FAIL is right on 5; under rule v4 it gave none on 3 dev items (all PubMedQA), where Sonnet is right on 3 and FAIL on 2. The "8 of 8" in the freeze commit message is the rule v3 count.
- **The CovidQA holdout shares passages with the tuning data.** The dev split keeps HaluBench passages apart, but the 370 fresh tuning items do not: 669 of the 785 CovidQA holdout items have a passage that also occurs among them. On the 116 that do not, rule v4 is right on 113 (97.4%, below 97.7%) and rule v3 on 112 (96.6%); on the 669 the figures are 98.2% and 96.0%. This subset was examined after the run.
- **The CovidQA margin is not separated from the published figure.** The interval [97.1, 98.9] contains 97.7, and our 785 holdout items are not the 1,000 the published rows use.
- **On CovidQA and HaluEval the gain is copy detection.** Rule v4 hands the judge the string check, which alone scores 96.2% and 97.5% there. On HaluEval the string check still beats the judge (97.5% against 93.7%).
- **This is the fourth judge run on the holdout.** The string check, defined on dev, was also scored on it.
- **RAGTruth did not improve.** Recall of its hallucinated answers is 67.3% and balanced accuracy 80.6%, against 82.4% for rule v2 on Sonnet.
- **For four sources the v4 − v3 difference mixes two changes.** Rule v3 ran DROP, FinanceBench, RAGTruth and PubMedQA at default effort; rule v4 ran everything at high effort. The fresh-data tuning set and the string-check and overlap analyses were run in a notebook session and are not reproduced by the script.

## Rule v5: RAGTruth recall, on Haiku 5.5

Rules v3 and v4 buy RAGTruth accuracy by passing long answers: recall of its hallucinated answers fell from 91% (paper prompt, Sonnet) to 67% (rule v4, Opus). Rule v5 targets that, and from here on the judge is Haiku 5.5.

**What the dev errors showed (Haiku, rule v3).** The judge passed 16 of the 50 hallucinated RAGTruth dev answers, and the paper prompt had caught 10 of those 16. In the cases read, the judge's own reasoning names the unsupported addition (an extra step, an added claim, a wrong statement about what a passage says) and then passes the answer, because rule v3 tells it to be lenient with long answers. [`rule-v5.md`](rule-v5.md) is rule v4 with that leniency bullet replaced: in longer answers that explain or instruct, a concrete addition the document does not contain is unfaithful even when minor, while rewording, a calculated result, a restating sentence, an off-question answer and declining to answer stay faithful, and study conclusions stay under the first bullet. Two drafts were tried on dev; the first cost about 2 points on both FinanceBench and PubMedQA and was dropped.

**Scoring change.** Haiku leaves out `P_FAIL` in 2% of replies under rule v3 and 6% under rule v5 (holdout: 183 and 656 of 10,517, 4 of them refusals each). With `--cut`, such a reply now keeps its own SCORE. No Sonnet or Opus row changes, because their only replies without `P_FAIL` are refusals.

**Frozen before the holdout runs** ([`76a4302`](https://github.com/d41sys/evalkit/commit/76a4302)): Haiku 5.5 through omp, rule v5, no fallback (a refusal counts as FAIL), two settings picked on dev. The primary setting keeps the cuts 0.5 / 0.8 (best dev mean accuracy, 90.5%). The recall setting uses 0.5 / 0.6 (best dev mean balanced accuracy, 90.1%). Comparators on the same model: the paper prompt, and rule v3 at 0.5 / 0.8.

| held-out 70% (10,517), Haiku 5.5, accuracy | paper prompt | rule v3 | rule v5 | v5 − v3, paired [95% CI] | rule v5, recall setting |
|---|---|---|---|---|---|
| HaluEval (6,953) | 88.2 | 89.8 | **90.4** | +0.6 [0.1, 1.1] | 90.5 |
| RAGTruth (636) | 80.3 | 85.8 | **87.7** | +1.9 [−0.9, 4.9] | 77.4 |
| FinanceBench (734) | 90.5 | 90.3 | **90.9** | +0.5 [−0.6, 1.8] | 90.9 |
| DROP (675) | 85.0 | 86.7 | **87.6** | +0.9 [−0.4, 2.1] | 87.6 |
| CovidQA (785) | 95.4 | 94.9 | **96.6** | +1.7 [0.7, 2.5] | 96.9 |
| PubMedQA (734) | 72.9 | **89.6** | 87.6 | −2.0 [−4.2, 0.0] | 80.9 |
| **mean of sources** | 85.4 | 89.5 | **90.1** [89.2, 90.9] | +0.6 [−0.1, 1.3] | 87.4 |
| mean of sources, balanced accuracy | 85.9 | 86.4 | **88.9** | | 88.4 |
| RAGTruth: recall of hallucinated answers | 87.3 | 38.2 | 68.2 | | **91.8** |
| RAGTruth: faithful answers passed | 78.9 | **95.8** | 91.8 | | 74.3 |
| RAGTruth: balanced accuracy | **83.1** | 67.0 | 80.0 | | **83.1** |

Verdicts: [`haiku-5-5-paper-held.jsonl`](haiku-5-5-paper-held.jsonl), [`haiku-5-5-rule-v3-held.jsonl`](haiku-5-5-rule-v3-held.jsonl), [`haiku-5-5-rule-v5-held.jsonl`](haiku-5-5-rule-v5-held.jsonl), [`haiku-5-5-rule-v5-recall-held.jsonl`](haiku-5-5-rule-v5-recall-held.jsonl).

- **Recall rose by 30 points at no cost in accuracy.** Against rule v3 on the same model, rule v5 catches 68.2% of RAGTruth's hallucinated answers instead of 38.2%, RAGTruth accuracy is 87.7% against 85.8%, and the mean balanced accuracy rises from 86.4% to 88.9%.
- **The fix is partial.** 68.2% is still below the 87.3% the paper prompt reaches, and no setting beats the paper prompt's RAGTruth balanced accuracy of 83.1%; the recall setting only equals it, and pays 7 points on PubMedQA for it.
- **The rule sharpens the ranking only a little.** ROC-AUC of `P_FAIL` on holdout RAGTruth is 0.911 under rule v5 and 0.885 under rule v3. Most of the difference between the columns is where the cut falls.
- **The mean accuracy gain over rule v3 is not separated from zero** (+0.6 [−0.1, 1.3]), and PubMedQA is 2 points lower.
- **Haiku with rule v5 is above the best published accuracy on four sources** (HaluEval, RAGTruth, FinanceBench, DROP) and below it on CovidQA (96.6% against 97.7%) and PubMedQA (87.6% against 90.4%). Opus with rule v4 remains the best row in this file (93.2%).
- **RAGTruth's gold limits what a rule can do.** [INFERENCE from reading dev items] Several faithful-labelled dev answers that the judge still flags contain what looks like a real contradiction (one says chard is related to spinach where the passage says it is not).
- **This is the fifth judge configuration scored on the holdout**, and rule v5 was not run on Sonnet or Opus. omp reports no effort level for these Haiku calls.

## Rule v6 draft: dropped on the tuning split (2026-11-25)

Tried on Haiku 5.5: rule v5 plus a `TYPE` key (conclusion, explanation, short) with one cut per type, to get the recall setting's RAGTruth recall without its PubMedQA cost. On the three long-answer sources of the tuning split (794 items) every cut combination scored below rule v5: best RAGTruth balanced accuracy 83.8 (rule v5: 86.6 at cuts 0.5 / 0.6), PubMedQA 87.2 (89.5), FinanceBench 92.5 (94.0), and replies without `P_FAIL` rose to 107 of 794. The draft was not frozen and the holdout was not run. Rule v5 stays the Haiku result.
