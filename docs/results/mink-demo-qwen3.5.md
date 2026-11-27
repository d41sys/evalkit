# Min-K% Prob demo (Qwen3.5-0.8B-Base, GSM8K test vs Claude paraphrases)

**A DEMO of the Min-K% Prob method on a tiny model. It is not a contamination audit of Qwen3.5-0.8B-Base, of any other model, or of GSM8K.** Protocol: `docs/protocol-mink.md` (committed before scoring). Reproduce: `uv run --offline python scripts/mink_demo.py --model qwen3.5-0.8b-base report` (replays committed caches; no model, key or network).

- Model `Qwen/Qwen3.5-0.8B-Base` revision `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`, float32; log-probs under teacher forcing after a prepended `<|endoftext|>` context token.
- 150 questions selected (`random.Random(0)`), 132 kept after the number-multiset check; dropped: {'numbers_differ': 18}.
- Statistic: AUROC of originals (label 1) vs paraphrases (label 0); 95% paired cluster-bootstrap CI over source questions, 2000 resamples, seed 0.

## Primary result and baselines

| score | AUROC [95% CI] | verdict | matched-length AUROC | residualised AUROC | orig > para (win rate) |
|---|---|---|---|---|---|
| Min-K% (K=10) | 0.582 [0.537, 0.625] | separates | 0.659 [0.592, 0.723] | 0.638 [0.586, 0.688] | 0.659 [0.576, 0.735] |
| Min-K% (K=20) **primary** | 0.645 [0.603, 0.686] | separates | 0.707 [0.650, 0.763] | 0.693 [0.648, 0.740] | 0.720 [0.636, 0.788] |
| Min-K% (K=30) | 0.662 [0.619, 0.706] | separates | 0.697 [0.642, 0.753] | 0.700 [0.655, 0.744] | 0.758 [0.682, 0.826] |
| Min-K% (K=50) | 0.679 [0.637, 0.719] | separates | 0.706 [0.649, 0.762] | 0.707 [0.663, 0.748] | 0.750 [0.674, 0.818] |
| mean log-prob (baseline) | 0.682 [0.641, 0.723] | separates | 0.713 [0.661, 0.767] | 0.708 [0.663, 0.748] | 0.773 [0.697, 0.841] |
| zlib ratio (baseline) | 0.607 [0.558, 0.654] | separates | 0.593 [0.530, 0.654] | 0.603 [0.554, 0.651] | 0.606 [0.523, 0.689] |

Matched-length AUROC uses the 2871 of 17424 (original, paraphrase) pairs whose token counts differ by at most 5. Residualised: OLS of the score on token count, refit in every resample.

## AUROC of the primary score minus another score (same resamples)

| other score | difference [95% CI] | CI excludes 0 |
|---|---|---|
| mean log-prob (baseline) | -0.037 [-0.069, -0.006] | True |
| zlib ratio (baseline) | 0.039 [-0.005, 0.082] | False |
| Min-K% (K=10) | 0.063 [0.035, 0.092] | True |
| Min-K% (K=30) | -0.017 [-0.034, -0.001] | True |
| Min-K% (K=50) | -0.034 [-0.060, -0.009] | True |

## Length

Token count (Qwen tokens): originals median 58 (mean 63.0), paraphrases median 64 (mean 67.46). AUROC of token count alone 0.421 [0.396, 0.443]. Median zlib bytes: originals 154, paraphrases 178.

## API ledger (paraphrases)

150 live calls to `claude-haiku-5-5` (returned model id(s): claude-haiku-5-5), 40107 input and 23508 output tokens, approx. $0.1576 at ASSUMED list prices of $1.00 / $5.00 per million input / output tokens (not read from the API). Cap: 200 calls, about $0.50.

## Outcome against the pre-registered predictions

1. K=20 AUROC below 0.5: **not met**. AUROC 0.645 [0.603, 0.686] -> separates.
2. If the K=20 CI is above 0.5, matched-length and residualised AUROC shrink towards 0.5: **not met** (matched 0.707, residualised 0.693).
3. Min-K% does not beat mean log-prob (difference CI includes 0): **not met**; AUROC difference -0.037 [-0.069, -0.006] (mean log-prob scores higher).
4. Token count alone differs from 0.5: **met** (AUROC 0.421 [0.396, 0.443]; paraphrases are longer).

No multiplicity correction is applied across scores and K. Any 'separates' verdict means only that the originals score higher than the paraphrases under this model; it is confounded with style and vocabulary and is not evidence of memorisation.


## Reading and limits

Decision rule (protocol): CI above 0.5 means the score separates originals from paraphrases, which is not proof of memorisation; CI including 0.5 means no detectable effect; CI below 0.5 means the paraphrases look more likely than the originals. Confounds: paraphrase style and length differ from the originals, the paraphrases come from one LLM with one prompt, the originals are only candidate members, and the model may have seen GSM8K-like data without the test split.
