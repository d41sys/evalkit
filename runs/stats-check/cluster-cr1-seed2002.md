## Clustered data (protocol: `docs/protocol-clustered-se.md`)

seed 2002; replications 2000 per coverage cell, 2000 per power cell; bootstrap resamples 1000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences or clusters). Intervals are Wilson 99% over replications. Estimators: naive = mean +/- 1.96 s/sqrt(n); item bootstrap = the CI `compare` printed before clusters; clustered normal = mean +/- 1.96 SE_clustered (Miller 2024); clustered normal CR1 = mean +/- t(C - 1) sqrt(C / (C - 1)) SE_clustered (`docs/protocol-cluster-small-sample.md`); cluster bootstrap = percentile interval from resampling clusters. ICC^ is the mean ANOVA estimate; SE ratio is mean clustered/naive SE next to sqrt(DEFF) of the design.

### Coverage of the true value, design `mean` (mean of one model's scores), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | clustered normal CR1 | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.944 [0.929, 0.956] | 0.954 [0.940, 0.965] | 0.929 [0.913, 0.943] **undercovers** | 0.947 [0.933, 0.958] | 0.939 [0.924, 0.951] | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.945 [0.930, 0.957] | 0.955 [0.941, 0.966] | 0.930 [0.914, 0.943] **undercovers** | 0.945 [0.930, 0.956] | 0.929 [0.913, 0.942] **undercovers** | 0.96 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.951 [0.937, 0.962] | 0.953 [0.939, 0.963] | 0.946 [0.931, 0.958] | 0.956 [0.942, 0.966] | 0.952 [0.938, 0.963] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.957 [0.944, 0.967] | 0.959 [0.945, 0.969] | 0.945 [0.930, 0.956] | 0.955 [0.941, 0.966] | 0.945 [0.930, 0.956] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.952 [0.938, 0.962] | 0.950 [0.936, 0.961] | 0.946 [0.931, 0.957] | 0.949 [0.935, 0.960] | 0.949 [0.934, 0.960] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.952 [0.938, 0.963] | 0.951 [0.937, 0.962] | 0.946 [0.931, 0.958] | 0.950 [0.935, 0.961] | 0.947 [0.932, 0.958] | 0.99 | 1.00 |
| binary | 0.1 | 0.11 | 20 | equal | 0.908 [0.890, 0.923] **undercovers** | 0.923 [0.907, 0.937] **undercovers** | 0.938 [0.922, 0.950] | 0.953 [0.939, 0.964] | 0.948 [0.934, 0.959] | 1.15 | 1.18 |
| binary | 0.1 | 0.10 | 20 | unequal | 0.885 [0.865, 0.902] **undercovers** | 0.901 [0.882, 0.917] **undercovers** | 0.926 [0.910, 0.940] **undercovers** | 0.944 [0.929, 0.956] | 0.928 [0.912, 0.942] **undercovers** | 1.16 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.891 [0.872, 0.908] **undercovers** | 0.888 [0.869, 0.905] **undercovers** | 0.936 [0.921, 0.949] **undercovers** | 0.947 [0.932, 0.958] | 0.945 [0.930, 0.956] | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.892 [0.873, 0.909] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.940 [0.924, 0.952] | 0.944 [0.929, 0.956] | 0.941 [0.925, 0.953] | 1.20 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.900 [0.882, 0.916] **undercovers** | 0.905 [0.887, 0.921] **undercovers** | 0.945 [0.930, 0.957] | 0.949 [0.934, 0.960] | 0.947 [0.932, 0.958] | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.897 [0.879, 0.914] **undercovers** | 0.901 [0.882, 0.917] **undercovers** | 0.948 [0.933, 0.959] | 0.951 [0.937, 0.962] | 0.947 [0.933, 0.958] | 1.21 | 1.22 |
| binary | 0.3 | 0.30 | 20 | equal | 0.814 [0.790, 0.835] **undercovers** | 0.836 [0.813, 0.856] **undercovers** | 0.924 [0.907, 0.938] **undercovers** | 0.949 [0.935, 0.960] | 0.940 [0.924, 0.952] | 1.45 | 1.48 |
| binary | 0.3 | 0.30 | 20 | unequal | 0.774 [0.750, 0.798] **undercovers** | 0.791 [0.767, 0.814] **undercovers** | 0.911 [0.893, 0.926] **undercovers** | 0.934 [0.918, 0.947] **undercovers** | 0.920 [0.903, 0.935] **undercovers** | 1.50 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.810 [0.786, 0.832] **undercovers** | 0.808 [0.784, 0.830] **undercovers** | 0.940 [0.924, 0.952] | 0.951 [0.936, 0.962] | 0.950 [0.935, 0.961] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.790 [0.766, 0.813] **undercovers** | 0.792 [0.768, 0.815] **undercovers** | 0.936 [0.920, 0.949] **undercovers** | 0.944 [0.929, 0.955] | 0.941 [0.925, 0.953] | 1.53 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.814 [0.790, 0.835] **undercovers** | 0.820 [0.796, 0.841] **undercovers** | 0.941 [0.926, 0.953] | 0.946 [0.931, 0.957] | 0.945 [0.930, 0.956] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.772 [0.747, 0.795] **undercovers** | 0.774 [0.749, 0.797] **undercovers** | 0.940 [0.924, 0.952] | 0.944 [0.929, 0.956] | 0.943 [0.928, 0.955] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.957 [0.944, 0.967] | 0.957 [0.943, 0.967] | 0.944 [0.929, 0.956] | 0.962 [0.949, 0.972] | 0.939 [0.923, 0.951] | 0.97 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.946 [0.931, 0.957] | 0.948 [0.933, 0.959] | 0.930 [0.914, 0.944] **undercovers** | 0.954 [0.940, 0.965] | 0.927 [0.911, 0.941] **undercovers** | 0.96 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.955 [0.941, 0.965] | 0.952 [0.938, 0.963] | 0.945 [0.930, 0.957] | 0.954 [0.940, 0.964] | 0.944 [0.929, 0.956] | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.932 [0.917, 0.946] **undercovers** | 0.930 [0.914, 0.944] **undercovers** | 0.924 [0.907, 0.938] **undercovers** | 0.935 [0.919, 0.948] **undercovers** | 0.924 [0.908, 0.938] **undercovers** | 0.98 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.944 [0.929, 0.956] | 0.945 [0.930, 0.957] | 0.940 [0.924, 0.952] | 0.944 [0.929, 0.955] | 0.936 [0.921, 0.949] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.951 [0.936, 0.962] | 0.945 [0.930, 0.956] | 0.945 [0.930, 0.957] | 0.949 [0.935, 0.960] | 0.942 [0.927, 0.954] | 0.99 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.912 [0.895, 0.927] **undercovers** | 0.912 [0.894, 0.927] **undercovers** | 0.944 [0.929, 0.956] | 0.961 [0.948, 0.970] | 0.942 [0.926, 0.954] | 1.14 | 1.18 |
| continuous | 0.1 | 0.10 | 20 | unequal | 0.892 [0.873, 0.909] **undercovers** | 0.891 [0.872, 0.908] **undercovers** | 0.927 [0.911, 0.941] **undercovers** | 0.947 [0.932, 0.958] | 0.928 [0.912, 0.942] **undercovers** | 1.17 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.905 [0.887, 0.921] **undercovers** | 0.906 [0.888, 0.922] **undercovers** | 0.941 [0.926, 0.953] | 0.947 [0.932, 0.958] | 0.937 [0.922, 0.950] **undercovers** | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.890 [0.871, 0.907] **undercovers** | 0.890 [0.871, 0.907] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.942 [0.927, 0.954] | 0.930 [0.914, 0.944] **undercovers** | 1.19 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.892 [0.873, 0.909] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.938 [0.922, 0.950] | 0.946 [0.931, 0.957] | 0.939 [0.923, 0.951] | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.894 [0.875, 0.910] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.945 [0.930, 0.956] | 0.952 [0.938, 0.962] | 0.945 [0.930, 0.956] | 1.21 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.801 [0.778, 0.823] **undercovers** | 0.804 [0.781, 0.826] **undercovers** | 0.933 [0.918, 0.946] **undercovers** | 0.954 [0.940, 0.965] | 0.928 [0.912, 0.942] **undercovers** | 1.43 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.771 [0.746, 0.794] **undercovers** | 0.775 [0.750, 0.798] **undercovers** | 0.919 [0.902, 0.933] **undercovers** | 0.945 [0.930, 0.956] | 0.921 [0.904, 0.935] **undercovers** | 1.49 | 1.56 |
| continuous | 0.3 | 0.30 | 50 | equal | 0.811 [0.787, 0.833] **undercovers** | 0.813 [0.790, 0.834] **undercovers** | 0.949 [0.935, 0.960] | 0.959 [0.945, 0.969] | 0.944 [0.929, 0.956] | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 50 | unequal | 0.786 [0.762, 0.809] **undercovers** | 0.784 [0.760, 0.807] **undercovers** | 0.936 [0.920, 0.949] **undercovers** | 0.946 [0.931, 0.958] | 0.932 [0.917, 0.946] **undercovers** | 1.53 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.802 [0.779, 0.824] **undercovers** | 0.799 [0.775, 0.821] **undercovers** | 0.934 [0.918, 0.947] **undercovers** | 0.938 [0.923, 0.950] | 0.930 [0.914, 0.944] **undercovers** | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.803 [0.779, 0.825] **undercovers** | 0.798 [0.774, 0.820] **undercovers** | 0.946 [0.931, 0.957] | 0.948 [0.934, 0.959] | 0.941 [0.925, 0.953] | 1.55 | 1.56 |

### Coverage of the true value, design `paired` (paired difference A - B (truth 0)), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | clustered normal CR1 | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.939 [0.924, 0.951] | 0.947 [0.932, 0.958] | 0.928 [0.912, 0.942] **undercovers** | 0.950 [0.936, 0.961] | 0.936 [0.920, 0.949] **undercovers** | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.943 [0.928, 0.955] | 0.949 [0.935, 0.960] | 0.927 [0.911, 0.941] **undercovers** | 0.945 [0.930, 0.956] | 0.934 [0.919, 0.947] **undercovers** | 0.97 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.950 [0.936, 0.961] | 0.951 [0.937, 0.962] | 0.943 [0.928, 0.955] | 0.951 [0.936, 0.962] | 0.949 [0.934, 0.960] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.947 [0.932, 0.958] | 0.949 [0.935, 0.960] | 0.934 [0.919, 0.947] **undercovers** | 0.944 [0.929, 0.956] | 0.941 [0.926, 0.953] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.954 [0.940, 0.965] | 0.958 [0.944, 0.968] | 0.950 [0.936, 0.961] | 0.956 [0.942, 0.966] | 0.955 [0.941, 0.966] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.948 [0.934, 0.959] | 0.949 [0.935, 0.960] | 0.941 [0.925, 0.953] | 0.942 [0.927, 0.954] | 0.939 [0.924, 0.951] | 0.99 | 1.00 |
| binary | 0.1 | 0.10 | 20 | equal | 0.903 [0.885, 0.919] **undercovers** | 0.912 [0.894, 0.927] **undercovers** | 0.937 [0.922, 0.950] **undercovers** | 0.950 [0.936, 0.961] | 0.940 [0.925, 0.952] | 1.15 | 1.18 |
| binary | 0.1 | 0.10 | 20 | unequal | 0.891 [0.872, 0.908] **undercovers** | 0.903 [0.885, 0.919] **undercovers** | 0.929 [0.913, 0.942] **undercovers** | 0.948 [0.934, 0.959] | 0.938 [0.923, 0.950] | 1.17 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.889 [0.870, 0.906] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.936 [0.920, 0.949] **undercovers** | 0.943 [0.928, 0.955] | 0.939 [0.923, 0.951] | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.898 [0.879, 0.914] **undercovers** | 0.902 [0.884, 0.918] **undercovers** | 0.946 [0.931, 0.957] | 0.953 [0.939, 0.963] | 0.950 [0.936, 0.961] | 1.19 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.885 [0.865, 0.902] **undercovers** | 0.888 [0.869, 0.905] **undercovers** | 0.936 [0.920, 0.949] **undercovers** | 0.940 [0.924, 0.952] | 0.935 [0.919, 0.948] **undercovers** | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.883 [0.863, 0.900] **undercovers** | 0.888 [0.869, 0.905] **undercovers** | 0.939 [0.923, 0.951] | 0.944 [0.929, 0.955] | 0.940 [0.924, 0.952] | 1.20 | 1.22 |
| binary | 0.3 | 0.29 | 20 | equal | 0.820 [0.796, 0.841] **undercovers** | 0.827 [0.804, 0.848] **undercovers** | 0.932 [0.917, 0.946] **undercovers** | 0.957 [0.944, 0.967] | 0.937 [0.922, 0.950] **undercovers** | 1.44 | 1.48 |
| binary | 0.3 | 0.30 | 20 | unequal | 0.784 [0.759, 0.807] **undercovers** | 0.796 [0.772, 0.818] **undercovers** | 0.918 [0.901, 0.933] **undercovers** | 0.941 [0.926, 0.953] | 0.928 [0.912, 0.942] **undercovers** | 1.50 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.805 [0.781, 0.827] **undercovers** | 0.809 [0.785, 0.831] **undercovers** | 0.945 [0.930, 0.956] | 0.953 [0.939, 0.964] | 0.947 [0.933, 0.958] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.771 [0.746, 0.795] **undercovers** | 0.775 [0.751, 0.799] **undercovers** | 0.933 [0.917, 0.946] **undercovers** | 0.940 [0.924, 0.952] | 0.939 [0.923, 0.951] | 1.54 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.801 [0.777, 0.823] **undercovers** | 0.807 [0.783, 0.829] **undercovers** | 0.943 [0.928, 0.955] | 0.948 [0.933, 0.959] | 0.941 [0.926, 0.953] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.780 [0.756, 0.803] **undercovers** | 0.786 [0.761, 0.809] **undercovers** | 0.949 [0.935, 0.960] | 0.955 [0.941, 0.965] | 0.950 [0.936, 0.961] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.949 [0.935, 0.960] | 0.951 [0.936, 0.962] | 0.932 [0.917, 0.946] **undercovers** | 0.954 [0.940, 0.964] | 0.928 [0.912, 0.942] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.939 [0.923, 0.951] | 0.939 [0.924, 0.951] | 0.922 [0.905, 0.936] **undercovers** | 0.943 [0.928, 0.955] | 0.917 [0.900, 0.932] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.957 [0.943, 0.967] | 0.954 [0.940, 0.965] | 0.946 [0.931, 0.957] | 0.952 [0.938, 0.963] | 0.943 [0.928, 0.955] | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.946 [0.931, 0.958] | 0.947 [0.933, 0.958] | 0.937 [0.922, 0.950] **undercovers** | 0.947 [0.933, 0.958] | 0.934 [0.918, 0.947] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.948 [0.933, 0.959] | 0.946 [0.931, 0.957] | 0.946 [0.931, 0.957] | 0.948 [0.933, 0.959] | 0.943 [0.928, 0.955] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.947 [0.932, 0.958] | 0.946 [0.931, 0.958] | 0.943 [0.928, 0.955] | 0.947 [0.933, 0.958] | 0.942 [0.926, 0.954] | 0.99 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.899 [0.881, 0.916] **undercovers** | 0.902 [0.884, 0.918] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.949 [0.934, 0.960] | 0.931 [0.915, 0.945] **undercovers** | 1.14 | 1.18 |
| continuous | 0.1 | 0.10 | 20 | unequal | 0.879 [0.859, 0.897] **undercovers** | 0.883 [0.864, 0.901] **undercovers** | 0.920 [0.903, 0.935] **undercovers** | 0.945 [0.930, 0.956] | 0.915 [0.898, 0.930] **undercovers** | 1.16 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.892 [0.873, 0.909] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.939 [0.924, 0.951] | 0.950 [0.936, 0.961] | 0.934 [0.919, 0.947] **undercovers** | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.897 [0.878, 0.913] **undercovers** | 0.897 [0.878, 0.913] **undercovers** | 0.939 [0.924, 0.951] | 0.946 [0.931, 0.958] | 0.936 [0.920, 0.949] **undercovers** | 1.20 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.907 [0.889, 0.922] **undercovers** | 0.904 [0.886, 0.920] **undercovers** | 0.945 [0.930, 0.956] | 0.949 [0.935, 0.960] | 0.945 [0.930, 0.956] | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.885 [0.865, 0.902] **undercovers** | 0.881 [0.862, 0.899] **undercovers** | 0.942 [0.927, 0.954] | 0.944 [0.929, 0.956] | 0.940 [0.924, 0.952] | 1.21 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.810 [0.786, 0.832] **undercovers** | 0.815 [0.792, 0.836] **undercovers** | 0.934 [0.919, 0.947] **undercovers** | 0.952 [0.938, 0.962] | 0.934 [0.919, 0.947] **undercovers** | 1.44 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.789 [0.765, 0.812] **undercovers** | 0.789 [0.765, 0.812] **undercovers** | 0.925 [0.909, 0.939] **undercovers** | 0.945 [0.930, 0.956] | 0.926 [0.910, 0.940] **undercovers** | 1.48 | 1.56 |
| continuous | 0.3 | 0.29 | 50 | equal | 0.816 [0.792, 0.837] **undercovers** | 0.816 [0.793, 0.837] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.944 [0.929, 0.955] | 0.930 [0.914, 0.944] **undercovers** | 1.46 | 1.48 |
| continuous | 0.3 | 0.30 | 50 | unequal | 0.797 [0.773, 0.820] **undercovers** | 0.801 [0.778, 0.823] **undercovers** | 0.946 [0.931, 0.957] | 0.955 [0.941, 0.965] | 0.944 [0.929, 0.955] | 1.53 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.814 [0.790, 0.835] **undercovers** | 0.809 [0.785, 0.831] **undercovers** | 0.937 [0.922, 0.950] **undercovers** | 0.940 [0.924, 0.952] | 0.935 [0.920, 0.948] **undercovers** | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.777 [0.753, 0.801] **undercovers** | 0.769 [0.744, 0.793] **undercovers** | 0.950 [0.936, 0.961] | 0.954 [0.940, 0.965] | 0.947 [0.932, 0.958] | 1.54 | 1.56 |

### Type-I error at alpha = 0.05, paired design (true difference 0)

| kind | ICC | clusters | sizes | item sign-flip | cluster sign-flip |
|---|---|---|---|---|---|
| binary | 0 | 20 | equal | 0.035 [0.026, 0.048] | 0.035 [0.026, 0.048] |
| binary | 0 | 20 | unequal | 0.035 [0.026, 0.047] | 0.032 [0.023, 0.044] |
| binary | 0 | 50 | equal | 0.041 [0.031, 0.054] | 0.037 [0.028, 0.049] |
| binary | 0 | 50 | unequal | 0.040 [0.030, 0.052] | 0.043 [0.033, 0.056] |
| binary | 0 | 100 | equal | 0.040 [0.030, 0.052] | 0.037 [0.028, 0.050] |
| binary | 0 | 100 | unequal | 0.047 [0.036, 0.061] | 0.049 [0.038, 0.063] |
| binary | 0.1 | 20 | equal | 0.069 [0.055, 0.085] **anti-conservative** | 0.034 [0.025, 0.046] |
| binary | 0.1 | 20 | unequal | 0.077 [0.063, 0.094] **anti-conservative** | 0.036 [0.027, 0.049] |
| binary | 0.1 | 50 | equal | 0.091 [0.076, 0.109] **anti-conservative** | 0.048 [0.037, 0.062] |
| binary | 0.1 | 50 | unequal | 0.086 [0.071, 0.104] **anti-conservative** | 0.040 [0.030, 0.052] |
| binary | 0.1 | 100 | equal | 0.102 [0.085, 0.120] **anti-conservative** | 0.055 [0.043, 0.070] |
| binary | 0.1 | 100 | unequal | 0.103 [0.087, 0.122] **anti-conservative** | 0.050 [0.038, 0.064] |
| binary | 0.3 | 20 | equal | 0.156 [0.136, 0.178] **anti-conservative** | 0.030 [0.022, 0.042] |
| binary | 0.3 | 20 | unequal | 0.181 [0.160, 0.204] **anti-conservative** | 0.037 [0.028, 0.050] |
| binary | 0.3 | 50 | equal | 0.174 [0.153, 0.197] **anti-conservative** | 0.043 [0.033, 0.056] |
| binary | 0.3 | 50 | unequal | 0.209 [0.187, 0.234] **anti-conservative** | 0.051 [0.039, 0.065] |
| binary | 0.3 | 100 | equal | 0.184 [0.163, 0.208] **anti-conservative** | 0.049 [0.038, 0.063] |
| binary | 0.3 | 100 | unequal | 0.203 [0.180, 0.227] **anti-conservative** | 0.041 [0.031, 0.054] |
| continuous | 0 | 20 | equal | 0.049 [0.038, 0.062] | 0.048 [0.037, 0.062] |
| continuous | 0 | 20 | unequal | 0.059 [0.046, 0.074] | 0.056 [0.044, 0.071] |
| continuous | 0 | 50 | equal | 0.041 [0.031, 0.054] | 0.049 [0.038, 0.062] |
| continuous | 0 | 50 | unequal | 0.053 [0.042, 0.068] | 0.054 [0.042, 0.069] |
| continuous | 0 | 100 | equal | 0.051 [0.040, 0.066] | 0.051 [0.040, 0.066] |
| continuous | 0 | 100 | unequal | 0.054 [0.042, 0.069] | 0.052 [0.041, 0.067] |
| continuous | 0.1 | 20 | equal | 0.096 [0.080, 0.114] **anti-conservative** | 0.051 [0.040, 0.066] |
| continuous | 0.1 | 20 | unequal | 0.117 [0.099, 0.136] **anti-conservative** | 0.052 [0.041, 0.066] |
| continuous | 0.1 | 50 | equal | 0.105 [0.089, 0.124] **anti-conservative** | 0.050 [0.039, 0.064] |
| continuous | 0.1 | 50 | unequal | 0.103 [0.087, 0.122] **anti-conservative** | 0.053 [0.042, 0.068] |
| continuous | 0.1 | 100 | equal | 0.093 [0.078, 0.112] **anti-conservative** | 0.050 [0.038, 0.064] |
| continuous | 0.1 | 100 | unequal | 0.114 [0.097, 0.134] **anti-conservative** | 0.054 [0.043, 0.069] |
| continuous | 0.3 | 20 | equal | 0.183 [0.162, 0.207] **anti-conservative** | 0.049 [0.038, 0.063] |
| continuous | 0.3 | 20 | unequal | 0.207 [0.185, 0.231] **anti-conservative** | 0.049 [0.038, 0.063] |
| continuous | 0.3 | 50 | equal | 0.183 [0.162, 0.206] **anti-conservative** | 0.056 [0.044, 0.071] |
| continuous | 0.3 | 50 | unequal | 0.201 [0.179, 0.225] **anti-conservative** | 0.045 [0.034, 0.059] |
| continuous | 0.3 | 100 | equal | 0.186 [0.165, 0.209] **anti-conservative** | 0.059 [0.047, 0.075] |
| continuous | 0.3 | 100 | unequal | 0.222 [0.199, 0.246] **anti-conservative** | 0.044 [0.034, 0.058] |

### Power with the design effect (paired continuous, clusters of 5, effect 0.1, SD 0.25)

| ICC | n rule | DEFF | items | clusters | predicted | cluster sign-flip | cluster CI excludes 0 |
|---|---|---|---|---|---|---|---|
| 0 | DEFF-inflated | 1.00 | 50 | 10 | 0.80 | 0.718 [0.691, 0.743] **optimistic** | 0.831 [0.808, 0.851] |
| 0 | naive (no DEFF) | 1.00 | 50 | 10 | - | 0.698 [0.671, 0.724] | 0.829 [0.806, 0.849] |
| 0.1 | DEFF-inflated | 1.40 | 70 | 14 | 0.80 | 0.746 [0.720, 0.770] **optimistic** | 0.816 [0.793, 0.837] |
| 0.1 | naive (no DEFF) | 1.40 | 50 | 10 | - | 0.550 [0.522, 0.579] | 0.703 [0.676, 0.729] |
| 0.3 | DEFF-inflated | 2.20 | 110 | 22 | 0.80 | 0.756 [0.730, 0.780] **optimistic** | 0.811 [0.788, 0.833] |
| 0.3 | naive (no DEFF) | 2.20 | 50 | 10 | - | 0.405 [0.377, 0.434] | 0.556 [0.528, 0.585] |

### Claims under the pre-registered rules

- Claim 1 (naive undercovers), supported: the naive normal interval is flagged `undercovers` in 48 of 48 cells with ICC > 0, the item bootstrap in 48 (rule: at least 90% of cells for both).
- Claim 2 (clustered is calibrated), clustered-SE normal: not supported. Flagged `undercovers` in 13 of 48 cells with at least 50 clusters (lowest point coverage 0.924).
-   Not binding, fewer than 50 clusters: clustered-SE normal flagged in 21 of 24 cells (lowest point coverage 0.911).
-   Control (ICC 0, at least 50 clusters): clustered-SE normal flagged in 3 of 16 cells.
- Claim 2 (clustered is calibrated), cluster bootstrap: not supported. Flagged `undercovers` in 12 of 48 cells with at least 50 clusters (lowest point coverage 0.924).
-   Not binding, fewer than 50 clusters: cluster bootstrap flagged in 17 of 24 cells (lowest point coverage 0.915).
-   Control (ICC 0, at least 50 clusters): cluster bootstrap flagged in 3 of 16 cells.
- Claim 3a (item sign-flip is anti-conservative under clustering), supported: flagged in 24 of 24 paired cells with ICC > 0.
- Claim 3b (cluster sign-flip is valid), supported: anti-conservative in 0 of 36 paired cells.
- Claim 4 (power at the design-effect n), ICC 0, n = 50 items (10 clusters): cluster sign-flip power 0.718 [0.691, 0.743], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.1, n = 70 items (14 clusters): cluster sign-flip power 0.746 [0.720, 0.770], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.3, n = 110 items (22 clusters): cluster sign-flip power 0.756 [0.730, 0.780], optimistic.
- SE ratio (descriptive): mean clustered/naive SE over sqrt(DEFF) is 0.981 (range 0.951 to 0.996) over 72 cells.

### Small-cluster correction (`docs/protocol-cluster-small-sample.md`)

- CR1 small-cluster correction: flagged `undercovers` in 2 of 72 cells against 34 for the uncorrected clustered normal interval on the same replications; flagged `overcovers` in 0.
-   fewer than 50 clusters (24 cells): flagged 1 corrected vs 21 uncorrected; point coverage 0.934 to 0.962 corrected, 0.911 to 0.944 uncorrected.
-   at least 50 clusters (48 cells): flagged 1 corrected vs 13 uncorrected; point coverage 0.935 to 0.959 corrected, 0.924 to 0.950 uncorrected.
-   ICC 0 (24 cells): flagged 1 corrected vs 10 uncorrected; point coverage 0.935 to 0.962 corrected, 0.922 to 0.950 uncorrected.
- Rule for this seed (F1 <= 16, F1 <= F0 / 2, no `overcovers`): met (F0 = 34, F1 = 2, O1 = 0). Adoption needs 'met' on all three final seeds.

### Every flagged cell

- undercovers: cluster_normal coverage mean binary ICC=0 C=20 equal: 0.929 [0.913, 0.943]
- undercovers: cluster_normal coverage mean binary ICC=0 C=20 unequal: 0.930 [0.914, 0.943]
- undercovers: cluster_bootstrap coverage mean binary ICC=0 C=20 unequal: 0.929 [0.913, 0.942]
- undercovers: naive coverage mean binary ICC=0.1 C=20 equal: 0.908 [0.890, 0.923]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 equal: 0.923 [0.907, 0.937]
- undercovers: naive coverage mean binary ICC=0.1 C=20 unequal: 0.885 [0.865, 0.902]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.901 [0.882, 0.917]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=20 unequal: 0.926 [0.910, 0.940]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.928 [0.912, 0.942]
- undercovers: naive coverage mean binary ICC=0.1 C=50 equal: 0.891 [0.872, 0.908]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 equal: 0.888 [0.869, 0.905]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=50 equal: 0.936 [0.921, 0.949]
- undercovers: naive coverage mean binary ICC=0.1 C=50 unequal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 unequal: 0.892 [0.873, 0.909]
- undercovers: naive coverage mean binary ICC=0.1 C=100 equal: 0.900 [0.882, 0.916]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 equal: 0.905 [0.887, 0.921]
- undercovers: naive coverage mean binary ICC=0.1 C=100 unequal: 0.897 [0.879, 0.914]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 unequal: 0.901 [0.882, 0.917]
- undercovers: naive coverage mean binary ICC=0.3 C=20 equal: 0.814 [0.790, 0.835]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 equal: 0.836 [0.813, 0.856]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 equal: 0.924 [0.907, 0.938]
- undercovers: naive coverage mean binary ICC=0.3 C=20 unequal: 0.774 [0.750, 0.798]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.791 [0.767, 0.814]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 unequal: 0.911 [0.893, 0.926]
- undercovers: cluster_normal_cr1 coverage mean binary ICC=0.3 C=20 unequal: 0.934 [0.918, 0.947]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.920 [0.903, 0.935]
- undercovers: naive coverage mean binary ICC=0.3 C=50 equal: 0.810 [0.786, 0.832]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 equal: 0.808 [0.784, 0.830]
- undercovers: naive coverage mean binary ICC=0.3 C=50 unequal: 0.790 [0.766, 0.813]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 unequal: 0.792 [0.768, 0.815]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=50 unequal: 0.936 [0.920, 0.949]
- undercovers: naive coverage mean binary ICC=0.3 C=100 equal: 0.814 [0.790, 0.835]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 equal: 0.820 [0.796, 0.841]
- undercovers: naive coverage mean binary ICC=0.3 C=100 unequal: 0.772 [0.747, 0.795]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 unequal: 0.774 [0.749, 0.797]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=20 unequal: 0.930 [0.914, 0.944]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: naive coverage mean continuous ICC=0 C=50 unequal: 0.932 [0.917, 0.946]
- undercovers: item_bootstrap coverage mean continuous ICC=0 C=50 unequal: 0.930 [0.914, 0.944]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=50 unequal: 0.924 [0.907, 0.938]
- undercovers: cluster_normal_cr1 coverage mean continuous ICC=0 C=50 unequal: 0.935 [0.919, 0.948]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=50 unequal: 0.924 [0.908, 0.938]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=100 equal: 0.936 [0.921, 0.949]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 equal: 0.912 [0.895, 0.927]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 equal: 0.912 [0.894, 0.927]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 unequal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.891 [0.872, 0.908]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.928 [0.912, 0.942]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 equal: 0.905 [0.887, 0.921]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 equal: 0.906 [0.888, 0.922]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=50 equal: 0.937 [0.922, 0.950]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 unequal: 0.890 [0.871, 0.907]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.890 [0.871, 0.907]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=50 unequal: 0.935 [0.920, 0.948]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.930 [0.914, 0.944]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 equal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 equal: 0.892 [0.873, 0.909]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 unequal: 0.894 [0.875, 0.910]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 unequal: 0.892 [0.873, 0.909]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 equal: 0.801 [0.778, 0.823]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.804 [0.781, 0.826]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 equal: 0.933 [0.918, 0.946]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.928 [0.912, 0.942]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 unequal: 0.771 [0.746, 0.794]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.775 [0.750, 0.798]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 unequal: 0.919 [0.902, 0.933]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.921 [0.904, 0.935]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 equal: 0.811 [0.787, 0.833]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 equal: 0.813 [0.790, 0.834]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 unequal: 0.786 [0.762, 0.809]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 unequal: 0.784 [0.760, 0.807]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=50 unequal: 0.936 [0.920, 0.949]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=50 unequal: 0.932 [0.917, 0.946]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 equal: 0.802 [0.779, 0.824]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 equal: 0.799 [0.775, 0.821]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=100 equal: 0.934 [0.918, 0.947]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=100 equal: 0.930 [0.914, 0.944]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 unequal: 0.803 [0.779, 0.825]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 unequal: 0.798 [0.774, 0.820]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 equal: 0.928 [0.912, 0.942]
- undercovers: cluster_bootstrap coverage paired binary ICC=0 C=20 equal: 0.936 [0.920, 0.949]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage paired binary ICC=0 C=20 unequal: 0.934 [0.919, 0.947]
- undercovers: cluster_normal coverage paired binary ICC=0 C=50 unequal: 0.934 [0.919, 0.947]
- undercovers: naive coverage paired binary ICC=0.1 C=20 equal: 0.903 [0.885, 0.919]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 equal: 0.912 [0.894, 0.927]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 equal: 0.937 [0.922, 0.950]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 equal: 0.069 [0.055, 0.085]
- undercovers: naive coverage paired binary ICC=0.1 C=20 unequal: 0.891 [0.872, 0.908]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 unequal: 0.903 [0.885, 0.919]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 unequal: 0.929 [0.913, 0.942]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 unequal: 0.077 [0.063, 0.094]
- undercovers: naive coverage paired binary ICC=0.1 C=50 equal: 0.889 [0.870, 0.906]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 equal: 0.892 [0.873, 0.909]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=50 equal: 0.936 [0.920, 0.949]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 equal: 0.091 [0.076, 0.109]
- undercovers: naive coverage paired binary ICC=0.1 C=50 unequal: 0.898 [0.879, 0.914]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 unequal: 0.902 [0.884, 0.918]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 unequal: 0.086 [0.071, 0.104]
- undercovers: naive coverage paired binary ICC=0.1 C=100 equal: 0.885 [0.865, 0.902]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 equal: 0.888 [0.869, 0.905]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=100 equal: 0.936 [0.920, 0.949]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.1 C=100 equal: 0.935 [0.919, 0.948]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 equal: 0.102 [0.085, 0.120]
- undercovers: naive coverage paired binary ICC=0.1 C=100 unequal: 0.883 [0.863, 0.900]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 unequal: 0.888 [0.869, 0.905]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 unequal: 0.103 [0.087, 0.122]
- undercovers: naive coverage paired binary ICC=0.3 C=20 equal: 0.820 [0.796, 0.841]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.827 [0.804, 0.848]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 equal: 0.932 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.937 [0.922, 0.950]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 equal: 0.156 [0.136, 0.178]
- undercovers: naive coverage paired binary ICC=0.3 C=20 unequal: 0.784 [0.759, 0.807]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.796 [0.772, 0.818]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 unequal: 0.918 [0.901, 0.933]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.928 [0.912, 0.942]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 unequal: 0.181 [0.160, 0.204]
- undercovers: naive coverage paired binary ICC=0.3 C=50 equal: 0.805 [0.781, 0.827]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 equal: 0.809 [0.785, 0.831]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 equal: 0.174 [0.153, 0.197]
- undercovers: naive coverage paired binary ICC=0.3 C=50 unequal: 0.771 [0.746, 0.795]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 unequal: 0.775 [0.751, 0.799]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=50 unequal: 0.933 [0.917, 0.946]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 unequal: 0.209 [0.187, 0.234]
- undercovers: naive coverage paired binary ICC=0.3 C=100 equal: 0.801 [0.777, 0.823]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 equal: 0.807 [0.783, 0.829]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 equal: 0.184 [0.163, 0.208]
- undercovers: naive coverage paired binary ICC=0.3 C=100 unequal: 0.780 [0.756, 0.803]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 unequal: 0.786 [0.761, 0.809]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 unequal: 0.203 [0.180, 0.227]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=20 equal: 0.932 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 equal: 0.928 [0.912, 0.942]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=20 unequal: 0.922 [0.905, 0.936]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 unequal: 0.917 [0.900, 0.932]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=50 unequal: 0.937 [0.922, 0.950]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=50 unequal: 0.934 [0.918, 0.947]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 equal: 0.899 [0.881, 0.916]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.902 [0.884, 0.918]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 equal: 0.935 [0.920, 0.948]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.931 [0.915, 0.945]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 equal: 0.096 [0.080, 0.114]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 unequal: 0.879 [0.859, 0.897]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.883 [0.864, 0.901]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 unequal: 0.920 [0.903, 0.935]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.915 [0.898, 0.930]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 unequal: 0.117 [0.099, 0.136]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 equal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 equal: 0.892 [0.873, 0.909]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=50 equal: 0.934 [0.919, 0.947]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 equal: 0.105 [0.089, 0.124]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 unequal: 0.897 [0.878, 0.913]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 unequal: 0.897 [0.878, 0.913]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=50 unequal: 0.936 [0.920, 0.949]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 unequal: 0.103 [0.087, 0.122]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 equal: 0.907 [0.889, 0.922]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 equal: 0.904 [0.886, 0.920]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 equal: 0.093 [0.078, 0.112]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 unequal: 0.885 [0.865, 0.902]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 unequal: 0.881 [0.862, 0.899]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 unequal: 0.114 [0.097, 0.134]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 equal: 0.810 [0.786, 0.832]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.815 [0.792, 0.836]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 equal: 0.934 [0.919, 0.947]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.934 [0.919, 0.947]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 equal: 0.183 [0.162, 0.207]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 unequal: 0.789 [0.765, 0.812]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.789 [0.765, 0.812]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 unequal: 0.925 [0.909, 0.939]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.926 [0.910, 0.940]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 unequal: 0.207 [0.185, 0.231]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 equal: 0.816 [0.792, 0.837]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 equal: 0.816 [0.793, 0.837]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=50 equal: 0.935 [0.920, 0.948]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=50 equal: 0.930 [0.914, 0.944]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 equal: 0.183 [0.162, 0.206]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 unequal: 0.797 [0.773, 0.820]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 unequal: 0.801 [0.778, 0.823]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 unequal: 0.201 [0.179, 0.225]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 equal: 0.814 [0.790, 0.835]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 equal: 0.809 [0.785, 0.831]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=100 equal: 0.937 [0.922, 0.950]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=100 equal: 0.935 [0.920, 0.948]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 equal: 0.186 [0.165, 0.209]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 unequal: 0.777 [0.753, 0.801]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 unequal: 0.769 [0.744, 0.793]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 unequal: 0.222 [0.199, 0.246]
- optimistic: cluster sign-flip power ICC=0 n=50 (deff): 0.718 [0.691, 0.743]
- optimistic: cluster sign-flip power ICC=0 n=50 (naive): 0.698 [0.671, 0.724]
- optimistic: cluster sign-flip power ICC=0.1 n=70 (deff): 0.746 [0.720, 0.770]
- optimistic: cluster sign-flip power ICC=0.1 n=50 (naive): 0.550 [0.522, 0.579]
- optimistic: cluster sign-flip power ICC=0.3 n=110 (deff): 0.756 [0.730, 0.780]
- optimistic: cluster sign-flip power ICC=0.3 n=50 (naive): 0.405 [0.377, 0.434]

Wall time 114 s on 8 worker(s).
