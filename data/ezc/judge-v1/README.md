# ezc answer judge, v1 (issue #5)

A judge for `ungrounded_claim`, the text failure mode from #3 that the code checks only approximate: the answer states a number, unit, fact or rule that no tool result supports.
- **Not judged:** `question_not_panel` and `unasked_change` are tool-state checks and stay in code. `omitted_fact` occurs 2 times in 196 sessions, too rarely to validate a judge or to need one.
- **Deviation from #5:** the labels are Claude-subagent labels, on the owner's instruction, not labels from a domain expert. The labellers and the judge are both Claude, so their agreement can be inflated.

## Pools and split

- [`pool.jsonl`](pool.jsonl) (frozen in `37c7df8` before any label), built by [`scripts/ezc_judge_pool.py`](../../../scripts/ezc_judge_pool.py) (seed 5): every kept heldout-v1..v3 session, both models, whose case targets `ungrounded` (180) or `omitted` (196). Each item holds the user prompt, every tool result, and all assistant text of the turn (not only the final message; see heldout-v3 w063).
- Split per case, so a case's Sonnet and Haiku sessions share a split. Cases are stratified by whether a session fails the code check, then 15% `train`, 42.5% `dev`, 42.5% `test`.
- [`pool-2.jsonl`](pool-2.jsonl): the 90 `ungrounded` cases run once more ([`../2026-11-17-judge-rerun/`](../2026-11-17-judge-rerun/README.md)), 180 new sessions, each case keeping its pool-1 split.
  - The new answers are not copies: their median similarity to the same case and model in pool 1 is 0.27.
  - 5 are ≥ 0.8 similar. Removing the one in test (k022) moves test TPR from 88.2% to 88.0% and leaves TNR at 96.0%.

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

| `ungrounded` | train fail / pass | dev fail / pass | test fail / pass |
|---|---|---|---|
| pool 1 | 19 / 9 | 21 / 55 | 24 / 52 |
| pool 2 | 15 / 13 | 18 / 58 | 25 / 51 |
| both | 34 / 22 | **39 / 113** | **49 / 103** |

## Judge

[`scripts/ezc_judge.py`](../../../scripts/ezc_judge.py): evalkit's pointwise `Judge` scores each item 0 or 1 with one rubric. It runs on `claude-sonnet-5-5`, neither compared model.
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
| **test, both pools** | 49 / 103 | **89.3% [81.9, 93.9]** | **95.9% [86.3, 98.9]** |
| test, both pools, Sonnet 4.5 answers | 20 / 56 | 91.1% [80.7, 96.1] | 100% [83.9, 100] |
| test, both pools, Haiku 4.5 answers | 29 / 47 | 87.2% [74.8, 94.0] | 93.1% [78.0, 98.1] |

One test reply had no parsable score and counts as a fail (k049). Per-model error rates overlap; the pooled Rogan–Gladen correction in `judge-correct` assumes they are equal.

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
