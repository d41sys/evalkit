# ezc eval, 2026-11-17, `ungrounded` cases run again for the judge pool (issue #5)

- Set: the 90 kept `-ungrounded-` cases of heldout-v1..v3 (unchanged; ids as in [`../heldout-v1.jsonl`](../heldout-v1.jsonl), [`../heldout-v2.jsonl`](../heldout-v2.jsonl), [`../heldout-v3.jsonl`](../heldout-v3.jsonl)).
- Agent: ezcross-ems `harness/` at `ddc56cfd`, `--temperature default`; 0 network errors. Cost: Sonnet $1.08, Haiku $0.75.
- Code checks: Sonnet 63/90, Haiku 48/90. Not a capability result; the sessions only feed [`../judge-v1/pool-2.jsonl`](../judge-v1/README.md).
- Fresh evidence check: answer similarity to the same case and model in heldout-v1..v3 (difflib ratio) has median 0.27; 2 answers are ≥ 0.9 and 5 are ≥ 0.8, none identical.
