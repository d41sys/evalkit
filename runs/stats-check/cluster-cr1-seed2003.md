## Clustered data (protocol: `docs/protocol-clustered-se.md`)

seed 2003; replications 2000 per coverage cell, 2000 per power cell; bootstrap resamples 1000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences or clusters). Intervals are Wilson 99% over replications. Estimators: naive = mean +/- 1.96 s/sqrt(n); item bootstrap = the CI `compare` printed before clusters; clustered normal = mean +/- 1.96 SE_clustered (Miller 2024); clustered normal CR1 = mean +/- t(C - 1) sqrt(C / (C - 1)) SE_clustered (`docs/protocol-cluster-small-sample.md`); cluster bootstrap = percentile interval from resampling clusters. ICC^ is the mean ANOVA estimate; SE ratio is mean clustered/naive SE next to sqrt(DEFF) of the design.

### Coverage of the true value, design `mean` (mean of one model's scores), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | clustered normal CR1 | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.947 [0.932, 0.958] | 0.958 [0.945, 0.968] | 0.930 [0.914, 0.944] **undercovers** | 0.944 [0.929, 0.956] | 0.938 [0.922, 0.950] | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.946 [0.931, 0.957] | 0.956 [0.942, 0.966] | 0.922 [0.905, 0.936] **undercovers** | 0.941 [0.926, 0.953] | 0.924 [0.907, 0.938] **undercovers** | 0.96 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.949 [0.935, 0.960] | 0.943 [0.928, 0.955] | 0.944 [0.929, 0.955] | 0.953 [0.939, 0.964] | 0.947 [0.933, 0.958] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.947 [0.932, 0.958] | 0.949 [0.935, 0.960] | 0.940 [0.924, 0.952] | 0.947 [0.933, 0.958] | 0.943 [0.928, 0.955] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.955 [0.941, 0.966] | 0.956 [0.942, 0.966] | 0.951 [0.936, 0.962] | 0.954 [0.940, 0.964] | 0.951 [0.937, 0.962] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.951 [0.936, 0.962] | 0.949 [0.935, 0.960] | 0.948 [0.934, 0.959] | 0.952 [0.938, 0.962] | 0.950 [0.936, 0.961] | 0.99 | 1.00 |
| binary | 0.1 | 0.10 | 20 | equal | 0.902 [0.884, 0.918] **undercovers** | 0.917 [0.900, 0.932] **undercovers** | 0.926 [0.910, 0.940] **undercovers** | 0.943 [0.928, 0.955] | 0.938 [0.922, 0.950] | 1.15 | 1.18 |
| binary | 0.1 | 0.10 | 20 | unequal | 0.897 [0.879, 0.914] **undercovers** | 0.906 [0.888, 0.922] **undercovers** | 0.931 [0.915, 0.944] **undercovers** | 0.950 [0.935, 0.961] | 0.933 [0.918, 0.946] **undercovers** | 1.16 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.882 [0.862, 0.899] **undercovers** | 0.885 [0.866, 0.903] **undercovers** | 0.933 [0.918, 0.946] **undercovers** | 0.942 [0.926, 0.954] | 0.936 [0.920, 0.949] **undercovers** | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.887 [0.868, 0.904] **undercovers** | 0.886 [0.866, 0.903] **undercovers** | 0.941 [0.926, 0.953] | 0.948 [0.934, 0.959] | 0.940 [0.925, 0.952] | 1.20 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.910 [0.893, 0.926] **undercovers** | 0.914 [0.897, 0.929] **undercovers** | 0.943 [0.928, 0.955] | 0.948 [0.934, 0.959] | 0.952 [0.938, 0.962] | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.899 [0.880, 0.915] **undercovers** | 0.900 [0.881, 0.916] **undercovers** | 0.946 [0.931, 0.958] | 0.949 [0.935, 0.960] | 0.946 [0.931, 0.958] | 1.21 | 1.22 |
| binary | 0.3 | 0.30 | 20 | equal | 0.801 [0.778, 0.823] **undercovers** | 0.821 [0.798, 0.842] **undercovers** | 0.922 [0.906, 0.937] **undercovers** | 0.945 [0.930, 0.956] | 0.934 [0.919, 0.947] **undercovers** | 1.45 | 1.48 |
| binary | 0.3 | 0.29 | 20 | unequal | 0.776 [0.752, 0.800] **undercovers** | 0.794 [0.770, 0.816] **undercovers** | 0.912 [0.894, 0.927] **undercovers** | 0.934 [0.919, 0.947] **undercovers** | 0.920 [0.903, 0.935] **undercovers** | 1.50 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.803 [0.780, 0.825] **undercovers** | 0.804 [0.781, 0.826] **undercovers** | 0.940 [0.924, 0.952] | 0.950 [0.935, 0.961] | 0.949 [0.935, 0.960] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.784 [0.760, 0.807] **undercovers** | 0.788 [0.764, 0.811] **undercovers** | 0.944 [0.929, 0.956] | 0.955 [0.941, 0.966] | 0.945 [0.930, 0.957] | 1.54 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.812 [0.789, 0.834] **undercovers** | 0.819 [0.795, 0.840] **undercovers** | 0.940 [0.925, 0.952] | 0.945 [0.930, 0.956] | 0.944 [0.929, 0.956] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.778 [0.753, 0.801] **undercovers** | 0.777 [0.752, 0.800] **undercovers** | 0.949 [0.935, 0.960] | 0.953 [0.939, 0.964] | 0.951 [0.936, 0.962] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.950 [0.935, 0.961] | 0.951 [0.937, 0.962] | 0.937 [0.922, 0.950] **undercovers** | 0.959 [0.945, 0.969] | 0.934 [0.918, 0.947] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.952 [0.938, 0.962] | 0.954 [0.940, 0.965] | 0.931 [0.915, 0.944] **undercovers** | 0.955 [0.941, 0.965] | 0.926 [0.909, 0.940] **undercovers** | 0.96 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.948 [0.933, 0.959] | 0.944 [0.929, 0.955] | 0.945 [0.930, 0.956] | 0.951 [0.937, 0.962] | 0.942 [0.926, 0.954] | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.955 [0.941, 0.965] | 0.953 [0.939, 0.964] | 0.944 [0.929, 0.955] | 0.952 [0.938, 0.963] | 0.944 [0.929, 0.956] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.949 [0.934, 0.960] | 0.947 [0.932, 0.958] | 0.948 [0.933, 0.959] | 0.951 [0.937, 0.962] | 0.946 [0.931, 0.957] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.953 [0.939, 0.963] | 0.950 [0.936, 0.961] | 0.948 [0.934, 0.959] | 0.953 [0.939, 0.963] | 0.943 [0.928, 0.955] | 0.99 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.898 [0.880, 0.915] **undercovers** | 0.900 [0.882, 0.916] **undercovers** | 0.925 [0.909, 0.939] **undercovers** | 0.948 [0.934, 0.959] | 0.921 [0.905, 0.936] **undercovers** | 1.14 | 1.18 |
| continuous | 0.1 | 0.11 | 20 | unequal | 0.895 [0.876, 0.911] **undercovers** | 0.896 [0.877, 0.912] **undercovers** | 0.933 [0.917, 0.946] **undercovers** | 0.952 [0.938, 0.963] | 0.928 [0.912, 0.942] **undercovers** | 1.17 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.897 [0.878, 0.913] **undercovers** | 0.896 [0.878, 0.913] **undercovers** | 0.945 [0.930, 0.957] | 0.952 [0.938, 0.963] | 0.943 [0.928, 0.955] | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.882 [0.862, 0.899] **undercovers** | 0.882 [0.863, 0.900] **undercovers** | 0.936 [0.921, 0.949] **undercovers** | 0.942 [0.927, 0.954] | 0.934 [0.918, 0.947] **undercovers** | 1.19 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.910 [0.892, 0.925] **undercovers** | 0.904 [0.886, 0.920] **undercovers** | 0.956 [0.942, 0.966] | 0.959 [0.945, 0.969] | 0.952 [0.938, 0.963] | 1.18 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.894 [0.875, 0.910] **undercovers** | 0.885 [0.866, 0.903] **undercovers** | 0.939 [0.923, 0.951] | 0.944 [0.929, 0.956] | 0.936 [0.921, 0.949] **undercovers** | 1.21 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.799 [0.775, 0.822] **undercovers** | 0.802 [0.779, 0.824] **undercovers** | 0.927 [0.911, 0.941] **undercovers** | 0.948 [0.933, 0.959] | 0.925 [0.908, 0.939] **undercovers** | 1.44 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.787 [0.762, 0.810] **undercovers** | 0.786 [0.762, 0.809] **undercovers** | 0.923 [0.906, 0.937] **undercovers** | 0.951 [0.937, 0.962] | 0.923 [0.907, 0.937] **undercovers** | 1.49 | 1.56 |
| continuous | 0.3 | 0.30 | 50 | equal | 0.808 [0.785, 0.830] **undercovers** | 0.812 [0.789, 0.834] **undercovers** | 0.946 [0.931, 0.958] | 0.954 [0.940, 0.965] | 0.944 [0.929, 0.955] | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 50 | unequal | 0.787 [0.763, 0.810] **undercovers** | 0.790 [0.766, 0.813] **undercovers** | 0.944 [0.929, 0.955] | 0.950 [0.935, 0.961] | 0.942 [0.926, 0.954] | 1.53 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.828 [0.805, 0.848] **undercovers** | 0.825 [0.802, 0.845] **undercovers** | 0.955 [0.941, 0.965] | 0.958 [0.944, 0.968] | 0.950 [0.935, 0.961] | 1.48 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.795 [0.771, 0.818] **undercovers** | 0.795 [0.771, 0.818] **undercovers** | 0.953 [0.939, 0.964] | 0.956 [0.942, 0.966] | 0.949 [0.934, 0.960] | 1.55 | 1.56 |

### Coverage of the true value, design `paired` (paired difference A - B (truth 0)), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | clustered normal CR1 | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.939 [0.923, 0.951] | 0.946 [0.931, 0.958] | 0.920 [0.903, 0.935] **undercovers** | 0.944 [0.929, 0.955] | 0.932 [0.916, 0.945] **undercovers** | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.948 [0.933, 0.959] | 0.953 [0.939, 0.963] | 0.932 [0.916, 0.945] **undercovers** | 0.957 [0.943, 0.967] | 0.944 [0.929, 0.956] | 0.97 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.955 [0.941, 0.965] | 0.958 [0.945, 0.968] | 0.950 [0.935, 0.961] | 0.958 [0.944, 0.968] | 0.950 [0.936, 0.961] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.951 [0.937, 0.962] | 0.954 [0.940, 0.964] | 0.948 [0.934, 0.959] | 0.956 [0.943, 0.966] | 0.950 [0.935, 0.961] | 0.98 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.944 [0.929, 0.956] | 0.944 [0.929, 0.956] | 0.936 [0.921, 0.949] **undercovers** | 0.939 [0.923, 0.951] | 0.941 [0.926, 0.953] | 1.00 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.946 [0.931, 0.957] | 0.950 [0.936, 0.961] | 0.942 [0.926, 0.954] | 0.947 [0.932, 0.958] | 0.945 [0.930, 0.956] | 0.99 | 1.00 |
| binary | 0.1 | 0.11 | 20 | equal | 0.905 [0.887, 0.921] **undercovers** | 0.913 [0.895, 0.928] **undercovers** | 0.935 [0.919, 0.948] **undercovers** | 0.959 [0.946, 0.969] | 0.942 [0.927, 0.954] | 1.15 | 1.18 |
| binary | 0.1 | 0.10 | 20 | unequal | 0.887 [0.868, 0.904] **undercovers** | 0.899 [0.880, 0.915] **undercovers** | 0.923 [0.906, 0.937] **undercovers** | 0.945 [0.930, 0.957] | 0.932 [0.917, 0.946] **undercovers** | 1.17 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.911 [0.893, 0.926] **undercovers** | 0.913 [0.895, 0.928] **undercovers** | 0.948 [0.933, 0.959] | 0.955 [0.941, 0.965] | 0.949 [0.934, 0.960] | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.893 [0.874, 0.910] **undercovers** | 0.898 [0.879, 0.914] **undercovers** | 0.945 [0.930, 0.956] | 0.953 [0.939, 0.963] | 0.949 [0.934, 0.960] | 1.20 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.893 [0.874, 0.910] **undercovers** | 0.899 [0.881, 0.916] **undercovers** | 0.934 [0.919, 0.947] **undercovers** | 0.938 [0.923, 0.950] | 0.936 [0.921, 0.949] **undercovers** | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.877 [0.857, 0.895] **undercovers** | 0.884 [0.864, 0.901] **undercovers** | 0.934 [0.919, 0.947] **undercovers** | 0.938 [0.923, 0.950] | 0.939 [0.923, 0.951] | 1.21 | 1.22 |
| binary | 0.3 | 0.30 | 20 | equal | 0.801 [0.778, 0.823] **undercovers** | 0.811 [0.787, 0.833] **undercovers** | 0.925 [0.909, 0.939] **undercovers** | 0.945 [0.930, 0.956] | 0.934 [0.918, 0.947] **undercovers** | 1.45 | 1.48 |
| binary | 0.3 | 0.30 | 20 | unequal | 0.790 [0.766, 0.813] **undercovers** | 0.797 [0.773, 0.820] **undercovers** | 0.924 [0.907, 0.938] **undercovers** | 0.941 [0.925, 0.953] | 0.929 [0.913, 0.942] **undercovers** | 1.51 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.811 [0.787, 0.833] **undercovers** | 0.814 [0.791, 0.835] **undercovers** | 0.941 [0.925, 0.953] | 0.948 [0.934, 0.959] | 0.946 [0.931, 0.957] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.777 [0.753, 0.801] **undercovers** | 0.788 [0.764, 0.811] **undercovers** | 0.942 [0.926, 0.954] | 0.951 [0.937, 0.962] | 0.946 [0.931, 0.958] | 1.54 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.798 [0.774, 0.820] **undercovers** | 0.803 [0.780, 0.825] **undercovers** | 0.946 [0.931, 0.957] | 0.950 [0.936, 0.961] | 0.946 [0.931, 0.958] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.780 [0.756, 0.803] **undercovers** | 0.784 [0.759, 0.807] **undercovers** | 0.940 [0.925, 0.952] | 0.946 [0.931, 0.957] | 0.942 [0.927, 0.954] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.952 [0.938, 0.962] | 0.952 [0.938, 0.962] | 0.938 [0.923, 0.950] | 0.952 [0.938, 0.962] | 0.928 [0.912, 0.942] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.957 [0.943, 0.967] | 0.955 [0.941, 0.965] | 0.930 [0.914, 0.943] **undercovers** | 0.951 [0.936, 0.962] | 0.927 [0.911, 0.941] **undercovers** | 0.96 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.948 [0.933, 0.959] | 0.943 [0.928, 0.955] | 0.937 [0.922, 0.950] **undercovers** | 0.948 [0.934, 0.959] | 0.934 [0.919, 0.947] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.951 [0.936, 0.962] | 0.948 [0.934, 0.959] | 0.946 [0.931, 0.957] | 0.950 [0.936, 0.961] | 0.946 [0.931, 0.958] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.945 [0.930, 0.957] | 0.945 [0.930, 0.957] | 0.941 [0.925, 0.953] | 0.947 [0.933, 0.958] | 0.936 [0.920, 0.949] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.950 [0.936, 0.961] | 0.951 [0.937, 0.962] | 0.947 [0.933, 0.958] | 0.951 [0.936, 0.962] | 0.948 [0.934, 0.959] | 1.00 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.898 [0.880, 0.915] **undercovers** | 0.897 [0.878, 0.913] **undercovers** | 0.931 [0.915, 0.944] **undercovers** | 0.952 [0.938, 0.962] | 0.926 [0.910, 0.940] **undercovers** | 1.15 | 1.18 |
| continuous | 0.1 | 0.10 | 20 | unequal | 0.876 [0.856, 0.894] **undercovers** | 0.877 [0.857, 0.895] **undercovers** | 0.915 [0.898, 0.930] **undercovers** | 0.940 [0.925, 0.952] | 0.914 [0.897, 0.929] **undercovers** | 1.16 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.908 [0.890, 0.923] **undercovers** | 0.905 [0.887, 0.921] **undercovers** | 0.949 [0.934, 0.960] | 0.956 [0.943, 0.966] | 0.946 [0.931, 0.957] | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.892 [0.873, 0.909] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.941 [0.926, 0.953] | 0.945 [0.930, 0.957] | 0.942 [0.926, 0.954] | 1.19 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.900 [0.881, 0.916] **undercovers** | 0.899 [0.880, 0.915] **undercovers** | 0.943 [0.928, 0.955] | 0.946 [0.931, 0.958] | 0.943 [0.928, 0.955] | 1.18 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.901 [0.882, 0.917] **undercovers** | 0.899 [0.880, 0.915] **undercovers** | 0.951 [0.936, 0.962] | 0.954 [0.940, 0.965] | 0.948 [0.933, 0.959] | 1.20 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.803 [0.780, 0.825] **undercovers** | 0.804 [0.780, 0.826] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.955 [0.941, 0.966] | 0.930 [0.914, 0.944] **undercovers** | 1.44 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.779 [0.754, 0.802] **undercovers** | 0.779 [0.755, 0.802] **undercovers** | 0.913 [0.895, 0.928] **undercovers** | 0.942 [0.926, 0.954] | 0.912 [0.894, 0.927] **undercovers** | 1.49 | 1.56 |
| continuous | 0.3 | 0.30 | 50 | equal | 0.819 [0.795, 0.840] **undercovers** | 0.813 [0.790, 0.834] **undercovers** | 0.943 [0.928, 0.955] | 0.950 [0.936, 0.961] | 0.940 [0.924, 0.952] | 1.46 | 1.48 |
| continuous | 0.3 | 0.30 | 50 | unequal | 0.793 [0.769, 0.816] **undercovers** | 0.794 [0.770, 0.816] **undercovers** | 0.945 [0.930, 0.957] | 0.952 [0.938, 0.963] | 0.943 [0.928, 0.955] | 1.53 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.811 [0.787, 0.833] **undercovers** | 0.802 [0.778, 0.824] **undercovers** | 0.941 [0.925, 0.953] | 0.944 [0.929, 0.956] | 0.940 [0.924, 0.952] | 1.48 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.793 [0.769, 0.815] **undercovers** | 0.788 [0.764, 0.811] **undercovers** | 0.940 [0.925, 0.952] | 0.944 [0.929, 0.956] | 0.938 [0.922, 0.950] | 1.54 | 1.56 |

### Type-I error at alpha = 0.05, paired design (true difference 0)

| kind | ICC | clusters | sizes | item sign-flip | cluster sign-flip |
|---|---|---|---|---|---|
| binary | 0 | 20 | equal | 0.038 [0.029, 0.051] | 0.042 [0.031, 0.055] |
| binary | 0 | 20 | unequal | 0.035 [0.025, 0.047] | 0.025 [0.018, 0.036] **conservative** |
| binary | 0 | 50 | equal | 0.035 [0.026, 0.048] | 0.038 [0.028, 0.051] |
| binary | 0 | 50 | unequal | 0.037 [0.028, 0.049] | 0.038 [0.028, 0.051] |
| binary | 0 | 100 | equal | 0.050 [0.039, 0.064] | 0.051 [0.040, 0.065] |
| binary | 0 | 100 | unequal | 0.044 [0.034, 0.058] | 0.044 [0.034, 0.057] |
| binary | 0.1 | 20 | equal | 0.074 [0.061, 0.091] **anti-conservative** | 0.030 [0.022, 0.041] |
| binary | 0.1 | 20 | unequal | 0.083 [0.068, 0.100] **anti-conservative** | 0.039 [0.029, 0.052] |
| binary | 0.1 | 50 | equal | 0.076 [0.062, 0.093] **anti-conservative** | 0.039 [0.029, 0.052] |
| binary | 0.1 | 50 | unequal | 0.089 [0.074, 0.107] **anti-conservative** | 0.038 [0.028, 0.051] |
| binary | 0.1 | 100 | equal | 0.099 [0.083, 0.117] **anti-conservative** | 0.054 [0.043, 0.069] |
| binary | 0.1 | 100 | unequal | 0.106 [0.090, 0.125] **anti-conservative** | 0.054 [0.043, 0.069] |
| binary | 0.3 | 20 | equal | 0.171 [0.150, 0.193] **anti-conservative** | 0.045 [0.034, 0.059] |
| binary | 0.3 | 20 | unequal | 0.173 [0.152, 0.196] **anti-conservative** | 0.040 [0.030, 0.052] |
| binary | 0.3 | 50 | equal | 0.169 [0.148, 0.191] **anti-conservative** | 0.049 [0.038, 0.062] |
| binary | 0.3 | 50 | unequal | 0.193 [0.171, 0.217] **anti-conservative** | 0.043 [0.032, 0.056] |
| binary | 0.3 | 100 | equal | 0.189 [0.167, 0.213] **anti-conservative** | 0.045 [0.034, 0.059] |
| binary | 0.3 | 100 | unequal | 0.204 [0.182, 0.229] **anti-conservative** | 0.046 [0.036, 0.060] |
| continuous | 0 | 20 | equal | 0.046 [0.036, 0.060] | 0.051 [0.039, 0.065] |
| continuous | 0 | 20 | unequal | 0.043 [0.033, 0.057] | 0.048 [0.037, 0.061] |
| continuous | 0 | 50 | equal | 0.053 [0.042, 0.067] | 0.053 [0.042, 0.067] |
| continuous | 0 | 50 | unequal | 0.048 [0.037, 0.062] | 0.048 [0.037, 0.062] |
| continuous | 0 | 100 | equal | 0.053 [0.042, 0.067] | 0.057 [0.045, 0.071] |
| continuous | 0 | 100 | unequal | 0.050 [0.038, 0.064] | 0.049 [0.038, 0.063] |
| continuous | 0.1 | 20 | equal | 0.100 [0.084, 0.118] **anti-conservative** | 0.050 [0.038, 0.064] |
| continuous | 0.1 | 20 | unequal | 0.119 [0.102, 0.139] **anti-conservative** | 0.056 [0.044, 0.071] |
| continuous | 0.1 | 50 | equal | 0.092 [0.077, 0.110] **anti-conservative** | 0.044 [0.034, 0.058] |
| continuous | 0.1 | 50 | unequal | 0.103 [0.087, 0.122] **anti-conservative** | 0.050 [0.039, 0.064] |
| continuous | 0.1 | 100 | equal | 0.102 [0.086, 0.121] **anti-conservative** | 0.053 [0.042, 0.067] |
| continuous | 0.1 | 100 | unequal | 0.100 [0.084, 0.118] **anti-conservative** | 0.048 [0.037, 0.061] |
| continuous | 0.3 | 20 | equal | 0.192 [0.170, 0.216] **anti-conservative** | 0.045 [0.035, 0.059] |
| continuous | 0.3 | 20 | unequal | 0.220 [0.197, 0.244] **anti-conservative** | 0.057 [0.045, 0.071] |
| continuous | 0.3 | 50 | equal | 0.182 [0.161, 0.206] **anti-conservative** | 0.051 [0.039, 0.065] |
| continuous | 0.3 | 50 | unequal | 0.205 [0.183, 0.230] **anti-conservative** | 0.045 [0.035, 0.059] |
| continuous | 0.3 | 100 | equal | 0.185 [0.164, 0.209] **anti-conservative** | 0.057 [0.045, 0.072] |
| continuous | 0.3 | 100 | unequal | 0.209 [0.187, 0.234] **anti-conservative** | 0.055 [0.043, 0.070] |

### Power with the design effect (paired continuous, clusters of 5, effect 0.1, SD 0.25)

| ICC | n rule | DEFF | items | clusters | predicted | cluster sign-flip | cluster CI excludes 0 |
|---|---|---|---|---|---|---|---|
| 0 | DEFF-inflated | 1.00 | 50 | 10 | 0.80 | 0.704 [0.677, 0.729] **optimistic** | 0.827 [0.804, 0.847] |
| 0 | naive (no DEFF) | 1.00 | 50 | 10 | - | 0.712 [0.685, 0.737] | 0.829 [0.806, 0.849] |
| 0.1 | DEFF-inflated | 1.40 | 70 | 14 | 0.80 | 0.752 [0.727, 0.776] **optimistic** | 0.833 [0.810, 0.853] |
| 0.1 | naive (no DEFF) | 1.40 | 50 | 10 | - | 0.559 [0.531, 0.588] | 0.706 [0.679, 0.731] |
| 0.3 | DEFF-inflated | 2.20 | 110 | 22 | 0.80 | 0.771 [0.746, 0.795] **optimistic** | 0.825 [0.802, 0.846] |
| 0.3 | naive (no DEFF) | 2.20 | 50 | 10 | - | 0.374 [0.347, 0.402] | 0.534 [0.505, 0.563] |

### Claims under the pre-registered rules

- Claim 1 (naive undercovers), supported: the naive normal interval is flagged `undercovers` in 48 of 48 cells with ICC > 0, the item bootstrap in 48 (rule: at least 90% of cells for both).
- Claim 2 (clustered is calibrated), clustered-SE normal: approximately supported. Flagged `undercovers` in 6 of 48 cells with at least 50 clusters (lowest point coverage 0.933).
-   Not binding, fewer than 50 clusters: clustered-SE normal flagged in 23 of 24 cells (lowest point coverage 0.912).
-   Control (ICC 0, at least 50 clusters): clustered-SE normal flagged in 2 of 16 cells.
- Claim 2 (clustered is calibrated), cluster bootstrap: approximately supported. Flagged `undercovers` in 6 of 48 cells with at least 50 clusters (lowest point coverage 0.934).
-   Not binding, fewer than 50 clusters: cluster bootstrap flagged in 20 of 24 cells (lowest point coverage 0.912).
-   Control (ICC 0, at least 50 clusters): cluster bootstrap flagged in 2 of 16 cells.
- Claim 3a (item sign-flip is anti-conservative under clustering), supported: flagged in 24 of 24 paired cells with ICC > 0.
- Claim 3b (cluster sign-flip is valid), supported: anti-conservative in 0 of 36 paired cells.
- Claim 4 (power at the design-effect n), ICC 0, n = 50 items (10 clusters): cluster sign-flip power 0.704 [0.677, 0.729], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.1, n = 70 items (14 clusters): cluster sign-flip power 0.752 [0.727, 0.776], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.3, n = 110 items (22 clusters): cluster sign-flip power 0.771 [0.746, 0.795], optimistic.
- SE ratio (descriptive): mean clustered/naive SE over sqrt(DEFF) is 0.982 (range 0.952 to 0.996) over 72 cells.

### Small-cluster correction (`docs/protocol-cluster-small-sample.md`)

- CR1 small-cluster correction: flagged `undercovers` in 1 of 72 cells against 29 for the uncorrected clustered normal interval on the same replications; flagged `overcovers` in 0.
-   fewer than 50 clusters (24 cells): flagged 1 corrected vs 23 uncorrected; point coverage 0.934 to 0.959 corrected, 0.912 to 0.938 uncorrected.
-   at least 50 clusters (48 cells): flagged 0 corrected vs 6 uncorrected; point coverage 0.938 to 0.959 corrected, 0.933 to 0.956 uncorrected.
-   ICC 0 (24 cells): flagged 0 corrected vs 9 uncorrected; point coverage 0.939 to 0.959 corrected, 0.920 to 0.951 uncorrected.
- Rule for this seed (F1 <= 16, F1 <= F0 / 2, no `overcovers`): met (F0 = 29, F1 = 1, O1 = 0). Adoption needs 'met' on all three final seeds.

### Every flagged cell

- undercovers: cluster_normal coverage mean binary ICC=0 C=20 equal: 0.930 [0.914, 0.944]
- undercovers: cluster_normal coverage mean binary ICC=0 C=20 unequal: 0.922 [0.905, 0.936]
- undercovers: cluster_bootstrap coverage mean binary ICC=0 C=20 unequal: 0.924 [0.907, 0.938]
- undercovers: naive coverage mean binary ICC=0.1 C=20 equal: 0.902 [0.884, 0.918]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 equal: 0.917 [0.900, 0.932]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=20 equal: 0.926 [0.910, 0.940]
- undercovers: naive coverage mean binary ICC=0.1 C=20 unequal: 0.897 [0.879, 0.914]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.906 [0.888, 0.922]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=20 unequal: 0.931 [0.915, 0.944]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.933 [0.918, 0.946]
- undercovers: naive coverage mean binary ICC=0.1 C=50 equal: 0.882 [0.862, 0.899]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 equal: 0.885 [0.866, 0.903]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=50 equal: 0.933 [0.918, 0.946]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=50 equal: 0.936 [0.920, 0.949]
- undercovers: naive coverage mean binary ICC=0.1 C=50 unequal: 0.887 [0.868, 0.904]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 unequal: 0.886 [0.866, 0.903]
- undercovers: naive coverage mean binary ICC=0.1 C=100 equal: 0.910 [0.893, 0.926]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 equal: 0.914 [0.897, 0.929]
- undercovers: naive coverage mean binary ICC=0.1 C=100 unequal: 0.899 [0.880, 0.915]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 unequal: 0.900 [0.881, 0.916]
- undercovers: naive coverage mean binary ICC=0.3 C=20 equal: 0.801 [0.778, 0.823]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 equal: 0.821 [0.798, 0.842]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 equal: 0.922 [0.906, 0.937]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=20 equal: 0.934 [0.919, 0.947]
- undercovers: naive coverage mean binary ICC=0.3 C=20 unequal: 0.776 [0.752, 0.800]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.794 [0.770, 0.816]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 unequal: 0.912 [0.894, 0.927]
- undercovers: cluster_normal_cr1 coverage mean binary ICC=0.3 C=20 unequal: 0.934 [0.919, 0.947]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.920 [0.903, 0.935]
- undercovers: naive coverage mean binary ICC=0.3 C=50 equal: 0.803 [0.780, 0.825]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 equal: 0.804 [0.781, 0.826]
- undercovers: naive coverage mean binary ICC=0.3 C=50 unequal: 0.784 [0.760, 0.807]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 unequal: 0.788 [0.764, 0.811]
- undercovers: naive coverage mean binary ICC=0.3 C=100 equal: 0.812 [0.789, 0.834]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 equal: 0.819 [0.795, 0.840]
- undercovers: naive coverage mean binary ICC=0.3 C=100 unequal: 0.778 [0.753, 0.801]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 unequal: 0.777 [0.752, 0.800]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=20 equal: 0.937 [0.922, 0.950]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=20 equal: 0.934 [0.918, 0.947]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=20 unequal: 0.931 [0.915, 0.944]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=20 unequal: 0.926 [0.909, 0.940]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 equal: 0.898 [0.880, 0.915]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 equal: 0.900 [0.882, 0.916]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=20 equal: 0.925 [0.909, 0.939]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=20 equal: 0.921 [0.905, 0.936]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 unequal: 0.895 [0.876, 0.911]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.896 [0.877, 0.912]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=20 unequal: 0.933 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.928 [0.912, 0.942]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 equal: 0.897 [0.878, 0.913]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 equal: 0.896 [0.878, 0.913]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 unequal: 0.882 [0.862, 0.899]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.882 [0.863, 0.900]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=50 unequal: 0.936 [0.921, 0.949]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.934 [0.918, 0.947]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 equal: 0.910 [0.892, 0.925]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 equal: 0.904 [0.886, 0.920]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 unequal: 0.894 [0.875, 0.910]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 unequal: 0.885 [0.866, 0.903]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=100 unequal: 0.936 [0.921, 0.949]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 equal: 0.799 [0.775, 0.822]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.802 [0.779, 0.824]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 equal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.925 [0.908, 0.939]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 unequal: 0.787 [0.762, 0.810]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.786 [0.762, 0.809]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 unequal: 0.923 [0.906, 0.937]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.923 [0.907, 0.937]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 equal: 0.808 [0.785, 0.830]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 equal: 0.812 [0.789, 0.834]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 unequal: 0.787 [0.763, 0.810]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 unequal: 0.790 [0.766, 0.813]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 equal: 0.828 [0.805, 0.848]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 equal: 0.825 [0.802, 0.845]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 unequal: 0.795 [0.771, 0.818]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 unequal: 0.795 [0.771, 0.818]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 equal: 0.920 [0.903, 0.935]
- undercovers: cluster_bootstrap coverage paired binary ICC=0 C=20 equal: 0.932 [0.916, 0.945]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 unequal: 0.932 [0.916, 0.945]
- undercovers: cluster_normal coverage paired binary ICC=0 C=100 equal: 0.936 [0.921, 0.949]
- undercovers: naive coverage paired binary ICC=0.1 C=20 equal: 0.905 [0.887, 0.921]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 equal: 0.913 [0.895, 0.928]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 equal: 0.935 [0.919, 0.948]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 equal: 0.074 [0.061, 0.091]
- undercovers: naive coverage paired binary ICC=0.1 C=20 unequal: 0.887 [0.868, 0.904]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 unequal: 0.899 [0.880, 0.915]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 unequal: 0.923 [0.906, 0.937]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.1 C=20 unequal: 0.932 [0.917, 0.946]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 unequal: 0.083 [0.068, 0.100]
- undercovers: naive coverage paired binary ICC=0.1 C=50 equal: 0.911 [0.893, 0.926]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 equal: 0.913 [0.895, 0.928]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 equal: 0.076 [0.062, 0.093]
- undercovers: naive coverage paired binary ICC=0.1 C=50 unequal: 0.893 [0.874, 0.910]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 unequal: 0.898 [0.879, 0.914]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 unequal: 0.089 [0.074, 0.107]
- undercovers: naive coverage paired binary ICC=0.1 C=100 equal: 0.893 [0.874, 0.910]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 equal: 0.899 [0.881, 0.916]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=100 equal: 0.934 [0.919, 0.947]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.1 C=100 equal: 0.936 [0.921, 0.949]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 equal: 0.099 [0.083, 0.117]
- undercovers: naive coverage paired binary ICC=0.1 C=100 unequal: 0.877 [0.857, 0.895]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 unequal: 0.884 [0.864, 0.901]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=100 unequal: 0.934 [0.919, 0.947]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 unequal: 0.106 [0.090, 0.125]
- undercovers: naive coverage paired binary ICC=0.3 C=20 equal: 0.801 [0.778, 0.823]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.811 [0.787, 0.833]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 equal: 0.925 [0.909, 0.939]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.934 [0.918, 0.947]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 equal: 0.171 [0.150, 0.193]
- undercovers: naive coverage paired binary ICC=0.3 C=20 unequal: 0.790 [0.766, 0.813]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.797 [0.773, 0.820]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 unequal: 0.924 [0.907, 0.938]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.929 [0.913, 0.942]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 unequal: 0.173 [0.152, 0.196]
- undercovers: naive coverage paired binary ICC=0.3 C=50 equal: 0.811 [0.787, 0.833]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 equal: 0.814 [0.791, 0.835]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 equal: 0.169 [0.148, 0.191]
- undercovers: naive coverage paired binary ICC=0.3 C=50 unequal: 0.777 [0.753, 0.801]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 unequal: 0.788 [0.764, 0.811]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 unequal: 0.193 [0.171, 0.217]
- undercovers: naive coverage paired binary ICC=0.3 C=100 equal: 0.798 [0.774, 0.820]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 equal: 0.803 [0.780, 0.825]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 equal: 0.189 [0.167, 0.213]
- undercovers: naive coverage paired binary ICC=0.3 C=100 unequal: 0.780 [0.756, 0.803]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 unequal: 0.784 [0.759, 0.807]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 unequal: 0.204 [0.182, 0.229]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 equal: 0.928 [0.912, 0.942]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=20 unequal: 0.930 [0.914, 0.943]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=50 equal: 0.937 [0.922, 0.950]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=50 equal: 0.934 [0.919, 0.947]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=100 equal: 0.936 [0.920, 0.949]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 equal: 0.898 [0.880, 0.915]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.897 [0.878, 0.913]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 equal: 0.931 [0.915, 0.944]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.926 [0.910, 0.940]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 equal: 0.100 [0.084, 0.118]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 unequal: 0.876 [0.856, 0.894]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.877 [0.857, 0.895]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 unequal: 0.915 [0.898, 0.930]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.914 [0.897, 0.929]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 unequal: 0.119 [0.102, 0.139]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 equal: 0.908 [0.890, 0.923]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 equal: 0.905 [0.887, 0.921]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 equal: 0.092 [0.077, 0.110]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 unequal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 unequal: 0.892 [0.873, 0.909]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 unequal: 0.103 [0.087, 0.122]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 equal: 0.900 [0.881, 0.916]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 equal: 0.899 [0.880, 0.915]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 equal: 0.102 [0.086, 0.121]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 unequal: 0.901 [0.882, 0.917]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 unequal: 0.899 [0.880, 0.915]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 unequal: 0.100 [0.084, 0.118]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 equal: 0.803 [0.780, 0.825]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.804 [0.780, 0.826]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 equal: 0.935 [0.920, 0.948]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.930 [0.914, 0.944]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 equal: 0.192 [0.170, 0.216]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 unequal: 0.779 [0.754, 0.802]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.779 [0.755, 0.802]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 unequal: 0.913 [0.895, 0.928]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.912 [0.894, 0.927]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 unequal: 0.220 [0.197, 0.244]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 equal: 0.819 [0.795, 0.840]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 equal: 0.813 [0.790, 0.834]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 equal: 0.182 [0.161, 0.206]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 unequal: 0.793 [0.769, 0.816]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 unequal: 0.794 [0.770, 0.816]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 unequal: 0.205 [0.183, 0.230]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 equal: 0.811 [0.787, 0.833]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 equal: 0.802 [0.778, 0.824]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 equal: 0.185 [0.164, 0.209]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 unequal: 0.793 [0.769, 0.815]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 unequal: 0.788 [0.764, 0.811]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 unequal: 0.209 [0.187, 0.234]
- optimistic: cluster sign-flip power ICC=0 n=50 (deff): 0.704 [0.677, 0.729]
- optimistic: cluster sign-flip power ICC=0 n=50 (naive): 0.712 [0.685, 0.737]
- optimistic: cluster sign-flip power ICC=0.1 n=70 (deff): 0.752 [0.727, 0.776]
- optimistic: cluster sign-flip power ICC=0.1 n=50 (naive): 0.559 [0.531, 0.588]
- optimistic: cluster sign-flip power ICC=0.3 n=110 (deff): 0.771 [0.746, 0.795]
- optimistic: cluster sign-flip power ICC=0.3 n=50 (naive): 0.374 [0.347, 0.402]
- conservative: cluster sign-flip type-I paired binary ICC=0 C=20 unequal: 0.025 [0.018, 0.036]

Wall time 72 s on 8 worker(s).
