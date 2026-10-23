seed 0; replications: H0 8000, power 3000, FWER 3000; bootstrap resamples 10000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences). Intervals are Wilson 99% over replications.

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|
| binary | 0.5 | 20 | 0.021 [0.017, 0.025] **conservative** | 0.021 [0.017, 0.025] **conservative** | 0.043 [0.037, 0.049] |
| binary | 0.5 | 50 | 0.031 [0.027, 0.037] **conservative** | 0.029 [0.025, 0.035] **conservative** | 0.047 [0.041, 0.053] |
| continuous | 0.5 | 20 | 0.046 [0.040, 0.052] | 0.022 [0.018, 0.026] **conservative** | 0.087 [0.079, 0.095] |
| continuous | 0.5 | 50 | 0.052 [0.046, 0.059] | 0.028 [0.024, 0.033] **conservative** | 0.067 [0.060, 0.074] |
| skewed | 0.5 | 20 | 0.089 [0.081, 0.097] **anti-conservative** | 0.074 [0.067, 0.082] **anti-conservative** | 0.127 [0.118, 0.137] |
| skewed | 0.5 | 50 | 0.075 [0.067, 0.083] **anti-conservative** | 0.194 [0.183, 0.206] **anti-conservative** | 0.081 [0.074, 0.089] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0.5 | 20 | 0.000 | 0.957 [0.951, 0.963] | 0.596 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.953 [0.947, 0.959] | 0.386 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.913 [0.905, 0.921] **undercovers** | 0.145 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.933 [0.926, 0.940] **undercovers** | 0.096 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.873 [0.863, 0.882] **undercovers** | 0.138 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.919 [0.911, 0.926] **undercovers** | 0.093 |
| mde | binary | 0.5 | 21 | 0.375 | 0.916 [0.902, 0.928] **undercovers** | 0.488 |
| mde | binary | 0.5 | 51 | 0.260 | 0.947 [0.936, 0.957] | 0.355 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.920 [0.906, 0.932] **undercovers** | 0.185 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.940 [0.928, 0.950] | 0.105 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.887 [0.871, 0.901] **undercovers** | 0.175 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.909 [0.894, 0.921] **undercovers** | 0.101 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0.5 | 0.375 | 0.599 | 21 | 0.80 | 0.622 [0.599, 0.644] **optimistic** | 0.622 [0.599, 0.644] | 0.723 [0.701, 0.743] |
| mde | binary | 0.5 | 0.260 | 0.657 | 51 | 0.80 | 0.716 [0.695, 0.737] **optimistic** | 0.712 [0.690, 0.733] | 0.769 [0.748, 0.788] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.867 [0.850, 0.882] **pessimistic** | 0.627 [0.604, 0.649] | 0.935 [0.923, 0.946] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.810 [0.791, 0.828] | 0.557 [0.534, 0.580] | 0.843 [0.825, 0.860] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.986 [0.979, 0.991] **pessimistic** | 0.986 [0.979, 0.991] | 0.999 [0.996, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.951 [0.939, 0.960] **pessimistic** | 0.341 [0.319, 0.363] | 0.975 [0.967, 0.982] |

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

- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.913 [0.905, 0.921]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.933 [0.926, 0.940]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.089 [0.081, 0.097]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.074 [0.067, 0.082]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.873 [0.863, 0.882]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.075 [0.067, 0.083]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.194 [0.183, 0.206]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.919 [0.911, 0.926]
- optimistic: randomisation power binary n*=21 ties=0.5 effect=0.375 (mde): 0.622 [0.599, 0.644]
- undercovers: bootstrap CI coverage binary n*=21 ties=0.5 effect=0.375 (mde): 0.916 [0.902, 0.928]
- optimistic: randomisation power binary n*=51 ties=0.5 effect=0.260 (mde): 0.716 [0.695, 0.737]
- undercovers: bootstrap CI coverage continuous n*=21 ties=0.5 effect=0.142 (mde): 0.920 [0.906, 0.932]
- undercovers: bootstrap CI coverage skewed n*=21 ties=0.5 effect=0.142 (mde): 0.887 [0.871, 0.901]
- undercovers: bootstrap CI coverage skewed n*=50 ties=0.5 effect=0.076 (mde): 0.909 [0.894, 0.921]
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

Wall time 29 s on 8 worker(s).
