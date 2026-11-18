# ezc eval, 2026-11-18, heldout-v4 (issue #5 judge test)

[`../heldout-v4.jsonl`](../heldout-v4.md): 40 new `ungrounded` cases on 9 worlds that no earlier `ungrounded` case used. This directory feeds `../judge-v1/pool-6.jsonl`. [`../2026-11-18-heldout-v4-b/`](../2026-11-18-heldout-v4-b/) is a second, simultaneous run and feeds `pool-7.jsonl`.

- **Agent:** ezcross-ems `harness/` at `ddc56cfd`, `--temperature default`; 0 network errors.
- **Timing:** both runs started after judge rule v3 was frozen in `b5ff681`.

| run | pool | Sonnet passed | Haiku passed | cost |
|---|---|---|---|---|
| this one | 6 | 22/40 | 23/40 | $0.81 |
| `-b` | 7 | 25/40 | 21/40 | $0.67 |

The pass counts come from the code checks and are not a capability result.
