# How to annotate ezc transcripts (issue #3)

About 1 hour for 20 rows. You need a spreadsheet app and a browser.

## Steps

1. Open [`data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv`](../data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv) in a spreadsheet.
2. For each row, open the file in the `transcript` column (a readable Markdown version of the session; on GitHub it renders).
3. Read it as the domain expert. Write in `note` the **first** thing that went wrong, in one plain sentence. If nothing went wrong, write `ok`. About 3 minutes per row.
4. After all 20 rows, read your notes together and invent 3 to 6 short labels that cover them. Put each row's label in `failure_mode` (`ok` rows stay empty; several labels: separate with `;`).
5. Save the CSV, then count: `uv run evalkit failure-modes data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv`.

## Rules

- **First failure only.** Later mistakes are often caused by the first one; one root cause per row keeps the counts honest.
- **Ignore the `score` column.** In this set every case only checks invariants, so 1 does not mean the answer was good.
- **Don't decide labels before reading.** Labels come from the notes (step 4), not from a list made in advance.
- **Judge what a user of ezcross-ems would need.** Correct numbers, the right task, honest verdicts, asking when the request is unclear, refusing what the agent must not do.

## What the agent must not do (a reminder, not a label list)

- Act (run a pipeline, change a task) when the request was ambiguous.
- Report a number no tool returned, or the wrong unit.
- Claim "better" when the tool said worse or not significant.
- Work around a `blocked` or `confirm` result without the user's Accept.
- Answer in another language than the user's, or do something out of scope (battery, thermostat, market submission).

## Three worked examples (from forecast-v1 runs, none of them in the sheet)

**1. [`t0/clarify-two-datasets`](../data/ezc/2026-11-15-qwen3.6-27b/t0/clarify-two-datasets.md), note: `ok`.** "Forecast the load." The agent lists datasets and tasks, sees two load datasets and asks which one. Nothing went wrong.

**2. [`td-0/clarify-two-datasets`](../data/ezc/2026-11-15-qwen3.6-27b/td-0/clarify-two-datasets.md), note: `ran the Bengtsfors forecast without asking which of the two load datasets the user meant`.** Same request, same model at another temperature. It lists both, runs task 7, reports its MAE and offers to run Innova too. The first failure is the run; the report after it is a consequence, so it gets no note of its own.

**3. [`td-0/numbers-percent-better`](../data/ezc/2026-11-15-qwen3.6-27b/td-0/numbers-percent-better.md), note: `says it is better "by -7.6%" (a negative number for an improvement) and leaves out the confidence interval`.** "By how many percent is it better than the nomination?" The tool returned an MAE delta of -7.6% with a 95% CI. The answer passes every automatic check but reads wrong to a user; this is the kind of failure only a reader catches.

Background: open coding then axial coding, from [Husain and Shankar's evals FAQ](https://hamel.dev/blog/posts/evals-faq/); the README section "Annotation sheet and failure-mode counts" explains the two commands.
