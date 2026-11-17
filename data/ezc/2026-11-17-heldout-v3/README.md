# ezc eval, 2026-11-17, heldout-v3 on `claude-sonnet-4-5` and `claude-haiku-4-5` (issue #4)

- Set: [`../heldout-v3.jsonl`](../heldout-v3.jsonl) (100 cases on the 30 smaller worlds, no run-tool pins; design and pre-registered analysis in [`../heldout-v3.md`](../heldout-v3.md)), committed in `6c4cae4` before this run.
- Agent: ezcross-ems `harness/` on `feat/ezc-eval-more-worlds` at `ddc56cfd` ([d41sys/ezcross-ems#254](https://github.com/d41sys/ezcross-ems/pull/254)), `--temperature default`; 0 sessions ended in a network error. Cost: Sonnet $1.35, Haiku $0.90.
- Files as in [`../2026-11-17-heldout-v2/`](../2026-11-17-heldout-v2/README.md).

## Broken-case review

31 cases failed by both models, reviewed by a Claude subagent with the reading used for v1 and v2 (drop when a check fails an answer that is correct on the case's target). 4 dropped, never edited:

| case | failing check | why dropped |
|---|---|---|
| w050 | `answer_asks` | Haiku asks "please confirm which IANA timezone", changes nothing; correct, but the sentence has no "?" |
| w060 | `answer_not_matches` MW/MWh | Sonnet quotes the value in the target's units and refuses to convert; the hit is a conditional repeating the user's words |
| w063 | `answer_matches` e-mail wording | Sonnet says e-mail is not available in an earlier text block of the turn; the check reads only the final message |
| w073 | `tools_any` run tool + `blocked_ids` | Haiku answers 5 days of history against a 7-day lookback from `list_datasets` and `model_catalog`; the checks demand the pre-flight path |

Kept: 21 `qnp` cases (plain text, an unasked edit or a run at a pushing-user block), 5 `claim_check` cases with numbers no tool returned, and w072 (the lead time is only in the pre-flight, which neither model read).

## Results

| model | v3, 100 | v3, 96 kept | v1 + v2 + v3 kept, 383 |
|---|---|---|---|
| `claude-sonnet-4-5` | 62 | 62 | 254 (0.663) |
| `claude-haiku-4-5` | 58 | 58 | 192 (0.501) |

Haiku − Sonnet, `evalkit compare --all-pairs`, the analysis fixed in `heldout-v3.md`:

| data | clusters | A − B [95% CI] | cluster randomisation p | ICC | DEFF | MDE (80%) |
|---|---|---|---|---|---|---|
| **v1 + v2 + v3 kept, by world (decides #4)** | 36 | −0.162 [−0.230, −0.089] | 0.0002 | 0.09 | 2.21 | **0.108** |
| v1 + v2 + v3 kept, by family (situation) | 12 | −0.162 [−0.235, −0.076] | 0.006 | 0.06 | 3.20 | 0.131 |
| v3 kept, by world | 30 | −0.042 [−0.131, +0.051] | 0.51 | 0.04 | 1.09 | 0.131 |
| sensitivity: v2 pin ignored, by world | 36 | −0.128 [−0.197, −0.055] | 0.001 | 0.08 | 2.11 | 0.099 |
| sensitivity: v2 pin ignored, by family | 12 | −0.128 [−0.203, −0.046] | 0.016 | 0.06 | 3.15 | 0.122 |

**#4's done-when is met:** the pre-registered row has MDE 0.108 <= 0.13 with 36 world clusters. By the 12 underlying situations it is 0.131, just above; with the v2 pin bug ignored, 0.122. The gap is resolved in every pooled row.

v3 alone barely separates the models (−0.042, unresolved): with no tool pins and most cases on the hard `qnp`/claim-check side, both models fail the same cases (82 of 100 agree). Part of the v1 + v2 gap came from checks Haiku fails on its tool path, not from answer quality; the pin-ignored rows bound that effect.
