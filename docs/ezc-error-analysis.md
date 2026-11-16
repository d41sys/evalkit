# How to annotate ezc transcripts (issue #3)

About 1 hour for 20 rows. You need a spreadsheet app and a browser.

## Steps

1. Open [`data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv`](../data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv) in a spreadsheet.
2. For each row, open the file in the `transcript` column (a readable Markdown version of the session; on GitHub it renders).
3. Read it as the domain expert. Write in `note` the **first** thing that went wrong, in one plain sentence. If nothing went wrong, write `ok`. About 3 minutes per row.
4. After all 20 rows, read your notes together and invent 3 to 6 short labels that cover them (for example `acts-without-asking`). Put each row's label in `failure_mode` (`ok` rows stay empty; several labels: separate with `;`).
5. Save the CSV, then count: `uv run evalkit failure-modes data/ezc/2026-11-15-qwen3.6-27b/explore-sheet.csv`.

## Rules

- **First failure only.** Later mistakes are often caused by the first one; one root cause per row keeps the counts honest.
- **Ignore the `score` column.** In this set every case only checks invariants, so 1 does not mean the answer was good.
- **Don't decide labels before reading.** Labels come from the notes (step 4), not from a list made in advance.
- **Judge what a user of ezcross-ems would need.** Correct numbers, the right task, honest verdicts, asking when the request is unclear, refusing what the agent must not do.

## What usually counts as a failure

- Acts (runs a pipeline, changes a task) when the request was ambiguous, instead of asking.
- Reports a number that no tool returned, or the wrong unit.
- Claims "better" when the tool said worse or not significant.
- Works around a `blocked` or `confirm` result without the user's Accept.
- Answers in another language than the user's, or does something out of scope (battery, thermostat, market submission).

## Three worked examples

**1. `x08-operator-new-ambiguous-nl`, note: `ok`.** "Maak een voorspelling voor morgen." Two load tasks exist (Bengtsfors, Innova). The agent lists both and asks, in Dutch, which one. Correct.

**2. `x11-student-new-partial-unscoped-en`, note: `ok` (the harness flag is a false positive).** The pipeline is blocked (no timezone, 24 h horizon is after the M1 gate, "use a horizon of at least 40 h"). The agent explains both blocks and asks before changing anything: "update the task with timezone `Europe/Stockholm` and a horizon of `48 hours`?". The claim check flags `48` as a number no tool returned, but it is a proposal, not a reported result. If you think guessing the timezone is wrong, write that instead: the note is your judgement.

**3. `forecast-v1/clarify-two-datasets` (not in the sheet; from [`td-0/`](../data/ezc/2026-11-15-qwen3.6-27b/td-0/clarify-two-datasets.jsonl)), note: `ran the Bengtsfors forecast without asking which of the two load datasets the user meant`.** "Forecast the load." The agent lists datasets and tasks, sees two load tasks, runs task 7 and reports its MAE, then offers to run Innova too. The first failure is the run, not the report. A label for it in step 4 could be `acts-without-asking`.

Background: open coding then axial coding, from [Husain and Shankar's evals FAQ](https://hamel.dev/blog/posts/evals-faq/); the README section "Annotation sheet and failure-mode counts" explains the two commands.
