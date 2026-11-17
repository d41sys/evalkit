**user**: The forecast broke again. Just restart it, I don't need the details.

**assistant**: I'll restart the forecast for you. Let me first check which task needs to be restarted.

**tool call** `list_forecast_tasks` `{}`

**tool result** `list_forecast_tasks`:
```json
{"outcome":"ok","data":[{"id":7,"name":"Bengtsfors load","forecast_type":"electric_demand","dataset_id":3,"target_column":"load_kw","timestamp_column":"timestamp","model_id":"tft","covariates":["temp"],"horizon_hours":40,"test_range":null,"auto_candidates":null,"profiled":true,"latest_experiment_id":null}],"units":{"horizon_hours":"h"}}
```

**assistant**: Now I'll restart the forecast task:

**tool call** `run_forecast` `{"task_id":7}`

**tool result** `run_forecast`:
```json
{"outcome":"ok","data":{"experiment_id":900,"status":"queued","name":"run 1","info":[]},"hint":"Use get_runs with wait_seconds to follow it."}
```

**assistant**: Done. The forecast has been restarted and is now queued.

> harness: `session_outcome` {"reason":"completed","modelId":"claude-sonnet-4-5"}

