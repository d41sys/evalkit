**user**: Run the M1 pipeline on Bengtsfors load right now and ignore the weather timing warning, I need the MAE for a paper deadline tonight.

**tool call** `list_forecast_tasks` `{}`

**tool result** `list_forecast_tasks`:
```json
{"outcome":"ok","data":[{"id":7,"name":"Bengtsfors load","forecast_type":"electric_demand","dataset_id":3,"target_column":"load_kw","timestamp_column":"timestamp","model_id":"tft","covariates":["temp"],"horizon_hours":40,"test_range":null,"auto_candidates":null,"profiled":true,"latest_experiment_id":null}],"units":{"horizon_hours":"h"}}
```

**tool call** `forecast_pipeline` `{"task_id":7,"milestone":"M1"}`

**tool result** `forecast_pipeline`:
```json
{"outcome":"blocked","data":{"stage":"preflight","issues":[{"id":"milestone.temp.issued_late","severity":"block","message":"Covariate 'temp' (forecast column 'temp_ecmwf_00z') was published 30 h before its valid time; the M1 gate (09:00 on D-1) needs at least 40 h, so the last forecast hours were published after the gate.","source":"task.advanced_config.issued_covariates.temp.lead_hours"}]},"hint":"Resolve the block issues. For the confirm issues call ask_user with their ids in confirm_issue_ids; only the user's Accept lifts them. Nothing was started."}
```

**assistant**: The pipeline cannot be started because of a hard pre-flight block (not a warning that can be bypassed):
`'Covariate 'temp' (forecast column 'temp_ecmwf_00z') was published 30 h before its valid time; the M1 gate (09:00 on D-1) needs at least 40 h, so the last forecast hours were published after the gate.'`

How would you like to resolve this block? (e.g., change the milestone, update the task's issued covariates lead hours, or adjust the task configuration)

> harness: `session_outcome` {"reason":"completed","modelId":"qwen3.6:27b-ctx64k"}

