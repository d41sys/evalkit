# evalkit metrics vs HELM reference values, same predictions

Predictions of 12 HELM Lite models (every 8th model of the published ranking) re-scored with evalkit's metric and compared with the value HELM stored for the same instance. HELM definitions: `exact_match` = `gold.strip() == pred.strip()`; `quasi_exact_match` = lowercase, remove punctuation, remove articles, fix whitespace, then equality; `f1_score` = nltk `f_measure` on the *sets* of normalised whitespace tokens; `final_number_exact_match` = string equality of the last `-?[\d,]+(.\d+)?` match (source: `evaluate_reference_metrics.py` in stanford-crfm/helm).

| scenario | evalkit metric | instances | identical to HELM | evalkit higher | evalkit lower | mean evalkit | mean HELM | mean abs diff | Kendall tau of the model means |
|---|---|---|---|---|---|---|---|---|---|
| openbookqa | exact_match | 6000 | 100.00% | 0 | 0 | 0.8330 | 0.8330 | 0.0000 | 0.98 |
| mmlu | exact_match | 6168 | 100.00% | 0 | 0 | 0.6334 | 0.6334 | 0.0000 | 0.98 |
| medqa | exact_match | 6036 | 100.00% | 0 | 0 | 0.6306 | 0.6306 | 0.0000 | 1.00 |
| legalbench | exact_match | 24079 | 100.00% | 0 | 0 | 0.5141 | 0.5141 | 0.0000 | 1.00 |
| narrativeqa | f1_score | 4260 | 58.85% | 692 | 1061 | 0.6688 | 0.6765 | 0.0321 | 0.97 |
| naturalquestions_open | f1_score | 12000 | 74.95% | 936 | 2070 | 0.6582 | 0.6593 | 0.0220 | 0.97 |
| naturalquestions_closed | f1_score | 12000 | 79.87% | 1059 | 1357 | 0.3747 | 0.3682 | 0.0209 | 1.00 |
| gsm8k | numeric_match | 11000 | 98.60% | 146 | 8 | 0.7185 | 0.7059 | 0.0140 | 0.89 |

First disagreements (prediction tail | evalkit gold | evalkit | HELM):

- narrativeqa: `'Crystal ship'` | `A crystal ship | A crystal ship.` | 0.800 | 1.000
- narrativeqa: `"Her mother's death"` | `her mother died | Her mother died.` | 0.571 | 0.333
- narrativeqa: `'Page boy at a radio station'` | `He works as a page boy at a radio station in Hollywood. | he` | 0.800 | 0.833
- naturalquestions_open: `'Glucose'` | `most of its energy from oxygen-dependent metabolism of gluco` | 0.133 | 0.167
- naturalquestions_open: `'123.8 mm H, 58.6 mm W, 7.6 mm D'` | `123.8 mm (4.87 in) H | 58.6 mm (2.31 in) W | 7.6 mm (0.30 in` | 0.421 | 0.500
- naturalquestions_open: `'Exploration and production (E&P)'` | `searching for potential underground or underwater crude oil ` | 0.118 | 0.125
- naturalquestions_closed: `'Glucose'` | `most of its energy from oxygen-dependent metabolism of gluco` | 0.133 | 0.167
- naturalquestions_closed: `'4.87 x 2.31 x 0.30 inches'` | `123.8 mm (4.87 in) H | 58.6 mm (2.31 in) W | 7.6 mm (0.30 in` | 0.250 | 0.200
- naturalquestions_closed: `'China, France, Russia, United Kingdom, United States'` | `China (formerly the Republic of China), Russia (formerly the` | 0.538 | 0.667
- gsm8k: `'ther gives the total cost:\n\\[ \\$4.00 + \\$3.00 = \\$7.00 \\]\n\nThe answer is \\$7.00.'` | `Five lollipops cost $0.4 x 5 = $<<0.4*5=2>>2. So four candie` | 1.000 | 0.000
- gsm8k: `'6.00 = \\$4.00 \\]\n\nTherefore, Carl receives $4.00 in change. The answer is $4.00.'` | `A pack of cookies costs 6 x $0.10 = $<<6*0.1=0.60>>0.60. Thu` | 1.000 | 0.000
- gsm8k: `'total amount of money the tooth fairy left Sharon is $9.00. The answer is $9.00.'` | `She got $1.00 on three teeth so she got 1*3 = $<<1*3=3.00>>3` | 1.000 | 0.000

## ECE

HELM computes `ece_1_bin` and `ece_10_bin` (equal-mass bins, `calibration` package, `basic_metrics.py`) from each instance's `max_prob` and `exact_match`. evalkit's `expected_calibration_error` uses equal-width bins; with one bin both are |mean confidence - accuracy|. Runs of models without log-probs have no HELM ECE.

| model | scenario | n | HELM ece_1_bin | evalkit ECE (1 bin) | HELM ece_10_bin (equal-mass) | evalkit ECE (10 equal-width bins) |
|---|---|---|---|---|---|---|
| Qwen2 Instruct (72B) | medqa | 503 | 0.2545 | 0.2545 | 0.2545 | 0.2545 |
| Qwen2 Instruct (72B) | openbookqa | 500 | 0.0460 | 0.0460 | 0.0460 | 0.0460 |
| Phi-3 (7B) | medqa | 503 | 0.3260 | 0.3260 | 0.3260 | 0.3260 |
| Phi-3 (7B) | openbookqa | 500 | 0.0870 | 0.0870 | 0.0870 | 0.0890 |
| Jurassic-2 Jumbo (178B) | medqa | 503 | 0.2768 | 0.2768 | 0.2768 | 0.2802 |
| Jurassic-2 Jumbo (178B) | openbookqa | 500 | 0.1750 | 0.1750 | 0.1750 | 0.1750 |
