### Judge validation on MT-Bench human judgments, split `test`

claude-sonnet-5-5 via Anthropic API, models returned ['claude-sonnet-5-5'], calls recorded 2026-10-28T23:24:48+00:00 to 2026-10-28T23:43:40+00:00, no logprobs. Prompt fingerprint `999579cc574d3989`. Items where a reply had no parsable verdict: 11 of 1000 (resolved to tie).
Cache: 2421 calls, 3138192 input and 708814 output tokens.

#### All items

1000 items, 72 questions, 1816 human votes; S2 judge-human items 754, human-human items S1 507 / S2 360.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 67.8% [64.9, 70.7] |
| judge-human agreement S2 (no ties) | 86.0% [83.8, 88.2] |
| Cohen's kappa S1 (3 labels) | +0.499 [+0.453, +0.547] |
| Cohen's kappa S2 (A/B only) | +0.729 [+0.680, +0.778] |
| human-human agreement S1 | 66.8% [62.8, 70.8] |
| human-human agreement S2 | 84.2% [80.4, 87.8] |
| judge minus human-human S1, matched items | +1.9 pp [-1.5, +5.1] |
| judge minus human-human S2, matched items | +2.6 pp [-0.6, +5.7] |
| released GPT-4 (pair) vs human S1, same items | 65.2% [61.9, 68.5] |
| released GPT-4 (pair) vs human S2, same items | 85.4% [83.1, 87.9] |
| judge minus GPT-4 S1 | +2.5 pp [-0.2, +5.3] |
| judge minus GPT-4 S2 | +0.6 pp [-1.5, +2.8] |
| position-flip rate (orders disagree) | 7.2% [5.5, 8.8] |
| same-slot rate (same position wins in both orders) | 2.9% [1.7, 4.3] |
| resolved-tie rate, judge | 14.5% [11.1, 17.9] |
| tie rate, humans (per vote) | 23.3% [19.6, 27.2] |
| Spearman rho, judge verdict vs length diff | +0.370 [+0.272, +0.463] |
| Spearman rho, mean human vote vs length diff | +0.379 [+0.289, +0.464] |
| rho judge minus rho human | -0.010 [-0.055, +0.034] |
| longer response wins, judge (decided pairs) | 69.0% [64.3, 73.7] |
| longer response wins, humans (per vote) | 69.4% [65.2, 73.7] |

#### Turn 1

505 items, 72 questions, 921 human votes; S2 judge-human items 374, human-human items S1 259 / S2 178.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 68.1% [63.6, 72.1] |
| judge-human agreement S2 (no ties) | 84.2% [80.5, 87.7] |
| Cohen's kappa S1 (3 labels) | +0.494 [+0.417, +0.561] |
| Cohen's kappa S2 (A/B only) | +0.699 [+0.620, +0.772] |
| human-human agreement S1 | 67.8% [62.2, 72.6] |
| human-human agreement S2 | 83.9% [78.1, 89.5] |
| judge minus human-human S1, matched items | +0.0 pp [-4.9, +4.4] |
| judge minus human-human S2, matched items | +2.0 pp [-2.6, +6.1] |
| released GPT-4 (pair) vs human S1, same items | 65.0% [60.6, 69.2] |
| released GPT-4 (pair) vs human S2, same items | 85.1% [81.6, 88.5] |
| judge minus GPT-4 S1 | +3.0 pp [-0.8, +6.9] |
| judge minus GPT-4 S2 | -0.9 pp [-4.1, +1.9] |
| position-flip rate (orders disagree) | 6.6% [4.6, 8.7] |
| same-slot rate (same position wins in both orders) | 2.2% [0.8, 3.8] |
| resolved-tie rate, judge | 16.4% [12.1, 21.1] |
| tie rate, humans (per vote) | 25.0% [20.8, 29.8] |
| Spearman rho, judge verdict vs length diff | +0.300 [+0.177, +0.417] |
| Spearman rho, mean human vote vs length diff | +0.319 [+0.199, +0.439] |
| rho judge minus rho human | -0.019 [-0.087, +0.044] |
| longer response wins, judge (decided pairs) | 66.7% [60.8, 72.5] |
| longer response wins, humans (per vote) | 66.7% [60.9, 72.5] |

#### Turn 2

495 items, 72 questions, 895 human votes; S2 judge-human items 380, human-human items S1 248 / S2 182.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 67.4% [63.5, 71.6] |
| judge-human agreement S2 (no ties) | 87.8% [84.7, 90.9] |
| Cohen's kappa S1 (3 labels) | +0.504 [+0.446, +0.561] |
| Cohen's kappa S2 (A/B only) | +0.758 [+0.695, +0.817] |
| human-human agreement S1 | 65.8% [60.7, 70.9] |
| human-human agreement S2 | 84.4% [79.7, 89.1] |
| judge minus human-human S1, matched items | +3.9 pp [-0.8, +8.5] |
| judge minus human-human S2, matched items | +3.1 pp [-1.3, +7.1] |
| released GPT-4 (pair) vs human S1, same items | 65.4% [61.1, 69.6] |
| released GPT-4 (pair) vs human S2, same items | 85.7% [82.0, 89.3] |
| judge minus GPT-4 S1 | +2.1 pp [-1.7, +5.9] |
| judge minus GPT-4 S2 | +2.1 pp [-1.1, +5.6] |
| position-flip rate (orders disagree) | 7.8% [5.4, 10.7] |
| same-slot rate (same position wins in both orders) | 3.7% [2.0, 5.7] |
| resolved-tie rate, judge | 12.5% [8.9, 16.5] |
| tie rate, humans (per vote) | 21.6% [17.6, 25.6] |
| Spearman rho, judge verdict vs length diff | +0.433 [+0.311, +0.538] |
| Spearman rho, mean human vote vs length diff | +0.432 [+0.322, +0.533] |
| rho judge minus rho human | +0.001 [-0.059, +0.059] |
| longer response wins, judge (decided pairs) | 71.3% [64.9, 77.2] |
| longer response wins, humans (per vote) | 72.0% [66.6, 77.1] |

#### Categories without reference need (writing, roleplay, extraction, STEM, humanities)

633 items, 45 questions, 1153 human votes; S2 judge-human items 514, human-human items S1 312 / S2 251.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 69.3% [65.6, 72.9] |
| judge-human agreement S2 (no ties) | 84.9% [81.9, 87.7] |
| Cohen's kappa S1 (3 labels) | +0.486 [+0.425, +0.544] |
| Cohen's kappa S2 (A/B only) | +0.691 [+0.627, +0.750] |
| human-human agreement S1 | 64.8% [60.3, 69.3] |
| human-human agreement S2 | 80.3% [75.5, 85.1] |
| judge minus human-human S1, matched items | +4.7 pp [+0.8, +8.1] |
| judge minus human-human S2, matched items | +3.8 pp [-0.3, +7.6] |
| released GPT-4 (pair) vs human S1, same items | 66.9% [63.3, 70.4] |
| released GPT-4 (pair) vs human S2, same items | 83.9% [80.9, 86.8] |
| judge minus GPT-4 S1 | +2.4 pp [-0.8, +5.7] |
| judge minus GPT-4 S2 | +1.0 pp [-1.5, +3.6] |
| position-flip rate (orders disagree) | 6.7% [4.8, 8.8] |
| same-slot rate (same position wins in both orders) | 4.0% [2.2, 6.0] |
| resolved-tie rate, judge | 10.6% [7.1, 14.3] |
| tie rate, humans (per vote) | 16.7% [14.2, 19.5] |
| Spearman rho, judge verdict vs length diff | +0.327 [+0.205, +0.443] |
| Spearman rho, mean human vote vs length diff | +0.334 [+0.221, +0.439] |
| rho judge minus rho human | -0.007 [-0.066, +0.052] |
| longer response wins, judge (decided pairs) | 66.2% [60.4, 71.6] |
| longer response wins, humans (per vote) | 66.3% [60.9, 71.3] |

#### Categories where Zheng et al. gave GPT-4 a reference (reasoning, math, coding)

367 items, 27 questions, 663 human votes; S2 judge-human items 240, human-human items S1 195 / S2 109.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 65.1% [60.1, 69.8] |
| judge-human agreement S2 (no ties) | 88.4% [84.9, 91.8] |
| Cohen's kappa S1 (3 labels) | +0.509 [+0.436, +0.582] |
| Cohen's kappa S2 (A/B only) | +0.816 [+0.748, +0.875] |
| human-human agreement S1 | 70.0% [62.3, 77.5] |
| human-human agreement S2 | 93.0% [88.8, 96.6] |
| judge minus human-human S1, matched items | -2.4 pp [-8.5, +3.5] |
| judge minus human-human S2, matched items | -0.2 pp [-5.3, +4.2] |
| released GPT-4 (pair) vs human S1, same items | 62.3% [56.0, 68.9] |
| released GPT-4 (pair) vs human S2, same items | 89.5% [86.1, 92.6] |
| judge minus GPT-4 S1 | +2.8 pp [-2.5, +7.7] |
| judge minus GPT-4 S2 | -1.1 pp [-4.3, +2.4] |
| position-flip rate (orders disagree) | 8.0% [5.4, 10.6] |
| same-slot rate (same position wins in both orders) | 1.1% [0.0, 2.5] |
| resolved-tie rate, judge | 21.3% [15.6, 27.4] |
| tie rate, humans (per vote) | 34.7% [28.1, 42.0] |
| Spearman rho, judge verdict vs length diff | +0.451 [+0.312, +0.571] |
| Spearman rho, mean human vote vs length diff | +0.470 [+0.337, +0.590] |
| rho judge minus rho human | -0.019 [-0.085, +0.041] |
| longer response wins, judge (decided pairs) | 74.6% [67.0, 81.1] |
| longer response wins, humans (per vote) | 76.1% [69.4, 82.8] |

#### Items that include claude-v1 (self-preference check, descriptive)

319 items, 71 questions, 523 human votes; S2 judge-human items 232, human-human items S1 134 / S2 94.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 67.4% [62.4, 72.5] |
| judge-human agreement S2 (no ties) | 85.2% [80.7, 89.6] |
| Cohen's kappa S1 (3 labels) | +0.489 [+0.412, +0.562] |
| Cohen's kappa S2 (A/B only) | +0.689 [+0.594, +0.774] |
| human-human agreement S1 | 66.0% [59.5, 72.5] |
| human-human agreement S2 | 80.7% [73.5, 86.9] |
| judge minus human-human S1, matched items | +2.0 pp [-3.8, +7.2] |
| judge minus human-human S2, matched items | +3.8 pp [-3.3, +9.8] |
| released GPT-4 (pair) vs human S1, same items | 64.1% [59.0, 69.1] |
| released GPT-4 (pair) vs human S2, same items | 83.3% [78.4, 88.1] |
| judge minus GPT-4 S1 | +3.3 pp [-1.6, +8.3] |
| judge minus GPT-4 S2 | +1.9 pp [-2.5, +6.2] |
| position-flip rate (orders disagree) | 9.8% [6.9, 13.1] |
| same-slot rate (same position wins in both orders) | 2.9% [1.0, 5.0] |
| resolved-tie rate, judge | 16.0% [11.5, 21.0] |
| tie rate, humans (per vote) | 22.6% [18.2, 27.2] |
| Spearman rho, judge verdict vs length diff | +0.393 [+0.262, +0.523] |
| Spearman rho, mean human vote vs length diff | +0.395 [+0.265, +0.514] |
| rho judge minus rho human | -0.002 [-0.084, +0.084] |
| longer response wins, judge (decided pairs) | 69.5% [62.2, 77.1] |
| longer response wins, humans (per vote) | 67.9% [60.6, 74.7] |

#### Items without claude-v1

681 items, 72 questions, 1293 human votes; S2 judge-human items 522, human-human items S1 373 / S2 266.

| Metric | Estimate [95% CI] |
|---|---|
| judge-human agreement S1 (ties count) | 67.9% [64.6, 71.3] |
| judge-human agreement S2 (no ties) | 86.4% [83.5, 89.1] |
| Cohen's kappa S1 (3 labels) | +0.503 [+0.451, +0.555] |
| Cohen's kappa S2 (A/B only) | +0.745 [+0.688, +0.800] |
| human-human agreement S1 | 67.1% [62.6, 71.5] |
| human-human agreement S2 | 85.4% [81.2, 89.2] |
| judge minus human-human S1, matched items | +1.9 pp [-1.6, +5.3] |
| judge minus human-human S2, matched items | +2.1 pp [-1.6, +5.7] |
| released GPT-4 (pair) vs human S1, same items | 65.7% [62.0, 69.5] |
| released GPT-4 (pair) vs human S2, same items | 86.4% [83.6, 89.2] |
| judge minus GPT-4 S1 | +2.2 pp [-0.9, +5.3] |
| judge minus GPT-4 S2 | -0.0 pp [-2.4, +2.3] |
| position-flip rate (orders disagree) | 5.9% [4.2, 7.7] |
| same-slot rate (same position wins in both orders) | 3.0% [1.7, 4.4] |
| resolved-tie rate, judge | 13.8% [10.3, 17.4] |
| tie rate, humans (per vote) | 23.6% [19.5, 27.7] |
| Spearman rho, judge verdict vs length diff | +0.356 [+0.259, +0.447] |
| Spearman rho, mean human vote vs length diff | +0.375 [+0.275, +0.472] |
| rho judge minus rho human | -0.019 [-0.070, +0.030] |
| longer response wins, judge (decided pairs) | 68.8% [64.2, 73.2] |
| longer response wins, humans (per vote) | 70.0% [65.1, 74.9] |

