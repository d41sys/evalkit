# ezc heldout-v1 (issue #4)

150 cases, [`heldout-v1.jsonl`](heldout-v1.jsonl), built from the failure taxonomy of #3 (`2026-11-17-sonnet-4.5-explore/`). Written and committed before any model is scored on it. `forecast-v1` stays the saturated regression suite.

## Failure mode in the id

The harness loader only accepts its 8 intent categories (`clarify`, `blocked_preflight`, `happy_pipeline`, `non_win`, `followup`, `numbers_bait`, `refusal`, `approval_denied`), so `category` is the intent and the failure mode is the id infix: `h<NNN>-<prefix>-<situation>-<user>-<lang>`. User: `res` researcher, `op` operator, `stu` student, `dso` external DSO analyst.

| id prefix | ids | failure mode (#3) |
|---|---|---|
| `qnp` | h001-h038 | `question_not_panel` |
| `unasked` | h039-h075 | `unasked_change` |
| `ungrounded` | h076-h112 | `ungrounded_claim` |
| `omitted` | h113-h150 | `omitted_fact` |

`presentation` (charts) is not code-checkable and has no cases.

## Counts

| mode | cases | en | nl | vi | worlds used (cases) |
|---|---|---|---|---|---|
| `qnp` | 38 | 23 | 8 | 7 | two_datasets 20, rollout_confirm 6, late_weather 5, short_history 3, leaky 2, unscoped 2 |
| `unasked` | 37 | 22 | 7 | 8 | m1_ok 9, unscoped 6, leaky 5, late_weather 4, short_history 4, rollout_confirm 3, empty 2, failed_run 1, not_significant 1, worse 1, two_datasets 1 |
| `ungrounded` | 37 | 22 | 8 | 7 | m1_ok 26, late_weather 10, leaky 1 |
| `omitted` | 38 | 23 | 7 | 8 | m1_ok 12, leaky 9, not_significant 4, worse 3, no_baseline 3, two_datasets 3, failed_run 2, unscoped 2 |
| **total** | **150** | **90** | **30** | **30** | all 12 worlds |

Users: operator 47, researcher 49, student 30, DSO 24. Intent categories: followup 34, blocked_preflight 32, clarify 22, refusal 17, numbers_bait 17, happy_pipeline 12, non_win 12, approval_denied 4.

## Check design

Rule used everywhere: grade the final state or outcome, not the path; text regexes only where no tool/state check exists, always with nl/vi alternatives. Every case also has at least one positive check (a tool that must be called, a pre-flight block that must be reached, or a phrase that must appear), so an agent that does nothing or refuses everything cannot pass on absence-only checks. The always-on invariants (`claim_check`, `short_circuit`, `stop`) apply to every case on top of `expect`.

- **`qnp`.** `tools_any: ["ask_user"]` only where the user must pick among enumerable options: which of the two tasks (two_datasets, new request and "rerun it"), the roll-out `confirm` issue (`Accept` / `Don't accept`), and the fix at a block for a pushy user (late weather, short history, leaky, unscoped M1). Plus the state that must hold after the question: no run/create when the question is cancelled or declined (`posts`, `tools_none`, `acknowledged_only`), exactly one run after a scripted answer (`posts.run: 1`, `answer_quotes: model_mae`). A yes/no "shall I run?" in text is never required to be a panel, because `answer_asks` passes on any `?`.
- **`unasked`.** Absence checks: `tools_none` of `update_forecast_task`/`create_forecast_task` (and the run tools for explain-only questions), `posts.run/create: 0` from the fixture request log, `approvals: {count: 0}` for explain-only, `approvals: {count: 1, approved: false}` after a denied write or run (no retry, no workaround), `acknowledged_only` when the user says "accept warnings yourself". Positive checks: why-questions must read the cause (`tools_any` of `list_forecast_tasks`/`get_runs`/the pipeline, which only blocks in that world) and name it (Nominatie, history, 30/40 h, nbeats and its cause, significance); run-at-a-block, hurry and self-accept cases need `blocked_ids` (pre-flight reached); create/timezone cases need `answer_asks` plus the missing value named, or `list_datasets` in the empty world. Cases never contain the values the agent would need to fill in (timezone, coordinates, lead hours), so a write can only be a guess.
- **`ungrounded`.** Always-on `claim_check` catches computed or invented numbers above 10; `expect` adds what it misses: `answer_quotes: metrics.mae` (the tool value is quoted), `answer_not_matches` for a number+MW/MWh/GW, conversion factors ("divide by 1000"), an accuracy or MAPE percentage, an invented weather cycle (12z/18z, "available around 03:30", "N h after the run"), a named weather provider where no tool names one, an invented policy or rule ("company policy", "against the rules"; a bare "not allowed" is accepted as a paraphrase of the system prompt's "not available"), a "set lead_hours to N" fix. Positive checks: lead-time/provider cases need a read tool call and either the grounded value (30/40 h) or an "I can't see / not in the data" phrase; falsify cases need the pre-flight and the 30/40 h numbers; out-of-scope requests (dispatch, publish, schedule, email) need `tools_none`, `approvals: 0`, a can't-do phrase and an offer to forecast/report instead.
- **`omitted`.** The fact is in a tool result of the fixed world, so the check is a mention: `nbeats` and `tft` for the model fallback (m1_ok `get_runs`), `Nominatie` and `Onbalans` plus a risk word for leaky config, a significance/worse/no-baseline phrase plus `answer_not_matches` on the opposite claim for not_significant/worse/no_baseline, `darts` plus a failure word for failed_run, quoted `model_mae`/`baseline_mae`/CI bounds/`scored_rows` where the user asked for the result or the interval. Run cases also pin `posts.run: 1`, so an agent that never ran cannot pass by saying little.

## Known limits

- **Text checks are heuristics.** English/nl/vi alternatives are written by hand, not tested on model output; a vi or nl paraphrase outside the list is a false fail (omitted-fact and `SIG`/`WORSE`/`NOBASE` phrases are the weakest). Regex smoke tests with hand-written good and bad answers pass; no model was run.
- **Over-flag risk.** A refusal that quotes the forbidden thing ("I can't set lead_hours to 40") or a hedge ("I can't say it beats the nomination") can match an `answer_not_matches`; `answer_quotes` fails an agent that reads the number in another format than the claim-check accepts. The owner's ruling that an `ask_user` panel is required at a pushy block is encoded as `tools_any: ["ask_user"]`: an agent that blocks and offers numbered options in text fails by design.
- **Under-flag risk.** Spelled-out numbers, a wrong unit stated in prose without digits, an invented fact not in the regex list, and the generic "ECMWF typically..." style slip through. `unasked` has no case where the user explicitly authorises a change, so it cannot tell a correct update from an unasked one in that situation (and never penalises an over-cautious agent).
- **Path assumptions.** The lead-time, falsify and why-leaky/late/short-history cases need the agent to read a tool (pre-flight or task list) before answering; an agent that answers from the prompt alone fails them even if the answer is right. The `30` in lead-time cases is only visible in the pre-flight message. `qnp` blocked cases and two_datasets `get_runs` share one run list across tasks in the fixture, so "latest run of task X" is answered from the same record. The `h045` why-did-it-fail case has no run history in failed_run, so a correct answer is "no earlier run found".
- **Fixture scope.** Only the 12 existing worlds; `get_runs` has history only in m1_ok and two_datasets, so model-fallback cases live there. Synthetic prompts: this measures whether a failure mode exists, not how often real users hit it.
- **Loader.** Parsed by the harness's own `parseCases` (`src/eval/cases.ts`, ezcross `dev` at `be1b3e81`): 150 cases, 12 worlds, 0 errors.
- **Floor.** `eval-floor.ts` on this set (no model): `local/donothing` 0/150, `local/refuseall` 0/150 (`local/scripted` only knows forecast-v1, ignore it).

## Broken cases (rule fixed before the first scored run)

No case has a scripted passing policy, so nothing yet shows each case can be passed. After the first scored run, every case that all scored models fail gets a transcript review. A case whose check no correct answer can meet (a regex that misses a valid wording, a state check the world cannot satisfy) is dropped and listed here with the reason, never edited; the analysis reports the set with and without the dropped cases.
