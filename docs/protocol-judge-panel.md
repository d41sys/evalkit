# Protocol: PoLL-style judge panel and self-preference on MT-Bench

Committed before the first scored run. Data, subsample, prompts, aggregation rules, metrics, decision rules and budget below are fixed. Results are reported whatever they show, including losses. This extends `docs/protocol-judge-mtbench.md` (single judge `claude-sonnet-5-5`, 1,000 test items, already scored); everything not restated here is as there.

## Questions

1. **Panel.** Does a panel of three Claude judges of different size (Haiku, Sonnet, Opus; Verga et al. 2024, "Replacing Judges with Juries", the PoLL idea) agree with MT-Bench human votes better than the single Sonnet judge, and what does it cost?
2. **Self-preference.** On pairs that include `claude-v1`, do Claude judges favour the Claude answer more than the human votes do, and more than the released GPT-4 judge does?

All judge calls: Anthropic API, no logprobs, no sampling parameter sent (the models reject `temperature`), decoding is the API default. A re-run can differ from the recorded run; the call caches make scoring reproducible.

## Data and subsample

`data/mtbench/test.jsonl` (1,000 items, 72 questions; sha256 `216cd7828953adb3988a940a2252aab66b0ca0b8aa6c5b7226d63f1a504e9668`; items, human votes and released GPT-4 verdicts as in the judge protocol). 319 items (in 71 of the 72 questions) are `claude-v1` pairs: 75 vs llama-13b, 71 vs gpt-4, 64 vs gpt-3.5-turbo, 62 vs alpaca-13b, 47 vs vicuna-13b-v1.2.

**Why not all 319.** The budget (below) was sized from a pilot. Opus costs $0.034 per item (both orders) at the assumed prices, Haiku $0.009; judging all 319 `claude-v1` items with both new judges would cost about $13 against a cap of about $10. So the subsample is as large as the cap allows with a 25% margin: **160 items, 96 with `claude-v1` and 64 without** (a 60/40 split, chosen so the self-preference test gets most of the budget and the panel metrics still have non-Claude pairs). The two new judges run on exactly these 160 items; Sonnet already has all 1,000.

**Selection** (`scripts/mtbench_panel.py select --n-claude 96 --n-other 64`, seed 0): the 319 `claude-v1` items and the 681 others are sampled separately. Each group is stratified by turn × category (16 cells), cells get a largest-remainder share in proportion to their size, items inside a cell are drawn with `random.Random(0)` after sorting cells. No verdict, human vote or response text entered the selection. The ids are in `data/mtbench/panel-subsample.json` (sha256 `b66dd4068cdd436fc4fda028e6d88b630e58cbba7fd75651a2e0973e8711bf51`): 160 items, 67 questions, 80 per turn.

Dev/pilot data are separate from test data: the pilot used 15 of the 60 dev items (`data/mtbench/dev.jsonl`, 8 questions that are not in the test file).

## Pilot (dev items; counted in the ledger; done before this protocol was finalised)

15 dev items chosen by the same stratified rule (seed 0, turn × category), both orders, frozen prompt `judge-v1` (fingerprint `999579cc574d3989`), for `claude-haiku-5-5` and `claude-opus-5-5`: 30 calls each.

* Haiku with `max_tokens` 1024: 3 of 30 calls returned no verdict (two empty replies after 1,024 output tokens, one cut off mid-explanation). **Deviation from the single-judge protocol, set before scoring:** Haiku's cap is `max_tokens` 2048 in the scored run; the prompt is unchanged. The 30 Haiku pilot calls were repeated at 2048: all 30 parsed (max 1,184 output tokens). Sonnet's cached run (1,024) and Opus (1,024) keep their caps; Opus had no unparsable reply in the pilot (max 741 output tokens). The 1,024-token Haiku calls stay in the pilot cache and the ledger.
* Tokens per call relative to Sonnet on the same 15 items: input 1.00× (same prompt), output 1.92× (Haiku) and 1.32× (Opus). Projected cost of the 160-item subsample, both orders, at the assumed prices: Haiku $1.37, Opus $5.41, total $6.78 for 640 calls.
* No pilot agreement number is reported or used.

## Judges and calls

Panel = `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. Each judges each of the 160 items in both presentation orders (`evalkit.judge.Judge`, `max_tokens` as above). Sonnet's verdicts are the existing recorded calls in `data/mtbench/cache-test.jsonl` (same prompt, same cache key; not re-called, referenced from the scoring script, not copied). New calls go to `data/mtbench/cache-panel-haiku.jsonl` and `data/mtbench/cache-panel-opus.jsonl`. A reply with no parsable verdict is `invalid`.

## Aggregation (both pre-registered, both reported)

Per judge: the **resolved verdict** keeps the verdict if both orders agree, otherwise `tie` (an `invalid` reply makes it `tie`).

* **(a) Majority vote (primary).** The three resolved verdicts vote; the side with at least 2 of 3 wins; anything else is `tie`. This includes the 3-way split A/B/tie and 1 A + 2 ties.
* **(b) Mean vote (secondary).** The six per-order signed verdicts (A = +1, B = -1, tie = 0, `invalid` = 0) are averaged. Mean above **+0.2** gives A, below **-0.2** gives B, otherwise tie. With six verdicts the mean moves in steps of 1/6, so the band makes a net margin of one verdict a tie and needs a margin of at least two. No other band is tried.

Panel position-flip rate: the aggregation applied to the three judges' first-order verdicts alone and to their second-order verdicts alone; the item flips if the two differ (items where any judge had an invalid reply excluded, as for single judges).

## Metrics

Computed on the same 160 items for Haiku, Sonnet, Opus, panel (a) and panel (b), with the code of the judge protocol (`evalkit.judge_stats`): judge-human agreement S1 (ties count) and S2 (no ties) with the per-item share of human votes matched; Cohen's kappa S1 (3 labels) and S2 (A/B); position-flip rate and same-slot rate; resolved-tie rate; Spearman rho of the verdict with the length difference; the human-human reference (S1/S2) and the released GPT-4 pairwise reference on the same items. **Intervals:** cluster bootstrap over questions, 2,000 resamples, seed 0, whole questions resampled; every difference is computed on the same resample as its two terms (paired). Paired differences: panel minus each single judge, and panel minus Sonnet (Sonnet restricted to the same subsample). Subgroups reported (descriptive, not corrected): items with / without `claude-v1`, turn 1, turn 2. Sonnet on all 1,000 test items is quoted from the same machinery for context.

Panel-specific: pairwise Cohen's kappa between the three judges' resolved verdicts (3 labels, cluster-bootstrap CI), and the cost per 1,000 resolved item verdicts (a resolved item verdict = both orders = 2 calls) for each judge and for the panel (sum of the three), from the tokens in the caches at the assumed prices.

**Assumed prices (not read from the API; the model ids are not in any price list I could query), US dollars per million input/output tokens: Haiku $1/$5, Sonnet $3/$15, Opus $5/$25.** If the real list prices differ the dollar figures scale; token counts are reported as recorded.

## Decision rules (margin 5 percentage points)

Applied to the 95% CI of a paired difference Δ = panel minus Sonnet (same subsample):

* **superior** if the CI lower bound is above 0 (the panel is "better than Sonnet");
* **inferior** if the upper bound is below 0;
* **non-inferior** if the lower bound is above -5 pp and the CI includes 0;
* otherwise **inconclusive**.

The **primary** test is aggregation (a), agreement S1. S2 and aggregation (b) are secondary, reported with the same rule; no claim picks the better of (a) and (b). The same rule is shown against Haiku and Opus as descriptive. With about 160 items from 67 questions the CI half-width is expected near 4-5 pp, so "inconclusive" is the likely outcome unless the true difference is large; it will be stated as inconclusive, not as "equal". Kappa and flip-rate differences, the judge-judge kappas and the cost comparison are descriptive. Quality vs cost: the panel costs about 3.4× Sonnet per verdict (predicted from the pilot ratios: Haiku $8.6, Sonnet about $17.4, Opus $33.8 per 1,000 verdicts), so a panel that is only non-inferior to Sonnet is a worse deal and is reported so.

## Self-preference test

Items: the `claude-v1` pairs (every one of them has cached Sonnet verdicts; the new judges have the 96 in the subsample, which are the primary items). Per item, with `claude-v1`'s side as the reference:

excess = (judge score for claude-v1) − (mean human vote score for claude-v1 on that item); both coded +1 win, 0 tie, -1 loss, the judge score resolved over both orders (equal verdicts stand, else tie), the human score the mean over the item's votes.

* **Primary statistic:** mean excess for each Claude judge (Haiku, Sonnet, Opus) over the 96 items, with a cluster-bootstrap 95% CI over questions (whole questions resampled, 2,000 resamples, seed 0).
* **Control / secondary:** the same excess for the released GPT-4 pairwise verdicts (a non-Claude judge, `tie (inconsistent)` = tie) on the same items, and the paired difference "Claude judge excess minus GPT-4 excess" with a CI. The human term cancels in the difference.
* **Panel excess** (a) and (b) and Sonnet on all 319 `claude-v1` pairs are reported as extras, descriptive.
* **Opposite direction, descriptive:** the same quantities split by opponent: vs gpt-4 (where `claude-v1` is the weaker model), vs gpt-3.5-turbo, and vs llama-13b / alpaca-13b / vicuna-13b-v1.2 (where it is the stronger). The split is by opponent, not by human outcome, to avoid selecting on the noisy human votes.

**Interpretation rule, fixed in advance.** Mean excess CI entirely above 0: evidence that the judge favours the Claude answer beyond human preference. CI including 0: no detectable effect (not evidence of none). CI entirely below 0: the judge favours the Claude answer less than humans do. For the difference to GPT-4: CI above 0 means the Claude judge drifts toward `claude-v1` more than the GPT-4 judge does, which is what "Claude judges like Claude" predicts; CI including 0 means no detectable difference from GPT-4's drift. No correction for the six primary-and-control intervals is applied; claims cite the number of looks.

**What the test cannot show.** (1) It cannot separate self-preference from **family affinity**: `claude-v1` is an older, different model than the three judges, so a positive excess means "style of the Claude family", not recognition of the judge's own output. (2) Humans are noisy (human-human agreement about 67% S1 and 84% S2 in the judge protocol, mostly 1-3 votes per item), so the excess has a noise floor and regression-to-the-mean effects when `claude-v1` is far stronger or weaker than its opponent. (3) The GPT-4 control is not free of bias either: GPT-4 may favour its own answers, which lowers its excess on `claude-v1` vs gpt-4 pairs and pushes the Claude-minus-GPT-4 difference up there; the by-opponent split shows this. (4) The primary sample is 96 items from 53 questions (by opponent: llama-13b 29, alpaca-13b 23, gpt-3.5-turbo 17, vicuna-13b-v1.2 15, gpt-4 12): only a large excess is detectable, and the opposite-direction split has 12 items vs gpt-4.

## Budget and ledger

At most **1,800 live API calls and about $10** (assumed prices) in total for this task, pilot included. Ledger before the scored run: pilot 90 calls (Haiku 60, Opus 30), $0.69 assumed. Scored run: 640 calls (160 items × 2 orders × 2 new judges), projected $6.78, projected total $7.46 (25% under the cap). The run script stops a judge if its assumed cost passes $1.60 (Haiku) / $6.00 (Opus). The call cap per judge is 320. The final report repeats the ledger from the caches (calls, input/output tokens, assumed cost); failed HTTP attempts retried by the SDK are not in the caches and not counted.

## Limitations stated in advance

One prompt, one run per item and judge, decoding at API default; Haiku's token cap differs from the other two (above); subsample 160 of 1,000 items, 60% of them `claude-v1` pairs, so panel numbers are not the full-test numbers (Sonnet on the same subsample is the comparison); no reference answers (as in the judge protocol); the human votes are experts and the dataset authors; no comparison with published numbers is made (the setup differs).
