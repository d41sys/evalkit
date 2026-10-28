`uv run evalkit compare runs/clustered-demo/results.jsonl --a model_a --b model_b`

### model_a (A) vs model_b (B), paired on 200 examples

| Task | n | clusters | A | B | A - B | 95% CI | naive SE | clustered SE | SE ratio | W / L / T | sign p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| passage_qa | 200 | 40 | 0.628 | 0.535 | +0.093 | [+0.008, +0.178] | 0.0282 | 0.0433 | 1.54x | 85 / 50 / 65 | 0.00328 |
| ALL | 200 | 40 | 0.628 | 0.535 | +0.093 | [+0.008, +0.178] | 0.0282 | 0.0433 | 1.54x | 85 / 50 / 65 | 0.00328 |

ALL pools examples across tasks (micro average). p-values are not corrected for the number of tasks.

95% CI: cluster bootstrap (whole clusters resampled; rows with fewer than two clusters fall back to the item bootstrap and show n/a). Naive SE = s / sqrt(n) of the per-item differences; clustered SE = Miller (2024, arXiv 2411.00640, sec. 3.2); SE ratio = clustered / naive. The sign test is item-level and ignores clusters. Items without a cluster id are their own cluster.


### Multi-sample: item averages and pass^3 (samples per item 3 to 3)

| model | items | pass^1 (mean over samples) | pass^3 | 95% CI of pass^3 |
|---|---|---|---|---|
| model_a | 200 | 0.628 | 0.345 | [0.240, 0.450] |
| model_b | 200 | 0.535 | 0.210 | [0.130, 0.295] |

Item score = mean of the item's samples. pass^3 = mean over items of C(c, 3) / C(n, 3) for c correct of n samples, an unbiased estimate of P(all samples of an item correct) (Yao et al. 2024, tau-bench, arXiv 2406.12045). CI: bootstrap over items (whole clusters).


`uv run evalkit compare runs/clustered-demo/results.jsonl --all-pairs`

### All pairs (3 comparisons, pooled over tasks, A - B)

| A vs B | n | clusters | naive SE | clustered SE (ratio) | ICC | DEFF | A - B | 95% CI (cluster bootstrap) | W / L / T | sign p | cluster randomisation p | Holm p | MDE (80%) | n for 80% power | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model_a vs model_b | 200 | 40 | 0.0282 | 0.0433 (1.54x) | 0.35 | 2.40 | +0.093 | [+0.008, +0.178] | 85 / 50 / 65 | 0.00328 | 0.0478 | 0.054 | 0.122 | 344 | unresolved (needs n≈344) |
| model_a vs model_c | 200 | 40 | 0.0307 | 0.0471 (1.54x) | 0.35 | 2.40 | +0.192 | [+0.098, +0.282] | 109 / 40 / 51 | 1.41e-08 | 0.0005 | 0.0015 | 0.133 | 97 | resolved |
| model_b vs model_c | 200 | 40 | 0.0299 | 0.0425 (1.42x) | 0.26 | 2.06 | +0.098 | [+0.013, +0.177] | 91 / 48 / 61 | 0.000333 | 0.027 | 0.054 | 0.120 | 299 | unresolved (needs n≈299) |

randomisation p: two-sided cluster sign-flip test (whole clusters change sign together; exact for <= 20 nonzero cluster sums, else 10,000 seeded Monte Carlo draws). Holm p: Holm-Bonferroni over these 3 pairs; resolved = Holm p < 0.05. MDE and n use alpha = 0.05, power 0.8, normal approximation with the observed SD of the differences; n is for the observed |A - B|; MDE `unattainable` means that even every discordant pair favouring one model would not be detected at this n. CI method: cluster-bootstrap. The sign test is shown for reference only.

Clustered: items sharing a `cluster_id` are one resampling unit. Naive SE = s / sqrt(n); clustered SE = Miller (2024, arXiv 2411.00640, sec. 3.2); ratio = clustered / naive (here 1.42x to 1.54x). ICC: one-way ANOVA estimate on the paired differences, clipped at 0. DEFF = 1 + (m - 1) ICC with m = sum of squared cluster sizes / n; MDE and n for power are inflated by it (n is a count of items). Items without a cluster id are their own cluster.


### Multi-sample: item averages and pass^3 (samples per item 3 to 3)

| model | items | pass^1 (mean over samples) | pass^3 | 95% CI of pass^3 |
|---|---|---|---|---|
| model_a | 200 | 0.628 | 0.345 | [0.240, 0.450] |
| model_b | 200 | 0.535 | 0.210 | [0.130, 0.295] |
| model_c | 200 | 0.437 | 0.115 | [0.065, 0.175] |

Item score = mean of the item's samples. pass^3 = mean over items of C(c, 3) / C(n, 3) for c correct of n samples, an unbiased estimate of P(all samples of an item correct) (Yao et al. 2024, tau-bench, arXiv 2406.12045). CI: bootstrap over items (whole clusters).

