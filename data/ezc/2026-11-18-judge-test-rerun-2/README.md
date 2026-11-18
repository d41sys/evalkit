# ezc eval, 2026-11-18, `ungrounded` test cases run again for pools 4 and 5 (issue #5)

This directory feeds [`../judge-v1/pool-4.jsonl`](../judge-v1/README.md). [`../2026-11-18-judge-test-rerun-3/`](../2026-11-18-judge-test-rerun-3/) is a second, simultaneous run of the same set and feeds `pool-5.jsonl`.

- **Set:** the 38 `-ungrounded-` cases in the judge's `test` split, unchanged.
- **Agent:** ezcross-ems `harness/` at `ddc56cfd`, `--temperature default`; 0 network errors in either run.
- **Runs:**

  | run | pool | Sonnet passed | Haiku passed | cost |
  |---|---|---|---|---|
  | this one | 4 | 32/38 | 23/38 | $0.54 |
  | `-3` | 5 | 30/38 | 20/38 | $0.73 |

  The pass counts are not a capability result.
- **Timing:** both runs started after the judge was frozen in `1b2a127`.
- **Fresh-evidence check:** each answer's highest similarity to the same case and model in pools 1–3 has median 0.37. 6 answers reach ≥ 0.8; none is identical.
