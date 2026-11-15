# ezc eval runs, 2026-11-15, `qwen3.6:27b-ctx64k` (pipeline check, not the production model)

- Agent: ezcross-ems `harness/` on branch `feat/ezc-eval-temperature-floor` (d41sys/ezcross-ems#240, `981b0b4a`), fixture worlds, no live backend.
- Model: Ollama `qwen3.6:27b-ctx64k` (Q4_K_M) on a shared RTX 4090 workstation, through an SSH tunnel, `local/` provider. GPUs were busy with other jobs, so `--case-timeout 900`.
- `explore/`: `data/ezc/forecast-explore-v0.jsonl`, `--temperature default`. Every `expect` is `{}`: read the transcripts, ignore the pass column.
- `t0/`: forecast-v1, `--temperature 0`. `td-0..2/`: forecast-v1, `--temperature default`, 3 trials. The Modelfile default is `temperature 0`, `seed 0`, so the 3 trials are identical (thinking, tool calls, answers, 20/20 cases): they are not samples, and their pass^3 and trial variance say nothing about sampling variance.
- `forecast-v1-results.jsonl`: bridged rows (`sample` = trial). `explore-sheet.csv`: `evalkit review` sheet for issue #3 (`note`, `failure_mode` empty).
- Each `<case>.jsonl` is the case's session transcript.
