# ezc answer judge, v1 (issue #5)

A judge for the two text failure modes from #3 that the code checks only approximate: `ungrounded_claim` (the answer states a number, unit, fact or rule no tool result supports) and `omitted_fact` (the answer leaves out a tool-result fact the user needs). `question_not_panel` and `unasked_change` are tool-state checks and stay in code.

**Status: the judge works for `ungrounded`, but #5's done-when is not met.** The labels are agent labels, not expert labels. Dev and test hold fewer than 30 human-fail items each, and `omitted` has 2 fails in 196 sessions.

## Pool and split (fixed before any label, `37c7df8`)

- [`pool.jsonl`](pool.jsonl), built by [`scripts/ezc_judge_pool.py`](../../../scripts/ezc_judge_pool.py) (seed 5): every kept heldout-v1..v3 session, both models, whose case targets one of the two modes. 376 items: 180 `ungrounded`, 196 `omitted`. Each item holds the user prompt, every tool result, and all assistant text of the turn (not only the final message; see heldout-v3 w063).
- The split is per case, so a case's Sonnet and Haiku sessions share a split. Cases are stratified by whether a session fails the code check, then 15% `train`, 42.5% `dev`, 42.5% `test`.

## Labels

- [`labels.jsonl`](labels.jsonl): `id`, `label` (1 pass / 0 fail), `note`. Written by Claude subagents that saw neither the model nor the code verdict, on the owner's instruction. They are not expert labels.
  - `omitted`: 4 agents split the 196 items.
  - `ungrounded`: one agent relabelled all 180 items. The first 4-agent pass disagreed on statements the assistant makes about itself ("I can't send email"). The final rule leaves these out because the assistant's system prompt is not in the item, and fails derived numbers, units read off column names, and unseen parameters. First pass vs final: 142 of 180 agree. The rule was fixed after the first dev run, so dev was seen; test was not.
- [`owner-labels.jsonl`](owner-labels.jsonl): 130 items the owner labelled in forms before handing labelling to agents. All 130 are "pass". On the 66 `ungrounded` ones they agree with the agent labels on 36: the 36 agent-pass items. The owner passed all 30 items the agents failed. They are kept, not used.

| mode | train fail / pass | dev fail / pass | test fail / pass |
|---|---|---|---|
| ungrounded | 19 / 9 | 21 / 55 | 24 / 52 |
| omitted | 0 / 32 | 0 / 82 | 2 / 80 |

## Judge

[`scripts/ezc_judge.py`](../../../scripts/ezc_judge.py) uses evalkit's pointwise `Judge` with one rubric per mode, scores 0 or 1, and runs on `claude-sonnet-5-5` (neither compared model, so no self-grading).
- Item: the user prompt plus that session's tool results as the request; all assistant text as the response.
- Tuning: the rubric took 3 runs on `dev`. The first run had a 0–1 scale that produced fractions. The second missed derived numbers and units read off column names, with TNR 62%. The frozen rubric runs once on `test`.
- Outputs:
  - [`dev-ungrounded/`](dev-ungrounded/): last dev run;
  - [`test-ungrounded/`](test-ungrounded/), [`test-omitted/`](test-omitted/): `results.jsonl` (score = verdict) and `judgments.jsonl` (the judge's reasoning).
- Cost: about 0.5M input and 0.12M output tokens over the 5 runs.

`evalkit judge-correct`, positive = pass:

| mode, split | answers from | labelled fail / pass | TPR (pass kept) | TNR (fail caught) |
|---|---|---|---|---|
| ungrounded, dev (tuned) | both | 21 / 55 | 80.0% [67.6, 88.4] | 100% [84.5, 100] |
| **ungrounded, test** | both | 24 / 52 | **73.1% [59.7, 83.2]** | **100% [86.2, 100]** |
| ungrounded, test | Sonnet 4.5 | 10 / 28 | 71.4% [52.9, 84.7] | 100% [72.2, 100] |
| ungrounded, test | Haiku 4.5 | 14 / 24 | 75.0% [55.1, 88.0] | 100% [78.5, 100] |
| omitted, test | both | 2 / 80 | 98.8% [93.3, 99.8] | 1 of 2 |

Reading:
- **`ungrounded`:** the judge catches every agent-labelled fail. It also fails about a quarter of the good answers, so its raw pass rate (50%) is too low; the Rogan–Gladen correction gives 68.4% [49.3, 87.5].
  - Error rates are similar for the two models; the intervals overlap. The pooled correction assumes they are equal.
  - The labeller and the judge are both Claude, so agreement can be inflated.
- **`omitted`:** almost never happens here, so a judge cannot be validated for it and is not needed for these sessions.

## Still open for #5

- Expert labels on at least the `ungrounded` dev and test items (152). Agreement with `labels.jsonl` would measure the agent labels.
- At least 30 fails in each of dev and test. That needs about 50 more failing `ungrounded` sessions, from new runs, added as a second pool with its own case-level split.
