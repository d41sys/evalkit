seed 1; replications: H0 8000, power 3000, FWER 3000; bootstrap resamples 2000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences); CI method `studentized`. Intervals are Wilson 99% over replications.

### Type-I error at alpha = 0.05 (H0: true difference 0)

| kind | tie rate | n | randomisation | sign test | CI excludes 0 | warn rate |
|---|---|---|---|---|---|---|
| binary | 0 | 20 | 0.038 [0.033, 0.044] | 0.038 [0.033, 0.044] | 0.035 [0.030, 0.041] | 0.038 [0.033, 0.044] |
| binary | 0 | 50 | 0.034 [0.030, 0.040] | 0.034 [0.029, 0.040] **conservative** | 0.050 [0.044, 0.056] | 0.000 [0.000, 0.001] |
| binary | 0 | 115 | 0.045 [0.040, 0.052] | 0.045 [0.040, 0.051] | 0.043 [0.038, 0.050] | 0.000 [0.000, 0.001] |
| binary | 0 | 240 | 0.044 [0.039, 0.051] | 0.046 [0.041, 0.053] | 0.048 [0.042, 0.054] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 20 | 0.024 [0.020, 0.028] **conservative** | 0.024 [0.020, 0.028] **conservative** | 0.046 [0.041, 0.053] | 0.004 [0.002, 0.006] |
| binary | 0.5 | 50 | 0.030 [0.026, 0.036] **conservative** | 0.029 [0.024, 0.034] **conservative** | 0.044 [0.039, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 115 | 0.034 [0.030, 0.040] | 0.035 [0.030, 0.040] | 0.044 [0.039, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.5 | 240 | 0.038 [0.033, 0.044] | 0.037 [0.032, 0.043] | 0.045 [0.040, 0.051] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 20 | 0.005 [0.003, 0.007] **conservative** | 0.005 [0.003, 0.007] **conservative** | 0.096 [0.088, 0.105] | 0.214 [0.203, 0.226] |
| binary | 0.8 | 50 | 0.026 [0.022, 0.031] **conservative** | 0.026 [0.022, 0.031] **conservative** | 0.071 [0.064, 0.079] | 0.020 [0.017, 0.025] |
| binary | 0.8 | 115 | 0.029 [0.025, 0.035] **conservative** | 0.028 [0.023, 0.033] **conservative** | 0.057 [0.051, 0.064] | 0.000 [0.000, 0.001] |
| binary | 0.8 | 240 | 0.036 [0.031, 0.042] | 0.036 [0.031, 0.042] | 0.055 [0.049, 0.062] | 0.000 [0.000, 0.001] |
| continuous | 0 | 20 | 0.049 [0.043, 0.055] | 0.043 [0.038, 0.049] | 0.047 [0.041, 0.053] | 0.062 [0.056, 0.069] |
| continuous | 0 | 50 | 0.048 [0.042, 0.054] | 0.032 [0.027, 0.037] **conservative** | 0.049 [0.043, 0.055] | 0.000 [0.000, 0.001] |
| continuous | 0 | 115 | 0.051 [0.045, 0.057] | 0.042 [0.037, 0.048] | 0.052 [0.046, 0.058] | 0.000 [0.000, 0.001] |
| continuous | 0 | 240 | 0.050 [0.044, 0.056] | 0.047 [0.041, 0.054] | 0.051 [0.045, 0.058] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 20 | 0.048 [0.042, 0.055] | 0.023 [0.019, 0.028] **conservative** | 0.094 [0.086, 0.103] | 0.390 [0.376, 0.404] |
| continuous | 0.5 | 50 | 0.048 [0.043, 0.055] | 0.030 [0.026, 0.036] **conservative** | 0.071 [0.064, 0.079] | 0.059 [0.052, 0.066] |
| continuous | 0.5 | 115 | 0.049 [0.043, 0.055] | 0.041 [0.035, 0.047] | 0.059 [0.052, 0.066] | 0.000 [0.000, 0.001] |
| continuous | 0.5 | 240 | 0.051 [0.045, 0.058] | 0.041 [0.036, 0.048] | 0.056 [0.050, 0.063] | 0.000 [0.000, 0.001] |
| continuous | 0.8 | 20 | 0.007 [0.005, 0.010] **conservative** | 0.004 [0.002, 0.006] **conservative** | 0.118 [0.109, 0.128] | 0.785 [0.773, 0.797] |
| continuous | 0.8 | 50 | 0.047 [0.041, 0.053] | 0.021 [0.018, 0.026] **conservative** | 0.121 [0.112, 0.131] | 0.523 [0.508, 0.537] |
| continuous | 0.8 | 115 | 0.051 [0.045, 0.058] | 0.030 [0.026, 0.035] **conservative** | 0.082 [0.074, 0.090] | 0.151 [0.141, 0.161] |
| continuous | 0.8 | 240 | 0.045 [0.040, 0.052] | 0.034 [0.029, 0.039] **conservative** | 0.062 [0.055, 0.069] | 0.005 [0.003, 0.007] |
| skewed | 0 | 20 | 0.078 [0.070, 0.086] **anti-conservative** | 0.190 [0.179, 0.201] **anti-conservative** | 0.048 [0.042, 0.055] | 0.739 [0.726, 0.751] |
| skewed | 0 | 50 | 0.065 [0.058, 0.072] **anti-conservative** | 0.392 [0.378, 0.406] **anti-conservative** | 0.053 [0.047, 0.060] | 0.587 [0.572, 0.601] |
| skewed | 0 | 115 | 0.057 [0.051, 0.064] **anti-conservative** | 0.789 [0.777, 0.801] **anti-conservative** | 0.050 [0.044, 0.057] | 0.207 [0.195, 0.219] |
| skewed | 0 | 240 | 0.055 [0.048, 0.062] | 0.986 [0.983, 0.989] **anti-conservative** | 0.052 [0.046, 0.059] | 0.017 [0.014, 0.021] |
| skewed | 0.5 | 20 | 0.094 [0.086, 0.103] **anti-conservative** | 0.080 [0.072, 0.088] **anti-conservative** | 0.131 [0.121, 0.141] | 0.649 [0.636, 0.663] |
| skewed | 0.5 | 50 | 0.077 [0.070, 0.085] **anti-conservative** | 0.195 [0.184, 0.207] **anti-conservative** | 0.082 [0.075, 0.091] | 0.666 [0.652, 0.679] |
| skewed | 0.5 | 115 | 0.067 [0.060, 0.074] **anti-conservative** | 0.478 [0.463, 0.492] **anti-conservative** | 0.065 [0.059, 0.073] | 0.514 [0.499, 0.528] |
| skewed | 0.5 | 240 | 0.062 [0.056, 0.069] **anti-conservative** | 0.804 [0.792, 0.815] **anti-conservative** | 0.058 [0.052, 0.065] | 0.191 [0.180, 0.203] |
| skewed | 0.8 | 20 | 0.017 [0.014, 0.021] **conservative** | 0.011 [0.008, 0.014] **conservative** | 0.169 [0.159, 0.180] | 0.834 [0.823, 0.845] |
| skewed | 0.8 | 50 | 0.088 [0.080, 0.096] **anti-conservative** | 0.072 [0.065, 0.080] **anti-conservative** | 0.152 [0.142, 0.162] | 0.714 [0.700, 0.726] |
| skewed | 0.8 | 115 | 0.080 [0.073, 0.088] **anti-conservative** | 0.183 [0.173, 0.195] **anti-conservative** | 0.102 [0.093, 0.111] | 0.644 [0.630, 0.658] |
| skewed | 0.8 | 240 | 0.066 [0.060, 0.074] **anti-conservative** | 0.405 [0.391, 0.420] **anti-conservative** | 0.073 [0.066, 0.081] | 0.568 [0.554, 0.582] |

### Bootstrap CI coverage of the true difference (nominal 0.95)

| group | kind | tie rate | n | effect | coverage | mean CI width |
|---|---|---|---|---|---|---|
| h0 | binary | 0 | 20 | 0.000 | 0.965 [0.959, 0.970] | 0.904 |
| h0 | binary | 0 | 50 | 0.000 | 0.951 [0.944, 0.956] | 0.577 |
| h0 | binary | 0 | 115 | 0.000 | 0.957 [0.950, 0.962] | 0.368 |
| h0 | binary | 0 | 240 | 0.000 | 0.952 [0.946, 0.958] | 0.254 |
| h0 | binary | 0.5 | 20 | 0.000 | 0.954 [0.947, 0.959] | 0.661 |
| h0 | binary | 0.5 | 50 | 0.000 | 0.956 [0.949, 0.961] | 0.400 |
| h0 | binary | 0.5 | 115 | 0.000 | 0.956 [0.949, 0.961] | 0.261 |
| h0 | binary | 0.5 | 240 | 0.000 | 0.955 [0.949, 0.960] | 0.179 |
| h0 | binary | 0.8 | 20 | 0.000 | 0.904 [0.895, 0.912] **undercovers** | 0.383 |
| h0 | binary | 0.8 | 50 | 0.000 | 0.929 [0.921, 0.936] **undercovers** | 0.252 |
| h0 | binary | 0.8 | 115 | 0.000 | 0.943 [0.936, 0.949] **undercovers** | 0.164 |
| h0 | binary | 0.8 | 240 | 0.000 | 0.945 [0.938, 0.951] | 0.113 |
| h0 | continuous | 0 | 20 | 0.000 | 0.953 [0.947, 0.959] | 0.234 |
| h0 | continuous | 0 | 50 | 0.000 | 0.951 [0.945, 0.957] | 0.142 |
| h0 | continuous | 0 | 115 | 0.000 | 0.948 [0.942, 0.954] | 0.092 |
| h0 | continuous | 0 | 240 | 0.000 | 0.949 [0.942, 0.955] | 0.063 |
| h0 | continuous | 0.5 | 20 | 0.000 | 0.906 [0.897, 0.914] **undercovers** | 0.172 |
| h0 | continuous | 0.5 | 50 | 0.000 | 0.929 [0.921, 0.936] **undercovers** | 0.100 |
| h0 | continuous | 0.5 | 115 | 0.000 | 0.942 [0.934, 0.948] **undercovers** | 0.065 |
| h0 | continuous | 0.5 | 240 | 0.000 | 0.944 [0.937, 0.950] | 0.045 |
| h0 | continuous | 0.8 | 20 | 0.000 | 0.882 [0.872, 0.891] **undercovers** | 0.304 |
| h0 | continuous | 0.8 | 50 | 0.000 | 0.878 [0.869, 0.888] **undercovers** | 0.071 |
| h0 | continuous | 0.8 | 115 | 0.000 | 0.918 [0.910, 0.926] **undercovers** | 0.041 |
| h0 | continuous | 0.8 | 240 | 0.000 | 0.938 [0.931, 0.945] **undercovers** | 0.028 |
| h0 | skewed | 0 | 20 | 0.000 | 0.952 [0.945, 0.958] | 0.264 |
| h0 | skewed | 0 | 50 | 0.000 | 0.947 [0.940, 0.953] | 0.148 |
| h0 | skewed | 0 | 115 | 0.000 | 0.950 [0.943, 0.956] | 0.094 |
| h0 | skewed | 0 | 240 | 0.000 | 0.948 [0.941, 0.954] | 0.064 |
| h0 | skewed | 0.5 | 20 | 0.000 | 0.869 [0.859, 0.879] **undercovers** | 0.185 |
| h0 | skewed | 0.5 | 50 | 0.000 | 0.918 [0.909, 0.925] **undercovers** | 0.108 |
| h0 | skewed | 0.5 | 115 | 0.000 | 0.935 [0.927, 0.941] **undercovers** | 0.067 |
| h0 | skewed | 0.5 | 240 | 0.000 | 0.942 [0.935, 0.948] **undercovers** | 0.046 |
| h0 | skewed | 0.8 | 20 | 0.000 | 0.831 [0.820, 0.841] **undercovers** | 0.358 |
| h0 | skewed | 0.8 | 50 | 0.000 | 0.848 [0.838, 0.858] **undercovers** | 0.074 |
| h0 | skewed | 0.8 | 115 | 0.000 | 0.898 [0.889, 0.907] **undercovers** | 0.044 |
| h0 | skewed | 0.8 | 240 | 0.000 | 0.927 [0.919, 0.934] **undercovers** | 0.029 |
| mde | binary | 0 | 21 | 0.590 | 0.818 [0.800, 0.836] **undercovers** | 0.694 |
| mde | binary | 0 | 51 | 0.387 | 0.974 [0.966, 0.981] **overcovers** | 0.527 |
| mde | binary | 0 | 115 | 0.259 | 0.957 [0.946, 0.965] | 0.357 |
| mde | binary | 0 | 240 | 0.180 | 0.951 [0.940, 0.960] | 0.250 |
| mde | binary | 0.5 | 20 | 0.417 | 0.979 [0.972, 0.985] **overcovers** | 0.531 |
| mde | binary | 0.5 | 50 | 0.274 | 0.953 [0.942, 0.962] | 0.371 |
| mde | binary | 0.5 | 115 | 0.183 | 0.956 [0.945, 0.964] | 0.252 |
| mde | binary | 0.5 | 240 | 0.127 | 0.956 [0.946, 0.965] | 0.176 |
| mde | binary | 0.8 | 51 | 0.173 | 0.964 [0.955, 0.972] | 0.240 |
| mde | binary | 0.8 | 115 | 0.116 | 0.940 [0.927, 0.950] **undercovers** | 0.159 |
| mde | binary | 0.8 | 241 | 0.080 | 0.948 [0.936, 0.957] | 0.111 |
| mde | continuous | 0 | 21 | 0.157 | 0.949 [0.938, 0.958] | 0.227 |
| mde | continuous | 0 | 51 | 0.099 | 0.948 [0.937, 0.958] | 0.140 |
| mde | continuous | 0 | 115 | 0.065 | 0.944 [0.932, 0.954] | 0.092 |
| mde | continuous | 0 | 241 | 0.045 | 0.946 [0.934, 0.956] | 0.063 |
| mde | continuous | 0.5 | 21 | 0.142 | 0.959 [0.949, 0.967] | 0.227 |
| mde | continuous | 0.5 | 50 | 0.076 | 0.945 [0.934, 0.955] | 0.111 |
| mde | continuous | 0.5 | 116 | 0.048 | 0.944 [0.933, 0.954] | 0.067 |
| mde | continuous | 0.5 | 241 | 0.033 | 0.950 [0.939, 0.960] | 0.045 |
| mde | continuous | 0.8 | 51 | 0.073 | 0.976 [0.968, 0.982] **overcovers** | 0.124 |
| mde | continuous | 0.8 | 116 | 0.034 | 0.948 [0.937, 0.958] | 0.050 |
| mde | continuous | 0.8 | 241 | 0.022 | 0.949 [0.938, 0.959] | 0.031 |
| mde | skewed | 0 | 21 | 0.157 | 0.941 [0.929, 0.951] | 0.254 |
| mde | skewed | 0 | 51 | 0.099 | 0.952 [0.941, 0.961] | 0.148 |
| mde | skewed | 0 | 115 | 0.065 | 0.951 [0.940, 0.960] | 0.094 |
| mde | skewed | 0 | 241 | 0.045 | 0.946 [0.934, 0.956] | 0.064 |
| mde | skewed | 0.5 | 21 | 0.142 | 0.952 [0.941, 0.961] | 0.258 |
| mde | skewed | 0.5 | 50 | 0.076 | 0.954 [0.943, 0.963] | 0.128 |
| mde | skewed | 0.5 | 116 | 0.048 | 0.947 [0.935, 0.956] | 0.071 |
| mde | skewed | 0.5 | 241 | 0.033 | 0.951 [0.940, 0.960] | 0.047 |
| mde | skewed | 0.8 | 51 | 0.073 | 0.961 [0.951, 0.969] | 0.125 |
| mde | skewed | 0.8 | 116 | 0.034 | 0.955 [0.944, 0.964] | 0.058 |
| mde | skewed | 0.8 | 241 | 0.022 | 0.950 [0.939, 0.959] | 0.033 |
| fixed | binary | 0.6 | 1254 | 0.050 | 0.944 [0.933, 0.954] | 0.070 |
| fixed | binary | 0.6 | 312 | 0.100 | 0.948 [0.937, 0.958] | 0.139 |
| fixed | binary | 0.6 | 77 | 0.200 | 0.954 [0.943, 0.963] | 0.272 |
| fixed | continuous | 0.6 | 91 | 0.050 | 0.940 [0.928, 0.951] | 0.071 |
| fixed | continuous | 0.6 | 32 | 0.100 | 0.956 [0.945, 0.965] | 0.156 |
| fixed | continuous | 0.6 | 17 | 0.200 | 0.977 [0.969, 0.983] **overcovers** | 0.376 |
| fixed | skewed | 0.6 | 91 | 0.050 | 0.947 [0.935, 0.957] | 0.079 |
| fixed | skewed | 0.6 | 32 | 0.100 | 0.951 [0.940, 0.960] | 0.182 |
| fixed | skewed | 0.6 | 17 | 0.200 | 0.960 [0.950, 0.969] | 0.332 |

### Power at the n the formula computes for 80% power

| group | kind | tie rate | true effect | true SD | n* | predicted | randomisation | sign test | CI excludes 0 |
|---|---|---|---|---|---|---|---|---|---|
| mde | binary | 0 | 0.590 | 0.807 | 21 | 0.80 | 0.759 [0.739, 0.779] **optimistic** | 0.759 [0.739, 0.779] | 0.734 [0.713, 0.755] |
| mde | binary | 0 | 0.387 | 0.922 | 51 | 0.80 | 0.777 [0.756, 0.796] **optimistic** | 0.809 [0.790, 0.827] | 0.767 [0.746, 0.786] |
| mde | binary | 0 | 0.259 | 0.966 | 115 | 0.80 | 0.770 [0.749, 0.789] **optimistic** | 0.770 [0.750, 0.790] | 0.764 [0.744, 0.784] |
| mde | binary | 0 | 0.180 | 0.984 | 240 | 0.80 | 0.782 [0.762, 0.800] | 0.790 [0.770, 0.809] | 0.792 [0.772, 0.810] |
| mde | binary | 0.5 | 0.417 | 0.571 | 20 | 0.80 | 0.754 [0.733, 0.773] **optimistic** | 0.754 [0.733, 0.773] | 0.856 [0.839, 0.872] |
| mde | binary | 0.5 | 0.274 | 0.652 | 50 | 0.80 | 0.745 [0.724, 0.765] **optimistic** | 0.739 [0.718, 0.759] | 0.793 [0.773, 0.811] |
| mde | binary | 0.5 | 0.183 | 0.683 | 115 | 0.80 | 0.750 [0.729, 0.770] **optimistic** | 0.753 [0.732, 0.772] | 0.787 [0.767, 0.805] |
| mde | binary | 0.5 | 0.127 | 0.696 | 240 | 0.80 | 0.781 [0.761, 0.800] | 0.782 [0.762, 0.801] | 0.809 [0.790, 0.827] |
| mde | binary | 0.8 | 0.173 | 0.412 | 51 | 0.80 | 0.786 [0.766, 0.805] | 0.786 [0.766, 0.805] | 0.918 [0.904, 0.930] |
| mde | binary | 0.8 | 0.116 | 0.432 | 115 | 0.80 | 0.758 [0.738, 0.778] **optimistic** | 0.755 [0.734, 0.775] | 0.837 [0.819, 0.853] |
| mde | binary | 0.8 | 0.080 | 0.440 | 241 | 0.80 | 0.771 [0.751, 0.790] **optimistic** | 0.772 [0.752, 0.791] | 0.819 [0.801, 0.837] |
| mde | continuous | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.787 [0.767, 0.806] | 0.510 [0.486, 0.533] | 0.777 [0.756, 0.796] |
| mde | continuous | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.786 [0.766, 0.804] | 0.600 [0.577, 0.623] | 0.789 [0.769, 0.808] |
| mde | continuous | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.779 [0.759, 0.798] **optimistic** | 0.555 [0.532, 0.578] | 0.780 [0.760, 0.799] |
| mde | continuous | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.793 [0.773, 0.811] | 0.563 [0.539, 0.586] | 0.794 [0.774, 0.812] |
| mde | continuous | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.855 [0.838, 0.871] | 0.629 [0.606, 0.651] | 0.930 [0.917, 0.941] |
| mde | continuous | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.817 [0.798, 0.835] | 0.555 [0.531, 0.578] | 0.859 [0.842, 0.875] |
| mde | continuous | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.807 [0.788, 0.825] | 0.580 [0.557, 0.603] | 0.829 [0.811, 0.846] |
| mde | continuous | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.805 [0.785, 0.823] | 0.572 [0.549, 0.595] | 0.814 [0.795, 0.831] |
| mde | continuous | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.912 [0.898, 0.924] **pessimistic** | 0.773 [0.753, 0.792] | 0.986 [0.979, 0.991] |
| mde | continuous | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.868 [0.851, 0.883] **pessimistic** | 0.633 [0.610, 0.655] | 0.912 [0.898, 0.925] |
| mde | continuous | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.843 [0.825, 0.859] | 0.605 [0.582, 0.628] | 0.876 [0.859, 0.890] |
| mde | skewed | 0 | 0.157 | 0.250 | 21 | 0.80 | 0.938 [0.926, 0.949] **pessimistic** | 0.305 [0.283, 0.327] | 0.977 [0.968, 0.983] |
| mde | skewed | 0 | 0.099 | 0.250 | 51 | 0.80 | 0.887 [0.872, 0.901] **pessimistic** | 0.090 [0.078, 0.105] | 0.940 [0.927, 0.950] |
| mde | skewed | 0 | 0.065 | 0.250 | 115 | 0.80 | 0.848 [0.830, 0.864] | 0.060 [0.049, 0.072] | 0.898 [0.883, 0.911] |
| mde | skewed | 0 | 0.045 | 0.250 | 241 | 0.80 | 0.828 [0.810, 0.845] | 0.411 [0.388, 0.434] | 0.873 [0.857, 0.888] |
| mde | skewed | 0.5 | 0.142 | 0.227 | 21 | 0.80 | 0.985 [0.978, 0.989] **pessimistic** | 0.985 [0.978, 0.989] | 0.999 [0.996, 1.000] |
| mde | skewed | 0.5 | 0.076 | 0.193 | 50 | 0.80 | 0.960 [0.950, 0.968] **pessimistic** | 0.341 [0.319, 0.364] | 0.987 [0.980, 0.991] |
| mde | skewed | 0.5 | 0.048 | 0.183 | 116 | 0.80 | 0.898 [0.883, 0.911] **pessimistic** | 0.081 [0.069, 0.095] | 0.950 [0.939, 0.959] |
| mde | skewed | 0.5 | 0.033 | 0.180 | 241 | 0.80 | 0.857 [0.840, 0.873] | 0.066 [0.055, 0.079] | 0.910 [0.895, 0.922] |
| mde | skewed | 0.8 | 0.073 | 0.183 | 51 | 0.80 | 0.966 [0.956, 0.974] **pessimistic** | 0.966 [0.956, 0.974] | 0.999 [0.996, 1.000] |
| mde | skewed | 0.8 | 0.034 | 0.131 | 116 | 0.80 | 0.982 [0.975, 0.987] **pessimistic** | 0.517 [0.494, 0.541] | 0.997 [0.994, 0.999] |
| mde | skewed | 0.8 | 0.022 | 0.120 | 241 | 0.80 | 0.921 [0.907, 0.932] **pessimistic** | 0.131 [0.116, 0.148] | 0.971 [0.962, 0.978] |
| fixed | binary | 0.6 | 0.050 | 0.630 | 1254 | 0.80 | 0.787 [0.767, 0.805] | 0.787 [0.767, 0.806] | 0.803 [0.784, 0.821] |
| fixed | binary | 0.6 | 0.100 | 0.624 | 312 | 0.80 | 0.776 [0.756, 0.795] **optimistic** | 0.776 [0.755, 0.795] | 0.802 [0.783, 0.820] |
| fixed | binary | 0.6 | 0.200 | 0.600 | 77 | 0.80 | 0.763 [0.742, 0.782] **optimistic** | 0.754 [0.733, 0.774] | 0.813 [0.794, 0.831] |
| fixed | continuous | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.829 [0.810, 0.846] | 0.595 [0.572, 0.618] | 0.859 [0.842, 0.875] |
| fixed | continuous | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.872 [0.856, 0.887] **pessimistic** | 0.637 [0.614, 0.659] | 0.936 [0.923, 0.946] |
| fixed | continuous | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.707 [0.685, 0.728] **optimistic** | 0.659 [0.637, 0.681] | 0.978 [0.970, 0.984] |
| fixed | skewed | 0.6 | 0.050 | 0.170 | 91 | 0.80 | 0.940 [0.928, 0.951] **pessimistic** | 0.206 [0.188, 0.226] | 0.976 [0.968, 0.982] |
| fixed | skewed | 0.6 | 0.100 | 0.200 | 32 | 0.80 | 0.997 [0.993, 0.999] **pessimistic** | 0.997 [0.993, 0.999] | 1.000 [0.997, 1.000] |
| fixed | skewed | 0.6 | 0.200 | 0.292 | 17 | 0.80 | 0.737 [0.716, 0.757] **optimistic** | 0.737 [0.716, 0.757] | 0.990 [0.984, 0.993] |

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
| continuous | independent | 3 | 50 | 0.143 [0.128, 0.161] | 0.042 [0.033, 0.052] |
| continuous | independent | 5 | 50 | 0.223 [0.204, 0.244] | 0.051 [0.041, 0.062] |
| continuous | independent | 10 | 50 | 0.398 [0.375, 0.421] | 0.049 [0.040, 0.060] |
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

- undercovers: bootstrap CI coverage binary n=20 ties=0.8 (H0): 0.904 [0.895, 0.912]
- undercovers: bootstrap CI coverage binary n=50 ties=0.8 (H0): 0.929 [0.921, 0.936]
- undercovers: bootstrap CI coverage binary n=115 ties=0.8 (H0): 0.943 [0.936, 0.949]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.5 (H0): 0.906 [0.897, 0.914]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.5 (H0): 0.929 [0.921, 0.936]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.5 (H0): 0.942 [0.934, 0.948]
- undercovers: bootstrap CI coverage continuous n=20 ties=0.8 (H0): 0.882 [0.872, 0.891]
- undercovers: bootstrap CI coverage continuous n=50 ties=0.8 (H0): 0.878 [0.869, 0.888]
- undercovers: bootstrap CI coverage continuous n=115 ties=0.8 (H0): 0.918 [0.910, 0.926]
- undercovers: bootstrap CI coverage continuous n=240 ties=0.8 (H0): 0.938 [0.931, 0.945]
- anti-conservative: randomisation type-I skewed n=20 ties=0 (H0): 0.078 [0.070, 0.086]
- anti-conservative: sign test type-I skewed n=20 ties=0 (H0): 0.190 [0.179, 0.201]
- anti-conservative: randomisation type-I skewed n=50 ties=0 (H0): 0.065 [0.058, 0.072]
- anti-conservative: sign test type-I skewed n=50 ties=0 (H0): 0.392 [0.378, 0.406]
- anti-conservative: randomisation type-I skewed n=115 ties=0 (H0): 0.057 [0.051, 0.064]
- anti-conservative: sign test type-I skewed n=115 ties=0 (H0): 0.789 [0.777, 0.801]
- anti-conservative: sign test type-I skewed n=240 ties=0 (H0): 0.986 [0.983, 0.989]
- anti-conservative: randomisation type-I skewed n=20 ties=0.5 (H0): 0.094 [0.086, 0.103]
- anti-conservative: sign test type-I skewed n=20 ties=0.5 (H0): 0.080 [0.072, 0.088]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.5 (H0): 0.869 [0.859, 0.879]
- anti-conservative: randomisation type-I skewed n=50 ties=0.5 (H0): 0.077 [0.070, 0.085]
- anti-conservative: sign test type-I skewed n=50 ties=0.5 (H0): 0.195 [0.184, 0.207]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.5 (H0): 0.918 [0.909, 0.925]
- anti-conservative: randomisation type-I skewed n=115 ties=0.5 (H0): 0.067 [0.060, 0.074]
- anti-conservative: sign test type-I skewed n=115 ties=0.5 (H0): 0.478 [0.463, 0.492]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.5 (H0): 0.935 [0.927, 0.941]
- anti-conservative: randomisation type-I skewed n=240 ties=0.5 (H0): 0.062 [0.056, 0.069]
- anti-conservative: sign test type-I skewed n=240 ties=0.5 (H0): 0.804 [0.792, 0.815]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.5 (H0): 0.942 [0.935, 0.948]
- undercovers: bootstrap CI coverage skewed n=20 ties=0.8 (H0): 0.831 [0.820, 0.841]
- anti-conservative: randomisation type-I skewed n=50 ties=0.8 (H0): 0.088 [0.080, 0.096]
- anti-conservative: sign test type-I skewed n=50 ties=0.8 (H0): 0.072 [0.065, 0.080]
- undercovers: bootstrap CI coverage skewed n=50 ties=0.8 (H0): 0.848 [0.838, 0.858]
- anti-conservative: randomisation type-I skewed n=115 ties=0.8 (H0): 0.080 [0.073, 0.088]
- anti-conservative: sign test type-I skewed n=115 ties=0.8 (H0): 0.183 [0.173, 0.195]
- undercovers: bootstrap CI coverage skewed n=115 ties=0.8 (H0): 0.898 [0.889, 0.907]
- anti-conservative: randomisation type-I skewed n=240 ties=0.8 (H0): 0.066 [0.060, 0.074]
- anti-conservative: sign test type-I skewed n=240 ties=0.8 (H0): 0.405 [0.391, 0.420]
- undercovers: bootstrap CI coverage skewed n=240 ties=0.8 (H0): 0.927 [0.919, 0.934]
- optimistic: randomisation power binary n*=21 ties=0 effect=0.590 (mde): 0.759 [0.739, 0.779]
- undercovers: bootstrap CI coverage binary n*=21 ties=0 effect=0.590 (mde): 0.818 [0.800, 0.836]
- optimistic: randomisation power binary n*=51 ties=0 effect=0.387 (mde): 0.777 [0.756, 0.796]
- optimistic: randomisation power binary n*=115 ties=0 effect=0.259 (mde): 0.770 [0.749, 0.789]
- optimistic: randomisation power binary n*=20 ties=0.5 effect=0.417 (mde): 0.754 [0.733, 0.773]
- optimistic: randomisation power binary n*=50 ties=0.5 effect=0.274 (mde): 0.745 [0.724, 0.765]
- optimistic: randomisation power binary n*=115 ties=0.5 effect=0.183 (mde): 0.750 [0.729, 0.770]
- optimistic: randomisation power binary n*=115 ties=0.8 effect=0.116 (mde): 0.758 [0.738, 0.778]
- undercovers: bootstrap CI coverage binary n*=115 ties=0.8 effect=0.116 (mde): 0.940 [0.927, 0.950]
- optimistic: randomisation power binary n*=241 ties=0.8 effect=0.080 (mde): 0.771 [0.751, 0.790]
- optimistic: randomisation power continuous n*=115 ties=0 effect=0.065 (mde): 0.779 [0.759, 0.798]
- optimistic: randomisation power binary n*=312 ties=0.6 effect=0.100 (fixed): 0.776 [0.756, 0.795]
- optimistic: randomisation power binary n*=77 ties=0.6 effect=0.200 (fixed): 0.763 [0.742, 0.782]
- optimistic: randomisation power continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.707 [0.685, 0.728]
- optimistic: randomisation power skewed n*=17 ties=0.6 effect=0.200 (fixed): 0.737 [0.716, 0.757]
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
- conservative: randomisation type-I continuous n=20 ties=0.8 (H0): 0.007 [0.005, 0.010]
- conservative: sign test type-I continuous n=20 ties=0.8 (H0): 0.004 [0.002, 0.006]
- conservative: sign test type-I continuous n=50 ties=0.8 (H0): 0.021 [0.018, 0.026]
- conservative: sign test type-I continuous n=115 ties=0.8 (H0): 0.030 [0.026, 0.035]
- conservative: sign test type-I continuous n=240 ties=0.8 (H0): 0.034 [0.029, 0.039]
- conservative: randomisation type-I skewed n=20 ties=0.8 (H0): 0.017 [0.014, 0.021]
- conservative: sign test type-I skewed n=20 ties=0.8 (H0): 0.011 [0.008, 0.014]
- overcovers: bootstrap CI coverage binary n*=51 ties=0 effect=0.387 (mde): 0.974 [0.966, 0.981]
- overcovers: bootstrap CI coverage binary n*=20 ties=0.5 effect=0.417 (mde): 0.979 [0.972, 0.985]
- pessimistic: randomisation power continuous n*=51 ties=0.8 effect=0.073 (mde): 0.912 [0.898, 0.924]
- overcovers: bootstrap CI coverage continuous n*=51 ties=0.8 effect=0.073 (mde): 0.976 [0.968, 0.982]
- pessimistic: randomisation power continuous n*=116 ties=0.8 effect=0.034 (mde): 0.868 [0.851, 0.883]
- pessimistic: randomisation power skewed n*=21 ties=0 effect=0.157 (mde): 0.938 [0.926, 0.949]
- pessimistic: randomisation power skewed n*=51 ties=0 effect=0.099 (mde): 0.887 [0.872, 0.901]
- pessimistic: randomisation power skewed n*=21 ties=0.5 effect=0.142 (mde): 0.985 [0.978, 0.989]
- pessimistic: randomisation power skewed n*=50 ties=0.5 effect=0.076 (mde): 0.960 [0.950, 0.968]
- pessimistic: randomisation power skewed n*=116 ties=0.5 effect=0.048 (mde): 0.898 [0.883, 0.911]
- pessimistic: randomisation power skewed n*=51 ties=0.8 effect=0.073 (mde): 0.966 [0.956, 0.974]
- pessimistic: randomisation power skewed n*=116 ties=0.8 effect=0.034 (mde): 0.982 [0.975, 0.987]
- pessimistic: randomisation power skewed n*=241 ties=0.8 effect=0.022 (mde): 0.921 [0.907, 0.932]
- pessimistic: randomisation power continuous n*=32 ties=0.6 effect=0.100 (fixed): 0.872 [0.856, 0.887]
- overcovers: bootstrap CI coverage continuous n*=17 ties=0.6 effect=0.200 (fixed): 0.977 [0.969, 0.983]
- pessimistic: randomisation power skewed n*=91 ties=0.6 effect=0.050 (fixed): 0.940 [0.928, 0.951]
- pessimistic: randomisation power skewed n*=32 ties=0.6 effect=0.100 (fixed): 0.997 [0.993, 0.999]
- conservative: Holm FWER binary independent m=3 n=50: 0.028 [0.021, 0.036]
- conservative: Holm FWER binary independent m=10 n=50: 0.025 [0.019, 0.033]
- conservative: Holm FWER binary all-pairs m=3 n=50: 0.021 [0.015, 0.028]
- conservative: Holm FWER binary all-pairs m=6 n=50: 0.029 [0.022, 0.038]
- conservative: Holm FWER binary all-pairs m=10 n=50: 0.020 [0.015, 0.028]
- conservative: Holm FWER binary all-pairs m=3 n=115: 0.029 [0.022, 0.038]
- conservative: Holm FWER binary all-pairs m=6 n=115: 0.024 [0.018, 0.032]
- conservative: Holm FWER binary all-pairs m=10 n=115: 0.026 [0.020, 0.035]

Wall time 190 s on 8 worker(s).
