### Tie margin, dev portion (leave-question-out selection)

Dev portion: 36 questions, 164 items (first 300 test items, pointwise scores from the cache). CV score = pooled held-out S1 of a fixed margin, which equals its S1 on the dev portion.

| delta | CV S1 | S2 | judge tie rate | human tie rate (per vote) |
|---|---|---|---|---|
| 0 | 71.1% | 89.4% | 24.4% | 27.4% |
| 1 | 66.8% | 93.5% | 47.6% | 27.4% |
| 2 | 59.7% | 95.6% | 62.2% | 27.4% |
| 3 | 51.1% | 94.0% | 72.0% | 27.4% |

**Selected delta-hat: 0** (largest CV S1; ties to the smaller delta).

Nested leave-question-out (selection inside each of 36 folds): out-of-fold S1 71.1% against 71.1% at delta 0 on the same items (+0.0 pp, no interval: descriptive). Fold choices (delta: folds): {'0.0': 36, '1.0': 0, '2.0': 0, '3.0': 0}.

delta-hat = 0: the confirmation portion is not scored (protocol).
