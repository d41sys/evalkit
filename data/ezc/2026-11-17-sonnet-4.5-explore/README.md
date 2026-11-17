# ezc eval, 2026-11-17, `anthropic/claude-sonnet-4-5` on forecast-explore-v1 (issue #3)

- Agent: ezcross-ems `harness/` on branch `feat/ezc-eval-temperature-floor` (d41sys/ezcross-ems#240), fixture worlds, no live backend; the production model at `--temperature default` (no temperature sent, as ezc-server does).
- Set: [`../forecast-explore-v1.jsonl`](../forecast-explore-v1.jsonl), 100 synthetic queries (committed in `9efd62f` before this run). Every `expect` is `{}`, so the pass column only reflects the always-on invariants (claim check, tool errors): 98/100. Read the transcripts, not the pass column.
- `explore/<case>.jsonl`: session transcript; `explore/<case>.md`: the same rendered by `scripts/ezc_transcript.jq`; `explore/results.json`: the ezc report. Cost $1.30.
- `explore-sheet.csv`: the `evalkit review --all` sheet for #3, annotated (guide: [`docs/ezc-error-analysis.md`](../../../docs/ezc-error-analysis.md)).

## Annotation (2026-11-17)

- **Who.** The repo owner (forecasting domain expert) reviewed 15 rows, one per distinct situation (category x world), in question forms that showed the query, the tool results and the agent's answer. The other 85 were reviewed by 4 Claude subagents that got the owner's 15 verdicts, verbatim, as the rubric; their notes start with `[agent]`. Claude grading Claude may be lenient (self-preference); the owner chose this to save time.
- **Aligned.** 2 agent notes contradicted the owner's verdict on the same behaviour (x056 like x09: restart a run on request; x069 like x14: "accuracy %" answered with the MAE improvement) and were set to `ok`; the agent's note is kept in the cell. 5 more were set to `ok` because they flagged a plain-text yes/no or open question, which the owner judged OK (x06, x09, x16): x039, x055, x061, x084, x091. The other notes that differ from the owner's verdict on the same situation stay, because the agent's behaviour differed (for example x046, x066, x067 leave out the model fallback that x05 reported). 4 agent notes were checked against the full transcripts and describe them correctly: x028, x076, x082 (still non-ok) and x039 (relabelled `ok` above). x076 stays `ungrounded_claim`: its "about 6 MW" converts the value, which the system prompt forbids, while x12 (owner: ok) only guessed kW.
- **Labels** (axial coding by the coordinating agent, first failure per row; `presentation` also on agent `ok` rows whose results are text only, because the owner marked text-only results as a problem):

| failure_mode | count | meaning |
|---|---|---|
| `ok` | 33 | nothing went wrong |
| `presentation` | 27 | results as text only (owner: "should render the chart / visualization"; markdown "like the Tern app") |
| `question_not_panel` | 17 | a pick between enumerable options (which task, dataset, location, fix), or the input needed past a block for a pushing user, asked in plain text instead of the `ask_user` panel; a plain yes/no question is fine |
| `unasked_change` | 9 | config/state changed, or a task created with assumed values after a cancelled question, without the user's consent (owner on x04: "follow the ponytail idea", the smallest change asked for) |
| `ungrounded_claim` | 8 | a fact, unit, conversion, rule or fix not in the tool results |
| `omitted_fact` | 6 | left out something the tools returned (model fallback, leaky covariates, the forecast itself) |

`uv run evalkit failure-modes explore-sheet.csv` prints the same counts with Wilson 95% intervals. The queries are synthetic, so these are the failure modes that exist, not how often real users hit them.
