seed 0; replications: H0 8000, power 3000, FWER 3000; bootstrap resamples 2000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences); CI method `auto`. Intervals are Wilson 99% over replications.

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |
|---|---|---|---|---|---|---|
| binary | 0 | 20 | 0.044 [0.039, 0.051] | 0.044 [0.039, 0.051] | 0.040 [0.035, 0.046] | 0.044 [0.039, 0.051] |
| binary | 0 | 50 | 0.031 [0.027, 0.037] **conservative** | 0.031 [0.027, 0.037] **conservative** | 0.044 [0.039, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0 | 115 | 0.039 [0.034, 0.045] | 0.039 [0.034, 0.045] | 0.038 [0.033, 0.044] | 0.000 [0.000, 0.001] |
| binary | 0 | 240 | 0.045 [0.039, 0.051] | 0.046 [0.040, 0.053] | 0.048 [0.042, 0.055] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 20 | 0.023 [0.019, 0.028] **conservative** | 0.023 [0.019, 0.028] **conservative** | 0.045 [0.039, 0.051] | 0.003 [0.002, 0.005] |
| binary | 0.5 | 50 | 0.029 [0.025, 0.035] **conservative** | 0.028 [0.024, 0.033] **conservative** | 0.044 [0.038, 0.050] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 115 | 0.037 [0.032, 0.043] | 0.038 [0.033, 0.044] | 0.051 [0.045, 0.057] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 240 | 0.039 [0.034, 0.045] | 0.039 [0.034, 0.045] | 0.046 [0.040, 0.052] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 20 | 0.004 [0.003, 0.006] **conservative** | 0.004 [0.003, 0.006] **conservative** | 0.096 [0.088, 0.105] | 0.214 [0.203, 0.226] |
| binary | 0.8 | 50 | 0.024 [0.020, 0.029] **conservative** | 0.024 [0.020, 0.029] **conservative** | 0.075 [0.068, 0.083] | 0.019 [0.015, 0.023] |
| binary | 0.8 | 115 | 0.030 [0.026, 0.036] **conservative** | 0.028 [0.024, 0.033] **conservative** | 0.055 [0.049, 0.062] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 240 | 0.038 [0.033, 0.044] | 0.038 [0.033, 0.044] | 0.056 [0.049, 0.062] | 0.000 [0.000, 0.001] |
| continuous | 0 | 20 | 0.051 [0.045, 0.058] | 0.042 [0.037, 0.048] | 0.053 [0.047, 0.060] | 0.061 [0.055, 0.068] |
| continuous | 0 | 50 | 0.048 [0.042, 0.054] | 0.034 [0.029, 0.040] **conservative** | 0.048 [0.043, 0.055] | 0.000 [0.000, 0.001] |
| continuous | 0 | 115 | 0.052 [0.046, 0.059] | 0.040 [0.034, 0.046] | 0.052 [0.046, 0.059] | 0.000 [0.000, 0.001] |
| continuous | 0 | 240 | 0.049 [0.043, 0.055] | 0.041 [0.036, 0.047] | 0.049 [0.043, 0.056] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 20 | 0.045 [0.039, 0.051] | 0.022 [0.018, 0.027] **conservative** | 0.093 [0.085, 0.102] | 0.388 [0.374, 0.402] |
| continuous | 0.5 | 50 | 0.053 [0.047, 0.060] | 0.033 [0.028, 0.038] **conservative** | 0.075 [0.068, 0.083] | 0.065 [0.058, 0.072] |
| continuous | 0.5 | 115 | 0.048 [0.042, 0.055] | 0.036 [0.031, 0.042] | 0.058 [0.052, 0.065] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 240 | 0.046 [0.041, 0.053] | 0.040 [0.035, 0.046] | 0.052 [0.046, 0.059] | 0.000 [0.000, 0.001] |
| continuous | 0.8 | 20 | 0.008 [0.006, 0.011] **conservative** | 0.005 [0.004, 0.008] **conservative** | 0.120 [0.111, 0.130] | 0.780 [0.768, 0.792] |
| continuous | 0.8 | 50 | 0.042 [0.037, 0.048] | 0.020 [0.016, 0.024] **conservative** | 0.111 [0.102, 0.120] | 0.517 [0.503, 0.531] |
| continuous | 0.8 | 115 | 0.050 [0.044, 0.057] | 0.031 [0.026, 0.036] **conservative** | 0.081 [0.073, 0.089] | 0.153 [0.143, 0.164] |
| continuous | 0.8 | 240 | 0.052 [0.046, 0.059] | 0.039 [0.034, 0.045] | 0.070 [0.063, 0.078] | 0.006 [0.004, 0.008] |
| skewed | 0 | 20 | 0.079 [0.072, 0.088] **anti-conservative** | 0.196 [0.185, 0.208] **anti-conservative** | 0.053 [0.047, 0.059] | 0.726 [0.713, 0.738] |
| skewed | 0 | 50 | 0.065 [0.058, 0.072] **anti-conservative** | 0.406 [0.392, 0.420] **anti-conservative** | 0.052 [0.046, 0.059] | 0.589 [0.575, 0.603] |
| skewed | 0 | 115 | 0.056 [0.050, 0.063] | 0.789 [0.777, 0.800] **anti-conservative** | 0.050 [0.044, 0.057] | 0.208 [0.197, 0.220] |
| skewed | 0 | 240 | 0.052 [0.046, 0.059] | 0.984 [0.980, 0.987] **anti-conservative** | 0.049 [0.043, 0.056] | 0.017 [0.014, 0.021] |
| skewed | 0.5 | 20 | 0.089 [0.081, 0.097] **anti-conservative** | 0.067 [0.060, 0.074] **anti-conservative** | 0.124 [0.115, 0.134] | 0.651 [0.637, 0.665] |
| skewed | 0.5 | 50 | 0.079 [0.072, 0.087] **anti-conservative** | 0.199 [0.188, 0.211] **anti-conservative** | 0.086 [0.078, 0.094] | 0.661 [0.647, 0.675] |
| skewed | 0.5 | 115 | 0.062 [0.055, 0.069] **anti-conservative** | 0.475 [0.461, 0.489] **anti-conservative** | 0.063 [0.056, 0.070] | 0.516 [0.501, 0.530] |
| skewed | 0.5 | 240 | 0.056 [0.050, 0.063] **anti-conservative** | 0.808 [0.797, 0.819] **anti-conservative** | 0.056 [0.050, 0.063] | 0.198 [0.187, 0.210] |
| skewed | 0.8 | 20 | 0.015 [0.011, 0.018] **conservative** | 0.009 [0.007, 0.012] **conservative** | 0.162 [0.152, 0.173] | 0.834 [0.823, 0.844] |
| skewed | 0.8 | 50 | 0.088 [0.080, 0.097] **anti-conservative** | 0.075 [0.068, 0.083] **anti-conservative** | 0.151 [0.141, 0.161] | 0.701 [0.688, 0.714] |
| skewed | 0.8 | 115 | 0.080 [0.073, 0.088] **anti-conservative** | 0.186 [0.175, 0.197] **anti-conservative** | 0.101 [0.093, 0.110] | 0.651 [0.637, 0.665] |
| skewed | 0.8 | 240 | 0.064 [0.057, 0.071] **anti-conservative** | 0.402 [0.388, 0.416] **anti-conservative** | 0.072 [0.065, 0.080] | 0.577 [0.562, 0.591] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0 | 20 | 0.000 | 0.960 [0.954, 0.965] | 0.904 |
| h0 | binary | 0 | 50 | 0.000 | 0.956 [0.949, 0.961] | 0.577 |
| h0 | binary | 0 | 115 | 0.000 | 0.962 [0.956, 0.967] | 0.368 |
| h0 | binary | 0 | 240 | 0.000 | 0.952 [0.945, 0.958] | 0.254 |
| h0 | binary | 0.5 | 20 | 0.000 | 0.955 [0.949, 0.961] | 0.661 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.956 [0.950, 0.962] | 0.401 |
| h0 | binary | 0.5 | 115 | 0.000 | 0.950 [0.943, 0.955] | 0.261 |
| h0 | binary | 0.5 | 240 | 0.000 | 0.954 [0.948, 0.960] | 0.179 |
| h0 | binary | 0.8 | 20 | 0.000 | 0.904 [0.895, 0.912] **undercovers** | 0.384 |
| h0 | binary | 0.8 | 50 | 0.000 | 0.925 [0.917, 0.932] **undercovers** | 0.250 |
| h0 | binary | 0.8 | 115 | 0.000 | 0.945 [0.938, 0.951] | 0.164 |
| h0 | binary | 0.8 | 240 | 0.000 | 0.945 [0.938, 0.951] | 0.113 |
| h0 | continuous | 0 | 20 | 0.000 | 0.947 [0.940, 0.953] | 0.233 |
| h0 | continuous | 0 | 50 | 0.000 | 0.952 [0.945, 0.957] | 0.142 |
| h0 | continuous | 0 | 115 | 0.000 | 0.948 [0.941, 0.954] | 0.092 |
| h0 | continuous | 0 | 240 | 0.000 | 0.951 [0.944, 0.957] | 0.063 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.907 [0.898, 0.915] **undercovers** | 0.173 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.925 [0.917, 0.932] **undercovers** | 0.100 |
| h0 | continuous | 0.5 | 115 | 0.000 | 0.942 [0.935, 0.948] **undercovers** | 0.065 |
| h0 | continuous | 0.5 | 240 | 0.000 | 0.948 [0.941, 0.954] | 0.045 |
| h0 | continuous | 0.8 | 20 | 0.000 | 0.880 [0.870, 0.889] **undercovers** | 0.276 |
| h0 | continuous | 0.8 | 50 | 0.000 | 0.889 [0.880, 0.898] **undercovers** | 0.072 |
| h0 | continuous | 0.8 | 115 | 0.000 | 0.919 [0.911, 0.927] **undercovers** | 0.041 |
| h0 | continuous | 0.8 | 240 | 0.000 | 0.929 [0.922, 0.937] **undercovers** | 0.028 |
| h0 | skewed | 0 | 20 | 0.000 | 0.947 [0.941, 0.953] | 0.263 |
| h0 | skewed | 0 | 50 | 0.000 | 0.948 [0.941, 0.954] | 0.148 |
| h0 | skewed | 0 | 115 | 0.000 | 0.950 [0.943, 0.956] | 0.094 |
| h0 | skewed | 0 | 240 | 0.000 | 0.951 [0.944, 0.957] | 0.064 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.875 [0.866, 0.885] **undercovers** | 0.187 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.914 [0.906, 0.922] **undercovers** | 0.107 |
| h0 | skewed | 0.5 | 115 | 0.000 | 0.937 [0.930, 0.944] **undercovers** | 0.067 |
| h0 | skewed | 0.5 | 240 | 0.000 | 0.944 [0.937, 0.950] | 0.046 |
| h0 | skewed | 0.8 | 20 | 0.000 | 0.838 [0.827, 0.848] **undercovers** | 0.226 |
| h0 | skewed | 0.8 | 50 | 0.000 | 0.849 [0.839, 0.859] **undercovers** | 0.073 |
| h0 | skewed | 0.8 | 115 | 0.000 | 0.899 [0.890, 0.907] **undercovers** | 0.044 |
| h0 | skewed | 0.8 | 240 | 0.000 | 0.928 [0.920, 0.935] **undercovers** | 0.029 |
| mde | binary | 0 | 21 | 0.590 | 0.813 [0.794, 0.830] **undercovers** | 0.692 |
| mde | binary | 0 | 51 | 0.387 | 0.977 [0.969, 0.983] **overcovers** | 0.527 |
| mde | binary | 0 | 115 | 0.259 | 0.954 [0.943, 0.963] | 0.357 |
| mde | binary | 0 | 240 | 0.180 | 0.949 [0.938, 0.958] | 0.250 |
| mde | binary | 0.5 | 20 | 0.417 | 0.976 [0.968, 0.982] **overcovers** | 0.531 |
| mde | binary | 0.5 | 50 | 0.274 | 0.953 [0.942, 0.962] | 0.371 |
| mde | binary | 0.5 | 115 | 0.183 | 0.946 [0.935, 0.956] | 0.252 |
| mde | binary | 0.5 | 240 | 0.127 | 0.945 [0.933, 0.955] | 0.176 |
| mde | binary | 0.8 | 51 | 0.173 | 0.959 [0.948, 0.967] | 0.240 |
| mde | binary | 0.8 | 115 | 0.116 | 0.943 [0.931, 0.953] | 0.159 |
| mde | binary | 0.8 | 241 | 0.080 | 0.948 [0.937, 0.958] | 0.111 |
| mde | continuous | 0 | 21 | 0.157 | 0.948 [0.937, 0.958] | 0.230 |
| mde | continuous | 0 | 51 | 0.099 | 0.951 [0.940, 0.960] | 0.140 |
| mde | continuous | 0 | 115 | 0.065 | 0.943 [0.931, 0.953] | 0.092 |
| mde | continuous | 0 | 241 | 0.045 | 0.953 [0.942, 0.962] | 0.063 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.966 [0.956, 0.973] | 0.228 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.947 [0.935, 0.956] | 0.111 |
| mde | continuous | 0.5 | 116 | 0.048 | 0.950 [0.938, 0.959] | 0.067 |
| mde | continuous | 0.5 | 241 | 0.033 | 0.946 [0.934, 0.955] | 0.045 |
| mde | continuous | 0.8 | 51 | 0.073 | 0.972 [0.963, 0.978] **overcovers** | 0.122 |
| mde | continuous | 0.8 | 116 | 0.034 | 0.952 [0.941, 0.961] | 0.050 |
| mde | continuous | 0.8 | 241 | 0.022 | 0.950 [0.939, 0.959] | 0.031 |
| mde | skewed | 0 | 21 | 0.157 | 0.952 [0.941, 0.961] | 0.259 |
| mde | skewed | 0 | 51 | 0.099 | 0.956 [0.945, 0.964] | 0.147 |
| mde | skewed | 0 | 115 | 0.065 | 0.944 [0.932, 0.954] | 0.094 |
| mde | skewed | 0 | 241 | 0.045 | 0.945 [0.933, 0.955] | 0.064 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.951 [0.940, 0.960] | 0.257 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.945 [0.933, 0.955] | 0.126 |
| mde | skewed | 0.5 | 116 | 0.048 | 0.949 [0.938, 0.959] | 0.071 |
| mde | skewed | 0.5 | 241 | 0.033 | 0.943 [0.931, 0.953] | 0.047 |
| mde | skewed | 0.8 | 51 | 0.073 | 0.960 [0.950, 0.968] | 0.125 |
| mde | skewed | 0.8 | 116 | 0.034 | 0.952 [0.941, 0.961] | 0.059 |
| mde | skewed | 0.8 | 241 | 0.022 | 0.947 [0.935, 0.957] | 0.033 |
| fixed | binary | 0.6 | 1254 | 0.050 | 0.953 [0.942, 0.962] | 0.070 |
| fixed | binary | 0.6 | 312 | 0.100 | 0.948 [0.936, 0.957] | 0.139 |
| fixed | binary | 0.6 | 77 | 0.200 | 0.947 [0.935, 0.957] | 0.271 |
| fixed | continuous | 0.6 | 91 | 0.050 | 0.942 [0.930, 0.952] | 0.071 |
| fixed | continuous | 0.6 | 32 | 0.100 | 0.968 [0.959, 0.976] | 0.157 |
| fixed | continuous | 0.6 | 17 | 0.200 | 0.974 [0.965, 0.981] **overcovers** | 0.382 |
| fixed | skewed | 0.6 | 91 | 0.050 | 0.945 [0.933, 0.955] | 0.079 |
| fixed | skewed | 0.6 | 32 | 0.100 | 0.961 [0.950, 0.969] | 0.183 |
| fixed | skewed | 0.6 | 17 | 0.200 | 0.964 [0.954, 0.972] | 0.338 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0 | 0.590 | 0.807 | 21 | 0.80 | 0.748 [0.727, 0.768] **optimistic** | 0.748 [0.727, 0.768] | 0.720 [0.698, 0.741] |
| mde | binary | 0 | 0.387 | 0.922 | 51 | 0.80 | 0.768 [0.748, 0.788] **optimistic** | 0.803 [0.784, 0.821] | 0.761 [0.741, 0.781] |
| mde | binary | 0 | 0.259 | 0.966 | 115 | 0.80 | 0.763 [0.743, 0.783] **optimistic** | 0.764 [0.743, 0.783] | 0.758 [0.737, 0.777] |
| mde | binary | 0 | 0.180 | 0.984 | 240 | 0.80 | 0.780 [0.760, 0.799] **optimistic** | 0.786 [0.766, 0.804] | 0.787 [0.767, 0.806] |
| mde | binary | 0.5 | 0.417 | 0.571 | 20 | 0.80 | 0.763 [0.742, 0.782] **optimistic** | 0.763 [0.742, 0.782] | 0.856 [0.839, 0.872] |
| mde | binary | 0.5 | 0.274 | 0.652 | 50 | 0.80 | 0.753 [0.733, 0.773] **optimistic** | 0.743 [0.722, 0.763] | 0.800 [0.781, 0.818] |
| mde | binary | 0.5 | 0.183 | 0.683 | 115 | 0.80 | 0.766 [0.746, 0.786] **optimistic** | 0.768 [0.748, 0.788] | 0.798 [0.778, 0.816] |
| mde | binary | 0.5 | 0.127 | 0.696 | 240 | 0.80 | 0.785 [0.765, 0.804] | 0.785 [0.765, 0.803] | 0.808 [0.789, 0.826] |
| mde | binary | 0.8 | 0.173 | 0.412 | 51 | 0.80 | 0.788 [0.768, 0.807] | 0.788 [0.768, 0.807] | 0.918 [0.904, 0.930] |
| mde | binary | 0.8 | 0.116 | 0.432 | 115 | 0.80 | 0.762 [0.741, 0.781] **optimistic** | 0.760 [0.739, 0.779] | 0.838 [0.820, 0.855] |
| mde | binary | 0.8 | 0.080 | 0.440 | 241 | 0.80 | 0.780 [0.760, 0.799] **optimistic** | 0.782 [0.762, 0.801] | 0.834 [0.816, 0.851] |
| mde | continuous | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.776 [0.755, 0.795] **optimistic** | 0.494 [0.470, 0.517] | 0.762 [0.742, 0.782] |
| mde | continuous | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.797 [0.778, 0.816] | 0.613 [0.590, 0.636] | 0.793 [0.774, 0.812] |
| mde | continuous | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.782 [0.762, 0.800] | 0.571 [0.548, 0.594] | 0.785 [0.765, 0.804] |
| mde | continuous | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.801 [0.782, 0.819] | 0.559 [0.536, 0.583] | 0.800 [0.781, 0.818] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.859 [0.841, 0.874] | 0.625 [0.602, 0.647] | 0.934 [0.921, 0.944] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.817 [0.798, 0.834] | 0.565 [0.542, 0.588] | 0.859 [0.841, 0.874] |
| mde | continuous | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.815 [0.796, 0.832] | 0.572 [0.548, 0.595] | 0.835 [0.817, 0.852] |
| mde | continuous | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.821 [0.802, 0.838] | 0.589 [0.566, 0.612] | 0.826 [0.808, 0.843] |
| mde | continuous | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.910 [0.896, 0.923] **pessimistic** | 0.775 [0.755, 0.794] | 0.985 [0.979, 0.990] |
| mde | continuous | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.866 [0.850, 0.882] | 0.625 [0.602, 0.648] | 0.917 [0.903, 0.929] |
| mde | continuous | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.833 [0.814, 0.849] | 0.618 [0.595, 0.640] | 0.864 [0.847, 0.879] |
| mde | skewed | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.940 [0.927, 0.950] **pessimistic** | 0.316 [0.294, 0.338] | 0.982 [0.974, 0.987] |
| mde | skewed | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.880 [0.864, 0.894] **pessimistic** | 0.096 [0.083, 0.111] | 0.936 [0.924, 0.947] |
| mde | skewed | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.834 [0.815, 0.850] | 0.067 [0.056, 0.080] | 0.887 [0.871, 0.901] |
| mde | skewed | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.822 [0.803, 0.839] | 0.418 [0.395, 0.441] | 0.872 [0.855, 0.887] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.985 [0.978, 0.989] **pessimistic** | 0.985 [0.978, 0.989] | 1.000 [0.998, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.960 [0.950, 0.968] **pessimistic** | 0.346 [0.324, 0.369] | 0.990 [0.984, 0.994] |
| mde | skewed | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.898 [0.883, 0.911] **pessimistic** | 0.064 [0.053, 0.076] | 0.947 [0.935, 0.957] |
| mde | skewed | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.853 [0.836, 0.869] | 0.072 [0.061, 0.085] | 0.905 [0.890, 0.918] |
| mde | skewed | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.957 [0.946, 0.965] **pessimistic** | 0.957 [0.946, 0.965] | 0.998 [0.995, 0.999] |
| mde | skewed | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.985 [0.978, 0.990] **pessimistic** | 0.540 [0.516, 0.563] | 0.997 [0.993, 0.999] |
| mde | skewed | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.924 [0.911, 0.936] **pessimistic** | 0.131 [0.116, 0.148] | 0.968 [0.959, 0.976] |
| fixed | binary | 0.6 | 0.050 | 0.630 | 1254 | 0.80 | 0.794 [0.775, 0.813] | 0.795 [0.775, 0.813] | 0.803 [0.784, 0.821] |
| fixed | binary | 0.6 | 0.100 | 0.624 | 312 | 0.80 | 0.769 [0.748, 0.788] **optimistic** | 0.767 [0.747, 0.786] | 0.794 [0.774, 0.812] |
| fixed | binary | 0.6 | 0.200 | 0.600 | 77 | 0.80 | 0.766 [0.745, 0.785] **optimistic** | 0.760 [0.739, 0.779] | 0.819 [0.800, 0.836] |
| fixed | continuous | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.827 [0.808, 0.844] | 0.599 [0.576, 0.622] | 0.864 [0.847, 0.879] |
| fixed | continuous | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.873 [0.857, 0.888] **pessimistic** | 0.623 [0.600, 0.645] | 0.938 [0.926, 0.948] |
| fixed | continuous | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.704 [0.682, 0.725] **optimistic** | 0.649 [0.626, 0.671] | 0.981 [0.973, 0.986] |
| fixed | skewed | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.934 [0.921, 0.944] **pessimistic** | 0.207 [0.188, 0.226] | 0.975 [0.966, 0.981] |
| fixed | skewed | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.997 [0.993, 0.999] **pessimistic** | 0.997 [0.993, 0.999] | 1.000 [0.997, 1.000] |
| fixed | skewed | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.728 [0.707, 0.748] **optimistic** | 0.728 [0.707, 0.748] | 0.987 [0.981, 0.992] |

MDE cells with no attainable effect (binary: even every discordant pair favouring one model is not detectable at this n; continuous: the formula's fixed point does not exist): binary n=20 ties=0.8; continuous n=20 ties=0.8; skewed n=20 ties=0.8.

### Holm family-wise error rate (all nulls true)

| kind | design | comparisons m | n | unadjusted FWER | Holm FWER |
|---|---|---|---|---|---|
| binary | independent | 3 | 50 | 0.095 [0.082, 0.110] | 0.030 [0.023, 0.039] **conservative** |
| binary | independent | 5 | 50 | 0.151 [0.135, 0.169] | 0.027 [0.020, 0.035] **conservative** |
| binary | independent | 10 | 50 | 0.261 [0.241, 0.282] | 0.024 [0.018, 0.032] **conservative** |
| binary | all-pairs | 3 | 50 | 0.080 [0.068, 0.093] | 0.024 [0.018, 0.032] **conservative** |
| binary | all-pairs | 6 | 50 | 0.132 [0.117, 0.148] | 0.022 [0.016, 0.030] **conservative** |
| binary | all-pairs | 10 | 50 | 0.203 [0.185, 0.223] | 0.026 [0.020, 0.035] **conservative** |
| binary | independent | 3 | 115 | 0.111 [0.097, 0.126] | 0.031 [0.024, 0.040] **conservative** |
| binary | independent | 5 | 115 | 0.162 [0.145, 0.180] | 0.031 [0.024, 0.041] |
| binary | independent | 10 | 115 | 0.305 [0.284, 0.327] | 0.030 [0.023, 0.039] **conservative** |
| binary | all-pairs | 3 | 115 | 0.094 [0.081, 0.109] | 0.030 [0.023, 0.039] **conservative** |
| binary | all-pairs | 6 | 115 | 0.155 [0.139, 0.173] | 0.030 [0.023, 0.039] **conservative** |
| binary | all-pairs | 10 | 115 | 0.222 [0.203, 0.242] | 0.025 [0.019, 0.034] **conservative** |
| continuous | independent | 3 | 50 | 0.143 [0.127, 0.160] | 0.047 [0.038, 0.058] |
| continuous | independent | 5 | 50 | 0.222 [0.203, 0.242] | 0.050 [0.040, 0.061] |
| continuous | independent | 10 | 50 | 0.403 [0.381, 0.427] | 0.049 [0.040, 0.061] |
| continuous | all-pairs | 3 | 50 | 0.118 [0.104, 0.134] | 0.039 [0.031, 0.050] |
| continuous | all-pairs | 6 | 50 | 0.209 [0.191, 0.229] | 0.041 [0.033, 0.052] |
| continuous | all-pairs | 10 | 50 | 0.295 [0.274, 0.317] | 0.043 [0.034, 0.053] |
| continuous | independent | 3 | 115 | 0.137 [0.121, 0.154] | 0.044 [0.036, 0.055] |
| continuous | independent | 5 | 115 | 0.223 [0.204, 0.244] | 0.050 [0.040, 0.061] |
| continuous | independent | 10 | 115 | 0.404 [0.381, 0.428] | 0.046 [0.037, 0.057] |
| continuous | all-pairs | 3 | 115 | 0.123 [0.109, 0.140] | 0.040 [0.031, 0.050] |
| continuous | all-pairs | 6 | 115 | 0.206 [0.188, 0.226] | 0.039 [0.031, 0.050] |
| continuous | all-pairs | 10 | 115 | 0.276 [0.255, 0.297] | 0.041 [0.033, 0.051] |

### Findings under the decision rules

- undercovers: bootstrap CI coverage binary n=20 ties=0.8 (H0): 0.904 [0.895, 0.912]
- undercovers: bootstrap CI coverage binary n=50 ties=0.8 (H0): 0.925 [0.917, 0.932]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.907 [0.898, 0.915]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.925 [0.917, 0.932]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.5 (H0): 0.942 [0.935, 0.948]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.8 (H0): 0.880 [0.870, 0.889]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.8 (H0): 0.889 [0.880, 0.898]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.8 (H0): 0.919 [0.911, 0.927]
- undercovers: bootstrap CI coverage continuous n=240 ties=0.8 (H0): 0.929 [0.922, 0.937]
- anti-conservative: randomisation type-I skewed n=20 ties=0 (H0): 0.079 [0.072, 0.088]
- anti-conservative: sign test type-I skewed n=20 ties=0 (H0): 0.196 [0.185, 0.208]
- anti-conservative: randomisation type-I skewed n=50 ties=0 (H0): 0.065 [0.058, 0.072]
- anti-conservative: sign test type-I skewed n=50 ties=0 (H0): 0.406 [0.392, 0.420]
- anti-conservative: sign test type-I skewed n=115 ties=0 (H0): 0.789 [0.777, 0.800]
- anti-conservative: sign test type-I skewed n=240 ties=0 (H0): 0.984 [0.980, 0.987]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.089 [0.081, 0.097]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.067 [0.060, 0.074]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.875 [0.866, 0.885]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.079 [0.072, 0.087]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.199 [0.188, 0.211]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.914 [0.906, 0.922]
- anti-conservative: randomisation type-I skewed n=115 ties=0.5 (H0): 0.062 [0.055, 0.069]
- anti-conservative: sign test type-I skewed n=115 ties=0.5 (H0): 0.475 [0.461, 0.489]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.5 (H0): 0.937 [0.930, 0.944]
- anti-conservative: randomisation type-I skewed n=240 ties=0.5 (H0): 0.056 [0.050, 0.063]
- anti-conservative: sign test type-I skewed n=240 ties=0.5 (H0): 0.808 [0.797, 0.819]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.8 (H0): 0.838 [0.827, 0.848]
- anti-conservative: randomisation type-I skewed n=50 ties=0.8 (H0): 0.088 [0.080, 0.097]
- anti-conservative: sign test type-I skewed n=50 ties=0.8 (H0): 0.075 [0.068, 0.083]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.8 (H0): 0.849 [0.839, 0.859]
- anti-conservative: randomisation type-I skewed n=115 ties=0.8 (H0): 0.080 [0.073, 0.088]
- anti-conservative: sign test type-I skewed n=115 ties=0.8 (H0): 0.186 [0.175, 0.197]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.8 (H0): 0.899 [0.890, 0.907]
- anti-conservative: randomisation type-I skewed n=240 ties=0.8 (H0): 0.064 [0.057, 0.071]
- anti-conservative: sign test type-I skewed n=240 ties=0.8 (H0): 0.402 [0.388, 0.416]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.8 (H0): 0.928 [0.920, 0.935]
- optimistic: randomisation power binary n*=21 ties=0 effect=0.590 (mde): 0.748 [0.727, 0.768]
- undercovers: bootstrap CI coverage binary n*=21 ties=0 effect=0.590 (mde): 0.813 [0.794, 0.830]
- optimistic: randomisation power binary n*=51 ties=0 effect=0.387 (mde): 0.768 [0.748, 0.788]
- optimistic: randomisation power binary n*=115 ties=0 effect=0.259 (mde): 0.763 [0.743, 0.783]
- optimistic: randomisation power binary n*=240 ties=0 effect=0.180 (mde): 0.780 [0.760, 0.799]
- optimistic: randomisation power binary n*=20 ties=0.5 effect=0.417 (mde): 0.763 [0.742, 0.782]
- optimistic: randomisation power binary n*=50 ties=0.5 effect=0.274 (mde): 0.753 [0.733, 0.773]
- optimistic: randomisation power binary n*=115 ties=0.5 effect=0.183 (mde): 0.766 [0.746, 0.786]
- optimistic: randomisation power binary n*=115 ties=0.8 effect=0.116 (mde): 0.762 [0.741, 0.781]
- optimistic: randomisation power binary n*=241 ties=0.8 effect=0.080 (mde): 0.780 [0.760, 0.799]
- optimistic: randomisation power continuous n*=21 ties=0 effect=0.157 (mde): 0.776 [0.755, 0.795]
- optimistic: randomisation power binary n*=312 ties=0.6 effect=0.100 (fixed): 0.769 [0.748, 0.788]
- optimistic: randomisation power binary n*=77 ties=0.6 effect=0.200 (fixed): 0.766 [0.745, 0.785]
- optimistic: randomisation power continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.704 [0.682, 0.725]
- optimistic: randomisation power skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.728 [0.707, 0.748]
- conservative: randomisation type-I binary n=50 ties=0 (H0): 0.031 [0.027, 0.037]
- conservative: sign test type-I binary n=50 ties=0 (H0): 0.031 [0.027, 0.037]
- conservative: randomisation type-I binary n=20 ties=0.5 (H0): 0.023 [0.019, 0.028]
- conservative: sign test type-I binary n=20 ties=0.5 (H0): 0.023 [0.019, 0.028]
- conservative: randomisation type-I binary n=50 ties=0.5 (H0): 0.029 [0.025, 0.035]
- conservative: sign test type-I binary n=50 ties=0.5 (H0): 0.028 [0.024, 0.033]
- conservative: randomisation type-I binary n=20 ties=0.8 (H0): 0.004 [0.003, 0.006]
- conservative: sign test type-I binary n=20 ties=0.8 (H0): 0.004 [0.003, 0.006]
- conservative: randomisation type-I binary n=50 ties=0.8 (H0): 0.024 [0.020, 0.029]
- conservative: sign test type-I binary n=50 ties=0.8 (H0): 0.024 [0.020, 0.029]
- conservative: randomisation type-I binary n=115 ties=0.8 (H0): 0.030 [0.026, 0.036]
- conservative: sign test type-I binary n=115 ties=0.8 (H0): 0.028 [0.024, 0.033]
- conservative: sign test type-I continuous n=50 ties=0 (H0): 0.034 [0.029, 0.040]
- conservative: sign test type-I continuous n=20 ties=0.5 (H0): 0.022 [0.018, 0.027]
- conservative: sign test type-I continuous n=50 ties=0.5 (H0): 0.033 [0.028, 0.038]
- conservative: randomisation type-I continuous n=20 ties=0.8 (H0): 0.008 [0.006, 0.011]
- conservative: sign test type-I continuous n=20 ties=0.8 (H0): 0.005 [0.004, 0.008]
- conservative: sign test type-I continuous n=50 ties=0.8 (H0): 0.020 [0.016, 0.024]
- conservative: sign test type-I continuous n=115 ties=0.8 (H0): 0.031 [0.026, 0.036]
- conservative: randomisation type-I skewed n=20 ties=0.8 (H0): 0.015 [0.011, 0.018]
- conservative: sign test type-I skewed n=20 ties=0.8 (H0): 0.009 [0.007, 0.012]
- overcovers: bootstrap CI coverage binary n*=51 ties=0 effect=0.387 (mde): 0.977 [0.969, 0.983]
- overcovers: bootstrap CI coverage binary n*=20 ties=0.5 effect=0.417 (mde): 0.976 [0.968, 0.982]
- pessimistic: randomisation power continuous n*=51 ties=0.8 effect=0.073 (mde): 0.910 [0.896, 0.923]
- overcovers: bootstrap CI coverage continuous n*=51 ties=0.8 effect=0.073 (mde): 0.972 [0.963, 0.978]
- pessimistic: randomisation power skewed n*=21 ties=0 effect=0.157 (mde): 0.940 [0.927, 0.950]
- pessimistic: randomisation power skewed n*=51 ties=0 effect=0.099 (mde): 0.880 [0.864, 0.894]
- pessimistic: randomisation power skewed n*=21 ties=0.5 effect=0.142 (mde): 0.985 [0.978, 0.989]
- pessimistic: randomisation power skewed n*=50 ties=0.5 effect=0.076 (mde): 0.960 [0.950, 0.968]
- pessimistic: randomisation power skewed n*=116 ties=0.5 effect=0.048 (mde): 0.898 [0.883, 0.911]
- pessimistic: randomisation power skewed n*=51 ties=0.8 effect=0.073 (mde): 0.957 [0.946, 0.965]
- pessimistic: randomisation power skewed n*=116 ties=0.8 effect=0.034 (mde): 0.985 [0.978, 0.990]
- pessimistic: randomisation power skewed n*=241 ties=0.8 effect=0.022 (mde): 0.924 [0.911, 0.936]
- pessimistic: randomisation power continuous n*=32 ties=0.6 effect=0.100 (fixed): 0.873 [0.857, 0.888]
- overcovers: bootstrap CI coverage continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.974 [0.965, 0.981]
- pessimistic: randomisation power skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.934 [0.921, 0.944]
- pessimistic: randomisation power skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.997 [0.993, 0.999]
- conservative: Holm FWER binary independent m=3 n=50: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary independent m=5 n=50: 0.027 [0.020, 0.035]
- conservative: Holm FWER binary independent m=10 n=50: 0.024 [0.018, 0.032]
- conservative: Holm FWER binary all-pairs m=3 n=50: 0.024 [0.018, 0.032]
- conservative: Holm FWER binary all-pairs m=6 n=50: 0.022 [0.016, 0.030]
- conservative: Holm FWER binary all-pairs m=10 n=50: 0.026 [0.020, 0.035]
- conservative: Holm FWER binary independent m=3 n=115: 0.031 [0.024, 0.040]
- conservative: Holm FWER binary independent m=10 n=115: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary all-pairs m=3 n=115: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary all-pairs m=6 n=115: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary all-pairs m=10 n=115: 0.025 [0.019, 0.034]

Wall time 194 s on 8 worker(s).
