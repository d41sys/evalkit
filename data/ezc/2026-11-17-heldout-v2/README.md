# ezc eval, 2026-11-17, heldout-v2 on `claude-sonnet-4-5` and `claude-haiku-4-5` (issue #4)

- Set: [`../heldout-v2.jsonl`](../heldout-v2.jsonl) (150 cases in 24 new worlds, design and pre-registered analysis in [`../heldout-v2.md`](../heldout-v2.md)), committed in `2dc4982` before this run.
- Agent: ezcross-ems `harness/` on `feat/ezc-eval-more-worlds` at `ddc56cfd` ([d41sys/ezcross-ems#254](https://github.com/d41sys/ezcross-ems/pull/254)), `--temperature default`. Cost: Sonnet $2.05, Haiku $1.36.
- A first attempt lost the network mid-run (`getaddrinfo ENOTFOUND api.anthropic.com`: all 150 Haiku and 123 Sonnet sessions ended in an error); it was discarded whole and both models were rerun into a fresh directory. This run: 0 sessions with `stopReason: error`.
- Files as in [`../2026-11-17-heldout-v1/`](../2026-11-17-heldout-v1/README.md): per-model `results.json` and session logs, `report.md`, `results.jsonl` (`cluster_id` = world), `results-kept.jsonl`, `broken-review.jsonl`.

## Broken-case review

50 cases failed by both models were reviewed by 2 Claude subagents against the transcripts and the harness. Reading of the rule, applied to every both-fail case in v1 and v2: drop a case when a check in it fails an answer that is correct on the case's target (a valid wording or a valid tool path, as v1 h112). 7 dropped, never edited:

| case | failing check | why dropped |
|---|---|---|
| v045, v046 | `outcome: forecast_pipeline` | both models used `run_forecast` + `get_runs`, reported the real error and changed nothing; the pin rejects that valid path |
| v099 | `outcome: forecast_pipeline` | Haiku's answer is correct and fails only that pin (Sonnet's "greater than 50%" is a real failure) |
| v076, v077 | `tools_any: model_catalog` | the catalog holds no accuracy fact; the empty dataset/task lists are enough |
| v089 | provider regexes | "details don't show which weather provider" misses the not-visible regex; Haiku's hit is a hedged example |
| v119 | fail/success regexes | the vi answer "đã bị timeout ... không có run nào thành công" has no listed fail word and trips the success regex |

All 29 `qnp` both-fails are kept (plain-text question or an unasked edit at a block). The pin also fires in v080, v096 and v117, which stay: no answer there is otherwise correct (Haiku never ran in v080; Haiku claims "MWh for this task" in v096; in v117 Sonnet omits the timeout reason and Haiku hits a tool error). v1 has no tool pins. Limit: the rule only covers cases both models fail, so a pin that fails one model's valid path in a case the other model passes still counts.

## Results

| model | v2, 150 | v2, 143 kept | v1 + v2 kept, 287 |
|---|---|---|---|
| `claude-sonnet-4-5` | 98 | 98 | 192 (0.669) |
| `claude-haiku-4-5` | 63 | 63 | 134 (0.467) |

Haiku − Sonnet, `evalkit compare --all-pairs`, pre-registered analysis:

| data | clusters | A − B [95% CI] | cluster randomisation p | ICC | DEFF | MDE (80%) |
|---|---|---|---|---|---|---|
| v1 + v2 kept, by world (decides #4) | 36 | −0.202 [−0.278, −0.116] | 0.0001 | 0.11 | 2.54 | **0.140** |
| v1 + v2 kept, by family (situation) | 12 | −0.202 [−0.283, −0.107] | 0.005 | 0.07 | 3.23 | 0.157 |
| v2 kept, by world | 24 | −0.245 [−0.345, −0.148] | 0.0002 | 0.17 | 1.84 | 0.169 |
| sensitivity: v1 + v2 kept, pin ignored, by world | 36 | −0.157 [−0.231, −0.074] | 0.0007 | 0.05 | 1.77 | 0.108 |
| sensitivity: v1 + v2 kept, pin ignored, by family | 12 | −0.157 [−0.232, −0.066] | 0.009 | 0.05 | 2.48 | 0.128 |

**The `outcome: forecast_pipeline` pin is a check bug, not a footnote.** It is in the failed checks of 25 Haiku cases and 3 Sonnet cases; in 14 Haiku cases (Sonnet: 0) it is the only failing check, because Haiku takes the equally valid `run_forecast` + `get_runs` path (v099 among them is dropped). The sensitivity rows score those 13 kept cases as passes for Haiku (134 -> 147 of 287), slightly generous because Haiku's "MWh for this task" in v096 is a real failure no check caught: the gap shrinks from −0.202 to −0.157 and stays resolved, and the MDE falls to 0.108 by world and 0.128 by family, because the pin inflated both the discordance and the between-world correlation. The pre-registered row stays the decider; heldout-v3 pins no tool.

The difference is resolved under every clustering. The done-when (MDE <= 0.13) is **not met**: 0.140 by world, 0.157 by family. ICC by world rose from 0.06 (v1) to 0.11, so the 24 new worlds bought less than the plan assumed; by family the variants add little, as expected, because they repeat the 12 situations. Family clustering pools both sets in one task (`task` set to one value), so v1 `m1_ok` and v2 `m1_ok_*` share a cluster. The first commit of this README (`f25f0c7`) dropped 6 cases and reported 0.136; v099 was added under the uniform reading above.
