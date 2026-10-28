## Clustered data (protocol: `docs/protocol-clustered-se.md`)

seed 0; replications 2000 per coverage cell, 2000 per power cell; bootstrap resamples 1000; randomisation draws 2000 (exact enumeration up to 20 nonzero differences or clusters). Intervals are Wilson 99% over replications. Estimators: naive = mean +/- 1.96 s/sqrt(n); item bootstrap = the CI `compare` printed before clusters; clustered normal = mean +/- 1.96 SE_clustered (Miller 2024); cluster bootstrap = percentile interval from resampling clusters. ICC^ is the mean ANOVA estimate; SE ratio is mean clustered/naive SE next to sqrt(DEFF) of the design.

### Coverage of the true value, design `mean` (mean of one model's scores), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.944 [0.929, 0.956] | 0.961 [0.948, 0.971] | 0.935 [0.919, 0.948] **undercovers** | 0.939 [0.924, 0.951] | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.942 [0.926, 0.954] | 0.954 [0.940, 0.965] | 0.917 [0.900, 0.932] **undercovers** | 0.923 [0.907, 0.937] **undercovers** | 0.97 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.958 [0.945, 0.968] | 0.960 [0.947, 0.969] | 0.956 [0.942, 0.966] | 0.962 [0.949, 0.971] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.953 [0.939, 0.963] | 0.952 [0.938, 0.962] | 0.943 [0.928, 0.955] | 0.946 [0.931, 0.958] | 0.99 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.950 [0.935, 0.961] | 0.952 [0.938, 0.962] | 0.950 [0.936, 0.961] | 0.950 [0.936, 0.961] | 1.00 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.962 [0.949, 0.971] | 0.963 [0.950, 0.972] | 0.956 [0.942, 0.966] | 0.956 [0.942, 0.966] | 0.99 | 1.00 |
| binary | 0.1 | 0.10 | 20 | equal | 0.895 [0.877, 0.912] **undercovers** | 0.914 [0.897, 0.929] **undercovers** | 0.921 [0.904, 0.935] **undercovers** | 0.933 [0.918, 0.946] **undercovers** | 1.14 | 1.18 |
| binary | 0.1 | 0.11 | 20 | unequal | 0.890 [0.871, 0.907] **undercovers** | 0.906 [0.888, 0.922] **undercovers** | 0.926 [0.909, 0.940] **undercovers** | 0.931 [0.915, 0.944] **undercovers** | 1.17 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.893 [0.874, 0.910] **undercovers** | 0.890 [0.871, 0.907] **undercovers** | 0.939 [0.924, 0.951] | 0.943 [0.928, 0.955] | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.882 [0.863, 0.900] **undercovers** | 0.888 [0.869, 0.905] **undercovers** | 0.932 [0.916, 0.945] **undercovers** | 0.936 [0.921, 0.949] **undercovers** | 1.20 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.895 [0.877, 0.912] **undercovers** | 0.899 [0.881, 0.916] **undercovers** | 0.948 [0.934, 0.959] | 0.951 [0.936, 0.962] | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.899 [0.880, 0.915] **undercovers** | 0.899 [0.881, 0.916] **undercovers** | 0.948 [0.933, 0.959] | 0.949 [0.935, 0.960] | 1.21 | 1.22 |
| binary | 0.3 | 0.29 | 20 | equal | 0.799 [0.775, 0.821] **undercovers** | 0.831 [0.808, 0.851] **undercovers** | 0.915 [0.898, 0.930] **undercovers** | 0.928 [0.912, 0.942] **undercovers** | 1.44 | 1.48 |
| binary | 0.3 | 0.30 | 20 | unequal | 0.783 [0.758, 0.806] **undercovers** | 0.794 [0.770, 0.817] **undercovers** | 0.915 [0.898, 0.930] **undercovers** | 0.923 [0.906, 0.937] **undercovers** | 1.50 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.809 [0.786, 0.831] **undercovers** | 0.806 [0.782, 0.828] **undercovers** | 0.940 [0.925, 0.952] | 0.946 [0.931, 0.957] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.791 [0.767, 0.813] **undercovers** | 0.794 [0.770, 0.816] **undercovers** | 0.932 [0.917, 0.946] **undercovers** | 0.934 [0.918, 0.947] **undercovers** | 1.54 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.811 [0.788, 0.833] **undercovers** | 0.818 [0.794, 0.839] **undercovers** | 0.952 [0.938, 0.963] | 0.952 [0.938, 0.962] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.801 [0.777, 0.823] **undercovers** | 0.801 [0.777, 0.823] **undercovers** | 0.957 [0.943, 0.967] | 0.956 [0.942, 0.966] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.943 [0.928, 0.955] | 0.945 [0.930, 0.957] | 0.927 [0.911, 0.941] **undercovers** | 0.923 [0.906, 0.937] **undercovers** | 0.98 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.947 [0.933, 0.958] | 0.946 [0.931, 0.958] | 0.930 [0.914, 0.944] **undercovers** | 0.927 [0.911, 0.941] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.943 [0.928, 0.955] | 0.942 [0.927, 0.954] | 0.939 [0.924, 0.951] | 0.936 [0.920, 0.949] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.952 [0.938, 0.962] | 0.951 [0.936, 0.962] | 0.950 [0.935, 0.961] | 0.947 [0.933, 0.958] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.941 [0.926, 0.953] | 0.943 [0.928, 0.955] | 0.939 [0.924, 0.951] | 0.936 [0.920, 0.949] **undercovers** | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.956 [0.943, 0.966] | 0.953 [0.939, 0.964] | 0.951 [0.936, 0.962] | 0.949 [0.934, 0.960] | 0.99 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.900 [0.881, 0.916] **undercovers** | 0.897 [0.879, 0.914] **undercovers** | 0.927 [0.911, 0.941] **undercovers** | 0.923 [0.906, 0.937] **undercovers** | 1.15 | 1.18 |
| continuous | 0.1 | 0.10 | 20 | unequal | 0.899 [0.880, 0.915] **undercovers** | 0.902 [0.884, 0.918] **undercovers** | 0.931 [0.915, 0.945] **undercovers** | 0.932 [0.917, 0.946] **undercovers** | 1.17 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.897 [0.879, 0.914] **undercovers** | 0.898 [0.879, 0.914] **undercovers** | 0.934 [0.918, 0.947] **undercovers** | 0.931 [0.915, 0.944] **undercovers** | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.891 [0.872, 0.908] **undercovers** | 0.886 [0.866, 0.903] **undercovers** | 0.932 [0.916, 0.945] **undercovers** | 0.933 [0.917, 0.946] **undercovers** | 1.20 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.900 [0.882, 0.916] **undercovers** | 0.896 [0.877, 0.912] **undercovers** | 0.942 [0.926, 0.954] | 0.937 [0.922, 0.950] **undercovers** | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.904 [0.886, 0.920] **undercovers** | 0.903 [0.885, 0.919] **undercovers** | 0.954 [0.940, 0.965] | 0.954 [0.940, 0.964] | 1.21 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.811 [0.788, 0.833] **undercovers** | 0.816 [0.792, 0.837] **undercovers** | 0.930 [0.914, 0.943] **undercovers** | 0.925 [0.909, 0.939] **undercovers** | 1.44 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.788 [0.764, 0.811] **undercovers** | 0.790 [0.766, 0.813] **undercovers** | 0.927 [0.911, 0.941] **undercovers** | 0.925 [0.908, 0.939] **undercovers** | 1.49 | 1.56 |
| continuous | 0.3 | 0.30 | 50 | equal | 0.811 [0.787, 0.833] **undercovers** | 0.811 [0.787, 0.833] **undercovers** | 0.946 [0.931, 0.957] | 0.944 [0.929, 0.956] | 1.47 | 1.48 |
| continuous | 0.3 | 0.29 | 50 | unequal | 0.803 [0.780, 0.825] **undercovers** | 0.800 [0.776, 0.822] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 1.53 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.808 [0.784, 0.830] **undercovers** | 0.804 [0.781, 0.826] **undercovers** | 0.948 [0.934, 0.959] | 0.945 [0.930, 0.957] | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.786 [0.762, 0.809] **undercovers** | 0.783 [0.759, 0.806] **undercovers** | 0.944 [0.929, 0.955] | 0.943 [0.928, 0.955] | 1.55 | 1.56 |

### Coverage of the true value, design `paired` (paired difference A - B (truth 0)), nominal 0.95

| kind | ICC | ICC^ | clusters | sizes | naive | item bootstrap | clustered normal | cluster bootstrap | SE ratio | sqrt(DEFF) |
|---|---|---|---|---|---|---|---|---|---|---|
| binary | 0 | 0.03 | 20 | equal | 0.955 [0.941, 0.965] | 0.958 [0.944, 0.968] | 0.936 [0.921, 0.949] **undercovers** | 0.943 [0.928, 0.955] | 0.97 | 1.00 |
| binary | 0 | 0.03 | 20 | unequal | 0.938 [0.923, 0.950] | 0.943 [0.928, 0.955] | 0.924 [0.908, 0.938] **undercovers** | 0.935 [0.920, 0.948] **undercovers** | 0.96 | 1.00 |
| binary | 0 | 0.02 | 50 | equal | 0.950 [0.935, 0.961] | 0.952 [0.938, 0.963] | 0.944 [0.929, 0.955] | 0.949 [0.934, 0.960] | 0.99 | 1.00 |
| binary | 0 | 0.02 | 50 | unequal | 0.950 [0.935, 0.961] | 0.950 [0.936, 0.961] | 0.939 [0.923, 0.951] | 0.943 [0.928, 0.955] | 0.98 | 1.00 |
| binary | 0 | 0.01 | 100 | equal | 0.951 [0.937, 0.962] | 0.954 [0.940, 0.965] | 0.951 [0.937, 0.962] | 0.955 [0.941, 0.965] | 1.00 | 1.00 |
| binary | 0 | 0.01 | 100 | unequal | 0.952 [0.938, 0.962] | 0.953 [0.939, 0.963] | 0.949 [0.935, 0.960] | 0.949 [0.935, 0.960] | 0.99 | 1.00 |
| binary | 0.1 | 0.10 | 20 | equal | 0.886 [0.867, 0.904] **undercovers** | 0.891 [0.872, 0.908] **undercovers** | 0.922 [0.905, 0.936] **undercovers** | 0.931 [0.915, 0.944] **undercovers** | 1.15 | 1.18 |
| binary | 0.1 | 0.10 | 20 | unequal | 0.878 [0.858, 0.896] **undercovers** | 0.894 [0.875, 0.910] **undercovers** | 0.920 [0.903, 0.935] **undercovers** | 0.928 [0.912, 0.942] **undercovers** | 1.17 | 1.22 |
| binary | 0.1 | 0.10 | 50 | equal | 0.888 [0.869, 0.905] **undercovers** | 0.892 [0.873, 0.909] **undercovers** | 0.935 [0.919, 0.948] **undercovers** | 0.939 [0.923, 0.951] | 1.17 | 1.18 |
| binary | 0.1 | 0.10 | 50 | unequal | 0.893 [0.874, 0.910] **undercovers** | 0.894 [0.875, 0.911] **undercovers** | 0.939 [0.924, 0.951] | 0.943 [0.928, 0.955] | 1.20 | 1.22 |
| binary | 0.1 | 0.10 | 100 | equal | 0.906 [0.888, 0.922] **undercovers** | 0.907 [0.889, 0.922] **undercovers** | 0.956 [0.942, 0.966] | 0.956 [0.943, 0.966] | 1.18 | 1.18 |
| binary | 0.1 | 0.10 | 100 | unequal | 0.894 [0.875, 0.910] **undercovers** | 0.902 [0.884, 0.918] **undercovers** | 0.947 [0.932, 0.958] | 0.948 [0.933, 0.959] | 1.21 | 1.22 |
| binary | 0.3 | 0.30 | 20 | equal | 0.805 [0.782, 0.827] **undercovers** | 0.817 [0.794, 0.838] **undercovers** | 0.929 [0.913, 0.943] **undercovers** | 0.936 [0.921, 0.949] **undercovers** | 1.45 | 1.48 |
| binary | 0.3 | 0.30 | 20 | unequal | 0.774 [0.750, 0.798] **undercovers** | 0.791 [0.767, 0.813] **undercovers** | 0.916 [0.899, 0.931] **undercovers** | 0.924 [0.907, 0.938] **undercovers** | 1.50 | 1.56 |
| binary | 0.3 | 0.30 | 50 | equal | 0.814 [0.791, 0.835] **undercovers** | 0.819 [0.795, 0.840] **undercovers** | 0.944 [0.929, 0.955] | 0.944 [0.929, 0.956] | 1.47 | 1.48 |
| binary | 0.3 | 0.30 | 50 | unequal | 0.791 [0.767, 0.813] **undercovers** | 0.797 [0.773, 0.820] **undercovers** | 0.940 [0.925, 0.952] | 0.945 [0.930, 0.957] | 1.54 | 1.56 |
| binary | 0.3 | 0.30 | 100 | equal | 0.799 [0.775, 0.822] **undercovers** | 0.802 [0.779, 0.824] **undercovers** | 0.935 [0.919, 0.948] **undercovers** | 0.938 [0.923, 0.950] | 1.48 | 1.48 |
| binary | 0.3 | 0.30 | 100 | unequal | 0.792 [0.768, 0.815] **undercovers** | 0.796 [0.772, 0.818] **undercovers** | 0.945 [0.930, 0.957] | 0.943 [0.928, 0.955] | 1.55 | 1.56 |
| continuous | 0 | 0.03 | 20 | equal | 0.952 [0.938, 0.963] | 0.955 [0.941, 0.965] | 0.932 [0.917, 0.946] **undercovers** | 0.925 [0.909, 0.939] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.03 | 20 | unequal | 0.952 [0.938, 0.963] | 0.952 [0.938, 0.963] | 0.933 [0.917, 0.946] **undercovers** | 0.930 [0.914, 0.944] **undercovers** | 0.97 | 1.00 |
| continuous | 0 | 0.02 | 50 | equal | 0.947 [0.933, 0.958] | 0.946 [0.931, 0.958] | 0.939 [0.924, 0.951] | 0.939 [0.923, 0.951] | 0.99 | 1.00 |
| continuous | 0 | 0.02 | 50 | unequal | 0.952 [0.938, 0.963] | 0.951 [0.936, 0.962] | 0.941 [0.926, 0.953] | 0.939 [0.924, 0.951] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | equal | 0.953 [0.939, 0.963] | 0.949 [0.935, 0.960] | 0.950 [0.935, 0.961] | 0.947 [0.932, 0.958] | 0.99 | 1.00 |
| continuous | 0 | 0.01 | 100 | unequal | 0.950 [0.936, 0.961] | 0.950 [0.935, 0.961] | 0.946 [0.931, 0.958] | 0.946 [0.931, 0.957] | 0.99 | 1.00 |
| continuous | 0.1 | 0.10 | 20 | equal | 0.892 [0.873, 0.909] **undercovers** | 0.894 [0.875, 0.910] **undercovers** | 0.924 [0.908, 0.938] **undercovers** | 0.917 [0.900, 0.932] **undercovers** | 1.14 | 1.18 |
| continuous | 0.1 | 0.10 | 20 | unequal | 0.894 [0.875, 0.911] **undercovers** | 0.891 [0.872, 0.908] **undercovers** | 0.931 [0.915, 0.945] **undercovers** | 0.929 [0.913, 0.942] **undercovers** | 1.16 | 1.22 |
| continuous | 0.1 | 0.10 | 50 | equal | 0.897 [0.878, 0.913] **undercovers** | 0.901 [0.883, 0.917] **undercovers** | 0.936 [0.921, 0.949] **undercovers** | 0.931 [0.915, 0.945] **undercovers** | 1.17 | 1.18 |
| continuous | 0.1 | 0.10 | 50 | unequal | 0.885 [0.866, 0.903] **undercovers** | 0.885 [0.866, 0.903] **undercovers** | 0.940 [0.924, 0.952] | 0.939 [0.923, 0.951] | 1.19 | 1.22 |
| continuous | 0.1 | 0.10 | 100 | equal | 0.897 [0.879, 0.914] **undercovers** | 0.898 [0.880, 0.915] **undercovers** | 0.945 [0.930, 0.956] | 0.939 [0.924, 0.951] | 1.18 | 1.18 |
| continuous | 0.1 | 0.10 | 100 | unequal | 0.883 [0.863, 0.900] **undercovers** | 0.882 [0.862, 0.899] **undercovers** | 0.943 [0.928, 0.955] | 0.944 [0.929, 0.955] | 1.21 | 1.22 |
| continuous | 0.3 | 0.29 | 20 | equal | 0.801 [0.778, 0.823] **undercovers** | 0.804 [0.780, 0.826] **undercovers** | 0.923 [0.907, 0.937] **undercovers** | 0.918 [0.901, 0.932] **undercovers** | 1.44 | 1.48 |
| continuous | 0.3 | 0.29 | 20 | unequal | 0.783 [0.759, 0.806] **undercovers** | 0.788 [0.764, 0.811] **undercovers** | 0.921 [0.904, 0.935] **undercovers** | 0.920 [0.903, 0.934] **undercovers** | 1.50 | 1.56 |
| continuous | 0.3 | 0.30 | 50 | equal | 0.817 [0.794, 0.838] **undercovers** | 0.818 [0.795, 0.839] **undercovers** | 0.949 [0.934, 0.960] | 0.948 [0.933, 0.959] | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 50 | unequal | 0.782 [0.757, 0.805] **undercovers** | 0.786 [0.761, 0.809] **undercovers** | 0.945 [0.930, 0.957] | 0.946 [0.931, 0.958] | 1.54 | 1.56 |
| continuous | 0.3 | 0.30 | 100 | equal | 0.817 [0.794, 0.838] **undercovers** | 0.814 [0.790, 0.835] **undercovers** | 0.941 [0.925, 0.953] | 0.938 [0.922, 0.950] | 1.47 | 1.48 |
| continuous | 0.3 | 0.30 | 100 | unequal | 0.790 [0.766, 0.812] **undercovers** | 0.787 [0.763, 0.810] **undercovers** | 0.945 [0.930, 0.956] | 0.942 [0.927, 0.954] | 1.55 | 1.56 |

### Type-I error at alpha = 0.05, paired design (true difference 0)

| kind | ICC | clusters | sizes | item sign-flip | cluster sign-flip |
|---|---|---|---|---|---|
| binary | 0 | 20 | equal | 0.030 [0.022, 0.042] | 0.029 [0.021, 0.041] |
| binary | 0 | 20 | unequal | 0.042 [0.031, 0.055] | 0.037 [0.028, 0.050] |
| binary | 0 | 50 | equal | 0.038 [0.028, 0.051] | 0.038 [0.029, 0.051] |
| binary | 0 | 50 | unequal | 0.043 [0.033, 0.057] | 0.044 [0.034, 0.058] |
| binary | 0 | 100 | equal | 0.041 [0.031, 0.053] | 0.040 [0.030, 0.053] |
| binary | 0 | 100 | unequal | 0.043 [0.033, 0.056] | 0.041 [0.031, 0.053] |
| binary | 0.1 | 20 | equal | 0.088 [0.073, 0.106] **anti-conservative** | 0.043 [0.033, 0.057] |
| binary | 0.1 | 20 | unequal | 0.088 [0.073, 0.106] **anti-conservative** | 0.041 [0.031, 0.054] |
| binary | 0.1 | 50 | equal | 0.097 [0.081, 0.115] **anti-conservative** | 0.049 [0.038, 0.063] |
| binary | 0.1 | 50 | unequal | 0.092 [0.077, 0.110] **anti-conservative** | 0.045 [0.034, 0.059] |
| binary | 0.1 | 100 | equal | 0.082 [0.068, 0.099] **anti-conservative** | 0.037 [0.028, 0.049] |
| binary | 0.1 | 100 | unequal | 0.091 [0.076, 0.109] **anti-conservative** | 0.044 [0.034, 0.058] |
| binary | 0.3 | 20 | equal | 0.160 [0.140, 0.182] **anti-conservative** | 0.042 [0.032, 0.055] |
| binary | 0.3 | 20 | unequal | 0.191 [0.169, 0.215] **anti-conservative** | 0.046 [0.036, 0.060] |
| binary | 0.3 | 50 | equal | 0.165 [0.144, 0.187] **anti-conservative** | 0.041 [0.031, 0.053] |
| binary | 0.3 | 50 | unequal | 0.188 [0.166, 0.211] **anti-conservative** | 0.042 [0.031, 0.055] |
| binary | 0.3 | 100 | equal | 0.185 [0.164, 0.209] **anti-conservative** | 0.054 [0.043, 0.069] |
| binary | 0.3 | 100 | unequal | 0.194 [0.172, 0.217] **anti-conservative** | 0.046 [0.035, 0.060] |
| continuous | 0 | 20 | equal | 0.046 [0.035, 0.060] | 0.050 [0.039, 0.064] |
| continuous | 0 | 20 | unequal | 0.046 [0.036, 0.060] | 0.047 [0.036, 0.061] |
| continuous | 0 | 50 | equal | 0.052 [0.041, 0.066] | 0.051 [0.039, 0.065] |
| continuous | 0 | 50 | unequal | 0.048 [0.037, 0.062] | 0.049 [0.038, 0.063] |
| continuous | 0 | 100 | equal | 0.049 [0.038, 0.062] | 0.048 [0.037, 0.061] |
| continuous | 0 | 100 | unequal | 0.049 [0.038, 0.063] | 0.049 [0.038, 0.063] |
| continuous | 0.1 | 20 | equal | 0.106 [0.090, 0.125] **anti-conservative** | 0.053 [0.042, 0.067] |
| continuous | 0.1 | 20 | unequal | 0.102 [0.086, 0.121] **anti-conservative** | 0.043 [0.033, 0.056] |
| continuous | 0.1 | 50 | equal | 0.101 [0.085, 0.120] **anti-conservative** | 0.059 [0.046, 0.074] |
| continuous | 0.1 | 50 | unequal | 0.114 [0.097, 0.134] **anti-conservative** | 0.052 [0.041, 0.066] |
| continuous | 0.1 | 100 | equal | 0.101 [0.085, 0.120] **anti-conservative** | 0.052 [0.041, 0.066] |
| continuous | 0.1 | 100 | unequal | 0.113 [0.096, 0.133] **anti-conservative** | 0.054 [0.043, 0.069] |
| continuous | 0.3 | 20 | equal | 0.193 [0.171, 0.216] **anti-conservative** | 0.055 [0.043, 0.070] |
| continuous | 0.3 | 20 | unequal | 0.215 [0.193, 0.240] **anti-conservative** | 0.052 [0.041, 0.066] |
| continuous | 0.3 | 50 | equal | 0.177 [0.156, 0.200] **anti-conservative** | 0.048 [0.037, 0.062] |
| continuous | 0.3 | 50 | unequal | 0.216 [0.193, 0.241] **anti-conservative** | 0.044 [0.034, 0.058] |
| continuous | 0.3 | 100 | equal | 0.184 [0.163, 0.208] **anti-conservative** | 0.054 [0.042, 0.069] |
| continuous | 0.3 | 100 | unequal | 0.209 [0.187, 0.234] **anti-conservative** | 0.050 [0.038, 0.064] |

### Power with the design effect (paired continuous, clusters of 5, effect 0.1, SD 0.25)

| ICC | n rule | DEFF | items | clusters | predicted | cluster sign-flip | cluster CI excludes 0 |
|---|---|---|---|---|---|---|---|
| 0 | DEFF-inflated | 1.00 | 50 | 10 | 0.80 | 0.701 [0.673, 0.726] **optimistic** | 0.817 [0.793, 0.838] |
| 0 | naive (no DEFF) | 1.00 | 50 | 10 | - | 0.710 [0.683, 0.735] | 0.839 [0.817, 0.859] |
| 0.1 | DEFF-inflated | 1.40 | 70 | 14 | 0.80 | 0.752 [0.727, 0.776] **optimistic** | 0.826 [0.803, 0.847] |
| 0.1 | naive (no DEFF) | 1.40 | 50 | 10 | - | 0.571 [0.542, 0.599] | 0.722 [0.695, 0.747] |
| 0.3 | DEFF-inflated | 2.20 | 110 | 22 | 0.80 | 0.758 [0.733, 0.782] **optimistic** | 0.811 [0.788, 0.833] |
| 0.3 | naive (no DEFF) | 2.20 | 50 | 10 | - | 0.386 [0.358, 0.414] | 0.523 [0.495, 0.552] |

### Claims under the pre-registered rules

- Claim 1 (naive undercovers), supported: the naive normal interval is flagged `undercovers` in 48 of 48 cells with ICC > 0, the item bootstrap in 48 (rule: at least 90% of cells for both).
- Claim 2 (clustered is calibrated), clustered-SE normal: approximately supported. Flagged `undercovers` in 8 of 48 cells with at least 50 clusters (lowest point coverage 0.932).
-   Not binding, fewer than 50 clusters: clustered-SE normal flagged in 24 of 24 cells (lowest point coverage 0.915).
-   Control (ICC 0, at least 50 clusters): clustered-SE normal flagged in 0 of 16 cells.
- Claim 2 (clustered is calibrated), cluster bootstrap: approximately supported. Flagged `undercovers` in 9 of 48 cells with at least 50 clusters (lowest point coverage 0.931).
-   Not binding, fewer than 50 clusters: cluster bootstrap flagged in 22 of 24 cells (lowest point coverage 0.917).
-   Control (ICC 0, at least 50 clusters): cluster bootstrap flagged in 2 of 16 cells.
- Claim 3a (item sign-flip is anti-conservative under clustering), supported: flagged in 24 of 24 paired cells with ICC > 0.
- Claim 3b (cluster sign-flip is valid), supported: anti-conservative in 0 of 36 paired cells.
- Claim 4 (power at the design-effect n), ICC 0, n = 50 items (10 clusters): cluster sign-flip power 0.701 [0.673, 0.726], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.1, n = 70 items (14 clusters): cluster sign-flip power 0.752 [0.727, 0.776], optimistic.
- Claim 4 (power at the design-effect n), ICC 0.3, n = 110 items (22 clusters): cluster sign-flip power 0.758 [0.733, 0.782], optimistic.
- SE ratio (descriptive): mean clustered/naive SE over sqrt(DEFF) is 0.982 (range 0.952 to 0.996) over 72 cells.

### Every flagged cell

- undercovers: cluster_normal coverage mean binary ICC=0 C=20 equal: 0.935 [0.919, 0.948]
- undercovers: cluster_normal coverage mean binary ICC=0 C=20 unequal: 0.917 [0.900, 0.932]
- undercovers: cluster_bootstrap coverage mean binary ICC=0 C=20 unequal: 0.923 [0.907, 0.937]
- undercovers: naive coverage mean binary ICC=0.1 C=20 equal: 0.895 [0.877, 0.912]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 equal: 0.914 [0.897, 0.929]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=20 equal: 0.921 [0.904, 0.935]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=20 equal: 0.933 [0.918, 0.946]
- undercovers: naive coverage mean binary ICC=0.1 C=20 unequal: 0.890 [0.871, 0.907]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.906 [0.888, 0.922]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=20 unequal: 0.926 [0.909, 0.940]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=20 unequal: 0.931 [0.915, 0.944]
- undercovers: naive coverage mean binary ICC=0.1 C=50 equal: 0.893 [0.874, 0.910]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 equal: 0.890 [0.871, 0.907]
- undercovers: naive coverage mean binary ICC=0.1 C=50 unequal: 0.882 [0.863, 0.900]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=50 unequal: 0.888 [0.869, 0.905]
- undercovers: cluster_normal coverage mean binary ICC=0.1 C=50 unequal: 0.932 [0.916, 0.945]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.1 C=50 unequal: 0.936 [0.921, 0.949]
- undercovers: naive coverage mean binary ICC=0.1 C=100 equal: 0.895 [0.877, 0.912]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 equal: 0.899 [0.881, 0.916]
- undercovers: naive coverage mean binary ICC=0.1 C=100 unequal: 0.899 [0.880, 0.915]
- undercovers: item_bootstrap coverage mean binary ICC=0.1 C=100 unequal: 0.899 [0.881, 0.916]
- undercovers: naive coverage mean binary ICC=0.3 C=20 equal: 0.799 [0.775, 0.821]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 equal: 0.831 [0.808, 0.851]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 equal: 0.915 [0.898, 0.930]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=20 equal: 0.928 [0.912, 0.942]
- undercovers: naive coverage mean binary ICC=0.3 C=20 unequal: 0.783 [0.758, 0.806]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.794 [0.770, 0.817]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=20 unequal: 0.915 [0.898, 0.930]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=20 unequal: 0.923 [0.906, 0.937]
- undercovers: naive coverage mean binary ICC=0.3 C=50 equal: 0.809 [0.786, 0.831]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 equal: 0.806 [0.782, 0.828]
- undercovers: naive coverage mean binary ICC=0.3 C=50 unequal: 0.791 [0.767, 0.813]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=50 unequal: 0.794 [0.770, 0.816]
- undercovers: cluster_normal coverage mean binary ICC=0.3 C=50 unequal: 0.932 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage mean binary ICC=0.3 C=50 unequal: 0.934 [0.918, 0.947]
- undercovers: naive coverage mean binary ICC=0.3 C=100 equal: 0.811 [0.788, 0.833]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 equal: 0.818 [0.794, 0.839]
- undercovers: naive coverage mean binary ICC=0.3 C=100 unequal: 0.801 [0.777, 0.823]
- undercovers: item_bootstrap coverage mean binary ICC=0.3 C=100 unequal: 0.801 [0.777, 0.823]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=20 equal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=20 equal: 0.923 [0.906, 0.937]
- undercovers: cluster_normal coverage mean continuous ICC=0 C=20 unequal: 0.930 [0.914, 0.944]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=50 equal: 0.936 [0.920, 0.949]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0 C=100 equal: 0.936 [0.920, 0.949]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 equal: 0.900 [0.881, 0.916]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 equal: 0.897 [0.879, 0.914]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=20 equal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=20 equal: 0.923 [0.906, 0.937]
- undercovers: naive coverage mean continuous ICC=0.1 C=20 unequal: 0.899 [0.880, 0.915]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.902 [0.884, 0.918]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=20 unequal: 0.931 [0.915, 0.945]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=20 unequal: 0.932 [0.917, 0.946]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 equal: 0.897 [0.879, 0.914]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 equal: 0.898 [0.879, 0.914]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=50 equal: 0.934 [0.918, 0.947]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=50 equal: 0.931 [0.915, 0.944]
- undercovers: naive coverage mean continuous ICC=0.1 C=50 unequal: 0.891 [0.872, 0.908]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.886 [0.866, 0.903]
- undercovers: cluster_normal coverage mean continuous ICC=0.1 C=50 unequal: 0.932 [0.916, 0.945]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=50 unequal: 0.933 [0.917, 0.946]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 equal: 0.900 [0.882, 0.916]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 equal: 0.896 [0.877, 0.912]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.1 C=100 equal: 0.937 [0.922, 0.950]
- undercovers: naive coverage mean continuous ICC=0.1 C=100 unequal: 0.904 [0.886, 0.920]
- undercovers: item_bootstrap coverage mean continuous ICC=0.1 C=100 unequal: 0.903 [0.885, 0.919]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 equal: 0.811 [0.788, 0.833]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.816 [0.792, 0.837]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 equal: 0.930 [0.914, 0.943]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 equal: 0.925 [0.909, 0.939]
- undercovers: naive coverage mean continuous ICC=0.3 C=20 unequal: 0.788 [0.764, 0.811]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.790 [0.766, 0.813]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=20 unequal: 0.927 [0.911, 0.941]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=20 unequal: 0.925 [0.908, 0.939]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 equal: 0.811 [0.787, 0.833]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 equal: 0.811 [0.787, 0.833]
- undercovers: naive coverage mean continuous ICC=0.3 C=50 unequal: 0.803 [0.780, 0.825]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=50 unequal: 0.800 [0.776, 0.822]
- undercovers: cluster_normal coverage mean continuous ICC=0.3 C=50 unequal: 0.935 [0.920, 0.948]
- undercovers: cluster_bootstrap coverage mean continuous ICC=0.3 C=50 unequal: 0.935 [0.920, 0.948]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 equal: 0.808 [0.784, 0.830]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 equal: 0.804 [0.781, 0.826]
- undercovers: naive coverage mean continuous ICC=0.3 C=100 unequal: 0.786 [0.762, 0.809]
- undercovers: item_bootstrap coverage mean continuous ICC=0.3 C=100 unequal: 0.783 [0.759, 0.806]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 equal: 0.936 [0.921, 0.949]
- undercovers: cluster_normal coverage paired binary ICC=0 C=20 unequal: 0.924 [0.908, 0.938]
- undercovers: cluster_bootstrap coverage paired binary ICC=0 C=20 unequal: 0.935 [0.920, 0.948]
- undercovers: naive coverage paired binary ICC=0.1 C=20 equal: 0.886 [0.867, 0.904]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 equal: 0.891 [0.872, 0.908]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 equal: 0.922 [0.905, 0.936]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.1 C=20 equal: 0.931 [0.915, 0.944]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 equal: 0.088 [0.073, 0.106]
- undercovers: naive coverage paired binary ICC=0.1 C=20 unequal: 0.878 [0.858, 0.896]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=20 unequal: 0.894 [0.875, 0.910]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=20 unequal: 0.920 [0.903, 0.935]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.1 C=20 unequal: 0.928 [0.912, 0.942]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=20 unequal: 0.088 [0.073, 0.106]
- undercovers: naive coverage paired binary ICC=0.1 C=50 equal: 0.888 [0.869, 0.905]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 equal: 0.892 [0.873, 0.909]
- undercovers: cluster_normal coverage paired binary ICC=0.1 C=50 equal: 0.935 [0.919, 0.948]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 equal: 0.097 [0.081, 0.115]
- undercovers: naive coverage paired binary ICC=0.1 C=50 unequal: 0.893 [0.874, 0.910]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=50 unequal: 0.894 [0.875, 0.911]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=50 unequal: 0.092 [0.077, 0.110]
- undercovers: naive coverage paired binary ICC=0.1 C=100 equal: 0.906 [0.888, 0.922]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 equal: 0.907 [0.889, 0.922]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 equal: 0.082 [0.068, 0.099]
- undercovers: naive coverage paired binary ICC=0.1 C=100 unequal: 0.894 [0.875, 0.910]
- undercovers: item_bootstrap coverage paired binary ICC=0.1 C=100 unequal: 0.902 [0.884, 0.918]
- anti-conservative: item sign-flip type-I paired binary ICC=0.1 C=100 unequal: 0.091 [0.076, 0.109]
- undercovers: naive coverage paired binary ICC=0.3 C=20 equal: 0.805 [0.782, 0.827]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.817 [0.794, 0.838]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 equal: 0.929 [0.913, 0.943]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 equal: 0.936 [0.921, 0.949]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 equal: 0.160 [0.140, 0.182]
- undercovers: naive coverage paired binary ICC=0.3 C=20 unequal: 0.774 [0.750, 0.798]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.791 [0.767, 0.813]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=20 unequal: 0.916 [0.899, 0.931]
- undercovers: cluster_bootstrap coverage paired binary ICC=0.3 C=20 unequal: 0.924 [0.907, 0.938]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=20 unequal: 0.191 [0.169, 0.215]
- undercovers: naive coverage paired binary ICC=0.3 C=50 equal: 0.814 [0.791, 0.835]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 equal: 0.819 [0.795, 0.840]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 equal: 0.165 [0.144, 0.187]
- undercovers: naive coverage paired binary ICC=0.3 C=50 unequal: 0.791 [0.767, 0.813]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=50 unequal: 0.797 [0.773, 0.820]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=50 unequal: 0.188 [0.166, 0.211]
- undercovers: naive coverage paired binary ICC=0.3 C=100 equal: 0.799 [0.775, 0.822]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 equal: 0.802 [0.779, 0.824]
- undercovers: cluster_normal coverage paired binary ICC=0.3 C=100 equal: 0.935 [0.919, 0.948]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 equal: 0.185 [0.164, 0.209]
- undercovers: naive coverage paired binary ICC=0.3 C=100 unequal: 0.792 [0.768, 0.815]
- undercovers: item_bootstrap coverage paired binary ICC=0.3 C=100 unequal: 0.796 [0.772, 0.818]
- anti-conservative: item sign-flip type-I paired binary ICC=0.3 C=100 unequal: 0.194 [0.172, 0.217]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=20 equal: 0.932 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 equal: 0.925 [0.909, 0.939]
- undercovers: cluster_normal coverage paired continuous ICC=0 C=20 unequal: 0.933 [0.917, 0.946]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0 C=20 unequal: 0.930 [0.914, 0.944]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 equal: 0.892 [0.873, 0.909]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.894 [0.875, 0.910]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 equal: 0.924 [0.908, 0.938]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 equal: 0.917 [0.900, 0.932]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 equal: 0.106 [0.090, 0.125]
- undercovers: naive coverage paired continuous ICC=0.1 C=20 unequal: 0.894 [0.875, 0.911]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.891 [0.872, 0.908]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=20 unequal: 0.931 [0.915, 0.945]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=20 unequal: 0.929 [0.913, 0.942]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=20 unequal: 0.102 [0.086, 0.121]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 equal: 0.897 [0.878, 0.913]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 equal: 0.901 [0.883, 0.917]
- undercovers: cluster_normal coverage paired continuous ICC=0.1 C=50 equal: 0.936 [0.921, 0.949]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.1 C=50 equal: 0.931 [0.915, 0.945]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 equal: 0.101 [0.085, 0.120]
- undercovers: naive coverage paired continuous ICC=0.1 C=50 unequal: 0.885 [0.866, 0.903]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=50 unequal: 0.885 [0.866, 0.903]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=50 unequal: 0.114 [0.097, 0.134]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 equal: 0.897 [0.879, 0.914]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 equal: 0.898 [0.880, 0.915]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 equal: 0.101 [0.085, 0.120]
- undercovers: naive coverage paired continuous ICC=0.1 C=100 unequal: 0.883 [0.863, 0.900]
- undercovers: item_bootstrap coverage paired continuous ICC=0.1 C=100 unequal: 0.882 [0.862, 0.899]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.1 C=100 unequal: 0.113 [0.096, 0.133]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 equal: 0.801 [0.778, 0.823]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.804 [0.780, 0.826]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 equal: 0.923 [0.907, 0.937]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 equal: 0.918 [0.901, 0.932]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 equal: 0.193 [0.171, 0.216]
- undercovers: naive coverage paired continuous ICC=0.3 C=20 unequal: 0.783 [0.759, 0.806]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.788 [0.764, 0.811]
- undercovers: cluster_normal coverage paired continuous ICC=0.3 C=20 unequal: 0.921 [0.904, 0.935]
- undercovers: cluster_bootstrap coverage paired continuous ICC=0.3 C=20 unequal: 0.920 [0.903, 0.934]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=20 unequal: 0.215 [0.193, 0.240]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 equal: 0.817 [0.794, 0.838]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 equal: 0.818 [0.795, 0.839]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 equal: 0.177 [0.156, 0.200]
- undercovers: naive coverage paired continuous ICC=0.3 C=50 unequal: 0.782 [0.757, 0.805]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=50 unequal: 0.786 [0.761, 0.809]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=50 unequal: 0.216 [0.193, 0.241]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 equal: 0.817 [0.794, 0.838]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 equal: 0.814 [0.790, 0.835]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 equal: 0.184 [0.163, 0.208]
- undercovers: naive coverage paired continuous ICC=0.3 C=100 unequal: 0.790 [0.766, 0.812]
- undercovers: item_bootstrap coverage paired continuous ICC=0.3 C=100 unequal: 0.787 [0.763, 0.810]
- anti-conservative: item sign-flip type-I paired continuous ICC=0.3 C=100 unequal: 0.209 [0.187, 0.234]
- optimistic: cluster sign-flip power ICC=0 n=50 (deff): 0.701 [0.673, 0.726]
- optimistic: cluster sign-flip power ICC=0 n=50 (naive): 0.710 [0.683, 0.735]
- optimistic: cluster sign-flip power ICC=0.1 n=70 (deff): 0.752 [0.727, 0.776]
- optimistic: cluster sign-flip power ICC=0.1 n=50 (naive): 0.571 [0.542, 0.599]
- optimistic: cluster sign-flip power ICC=0.3 n=110 (deff): 0.758 [0.733, 0.782]
- optimistic: cluster sign-flip power ICC=0.3 n=50 (naive): 0.386 [0.358, 0.414]

Wall time 88 s on 8 worker(s).
