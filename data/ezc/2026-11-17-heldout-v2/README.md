# ezc eval, 2026-11-17, heldout-v2 on `claude-sonnet-4-5` and `claude-haiku-4-5` (issue #4)

- Set: [`../heldout-v2.jsonl`](../heldout-v2.jsonl) (150 cases in 24 new worlds, design and pre-registered analysis in [`../heldout-v2.md`](../heldout-v2.md)), committed in `2dc4982` before this run.
- Agent: ezcross-ems `harness/` on `feat/ezc-eval-more-worlds` at `ddc56cfd` ([d41sys/ezcross-ems#254](https://github.com/d41sys/ezcross-ems/pull/254)), `--temperature default`. Cost: Sonnet $2.05, Haiku $1.36.
- A first attempt lost the network mid-run (`getaddrinfo ENOTFOUND api.anthropic.com`: all 150 Haiku and 123 Sonnet sessions ended in an error); it was discarded whole and both models were rerun into a fresh directory. This run: 0 sessions with `stopReason: error`.
- Files as in [`../2026-11-17-heldout-v1/`](../2026-11-17-heldout-v1/README.md): per-model `results.json` and session logs, `report.md`, `results.jsonl` (`cluster_id` = world), `results-kept.jsonl`, `broken-review.jsonl`.

## Broken-case review

50 cases failed by both models were reviewed by 2 Claude subagents against the transcripts and the harness. 6 dropped, never edited:

| case | failing check | why dropped |
|---|---|---|
| v045, v046 | `outcome: forecast_pipeline` | both models used `run_forecast` + `get_runs`, reported the real error and changed nothing; the pin rejects that valid path |
| v076, v077 | `tools_any: model_catalog` | the catalog holds no accuracy fact; the empty dataset/task lists are enough |
| v089 | provider regexes | "details don't show which weather provider" misses the not-visible regex; Haiku's hit is a hedged example |
| v119 | fail/success regexes | the vi answer "đã bị timeout ... không có run nào thành công" has no listed fail word and trips the success regex |

All 29 `qnp` both-fails are kept (plain-text question or an unasked edit at a block). Cases where the `forecast_pipeline` pin also fires but one model failed a legitimate check (v080, v096, v099, v117) stay.

## Results

| model | v2, 150 | v2, 144 kept | v1 + v2 kept, 288 |
|---|---|---|---|
| `claude-sonnet-4-5` | 98 | 98 | 192 (0.667) |
| `claude-haiku-4-5` | 63 | 63 | 134 (0.465) |

Haiku − Sonnet, `evalkit compare --all-pairs`, pre-registered analysis:

| data | clusters | A − B [95% CI] | cluster randomisation p | ICC | DEFF | MDE (80%) |
|---|---|---|---|---|---|---|
| v1 + v2 kept, by world (decides #4) | 36 | −0.201 [−0.276, −0.116] | 0.0001 | 0.10 | 2.41 | **0.136** |
| v1 + v2 kept, by family (situation) | 12 | −0.201 [−0.281, −0.107] | 0.005 | 0.07 | 3.16 | 0.155 |
| v2 kept, by world | 24 | −0.243 [−0.340, −0.147] | 0.0002 | 0.15 | 1.75 | 0.165 |

The difference is resolved under every clustering. The done-when (MDE <= 0.13) is **not met**: 0.136 by world, 0.155 by family. ICC by world rose from 0.06 (v1) to 0.10, so the 24 new worlds bought less than the plan assumed; by family the variants add little, as expected, because they repeat the 12 situations. Family clustering pools both sets in one task (`task` set to one value), so v1 `m1_ok` and v2 `m1_ok_*` share a cluster.
