**user**: How do I start forecasting? Make one for me.

**assistant**: I'll help you start forecasting! Let me first check what datasets you have available.

**tool call** `list_datasets` `{}`

**tool result** `list_datasets`:
```json
{"outcome":"ok","data":[],"units":{"rows":"count"}}
```

**assistant**: It looks like you don't have any datasets uploaded yet. To start forecasting, here's what you need:

## Steps to Start Forecasting:

1. **Upload a dataset** - You'll need historical data that includes:
   - A timestamp column
   - A target column (what you want to forecast, like energy demand, solar generation, etc.)
   - Optionally: weather data or other covariates

2. **Create a forecast task** - Once you have data, I can help you:
   - Choose the forecast type (electric demand, PV generation, market price, or heat demand)
   - Configure the task settings (location, horizon, model selection)
   - Set up the forecast

3. **Run the forecast** - Execute the model and get predictions

Would you like me to:
- Explain what data format you need to upload?
- Tell you about the different types of forecasts available?
- Or if you have data ready, you can upload it and let me know!

What would be most helpful for you?

> harness: `session_outcome` {"reason":"completed","modelId":"claude-sonnet-4-5"}

