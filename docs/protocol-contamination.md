# Protocol: GSM8K contamination probe (GSM-Symbolic-style number perturbation)

Status: pre-registered. Committed together with the built dataset and **before any scored API call** (0 of 900 calls used at commit time).

## Question

Do two Anthropic models solve GSM8K test problems less often when only the numbers are changed than when the original numbers are used?

Rationale: if a model has memorised the original test items, accuracy on the original problem should exceed accuracy on structurally identical problems with fresh numbers. This is the idea of GSM-Symbolic (Mirzadeh et al. 2024, arXiv 2410.05229). This study is a much smaller, number-only, deterministic-gold version of it. **No number from that paper is compared with ours** (different items, prompts, models, protocol).

## Interpretation rules (fixed now)

1. A significant drop is consistent with memorisation of the originals **or** with brittleness to changed numbers. The probe cannot separate the two.
2. No detectable drop is **no evidence of contamination by this probe**. It is not proof of its absence. The minimum detectable effect (MDE) is quoted next to every null.
3. A negative drop (perturbed accuracy higher) is reported as such.
4. One sample per prompt, default sampling (no temperature parameter can be sent; the models reject it). Sampling noise is part of every per-source difference and is not controlled.
5. The subset is restricted to problems whose annotated solution is parsable and cleanly templatable. Results apply to that subset, not to all of GSM8K.
6. `claude-sonnet-4-5-20250929` is a deliberately older model, assumed to have had longer public exposure to GSM8K. That assumption is not verified; no confirmatory claim depends on it.

## Data and split

- Source: GSM8K test split (1319 rows), `raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl`, sha256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`.
- Order: `random.Random(0).shuffle(list(range(1319)))` (same permutation as `scripts/build_gsm8k_subset.py`). Items are examined in this order.
- Pool: every item passing the solver checks below, in permutation order.
- Eyeball pass: I examined the pool in order and dropped items whose perturbed text is incoherent (reasons recorded in `data/contamination/eyeball_drops.json`). The first **146 kept** items are used: **dev = first 6, test = next 140**. Items after the 146th kept are not part of the dataset.
- Dev and test are disjoint. Dev is used only for the pilot (parse rate, truncation, tokens per call, cost projection). No prompt or rule is tuned on test.

### How each template is produced (no LLM writes or checks gold)

GSM8K solutions carry calculator annotations `<<expr=result>>`. For each question:

1. Every number in the question (digits or number words) becomes a **slot**.
2. Every annotation becomes a **step** whose operands are: a slot, an earlier step result, a percent slot written as `slot/100`, or a licensed implicit constant (a word in the question such as "twice", "dozen", "week").
3. The step list is replayed with exact `Fraction` arithmetic. A template is kept only if the replay on the original numbers reproduces every annotated result **and** the GSM8K final answer, and if rendering the original numbers reproduces the question text exactly.
4. Variant gold is computed only by that deterministic replay on the new numbers (`evalkit.contamination.solve`).

Solver-check rejections, counted at the first failing check over all 1319 items:

| check | rejected |
|---|---|
| unsupported question format | 14 |
| no calculator annotations | 18 |
| expression outside + - * / ( ) | 53 |
| unmapped constant (a literal in a step that no word of the question licenses) | 185 |
| ambiguous operand (a step number matches several slots/results, no unique mapping) | 288 |
| annotated result not reproduced by the replay | 0 |
| final answer not reproduced / not a positive integer | 66 |
| no perturbable slot | 48 |
| no feasible pair of variants | 115 |
| **kept by solver checks (pool)** | **532** |

Eyeball pass: 152 pool items examined in order, **6 dropped** as incoherent, **146 kept**.

**Slots.** 555 slots in the 146 kept templates; **165 are frozen** (never perturbed): value 0 or 1 (37); value occurs twice in the question (57); part of a fraction (18); small number (<= 12) used twice in the solution, so one use may be an implicit constant (17); implicit constant licensed by a word (17); not used by the solution (8); time, ordinal, label (6); year-like (3); calendar-bounded count (2). Freezing instead of rejecting is the main safeguard against hidden implicit constants.

**Rules added during development.** The rules were written while I looked at the first ~260 pool items and the variants they produced, **before any model call**. The test items are inside that prefix. Cases that triggered a rule: a derived constant that equals a sum or product of non-invariant numbers; a licensed constant that coincides with a computed result; a percent used without /100; a calendar bound (days per week, weeks per year); two numbers whose order matters (a goal above the amount raised). The rules are final and listed in the module docstring; they are not changed after the first API call.

### Perturbation constraints (per slot and per variant)

- Only numbers change. **Names, nouns and wording are not changed** (not done, to limit incoherence).
- Frozen slots are unchanged. Others: same integer-digit count, same decimals, between -50% and +50% of the original (symmetric, so numbers do not drift upward), at least 2 when the original is, same roundness (multiple of 10, 5, 0.5, ... stays one), percentages <= 99.
- The strict order of every pair among question numbers and step results is preserved when strict in the original.
- Each step result keeps its sign; integer steps stay integer; other steps keep at most max(2, original) decimals; each step result is within [1/4, 4] of the original.
- The final answer is a positive integer different from the original gold.
- The two variants differ from each other in numbers and in gold. Variant k uses `random.Random(f"{id}|variant|{k}")`.

Each source gives 3 prompts: `#v0` original, `#v1`, `#v2`.

### Frozen artefacts

| file | sha256 |
|---|---|
| `data/contamination/items.jsonl` | `884f0e78d841b5e3c103558949eaa8086c6bf6eeb7e7d4a35571f282642bae2f` |
| `data/contamination/templates.jsonl` | `b2cf2859c60fcf998af602fff6b765e98a1169c498ef398da21eaa345593d8a4` |
| `data/contamination/build_report.json` | `8363f39e7b08442e0553ac469f304d46b6cc1f4fd3d629cd6296008c5d57a4d5` |
| `data/contamination/eyeball_drops.json` | `bf80b79666a1189d6f5dddbb3c442aeea3defa0eddf743beee5b44f2cd7f7128` |

Difficulty neutrality of the gold answers (test, 140 sources, 280 variants; descriptive, reported again in the results): same digit count in 85.7% of variants, 8.2% more digits, 6.1% fewer; median gold 76.5 original vs 79.5 variant; mean log10(variant/original) = +0.044 (variants are about 10% larger on average, 64% are larger). Residual upward drift is a known confound, reported with the result.

## Models and prompt

Models: `claude-haiku-5-5` and `claude-sonnet-4-5-20250929`. Each is called through `evalkit.llmcache.CachedCompleter` + `evalkit.models.AnthropicModel`. **No sampling parameter is sent. No system prompt.** Every call is cached in `data/contamination/cache-<model>.jsonl`; scoring replays offline and never needs the key.

Prompt `gsm-cot-v1` (frozen; the question text replaces `{question}`):

```
Solve the following math problem. Think step by step, then write the final answer on the last line in exactly this format: Answer: <number>
Use digits only in the final line (no units, no commas, no words).

Problem: {question}
```

`max_tokens` = 1024. Ladder: if any dev reply reaches `output_tokens >= 1024`, only the truncated dev prompts are rerun at 2048 (counted in the ledger) and test uses 2048 for all prompts. Truncated replies are scored as they are. No retry of wrong or unparsable replies.

## Metrics

- Primary: `numeric_match(reply, str(gold))` (`evalkit.metrics.classical`): the number after the last `Answer:` marker, otherwise the last number in the reply. No number = wrong.
- Robustness (descriptive): HELM `final_number_exact_match` (`evalkit.metrics.helm_compat`), same analysis.
- A source is analysed for a model only if all 3 of its prompts have a cached reply (complete case); omissions are reported.

## Statistics

Per model, per source i: `d_i = acc(original_i) - mean(acc(v1_i), acc(v2_i))`. The **drop** is the mean of `d_i`; the cluster is the source.

- 95% cluster-bootstrap CI (10000 resamples, seed 0) and a 97.5% CI (Holm-worst-case level for 2 models): `evalkit.clustered.cluster_bootstrap_ci`.
- Sign-flip randomisation test of mean(d_i) = 0, two-sided (`evalkit.aggregate.randomization_test_p`, 10000 resamples, seed 0), Holm-adjusted over the 2 models.
- Per-variant drops (original - v1, original - v2) with 95% CIs; exact McNemar of original vs v1 (and v2), descriptive.
- MDE at 80% power from the observed SD of `d_i` (`minimum_detectable_effect`, alpha .05 and .025).
- Descriptive only: difference of drops (Sonnet 4.5 minus Haiku 5.5) per source with a cluster-bootstrap CI.

## Decision rule (pre-registered)

Per model:

- **significant drop** if drop > 0 **and** Holm-adjusted p < 0.05 **and** the 97.5% CI lower bound > 0;
- **borderline** if drop > 0 and exactly one of the two holds;
- **negative drop** if drop < 0 (called significant only if Holm p < 0.05 and the 97.5% upper bound < 0);
- otherwise **no detectable drop**; wording "no detectable effect" whenever the CI includes 0.

Predictions (written before the run, no direction confirmed or refuted by them): original accuracy of both models is high (>= 85%); drops are small, below the MDE for most of the range of plausible effects; the older Sonnet 4.5 is not expected to differ detectably from Haiku 5.5.

## Budget

- Hard cap: **900 live calls and about $4**, pilot included. Dev: 6 sources x 3 x 2 models = 36 calls. Test: 140 x 3 x 2 = 840. Total 876, 24 spare for the max_tokens ladder or failed calls. The cap counts records in all cache files.
- List prices are **ASSUMED, not read from the API**: Haiku 5.5 $1 / MTok input, $5 / MTok output; Sonnet 4.5 $3 / $15.
- After dev: project test cost from the measured mean tokens per call per model; if projection x 1.25 plus the dev cost exceeds $4, the test set is truncated to the first N sources in `items.jsonl` order (all 3 prompts, both models), N the largest value meeting the rule. Pre-registered; nothing else about the test set changes.
- Ledger (calls, tokens, cost per model) is in the results document.

## Limitations

- 140 sources: only drops of roughly 7 to 10 points are detectable (a-priori guess; the observed MDE is reported).
- Templatable subset only (532 of 1319 pass the checks, 40%); simple arithmetic traces are over-represented.
- Hidden implicit constants and incoherent perturbed text can remain; I eyeballed the pool alone (no second rater). Incoherent variants lower perturbed accuracy and would mimic contamination.
- Numbers only; GSM-Symbolic also changes names and adds clauses.
- Variants are slightly larger on average (see neutrality above).
- Single sample per prompt with default sampling.
- Exposure of a model to GSM8K is not observable; the probe can only show a gap.

## Procedure

1. Commit this protocol and the dataset (this commit).
2. `scripts/contamination_probe.py run --split dev` (pilot). Check truncation, parse rate, tokens; apply the ladder and the cost rule.
3. `scripts/contamination_probe.py run --split test`.
4. `scripts/contamination_probe.py score` (cache only) writes `docs/results/contamination-gsm.md` and `.json`.
5. A bug found after step 3 is fixed with a regression test and both results are reported; a limitation is a finding, not a patch.
