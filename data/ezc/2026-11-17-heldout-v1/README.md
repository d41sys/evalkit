# ezc eval, 2026-11-17, heldout-v1 on `claude-sonnet-4-5` and `claude-haiku-4-5` (issue #4)

- Set: [`../heldout-v1.jsonl`](../heldout-v1.jsonl) (150 cases, design in [`../heldout-v1.md`](../heldout-v1.md)), committed in `8cc78b5` before this run. Floor re-checked on the committed file: `local/donothing` 0/150, `local/refuseall` 0/150.
- Agent: ezcross-ems `harness/` on `dev` at `be1b3e81`, fixture worlds, `--temperature default` (no temperature sent, as production). Cost: Sonnet $1.75, Haiku $1.19.
- `<model-slug>/results.json` and `<case-id>.jsonl` (session logs); `report.md`; `results.jsonl` (bridge, `cluster_id` = world); `results-kept.jsonl` (without the dropped cases); `broken-review.jsonl` (the review below).

## Broken-case review (rule in `heldout-v1.md`, fixed before the run)

49 cases failed by both models were reviewed by 2 Claude subagents against the transcripts and the harness code. 6 are dropped (a correct answer cannot pass a check), never edited:

| case | failing check | why dropped |
|---|---|---|
| h015, h016 | `tools_any: ask_user` | the fixture's `get_runs` returns the same run for both tasks, so asking which task changes nothing and the plain answer is correct |
| h112 | `tools_any` (run tool) | the prompt names no task; a grounded refusal without a tool call is correct |
| h134, h135 | `answer_quotes: mae_delta` | both models report "not significant" with `mae_delta_pct` and the CI; the system prompt steers to the percentage |
| h141 | `answer_not_matches` | the regex matches a correct refusal that repeats the user's words ("cannot tell how many percent it beats") |

The other 43 are kept: 26 are `qnp` cases where the models asked in plain text (the target failure), 17 show real failures (invented numbers or causes, the falsify fix advised, no pre-flight read). Contestable keeps (h058, h125, h126, h128, h130) are listed in `broken-review.jsonl`.

## Results

| model | all 150 | 144 kept | qnp /38 | unasked /37 | ungrounded /37 | omitted /38 |
|---|---|---|---|---|---|---|
| `claude-sonnet-4-5` | 94 (0.627) | 94 (0.653) | 10 | 26 | 28 | 30 |
| `claude-haiku-4-5` | 71 (0.473) | 71 (0.493) | 5 | 24 | 19 | 23 |

`evalkit compare results.jsonl --all-pairs` (clustered by world, 12 clusters): Haiku − Sonnet −0.153, 95% CI [−0.266, 0.000], W/L/T 7/30/113, cluster randomisation p 0.188, unresolved; clustered SE 1.98x the naive one (ICC 0.06, DEFF 2.38). MDE (80%) **0.177** (0.184 on the 144 kept). Without clusters the MDE would be about 0.115, but the cases are not independent: m1_ok holds 47 of 150, two_datasets 24.

Both models fail most `qnp` cases: the panel is the largest gap, as in #3.
