**user**: Maak een voorspelling voor morgen.

**tool call** `list_datasets` `{}`

**tool call** `list_forecast_tasks` `{}`

**tool result** `list_datasets`:
```json
{"outcome":"ok","data":[{"id":3,"name":"Bengtsfors substation","category":"load","rows":35040,"column_count":2,"columns":["timestamp","load_kw"],"first_date":"2024-01-01","last_date":"2024-12-31"},{"id":4,"name":"Innova building","category":"load","rows":68352,"column_count":2,"columns":["timestamp","load_kw"],"first_date":"2024-01-01","last_date":"2024-12-31"}],"units":{"rows":"count"}}
```

**tool result** `list_forecast_tasks`:
```json
{"outcome":"ok","data":[{"id":7,"name":"Bengtsfors load","forecast_type":"electric_demand","dataset_id":3,"target_column":"load_kw","timestamp_column":"timestamp","model_id":"tft","covariates":["temp"],"horizon_hours":40,"test_range":null,"auto_candidates":null,"profiled":true,"latest_experiment_id":null},{"id":8,"name":"Innova load","forecast_type":"electric_demand","dataset_id":4,"target_column":"load_kw","timestamp_column":"timestamp","model_id":"tft","covariates":["temp"],"horizon_hours":40,"test_range":null,"auto_candidates":null,"profiled":true,"latest_experiment_id":null}],"units":{"horizon_hours":"h"}}
```

**assistant**: Ik zie twee bestaande voorspellingstaken die u kunt gebruiken:

1. **Bengtsfors load** - Lastvoorspelling voor Bengtsfors substation (dataset id 3)
2. **Innova load** - Lastvoorspelling voor Innova building (dataset id 4)

Voor welke van deze twee wilt u een voorspelling voor morgen maken?

> harness: `session_outcome` {"reason":"completed","modelId":"qwen3.6:27b-ctx64k"}

