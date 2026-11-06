seed 101; replications: H0 10000, power 10000, FWER 3000; bootstrap resamples 2000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences); CI method `auto`. Intervals are Wilson 99% over replications.

randomisation-test method `auto` (fallback `boott`; tie path `boott_nz_cal` above a tie share of 0.5).

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |
|---|---|---|---|---|---|---|
| binary | 0 | 20 | 0.041 [0.036, 0.046] | 0.041 [0.036, 0.046] | 0.038 [0.034, 0.044] | 0.041 [0.036, 0.046] |
| binary | 0 | 50 | 0.033 [0.028, 0.038] **conservative** | 0.033 [0.028, 0.038] **conservative** | 0.046 [0.041, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0 | 115 | 0.037 [0.033, 0.042] | 0.037 [0.033, 0.042] | 0.035 [0.031, 0.041] | 0.000 [0.000, 0.001] |
| binary | 0 | 240 | 0.043 [0.038, 0.049] | 0.045 [0.040, 0.051] | 0.047 [0.042, 0.053] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 20 | 0.022 [0.019, 0.026] **conservative** | 0.022 [0.019, 0.026] **conservative** | 0.039 [0.034, 0.044] | 0.003 [0.002, 0.004] |
| binary | 0.5 | 50 | 0.033 [0.028, 0.037] **conservative** | 0.031 [0.027, 0.036] **conservative** | 0.045 [0.040, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 115 | 0.039 [0.035, 0.045] | 0.040 [0.035, 0.046] | 0.049 [0.044, 0.055] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 240 | 0.044 [0.039, 0.050] | 0.044 [0.039, 0.049] | 0.050 [0.045, 0.056] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 20 | 0.005 [0.003, 0.007] **conservative** | 0.005 [0.003, 0.007] **conservative** | 0.047 [0.041, 0.052] | 0.215 [0.205, 0.226] |
| binary | 0.8 | 50 | 0.021 [0.018, 0.026] **conservative** | 0.021 [0.018, 0.026] **conservative** | 0.044 [0.039, 0.049] | 0.019 [0.016, 0.023] |
| binary | 0.8 | 115 | 0.034 [0.029, 0.039] **conservative** | 0.032 [0.028, 0.037] **conservative** | 0.047 [0.041, 0.052] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 240 | 0.033 [0.029, 0.038] **conservative** | 0.034 [0.030, 0.039] **conservative** | 0.042 [0.037, 0.047] | 0.000 [0.000, 0.001] |
| continuous | 0 | 20 | 0.048 [0.043, 0.054] | 0.043 [0.038, 0.049] | 0.050 [0.045, 0.056] | 0.063 [0.057, 0.070] |
| continuous | 0 | 50 | 0.050 [0.045, 0.056] | 0.035 [0.030, 0.040] **conservative** | 0.051 [0.046, 0.057] | 0.000 [0.000, 0.001] |
| continuous | 0 | 115 | 0.044 [0.039, 0.049] | 0.039 [0.035, 0.045] | 0.046 [0.041, 0.052] | 0.000 [0.000, 0.001] |
| continuous | 0 | 240 | 0.049 [0.044, 0.055] | 0.044 [0.039, 0.049] | 0.050 [0.045, 0.056] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 20 | 0.041 [0.036, 0.046] | 0.023 [0.019, 0.027] **conservative** | 0.094 [0.087, 0.102] | 0.394 [0.382, 0.407] |
| continuous | 0.5 | 50 | 0.053 [0.048, 0.060] | 0.030 [0.026, 0.035] **conservative** | 0.070 [0.063, 0.077] | 0.063 [0.057, 0.069] |
| continuous | 0.5 | 115 | 0.050 [0.045, 0.056] | 0.038 [0.033, 0.043] | 0.058 [0.053, 0.065] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 240 | 0.046 [0.041, 0.052] | 0.040 [0.035, 0.045] | 0.051 [0.046, 0.057] | 0.000 [0.000, 0.001] |
| continuous | 0.8 | 20 | 0.006 [0.004, 0.008] **conservative** | 0.005 [0.003, 0.007] **conservative** | 0.072 [0.065, 0.079] | 0.786 [0.775, 0.796] |
| continuous | 0.8 | 50 | 0.043 [0.038, 0.048] | 0.025 [0.021, 0.029] **conservative** | 0.088 [0.081, 0.095] | 0.515 [0.502, 0.528] |
| continuous | 0.8 | 115 | 0.049 [0.043, 0.055] | 0.032 [0.027, 0.036] **conservative** | 0.066 [0.060, 0.072] | 0.151 [0.142, 0.160] |
| continuous | 0.8 | 240 | 0.048 [0.043, 0.054] | 0.036 [0.032, 0.041] | 0.056 [0.050, 0.062] | 0.004 [0.003, 0.006] |
| skewed | 0 | 20 | 0.058 [0.052, 0.065] **anti-conservative** | 0.194 [0.184, 0.204] **anti-conservative** | 0.050 [0.045, 0.056] | 0.733 [0.721, 0.744] |
| skewed | 0 | 50 | 0.058 [0.052, 0.064] **anti-conservative** | 0.400 [0.387, 0.412] **anti-conservative** | 0.051 [0.046, 0.057] | 0.597 [0.584, 0.610] |
| skewed | 0 | 115 | 0.056 [0.051, 0.062] **anti-conservative** | 0.795 [0.785, 0.806] **anti-conservative** | 0.051 [0.046, 0.057] | 0.202 [0.192, 0.213] |
| skewed | 0 | 240 | 0.053 [0.047, 0.059] | 0.985 [0.982, 0.988] **anti-conservative** | 0.049 [0.044, 0.055] | 0.015 [0.013, 0.019] |
| skewed | 0.5 | 20 | 0.083 [0.076, 0.090] **anti-conservative** | 0.073 [0.067, 0.080] **anti-conservative** | 0.126 [0.117, 0.134] | 0.647 [0.634, 0.659] |
| skewed | 0.5 | 50 | 0.059 [0.054, 0.066] **anti-conservative** | 0.198 [0.188, 0.208] **anti-conservative** | 0.077 [0.070, 0.084] | 0.663 [0.651, 0.675] |
| skewed | 0.5 | 115 | 0.055 [0.049, 0.061] | 0.470 [0.457, 0.483] **anti-conservative** | 0.065 [0.059, 0.072] | 0.527 [0.514, 0.540] |
| skewed | 0.5 | 240 | 0.056 [0.050, 0.062] **anti-conservative** | 0.808 [0.798, 0.818] **anti-conservative** | 0.058 [0.053, 0.065] | 0.186 [0.177, 0.197] |
| skewed | 0.8 | 20 | 0.015 [0.013, 0.019] **conservative** | 0.012 [0.010, 0.016] **conservative** | 0.098 [0.091, 0.106] | 0.839 [0.830, 0.849] |
| skewed | 0.8 | 50 | 0.057 [0.051, 0.063] **anti-conservative** | 0.067 [0.061, 0.074] **anti-conservative** | 0.120 [0.112, 0.129] | 0.706 [0.694, 0.717] |
| skewed | 0.8 | 115 | 0.055 [0.050, 0.061] | 0.175 [0.165, 0.185] **anti-conservative** | 0.082 [0.075, 0.089] | 0.638 [0.626, 0.651] |
| skewed | 0.8 | 240 | 0.056 [0.050, 0.062] | 0.392 [0.379, 0.405] **anti-conservative** | 0.070 [0.064, 0.077] | 0.575 [0.562, 0.588] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0 | 20 | 0.000 | 0.962 [0.956, 0.966] | 0.904 |
| h0 | binary | 0 | 50 | 0.000 | 0.954 [0.949, 0.959] | 0.577 |
| h0 | binary | 0 | 115 | 0.000 | 0.965 [0.959, 0.969] | 0.368 |
| h0 | binary | 0 | 240 | 0.000 | 0.953 [0.947, 0.958] | 0.254 |
| h0 | binary | 0.5 | 20 | 0.000 | 0.961 [0.956, 0.966] | 0.639 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.955 [0.949, 0.960] | 0.394 |
| h0 | binary | 0.5 | 115 | 0.000 | 0.951 [0.945, 0.956] | 0.259 |
| h0 | binary | 0.5 | 240 | 0.000 | 0.950 [0.944, 0.955] | 0.179 |
| h0 | binary | 0.8 | 20 | 0.000 | 0.953 [0.948, 0.959] | 0.363 |
| h0 | binary | 0.8 | 50 | 0.000 | 0.956 [0.951, 0.961] | 0.241 |
| h0 | binary | 0.8 | 115 | 0.000 | 0.953 [0.948, 0.959] | 0.162 |
| h0 | binary | 0.8 | 240 | 0.000 | 0.958 [0.953, 0.963] | 0.112 |
| h0 | continuous | 0 | 20 | 0.000 | 0.950 [0.944, 0.955] | 0.234 |
| h0 | continuous | 0 | 50 | 0.000 | 0.949 [0.943, 0.954] | 0.142 |
| h0 | continuous | 0 | 115 | 0.000 | 0.954 [0.948, 0.959] | 0.092 |
| h0 | continuous | 0 | 240 | 0.000 | 0.950 [0.944, 0.955] | 0.063 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.906 [0.898, 0.913] **undercovers** | 0.159 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.930 [0.923, 0.937] **undercovers** | 0.098 |
| h0 | continuous | 0.5 | 115 | 0.000 | 0.942 [0.935, 0.947] **undercovers** | 0.064 |
| h0 | continuous | 0.5 | 240 | 0.000 | 0.949 [0.943, 0.954] | 0.045 |
| h0 | continuous | 0.8 | 20 | 0.000 | 0.928 [0.921, 0.935] **undercovers** | 0.085 |
| h0 | continuous | 0.8 | 50 | 0.000 | 0.912 [0.905, 0.919] **undercovers** | 0.059 |
| h0 | continuous | 0.8 | 115 | 0.000 | 0.934 [0.928, 0.940] **undercovers** | 0.040 |
| h0 | continuous | 0.8 | 240 | 0.000 | 0.944 [0.938, 0.950] | 0.028 |
| h0 | skewed | 0 | 20 | 0.000 | 0.950 [0.944, 0.955] | 0.266 |
| h0 | skewed | 0 | 50 | 0.000 | 0.949 [0.943, 0.954] | 0.149 |
| h0 | skewed | 0 | 115 | 0.000 | 0.949 [0.943, 0.954] | 0.094 |
| h0 | skewed | 0 | 240 | 0.000 | 0.951 [0.945, 0.956] | 0.064 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.874 [0.866, 0.883] **undercovers** | 0.165 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.923 [0.916, 0.930] **undercovers** | 0.101 |
| h0 | skewed | 0.5 | 115 | 0.000 | 0.935 [0.928, 0.941] **undercovers** | 0.065 |
| h0 | skewed | 0.5 | 240 | 0.000 | 0.942 [0.935, 0.947] **undercovers** | 0.045 |
| h0 | skewed | 0.8 | 20 | 0.000 | 0.902 [0.894, 0.909] **undercovers** | 0.078 |
| h0 | skewed | 0.8 | 50 | 0.000 | 0.880 [0.871, 0.888] **undercovers** | 0.056 |
| h0 | skewed | 0.8 | 115 | 0.000 | 0.918 [0.911, 0.925] **undercovers** | 0.039 |
| h0 | skewed | 0.8 | 240 | 0.000 | 0.930 [0.923, 0.936] **undercovers** | 0.028 |
| mde | binary | 0 | 20 | 0.597 | 0.789 [0.778, 0.799] **undercovers** | 0.694 |
| mde | binary | 0 | 49 | 0.408 | 0.970 [0.966, 0.974] **overcovers** | 0.533 |
| mde | binary | 0 | 112 | 0.267 | 0.961 [0.956, 0.966] | 0.361 |
| mde | binary | 0 | 240 | 0.183 | 0.955 [0.950, 0.960] | 0.250 |
| mde | binary | 0.5 | 20 | 0.431 | 0.966 [0.961, 0.971] **overcovers** | 0.500 |
| mde | binary | 0.5 | 50 | 0.287 | 0.952 [0.946, 0.957] | 0.360 |
| mde | binary | 0.5 | 115 | 0.189 | 0.952 [0.946, 0.957] | 0.249 |
| mde | binary | 0.5 | 240 | 0.131 | 0.949 [0.943, 0.954] | 0.176 |
| mde | binary | 0.8 | 50 | 0.176 | 0.941 [0.935, 0.947] **undercovers** | 0.222 |
| mde | binary | 0.8 | 115 | 0.120 | 0.944 [0.938, 0.950] **undercovers** | 0.155 |
| mde | binary | 0.8 | 240 | 0.083 | 0.947 [0.941, 0.952] | 0.110 |
| mde | continuous | 0 | 21 | 0.157 | 0.948 [0.942, 0.954] | 0.227 |
| mde | continuous | 0 | 51 | 0.099 | 0.951 [0.945, 0.956] | 0.140 |
| mde | continuous | 0 | 115 | 0.065 | 0.951 [0.945, 0.956] | 0.092 |
| mde | continuous | 0 | 241 | 0.045 | 0.952 [0.946, 0.957] | 0.063 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.920 [0.913, 0.927] **undercovers** | 0.200 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.938 [0.931, 0.944] **undercovers** | 0.108 |
| mde | continuous | 0.5 | 116 | 0.048 | 0.942 [0.936, 0.948] **undercovers** | 0.066 |
| mde | continuous | 0.5 | 241 | 0.033 | 0.943 [0.937, 0.948] **undercovers** | 0.045 |
| mde | continuous | 0.8 | 51 | 0.073 | 0.925 [0.918, 0.932] **undercovers** | 0.097 |
| mde | continuous | 0.8 | 116 | 0.034 | 0.937 [0.930, 0.943] **undercovers** | 0.047 |
| mde | continuous | 0.8 | 241 | 0.022 | 0.940 [0.934, 0.946] **undercovers** | 0.030 |
| mde | skewed | 0 | 21 | 0.157 | 0.944 [0.938, 0.950] **undercovers** | 0.254 |
| mde | skewed | 0 | 51 | 0.099 | 0.946 [0.940, 0.952] | 0.147 |
| mde | skewed | 0 | 115 | 0.065 | 0.951 [0.945, 0.956] | 0.094 |
| mde | skewed | 0 | 241 | 0.045 | 0.948 [0.942, 0.953] | 0.064 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.900 [0.892, 0.908] **undercovers** | 0.210 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.918 [0.911, 0.925] **undercovers** | 0.114 |
| mde | skewed | 0.5 | 116 | 0.048 | 0.934 [0.927, 0.940] **undercovers** | 0.068 |
| mde | skewed | 0.5 | 241 | 0.033 | 0.937 [0.930, 0.943] **undercovers** | 0.046 |
| mde | skewed | 0.8 | 51 | 0.073 | 0.908 [0.900, 0.915] **undercovers** | 0.095 |
| mde | skewed | 0.8 | 116 | 0.034 | 0.911 [0.904, 0.918] **undercovers** | 0.045 |
| mde | skewed | 0.8 | 241 | 0.022 | 0.925 [0.918, 0.932] **undercovers** | 0.029 |
| fixed | binary | 0.6 | 1291 | 0.050 | 0.950 [0.944, 0.955] | 0.069 |
| fixed | binary | 0.6 | 329 | 0.100 | 0.948 [0.942, 0.954] | 0.134 |
| fixed | binary | 0.6 | 84 | 0.200 | 0.946 [0.940, 0.952] | 0.254 |
| fixed | continuous | 0.6 | 91 | 0.050 | 0.938 [0.931, 0.944] **undercovers** | 0.069 |
| fixed | continuous | 0.6 | 32 | 0.100 | 0.926 [0.919, 0.932] **undercovers** | 0.135 |
| fixed | continuous | 0.6 | 17 | 0.200 | 0.925 [0.918, 0.932] **undercovers** | 0.271 |
| fixed | skewed | 0.6 | 91 | 0.050 | 0.924 [0.917, 0.931] **undercovers** | 0.067 |
| fixed | skewed | 0.6 | 32 | 0.100 | 0.894 [0.886, 0.902] **undercovers** | 0.135 |
| fixed | skewed | 0.6 | 17 | 0.200 | 0.911 [0.903, 0.918] **undercovers** | 0.268 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0 | 0.597 | 0.802 | 20 | 0.80 | 0.803 [0.793, 0.813] | 0.803 [0.793, 0.813] | 0.784 [0.773, 0.794] |
| mde | binary | 0 | 0.408 | 0.913 | 49 | 0.80 | 0.809 [0.798, 0.819] | 0.821 [0.810, 0.830] | 0.806 [0.796, 0.816] |
| mde | binary | 0 | 0.267 | 0.964 | 112 | 0.80 | 0.789 [0.778, 0.799] **optimistic** | 0.802 [0.792, 0.812] | 0.800 [0.789, 0.810] |
| mde | binary | 0 | 0.183 | 0.983 | 240 | 0.80 | 0.803 [0.793, 0.813] | 0.809 [0.799, 0.819] | 0.811 [0.801, 0.821] |
| mde | binary | 0.5 | 0.431 | 0.560 | 20 | 0.80 | 0.800 [0.789, 0.810] | 0.800 [0.789, 0.810] | 0.877 [0.868, 0.885] |
| mde | binary | 0.5 | 0.287 | 0.646 | 50 | 0.80 | 0.805 [0.794, 0.815] | 0.801 [0.790, 0.811] | 0.847 [0.838, 0.856] |
| mde | binary | 0.5 | 0.189 | 0.681 | 115 | 0.80 | 0.802 [0.791, 0.812] | 0.804 [0.794, 0.814] | 0.827 [0.817, 0.837] |
| mde | binary | 0.5 | 0.131 | 0.695 | 240 | 0.80 | 0.803 [0.793, 0.813] | 0.803 [0.792, 0.813] | 0.822 [0.812, 0.832] |
| mde | binary | 0.8 | 0.176 | 0.411 | 50 | 0.80 | 0.800 [0.789, 0.810] | 0.800 [0.789, 0.810] | 0.888 [0.879, 0.896] |
| mde | binary | 0.8 | 0.120 | 0.431 | 115 | 0.80 | 0.806 [0.796, 0.816] | 0.802 [0.791, 0.812] | 0.846 [0.837, 0.855] |
| mde | binary | 0.8 | 0.083 | 0.439 | 240 | 0.80 | 0.799 [0.788, 0.809] | 0.801 [0.790, 0.811] | 0.827 [0.817, 0.837] |
| mde | continuous | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.775 [0.764, 0.786] **optimistic** | 0.497 [0.484, 0.509] | 0.768 [0.757, 0.779] |
| mde | continuous | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.800 [0.790, 0.811] | 0.609 [0.596, 0.621] | 0.799 [0.789, 0.810] |
| mde | continuous | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.788 [0.777, 0.798] **optimistic** | 0.561 [0.549, 0.574] | 0.788 [0.777, 0.798] |
| mde | continuous | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.799 [0.788, 0.809] | 0.569 [0.556, 0.582] | 0.799 [0.789, 0.809] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.816 [0.806, 0.826] | 0.635 [0.623, 0.647] | 0.932 [0.926, 0.939] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.818 [0.808, 0.828] | 0.567 [0.554, 0.580] | 0.856 [0.847, 0.865] |
| mde | continuous | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.816 [0.806, 0.826] | 0.581 [0.568, 0.593] | 0.832 [0.822, 0.841] |
| mde | continuous | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.809 [0.799, 0.819] | 0.592 [0.579, 0.605] | 0.821 [0.811, 0.830] |
| mde | continuous | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.870 [0.861, 0.878] **pessimistic** | 0.782 [0.771, 0.792] | 0.975 [0.971, 0.979] |
| mde | continuous | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.856 [0.847, 0.865] | 0.639 [0.627, 0.652] | 0.889 [0.880, 0.897] |
| mde | continuous | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.827 [0.817, 0.837] | 0.603 [0.591, 0.616] | 0.842 [0.832, 0.851] |
| mde | skewed | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.729 [0.718, 0.741] **optimistic** | 0.318 [0.306, 0.330] | 0.979 [0.975, 0.982] |
| mde | skewed | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.816 [0.806, 0.826] | 0.104 [0.096, 0.112] | 0.936 [0.929, 0.942] |
| mde | skewed | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.829 [0.819, 0.838] | 0.057 [0.051, 0.063] | 0.897 [0.889, 0.905] |
| mde | skewed | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.829 [0.819, 0.838] | 0.418 [0.405, 0.430] | 0.870 [0.861, 0.878] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.707 [0.695, 0.718] **optimistic** | 0.985 [0.982, 0.988] | 0.999 [0.998, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.732 [0.720, 0.743] **optimistic** | 0.351 [0.338, 0.363] | 0.983 [0.979, 0.986] |
| mde | skewed | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.806 [0.796, 0.816] | 0.075 [0.069, 0.082] | 0.931 [0.924, 0.937] |
| mde | skewed | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.834 [0.824, 0.843] | 0.069 [0.062, 0.075] | 0.894 [0.886, 0.901] |
| mde | skewed | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.714 [0.702, 0.725] **optimistic** | 0.960 [0.955, 0.965] | 0.996 [0.994, 0.997] |
| mde | skewed | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.744 [0.733, 0.755] **optimistic** | 0.533 [0.520, 0.546] | 0.993 [0.990, 0.995] |
| mde | skewed | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.780 [0.769, 0.791] **optimistic** | 0.126 [0.117, 0.134] | 0.943 [0.936, 0.948] |
| fixed | binary | 0.6 | 0.050 | 0.630 | 1291 | 0.80 | 0.794 [0.783, 0.804] | 0.792 [0.782, 0.803] | 0.803 [0.792, 0.813] |
| fixed | binary | 0.6 | 0.100 | 0.624 | 329 | 0.80 | 0.796 [0.786, 0.807] | 0.796 [0.785, 0.806] | 0.812 [0.802, 0.822] |
| fixed | binary | 0.6 | 0.200 | 0.600 | 84 | 0.80 | 0.811 [0.801, 0.821] | 0.805 [0.795, 0.815] | 0.845 [0.835, 0.854] |
| fixed | continuous | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.829 [0.819, 0.838] | 0.590 [0.577, 0.603] | 0.848 [0.838, 0.857] |
| fixed | continuous | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.848 [0.838, 0.857] | 0.639 [0.627, 0.652] | 0.931 [0.925, 0.938] |
| fixed | continuous | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.662 [0.650, 0.674] **optimistic** | 0.649 [0.637, 0.661] | 0.940 [0.934, 0.946] |
| fixed | skewed | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.760 [0.749, 0.771] **optimistic** | 0.199 [0.189, 0.209] | 0.964 [0.959, 0.968] |
| fixed | skewed | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.702 [0.690, 0.714] **optimistic** | 0.998 [0.996, 0.999] | 1.000 [0.999, 1.000] |
| fixed | skewed | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.565 [0.552, 0.578] **optimistic** | 0.737 [0.725, 0.748] | 0.957 [0.951, 0.962] |

MDE cells with no attainable effect (binary: even every discordant pair favouring one model is not detectable at this n; continuous: the formula's fixed point does not exist): binary n=20 ties=0.8; continuous n=20 ties=0.8; skewed n=20 ties=0.8.

### Holm family-wise error rate (all nulls true)

| kind | design | comparisons m | n | unadjusted FWER | Holm FWER |
|---|---|---|---|---|---|
| binary | independent | 3 | 50 | 0.082 [0.070, 0.095] | 0.027 [0.020, 0.036] **conservative** |
| binary | independent | 5 | 50 | 0.158 [0.142, 0.176] | 0.030 [0.023, 0.039] **conservative** |
| binary | independent | 10 | 50 | 0.280 [0.259, 0.302] | 0.028 [0.022, 0.037] **conservative** |
| binary | all-pairs | 3 | 50 | 0.072 [0.061, 0.085] | 0.019 [0.014, 0.027] **conservative** |
| binary | all-pairs | 6 | 50 | 0.141 [0.125, 0.158] | 0.023 [0.017, 0.032] **conservative** |
| binary | all-pairs | 10 | 50 | 0.197 [0.179, 0.216] | 0.019 [0.014, 0.027] **conservative** |
| binary | independent | 3 | 115 | 0.104 [0.091, 0.120] | 0.034 [0.026, 0.044] |
| binary | independent | 5 | 115 | 0.165 [0.148, 0.183] | 0.028 [0.022, 0.037] **conservative** |
| binary | independent | 10 | 115 | 0.308 [0.287, 0.330] | 0.033 [0.026, 0.043] |
| binary | all-pairs | 3 | 115 | 0.084 [0.072, 0.098] | 0.028 [0.022, 0.037] **conservative** |
| binary | all-pairs | 6 | 115 | 0.150 [0.134, 0.167] | 0.026 [0.019, 0.034] **conservative** |
| binary | all-pairs | 10 | 115 | 0.225 [0.206, 0.245] | 0.027 [0.020, 0.036] **conservative** |
| continuous | independent | 3 | 50 | 0.138 [0.123, 0.155] | 0.046 [0.037, 0.057] |
| continuous | independent | 5 | 50 | 0.211 [0.192, 0.230] | 0.045 [0.036, 0.055] |
| continuous | independent | 10 | 50 | 0.404 [0.381, 0.427] | 0.053 [0.043, 0.065] |
| continuous | all-pairs | 3 | 50 | 0.123 [0.109, 0.140] | 0.043 [0.034, 0.054] |
| continuous | all-pairs | 6 | 50 | 0.209 [0.190, 0.228] | 0.043 [0.034, 0.054] |
| continuous | all-pairs | 10 | 50 | 0.303 [0.282, 0.325] | 0.040 [0.032, 0.051] |
| continuous | independent | 3 | 115 | 0.144 [0.128, 0.161] | 0.048 [0.039, 0.059] |
| continuous | independent | 5 | 115 | 0.230 [0.210, 0.250] | 0.050 [0.040, 0.061] |
| continuous | independent | 10 | 115 | 0.398 [0.375, 0.421] | 0.050 [0.041, 0.062] |
| continuous | all-pairs | 3 | 115 | 0.122 [0.107, 0.138] | 0.044 [0.036, 0.055] |
| continuous | all-pairs | 6 | 115 | 0.195 [0.177, 0.214] | 0.043 [0.035, 0.054] |
| continuous | all-pairs | 10 | 115 | 0.279 [0.259, 0.301] | 0.037 [0.029, 0.047] |

### Findings under the decision rules

- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.906 [0.898, 0.913]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.930 [0.923, 0.937]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.5 (H0): 0.942 [0.935, 0.947]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.8 (H0): 0.928 [0.921, 0.935]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.8 (H0): 0.912 [0.905, 0.919]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.8 (H0): 0.934 [0.928, 0.940]
- anti-conservative: randomisation type-I skewed n=20 ties=0 (H0): 0.058 [0.052, 0.065]
- anti-conservative: sign test type-I skewed n=20 ties=0 (H0): 0.194 [0.184, 0.204]
- anti-conservative: randomisation type-I skewed n=50 ties=0 (H0): 0.058 [0.052, 0.064]
- anti-conservative: sign test type-I skewed n=50 ties=0 (H0): 0.400 [0.387, 0.412]
- anti-conservative: randomisation type-I skewed n=115 ties=0 (H0): 0.056 [0.051, 0.062]
- anti-conservative: sign test type-I skewed n=115 ties=0 (H0): 0.795 [0.785, 0.806]
- anti-conservative: sign test type-I skewed n=240 ties=0 (H0): 0.985 [0.982, 0.988]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.083 [0.076, 0.090]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.073 [0.067, 0.080]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.874 [0.866, 0.883]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.059 [0.054, 0.066]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.198 [0.188, 0.208]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.923 [0.916, 0.930]
- anti-conservative: sign test type-I skewed n=115 ties=0.5 (H0): 0.470 [0.457, 0.483]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.5 (H0): 0.935 [0.928, 0.941]
- anti-conservative: randomisation type-I skewed n=240 ties=0.5 (H0): 0.056 [0.050, 0.062]
- anti-conservative: sign test type-I skewed n=240 ties=0.5 (H0): 0.808 [0.798, 0.818]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.5 (H0): 0.942 [0.935, 0.947]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.8 (H0): 0.902 [0.894, 0.909]
- anti-conservative: randomisation type-I skewed n=50 ties=0.8 (H0): 0.057 [0.051, 0.063]
- anti-conservative: sign test type-I skewed n=50 ties=0.8 (H0): 0.067 [0.061, 0.074]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.8 (H0): 0.880 [0.871, 0.888]
- anti-conservative: sign test type-I skewed n=115 ties=0.8 (H0): 0.175 [0.165, 0.185]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.8 (H0): 0.918 [0.911, 0.925]
- anti-conservative: sign test type-I skewed n=240 ties=0.8 (H0): 0.392 [0.379, 0.405]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.8 (H0): 0.930 [0.923, 0.936]
- undercovers: bootstrap CI coverage binary n*=20 ties=0 effect=0.597 (mde): 0.789 [0.778, 0.799]
- optimistic: randomisation power binary n*=112 ties=0 effect=0.267 (mde): 0.789 [0.778, 0.799]
- undercovers: bootstrap CI coverage binary n*=50 ties=0.8 effect=0.176 (mde): 0.941 [0.935, 0.947]
- undercovers: bootstrap CI coverage binary n*=115 ties=0.8 effect=0.120 (mde): 0.944 [0.938, 0.950]
- optimistic: randomisation power continuous n*=21 ties=0 effect=0.157 (mde): 0.775 [0.764, 0.786]
- optimistic: randomisation power continuous n*=115 ties=0 effect=0.065 (mde): 0.788 [0.777, 0.798]
- undercovers: bootstrap CI coverage continuous n*=21 ties=0.5 effect=0.142 (mde): 0.920 [0.913, 0.927]
- undercovers: bootstrap CI coverage continuous n*=50 ties=0.5 effect=0.076 (mde): 0.938 [0.931, 0.944]
- undercovers: bootstrap CI coverage continuous n*=116 ties=0.5 effect=0.048 (mde): 0.942 [0.936, 0.948]
- undercovers: bootstrap CI coverage continuous n*=241 ties=0.5 effect=0.033 (mde): 0.943 [0.937, 0.948]
- undercovers: bootstrap CI coverage continuous n*=51 ties=0.8 effect=0.073 (mde): 0.925 [0.918, 0.932]
- undercovers: bootstrap CI coverage continuous n*=116 ties=0.8 effect=0.034 (mde): 0.937 [0.930, 0.943]
- undercovers: bootstrap CI coverage continuous n*=241 ties=0.8 effect=0.022 (mde): 0.940 [0.934, 0.946]
- optimistic: randomisation power skewed n*=21 ties=0 effect=0.157 (mde): 0.729 [0.718, 0.741]
- undercovers: bootstrap CI coverage skewed n*=21 ties=0 effect=0.157 (mde): 0.944 [0.938, 0.950]
- optimistic: randomisation power skewed n*=21 ties=0.5 effect=0.142 (mde): 0.707 [0.695, 0.718]
- undercovers: bootstrap CI coverage skewed n*=21 ties=0.5 effect=0.142 (mde): 0.900 [0.892, 0.908]
- optimistic: randomisation power skewed n*=50 ties=0.5 effect=0.076 (mde): 0.732 [0.720, 0.743]
- undercovers: bootstrap CI coverage skewed n*=50 ties=0.5 effect=0.076 (mde): 0.918 [0.911, 0.925]
- undercovers: bootstrap CI coverage skewed n*=116 ties=0.5 effect=0.048 (mde): 0.934 [0.927, 0.940]
- undercovers: bootstrap CI coverage skewed n*=241 ties=0.5 effect=0.033 (mde): 0.937 [0.930, 0.943]
- optimistic: randomisation power skewed n*=51 ties=0.8 effect=0.073 (mde): 0.714 [0.702, 0.725]
- undercovers: bootstrap CI coverage skewed n*=51 ties=0.8 effect=0.073 (mde): 0.908 [0.900, 0.915]
- optimistic: randomisation power skewed n*=116 ties=0.8 effect=0.034 (mde): 0.744 [0.733, 0.755]
- undercovers: bootstrap CI coverage skewed n*=116 ties=0.8 effect=0.034 (mde): 0.911 [0.904, 0.918]
- optimistic: randomisation power skewed n*=241 ties=0.8 effect=0.022 (mde): 0.780 [0.769, 0.791]
- undercovers: bootstrap CI coverage skewed n*=241 ties=0.8 effect=0.022 (mde): 0.925 [0.918, 0.932]
- undercovers: bootstrap CI coverage continuous n*=91 ties=0.6 effect=0.050 (fixed): 0.938 [0.931, 0.944]
- undercovers: bootstrap CI coverage continuous n*=32 ties=0.6 effect=0.100 (fixed): 0.926 [0.919, 0.932]
- optimistic: randomisation power continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.662 [0.650, 0.674]
- undercovers: bootstrap CI coverage continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.925 [0.918, 0.932]
- optimistic: randomisation power skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.760 [0.749, 0.771]
- undercovers: bootstrap CI coverage skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.924 [0.917, 0.931]
- optimistic: randomisation power skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.702 [0.690, 0.714]
- undercovers: bootstrap CI coverage skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.894 [0.886, 0.902]
- optimistic: randomisation power skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.565 [0.552, 0.578]
- undercovers: bootstrap CI coverage skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.911 [0.903, 0.918]
- conservative: randomisation type-I binary n=50 ties=0 (H0): 0.033 [0.028, 0.038]
- conservative: sign test type-I binary n=50 ties=0 (H0): 0.033 [0.028, 0.038]
- conservative: randomisation type-I binary n=20 ties=0.5 (H0): 0.022 [0.019, 0.026]
- conservative: sign test type-I binary n=20 ties=0.5 (H0): 0.022 [0.019, 0.026]
- conservative: randomisation type-I binary n=50 ties=0.5 (H0): 0.033 [0.028, 0.037]
- conservative: sign test type-I binary n=50 ties=0.5 (H0): 0.031 [0.027, 0.036]
- conservative: randomisation type-I binary n=20 ties=0.8 (H0): 0.005 [0.003, 0.007]
- conservative: sign test type-I binary n=20 ties=0.8 (H0): 0.005 [0.003, 0.007]
- conservative: randomisation type-I binary n=50 ties=0.8 (H0): 0.021 [0.018, 0.026]
- conservative: sign test type-I binary n=50 ties=0.8 (H0): 0.021 [0.018, 0.026]
- conservative: randomisation type-I binary n=115 ties=0.8 (H0): 0.034 [0.029, 0.039]
- conservative: sign test type-I binary n=115 ties=0.8 (H0): 0.032 [0.028, 0.037]
- conservative: randomisation type-I binary n=240 ties=0.8 (H0): 0.033 [0.029, 0.038]
- conservative: sign test type-I binary n=240 ties=0.8 (H0): 0.034 [0.030, 0.039]
- conservative: sign test type-I continuous n=50 ties=0 (H0): 0.035 [0.030, 0.040]
- conservative: sign test type-I continuous n=20 ties=0.5 (H0): 0.023 [0.019, 0.027]
- conservative: sign test type-I continuous n=50 ties=0.5 (H0): 0.030 [0.026, 0.035]
- conservative: randomisation type-I continuous n=20 ties=0.8 (H0): 0.006 [0.004, 0.008]
- conservative: sign test type-I continuous n=20 ties=0.8 (H0): 0.005 [0.003, 0.007]
- conservative: sign test type-I continuous n=50 ties=0.8 (H0): 0.025 [0.021, 0.029]
- conservative: sign test type-I continuous n=115 ties=0.8 (H0): 0.032 [0.027, 0.036]
- conservative: randomisation type-I skewed n=20 ties=0.8 (H0): 0.015 [0.013, 0.019]
- conservative: sign test type-I skewed n=20 ties=0.8 (H0): 0.012 [0.010, 0.016]
- overcovers: bootstrap CI coverage binary n*=49 ties=0 effect=0.408 (mde): 0.970 [0.966, 0.974]
- overcovers: bootstrap CI coverage binary n*=20 ties=0.5 effect=0.431 (mde): 0.966 [0.961, 0.971]
- pessimistic: randomisation power continuous n*=51 ties=0.8 effect=0.073 (mde): 0.870 [0.861, 0.878]
- conservative: Holm FWER binary independent m=3 n=50: 0.027 [0.020, 0.036]
- conservative: Holm FWER binary independent m=5 n=50: 0.030 [0.023, 0.039]
- conservative: Holm FWER binary independent m=10 n=50: 0.028 [0.022, 0.037]
- conservative: Holm FWER binary all-pairs m=3 n=50: 0.019 [0.014, 0.027]
- conservative: Holm FWER binary all-pairs m=6 n=50: 0.023 [0.017, 0.032]
- conservative: Holm FWER binary all-pairs m=10 n=50: 0.019 [0.014, 0.027]
- conservative: Holm FWER binary independent m=5 n=115: 0.028 [0.022, 0.037]
- conservative: Holm FWER binary all-pairs m=3 n=115: 0.028 [0.022, 0.037]
- conservative: Holm FWER binary all-pairs m=6 n=115: 0.026 [0.019, 0.034]
- conservative: Holm FWER binary all-pairs m=10 n=115: 0.027 [0.020, 0.036]

Wall time 842 s on 10 worker(s).
