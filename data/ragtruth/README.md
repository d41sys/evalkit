# evalkit judge on RAGTruth (public benchmark)

[`scripts/ragtruth_judge.py`](../../scripts/ragtruth_judge.py) runs evalkit's pointwise `Judge` on the full [RAGTruth](https://github.com/ParticleMedia/RAGTruth) test split (Niu et al., ACL 2024; commit `c103204`, MIT): 2,700 responses from 6 LLMs on 450 sources.
- **Same protocol as the paper's Table 5:** response-level detection, where a response is hallucinated if it has any labelled span; precision / recall / F1 for the hallucinated class, per task.
- **Setup:** `claude-sonnet-5-5`, 1 sample, zero-shot. For rule v1 (this section), the rubric is the paper's annotation rule (section 3), written once before the run and not tuned. This is the same method as the ezc judge, where the written rule is the rubric. Rule v2 (below) was tuned on train labels.
- **Interval:** 95% bootstrap over sources.

[`sonnet-5-5-test.jsonl`](sonnet-5-5-test.jsonl) holds the verdicts (`gold`/`score`: 1 = hallucinated / passes). The judge's reasoning texts stay in `runs/` (2.5 MB).

| method | QA F1 | data-to-text F1 | summary F1 | overall F1 |
|---|---|---|---|---|
| GPT-4-turbo prompt (paper) | 45.6 | 78.3 | 47.6 | 63.4 |
| fine-tuned Llama-2-13B (paper) | 68.2 | 88.1 | 59.1 | **78.7** |
| **evalkit judge, Sonnet 5.5** | 43.9 | 81.6 | 48.1 | **63.1** [60.4, 65.6] |

Our judge's per-task detail:

| task | precision | recall | balanced acc. |
|---|---|---|---|
| QA | 28.3% | 98.8% | 72.3% |
| data-to-text | 69.1% | 99.8% | 59.6% |
| summary | 31.9% | 97.5% | 68.3% |
| all | 46.3% | 99.2% | 68.7% |

**Reading.**
- The zero-shot judge ties the paper's GPT-4-turbo prompt and is 15 F1 points below the fine-tuned detector.
- **Over-flagging:** it catches 99% of hallucinated responses, but it also flags 1,084 of the 1,757 responses that the annotators passed (62%). A keyword count over those 1,084 reasons (one reason can match several types):

  | reason mentions | share of the 1,084 |
  |---|---|
  | "baseless" | 56% |
  | "subtle conflict" | 33% |
  | qualifier or overstatement | 27% |
  | "evident conflict" or "contradict" | 15% |

  The count does not check whether those flags are wrong. RAGTruth's labels can miss hallucinations, and a few of the reasons read like real subtle conflicts, so part of the 62% may be annotation misses.
- **Same pattern in other work:** Valjakka et al. 2026 ([arXiv 2610.08026](https://arxiv.org/abs/2610.08026)) found the same false-positive-heavy errors when the written criterion is stricter than the annotators' practice.
- **Cause: the criterion.** Here the rule is the paper's short taxonomy, applied literally. Confirmed below: with the same model and settings, rule v2 alone raises balanced accuracy from 68.7 to 84.7 on test.

**Not comparable:** FaithJudge's RAGTruth numbers (Tamber et al. 2025, balanced accuracy about 85%) use up to 150 sources per task, top up with dev, drop sources with no hallucinated response, and put annotated examples of other responses in the prompt.

**Cost:** 4.5M input tokens. Output was about 0.6M tokens, estimated from the reply length (about 830 characters per reply).

## Rule v2: aligned on train labels

The criterion above is stricter than the annotators' practice. Rule v2 ([`rule-v2.md`](rule-v2.md)) tries to match the annotators, using train labels only. That makes v2 a method that learned from train labels, like the paper's fine-tuned Llama-2-13B, and not a zero-shot prompt like the GPT-4-turbo row.
- **Data:** two disjoint seeded train samples of 17 sources per task, 6 responses each, so 306 responses per sample (`--split train --sources-per-task 17 --part 0|1`). Part 0 was used for tuning. Part 1 was held back to check it.
- **Change:** v1's false positives on part 0 were mostly dropped qualifiers, shifts in certainty or tone, and summary judgements. The annotators rarely mark these: only 185 of 12,756 train spans are "Subtle Conflict". v2 still flags wrong specific facts, misattributions, added facts or descriptions, and JSON null stated as yes/no. It lists the shifts above as not hallucinations. One revision, no further iteration.
- **Frozen** in `2ed47f8` before the single test run.

| sample | rule | F1 | balanced acc. |
|---|---|---|---|
| train part 0 (tuning) | v1 | 74.3 | 66.8 |
| train part 0 (tuning) | v2 | 84.3 [79.4, 88.5] | 83.1 |
| train part 1 (check) | v1 | 72.1 | 68.4 |
| train part 1 (check) | v2 | 86.0 [80.8, 90.3] | 86.7 |

Train has more hallucinated responses than test (45% in part 1 vs 35% in test), so F1 runs higher on train. Balanced accuracy does not depend on that rate. Re-weighting part 1 to the test rate (943/2,700) forecasts F1 62.8 for v1 (the actual test value was 63.1) and 80.8 for v2.

**Test (2,700 responses, run once):**

| method | QA F1 | data-to-text F1 | summary F1 | overall F1 | balanced acc. |
|---|---|---|---|---|---|
| GPT-4-turbo prompt (paper, zero-shot) | 45.6 | 78.3 | 47.6 | 63.4 | |
| evalkit judge, rule v1 (zero-shot) | 43.9 | 81.6 | 48.1 | 63.1 [60.4, 65.6] | 68.7 |
| fine-tuned Llama-2-13B (paper, train labels) | 68.2 | 88.1 | 59.1 | 78.7 | |
| **evalkit judge, rule v2** (revised on 306 train responses, checked on another 306) | 63.3 | 88.2 | 67.1 | **78.2** [76.0, 80.2] | **84.7** |

- **Headline:** balanced accuracy 68.7 → 84.7 (+16.0 points), and F1 63.1 → 78.2. The two F1 intervals do not overlap.
- **Where the gain comes from:** recall drops slightly (99.2% → 96.0%). Clean responses flagged fall from 1,084 to 467 of 1,757 (62% → 27%).
- **Against the fine-tuned Llama-2-13B:** overall F1 78.2 vs 78.7, inside our interval, so a tie. QA is lower (63.3 vs 68.2), data-to-text is equal (88.2 vs 88.1) and summary is higher (67.1 vs 59.1). The paper reports no intervals, so the per-task gaps are not tested.
- **Below the forecast:** test F1 came in 2.6 points under the 80.8 forecast from part 1, which suggests some fit to the two train samples or plain sampling noise (306 responses); this was not separated.
- **Caveats:** one model (`claude-sonnet-5-5`), one sample, one rule revision. The remaining false positives are checked on train below, not on test.

Rule v2 test verdicts: [`rule-v2-test.jsonl`](rule-v2-test.jsonl), same format.

## Label check: are the remaining false positives real errors?

Rule v2 flags 27% of test responses the annotators passed. To see how much of that is the judge and how much is the labels, 40 of the 77 rule-v2 false positives on train parts 0/1 were re-read **blind**, plus 10 controls the judge passed (seeded sample, shuffled; 27 summary, 14 QA, 9 data-to-text). Two Claude subagents saw only the source and the response, applied rule v2's definition, and had to quote the span; they did not see the judge's reason or the label. Calls and evidence: [`blind-check.jsonl`](blind-check.jsonl).

| judge | blind reader | n |
|---|---|---|
| flagged | error, high confidence | 15 |
| flagged | error, low confidence | 15 |
| flagged | clean | 10 |
| passed (control) | clean | 10 of 10 |

- **Most of the remaining false positives look like annotation misses.** 30 of 40 have a span the blind reader can quote, 15 with high confidence. Examples: the wrong case listed among "the three other cases" (b14), tags put on the *surviving* students when the source says the dead students' bodies (b43), a student's criticism credited to the protesters (b47). These are evident conflicts under RAGTruth's own taxonomy.
- **The blind reader is not just strict:** it passed all 10 controls.
- **Estimate [inference]:** if 10–25 of every 40 test false positives are real judge mistakes, rule v2's balanced accuracy against corrected labels would be roughly 90–95, not 84.7. This extrapolates 40 train items to test, and the 38 test misses were not re-read (labels can be wrong that way too).
- **Limits:** the blind readers are the same model family as the judge and used its rule, so a shared bias can remain; the controls only rule out blanket strictness.
- **Consequence:** tuning further against these labels would partly teach the judge to pass real errors. The judge's own mistakes in the sample are borderline calls flagged anyway ("I lean toward flagging", 4 of 10), over-strict summary readings, and one reply whose reason finds nothing but scores 0.

## Five votes per response: no gain, not run on test

One 0/1 call gives no threshold to trade precision for recall, so rule v2 was asked 5 times per response on train parts 0/1 (`--samples 5`; default sampling temperature, one cache file per sample; on part 0, none of sample 1's 303 reply texts matched sample 0's). A response is flagged when at least *m* of the 5 replies fail it.
- **The judge barely varies:** 579 of 612 responses get 5 identical votes. Only 33 split (16 QA, 14 summary, 3 data-to-text), so no cutoff can move more than about 5% of the items.
- **Balanced accuracy, parts 0+1 pooled:** one call 84.9, majority of 5 85.1.

  | task | m=1 | m=2 | m=3 | m=4 | m=5 |
  |---|---|---|---|---|---|
  | QA | 84.6 | 82.7 | 82.3 | 82.3 | 83.7 |
  | data-to-text | 79.7 | 81.7 | 82.7 | 82.7 | 82.7 |
  | summary | 82.6 | 84.1 | 84.2 | 84.9 | 85.7 |

  The best per-task cutoffs beat the majority by at most 3 points on about 200 responses per task, are not monotone for QA, and would be picked in-sample, so they are noise-level. The test run (~$100) was skipped.
- **Reading:** the remaining false positives are stable judgements, not sampling noise; together with the label check above, they are mostly a rule-vs-annotator difference or annotation misses, which voting cannot fix.
