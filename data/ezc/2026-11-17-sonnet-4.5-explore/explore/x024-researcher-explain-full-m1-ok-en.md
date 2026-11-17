**user**: What does the confidence interval on the MAE difference of the latest task 7 run mean in plain terms?

**assistant**: I'll get the latest run information for task 7 to explain the confidence interval on the MAE difference.

**tool call** `get_runs` `{"task_id":7}`

**tool result** `get_runs`:
```json
{"outcome":"ok","data":[{"experiment_id":812,"status":"completed","progress_pct":100,"requested_model":"auto","model_used":"tft","fallback_reason":"nbeats unavailable: weights missing","primary_metric":"mae","metrics":{"mae":6212.8,"rmse":7991.4},"horizon_hours":40,"issue_lead_hours":15,"validation_days":30,"test_range":"2025-01-01..2025-01-30","error":null,"verdict":"better","baseline_column":"Nominatie [kWh]","scored_rows":720,"model_mae":6212.8,"baseline_mae":6576.1,"mae_delta":-363.3,"mae_delta_pct":-5.5,"mae_delta_ci95_low":-702.1,"mae_delta_ci95_high":-45.9,"mae_delta_ci_level_pct":95,"significant":true}],"units":{"horizon_hours":"h","issue_lead_hours":"h","validation_days":"d","progress_pct":"%","scored_rows":"rows","model_mae":"target unit","baseline_mae":"target unit","mae_delta":"target unit","mae_delta_pct":"%","mae_delta_ci95_low":"target unit","mae_delta_ci95_high":"target unit","mae_delta_ci_level_pct":"%"},"hint":"Report the numbers from data only, with the interval and the scored rows."}
```

**assistant**: Based on the latest run of task 7, here's what the confidence interval means in plain terms:

The **MAE difference is -363.3** (in the target's units), meaning the model's forecast error was lower than the baseline nomination by that amount.

The **95% confidence interval is -702.1 to -45.9** (in the target's units).

**What this means:**

This interval tells you about the **uncertainty** in that improvement. Even though we measured an improvement of -363.3 on these particular 720 rows, if we had a different test period, the true improvement might vary. 

The confidence interval says: **We're 95% confident that the real improvement is somewhere between -702.1 and -45.9** (in the target's units). 

In practical terms:
- The model **definitely improved** over the baseline (the entire interval is negative, marked as `significant: true`)
- In the **best case**, the improvement could be as much as -702.1
- In the **worst case**, the improvement might be only -45.9
- Most likely, the true improvement is around the middle estimate of -363.3

The interval is relatively wide because there's natural variability in forecast performance across different time periods, but since it's entirely on the negative (better) side, you can be confident the model genuinely outperforms the baseline.

> harness: `session_outcome` {"reason":"completed","modelId":"claude-sonnet-4-5"}

