# ezc eval, 2026-11-18, `ungrounded` test cases run a third time (issue #5)

- **Set:** the 38 `-ungrounded-` cases in the judge's `test` split, from heldout-v1..v3, unchanged.
- **Agent:** ezcross-ems `harness/` at `ddc56cfd`, `--temperature default`; 0 network errors.
- **Cost:** Sonnet $0.44, Haiku $0.31.
- **Code checks:** Sonnet 28/38, Haiku 18/38. This is not a capability result; the sessions only feed [`../judge-v1/pool-3.jsonl`](../judge-v1/README.md), the final test of the frozen judge.
- **Fresh-evidence check:** each answer's highest difflib similarity to the same case and model in pools 1–2 has median 0.33. 2 answers reach ≥ 0.8 (m010, m043); none is identical.
