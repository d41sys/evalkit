seed 0; replications: H0 8000, power 3000, FWER 3000; bootstrap resamples 10000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences); CI method `auto`. Intervals are Wilson 99% over replications.

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |
|---|---|---|---|---|---|---|
| binary | 0.5 | 20 | 0.021 [0.017, 0.025] **conservative** | 0.021 [0.017, 0.025] **conservative** | 0.039 [0.034, 0.045] | 0.004 [0.002, 0.006] |
| binary | 0.5 | 50 | 0.031 [0.027, 0.037] **conservative** | 0.029 [0.025, 0.035] **conservative** | 0.046 [0.040, 0.052] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 20 | 0.046 [0.040, 0.052] | 0.022 [0.018, 0.026] **conservative** | 0.088 [0.080, 0.096] | 0.386 [0.372, 0.400] |
| continuous | 0.5 | 50 | 0.052 [0.046, 0.059] | 0.028 [0.024, 0.033] **conservative** | 0.069 [0.062, 0.076] | 0.057 [0.051, 0.064] |
| skewed | 0.5 | 20 | 0.089 [0.081, 0.097] **anti-conservative** | 0.074 [0.067, 0.082] **anti-conservative** | 0.122 [0.113, 0.132] | 0.652 [0.639, 0.666] |
| skewed | 0.5 | 50 | 0.075 [0.067, 0.083] **anti-conservative** | 0.194 [0.183, 0.206] **anti-conservative** | 0.080 [0.072, 0.088] | 0.668 [0.654, 0.681] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0.5 | 20 | 0.000 | 0.961 [0.955, 0.966] | 0.641 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.954 [0.948, 0.960] | 0.395 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.912 [0.904, 0.920] **undercovers** | 0.158 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.931 [0.924, 0.938] **undercovers** | 0.098 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.878 [0.868, 0.887] **undercovers** | 0.165 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.920 [0.912, 0.928] **undercovers** | 0.101 |
| mde | binary | 0.5 | 20 | 0.431 | 0.968 [0.959, 0.975] | 0.498 |
| mde | binary | 0.5 | 50 | 0.287 | 0.953 [0.942, 0.962] | 0.361 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.928 [0.915, 0.939] **undercovers** | 0.201 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.940 [0.928, 0.951] | 0.109 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.892 [0.876, 0.905] **undercovers** | 0.209 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.917 [0.903, 0.929] **undercovers** | 0.114 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0.5 | 0.431 | 0.560 | 20 | 0.80 | 0.792 [0.772, 0.810] | 0.792 [0.772, 0.810] | 0.870 [0.853, 0.885] |
| mde | binary | 0.5 | 0.287 | 0.646 | 50 | 0.80 | 0.802 [0.783, 0.820] | 0.796 [0.776, 0.814] | 0.836 [0.818, 0.853] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.867 [0.850, 0.882] **pessimistic** | 0.627 [0.604, 0.649] | 0.934 [0.922, 0.945] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.810 [0.791, 0.828] | 0.557 [0.534, 0.580] | 0.847 [0.829, 0.863] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.986 [0.979, 0.991] **pessimistic** | 0.986 [0.979, 0.991] | 0.999 [0.996, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.951 [0.939, 0.960] **pessimistic** | 0.341 [0.319, 0.363] | 0.978 [0.970, 0.984] |

### Holm family-wise error rate (all nulls true)

| kind | design | comparisons m | n | unadjusted FWER | Holm FWER |
|---|---|---|---|---|---|
| binary | independent | 3 | 50 | 0.097 [0.084, 0.111] | 0.030 [0.023, 0.039] **conservative** |
| binary | independent | 5 | 50 | 0.153 [0.137, 0.170] | 0.026 [0.020, 0.035] **conservative** |
| binary | independent | 10 | 50 | 0.280 [0.260, 0.302] | 0.029 [0.022, 0.038] **conservative** |
| binary | all-pairs | 3 | 50 | 0.073 [0.062, 0.087] | 0.021 [0.015, 0.029] **conservative** |
| binary | all-pairs | 6 | 50 | 0.147 [0.131, 0.164] | 0.027 [0.020, 0.036] **conservative** |
| binary | all-pairs | 10 | 50 | 0.192 [0.174, 0.211] | 0.020 [0.014, 0.028] **conservative** |
| continuous | independent | 3 | 50 | 0.142 [0.126, 0.159] | 0.050 [0.041, 0.062] |
| continuous | independent | 5 | 50 | 0.221 [0.202, 0.241] | 0.045 [0.036, 0.056] |
| continuous | independent | 10 | 50 | 0.409 [0.386, 0.432] | 0.045 [0.036, 0.056] |
| continuous | all-pairs | 3 | 50 | 0.123 [0.109, 0.140] | 0.042 [0.034, 0.053] |
| continuous | all-pairs | 6 | 50 | 0.210 [0.191, 0.229] | 0.044 [0.035, 0.054] |
| continuous | all-pairs | 10 | 50 | 0.289 [0.268, 0.311] | 0.047 [0.038, 0.058] |

### Findings under the decision rules

- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.912 [0.904, 0.920]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.931 [0.924, 0.938]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.089 [0.081, 0.097]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.074 [0.067, 0.082]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.878 [0.868, 0.887]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.075 [0.067, 0.083]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.194 [0.183, 0.206]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.920 [0.912, 0.928]
- undercovers: bootstrap CI coverage continuous n*=21 ties=0.5 effect=0.142 (mde): 0.928 [0.915, 0.939]
- undercovers: bootstrap CI coverage skewed n*=21 ties=0.5 effect=0.142 (mde): 0.892 [0.876, 0.905]
- undercovers: bootstrap CI coverage skewed n*=50 ties=0.5 effect=0.076 (mde): 0.917 [0.903, 0.929]
- conservative: randomisation type-I binary n=20 ties=0.5 (H0): 0.021 [0.017, 0.025]
- conservative: sign test type-I binary n=20 ties=0.5 (H0): 0.021 [0.017, 0.025]
- conservative: randomisation type-I binary n=50 ties=0.5 (H0): 0.031 [0.027, 0.037]
- conservative: sign test type-I binary n=50 ties=0.5 (H0): 0.029 [0.025, 0.035]
- conservative: sign test type-I continuous n=20 ties=0.5 (H0): 0.022 [0.018, 0.026]
- conservative: sign test type-I continuous n=50 ties=0.5 (H0): 0.028 [0.024, 0.033]
- pessimistic: randomisation power continuous n*=21 ties=0.5 effect=0.142 (mde): 0.867 [0.850, 0.882]
- pessimistic: randomisation power skewed n*=21 ties=0.5 effect=0.142 (mde): 0.986 [0.979, 0.991]
- pessimistic: randomisation power skewed n*=50 ties=0.5 effect=0.076 (mde): 0.951 [0.939, 0.960]
- conservative: Holm FWER binary independent m=3 n=50: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary independent m=5 n=50: 0.026 [0.020, 0.035]
- conservative: Holm FWER binary independent m=10 n=50: 0.029 [0.022, 0.038]
- conservative: Holm FWER binary all-pairs m=3 n=50: 0.021 [0.015, 0.029]
- conservative: Holm FWER binary all-pairs m=6 n=50: 0.027 [0.020, 0.036]
- conservative: Holm FWER binary all-pairs m=10 n=50: 0.020 [0.014, 0.028]

Wall time 54 s on 8 worker(s).
