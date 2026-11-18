# evalkit judge on RAGTruth (public benchmark)

[`scripts/ragtruth_judge.py`](../../scripts/ragtruth_judge.py) runs evalkit's pointwise `Judge` on the full [RAGTruth](https://github.com/ParticleMedia/RAGTruth) test split (Niu et al., ACL 2024; commit `c103204`, MIT): 2,700 responses from 6 LLMs on 450 sources.
- **Same protocol as the paper's Table 5:** response-level detection, where a response is hallucinated if it has any labelled span; precision / recall / F1 for the hallucinated class, per task.
- **Setup:** `claude-sonnet-5-5`, 1 sample, zero-shot. The rubric is the paper's annotation rule (section 3), written once before the run and not tuned. This is the same method as the ezc judge, where the written rule is the rubric.
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
- **Likely cause: the criterion.** On ezc the rule was aligned with the labellers over 4 rounds, and the judge reaches 94.5% balanced accuracy there. Here the rule is the paper's short taxonomy, applied literally. This run tested one criterion with one model, so it does not separate the criterion's effect from the model's.

**Not comparable:** FaithJudge's RAGTruth numbers (Tamber et al. 2025, balanced accuracy about 85%) use up to 150 sources per task, top up with dev, drop sources with no hallucinated response, and put annotated examples of other responses in the prompt.

**Cost:** 4.5M input tokens. Output was about 0.6M tokens, estimated from the reply length (about 830 characters per reply).
