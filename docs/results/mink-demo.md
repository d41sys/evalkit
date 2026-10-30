# Min-K% Prob demo (Qwen2.5-0.5B, GSM8K test vs Claude paraphrases)

**A DEMO of the Min-K% Prob method on a tiny model. It is not a contamination audit of Qwen2.5-0.5B, of any other model, or of GSM8K.** Protocol: `docs/protocol-mink.md` (committed before scoring). Reproduce: `uv run --offline python scripts/mink_demo.py report` (replays committed caches; no model, key or network).

- Model `Qwen/Qwen2.5-0.5B` revision `060db6499f32faf8b98477b0a26969ef7d8b9987`, float32; log-probs under teacher forcing after a prepended `<|endoftext|>` context token.
- 150 questions selected (`random.Random(0)`), 132 kept after the number-multiset check; dropped: {'numbers_differ': 18}.
- Statistic: AUROC of originals (label 1) vs paraphrases (label 0); 95% paired cluster-bootstrap CI over source questions, 2000 resamples, seed 0.

## Primary result and baselines

| score | AUROC [95% CI] | verdict | matched-length AUROC | residualised AUROC | orig > para (win rate) |
|---|---|---|---|---|---|
| Min-K% (K=10) | 0.486 [0.425, 0.546] | no detectable effect | 0.485 [0.420, 0.556] | 0.487 [0.426, 0.545] | 0.500 [0.417, 0.583] |
| Min-K% (K=20) **primary** | 0.535 [0.477, 0.594] | no detectable effect | 0.551 [0.489, 0.616] | 0.533 [0.475, 0.592] | 0.561 [0.477, 0.636] |
| Min-K% (K=30) | 0.555 [0.498, 0.611] | no detectable effect | 0.574 [0.511, 0.642] | 0.552 [0.495, 0.610] | 0.583 [0.500, 0.659] |
| Min-K% (K=50) | 0.589 [0.533, 0.643] | separates | 0.602 [0.538, 0.670] | 0.585 [0.528, 0.639] | 0.659 [0.576, 0.735] |
| mean log-prob (baseline) | 0.624 [0.568, 0.677] | separates | 0.627 [0.561, 0.697] | 0.622 [0.567, 0.674] | 0.697 [0.614, 0.773] |
| zlib ratio (baseline) | 0.531 [0.475, 0.585] | no detectable effect | 0.524 [0.456, 0.597] | 0.513 [0.455, 0.572] | 0.576 [0.492, 0.659] |

Matched-length AUROC uses the 2878 of 17424 (original, paraphrase) pairs whose token counts differ by at most 5. Residualised: OLS of the score on token count, refit in every resample.

## AUROC of the primary score minus another score (same resamples)

| other score | difference [95% CI] | CI excludes 0 |
|---|---|---|
| mean log-prob (baseline) | -0.089 [-0.125, -0.051] | True |
| zlib ratio (baseline) | 0.004 [-0.031, 0.041] | False |
| Min-K% (K=10) | 0.049 [0.022, 0.076] | True |
| Min-K% (K=30) | -0.020 [-0.037, -0.004] | True |
| Min-K% (K=50) | -0.054 [-0.084, -0.027] | True |

## Length

Token count (Qwen tokens): originals median 58 (mean 63.11), paraphrases median 64 (mean 67.55). AUROC of token count alone 0.421 [0.396, 0.443]. Median zlib bytes: originals 154, paraphrases 178.

## API ledger (paraphrases)

150 live calls to `claude-haiku-5-5` (returned model id(s): claude-haiku-5-5), 40107 input and 23508 output tokens, approx. $0.1576 at ASSUMED list prices of $1.00 / $5.00 per million input / output tokens (not read from the API). Cap: 200 calls, about $0.50.

## Outcome against the pre-registered predictions

1. K=20 AUROC below 0.5: **not met**. AUROC 0.535 [0.477, 0.594] -> no detectable effect.
2. If the K=20 CI is above 0.5, matched-length and residualised AUROC shrink towards 0.5: **not met** (moot: the K=20 CI is not above 0.5) (matched 0.551, residualised 0.533).
3. Min-K% does not beat mean log-prob (difference CI includes 0): **not met**; AUROC difference -0.089 [-0.125, -0.051] (mean log-prob scores higher).
4. Token count alone differs from 0.5: **met** (AUROC 0.421 [0.396, 0.443]; paraphrases are longer).

No multiplicity correction is applied across scores and K. Any 'separates' verdict means only that the originals score higher than the paraphrases under this model; it is confounded with style and vocabulary and is not evidence of memorisation.


## Reading and limits

Decision rule (protocol): CI above 0.5 means the score separates originals from paraphrases, which is not proof of memorisation; CI including 0.5 means no detectable effect; CI below 0.5 means the paraphrases look more likely than the originals. Confounds: paraphrase style and length differ from the originals, the paraphrases come from one LLM with one prompt, the originals are only candidate members, and the model may have seen GSM8K-like data without the test split.
