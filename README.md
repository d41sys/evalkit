# evalkit

Evaluate LLMs and agents, and tell whether a difference between two models is real.

evalkit runs tasks against models, scores them, and reports paired statistics: confidence intervals, significance with multiple-comparison correction, and how many examples you would need to see a difference. It also grades free-text answers with an LLM judge whose agreement with humans is measured. It supplies the statistics for the ezcross-ems agent evals.

Every number below has a full protocol, data and caveats in [REPORT.md](REPORT.md) or the linked folder.

## Quickstart

```bash
uv run evalkit run --tasks tasks --models oracle,noisy:0.3,random --out runs/demo
uv run evalkit leaderboard runs/demo
uv run evalkit compare runs/demo/results.jsonl --all-pairs
```

The last command answers "is model A better than model B?" for every pair, with a p-value corrected for the number of pairs and the sample size each unresolved pair would need. The LLM judge needs `uv sync --extra llm` and `ANTHROPIC_API_KEY`; local Hugging Face models need `--extra hf`.

## Commands

| Command | What it does |
|---|---|
| `run`, `leaderboard` | Run YAML tasks against models; ranked table with intervals, Elo, calibration |
| `compare` | Paired test of two models, or all pairs with Holm correction, effect size and power |
| `judge`, `judge-correct` | LLM-as-judge with position and length controls; pass rate corrected for judge error |
| `monitor`, `review`, `failure-modes`, `audit` | Weekly pass rate with alert; annotation sheet; label counts; broken-item check |
| `trajectory`, `variance`, `rank` | Agent tool-call metrics; item / prompt / trial variance; Bradley-Terry ranking |
| `stats-check`, `judge-correct-check` | Monte Carlo check that the statistics above keep their promised error rates |
| `import-helm`, `helm-study`, `metric-check`, `irt-subset` | Rerun the statistics on public HELM Lite results |

`uv run evalkit <command> --help` lists the options.

## Results

### Statistics

| Check | Result | Details |
|---|---|---|
| Do the tests keep their promised error rates? | Five rounds of Monte Carlo checks, each protocol committed before scoring; the problems found (undercoverage at small n, skewed scores, many ties) were fixed and rechecked | [REPORT.md](REPORT.md#do-the-statistics-hold-up-monte-carlo-check-evalkit-stats-check) |
| Does evalkit reproduce HELM Lite? | Exactly, from HELM's per-item data (91 models) | [REPORT.md](REPORT.md#comparison-with-sota) |
| Is HELM Lite's ranking supported? | Only 41 of 90 adjacent rank gaps are resolved; 16 of those go the other way | [docs/sota-review.md](docs/sota-review.md) |

### LLM judge for hallucination (public benchmarks)

Each rule was tuned on a training or dev split, frozen in a commit, then run once on held-out data.

| Benchmark | evalkit judge | Best published | Details |
|---|---|---|---|
| MT-Bench, agreement with experts | 86.0% (Sonnet 5.5) | humans with each other 84.2%, GPT-4 85.4% | [REPORT.md](REPORT.md#does-it-agree-with-humans-mt-bench-validation) |
| RAGTruth, F1 | 78.2 (Sonnet 5.5, rule v2) | 78.7, fine-tuned Llama-2-13B | [data/ragtruth](data/ragtruth/README.md) |
| TRIVIA+, ROC-AUC | 0.865 (Sonnet 5.5, rule v2) | 0.795 | [data/triviaplus](data/triviaplus/README.md) |
| HaluBench, mean accuracy | 93.2 (Opus 5.5, rule v4)\*; 90.1 (Haiku 5.5, rule v5) | 87.4, fine-tuned LYNX 70B | [data/halubench](data/halubench/README.md) |
| FaithBench, balanced accuracy | 77.7 (Haiku 5.5, rule s1) | 68.8 zero-shot; 84.0 FaithJudge (few-shot) | [data/faithbench](data/faithbench/README.md) |

\* Rule v4's tuning data shared passages with part of the HaluBench holdout; on the clean part it scores 97.4% on CovidQA. FaithBench is on 417 summaries from 53 articles, the published rows on 599.

### ezcross-ems agent evals

| Question | Result | Details |
|---|---|---|
| Does the eval separate agents from do-nothing baselines? | Yes: scripted agent 20/20, do-nothing 0/20, refuse-all 1/20 | [REPORT.md](REPORT.md#the-floor-a-fresh-clone-reproduces-it-without-an-api-key) |
| Production model, forecast-v1 | Sonnet 4.5 passes 99 of 100 trials; the set is saturated | [data/ezc/2026-11-16-sonnet-4.5](data/ezc/2026-11-16-sonnet-4.5/) |
| Held-out set: Haiku 4.5 vs Sonnet 4.5 | Haiku lower by 0.162 [0.089, 0.230] on 383 cases; an upper bound, part of it comes from check bugs | [REPORT.md](REPORT.md#held-out-capability-set-issue-4) |
| Judge for invented claims in answers | Passes 93.8% of good answers, catches 95.3% of bad ones (Sonnet 5.5, held-out test) | [data/ezc/judge-v1](data/ezc/judge-v1/README.md) |

## Open items

- **Issue #7, weekly grading of production sessions:** `evalkit monitor` is ready; it waits on ezcross-ems#254 being merged and four weeks of sessions.
- **ezc judge labels:** the owner relabelled six items after seeing judge output; two blind rechecks confirm three of them. See [data/ezc/judge-v1](data/ezc/judge-v1/README.md#blind-recheck-with-codex-gpt-6-luna-2026-11-27).

## Development

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs ruff, the format check, mypy and pytest on every push to `main`. A release is a tag `v<version>` matching `pyproject.toml`; the workflow attaches the wheel:

```bash
uv tool install https://github.com/d41sys/evalkit/releases/download/v0.1.0/evalkit-0.1.0-py3-none-any.whl
```

Design choices (metrics in plain NumPy, sandboxed code execution, unbiased pass@k, randomisation test over sign test) are listed at the end of [REPORT.md](REPORT.md#design-decisions).
