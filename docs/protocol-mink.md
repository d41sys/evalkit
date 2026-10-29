# Protocol: Min-K% Prob demo on a tiny local model

Committed before the first scored run. Everything below (data, prompts, K, baselines, metrics, bootstrap, decision rule, predictions) is fixed; results are reported whatever they show, including a null or reversed result.

**This is a DEMO of the Min-K% Prob method on a 0.5B-parameter model. It is not a contamination audit of Qwen2.5-0.5B, of any other model, or of GSM8K.** The comparison below cannot establish memorisation (see Confounds). It exists to show that `evalkit.mink` implements the method, runs end to end offline from committed caches, and reports an honest CI.

## Question

Does Min-K% Prob, computed under `Qwen/Qwen2.5-0.5B`, separate 150 original GSM8K test questions from fresh paraphrases of the same questions? A higher score is read as "more likely seen in training" (Shi et al. 2023, "Detecting Pretraining Data from Large Language Models", arXiv [2310.16789](https://arxiv.org/abs/2310.16789)).

## Method

For a text with per-token log-probabilities `l_1..l_n` under teacher forcing, `Min-K%(K) = mean of the lowest max(1, floor(n*K/100)) values of l`. Higher means more likely a training member. This follows the `int(len * ratio)` rule of the authors' reference code with a floor of one token.

## Data

- **Originals (label 1, "member candidates")**: 150 questions of GSM8K `test` (Cobbe et al. 2021, [openai/grade-school-math](https://github.com/openai/grade-school-math), MIT). `grade_school_math/data/test.jsonl` (1319 rows) is downloaded to the gitignored `data/raw/gsm8k_test.jsonl`. Selection: `random.Random(0).shuffle(list(range(1319)))`, first 150 indices (the same permutation `scripts/build_gsm8k_subset.py` uses, so this is the first 150 rows of its subsets). Only the `question` field is scored (no answer, no chain of thought).
- **Paraphrases (label 0, "non-members")**: each of the 150 questions rewritten once by `claude-haiku-5-5` (one API call each, no sampling parameter sent, `max_tokens=512`), cached in `data/mink/paraphrase-cache.jsonl` through `evalkit.llmcache.CachedCompleter`. System prompt: `You rewrite math word problems. Output only the rewritten problem.` User prompt:

  ```
  Rewrite the following math word problem.
  Rules:
  - Keep every number, quantity, name and entity exactly. Digits stay digits; do not spell numbers out, round, or convert units.
  - Change the wording and the sentence structure (reorder clauses, use different verbs and connectors, split or merge sentences).
  - Add no new information and no hints, remove nothing, and do not solve it.
  - Output only the rewritten problem, with no preamble.

  Problem:
  {question}
  ```

- **Validity filter**: a paraphrase is kept only if the multiset of numbers (regex `\d+(?:,\d{3})*(?:\.\d+)?`, thousands commas removed) equals the original's, it is non-empty, and it differs from the original after whitespace normalisation. Failures are dropped together with their original (the unit is the pair) and counted in the report. There is no retry. Dropping can favour questions that are easier to paraphrase; this is a limitation. The filter checks digit numbers only, not number words or entities.
- Pilot: the first 5 selected questions are paraphrased first to measure tokens per call and to check the filter and the cost projection. The prompt above is frozen after that pilot; the pilot calls are cached, reused in the full run and counted in the ledger. No scored quantity (log-prob, AUROC) is computed before this protocol is committed, so there is no dev/test split of scores and nothing to tune: K and every statistic are pre-set.

## Scoring convention

- Model: `Qwen/Qwen2.5-0.5B` (base, public, ungated, Apache-2.0), revision `060db6499f32faf8b98477b0a26969ef7d8b9987` (Hub `sha` at planning time), `model.safetensors` only (988,097,824 bytes), float32 on Apple MPS when available, else CPU.
- Qwen has no BOS token. The input is `[<|endoftext|>] + tokens(text)`: the end-of-text token (id 151643) is prepended as the context so that the first real token is also scored; every token of the text gets a log-probability `log softmax(logits)[token]` under teacher forcing. Raw text, no chat template, no prefix such as "Question:", texts truncated to 512 tokens (GSM8K questions are far shorter). The stored per-token log-probs, token strings and ids go to `data/mink/logprobs-qwen2.5-0.5b.jsonl`, so the metrics replay without the model.
- Scores (higher = more member-like):
  - **Min-K%** at K in {10, 20, 30, 50}; **K=20 is primary**, the others are reported as pre-set sensitivity, not chosen between.
  - **Mean log-prob** (negative log-perplexity) over all tokens: baseline.
  - **Zlib ratio** `sum(logprob) / zlib_len` with `zlib_len = len(zlib.compress(text.encode("utf-8"), 9))` bytes: reference-style baseline after Carlini et al. 2021 (arXiv [2012.07805](https://arxiv.org/abs/2012.07805)); `sum(logprob)` is negative, so a higher value means more probable relative to compressibility.

## Metrics

- **AUROC** of separating originals (label 1) from paraphrases (label 0) by the score, ties counting 1/2 (Mann-Whitney).
- **95% CI**: paired (cluster) bootstrap over the source question: resample the kept pairs with replacement, carrying the original and its paraphrase together, recompute the AUROC; 2000 resamples, seed 0, percentile interval. Differences between two scores' AUROCs use the same resamples.
- **Length-matched sensitivity** (both with the same bootstrap):
  1. *Matched-pair AUROC*: the AUROC restricted to (original, paraphrase) pairs of texts whose token counts differ by at most 5 tokens (pre-set), with the number of such pairs reported.
  2. *Residualised AUROC*: score regressed by ordinary least squares on token count (refit in every resample on all 2n texts), AUROC of the residuals.
- Also reported (descriptive): median token counts per class, the fraction of questions whose original outscores its own paraphrase (paired win rate, bootstrap CI), and the AUROC of token count alone (how much length by itself separates the classes).

## Decision rule (fixed now)

Primary: AUROC of Min-K% at K=20.

- CI entirely above 0.5: "the score separates originals from paraphrases". This is **not** proof of memorisation: it is exactly what the confounds below would also produce.
- CI includes 0.5: **no detectable effect** at this sample size.
- CI entirely below 0.5: the paraphrases look more likely than the originals, the reverse of the memorisation direction; reported as a style/length effect.

The same rule is applied to each other K and baseline, descriptively; no multiplicity correction, no switch of the primary after seeing results. "Min-K% beats the baseline" is claimed only if the paired-bootstrap CI of the AUROC difference excludes 0.

## Predictions (before scoring)

1. K=20 AUROC falls below 0.5 (CI below or touching 0.5): an LLM paraphrase is smoother, more conventional English than the human-written original, and small models assign such text higher probability. I put roughly 60% on this, 25% on a CI that includes 0.5, 15% on a CI above 0.5.
2. Even if the K=20 CI is above 0.5, the length-matched and residualised AUROCs shrink towards 0.5.
3. Min-K% does not beat mean log-prob: the CI of their difference includes 0 (about 75%).
4. The AUROC of token count alone differs measurably from 0.5, because paraphrases are not length-matched.
5. A 0.5B model was trained on more than 10T tokens, GSM8K-like data is plentiful and decontamination is imperfect, so a small genuine memorisation signal cannot be excluded; this design cannot separate it from the confounds.

## Confounds and limitations (stated up front)

- **Style**: paraphrases are LLM-written and differ in style, register and sentence structure from the crowd-written originals; a score can separate them for that reason alone.
- **Length**: token counts differ between the classes (paraphrases usually longer); Min-K% averages the lowest `floor(nK/100)` tokens, so it depends on length. The sensitivity analyses reduce, not remove, this.
- **Not a membership ground truth**: paraphrases are non-members only in the sense that they cannot appear in pre-2024 corpora. The originals are only *candidate* members: the model may or may not have seen the GSM8K test split, and it may have seen GSM8K-like data (train split, synthetic variants, benchmark discussions) without it. No known-member positive control is used.
- **One paraphraser, one paraphrase per question**, one prompt, one model; the paraphraser's idiosyncrasies are shared by all negatives.
- n = at most 150 pairs, so CIs are wide; a small effect is not detectable.
- The validity filter drops pairs (counted), and checks digits only.
- Results say nothing about GSM8K contamination of larger models and are not comparable to published Min-K% numbers (WikiMIA, MIMIR), which use other data and membership labels.

## Budget

- Disk: new model files at most 1.2 GB (`model.safetensors` is 0.99 GB); `du -sh ~/.cache/huggingface` before and after is reported.
- API: at most 200 live calls (150 planned + the pilot is part of the 150) and about $0.50 in total. Prices are ASSUMED (list prices not read from the API): claude-haiku-5-5 at $1.00 per million input tokens and $5.00 per million output tokens. The ledger (calls, tokens, cost) is in the results document.
- Everything replays offline: `uv run --offline python scripts/mink_demo.py report` needs neither the key nor the model nor the network.

## Outputs

`data/mink/paraphrase-cache.jsonl`, `data/mink/pairs.jsonl` (selected originals, paraphrases, filter status), `data/mink/logprobs-qwen2.5-0.5b.jsonl`, `docs/results/mink-demo.md` and `docs/results/mink-demo.json`; code in `src/evalkit/mink.py` (numpy-only core; torch and transformers are imported only inside `scripts/mink_demo.py score`) and `scripts/mink_demo.py`; tests in `tests/test_evalkit_mink.py`.
