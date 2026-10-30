# Contamination probe: GSM8K, program-built number variants

Protocol: `docs/protocol-contamination.md` (committed before the scored run). Scored
offline from the call caches. 140 source problems, original + 2 variants
each,
prompt `gsm-cot-v1`, max_tokens 1024, one sample per prompt, no sampling
parameter sent. Drop = accuracy(original) minus mean accuracy(perturbed variants),
item = source problem; CIs are cluster bootstraps over sources (10,000 resamples,
seed 0).

## Primary: evalkit `numeric_match`

| model | acc original | acc v1 | acc v2 | drop (pp) | 95% CI | 97.5% CI | sign-flip p | Holm p | reading |
|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 96.4% | 94.3% | 94.3% | +2.1 | [+0.0, +4.6] | [+0.0, +5.0] | 0.1094 | 0.2188 | no detectable drop |
| claude-sonnet-4-5-20250929 | 95.7% | 97.1% | 97.1% | -1.4 | [-3.9, +0.4] | [-4.3, +0.7] | 0.3750 | 0.3750 | negative drop (perturbed accuracy higher), not significant |

| model | orig right, v1 wrong | orig wrong, v1 right | orig right, v2 wrong | orig wrong, v2 right | McNemar exact p (orig vs v1) | McNemar exact p (orig vs v2) | drop orig-v1 (pp) [95% CI] | SD of per-source diff | MDE 80% power (alpha .05 / .025), pp |
|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 3 | 0 | 4 | 1 | 0.2500 | 0.3750 | +2.1 [+0.0, +5.0] | 0.132 | 3.1 / 3.4 |
| claude-sonnet-4-5-20250929 | 0 | 2 | 1 | 3 | 0.5000 | 0.6250 | -1.4 [-3.6, +0.0] | 0.133 | 3.2 / 3.5 |

## Robustness: HELM `final_number_exact_match`

| model | acc original | acc v1 | acc v2 | drop (pp) | 95% CI | 97.5% CI | sign-flip p | Holm p | reading |
|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 96.4% | 94.3% | 94.3% | +2.1 | [+0.0, +4.6] | [+0.0, +5.0] | 0.1094 | 0.2188 | no detectable drop |
| claude-sonnet-4-5-20250929 | 95.7% | 97.1% | 97.1% | -1.4 | [-3.9, +0.4] | [-4.3, +0.7] | 0.3750 | 0.3750 | negative drop (perturbed accuracy higher), not significant |

| model | orig right, v1 wrong | orig wrong, v1 right | orig right, v2 wrong | orig wrong, v2 right | McNemar exact p (orig vs v1) | McNemar exact p (orig vs v2) | drop orig-v1 (pp) [95% CI] | SD of per-source diff | MDE 80% power (alpha .05 / .025), pp |
|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 3 | 0 | 4 | 1 | 0.2500 | 0.3750 | +2.1 [+0.0, +5.0] | 0.132 | 3.1 / 3.4 |
| claude-sonnet-4-5-20250929 | 0 | 2 | 1 | 3 | 0.5000 | 0.6250 | -1.4 [-3.6, +0.0] | 0.133 | 3.2 / 3.5 |

## Reading (numeric mode, pre-registered rules)

- claude-haiku-5-5: no detectable drop; drop +2.1 pp, the 95% CI includes 0; MDE at 80% power 3.4 pp (alpha .025). A drop smaller than the MDE could not be excluded.
- claude-sonnet-4-5-20250929: negative drop (perturbed accuracy higher), not significant; drop -1.4 pp, the 95% CI includes 0; MDE at 80% power 3.5 pp (alpha .025). A drop smaller than the MDE could not be excluded.

## Difference of drops (descriptive, numeric mode)

claude-sonnet-4-5-20250929 minus claude-haiku-5-5: -3.6 pp [95% CI -6.8, -1.1], cluster bootstrap over sources.

## Difficulty neutrality of the golds (test sources)

| statistic | value |
|---|---|
| n_sources | 140.000 |
| mean_digits_original | 2.550 |
| mean_digits_perturbed | 2.571 |
| share_same_digit_count | 0.857 |
| share_perturbed_more_digits | 0.082 |
| share_perturbed_fewer_digits | 0.061 |
| median_gold_original | 76.500 |
| median_gold_perturbed | 79.500 |
| mean_log10_ratio | 0.044 |
| share_perturbed_larger | 0.639 |

## Reply diagnostics (numeric mode)

| model | missing | truncated at max_tokens | no `Answer:` line |
|---|---|---|---|
| claude-haiku-5-5 | 0 | 0 | 0 |
| claude-sonnet-4-5-20250929 | 0 | 0 | 0 |

## API ledger (all calls, dev pilot included; prices ASSUMED, not read from the API)

| model | calls | input tokens | output tokens | cost (USD, ASSUMED prices) | first | last |
|---|---|---|---|---|---|---|
| claude-haiku-5-5 (returned claude-haiku-5-5) | 438 | 66,475 | 77,487 | 0.45 | 2026-10-30T00:23:06+00:00 | 2026-10-30T00:25:29+00:00 |
| claude-sonnet-4-5-20250929 (returned claude-sonnet-4-5-20250929) | 438 | 52,890 | 84,341 | 1.42 | 2026-10-30T00:23:14+00:00 | 2026-10-30T00:29:20+00:00 |
| **total** | **876** | | | **1.88** | | |

Reading rules (pre-registered): a significant drop is consistent with memorisation of the
original items OR brittleness to number changes (this probe cannot separate the two); no
detectable drop is no evidence of contamination by this probe, not proof of none.
