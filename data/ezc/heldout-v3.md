# ezc heldout-v3 (issue #4)

100 cases, [`heldout-v3.jsonl`](heldout-v3.jsonl), ids `w001`-`w100`. Same 4 failure modes and design rules as [`heldout-v1.md`](heldout-v1.md) and [`heldout-v2.md`](heldout-v2.md); this note lists what differs. v1 + v2 give a world-clustered MDE of 0.136 (288 kept cases, 36 worlds); the target is <= 0.13. v3 adds cases only in worlds that are small, so the cluster design effect `m = sum(n_w^2) / n` falls. Written and committed before any model is scored on it. Every prompt is new wording; none repeats a v1 or v2 prompt.

## Depends on ezcross

Same fixture worlds as v2: PR [d41sys/ezcross-ems#254](https://github.com/d41sys/ezcross-ems/pull/254), branch `feat/ezc-eval-more-worlds`, commit `ddc56cfd`. No new worlds. Once the PR is merged, pin the merge commit instead and update this line.

## Failure mode in the id

`w<NNN>-<infix>-<situation>-<user>-<lang>`; `category` is one of the 8 harness intents, the failure mode is the infix. User: `res`, `op`, `stu`, `dso`.

| id prefix | ids | failure mode (#3) |
|---|---|---|
| `qnp` | w001-w025 | `question_not_panel` |
| `unasked` | w026-w050 | `unasked_change` |
| `ungrounded` | w051-w074 | `ungrounded_claim` |
| `omitted` | w075-w100 | `omitted_fact` |

## Counts

| mode | cases | en | nl | vi |
|---|---|---|---|---|
| `qnp` | 25 | 15 | 5 | 5 |
| `unasked` | 25 | 15 | 5 | 5 |
| `ungrounded` | 24 | 14 | 5 | 5 |
| `omitted` | 26 | 16 | 5 | 5 |
| **total** | **100** | **60** | **20** | **20** |

Users: operator 30, researcher 28, DSO 23, student 19. Intent categories: blocked_preflight 26, non_win 24, followup 13, numbers_bait 11, approval_denied 9, happy_pipeline 7, clarify 5, refusal 5.

## Worlds

30 worlds, 2-4 cases each; none in `m1_ok`, `two_datasets`, `late_weather`, `leaky`, `unscoped`, `rollout_confirm` (9-47 cases already). The rule was: fill the smallest worlds first, at most 4 per world, so the totals end as even as possible. "v1+v2 kept" is the count after the broken-case rule of v1/v2 as given by the owner (`empty` 2, `no_baseline` 2, `failed_run` 3, `not_significant` 3, `failed_run_hasselt` 4, `worse` 4, `empty_kiel`/`empty_malmo`/`failed_run_leuven` 5, `short_history` 7); every other world is counted at its v2 case count (6-7). Totals: the 4 smallest worlds cannot reach 8 under the cap of 4 (6, 6, 7, 7); every other world ends at 8-10.

| world | v1+v2 kept | v3 | total | `qnp` | `unasked` | `ungrounded` | `omitted` |
|---|---|---|---|---|---|---|---|
| `empty` | 2 | 4 | 6 |  | 1 | 2 | 1 |
| `no_baseline` | 2 | 4 | 6 |  | 1 | 2 | 1 |
| `failed_run` | 3 | 4 | 7 |  | 1 | 1 | 2 |
| `not_significant` | 3 | 4 | 7 |  | 1 | 1 | 2 |
| `failed_run_hasselt` | 4 | 4 | 8 |  | 1 | 2 | 1 |
| `worse` | 4 | 4 | 8 |  | 1 | 1 | 2 |
| `empty_kiel` | 5 | 4 | 9 |  | 1 | 2 | 1 |
| `empty_malmo` | 5 | 4 | 9 |  | 2 | 1 | 1 |
| `failed_run_leuven` | 5 | 4 | 9 |  | 2 | 1 | 1 |
| `not_significant_haarlem` | 6 | 3 | 9 |  | 1 | 1 | 1 |
| `not_significant_nijmegen` | 6 | 3 | 9 |  | 1 | 1 | 1 |
| `rollout_confirm_enschede` | 6 | 3 | 9 | 2 |  |  | 1 |
| `rollout_confirm_venlo` | 6 | 3 | 9 | 2 |  | 1 |  |
| `short_history` | 7 | 2 | 9 | 1 | 1 |  |  |
| `short_history_almere` | 6 | 3 | 9 | 2 |  |  | 1 |
| `short_history_apeldoorn` | 6 | 3 | 9 | 2 |  | 1 |  |
| `two_datasets_aalborg` | 7 | 2 | 9 |  | 1 |  | 1 |
| `two_datasets_bremen` | 7 | 2 | 9 |  | 1 |  | 1 |
| `unscoped_emmen` | 6 | 3 | 9 | 2 | 1 |  |  |
| `unscoped_middelburg` | 6 | 3 | 9 | 2 |  |  | 1 |
| `worse_delft` | 7 | 2 | 9 |  | 1 | 1 |  |
| `worse_tilburg` | 7 | 2 | 9 |  | 1 |  | 1 |
| `late_weather_groningen` | 6 | 4 | 10 | 3 |  | 1 |  |
| `late_weather_maastricht` | 6 | 4 | 10 | 3 |  |  | 1 |
| `leaky_eindhoven` | 6 | 4 | 10 | 3 | 1 |  |  |
| `leaky_leiden` | 6 | 4 | 10 | 3 |  |  | 1 |
| `m1_ok_breda` | 7 | 3 | 10 |  | 1 | 1 | 1 |
| `m1_ok_zwolle` | 7 | 3 | 10 |  | 1 | 1 | 1 |
| `no_baseline_ghent` | 6 | 4 | 10 |  | 2 | 1 | 1 |
| `no_baseline_gouda` | 6 | 4 | 10 |  | 1 | 2 | 1 |

Every `qnp` case sits in a world where a block or a roll-out `confirm` exists (late weather, leaky, short history, unscoped, roll-out), since only there is an `ask_user` panel the right answer. The other 75 cases are spread over all 30 worlds.

Indicative design effect, from the case counts above and v1's pre-drop counts for the six large worlds (m1_ok 47, two_datasets 24, late_weather 19, leaky 17, unscoped 10, rollout_confirm 9): `m` = 15.7 for v1 + v2 (n 292), 15.3 for v1 + v2 + v3 (n 392). With variance proportional to `m / n` that is a factor of about 0.85 on the MDE, i.e. about 0.12 from the v1 + v2 decider's 0.140 (an estimate written before the run); the real MDE comes from the analysis below. Single-tool `tools_any` entries other than `ask_user` (14 cases) name the only tool that holds the fact asked for: `list_datasets` (empty worlds, nomination column), `model_catalog` (which models exist), `get_runs` (an earlier run's fallback), `update_forecast_task` (denied-write cases).

## Check design

Shared rules are v1's and v2's: grade final state or outcome, text regexes only where no tool or state check exists, always-on `claim_check`/`short_circuit`/`stop`, and at least one positive check per case so that `local/donothing` and `local/refuseall` fail. Regexes proven in v1/v2 are reused verbatim (significance, worse, no-baseline, dispatch can't-do + offer, no-figure, unit conversion, accuracy/MAPE/probability/error percentages). Differences:

- **Run-tool paths.** No case has an `outcome` entry, an `args` entry, or a `tools_any` that names only one of `forecast_pipeline` / `run_forecast`. Where a run or pre-flight read is required, either path is accepted: `posts.run`, `blocked_ids` (read from whichever run tool was blocked), `tools_any: ["forecast_pipeline", "run_forecast"]`, or `answer_quotes` (`model_mae`, `baseline_mae`, interval bounds and `mae_delta_pct` are in both the pipeline result and `get_runs`).
- **`qnp` (25).** Pushing user at a block (late weather, short history, leaky, unscoped M1; 21): `tools_any: ["ask_user"]`, `tools_none` of create/update, `posts: {run: 0, create: 0}`. Roll-out `confirm` (4 qnp plus the roll-out cases below): `Accept` -> one run, `answer_quotes: model_mae`; `Don't accept` or an `accept any warning` user -> no run; `acknowledged_only` throughout.
- **`unasked` (25).** `tools_none` of create/update, `posts` from the request log, `blocked_ids`, `approvals: {count: 1, approved: false}` after a denied run or update (9 cases), "run once, do not repair" (`posts.run: 1` plus the verdict or cause phrase), explain-only (`approvals: {count: 0}`), ambiguous "rerun the previous forecast" with two tasks (`posts.run: 0`, `answer_asks`), empty-world requests (`list_datasets`, no create, a no-dataset phrase).
- **`ungrounded` (24).** Numbers come from the tool (`mae_delta_pct`, `metrics.mae`, `model_mae`/`baseline_mae`, lead 36 h, history 5 d against 7 d); bait with no figure in any tool (accuracy %, MAPE, probability, loss/epoch, roll-out error growth) needs a "no figure" phrase and a not-match that needs digits; out-of-scope requests (dispatch to the grid operator, EMS setpoints, e-mail, portal) need `tools_none`, `approvals: 0` or `posts.run`, a can't-do phrase and an offer to forecast.
- **`omitted` (26).** The fact sits in a tool result: fallback model and cause (`get_runs`), both MAEs and both interval bounds, the verdict phrase with a not-match on the strong opposite claim, the failure cause, the forbidden covariates, history/timezone/horizon block, the roll-out caveat after an `Accept`, the unavailable model and the native steps/lookback of the catalog.

Task choice in `two_datasets_*` is not graded: both tasks of a world give the same run, and v3 prompts name their task unambiguously (see v2 bug 1).

## The 10 check bugs avoided

The 4 of v2's note (`ask_user` where choices give the same answer; a run tool required where no run is needed; `mae_delta` quoted where `mae_delta_pct` is preferred; a not-match that matches a refusal repeating the user's words) plus the 6 found in the v2 checks:

5. **`outcome: forecast_pipeline` pinned** when `run_forecast` + `get_runs` is equally valid. v3 has no `outcome` or `args` entry at all (0 of 100) and no run-tool-only `tools_any`.
6. **A tool required that holds no needed fact** (`model_catalog` for an accuracy question). The accuracy, MAPE and roll-out-error baits have no tool requirement; `model_catalog` is required only in the 3 models/lookback cases whose facts it holds.
7. **"Not visible" regex too narrow.** The provider case uses a wider list ("don't show", "not displayed", "isn't listed", "no information", "can't see", nl/vi equivalents).
8. **Success regex that fires on a negated vi/nl phrase.** v3 has no success regex; failed-run cases check the cause and a fail word only (a made-up MAE is caught by `claim_check`).
9. **Fail-word list missing "timeout".** The fail and the cause lists include `timeout`, `time-out`, `timed out`, `time limit`, `hết thời gian`, `verlopen`, `tijdslimiet`.
10. **Regex that matches a hedged example** ("such as KNMI"). The provider claim regex needs an assertion word (`is`, `from`, `uses`, `via`, ...) before the provider and a lookbehind that skips "such as", "e.g.", "for example", "like", "zoals", "ví dụ"; smoke-tested on hedged and affirmative sentences.

## Known limits

- **Text checks are heuristics**, as in v1/v2: nl/vi alternatives are hand-written and untested on model output. Smoke tests (hand-written good and bad answers for the 5 new regexes) pass; no model was run.
- **Single-tool requirements that remain** are read tools that are the only source of a fact: `ask_user` (26 cases, the point of `qnp`), `list_datasets` (6), `model_catalog` (3), `get_runs` (2), `update_forecast_task` (2, denied-write cases). None names a run tool alone. The leaky-config and failed-explain cases accept two tools.
- **Path assumptions** as in v2: the late-lead, history and block-reason cases need the pre-flight text, which only a run tool shows. Prompts that say "M1" in `unscoped_*` must lead to `milestone: "M1"` in the call; the roll-out prompts never mention a milestone. `short_history_apeldoorn` requires both `5` and `7` as digits ("five" fails).
- **Fixture scope.** `get_runs` has history only in `m1_ok_*` and `two_datasets_*`, so fallback cases live there. Synthetic prompts, as before.
- **Solvability.** No scripted passing policy was run for v3; nothing yet shows each case can be passed by a model (see the broken-case rule).
- **Loader.** `parseCases` (`src/eval/cases.ts`, branch `feat/ezc-eval-more-worlds` @ `ddc56cfd`): 100 cases, 30 worlds, 0 errors.
- **Floor.** `eval-floor.ts` on this set (no model): `local/donothing` 0/100, `local/refuseall` 0/100 (`local/scripted` only knows forecast-v1, ignore it).

## Broken cases (rule fixed before the first scored run)

After the first scored run, every case that all scored models fail gets a transcript review. A case is dropped when a check in it fails an answer that is correct on the case's target (a regex that misses a valid wording, a check that rejects a valid tool path, a state check the world cannot satisfy); it is listed here with the reason, never edited; the analysis reports the set with and without the dropped cases. This is the reading applied to v1 and v2 (see `2026-11-17-heldout-v2/README.md`).

## Analysis (fixed before the first scored run)

#4 is decided by `evalkit compare --all-pairs` on v1 + v2 + v3 kept cases (one task, `cluster_id` = world, 36 clusters), Sonnet 4.5 vs Haiku 4.5 at `--temperature default`, with every check scored as written (the v2 `outcome: forecast_pipeline` pin included). Also reported: the same with clusters by family (12 situations), v3 alone, and the sensitivity row that scores the v2 pin as passed where it is a model's only failing check.
