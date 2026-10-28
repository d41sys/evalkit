# Protocol: LLM judge vs MT-Bench human judgments

Committed before the first scored run on the test split. The data, split, prompts, metrics, decision rules and call budget below are fixed. Results are reported whatever they show, including losses.

## Question

Does `evalkit judge` (pairwise, both orders, inconsistent verdicts resolved to tie) agree with human expert preferences on MT-Bench as well as the GPT-4 judge of Zheng et al. 2023 (arXiv 2306.05685), and does it show position or length bias?

Judge: `claude-sonnet-5-5` via the Anthropic API, called through `evalkit.llmcache` (every call recorded in a tracked JSONL cache; scoring reads the cache). No logprobs. The model rejects the `temperature` parameter (HTTP 400, "Extra inputs are not permitted"; probed once on 2026-10-29), so no sampling parameter is sent and decoding is the API default. A re-run can differ from the recorded run; the cache is what makes scoring reproducible.

## Data

`lmsys/mt_bench_human_judgments` (CC-BY-4.0, revision `f7d2896d2cc5d80f8b55c2bbc722613555233c25`): 3,355 expert human votes (`human` split) on 80 two-turn questions and 6 models, plus 2,400 GPT-4 pairwise verdicts (`gpt4_pair` split, Zheng et al.'s released judgments). No parquet reader is installed and none may be added, so `scripts/mtbench_judge.py fetch` reads the same table through the Hugging Face datasets-server rows API.

An **item** is (question, unordered model pair, turn). Votes on the same item are grouped (1,814 items; 1-7 votes each). Each item is oriented once: `A` is the alphabetically first model name, and human and GPT-4 labels are re-oriented to it. The released GPT-4 verdict is `A`, `B` or `tie` (its `tie (inconsistent)` label counts as tie, as in Zheng et al.'s S1).

## Splits (seed 0, `scripts/mtbench_judge.py build`)

* **Dev**: one question per category (writing, roleplay, reasoning, math, coding, extraction, STEM, humanities) drawn with `random.Random(0)`: questions 85, 98, 109, 115, 127, 137, 147, 151. 60 items sampled from those questions' 176 items. Used only to check that prompts parse and to choose `max_tokens`. **Dev size: 60 items, 8 questions, 132 human votes, 120 API calls.**
* **Test**: 1,000 items sampled with the same generator from the 1,638 items of the other 72 questions. Whole dev questions are excluded, so no dev question appears in test. 1,816 human votes.

`data/mtbench/dev.jsonl` (sha256 `05d7f167ee21354922f02f4eb20e6643bca3218be3b4ec727b80e6b851bd807f`) and `data/mtbench/test.jsonl` (sha256 `216cd7828953adb3988a940a2252aab66b0ca0b8aa6c5b7226d63f1a504e9668`) are tracked. The responses are shown verbatim from the dataset.

## Judging

Prompt version `judge-v1`, fingerprint `999579cc574d3989` (`evalkit.judge.prompt_fingerprint()`), frozen after one dev run. `max_tokens` 1024 (a first dev smoke with 400 truncated one reply before its verdict line; that run was discarded and is counted below). Each item is judged twice, once per presentation order. The judge replies with a short explanation and a final `VERDICT: A|B|TIE` line.

* Turn 1: the user's first question and the two first replies.
* Turn 2: each response block is the assistant's full two-turn conversation; the judge is told to judge the reply to the second user message.
* **No reference answers.** The dataset has none. Zheng et al. gave GPT-4 reference answers for math, reasoning and coding. The categories are reported separately.
* Resolution: equal verdicts in both orders stand; any disagreement or an unparsable reply gives `tie`. The unparsable count is reported; if it exceeds 5% of items the run is reported as failed rather than tuned.

## Metrics (all on the test split; unit = item; clusters = question)

Following Zheng et al. App. D.3:

* **Judge-human agreement**: per item, the share of its human votes the judge matches; mean over items. **S1** counts `tie` as a label; **S2** drops every (judge, vote) pair where either side is a tie and items left with no pair.
* **Human-human agreement**: per item, the share of agreeing pairs of votes from different humans; mean over items with at least one such pair. S1 and S2 as above.
* **Cohen's kappa** between judge and human votes, pooled over (item, vote) rows: 3 labels (S1) and the 2 non-tie labels (S2).
* **Matched difference** (judge minus human-human): both agreements restricted to the items where human-human agreement is defined.
* **Same-items difference** (judge minus released GPT-4): both agreements on the same items.
* **Position-flip rate**: share of items whose two orders name different verdicts, over items where both replies parsed. Also the same-slot rate (the same position won in both orders).
* **Length**: Spearman rho of the resolved verdict (A=+1, tie=0, B=-1) with the length difference (words of the judged assistant reply, A minus B), for the judge and for the mean human vote per item; their difference; and the share of decided pairs won by the longer reply.
* **Intervals**: percentile 95% intervals from a cluster bootstrap over the 72 test questions (2,000 resamples, seed 0, whole questions resampled; every statistic and every difference is computed on the same resample). Rank correlations rank the original sample once and reweight.

## Decision rules

Margin $\delta = 5$ percentage points, applied to the 95% CI of a difference $\Delta$.

1. **Against GPT-4 (like-for-like, primary).** $\Delta$ = judge minus released GPT-4 pairwise agreement with humans on the same items, for S1 and for S2. *Superior* if the CI lower bound is above 0; *non-inferior* if it is above $-\delta$; *inferior* if the upper bound is below 0; otherwise *inconclusive*.
2. **Against human-human.** Same rule on the matched difference.
3. **Against the published numbers.** Zheng et al. Table 5 gives GPT-4-pair vs human 66% (S1) / 85% (S2) on first turns and 66% / 84% on second turns, human-human 63% / 81% and 67% / 82%. They are quoted for context only and called **comparable** only if the protocol matches. It does not match: our prompt differs, no reference answers, the judge model cannot be run at temperature 0, 1,000 of 1,814 items are used, and the 8 dev questions are excluded. Rule 1 is the comparison that is like-for-like.
4. **Position bias.** Flip rate above 20% is flagged high; otherwise reported only.
5. **Length bias.** The judge is called length-biased relative to humans only if the lower bound of (rho judge minus rho human) is above 0.

Subgroups (turn 1, turn 2, categories with and without a reference need, items that include `claude-v1` and items that do not) are descriptive; no correction for multiple looks is applied and no claim rests on them.

**Secondary (pointwise).** The first 300 items of the test file (the seeded sample order) are also scored pointwise (1-10 rubric `overall quality`, one call per response, 600 calls); the verdict is the higher score, equal scores a tie. It is reported with the same metrics, and is not tuned.

## Budget and reporting

At most 4,000 live API calls in total. Ledger before the test run: 2 probes (1 accepted, 1 rejected for `temperature`), 8 smoke calls (discarded), 120 dev calls = 130. Planned test run: 2,000 pairwise + 600 pointwise + about 60 CLI demo calls. Every number carries "claude-sonnet-5-5 via Anthropic API, date, no logprobs". The report states the model id the API returned for every call, calls, tokens, and the date range.

## Dev result (not a test result; 60 items, 8 questions, noisy)

Judge-human agreement S1 61.7%, S2 84.3%; released GPT-4 on the same items 70.4% / 90.3%; position-flip rate 8.3%; no unparsable replies. The prompt was not changed after seeing these numbers.

## Limitations stated in advance

* **Self-preference** is not controlled: the judge is a Claude model and the responses include Claude-v1 (the dataset's six models are GPT-4, GPT-3.5, Claude-v1, Vicuna-13B, Alpaca-13B, LLaMA-13B). The `claude-v1` subgroup shows whether agreement differs on those pairs; it cannot separate self-preference from quality.
* Humans are experts and the dataset authors (judge ids `expert_*` and `author_*`); their agreement is itself imperfect.
* One prompt, one judge model, one run per item.
