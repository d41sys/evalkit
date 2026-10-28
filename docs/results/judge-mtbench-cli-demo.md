# `evalkit judge` on the MT-Bench test split, then `compare --all-pairs`

claude-sonnet-5-5 via Anthropic API, 2026-10-29, no logprobs. Replayed from the recorded cache (0 live calls), so it costs nothing and needs no key:

```bash
uv run evalkit judge --pairs data/mtbench/test.jsonl --cache data/mtbench/cache-test.jsonl --cache-only --task mt-bench --out runs/judge-mtbench
uv run evalkit compare runs/judge-mtbench/results.jsonl --all-pairs
```

`--task mt-bench` puts both turns of a question in one task, so the (task, question) cluster holds every judged item of that question. Without it the two turns would be two clusters.


### Judge `anthropic:claude-sonnet-5-5`, pairwise, 1000 items

| Model | Items | Mean judge score | Elo |
|---|---|---|---|
| gpt-4 | 332 | 0.858 | 1265.0 |
| claude-v1 | 319 | 0.701 | 1201.9 |
| gpt-3.5-turbo | 379 | 0.653 | 1121.5 |
| vicuna-13b-v1.2 | 315 | 0.397 | 900.2 |
| alpaca-13b | 326 | 0.233 | 792.5 |
| llama-13b | 329 | 0.131 | 718.9 |

Position-flip rate 7.2% over 989 items with both replies parsed; inconsistent verdicts were resolved to tie. 11 items had an unparsable reply (counted as tie).

Length diagnostic: Spearman rho of verdict with length difference 0.37; longer response wins 0.69 of decided pairs. Longer answers can be better; compare with a human baseline before calling it bias.

Elo: processed in file order, K = 32, from the resolved verdicts. API calls this run: 0 live, 2000 cache hits; tokens in/out 0/0. Self-preference is not controlled: do not rank answers from the judge's own model family without a human check. No logprobs.

Next: `evalkit compare runs/judge-mtbench/results.jsonl --all-pairs` (clustered SE where rows carry a cluster_id).


### All pairs (15 comparisons, pooled over tasks, A - B)

| A vs B | n | clusters | naive SE | clustered SE (ratio) | ICC | DEFF | A - B | 95% CI (cluster bootstrap) | W / L / T | sign p | cluster randomisation p | Holm p | MDE (80%) | n for 80% power | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpaca-13b vs gpt-3.5-turbo | 81 | 52 | 0.0692 | 0.0671 (0.97x) | 0.16 | 1.11 | -0.753 | [-0.875, -0.609] | 8 / 69 / 4 | 3.14e-13 | 0.0001 | 0.0015 | 0.205 | 6 | resolved |
| alpaca-13b vs gpt-4 | 64 | 43 | 0.0405 | 0.0389 (0.96x) | 0.00 | 1.00 | -0.922 | [-0.984, -0.839] | 1 / 60 / 3 | 5.38e-17 | 0.0001 | 0.0015 | 0.113 | 2 | resolved |
| alpaca-13b vs llama-13b | 55 | 40 | 0.1050 | 0.1110 (1.06x) | 0.18 | 1.10 | +0.364 | [+0.140, +0.571] | 30 / 10 / 15 | 0.00222 | 0.0056 | 0.0112 | 0.308 | 40 | resolved |
| alpaca-13b vs vicuna-13b-v1.2 | 64 | 48 | 0.0940 | 0.0981 (1.04x) | 0.00 | 1.00 | -0.422 | [-0.609, -0.230] | 10 / 37 / 17 | 9.85e-05 | 0.0004 | 0.0016 | 0.264 | 25 | resolved |
| alpaca-13b vs claude-v1 | 62 | 43 | 0.0678 | 0.0730 (1.08x) | 0.72 | 1.44 | -0.758 | [-0.889, -0.600] | 3 / 50 / 9 | 5.52e-12 | 0.0001 | 0.0015 | 0.228 | 6 | resolved |
| gpt-3.5-turbo vs gpt-4 | 76 | 55 | 0.0826 | 0.0884 (1.07x) | 0.04 | 1.02 | -0.539 | [-0.703, -0.364] | 10 / 51 / 15 | 9.62e-08 | 0.0001 | 0.0015 | 0.234 | 15 | resolved |
| gpt-3.5-turbo vs llama-13b | 74 | 50 | 0.0484 | 0.0459 (0.95x) | 0.00 | 1.00 | +0.865 | [+0.768, +0.946] | 66 / 2 / 6 | 1.59e-17 | 0.0001 | 0.0015 | 0.136 | 2 | resolved |
| gpt-3.5-turbo vs vicuna-13b-v1.2 | 84 | 58 | 0.0744 | 0.0797 (1.07x) | 0.22 | 1.13 | +0.571 | [+0.411, +0.723] | 57 / 9 / 18 | 1.18e-09 | 0.0001 | 0.0015 | 0.222 | 13 | resolved |
| gpt-3.5-turbo vs claude-v1 | 64 | 46 | 0.1091 | 0.1205 (1.10x) | 0.46 | 1.26 | -0.250 | [-0.484, -0.016] | 18 / 34 / 12 | 0.0365 | 0.0636 | 0.0636 | 0.343 | 121 | unresolved (needs n≈121) |
| gpt-4 vs llama-13b | 63 | 44 | 0.0310 | 0.0300 (0.97x) | 0.00 | 1.00 | +0.937 | [+0.873, +0.985] | 59 / 0 / 4 | 3.47e-18 | 0.0001 | 0.0015 | 0.087 | 2 | resolved |
| gpt-4 vs vicuna-13b-v1.2 | 58 | 40 | 0.0574 | 0.0660 (1.15x) | 0.71 | 1.44 | +0.862 | [+0.721, +0.968] | 52 / 2 / 4 | 1.65e-13 | 0.0001 | 0.0015 | 0.193 | 3 | resolved |
| gpt-4 vs claude-v1 | 71 | 48 | 0.0974 | 0.1043 (1.07x) | 0.13 | 1.08 | +0.408 | [+0.205, +0.611] | 44 / 15 / 12 | 0.000204 | 0.0007 | 0.0021 | 0.284 | 35 | resolved |
| llama-13b vs vicuna-13b-v1.2 | 62 | 44 | 0.0901 | 0.1011 (1.12x) | 0.45 | 1.26 | -0.613 | [-0.797, -0.406] | 8 / 46 / 8 | 1.38e-07 | 0.0001 | 0.0015 | 0.284 | 14 | resolved |
| llama-13b vs claude-v1 | 75 | 49 | 0.0515 | 0.0577 (1.12x) | 0.13 | 1.09 | -0.827 | [-0.932, -0.707] | 2 / 64 / 9 | 6e-17 | 0.0001 | 0.0015 | 0.151 | 3 | resolved |
| vicuna-13b-v1.2 vs claude-v1 | 47 | 35 | 0.0866 | 0.1069 (1.23x) | 0.65 | 1.33 | -0.681 | [-0.867, -0.462] | 3 / 35 / 9 | 6.68e-08 | 0.0001 | 0.0015 | 0.280 | 8 | resolved |

randomisation p: two-sided cluster sign-flip test (whole clusters change sign together; exact for <= 20 nonzero cluster sums, else 10,000 seeded Monte Carlo draws). Holm p: Holm-Bonferroni over these 15 pairs; resolved = Holm p < 0.05. MDE and n use alpha = 0.05, power 0.8, normal approximation with the observed SD of the differences; n is for the observed |A - B|; MDE `unattainable` means that even every discordant pair favouring one model would not be detected at this n. CI method: cluster-bootstrap. The sign test is shown for reference only.

Clustered: items sharing a `cluster_id` are one resampling unit. Naive SE = s / sqrt(n); clustered SE = Miller (2024, arXiv 2411.00640, sec. 3.2); ratio = clustered / naive (here 0.95x to 1.23x). ICC: one-way ANOVA estimate on the paired differences, clipped at 0. DEFF = 1 + (m - 1) ICC with m = sum of squared cluster sizes / n; MDE and n for power are inflated by it (n is a count of items). Items without a cluster id are their own cluster.

Skewness warning (n < 25 * skewness^2, Cochran's rule): the randomisation test assumes the differences are symmetric around 0 under H0 and is anti-conservative on skewed differences, so read its p-value as approximate for: alpaca-13b vs gpt-3.5-turbo (n = 81, skewness +2.28); alpaca-13b vs gpt-4 (n = 64, skewness +4.44); alpaca-13b vs claude-v1 (n = 62, skewness +2.12); gpt-3.5-turbo vs llama-13b (n = 74, skewness -3.19); gpt-4 vs llama-13b (n = 63, skewness -3.58); gpt-4 vs vicuna-13b-v1.2 (n = 58, skewness -3.25); llama-13b vs claude-v1 (n = 75, skewness +2.59); vicuna-13b-v1.2 vs claude-v1 (n = 47, skewness +1.67).

