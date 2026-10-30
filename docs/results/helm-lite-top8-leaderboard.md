# Evaluation Leaderboard

| Rank | Model | Macro Mean | 95% CI | Win Rate | Elo Rating | Bradley-Terry [95% CI] | ECE (15 bins) | Brier | Tasks Evaluated | Tie group |
|------|-------|------------|--------|----------|------------|------------------------|---------------|-------|-----------------|-----------|
| 1 | GPT-4o (2024-05-13) | 0.732 | [0.724, 0.740] | 0.512 | 1090.8 | 1007.5 [1005.1, 1009.7] | 0.500 | 0.250 | 10 | 1 |
| 2 | GPT-4o (2024-08-06) | 0.731 | [0.723, 0.738] | 0.507 | 1084.1 | 1004.5 [1002.3, 1006.8] | 0.500 | 0.250 | 10 | 1 |
| 3 | DeepSeek v3 | 0.730 | [0.723, 0.738] | 0.485 | 832.4 | 991.6 [989.2, 993.3] | 0.500 | 0.250 | 10 | 1 |
| 4 | Claude 3.5 Sonnet (20240620) | 0.721 | [0.713, 0.730] | 0.503 | 916.1 | 1001.2 [998.8, 1003.4] | 0.500 | 0.250 | 10 | 1 |
| 5 | Amazon Nova Pro | 0.719 | [0.710, 0.727] | 0.507 | 949.8 | 1004.1 [1001.7, 1006.6] | 0.500 | 0.250 | 10 | 1 |
| 6 | GPT-4 (0613) | 0.716 | [0.708, 0.724] | 0.489 | 994.2 | 993.3 [991.3, 995.8] | 0.500 | 0.250 | 10 | 1 |
| 7 | Llama 3.1 Instruct Turbo (405B) | 0.709 | [0.701, 0.717] | 0.502 | 1060.9 | 1001.0 [998.4, 1003.9] | 0.500 | 0.250 | 10 | 2 |
| 8 | GPT-4 Turbo (2024-04-09) | 0.708 | [0.699, 0.716] | 0.495 | 1071.8 | 996.9 [994.6, 998.9] | 0.500 | 0.250 | 10 | 2 |

95% CI: stratified bootstrap over tasks; in the 2 task(s) whose rows carry a cluster_id whole clusters are resampled (the same cluster bootstrap `evalkit compare` uses), elsewhere single items.

Bradley-Terry: maximum-likelihood strengths from the per-item pairwise outcomes (ties count as half a win each), on the Elo scale (400 points per factor 10 in odds, mean rating 1000); the interval is a bootstrap over items (whole clusters where rows carry a cluster_id).

Tie group: a model joins the group of the model ranked directly above it unless the paired randomisation test on their per-example differences is resolved (Holm-adjusted p < 0.05 over the adjacent pairs; whole clusters are flipped where rows carry a cluster_id). Models sharing a group are not separated by this data.

## Per-Task Breakdown

| Model | gsm8k | legalbench | math | medqa | mmlu | narrativeqa | naturalquestions_closed | naturalquestions_open | openbookqa | wmt14 |
|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| GPT-4o (2024-05-13) | 0.905 | 0.647 | 0.865 | 0.857 | 0.747 | 0.804 | 0.501 | 0.803 | 0.966 | 0.224 |
| GPT-4o (2024-08-06) | 0.909 | 0.648 | 0.879 | 0.863 | 0.737 | 0.795 | 0.496 | 0.793 | 0.968 | 0.220 |
| DeepSeek v3 | 0.940 | 0.635 | 0.929 | 0.809 | 0.802 | 0.796 | 0.467 | 0.765 | 0.954 | 0.204 |
| Claude 3.5 Sonnet (20240620) | 0.949 | 0.620 | 0.826 | 0.825 | 0.800 | 0.746 | 0.502 | 0.749 | 0.972 | 0.223 |
| Amazon Nova Pro | 0.870 | 0.681 | 0.858 | 0.811 | 0.757 | 0.791 | 0.405 | 0.829 | 0.960 | 0.224 |
| GPT-4 (0613) | 0.932 | 0.662 | 0.840 | 0.815 | 0.733 | 0.768 | 0.457 | 0.790 | 0.960 | 0.203 |
| Llama 3.1 Instruct Turbo (405B) | 0.949 | 0.580 | 0.860 | 0.805 | 0.759 | 0.749 | 0.456 | 0.756 | 0.940 | 0.234 |
| GPT-4 Turbo (2024-04-09) | 0.824 | 0.672 | 0.870 | 0.783 | 0.710 | 0.761 | 0.482 | 0.795 | 0.970 | 0.212 |
