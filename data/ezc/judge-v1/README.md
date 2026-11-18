# ezc answer judge, v1 (issue #5)

A judge for `ungrounded_claim`, the text failure mode from #3 that the code checks only approximate: the answer states a number, unit, fact or rule that no tool result supports.
- **Not judged:** `question_not_panel` and `unasked_change` are tool-state checks and stay in code. `omitted_fact` occurs 2 times in 196 sessions, too rarely to validate a judge or to need one.
- **Deviation from #5:** the labels are Claude-subagent labels, on the owner's instruction, not labels from a domain expert. The labellers and the judge are both Claude, so their agreement can be inflated.

**Current result (frozen judge, `1b2a127`, one run on pools 4–5):** the test set is 152 new sessions (45 fail / 107 pass). The judge passes 93.5% [86.9, 98.3] of the good answers and catches all 45 ungrounded ones (Wilson [92.1, 100]). Intervals come from a bootstrap over cases. The judge agrees with the two labellers about as often as they agree with each other: 94.1% and 89.5% against 92.8%. All 7 errors are borderline answers that the labellers passed and the judge failed. See [Round 3](#round-3-one-rule-for-labellers-and-judge).

## Pools and split

- [`pool.jsonl`](pool.jsonl) (frozen in `37c7df8` before any label), built by [`scripts/ezc_judge_pool.py`](../../../scripts/ezc_judge_pool.py) (seed 5): every kept heldout-v1..v3 session, both models, whose case targets `ungrounded` (180) or `omitted` (196). Each item holds the user prompt, every tool result, and all assistant text of the turn (not only the final message; see heldout-v3 w063).
- Split per case, so a case's Sonnet and Haiku sessions share a split. Cases are stratified by whether a session fails the code check, then 15% `train`, 42.5% `dev`, 42.5% `test`.
- [`pool-2.jsonl`](pool-2.jsonl): the 90 `ungrounded` cases run once more ([`../2026-11-17-judge-rerun/`](../2026-11-17-judge-rerun/README.md)), 180 new sessions, each case keeping its pool-1 split.
  - The new answers are not copies: their median similarity to the same case and model in pool 1 is 0.27.
  - 5 are ≥ 0.8 similar. Removing the one in test (k022) moves test TPR from 88.2% to 88.0% and leaves TNR at 96.0%.
- [`pool-3.jsonl`](pool-3.jsonl): the 38 test cases run a third time ([`../2026-11-18-judge-test-rerun/`](../2026-11-18-judge-test-rerun/README.md)), 76 new sessions, committed with the frozen judge in `fd57bb8` before they were labelled. The highest similarity to the same case and model in pools 1–2 has median 0.33; 2 answers are ≥ 0.8.
- [`pool-4.jsonl`](pool-4.jsonl), [`pool-5.jsonl`](pool-5.jsonl): the 38 test cases run twice more, 152 sessions ([`../2026-11-18-judge-test-rerun-2/`](../2026-11-18-judge-test-rerun-2/README.md)), run and committed after the rule-v2 judge was frozen in `1b2a127`.

## Labels

- [`labels.jsonl`](labels.jsonl), [`labels-2.jsonl`](labels-2.jsonl): `id`, `label` (1 pass / 0 fail), `note`. Agents never saw the model or the code verdict.
- **The `ungrounded` rule:**
  - fail: numbers, units, ids, data/config facts and system-behaviour claims that no tool result or user word supports. This includes derived numbers (96 steps × 15 min = 24 h), units read off column names, and unseen named fields.
  - out of scope: statements about what the assistant or the system can do, because its system prompt is not in the item.
- **How the labels were made:**
  - The first 4-agent pass on pool 1 disagreed on capability statements, so one agent relabelled all 180 under the rule (142 of 180 agree with the first pass).
  - Pool 2 was labelled by a fresh agent given the same rule text, not the judge's rubric.
  - The rule was fixed after the first dev run, so dev was seen.
- [`owner-labels.jsonl`](owner-labels.jsonl): 130 items the owner labelled in forms before handing labelling to agents. All 130 are "pass". On the 66 `ungrounded` ones, the owner passed all 30 that the agents failed. These labels are kept but not used.
- **Round 3 labels (current gold):** [`labels-v2.jsonl`](labels-v2.jsonl) relabels pools 1–3 under [`rule-v2.md`](rule-v2.md); [`labels-4.jsonl`](labels-4.jsonl) and [`labels-5.jsonl`](labels-5.jsonl) label the test pools. Each item has `labels_ab` (two independent labellers) and `adjudicated` (a third agent decided a split). See [Round 3](#round-3-one-rule-for-labellers-and-judge).

| `ungrounded` | train fail / pass | dev fail / pass | test fail / pass |
|---|---|---|---|
| pool 1 | 19 / 9 | 21 / 55 | 24 / 52 |
| pool 2 | 15 / 13 | 18 / 58 | 25 / 51 |
| both | 34 / 22 | **39 / 113** | **49 / 103** |

## Judge

[`scripts/ezc_judge.py`](../../../scripts/ezc_judge.py): evalkit's pointwise `Judge` scores each item 0 or 1 with one rubric. It runs on `claude-sonnet-5-5`, neither compared model. Since Round 3 the rubric is [`rule-v2.md`](rule-v2.md) verbatim; the r4 numbers below are history.
- Item: the user prompt plus that session's own tool results as the request; all assistant text as the response.
- **Rubric history:** 4 rubric versions, each changed only after reading pool-1 dev errors:
  - r1 used a 0–1 scale and got fractions;
  - r2 missed derived numbers and units read off column names (TNR 62%);
  - r3 failed answers for what the system can or can't do, for asking the user for a task id, and for general advice;
  - r4 is the frozen version.
- r3 ran once on pool-1 test (TPR 73.1%, TNR 100%; [`test-ungrounded/`](test-ungrounded/)). Only those aggregate numbers were read before r4.
- Cost: about 1.0M input and 0.23M output tokens across all judge runs, plus $1.83 for the rerun sessions.

r4, `evalkit judge-correct`, positive = pass ([`r4-dev/`](r4-dev/), [`r4-test/`](r4-test/)):

| split, sessions | labelled fail / pass | TPR (pass kept) | TNR (fail caught) |
|---|---|---|---|
| dev, both pools (tuned on pool 1) | 39 / 113 | 92.0% [85.6, 95.8] | 94.9% [83.1, 98.6] |
| **test, pool 2 (new sessions, never read)** | 25 / 51 | **88.2% [76.6, 94.5]** | **96.0% [80.5, 99.3]** |
| test, both pools (pool-1 test was read once at r3, as aggregates) | 49 / 103 | 89.3% [81.9, 93.9] | 95.9% [86.3, 98.9] |
| test, both pools, Sonnet 4.5 answers | 20 / 56 | 91.1% [80.7, 96.1] | 100% [83.9, 100] |
| test, both pools, Haiku 4.5 answers | 29 / 47 | 87.2% [74.8, 94.0] | 93.1% [78.0, 98.1] |

The intervals are Wilson intervals, which treat sessions as independent. The test split holds up to 4 sessions per case (2 pools × 2 models), so the case-clustered bootstrap (`evalkit.clustered.cluster_bootstrap_ci`, 10,000 resamples by case) is the honest interval:
- pool 2: TPR 88.2% [76.9, 97.9] over 31 cases, TNR 96.0% [86.4, 100] over 18 cases;
- both pools: TPR 89.3% [82.0, 95.3] over 34 cases, TNR 95.9% [89.1, 100] over 22 cases.

One test reply had no parsable score (k049). It counts as a fail; its label is pass, so this lowers TPR and does not inflate TNR. Per-model error rates overlap. The pooled Rogan–Gladen correction in `judge-correct` assumes they are equal.

## Through `evalkit compare`

[`r4-test/compare-rows.jsonl`](r4-test/compare-rows.jsonl) holds the judge's test verdicts as ordinary result rows:
- `task` is `ezc-ungrounded-judge` and `model` is the answering model;
- `example_id` is the case, and pool 1 / pool 2 are `sample` 0 / 1;
- `cluster_id` is the world.

`uv run evalkit compare data/ezc/judge-v1/r4-test/compare-rows.jsonl --all-pairs` gives, over 38 cases and 19 worlds:

| | value |
|---|---|
| Sonnet pass^1 | 0.671 |
| Haiku pass^1 | 0.566 |
| Haiku − Sonnet | −0.105 [−0.214, +0.030] |
| p | 0.23 |
| MDE | 0.212 |
| Verdict | unresolved |

## Round 2: research and final test

**Label-noise ceiling.** A second agent, given the same rule text, labelled the 152 dev items independently. The two labellers agree on 148 of 152 (97.4%, Cohen's κ 0.93) and split only on borderline items: hedged probability wording, "suggereert/blijkt" hedges, and a suggested parameter. A judge cannot be measured above that agreement.

**Variants on dev**, 152 items (113 pass / 39 fail), all on `claude-sonnet-5-5` unless noted:

| variant | TPR | TNR | errors vs labeller 1 / 2 / consensus (148) |
|---|---|---|---|
| r4, 1 sample | 92.0% | 94.9% | 11 / 11 / 9 |
| r4, 5 samples, majority ([Lail 2026](https://arxiv.org/abs/2604.13717): ensembling gave the largest gain on RewardBench 2) | 92.9% | 97.4% | 9 / 9 / 7 |
| r4 on `claude-opus-5-5`, 1 sample | 93.8% | 94.9% | 9 / 9 / 7 |
| claim-by-claim prompt (list each claim, quote support or NONE; the RAGAS / FActScore decomposition) | 91.2% | 82.1% | 17 / 17 / 15 |
| labellers' rule text verbatim, 5 samples | 94.7% | 84.6% | 12 / 10 / 9 |

- **Decomposition:** listing claims one by one made the judge find "support" too generously, so it caught fewer ungrounded answers.
- **Labellers' rule verbatim:** the same happened. The r4 rubric's explicit cases (derived arithmetic, units read off column names) do the work.
- **Choice:** r4 with a 5-sample majority vote: it ties Opus on errors and has the best TNR. It was frozen in `fd57bb8`, before the pool-3 labels existed. None of these variants separates from r4 with 1 sample on dev: the differences are 1–3 items.

**Final test, pool 3**, run once ([`final-p3/`](final-p3/)). Labels by a fresh agent told to read every tool result in full; the read tool truncates long lines, which earlier labellers had flagged.

| | case-bootstrap 95% CI | Wilson 95% |
|---|---|---|
| TPR, 48 / 52 (29 cases) | 92.3% [80.8, 100] | [81.8, 97.0] |
| TNR, 22 / 24 (15 cases) | 91.7% [80.0, 100] | [74.2, 97.7] |
| Sonnet 4.5 answers | TPR 92.9%, TNR 100% (10 fails) | |
| Haiku 4.5 answers | TPR 91.7%, TNR 85.7% (14 fails) | |

- **The 5-sample vote added nothing on test.** 97% of items got 5 identical votes, and the first vote alone scores TPR 94.2% and TNR 91.7%. One sample costs a fifth as much and is as good.
- **Compared with the r4 one-sample result on pool 2** (88.2% / 96.0%), the difference is inside the intervals. No variant tested here measurably beats r4.
- **All 6 test errors are rule-boundary cases:**
  - 3 hedged guesses at a failure's cause ("possible causes…", "typically happens before…") that the judge fails and the labeller passes;
  - Gouda's "approximately 52.0° N, 4.7° E" and a timezone, offered as defaults to confirm: the judge passes them as hedged world knowledge, while the rule lists coordinates;
  - a conditional "lat/long or timezone are common blockers";
  - "600 s = 10 min".

  Narrowing the error further needs a decision on those boundaries, not a better prompt.

**Recommendation:** run with `--samples 1` from now on. The vote buys nothing measurable at 5× the cost; the unanimity rate shows that without using labels.

**Limit of the pool 1–2 labels:** the agents' read tool cuts JSONL lines at about 768 bytes, and the second dev labeller said it did not re-read cut-off tool results. A labeller that missed support written past that point would label a fail where the judge (full text) passes. That pattern shows up as missed fails, and those are rare (TNR 95–97% on dev), so the effect looks small. The pool-3 labeller was told to read every tool result in full.

## Round 3: one rule for labellers and judge

**Problem.** In Round 2 every remaining error was a rule-boundary case. Labellers and the judge resolved those boundaries differently because the rule never decided them.

**Rule v2** ([`rule-v2.md`](rule-v2.md)) decides each boundary:
- hedged explanations with no number, field or system rule pass;
- defaults offered for confirmation pass;
- every unit conversion fails, time units included (as the owner did in x076);
- support anywhere in the tool results counts;
- capability statements stay out of scope.

The judge now uses the same file as its rubric.

**Labels.** Each item is a pretty-printed Markdown file, so no tool result is cut. Two agents labelled every item independently, and a third decided their splits.

| pools | items | labellers agree | Cohen's κ | adjudicated |
|---|---|---|---|---|
| 1–3 (train, dev, pool-3 test) | 436 | 97.0% | 0.93 | 13 |
| 4–5 (final test) | 152 | 92.8% | 0.82 | 11 |

**Tuning, one sample each, against the v2 gold.** Pool 3 was read at this step, so it is tuning data now.

| rubric | train (56) | dev, pools 1–2 (152) | pool 3 (76) |
|---|---|---|---|
| r4 | 2 errors | TPR 93.8%, TNR 100%, 7 errors | TPR 96.2%, TNR 95.8%, 3 errors |
| **rule v2** | 2 errors | **TPR 97.3%, TNR 100%, 3 errors** | **TPR 98.1%, TNR 100%, 1 error** |

Rule v2 was frozen in `1b2a127`. That commit came before any pool-4/5 label existed and before the judge saw pools 4–5.

**Final test, pools 4–5**, run once ([`final-p45/`](final-p45/)):

| | value | case-bootstrap 95% CI | Wilson 95% |
|---|---|---|---|
| TPR, 100 / 107 (35 cases) | 93.5% | [86.9, 98.3] | [87.1, 96.8] |
| TNR, 45 / 45 (20 cases) | 100% | (no misses to resample) | [92.1, 100] |
| Sonnet 4.5 answers (18 fail) | TPR 96.6%, TNR 100% | | |
| Haiku 4.5 answers (27 fail) | TPR 89.8%, TNR 100% | | |

- **Agreement:** the judge agrees with labeller A on 143/152 items and with labeller B on 136/152. A and B agree with each other on 141/152. On these items the judge is as consistent with the labels as a second labeller.
- **Errors:** all 7 are labelled passes that the judge failed, so the judge is stricter, not looser. Six fail a mild inference the labellers accepted, about system behaviour or a config field (`lead_hours`). Examples:
  - "terminated without saving intermediate metrics", read off `metrics: null`;
  - a "guaranteed" D-1 availability.

  One (p015) had no parsable score and counts as a fail, although its reasoning passes the answer.
- **Compared with Round 2:** TNR is 100% against 91.7%, and TPR is 93.5% against 92.3%. The test sets differ (pool 3 vs pools 4–5), so this is not a paired comparison.
- **Caveats:**
  - The labels are agent labels.
  - Labellers and judge read the same rule text, so part of their agreement comes from shared wording. The two labellers still agree with each other only at κ 0.82 on test.
  - Either/or cause guesses ("training didn't complete or couldn't log") are still undecided in the rule. The adjudicator passed n068 and flagged it.
- **Cost:** about 0.92M input and 0.14M output judge tokens, plus $1.27 for the pool-4/5 sessions.
