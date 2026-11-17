# ezc answer judge, v1 (issue #5)

A judge for the two text failure modes from #3 that the code checks only approximate: `ungrounded_claim` (the answer states a number, unit, fact or rule no tool result supports) and `omitted_fact` (the answer leaves out a tool-result fact the user needs). `question_not_panel` and `unasked_change` are tool-state checks and stay in code.

Fixed before any label, in this commit:

- [`pool.jsonl`](pool.jsonl), built by [`scripts/ezc_judge_pool.py`](../../../scripts/ezc_judge_pool.py) (seed 5): every kept heldout-v1..v3 session, both models, whose case targets one of the two modes. 376 items: 180 `ungrounded`, 196 `omitted`. Each item holds the user prompt, every tool result, and all assistant text of the turn (not only the final message; see heldout-v3 w063).
- Split per case, so a case's Sonnet and Haiku sessions share a split; cases stratified by whether a session fails the code check, then 15% `train`, 42.5% `dev`, 42.5% `test`.

| mode | split | code fail | code pass |
|---|---|---|---|
| ungrounded | train / dev / test | 11 / 25 / 23 | 17 / 51 / 53 |
| omitted | train / dev / test | 7 / 20 / 18 | 25 / 62 / 64 |

Protocol:

1. The owner labels every item, pass or fail on its mode only, without seeing the code verdict or the model. Agent labels do not count. Labels go to `labels.jsonl` (`id`, `label`: 1 pass / 0 fail, `note`).
2. The judge prompt is written and tuned on `train` (few-shot examples) and `dev` only.
3. Once frozen, the judge runs on `test` once; TPR and TNR with Wilson intervals come from `evalkit judge-correct`, and judged rows go through `evalkit compare`.

Known limit: the code checks fail only 45 `omitted` and 59 `ungrounded` sessions, so dev and test may hold fewer than the 30 human-labelled fails each that #5 asks for. If the owner's labels confirm that, more failing sessions get added as a second pool with its own case-level split; this pool and split stay as they are.
