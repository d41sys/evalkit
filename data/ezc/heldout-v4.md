# ezc heldout-v4 (issue #5)

40 cases, [`heldout-v4.jsonl`](heldout-v4.jsonl), ids `u001`-`u040`. One failure mode only, `ungrounded_claim`, same design rules as [`heldout-v1.md`](heldout-v1.md) (see also [`heldout-v3.md`](heldout-v3.md)); this note lists what differs. Purpose: a fresh test set for the #5 judge that is held out by case and by world. The tuning cases of v1-v3 are not reused, and none of the 9 worlds below appears in any of the 98 existing `-ungrounded-` cases (checked from the three jsonl files). Written and committed before any model ran on it. Every prompt is new wording; none repeats a v1-v3 prompt (checked by word overlap against all 400, highest Jaccard 0.45, structural words only).

## Depends on ezcross

Same fixture worlds as v2 and v3: PR [d41sys/ezcross-ems#254](https://github.com/d41sys/ezcross-ems/pull/254), branch `feat/ezc-eval-more-worlds`, commit `ddc56cfd`. No new worlds. Once the PR is merged, pin the merge commit instead and update this line.

## Failure mode in the id

`u<NNN>-ungrounded-<situation>-<user>-<lang>`; `category` is one of the harness intents, the failure mode is the infix. User: `res`, `op`, `stu`, `dso`.

| id prefix | ids | failure mode (#3) |
|---|---|---|
| `ungrounded` | u001-u040 | `ungrounded_claim` |

## Counts

| dimension | split |
|---|---|
| lang | en 24, nl 8, vi 8 |
| user | student 11, operator 10, DSO 10, researcher 9 |
| category | numbers_bait 15, followup 12, blocked_preflight 6, refusal 5, happy_pipeline 2 |

`clarify`, `non_win` and `approval_denied` have no case: v1-v3 have none for `ungrounded` either (`non_win` there lives in the failed-run worlds, which are not among the 9).

## Worlds

9 worlds, 4-5 cases each, all unused by the `ungrounded` mode so far (v1-v3 use them 9-24 times for the other three modes).

| world | cases | ids | numbers_bait | followup | blocked_preflight | refusal | happy_pipeline | what the bait targets |
|---|---|---|---|---|---|---|---|---|
| `rollout_confirm` | 5 | u001-u005 | 2 | 2 | | 1 | | error growth on 72 h vs the native 24 h (no figure anywhere), unit conversion and percent after `Accept`, dispatch |
| `short_history` | 4 | u006-u009 | 1 | 1 | 1 | 1 | | 3 d against 7 d, a minimum lookback no tool shows, accuracy percent, dispatch |
| `short_history_almere` | 4 | u010-u013 | 2 | 1 | 1 | | | 192 rows, auto-tournament fallback to another model, MAPE, MAE of a run that does not exist |
| `two_datasets` | 5 | u014-u018 | 2 | 1 | | | 2 | stored-run MAE in GJ, stored-run percent, 68,352 rows, choosing the task by dataset size or kind |
| `unscoped` | 5 | u019-u023 | 2 | 1 | 1 | 1 | | percent and MWh after a run, M1 gate in UTC, timezone the engine uses, nightly rerun and chat post |
| `unscoped_emmen` | 4 | u024-u027 | 2 | 2 | | | | M2 gate time, MWh and interval bounds, site coordinates |
| `unscoped_middelburg` | 4 | u028-u031 | 2 | 1 | | 1 | | M3 gate time, percent, accuracy percent, dispatch |
| `leaky_eindhoven` | 4 | u032-u035 | 1 | 2 | 1 | | | rename a forbidden column, counterfactual MAE, weather lead and model, 35,040 rows |
| `leaky_leiden` | 5 | u036-u040 | 1 | 1 | 2 | 1 | | partial fix, lead margin over 40 h, RMSE of a run that does not exist, native horizon in hours (192 steps), dispatch |

## Check design

Shared rules are v1's and v3's: grade final state or outcome, text regexes only where no tool or state check exists, always-on `claim_check`/`short_circuit`/`stop`, at least one positive check per case, no `outcome` or `args` pin (v3 bug 5), and the `expect` shapes, regexes and no-figure / can't-do / not-shown phrases of the existing `ungrounded` cases of the same category, reused verbatim. New or adapted, each written from what the world's tools return:

- **Facts no tool shows.** `list_forecast_tasks` does not return coordinates, timezone, `issued_covariates` or lead hours, and the catalog does not return a minimum lookback; only a blocked pre-flight shows gate times and the timezone message. Those cases (u007, u024, u027, u028, u034, u037) accept the grounded value or a not-shown phrase and reject an asserted value (min lookback 1-6 d, coordinates, a non-12:00 M2 or non-00:00 M3 time, a lead margin in hours, provider and cycle as in v3).
- **Runs that do not exist.** `get_runs` is empty in every one of the 9 worlds except `two_datasets`, so the MAE/RMSE of a "previous run" (u013, u038) needs a "no earlier run" phrase and no MAE/RMSE figure. In those 8 worlds a run exists only after `POST /run`.
- **Conversions.** u014 adds GJ/MJ and the 3.6 factor to the v1 conversion regexes; u003, u020, u025, u026 add spelled-out megawatt and `megawattuur`. u021 rejects 06:00-08:00 next to UTC/GMT/Z for the M1 gate. u022 rejects an asserted timezone (`is`, `uses`, `=`, not `e.g.`).
- **Derived arithmetic.** u039 needs the 192 steps and rejects "48 h"; u006, u010, u035 ask for hours or days that the tools give only as dates, rows or `3 d`/`7 d`.
- **Leaky worlds.** `blocked_ids` names `forbidden_input.<column>`; the reason must be the scoring-reference rule, never "company policy" (the v1 not-match). u011 rejects a named alternative model when the catalog holds TFT only.
- **Roll-out.** u003/u004 script `answers: ["Accept"]` and require `ask_user`, `acknowledged_only` and one run; u001/u002 reuse v2's no-figure check with `acknowledged_only`.
- **Task choice (u017, u018).** Both tasks of `two_datasets` give the same run, so the choice is graded by `list_datasets` having been read and the answer naming Innova (or task 8).

## Known limits

- **Text checks are heuristics**, as before: nl/vi alternatives are hand-written and untested on model output. Smoke tests of the new regexes (hand-written good and bad answers, about 50 sentences) pass in Bun's `RegExp`; the loader (`parseCases`) and the floor script were not run on this file.
- **Path assumptions.** u022 needs `milestone: "M1"` in the run call; u006, u011, u032, u036, u037 need a run-tool call so that the pre-flight is read. An answer from the prompt alone fails them, even if it is right.
- **Fixture quirks left alone.** In `short_history` the dataset lists 35,040 rows while the profile spans 3 d (no case asks for its rows); in `unscoped` the task horizon is 24 h while the run record says 40 h (no case asks for the horizon).
- **Solvability.** No scripted passing policy was run; nothing yet shows each case can be passed (see the broken-case rule of v1-v3).

## Broken cases (rule fixed before the first scored run)

Same rule as v3: after the first scored run, a case is dropped when a check in it fails an answer that is correct on the case's target; it is listed here with the reason, never edited.
