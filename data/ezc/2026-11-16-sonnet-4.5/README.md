# ezc eval runs, 2026-11-16, `anthropic/claude-sonnet-4-5` (the production model, issue #2)

- Agent: ezcross-ems `harness/` on branch `feat/ezc-eval-temperature-floor` (d41sys/ezcross-ems#240, `981b0b4a`), forecast-v1 fixture worlds, no live backend.
- `t0/`: `--temperature 0`. `td-0..4/`: `--temperature default` (no temperature sent, as ezc-server does in production), 5 trials. The Anthropic API has no seed, so the trials are real samples (transcripts differ).
- `forecast-v1-results.jsonl`: bridged rows (`sample` = trial, `cost_usd` summed from the transcript's per-call usage, `latency_s` = case wall time). Total cost of the 120 runs: $0.89.
- Each `<case>.jsonl` is the session transcript; `results.json` is the ezc report for the run.
- All 3 failures are D5 claim-check flags: `numbers-mwh` (T0) is a true positive (a conversion factor, "dividing by 1000", which the system prompt forbids); `blocked-late-weather` (trial 4) is an invented lead time in a suggestion ("like a 48h lead time forecast"); `clarify-no-dataset` (T0) is an illustrative "e.g., 24 hours", the one clear false positive.
