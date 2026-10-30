### Judge panel vs MT-Bench human judgments (and self-preference), test subsample

Protocol: `docs/protocol-judge-panel.md`. Prompt `judge-v1` (fingerprint `999579cc574d3989`), no logprobs, no sampling parameter. Models returned: Haiku ['claude-haiku-5-5']; Sonnet ['claude-sonnet-5-5']; Opus ['claude-opus-5-5']. Subsample: 160 of 1,000 test items (96 with claude-v1, 64 without). Items with an unparsable reply (resolved to tie by that judge): Haiku 0, Sonnet 0, Opus 0. Panel tie band for aggregation (b): 0.2. Intervals: cluster bootstrap over questions, 2000 resamples, seed 0. Prices are ASSUMED list prices Haiku $1/$5, Sonnet $3/$15, Opus $5/$25 per million input/output tokens.

#### Pre-registered decisions (panel minus Sonnet, same subsample, margin 5 pp)

| Aggregation | S1 difference | S1 rule | S2 difference | S2 rule |
|---|---|---|---|---|
| (a) majority (primary) | +2.9 pp [+0.4, +5.9] | **superior** | +0.2 pp [-1.9, +1.9] | non-inferior (CI includes 0) |
| (b) mean (secondary) | +1.0 pp [-2.5, +5.4] | non-inferior (CI includes 0) | -0.1 pp [-1.8, +1.1] | non-inferior (CI includes 0) |

The rule is applied mechanically to the pre-registered contrast only. Every other row (subgroups, other single judges, kappas, flips, opponent splits) is descriptive; no correction for multiple looks is made. The panel is also compared with Opus alone in the paired tables below: a panel gain over Sonnet is not a gain over its best member. Sonnet's 320 calls on the subsample were recorded earlier (`data/mtbench/cache-test.jsonl`) and are not in the ledger; the cost tables price them at the same assumed prices.

### Agreement with human votes

#### All subsample items

160 items, 67 questions, 268 human votes; S2 judge-human items 129; human-human items S1 67 / S2 46.

| Metric | Haiku | Sonnet | Opus | Panel (a) majority | Panel (b) mean | GPT-4 (released) | human-human |
|---|---|---|---|---|---|---|---|
| judge-human agreement S1 | 71.6% [64.2, 78.5] | 70.6% [63.2, 77.5] | 74.8% [67.9, 81.2] | 73.5% [66.5, 80.1] | 71.7% [64.6, 78.6] | 72.2% [65.3, 78.7] | 63.4% [53.0, 72.9] |
| judge-human agreement S2 | 87.3% [80.9, 92.8] | 86.8% [80.1, 92.9] | 85.7% [79.2, 91.5] | 87.0% [80.6, 92.6] | 86.8% [80.1, 92.6] | 89.5% [83.7, 94.5] | 83.2% [72.4, 92.0] |
| Cohen's kappa S1 (3 labels) | +0.528 [+0.408, +0.626] | +0.514 [+0.393, +0.620] | +0.568 [+0.460, +0.664] | +0.557 [+0.448, +0.657] | +0.518 [+0.409, +0.617] | +0.547 [+0.451, +0.633] |  |
| Cohen's kappa S2 (A/B) | +0.730 [+0.580, +0.842] | +0.722 [+0.571, +0.841] | +0.708 [+0.558, +0.825] | +0.724 [+0.574, +0.840] | +0.722 [+0.577, +0.837] | +0.771 [+0.654, +0.869] |  |
| position-flip rate | 8.1% [3.6, 13.3] | 6.2% [2.6, 10.9] | 6.2% [2.4, 11.1] | 2.5% [0.0, 5.8] | 3.8% [0.6, 7.7] |  |  |
| same-slot rate | 4.4% [1.2, 7.9] | 3.8% [1.2, 6.7] | 2.5% [0.6, 5.2] | 0.6% [0.0, 1.9] | 1.9% [0.0, 4.1] |  |  |
| resolved-tie rate | 11.9% [6.7, 17.9] | 11.2% [5.8, 17.3] | 10.6% [5.2, 16.6] | 11.2% [6.0, 17.4] | 5.0% [1.9, 8.9] |  |  |
| rho verdict vs length diff | +0.476 [+0.318, +0.621] | +0.455 [+0.286, +0.606] | +0.462 [+0.305, +0.604] | +0.463 [+0.298, +0.612] | +0.460 [+0.297, +0.606] |  |  |

Paired differences, panel minus single judge (same items, same resamples):

| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |
|---|---|---|---|
| Haiku (Panel (a) majority) | S1 | +2.0 pp [-1.0, +5.2] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | S2 | -0.3 pp [-2.9, +2.1] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | kappa S1 | +0.030 [-0.019, +0.078] | |
| Haiku (Panel (a) majority) | kappa S2 | -0.006 [-0.047, +0.029] | |
| Haiku (Panel (a) majority) | position-flip rate | -5.6 pp [-10.8, -1.2] | |
| Sonnet (Panel (a) majority) | S1 | +2.9 pp [+0.4, +5.9] | superior |
| Sonnet (Panel (a) majority) | S2 | +0.2 pp [-1.9, +1.9] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | kappa S1 | +0.043 [+0.012, +0.082] | |
| Sonnet (Panel (a) majority) | kappa S2 | +0.002 [-0.025, +0.024] | |
| Sonnet (Panel (a) majority) | position-flip rate | -3.8 pp [-8.6, +0.6] | |
| Opus (Panel (a) majority) | S1 | -1.3 pp [-3.9, +0.8] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | S2 | +1.3 pp [-0.2, +3.3] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | kappa S1 | -0.011 [-0.063, +0.031] | |
| Opus (Panel (a) majority) | kappa S2 | +0.016 [-0.006, +0.044] | |
| Opus (Panel (a) majority) | position-flip rate | -3.8 pp [-7.9, +0.0] | |
| Haiku (Panel (b) mean) | S1 | +0.1 pp [-3.5, +4.3] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | S2 | -0.5 pp [-3.3, +2.1] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | kappa S1 | -0.010 [-0.071, +0.063] | |
| Haiku (Panel (b) mean) | kappa S2 | -0.008 [-0.051, +0.030] | |
| Haiku (Panel (b) mean) | position-flip rate | -4.4 pp [-9.9, +0.6] | |
| Sonnet (Panel (b) mean) | S1 | +1.0 pp [-2.5, +5.4] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | S2 | -0.1 pp [-1.8, +1.1] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | kappa S1 | +0.003 [-0.050, +0.070] | |
| Sonnet (Panel (b) mean) | kappa S2 | +0.001 [-0.024, +0.020] | |
| Sonnet (Panel (b) mean) | position-flip rate | -2.5 pp [-7.5, +2.1] | |
| Opus (Panel (b) mean) | S1 | -3.1 pp [-6.6, -0.2] | inferior |
| Opus (Panel (b) mean) | S2 | +1.1 pp [-1.0, +3.3] | non-inferior (CI includes 0) |
| Opus (Panel (b) mean) | kappa S1 | -0.050 [-0.108, +0.006] | |
| Opus (Panel (b) mean) | kappa S2 | +0.014 [-0.013, +0.043] | |
| Opus (Panel (b) mean) | position-flip rate | -2.5 pp [-7.0, +1.4] | |

Pairwise Cohen's kappa between judges (resolved verdicts, 3 labels, all subsample items):

| Pair | kappa [95% CI] |
|---|---|
| Haiku - Sonnet | +0.807 [+0.719, +0.887] |
| Haiku - Opus | +0.839 [+0.756, +0.912] |
| Sonnet - Opus | +0.849 [+0.763, +0.924] |

#### Items that include claude-v1

96 items, 53 questions, 162 human votes; S2 judge-human items 78; human-human items S1 41 / S2 28.

| Metric | Haiku | Sonnet | Opus | Panel (a) majority | Panel (b) mean | GPT-4 (released) | human-human |
|---|---|---|---|---|---|---|---|
| judge-human agreement S1 | 70.2% [60.2, 79.3] | 70.4% [61.9, 78.3] | 74.6% [65.0, 83.2] | 73.5% [64.4, 82.0] | 72.1% [63.3, 80.6] | 72.7% [63.9, 80.2] | 63.8% [50.9, 75.0] |
| judge-human agreement S2 | 87.6% [78.5, 95.0] | 86.8% [77.4, 94.3] | 83.7% [74.4, 92.0] | 85.9% [76.3, 93.6] | 86.5% [77.7, 93.9] | 88.7% [80.3, 95.2] | 84.5% [70.5, 95.5] |
| Cohen's kappa S1 (3 labels) | +0.511 [+0.343, +0.659] | +0.521 [+0.367, +0.650] | +0.568 [+0.415, +0.702] | +0.562 [+0.406, +0.700] | +0.539 [+0.385, +0.669] | +0.559 [+0.429, +0.665] |  |
| Cohen's kappa S2 (A/B) | +0.747 [+0.537, +0.901] | +0.733 [+0.522, +0.883] | +0.695 [+0.485, +0.848] | +0.720 [+0.510, +0.870] | +0.732 [+0.530, +0.876] | +0.760 [+0.592, +0.879] |  |
| position-flip rate | 9.4% [3.6, 16.7] | 8.3% [3.2, 14.3] | 7.3% [2.6, 13.3] | 3.1% [0.0, 7.3] | 3.1% [0.0, 7.1] |  |  |
| same-slot rate | 5.2% [0.9, 11.6] | 6.2% [2.1, 11.2] | 3.1% [0.0, 6.9] | 1.0% [0.0, 3.2] | 2.1% [0.0, 5.3] |  |  |
| resolved-tie rate | 12.5% [6.0, 20.2] | 12.5% [6.3, 19.8] | 10.4% [4.7, 17.9] | 12.5% [6.2, 20.4] | 4.2% [1.0, 8.2] |  |  |
| rho verdict vs length diff | +0.494 [+0.284, +0.676] | +0.490 [+0.295, +0.668] | +0.465 [+0.270, +0.645] | +0.490 [+0.291, +0.675] | +0.503 [+0.309, +0.679] |  |  |

Paired differences, panel minus single judge (same items, same resamples):

| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |
|---|---|---|---|
| Haiku (Panel (a) majority) | S1 | +3.3 pp [-0.6, +8.2] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | S2 | -1.7 pp [-5.7, +0.2] | inconclusive |
| Haiku (Panel (a) majority) | kappa S1 | +0.051 [-0.021, +0.133] | |
| Haiku (Panel (a) majority) | kappa S2 | -0.026 [-0.094, +0.007] | |
| Haiku (Panel (a) majority) | position-flip rate | -6.2 pp [-14.1, +0.0] | |
| Sonnet (Panel (a) majority) | S1 | +3.1 pp [-1.1, +7.9] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | S2 | -0.9 pp [-3.8, +0.6] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | kappa S1 | +0.041 [-0.009, +0.108] | |
| Sonnet (Panel (a) majority) | kappa S2 | -0.013 [-0.051, +0.008] | |
| Sonnet (Panel (a) majority) | position-flip rate | -5.2 pp [-10.8, +0.0] | |
| Opus (Panel (a) majority) | S1 | -1.0 pp [-4.8, +1.7] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | S2 | +2.1 pp [-0.4, +5.8] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | kappa S1 | -0.006 [-0.088, +0.057] | |
| Opus (Panel (a) majority) | kappa S2 | +0.025 [-0.011, +0.072] | |
| Opus (Panel (a) majority) | position-flip rate | -4.2 pp [-9.5, +0.9] | |
| Haiku (Panel (b) mean) | S1 | +1.9 pp [-3.5, +7.4] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | S2 | -1.1 pp [-4.8, +1.2] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | kappa S1 | +0.028 [-0.063, +0.126] | |
| Haiku (Panel (b) mean) | kappa S2 | -0.015 [-0.081, +0.027] | |
| Haiku (Panel (b) mean) | position-flip rate | -6.2 pp [-14.3, +0.0] | |
| Sonnet (Panel (b) mean) | S1 | +1.7 pp [-3.1, +6.8] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | S2 | -0.3 pp [-3.0, +1.5] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | kappa S1 | +0.018 [-0.048, +0.097] | |
| Sonnet (Panel (b) mean) | kappa S2 | -0.001 [-0.039, +0.029] | |
| Sonnet (Panel (b) mean) | position-flip rate | -5.2 pp [-11.7, +0.0] | |
| Opus (Panel (b) mean) | S1 | -2.4 pp [-8.2, +2.1] | inconclusive |
| Opus (Panel (b) mean) | S2 | +2.8 pp [+0.3, +6.5] | superior |
| Opus (Panel (b) mean) | kappa S1 | -0.029 [-0.122, +0.046] | |
| Opus (Panel (b) mean) | kappa S2 | +0.037 [+0.004, +0.083] | |
| Opus (Panel (b) mean) | position-flip rate | -4.2 pp [-9.6, +0.0] | |

#### Items without claude-v1

64 items, 46 questions, 106 human votes; S2 judge-human items 51; human-human items S1 26 / S2 18.

| Metric | Haiku | Sonnet | Opus | Panel (a) majority | Panel (b) mean | GPT-4 (released) | human-human |
|---|---|---|---|---|---|---|---|
| judge-human agreement S1 | 73.5% [62.7, 83.3] | 70.9% [59.0, 80.7] | 75.1% [64.3, 83.6] | 73.5% [62.5, 82.6] | 70.9% [59.0, 80.8] | 71.5% [60.6, 81.1] | 62.8% [46.4, 77.7] |
| judge-human agreement S2 | 86.9% [76.0, 95.5] | 86.9% [75.9, 95.2] | 88.8% [78.3, 96.9] | 88.8% [78.3, 96.9] | 87.1% [76.1, 95.3] | 90.9% [82.5, 97.5] | 81.1% [65.4, 96.7] |
| Cohen's kappa S1 (3 labels) | +0.551 [+0.402, +0.687] | +0.504 [+0.335, +0.652] | +0.565 [+0.415, +0.698] | +0.549 [+0.398, +0.685] | +0.485 [+0.314, +0.633] | +0.529 [+0.375, +0.662] |  |
| Cohen's kappa S2 (A/B) | +0.702 [+0.469, +0.880] | +0.702 [+0.469, +0.880] | +0.728 [+0.508, +0.904] | +0.728 [+0.508, +0.904] | +0.705 [+0.473, +0.881] | +0.788 [+0.597, +0.932] |  |
| position-flip rate | 6.2% [1.5, 12.7] | 3.1% [0.0, 8.3] | 4.7% [0.0, 10.3] | 1.6% [0.0, 4.9] | 4.7% [0.0, 10.6] |  |  |
| same-slot rate | 3.1% [0.0, 8.3] | 0.0% [0.0, 0.0] | 1.6% [0.0, 5.2] | 0.0% [0.0, 0.0] | 1.6% [0.0, 5.2] |  |  |
| resolved-tie rate | 10.9% [4.3, 18.8] | 9.4% [3.0, 17.1] | 10.9% [4.3, 19.0] | 9.4% [3.1, 16.7] | 6.2% [1.5, 13.1] |  |  |
| rho verdict vs length diff | +0.448 [+0.210, +0.659] | +0.407 [+0.164, +0.622] | +0.465 [+0.249, +0.661] | +0.431 [+0.196, +0.637] | +0.399 [+0.158, +0.608] |  |  |

Paired differences, panel minus single judge (same items, same resamples):

| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |
|---|---|---|---|
| Haiku (Panel (a) majority) | S1 | +0.0 pp [-4.8, +4.6] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | S2 | +2.0 pp [+0.0, +6.7] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | kappa S1 | -0.002 [-0.049, +0.041] | |
| Haiku (Panel (a) majority) | kappa S2 | +0.026 [+0.000, +0.093] | |
| Haiku (Panel (a) majority) | position-flip rate | -4.7 pp [-10.4, +0.0] | |
| Sonnet (Panel (a) majority) | S1 | +2.6 pp [+0.0, +6.8] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | S2 | +2.0 pp [+0.0, +6.6] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | kappa S1 | +0.045 [+0.000, +0.117] | |
| Sonnet (Panel (a) majority) | kappa S2 | +0.026 [+0.000, +0.091] | |
| Sonnet (Panel (a) majority) | position-flip rate | -1.6 pp [-7.4, +3.2] | |
| Opus (Panel (a) majority) | S1 | -1.6 pp [-5.0, +0.0] | inconclusive |
| Opus (Panel (a) majority) | S2 | +0.0 pp [+0.0, +0.0] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | kappa S1 | -0.016 [-0.054, +0.000] | |
| Opus (Panel (a) majority) | kappa S2 | +0.000 [+0.000, +0.000] | |
| Opus (Panel (a) majority) | position-flip rate | -3.1 pp [-8.2, +0.0] | |
| Haiku (Panel (b) mean) | S1 | -2.6 pp [-8.5, +3.0] | inconclusive |
| Haiku (Panel (b) mean) | S2 | +0.3 pp [-5.2, +5.6] | inconclusive |
| Haiku (Panel (b) mean) | kappa S1 | -0.066 [-0.164, +0.015] | |
| Haiku (Panel (b) mean) | kappa S2 | +0.003 [-0.074, +0.076] | |
| Haiku (Panel (b) mean) | position-flip rate | -1.6 pp [-7.4, +3.4] | |
| Sonnet (Panel (b) mean) | S1 | +0.0 pp [-4.4, +4.7] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | S2 | +0.3 pp [+0.0, +1.0] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | kappa S1 | -0.019 [-0.097, +0.041] | |
| Sonnet (Panel (b) mean) | kappa S2 | +0.003 [+0.000, +0.011] | |
| Sonnet (Panel (b) mean) | position-flip rate | +1.6 pp [-3.4, +6.8] | |
| Opus (Panel (b) mean) | S1 | -4.2 pp [-9.4, +0.0] | inconclusive |
| Opus (Panel (b) mean) | S2 | -1.7 pp [-6.2, +0.0] | inconclusive |
| Opus (Panel (b) mean) | kappa S1 | -0.080 [-0.176, +0.000] | |
| Opus (Panel (b) mean) | kappa S2 | -0.023 [-0.086, +0.000] | |
| Opus (Panel (b) mean) | position-flip rate | +0.0 pp [-6.2, +6.5] | |

#### Turn 1

80 items, 54 questions, 139 human votes; S2 judge-human items 61; human-human items S1 37 / S2 24.

| Metric | Haiku | Sonnet | Opus | Panel (a) majority | Panel (b) mean | GPT-4 (released) | human-human |
|---|---|---|---|---|---|---|---|
| judge-human agreement S1 | 70.4% [61.1, 79.1] | 67.5% [58.3, 76.2] | 73.4% [64.6, 81.2] | 72.1% [63.4, 80.1] | 68.4% [59.4, 76.6] | 70.6% [59.8, 80.7] | 61.0% [49.1, 73.2] |
| judge-human agreement S2 | 88.8% [80.0, 96.2] | 85.8% [76.3, 93.9] | 87.4% [77.9, 95.1] | 87.4% [77.9, 95.1] | 86.6% [77.3, 94.2] | 92.1% [84.7, 98.0] | 84.7% [70.4, 96.8] |
| Cohen's kappa S1 (3 labels) | +0.490 [+0.342, +0.620] | +0.443 [+0.298, +0.571] | +0.544 [+0.417, +0.659] | +0.512 [+0.373, +0.629] | +0.458 [+0.326, +0.579] | +0.521 [+0.377, +0.663] |  |
| Cohen's kappa S2 (A/B) | +0.736 [+0.512, +0.906] | +0.699 [+0.481, +0.870] | +0.724 [+0.504, +0.892] | +0.720 [+0.501, +0.888] | +0.715 [+0.501, +0.879] | +0.850 [+0.714, +0.955] |  |
| position-flip rate | 11.2% [4.1, 19.5] | 7.5% [1.4, 14.8] | 7.5% [1.4, 14.6] | 1.2% [0.0, 4.1] | 2.5% [0.0, 6.3] |  |  |
| same-slot rate | 5.0% [1.2, 10.3] | 2.5% [0.0, 6.3] | 5.0% [1.2, 10.5] | 0.0% [0.0, 0.0] | 1.2% [0.0, 3.9] |  |  |
| resolved-tie rate | 16.2% [8.1, 25.3] | 12.5% [4.9, 21.3] | 15.0% [6.7, 25.0] | 15.0% [6.3, 24.7] | 5.0% [1.2, 10.3] |  |  |
| rho verdict vs length diff | +0.513 [+0.268, +0.719] | +0.467 [+0.231, +0.681] | +0.494 [+0.259, +0.695] | +0.507 [+0.267, +0.715] | +0.492 [+0.262, +0.702] |  |  |

Paired differences, panel minus single judge (same items, same resamples):

| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |
|---|---|---|---|
| Haiku (Panel (a) majority) | S1 | +1.7 pp [-3.6, +7.3] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | S2 | -1.4 pp [-5.2, +0.4] | inconclusive |
| Haiku (Panel (a) majority) | kappa S1 | +0.021 [-0.053, +0.100] | |
| Haiku (Panel (a) majority) | kappa S2 | -0.016 [-0.067, +0.012] | |
| Haiku (Panel (a) majority) | position-flip rate | -10.0 pp [-18.6, -2.5] | |
| Sonnet (Panel (a) majority) | S1 | +4.6 pp [+0.4, +9.5] | superior |
| Sonnet (Panel (a) majority) | S2 | +1.6 pp [+0.0, +4.5] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | kappa S1 | +0.069 [+0.019, +0.133] | |
| Sonnet (Panel (a) majority) | kappa S2 | +0.021 [+0.000, +0.061] | |
| Sonnet (Panel (a) majority) | position-flip rate | -6.2 pp [-13.0, -1.2] | |
| Opus (Panel (a) majority) | S1 | -1.3 pp [-3.9, +0.0] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | S2 | +0.0 pp [-0.6, +0.6] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | kappa S1 | -0.032 [-0.099, +0.000] | |
| Opus (Panel (a) majority) | kappa S2 | -0.004 [-0.022, +0.010] | |
| Opus (Panel (a) majority) | position-flip rate | -6.2 pp [-13.2, -1.2] | |
| Haiku (Panel (b) mean) | S1 | -2.1 pp [-8.4, +3.7] | inconclusive |
| Haiku (Panel (b) mean) | S2 | -2.2 pp [-6.4, +0.5] | inconclusive |
| Haiku (Panel (b) mean) | kappa S1 | -0.032 [-0.131, +0.064] | |
| Haiku (Panel (b) mean) | kappa S2 | -0.021 [-0.082, +0.019] | |
| Haiku (Panel (b) mean) | position-flip rate | -8.8 pp [-17.3, -1.4] | |
| Sonnet (Panel (b) mean) | S1 | +0.8 pp [-5.2, +7.8] | inconclusive |
| Sonnet (Panel (b) mean) | S2 | +0.9 pp [+0.0, +2.3] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | kappa S1 | +0.016 [-0.059, +0.113] | |
| Sonnet (Panel (b) mean) | kappa S2 | +0.016 [+0.000, +0.047] | |
| Sonnet (Panel (b) mean) | position-flip rate | -5.0 pp [-12.3, +1.2] | |
| Opus (Panel (b) mean) | S1 | -5.0 pp [-10.4, -0.9] | inferior |
| Opus (Panel (b) mean) | S2 | -0.7 pp [-3.5, +0.9] | non-inferior (CI includes 0) |
| Opus (Panel (b) mean) | kappa S1 | -0.085 [-0.150, -0.029] | |
| Opus (Panel (b) mean) | kappa S2 | -0.009 [-0.046, +0.013] | |
| Opus (Panel (b) mean) | position-flip rate | -5.0 pp [-12.8, +1.4] | |

#### Turn 2

80 items, 56 questions, 129 human votes; S2 judge-human items 68; human-human items S1 30 / S2 22.

| Metric | Haiku | Sonnet | Opus | Panel (a) majority | Panel (b) mean | GPT-4 (released) | human-human |
|---|---|---|---|---|---|---|---|
| judge-human agreement S1 | 72.7% [62.4, 81.7] | 73.7% [63.9, 82.4] | 76.2% [66.4, 84.6] | 75.0% [65.2, 83.5] | 75.0% [65.1, 83.7] | 73.7% [64.4, 82.1] | 66.4% [49.7, 80.8] |
| judge-human agreement S2 | 86.0% [77.4, 93.2] | 87.8% [80.5, 94.5] | 84.2% [75.9, 91.9] | 86.7% [78.8, 93.5] | 86.9% [79.1, 93.6] | 87.2% [79.7, 93.9] | 81.5% [63.8, 95.0] |
| Cohen's kappa S1 (3 labels) | +0.563 [+0.400, +0.696] | +0.594 [+0.435, +0.717] | +0.591 [+0.430, +0.724] | +0.605 [+0.446, +0.728] | +0.587 [+0.439, +0.710] | +0.566 [+0.406, +0.700] |  |
| Cohen's kappa S2 (A/B) | +0.723 [+0.551, +0.857] | +0.740 [+0.584, +0.869] | +0.693 [+0.530, +0.831] | +0.726 [+0.565, +0.857] | +0.728 [+0.569, +0.859] | +0.703 [+0.522, +0.850] |  |
| position-flip rate | 5.0% [0.0, 11.4] | 5.0% [1.2, 10.0] | 5.0% [0.0, 11.4] | 3.8% [0.0, 9.6] | 5.0% [0.0, 11.5] |  |  |
| same-slot rate | 3.8% [0.0, 8.6] | 5.0% [1.2, 10.0] | 0.0% [0.0, 0.0] | 1.2% [0.0, 3.8] | 2.5% [0.0, 6.2] |  |  |
| resolved-tie rate | 7.5% [1.2, 14.7] | 10.0% [3.7, 17.9] | 6.2% [1.2, 13.0] | 7.5% [1.3, 14.6] | 5.0% [1.2, 10.0] |  |  |
| rho verdict vs length diff | +0.418 [+0.204, +0.606] | +0.411 [+0.203, +0.593] | +0.399 [+0.187, +0.587] | +0.393 [+0.168, +0.585] | +0.396 [+0.187, +0.582] |  |  |

Paired differences, panel minus single judge (same items, same resamples):

| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |
|---|---|---|---|
| Haiku (Panel (a) majority) | S1 | +2.3 pp [+0.0, +5.6] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | S2 | +0.7 pp [-1.8, +4.5] | non-inferior (CI includes 0) |
| Haiku (Panel (a) majority) | kappa S1 | +0.042 [+0.000, +0.092] | |
| Haiku (Panel (a) majority) | kappa S2 | +0.004 [-0.042, +0.060] | |
| Haiku (Panel (a) majority) | position-flip rate | -1.3 pp [-6.3, +2.5] | |
| Sonnet (Panel (a) majority) | S1 | +1.3 pp [+0.0, +3.9] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | S2 | -1.1 pp [-4.3, +0.5] | non-inferior (CI includes 0) |
| Sonnet (Panel (a) majority) | kappa S1 | +0.011 [-0.003, +0.039] | |
| Sonnet (Panel (a) majority) | kappa S2 | -0.014 [-0.059, +0.010] | |
| Sonnet (Panel (a) majority) | position-flip rate | -1.3 pp [-7.4, +5.1] | |
| Opus (Panel (a) majority) | S1 | -1.2 pp [-5.7, +2.2] | inconclusive |
| Opus (Panel (a) majority) | S2 | +2.5 pp [-0.3, +6.8] | non-inferior (CI includes 0) |
| Opus (Panel (a) majority) | kappa S1 | +0.014 [-0.057, +0.086] | |
| Opus (Panel (a) majority) | kappa S2 | +0.033 [-0.004, +0.089] | |
| Opus (Panel (a) majority) | position-flip rate | -1.3 pp [-5.6, +2.5] | |
| Haiku (Panel (b) mean) | S1 | +2.3 pp [-1.8, +7.1] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | S2 | +0.9 pp [-1.7, +4.8] | non-inferior (CI includes 0) |
| Haiku (Panel (b) mean) | kappa S1 | +0.024 [-0.051, +0.102] | |
| Haiku (Panel (b) mean) | kappa S2 | +0.006 [-0.039, +0.062] | |
| Haiku (Panel (b) mean) | position-flip rate | +0.0 pp [-5.3, +4.9] | |
| Sonnet (Panel (b) mean) | S1 | +1.2 pp [-2.6, +5.5] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | S2 | -0.9 pp [-4.1, +0.9] | non-inferior (CI includes 0) |
| Sonnet (Panel (b) mean) | kappa S1 | -0.007 [-0.070, +0.051] | |
| Sonnet (Panel (b) mean) | kappa S2 | -0.012 [-0.056, +0.014] | |
| Sonnet (Panel (b) mean) | position-flip rate | +0.0 pp [-6.7, +6.9] | |
| Opus (Panel (b) mean) | S1 | -1.3 pp [-5.5, +2.2] | inconclusive |
| Opus (Panel (b) mean) | S2 | +2.7 pp [+0.0, +7.0] | non-inferior (CI includes 0) |
| Opus (Panel (b) mean) | kappa S1 | -0.005 [-0.088, +0.082] | |
| Opus (Panel (b) mean) | kappa S2 | +0.035 [+0.000, +0.091] | |
| Opus (Panel (b) mean) | position-flip rate | +0.0 pp [-3.8, +3.5] | |

#### Sonnet on all 1,000 test items (existing run, for context)

agreement S1 67.8% [64.9, 70.7], S2 86.0% [83.8, 88.2]; kappa S1 +0.499 [+0.453, +0.547], S2 +0.729 [+0.680, +0.778]; released GPT-4 on the same items S1 65.2% [61.9, 68.5], S2 85.4% [83.1, 87.9].

### Self-preference (pre-registered)

#### Primary: claude-v1 items of the subsample

96 items with claude-v1, 53 questions; by opponent: vs gpt-4 12, vs gpt-3.5-turbo 17, vs llama-13b / alpaca-13b / vicuna-13b-v1.2 67.

| Judge | mean excess [95% CI] | interpretation |
|---|---|---|
| Haiku | +0.013 [-0.144, +0.168] | CI includes 0: no detectable effect |
| Sonnet | +0.034 [-0.138, +0.194] | CI includes 0: no detectable effect |
| Opus | -0.008 [-0.168, +0.145] | CI includes 0: no detectable effect |
| Panel (a) majority | -0.008 [-0.177, +0.155] | CI includes 0: no detectable effect |
| Panel (b) mean | +0.055 [-0.119, +0.218] | CI includes 0: no detectable effect |
| GPT-4 (released, control) | -0.029 [-0.168, +0.107] | CI includes 0: no detectable effect |

Claude judge excess minus GPT-4 excess (same items, paired):

| Judge | difference [95% CI] | interpretation |
|---|---|---|
| Haiku | +0.042 [-0.098, +0.198] | CI includes 0: no detectable effect |
| Sonnet | +0.062 [-0.092, +0.225] | CI includes 0: no detectable effect |
| Opus | +0.021 [-0.136, +0.183] | CI includes 0: no detectable effect |
| Panel (a) majority | +0.021 [-0.142, +0.183] | CI includes 0: no detectable effect |
| Panel (b) mean | +0.083 [-0.076, +0.256] | CI includes 0: no detectable effect |

Descriptive, by opponent (mean excess [95% CI]; n = items):

| Judge | vs gpt-4 (n=12) | vs gpt-3.5-turbo (n=17) | vs llama-13b / alpaca-13b / vicuna-13b-v1.2 (n=67) |
|---|---|---|---|
| Haiku | -0.458 [-1.056, +0.236] | +0.255 [-0.111, +0.548] | +0.036 [-0.111, +0.202] |
| Sonnet | -0.375 [-1.000, +0.312] | +0.196 [-0.102, +0.492] | +0.066 [-0.110, +0.243] |
| Opus | -0.292 [-0.941, +0.400] | +0.020 [-0.372, +0.397] | +0.036 [-0.114, +0.192] |
| Panel (a) majority | -0.375 [-1.000, +0.312] | +0.078 [-0.298, +0.417] | +0.036 [-0.123, +0.197] |
| Panel (b) mean | -0.458 [-1.056, +0.236] | +0.137 [-0.254, +0.480] | +0.126 [-0.028, +0.295] |
| GPT-4 (released) | -0.708 [-1.267, -0.115] | +0.196 [-0.156, +0.562] | +0.036 [-0.075, +0.160] |

#### Sonnet on all claude-v1 pairs of the test file (extra)

319 items with claude-v1, 71 questions; by opponent: vs gpt-4 71, vs gpt-3.5-turbo 64, vs llama-13b / alpaca-13b / vicuna-13b-v1.2 184.

| Judge | mean excess [95% CI] | interpretation |
|---|---|---|
| Sonnet | +0.074 [-0.012, +0.170] | CI includes 0: no detectable effect |
| GPT-4 (released, control) | +0.087 [-0.013, +0.183] | CI includes 0: no detectable effect |

Claude judge excess minus GPT-4 excess (same items, paired):

| Judge | difference [95% CI] | interpretation |
|---|---|---|
| Sonnet | -0.013 [-0.111, +0.093] | CI includes 0: no detectable effect |

Descriptive, by opponent (mean excess [95% CI]; n = items):

| Judge | vs gpt-4 (n=71) | vs gpt-3.5-turbo (n=64) | vs llama-13b / alpaca-13b / vicuna-13b-v1.2 (n=184) |
|---|---|---|---|
| Sonnet | -0.239 [-0.433, -0.056] | +0.267 [+0.053, +0.486] | +0.128 [+0.041, +0.223] |
| GPT-4 (released) | -0.140 [-0.416, +0.130] | +0.314 [+0.113, +0.513] | +0.096 [+0.005, +0.181] |

### Cost

| Judge | calls | input tokens | output tokens | cost on subsample | cost per 1,000 resolved verdicts |
|---|---|---|---|---|---|
| Haiku | 320 | 449988 | 171289 | $1.31 | $8.17 |
| Sonnet | 320 | 449988 | 96042 | $2.79 | $17.44 |
| Opus | 320 | 449988 | 111726 | $5.04 | $31.52 |
| Panel (all three) | 960 | 1349964 | 379057 | $9.14 | $57.13 |

### Ledger

| Cache file | calls | input tokens | output tokens | assumed cost | recorded |
|---|---|---|---|---|---|
| `data/mtbench/cache-panel-haiku-pilot.jsonl` | 60 | 74756 | 30853 | $0.23 | 2026-10-29 to 2026-10-29 |
| `data/mtbench/cache-panel-haiku.jsonl` | 319 | 449678 | 171203 | $1.31 | 2026-10-29 to 2026-10-29 |
| `data/mtbench/cache-panel-opus-pilot.jsonl` | 30 | 37378 | 10770 | $0.46 | 2026-10-29 to 2026-10-29 |
| `data/mtbench/cache-panel-opus.jsonl` | 319 | 449678 | 111606 | $5.04 | 2026-10-29 to 2026-10-29 |
| **total live calls this task** | 728 | | | **$7.03** | cap 1,800 calls / about $10 |

