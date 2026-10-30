seed 1; replications: H0 8000, power 3000, FWER 3000; bootstrap resamples 2000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences); CI method `auto`. Intervals are Wilson 99% over replications.

randomisation-test method `auto` (fallback `johnson`).

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |
|---|---|---|---|---|---|---|
| binary | 0 | 20 | 0.038 [0.033, 0.044] | 0.038 [0.033, 0.044] | 0.035 [0.030, 0.041] | 0.038 [0.033, 0.044] |
| binary | 0 | 50 | 0.034 [0.030, 0.040] | 0.034 [0.029, 0.040] **conservative** | 0.050 [0.044, 0.056] | 0.000 [0.000, 0.001] |
| binary | 0 | 115 | 0.045 [0.040, 0.052] | 0.045 [0.040, 0.051] | 0.043 [0.038, 0.050] | 0.000 [0.000, 0.001] |
| binary | 0 | 240 | 0.044 [0.039, 0.051] | 0.046 [0.041, 0.053] | 0.048 [0.042, 0.054] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 20 | 0.024 [0.020, 0.028] **conservative** | 0.024 [0.020, 0.028] **conservative** | 0.043 [0.038, 0.049] | 0.004 [0.002, 0.006] |
| binary | 0.5 | 50 | 0.030 [0.026, 0.036] **conservative** | 0.029 [0.024, 0.034] **conservative** | 0.045 [0.039, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 115 | 0.034 [0.030, 0.040] | 0.035 [0.030, 0.040] | 0.043 [0.038, 0.050] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 240 | 0.038 [0.033, 0.044] | 0.037 [0.032, 0.043] | 0.045 [0.039, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 20 | 0.005 [0.003, 0.007] **conservative** | 0.005 [0.003, 0.007] **conservative** | 0.046 [0.040, 0.053] | 0.214 [0.203, 0.226] |
| binary | 0.8 | 50 | 0.026 [0.022, 0.031] **conservative** | 0.026 [0.022, 0.031] **conservative** | 0.046 [0.040, 0.052] | 0.020 [0.017, 0.025] |
| binary | 0.8 | 115 | 0.029 [0.025, 0.035] **conservative** | 0.028 [0.023, 0.033] **conservative** | 0.042 [0.037, 0.048] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 240 | 0.036 [0.031, 0.042] | 0.036 [0.031, 0.042] | 0.046 [0.041, 0.053] | 0.000 [0.000, 0.001] |
| continuous | 0 | 20 | 0.050 [0.044, 0.056] | 0.043 [0.038, 0.049] | 0.047 [0.041, 0.053] | 0.062 [0.056, 0.069] |
| continuous | 0 | 50 | 0.048 [0.042, 0.054] | 0.032 [0.027, 0.037] **conservative** | 0.049 [0.043, 0.055] | 0.000 [0.000, 0.001] |
| continuous | 0 | 115 | 0.051 [0.045, 0.057] | 0.042 [0.037, 0.048] | 0.052 [0.046, 0.058] | 0.000 [0.000, 0.001] |
| continuous | 0 | 240 | 0.050 [0.044, 0.056] | 0.047 [0.041, 0.054] | 0.051 [0.045, 0.058] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 20 | 0.067 [0.060, 0.074] **anti-conservative** | 0.023 [0.019, 0.028] **conservative** | 0.090 [0.082, 0.099] | 0.390 [0.376, 0.404] |
| continuous | 0.5 | 50 | 0.050 [0.044, 0.057] | 0.030 [0.026, 0.036] **conservative** | 0.068 [0.061, 0.075] | 0.059 [0.052, 0.066] |
| continuous | 0.5 | 115 | 0.049 [0.043, 0.055] | 0.041 [0.035, 0.047] | 0.056 [0.050, 0.063] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 240 | 0.051 [0.045, 0.058] | 0.041 [0.036, 0.048] | 0.054 [0.048, 0.061] | 0.000 [0.000, 0.001] |
| continuous | 0.8 | 20 | 0.084 [0.076, 0.092] **anti-conservative** | 0.004 [0.002, 0.006] **conservative** | 0.065 [0.058, 0.073] | 0.785 [0.773, 0.797] |
| continuous | 0.8 | 50 | 0.073 [0.066, 0.081] **anti-conservative** | 0.021 [0.018, 0.026] **conservative** | 0.092 [0.084, 0.100] | 0.523 [0.508, 0.537] |
| continuous | 0.8 | 115 | 0.053 [0.047, 0.060] | 0.030 [0.026, 0.035] **conservative** | 0.062 [0.056, 0.070] | 0.151 [0.141, 0.161] |
| continuous | 0.8 | 240 | 0.045 [0.040, 0.052] | 0.034 [0.029, 0.039] **conservative** | 0.054 [0.048, 0.061] | 0.005 [0.003, 0.007] |
| skewed | 0 | 20 | 0.062 [0.055, 0.069] **anti-conservative** | 0.190 [0.179, 0.201] **anti-conservative** | 0.048 [0.042, 0.055] | 0.739 [0.726, 0.751] |
| skewed | 0 | 50 | 0.058 [0.052, 0.065] **anti-conservative** | 0.392 [0.378, 0.406] **anti-conservative** | 0.053 [0.047, 0.060] | 0.587 [0.572, 0.601] |
| skewed | 0 | 115 | 0.057 [0.050, 0.064] **anti-conservative** | 0.789 [0.777, 0.801] **anti-conservative** | 0.050 [0.044, 0.057] | 0.207 [0.195, 0.219] |
| skewed | 0 | 240 | 0.054 [0.048, 0.061] | 0.986 [0.983, 0.989] **anti-conservative** | 0.052 [0.046, 0.059] | 0.017 [0.014, 0.021] |
| skewed | 0.5 | 20 | 0.117 [0.109, 0.127] **anti-conservative** | 0.080 [0.072, 0.088] **anti-conservative** | 0.129 [0.120, 0.139] | 0.649 [0.636, 0.663] |
| skewed | 0.5 | 50 | 0.077 [0.070, 0.085] **anti-conservative** | 0.195 [0.184, 0.207] **anti-conservative** | 0.082 [0.074, 0.090] | 0.666 [0.652, 0.679] |
| skewed | 0.5 | 115 | 0.066 [0.059, 0.073] **anti-conservative** | 0.478 [0.463, 0.492] **anti-conservative** | 0.069 [0.062, 0.077] | 0.514 [0.499, 0.528] |
| skewed | 0.5 | 240 | 0.060 [0.054, 0.067] **anti-conservative** | 0.804 [0.792, 0.815] **anti-conservative** | 0.061 [0.054, 0.068] | 0.191 [0.180, 0.203] |
| skewed | 0.8 | 20 | 0.118 [0.109, 0.127] **anti-conservative** | 0.011 [0.008, 0.014] **conservative** | 0.102 [0.094, 0.111] | 0.834 [0.823, 0.845] |
| skewed | 0.8 | 50 | 0.124 [0.114, 0.133] **anti-conservative** | 0.072 [0.065, 0.080] **anti-conservative** | 0.128 [0.118, 0.137] | 0.714 [0.700, 0.726] |
| skewed | 0.8 | 115 | 0.091 [0.083, 0.100] **anti-conservative** | 0.183 [0.173, 0.195] **anti-conservative** | 0.088 [0.080, 0.096] | 0.644 [0.630, 0.658] |
| skewed | 0.8 | 240 | 0.067 [0.060, 0.075] **anti-conservative** | 0.405 [0.391, 0.420] **anti-conservative** | 0.068 [0.061, 0.076] | 0.568 [0.554, 0.582] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0 | 20 | 0.000 | 0.965 [0.959, 0.970] | 0.904 |
| h0 | binary | 0 | 50 | 0.000 | 0.951 [0.944, 0.956] | 0.577 |
| h0 | binary | 0 | 115 | 0.000 | 0.957 [0.950, 0.962] | 0.368 |
| h0 | binary | 0 | 240 | 0.000 | 0.952 [0.946, 0.958] | 0.254 |
| h0 | binary | 0.5 | 20 | 0.000 | 0.957 [0.951, 0.962] | 0.639 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.955 [0.949, 0.961] | 0.394 |
| h0 | binary | 0.5 | 115 | 0.000 | 0.957 [0.950, 0.962] | 0.259 |
| h0 | binary | 0.5 | 240 | 0.000 | 0.955 [0.949, 0.961] | 0.179 |
| h0 | binary | 0.8 | 20 | 0.000 | 0.954 [0.947, 0.960] | 0.364 |
| h0 | binary | 0.8 | 50 | 0.000 | 0.954 [0.948, 0.960] | 0.242 |
| h0 | binary | 0.8 | 115 | 0.000 | 0.958 [0.952, 0.963] | 0.161 |
| h0 | binary | 0.8 | 240 | 0.000 | 0.954 [0.947, 0.959] | 0.112 |
| h0 | continuous | 0 | 20 | 0.000 | 0.953 [0.947, 0.959] | 0.234 |
| h0 | continuous | 0 | 50 | 0.000 | 0.951 [0.945, 0.957] | 0.142 |
| h0 | continuous | 0 | 115 | 0.000 | 0.948 [0.942, 0.954] | 0.092 |
| h0 | continuous | 0 | 240 | 0.000 | 0.949 [0.942, 0.955] | 0.063 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.910 [0.901, 0.918] **undercovers** | 0.159 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.932 [0.925, 0.939] **undercovers** | 0.098 |
| h0 | continuous | 0.5 | 115 | 0.000 | 0.944 [0.937, 0.950] **undercovers** | 0.064 |
| h0 | continuous | 0.5 | 240 | 0.000 | 0.946 [0.939, 0.952] | 0.045 |
| h0 | continuous | 0.8 | 20 | 0.000 | 0.935 [0.927, 0.942] **undercovers** | 0.085 |
| h0 | continuous | 0.8 | 50 | 0.000 | 0.908 [0.900, 0.916] **undercovers** | 0.059 |
| h0 | continuous | 0.8 | 115 | 0.000 | 0.938 [0.930, 0.944] **undercovers** | 0.040 |
| h0 | continuous | 0.8 | 240 | 0.000 | 0.946 [0.939, 0.952] | 0.028 |
| h0 | skewed | 0 | 20 | 0.000 | 0.952 [0.945, 0.958] | 0.264 |
| h0 | skewed | 0 | 50 | 0.000 | 0.947 [0.940, 0.953] | 0.148 |
| h0 | skewed | 0 | 115 | 0.000 | 0.950 [0.943, 0.956] | 0.094 |
| h0 | skewed | 0 | 240 | 0.000 | 0.948 [0.941, 0.954] | 0.064 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.871 [0.861, 0.880] **undercovers** | 0.164 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.918 [0.910, 0.926] **undercovers** | 0.102 |
| h0 | skewed | 0.5 | 115 | 0.000 | 0.931 [0.923, 0.938] **undercovers** | 0.065 |
| h0 | skewed | 0.5 | 240 | 0.000 | 0.939 [0.932, 0.946] **undercovers** | 0.045 |
| h0 | skewed | 0.8 | 20 | 0.000 | 0.898 [0.889, 0.906] **undercovers** | 0.080 |
| h0 | skewed | 0.8 | 50 | 0.000 | 0.873 [0.863, 0.882] **undercovers** | 0.056 |
| h0 | skewed | 0.8 | 115 | 0.000 | 0.912 [0.904, 0.920] **undercovers** | 0.039 |
| h0 | skewed | 0.8 | 240 | 0.000 | 0.932 [0.924, 0.939] **undercovers** | 0.028 |
| mde | binary | 0 | 20 | 0.597 | 0.784 [0.764, 0.803] **undercovers** | 0.688 |
| mde | binary | 0 | 49 | 0.408 | 0.975 [0.967, 0.981] **overcovers** | 0.532 |
| mde | binary | 0 | 112 | 0.267 | 0.966 [0.956, 0.974] | 0.361 |
| mde | binary | 0 | 240 | 0.183 | 0.951 [0.940, 0.960] | 0.250 |
| mde | binary | 0.5 | 20 | 0.431 | 0.965 [0.955, 0.972] | 0.499 |
| mde | binary | 0.5 | 50 | 0.287 | 0.954 [0.943, 0.963] | 0.362 |
| mde | binary | 0.5 | 115 | 0.189 | 0.953 [0.942, 0.962] | 0.249 |
| mde | binary | 0.5 | 240 | 0.131 | 0.955 [0.945, 0.964] | 0.175 |
| mde | binary | 0.8 | 50 | 0.176 | 0.937 [0.924, 0.947] **undercovers** | 0.222 |
| mde | binary | 0.8 | 115 | 0.120 | 0.938 [0.926, 0.949] **undercovers** | 0.156 |
| mde | binary | 0.8 | 240 | 0.083 | 0.947 [0.936, 0.957] | 0.111 |
| mde | continuous | 0 | 21 | 0.157 | 0.949 [0.938, 0.958] | 0.227 |
| mde | continuous | 0 | 51 | 0.099 | 0.948 [0.937, 0.958] | 0.140 |
| mde | continuous | 0 | 115 | 0.065 | 0.944 [0.932, 0.954] | 0.092 |
| mde | continuous | 0 | 241 | 0.045 | 0.946 [0.934, 0.956] | 0.063 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.917 [0.903, 0.929] **undercovers** | 0.200 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.935 [0.923, 0.946] **undercovers** | 0.107 |
| mde | continuous | 0.5 | 116 | 0.048 | 0.942 [0.930, 0.952] | 0.067 |
| mde | continuous | 0.5 | 241 | 0.033 | 0.953 [0.942, 0.962] | 0.045 |
| mde | continuous | 0.8 | 51 | 0.073 | 0.924 [0.911, 0.936] **undercovers** | 0.097 |
| mde | continuous | 0.8 | 116 | 0.034 | 0.934 [0.921, 0.944] **undercovers** | 0.047 |
| mde | continuous | 0.8 | 241 | 0.022 | 0.948 [0.937, 0.957] | 0.030 |
| mde | skewed | 0 | 21 | 0.157 | 0.941 [0.929, 0.951] | 0.254 |
| mde | skewed | 0 | 51 | 0.099 | 0.952 [0.941, 0.961] | 0.148 |
| mde | skewed | 0 | 115 | 0.065 | 0.951 [0.940, 0.960] | 0.094 |
| mde | skewed | 0 | 241 | 0.045 | 0.946 [0.934, 0.956] | 0.064 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.892 [0.877, 0.906] **undercovers** | 0.210 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.927 [0.914, 0.939] **undercovers** | 0.115 |
| mde | skewed | 0.5 | 116 | 0.048 | 0.929 [0.916, 0.940] **undercovers** | 0.068 |
| mde | skewed | 0.5 | 241 | 0.033 | 0.943 [0.931, 0.953] | 0.046 |
| mde | skewed | 0.8 | 51 | 0.073 | 0.909 [0.895, 0.922] **undercovers** | 0.094 |
| mde | skewed | 0.8 | 116 | 0.034 | 0.904 [0.890, 0.917] **undercovers** | 0.045 |
| mde | skewed | 0.8 | 241 | 0.022 | 0.927 [0.914, 0.939] **undercovers** | 0.029 |
| fixed | binary | 0.6 | 1291 | 0.050 | 0.948 [0.937, 0.957] | 0.069 |
| fixed | binary | 0.6 | 329 | 0.100 | 0.943 [0.931, 0.953] | 0.134 |
| fixed | binary | 0.6 | 84 | 0.200 | 0.947 [0.935, 0.957] | 0.254 |
| fixed | continuous | 0.6 | 91 | 0.050 | 0.937 [0.924, 0.947] **undercovers** | 0.069 |
| fixed | continuous | 0.6 | 32 | 0.100 | 0.915 [0.901, 0.927] **undercovers** | 0.135 |
| fixed | continuous | 0.6 | 17 | 0.200 | 0.935 [0.922, 0.946] **undercovers** | 0.271 |
| fixed | skewed | 0.6 | 91 | 0.050 | 0.926 [0.912, 0.937] **undercovers** | 0.068 |
| fixed | skewed | 0.6 | 32 | 0.100 | 0.879 [0.863, 0.894] **undercovers** | 0.133 |
| fixed | skewed | 0.6 | 17 | 0.200 | 0.906 [0.892, 0.919] **undercovers** | 0.266 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0 | 0.597 | 0.802 | 20 | 0.80 | 0.804 [0.785, 0.822] | 0.804 [0.785, 0.822] | 0.785 [0.765, 0.804] |
| mde | binary | 0 | 0.408 | 0.913 | 49 | 0.80 | 0.813 [0.794, 0.830] | 0.825 [0.807, 0.842] | 0.811 [0.792, 0.829] |
| mde | binary | 0 | 0.267 | 0.964 | 112 | 0.80 | 0.796 [0.776, 0.814] | 0.811 [0.792, 0.829] | 0.808 [0.789, 0.826] |
| mde | binary | 0 | 0.183 | 0.983 | 240 | 0.80 | 0.793 [0.774, 0.812] | 0.801 [0.782, 0.819] | 0.800 [0.781, 0.818] |
| mde | binary | 0.5 | 0.431 | 0.560 | 20 | 0.80 | 0.804 [0.785, 0.822] | 0.804 [0.785, 0.822] | 0.882 [0.866, 0.896] |
| mde | binary | 0.5 | 0.287 | 0.646 | 50 | 0.80 | 0.791 [0.772, 0.810] | 0.784 [0.764, 0.803] | 0.833 [0.814, 0.849] |
| mde | binary | 0.5 | 0.189 | 0.681 | 115 | 0.80 | 0.784 [0.764, 0.802] | 0.787 [0.767, 0.805] | 0.815 [0.796, 0.832] |
| mde | binary | 0.5 | 0.131 | 0.695 | 240 | 0.80 | 0.807 [0.788, 0.825] | 0.807 [0.788, 0.825] | 0.826 [0.807, 0.843] |
| mde | binary | 0.8 | 0.176 | 0.411 | 50 | 0.80 | 0.791 [0.772, 0.810] | 0.791 [0.772, 0.810] | 0.882 [0.866, 0.896] |
| mde | binary | 0.8 | 0.120 | 0.431 | 115 | 0.80 | 0.791 [0.772, 0.810] | 0.788 [0.768, 0.806] | 0.829 [0.811, 0.846] |
| mde | binary | 0.8 | 0.083 | 0.439 | 240 | 0.80 | 0.789 [0.770, 0.808] | 0.792 [0.772, 0.810] | 0.814 [0.795, 0.832] |
| mde | continuous | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.781 [0.761, 0.799] **optimistic** | 0.510 [0.486, 0.533] | 0.777 [0.756, 0.796] |
| mde | continuous | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.786 [0.766, 0.804] | 0.600 [0.577, 0.623] | 0.789 [0.769, 0.808] |
| mde | continuous | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.779 [0.759, 0.798] **optimistic** | 0.555 [0.532, 0.578] | 0.780 [0.760, 0.799] |
| mde | continuous | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.793 [0.773, 0.811] | 0.563 [0.539, 0.586] | 0.794 [0.774, 0.812] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.881 [0.865, 0.896] **pessimistic** | 0.629 [0.606, 0.651] | 0.924 [0.910, 0.935] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.819 [0.800, 0.836] | 0.555 [0.531, 0.578] | 0.852 [0.835, 0.868] |
| mde | continuous | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.807 [0.788, 0.825] | 0.580 [0.557, 0.603] | 0.825 [0.806, 0.842] |
| mde | continuous | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.805 [0.785, 0.823] | 0.572 [0.549, 0.595] | 0.812 [0.793, 0.830] |
| mde | continuous | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.943 [0.931, 0.953] **pessimistic** | 0.773 [0.753, 0.792] | 0.974 [0.966, 0.981] |
| mde | continuous | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.870 [0.854, 0.885] **pessimistic** | 0.633 [0.610, 0.655] | 0.891 [0.875, 0.904] |
| mde | continuous | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.843 [0.825, 0.859] | 0.605 [0.582, 0.628] | 0.857 [0.840, 0.873] |
| mde | skewed | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.982 [0.974, 0.987] **pessimistic** | 0.305 [0.283, 0.327] | 0.977 [0.968, 0.983] |
| mde | skewed | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.935 [0.922, 0.945] **pessimistic** | 0.090 [0.078, 0.105] | 0.940 [0.927, 0.950] |
| mde | skewed | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.870 [0.853, 0.885] **pessimistic** | 0.060 [0.049, 0.072] | 0.898 [0.883, 0.911] |
| mde | skewed | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.830 [0.812, 0.847] | 0.411 [0.388, 0.434] | 0.873 [0.857, 0.888] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.993 [0.987, 0.996] **pessimistic** | 0.985 [0.978, 0.989] | 1.000 [0.997, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.986 [0.980, 0.991] **pessimistic** | 0.341 [0.319, 0.364] | 0.980 [0.973, 0.986] |
| mde | skewed | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.940 [0.928, 0.950] **pessimistic** | 0.081 [0.069, 0.095] | 0.935 [0.922, 0.946] |
| mde | skewed | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.873 [0.857, 0.888] **pessimistic** | 0.066 [0.055, 0.079] | 0.892 [0.877, 0.906] |
| mde | skewed | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.987 [0.980, 0.991] **pessimistic** | 0.966 [0.956, 0.974] | 0.995 [0.990, 0.997] |
| mde | skewed | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.997 [0.994, 0.999] **pessimistic** | 0.517 [0.494, 0.541] | 0.995 [0.990, 0.997] |
| mde | skewed | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.962 [0.952, 0.970] **pessimistic** | 0.131 [0.116, 0.148] | 0.949 [0.938, 0.958] |
| fixed | binary | 0.6 | 0.050 | 0.630 | 1291 | 0.80 | 0.805 [0.785, 0.823] | 0.805 [0.786, 0.823] | 0.812 [0.793, 0.830] |
| fixed | binary | 0.6 | 0.100 | 0.624 | 329 | 0.80 | 0.803 [0.784, 0.821] | 0.806 [0.786, 0.824] | 0.818 [0.799, 0.835] |
| fixed | binary | 0.6 | 0.200 | 0.600 | 84 | 0.80 | 0.808 [0.789, 0.826] | 0.804 [0.785, 0.822] | 0.839 [0.821, 0.855] |
| fixed | continuous | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.829 [0.811, 0.846] | 0.595 [0.572, 0.618] | 0.849 [0.832, 0.865] |
| fixed | continuous | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.889 [0.873, 0.903] **pessimistic** | 0.637 [0.614, 0.659] | 0.924 [0.911, 0.936] |
| fixed | continuous | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.844 [0.827, 0.861] | 0.659 [0.637, 0.681] | 0.945 [0.933, 0.954] |
| fixed | skewed | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.974 [0.966, 0.981] **pessimistic** | 0.206 [0.188, 0.226] | 0.966 [0.956, 0.974] |
| fixed | skewed | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.998 [0.995, 0.999] **pessimistic** | 0.997 [0.993, 0.999] | 1.000 [0.998, 1.000] |
| fixed | skewed | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.890 [0.874, 0.904] **pessimistic** | 0.737 [0.716, 0.757] | 0.957 [0.947, 0.966] |

MDE cells with no attainable effect (binary: even every discordant pair favouring one model is not detectable at this n; continuous: the formula's fixed point does not exist): binary n=20 ties=0.8; continuous n=20 ties=0.8; skewed n=20 ties=0.8.

### Holm family-wise error rate (all nulls true)

| kind | design | comparisons m | n | unadjusted FWER | Holm FWER |
|---|---|---|---|---|---|
| binary | independent | 3 | 50 | 0.088 [0.076, 0.102] | 0.028 [0.021, 0.036] **conservative** |
| binary | independent | 5 | 50 | 0.149 [0.133, 0.166] | 0.033 [0.026, 0.043] |
| binary | independent | 10 | 50 | 0.270 [0.250, 0.292] | 0.025 [0.019, 0.033] **conservative** |
| binary | all-pairs | 3 | 50 | 0.075 [0.063, 0.088] | 0.021 [0.015, 0.028] **conservative** |
| binary | all-pairs | 6 | 50 | 0.139 [0.124, 0.156] | 0.029 [0.022, 0.038] **conservative** |
| binary | all-pairs | 10 | 50 | 0.182 [0.165, 0.201] | 0.020 [0.015, 0.028] **conservative** |
| binary | independent | 3 | 115 | 0.107 [0.093, 0.122] | 0.036 [0.028, 0.046] |
| binary | independent | 5 | 115 | 0.173 [0.156, 0.192] | 0.037 [0.029, 0.047] |
| binary | independent | 10 | 115 | 0.314 [0.293, 0.337] | 0.034 [0.026, 0.044] |
| binary | all-pairs | 3 | 115 | 0.087 [0.075, 0.101] | 0.029 [0.022, 0.038] **conservative** |
| binary | all-pairs | 6 | 115 | 0.142 [0.126, 0.159] | 0.024 [0.018, 0.032] **conservative** |
| binary | all-pairs | 10 | 115 | 0.223 [0.204, 0.244] | 0.026 [0.020, 0.035] **conservative** |
| continuous | independent | 3 | 50 | 0.145 [0.129, 0.162] | 0.044 [0.035, 0.055] |
| continuous | independent | 5 | 50 | 0.228 [0.209, 0.248] | 0.053 [0.043, 0.065] |
| continuous | independent | 10 | 50 | 0.401 [0.378, 0.424] | 0.052 [0.043, 0.063] |
| continuous | all-pairs | 3 | 50 | 0.125 [0.111, 0.142] | 0.041 [0.033, 0.052] |
| continuous | all-pairs | 6 | 50 | 0.192 [0.174, 0.211] | 0.046 [0.037, 0.057] |
| continuous | all-pairs | 10 | 50 | 0.306 [0.285, 0.328] | 0.044 [0.036, 0.055] |
| continuous | independent | 3 | 115 | 0.133 [0.118, 0.150] | 0.044 [0.035, 0.055] |
| continuous | independent | 5 | 115 | 0.218 [0.199, 0.238] | 0.044 [0.035, 0.054] |
| continuous | independent | 10 | 115 | 0.382 [0.360, 0.405] | 0.044 [0.035, 0.055] |
| continuous | all-pairs | 3 | 115 | 0.114 [0.100, 0.130] | 0.039 [0.031, 0.049] |
| continuous | all-pairs | 6 | 115 | 0.206 [0.188, 0.226] | 0.047 [0.038, 0.058] |
| continuous | all-pairs | 10 | 115 | 0.280 [0.259, 0.302] | 0.038 [0.030, 0.048] |

### Findings under the decision rules

- anti-conservative: randomisation type-I continuous n=20 ties=0.5 (H0): 0.067 [0.060, 0.074]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.910 [0.901, 0.918]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.932 [0.925, 0.939]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.5 (H0): 0.944 [0.937, 0.950]
- anti-conservative: randomisation type-I continuous n=20 ties=0.8 (H0): 0.084 [0.076, 0.092]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.8 (H0): 0.935 [0.927, 0.942]
- anti-conservative: randomisation type-I continuous n=50 ties=0.8 (H0): 0.073 [0.066, 0.081]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.8 (H0): 0.908 [0.900, 0.916]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.8 (H0): 0.938 [0.930, 0.944]
- anti-conservative: randomisation type-I skewed n=20 ties=0 (H0): 0.062 [0.055, 0.069]
- anti-conservative: sign test type-I skewed n=20 ties=0 (H0): 0.190 [0.179, 0.201]
- anti-conservative: randomisation type-I skewed n=50 ties=0 (H0): 0.058 [0.052, 0.065]
- anti-conservative: sign test type-I skewed n=50 ties=0 (H0): 0.392 [0.378, 0.406]
- anti-conservative: randomisation type-I skewed n=115 ties=0 (H0): 0.057 [0.050, 0.064]
- anti-conservative: sign test type-I skewed n=115 ties=0 (H0): 0.789 [0.777, 0.801]
- anti-conservative: sign test type-I skewed n=240 ties=0 (H0): 0.986 [0.983, 0.989]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.117 [0.109, 0.127]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.080 [0.072, 0.088]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.871 [0.861, 0.880]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.077 [0.070, 0.085]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.195 [0.184, 0.207]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.918 [0.910, 0.926]
- anti-conservative: randomisation type-I skewed n=115 ties=0.5 (H0): 0.066 [0.059, 0.073]
- anti-conservative: sign test type-I skewed n=115 ties=0.5 (H0): 0.478 [0.463, 0.492]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.5 (H0): 0.931 [0.923, 0.938]
- anti-conservative: randomisation type-I skewed n=240 ties=0.5 (H0): 0.060 [0.054, 0.067]
- anti-conservative: sign test type-I skewed n=240 ties=0.5 (H0): 0.804 [0.792, 0.815]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.5 (H0): 0.939 [0.932, 0.946]
- anti-conservative: randomisation type-I skewed n=20 ties=0.8 (H0): 0.118 [0.109, 0.127]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.8 (H0): 0.898 [0.889, 0.906]
- anti-conservative: randomisation type-I skewed n=50 ties=0.8 (H0): 0.124 [0.114, 0.133]
- anti-conservative: sign test type-I skewed n=50 ties=0.8 (H0): 0.072 [0.065, 0.080]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.8 (H0): 0.873 [0.863, 0.882]
- anti-conservative: randomisation type-I skewed n=115 ties=0.8 (H0): 0.091 [0.083, 0.100]
- anti-conservative: sign test type-I skewed n=115 ties=0.8 (H0): 0.183 [0.173, 0.195]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.8 (H0): 0.912 [0.904, 0.920]
- anti-conservative: randomisation type-I skewed n=240 ties=0.8 (H0): 0.067 [0.060, 0.075]
- anti-conservative: sign test type-I skewed n=240 ties=0.8 (H0): 0.405 [0.391, 0.420]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.8 (H0): 0.932 [0.924, 0.939]
- undercovers: bootstrap CI coverage binary n*=20 ties=0 effect=0.597 (mde): 0.784 [0.764, 0.803]
- undercovers: bootstrap CI coverage binary n*=50 ties=0.8 effect=0.176 (mde): 0.937 [0.924, 0.947]
- undercovers: bootstrap CI coverage binary n*=115 ties=0.8 effect=0.120 (mde): 0.938 [0.926, 0.949]
- optimistic: randomisation power continuous n*=21 ties=0 effect=0.157 (mde): 0.781 [0.761, 0.799]
- optimistic: randomisation power continuous n*=115 ties=0 effect=0.065 (mde): 0.779 [0.759, 0.798]
- undercovers: bootstrap CI coverage continuous n*=21 ties=0.5 effect=0.142 (mde): 0.917 [0.903, 0.929]
- undercovers: bootstrap CI coverage continuous n*=50 ties=0.5 effect=0.076 (mde): 0.935 [0.923, 0.946]
- undercovers: bootstrap CI coverage continuous n*=51 ties=0.8 effect=0.073 (mde): 0.924 [0.911, 0.936]
- undercovers: bootstrap CI coverage continuous n*=116 ties=0.8 effect=0.034 (mde): 0.934 [0.921, 0.944]
- undercovers: bootstrap CI coverage skewed n*=21 ties=0.5 effect=0.142 (mde): 0.892 [0.877, 0.906]
- undercovers: bootstrap CI coverage skewed n*=50 ties=0.5 effect=0.076 (mde): 0.927 [0.914, 0.939]
- undercovers: bootstrap CI coverage skewed n*=116 ties=0.5 effect=0.048 (mde): 0.929 [0.916, 0.940]
- undercovers: bootstrap CI coverage skewed n*=51 ties=0.8 effect=0.073 (mde): 0.909 [0.895, 0.922]
- undercovers: bootstrap CI coverage skewed n*=116 ties=0.8 effect=0.034 (mde): 0.904 [0.890, 0.917]
- undercovers: bootstrap CI coverage skewed n*=241 ties=0.8 effect=0.022 (mde): 0.927 [0.914, 0.939]
- undercovers: bootstrap CI coverage continuous n*=91 ties=0.6 effect=0.050 (fixed): 0.937 [0.924, 0.947]
- undercovers: bootstrap CI coverage continuous n*=32 ties=0.6 effect=0.100 (fixed): 0.915 [0.901, 0.927]
- undercovers: bootstrap CI coverage continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.935 [0.922, 0.946]
- undercovers: bootstrap CI coverage skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.926 [0.912, 0.937]
- undercovers: bootstrap CI coverage skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.879 [0.863, 0.894]
- undercovers: bootstrap CI coverage skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.906 [0.892, 0.919]
- conservative: sign test type-I binary n=50 ties=0 (H0): 0.034 [0.029, 0.040]
- conservative: randomisation type-I binary n=20 ties=0.5 (H0): 0.024 [0.020, 0.028]
- conservative: sign test type-I binary n=20 ties=0.5 (H0): 0.024 [0.020, 0.028]
- conservative: randomisation type-I binary n=50 ties=0.5 (H0): 0.030 [0.026, 0.036]
- conservative: sign test type-I binary n=50 ties=0.5 (H0): 0.029 [0.024, 0.034]
- conservative: randomisation type-I binary n=20 ties=0.8 (H0): 0.005 [0.003, 0.007]
- conservative: sign test type-I binary n=20 ties=0.8 (H0): 0.005 [0.003, 0.007]
- conservative: randomisation type-I binary n=50 ties=0.8 (H0): 0.026 [0.022, 0.031]
- conservative: sign test type-I binary n=50 ties=0.8 (H0): 0.026 [0.022, 0.031]
- conservative: randomisation type-I binary n=115 ties=0.8 (H0): 0.029 [0.025, 0.035]
- conservative: sign test type-I binary n=115 ties=0.8 (H0): 0.028 [0.023, 0.033]
- conservative: sign test type-I continuous n=50 ties=0 (H0): 0.032 [0.027, 0.037]
- conservative: sign test type-I continuous n=20 ties=0.5 (H0): 0.023 [0.019, 0.028]
- conservative: sign test type-I continuous n=50 ties=0.5 (H0): 0.030 [0.026, 0.036]
- conservative: sign test type-I continuous n=20 ties=0.8 (H0): 0.004 [0.002, 0.006]
- conservative: sign test type-I continuous n=50 ties=0.8 (H0): 0.021 [0.018, 0.026]
- conservative: sign test type-I continuous n=115 ties=0.8 (H0): 0.030 [0.026, 0.035]
- conservative: sign test type-I continuous n=240 ties=0.8 (H0): 0.034 [0.029, 0.039]
- conservative: sign test type-I skewed n=20 ties=0.8 (H0): 0.011 [0.008, 0.014]
- overcovers: bootstrap CI coverage binary n*=49 ties=0 effect=0.408 (mde): 0.975 [0.967, 0.981]
- pessimistic: randomisation power continuous n*=21 ties=0.5 effect=0.142 (mde): 0.881 [0.865, 0.896]
- pessimistic: randomisation power continuous n*=51 ties=0.8 effect=0.073 (mde): 0.943 [0.931, 0.953]
- pessimistic: randomisation power continuous n*=116 ties=0.8 effect=0.034 (mde): 0.870 [0.854, 0.885]
- pessimistic: randomisation power skewed n*=21 ties=0 effect=0.157 (mde): 0.982 [0.974, 0.987]
- pessimistic: randomisation power skewed n*=51 ties=0 effect=0.099 (mde): 0.935 [0.922, 0.945]
- pessimistic: randomisation power skewed n*=115 ties=0 effect=0.065 (mde): 0.870 [0.853, 0.885]
- pessimistic: randomisation power skewed n*=21 ties=0.5 effect=0.142 (mde): 0.993 [0.987, 0.996]
- pessimistic: randomisation power skewed n*=50 ties=0.5 effect=0.076 (mde): 0.986 [0.980, 0.991]
- pessimistic: randomisation power skewed n*=116 ties=0.5 effect=0.048 (mde): 0.940 [0.928, 0.950]
- pessimistic: randomisation power skewed n*=241 ties=0.5 effect=0.033 (mde): 0.873 [0.857, 0.888]
- pessimistic: randomisation power skewed n*=51 ties=0.8 effect=0.073 (mde): 0.987 [0.980, 0.991]
- pessimistic: randomisation power skewed n*=116 ties=0.8 effect=0.034 (mde): 0.997 [0.994, 0.999]
- pessimistic: randomisation power skewed n*=241 ties=0.8 effect=0.022 (mde): 0.962 [0.952, 0.970]
- pessimistic: randomisation power continuous n*=32 ties=0.6 effect=0.100 (fixed): 0.889 [0.873, 0.903]
- pessimistic: randomisation power skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.974 [0.966, 0.981]
- pessimistic: randomisation power skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.998 [0.995, 0.999]
- pessimistic: randomisation power skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.890 [0.874, 0.904]
- conservative: Holm FWER binary independent m=3 n=50: 0.028 [0.021, 0.036]
- conservative: Holm FWER binary independent m=10 n=50: 0.025 [0.019, 0.033]
- conservative: Holm FWER binary all-pairs m=3 n=50: 0.021 [0.015, 0.028]
- conservative: Holm FWER binary all-pairs m=6 n=50: 0.029 [0.022, 0.038]
- conservative: Holm FWER binary all-pairs m=10 n=50: 0.020 [0.015, 0.028]
- conservative: Holm FWER binary all-pairs m=3 n=115: 0.029 [0.022, 0.038]
- conservative: Holm FWER binary all-pairs m=6 n=115: 0.024 [0.018, 0.032]
- conservative: Holm FWER binary all-pairs m=10 n=115: 0.026 [0.020, 0.035]

Wall time 108 s on 12 worker(s).
