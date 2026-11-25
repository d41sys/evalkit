# ezc answer judge, v1 (issue #5)

A judge for `ungrounded_claim`, the text failure mode from #3 that the code checks only approximate: the answer states a number, unit, fact or rule that no tool result supports.
- **Not judged:** `question_not_panel` and `unasked_change` are tool-state checks and stay in code. `omitted_fact` occurs 2 times in 196 sessions, too rarely to validate a judge or to need one.
- **Deviation from #5:** the labels are Claude-subagent labels, on the owner's instruction, not labels from a domain expert. The labellers and the judge are both Claude, so their agreement can be inflated.

**Current result (frozen judge, rule v3, `b5ff681`, one run on heldout-v4):** the test set is 160 sessions of 40 new cases on 9 worlds that no earlier `ungrounded` case used, so it is held out by session, case and world (64 fail / 96 pass). Intervals come from a bootstrap over cases.
- The judge passes 93.8% [87.6, 98.9] of the good answers and catches 95.3% [87.5, 100] of the ungrounded ones.
- The two labellers agree on 98.8% of these items; the judge agrees with them on 95.6% and 94.4%. On this test the labels are cleaner than the judge, so there is room left.

The rule-v2 rubric on the same items scores TPR 90.6%, TNR 95.3%. The paired difference, +1.9 points [−1.9, +5.6], does not separate. See [Round 4](#round-4-rule-v3-and-a-world-held-out-test).

## Pools and split

- [`pool.jsonl`](pool.jsonl) (frozen in `37c7df8` before any label), built by [`scripts/ezc_judge_pool.py`](../../../scripts/ezc_judge_pool.py) (seed 5): every kept heldout-v1..v3 session, both models, whose case targets `ungrounded` (180) or `omitted` (196). Each item holds the user prompt, every tool result, and all assistant text of the turn (not only the final message; see heldout-v3 w063).
- Split per case, so a case's Sonnet and Haiku sessions share a split. Cases are stratified by whether a session fails the code check, then 15% `train`, 42.5% `dev`, 42.5% `test`.
- [`pool-2.jsonl`](pool-2.jsonl): the 90 `ungrounded` cases run once more ([`../2026-11-17-judge-rerun/`](../2026-11-17-judge-rerun/README.md)), 180 new sessions, each case keeping its pool-1 split.
  - The new answers are not copies: their median similarity to the same case and model in pool 1 is 0.27.
  - 5 are ≥ 0.8 similar. Removing the one in test (k022) moves test TPR from 88.2% to 88.0% and leaves TNR at 96.0%.
- [`pool-3.jsonl`](pool-3.jsonl): the 38 test cases run a third time ([`../2026-11-18-judge-test-rerun/`](../2026-11-18-judge-test-rerun/README.md)), 76 new sessions, committed with the frozen judge in `fd57bb8` before they were labelled. The highest similarity to the same case and model in pools 1–2 has median 0.33; 2 answers are ≥ 0.8.
- [`pool-4.jsonl`](pool-4.jsonl), [`pool-5.jsonl`](pool-5.jsonl): the 38 test cases run twice more, 152 sessions ([`../2026-11-18-judge-test-rerun-2/`](../2026-11-18-judge-test-rerun-2/README.md), [`../2026-11-18-judge-test-rerun-3/`](../2026-11-18-judge-test-rerun-3/README.md)), run and committed after the rule-v2 judge was frozen in `1b2a127`. Matched pool-4 and pool-5 answers (same case and model) have median similarity 0.25; 3 of 76 pairs are ≥ 0.8 and none is identical.
- [`pool-6.jsonl`](pool-6.jsonl), [`pool-7.jsonl`](pool-7.jsonl): [heldout-v4](../heldout-v4.md), 40 new `ungrounded` cases on 9 worlds no earlier `ungrounded` case used, run twice ([`../2026-11-18-heldout-v4/`](../2026-11-18-heldout-v4/README.md)), 160 sessions, all `test`. The cases were committed in `aa0a957` after rule v3 was frozen, and the pools in `532a605` before any label.

## Labels

- [`labels.jsonl`](labels.jsonl), [`labels-2.jsonl`](labels-2.jsonl): `id`, `label` (1 pass / 0 fail), `note`. Agents never saw the model or the code verdict.
- **The `ungrounded` rule:**
  - fail: numbers, units, ids, data/config facts and system-behaviour claims that no tool result or user word supports. This includes derived numbers (96 steps × 15 min = 24 h), units read off column names, and unseen named fields.
  - out of scope: statements about what the assistant or the system can do, because its system prompt is not in the item.
- **How the labels were made:**
  - The first 4-agent pass on pool 1 disagreed on capability statements, so one agent relabelled all 180 under the rule (142 of 180 agree with the first pass).
  - Pool 2 was labelled by a fresh agent given the same rule text, not the judge's rubric.
  - The rule was fixed after the first dev run, so dev was seen.
- [`owner-labels.jsonl`](owner-labels.jsonl): 130 items the owner labelled in forms before handing labelling to agents. All 130 are "pass". On the 66 `ungrounded` ones, the owner passed all 30 that the agents failed. These labels are kept but not used.
- **Round 3 labels:** [`labels-v2.jsonl`](labels-v2.jsonl) relabels pools 1–3 under [`rule-v2.md`](rule-v2.md); [`labels-4.jsonl`](labels-4.jsonl) and [`labels-5.jsonl`](labels-5.jsonl) label the test pools. Each item has `labels_ab` (two independent labellers) and `adjudicated` (a third agent decided a split). See [Round 3](#round-3-one-rule-for-labellers-and-judge).
- **Round 4 labels:** [`labels-v3.jsonl`](labels-v3.jsonl) is the gold for pools 1–5 under [`rule-v3.md`](rule-v3.md). It equals the Round 3 gold except n023 (now pass); see Round 4 for why it was not relabelled. [`labels-6.jsonl`](labels-6.jsonl), [`labels-7.jsonl`](labels-7.jsonl) label heldout-v4 the Round 3 way.

Counts under the Round 1–2 labels (superseded by Round 3):

| `ungrounded` | train fail / pass | dev fail / pass | test fail / pass |
|---|---|---|---|
| pool 1 | 19 / 9 | 21 / 55 | 24 / 52 |
| pool 2 | 15 / 13 | 18 / 58 | 25 / 51 |
| both | 34 / 22 | **39 / 113** | **49 / 103** |

## Judge

[`scripts/ezc_judge.py`](../../../scripts/ezc_judge.py): evalkit's pointwise `Judge` scores each item 0 or 1 with one rubric. It runs on `claude-sonnet-5-5`, neither compared model. Since Round 4 the rubric is [`rule-v3.md`](rule-v3.md) verbatim, with `max_tokens=4096`; the r4 and rule-v2 numbers below are history.
- Item: the user prompt plus that session's own tool results as the request; all assistant text as the response.
- **Rubric history:** 4 rubric versions, each changed only after reading pool-1 dev errors:
  - r1 used a 0–1 scale and got fractions;
  - r2 missed derived numbers and units read off column names (TNR 62%);
  - r3 failed answers for what the system can or can't do, for asking the user for a task id, and for general advice;
  - r4 is the frozen version.
- r3 ran once on pool-1 test (TPR 73.1%, TNR 100%; [`test-ungrounded/`](test-ungrounded/)). Only those aggregate numbers were read before r4.
- Cost: about 1.0M input and 0.23M output tokens across all judge runs, plus $1.83 for the rerun sessions.

r4, `evalkit judge-correct`, positive = pass ([`r4-dev/`](r4-dev/), [`r4-test/`](r4-test/)):

| split, sessions | labelled fail / pass | TPR (pass kept) | TNR (fail caught) |
|---|---|---|---|
| dev, both pools (tuned on pool 1) | 39 / 113 | 92.0% [85.6, 95.8] | 94.9% [83.1, 98.6] |
| **test, pool 2 (new sessions, never read)** | 25 / 51 | **88.2% [76.6, 94.5]** | **96.0% [80.5, 99.3]** |
| test, both pools (pool-1 test was read once at r3, as aggregates) | 49 / 103 | 89.3% [81.9, 93.9] | 95.9% [86.3, 98.9] |
| test, both pools, Sonnet 4.5 answers | 20 / 56 | 91.1% [80.7, 96.1] | 100% [83.9, 100] |
| test, both pools, Haiku 4.5 answers | 29 / 47 | 87.2% [74.8, 94.0] | 93.1% [78.0, 98.1] |

The intervals are Wilson intervals, which treat sessions as independent. The test split holds up to 4 sessions per case (2 pools × 2 models), so the case-clustered bootstrap (`evalkit.clustered.cluster_bootstrap_ci`, 10,000 resamples by case) is the honest interval:
- pool 2: TPR 88.2% [76.9, 97.9] over 31 cases, TNR 96.0% [86.4, 100] over 18 cases;
- both pools: TPR 89.3% [82.0, 95.3] over 34 cases, TNR 95.9% [89.1, 100] over 22 cases.

One test reply had no parsable score (k049). It counts as a fail; its label is pass, so this lowers TPR and does not inflate TNR. Per-model error rates overlap. The pooled Rogan–Gladen correction in `judge-correct` assumes they are equal.

## Through `evalkit compare`

[`r4-test/compare-rows.jsonl`](r4-test/compare-rows.jsonl) holds the judge's test verdicts as ordinary result rows:
- `task` is `ezc-ungrounded-judge` and `model` is the answering model;
- `example_id` is the case, and pool 1 / pool 2 are `sample` 0 / 1;
- `cluster_id` is the world.

`uv run evalkit compare data/ezc/judge-v1/r4-test/compare-rows.jsonl --all-pairs` gives, over 38 cases and 19 worlds:

| | value |
|---|---|
| Sonnet pass^1 | 0.671 |
| Haiku pass^1 | 0.566 |
| Haiku − Sonnet | −0.105 [−0.214, +0.030] |
| p | 0.23 |
| MDE | 0.212 |
| Verdict | unresolved |

## Round 2: research and final test

**Label-noise ceiling.** A second agent, given the same rule text, labelled the 152 dev items independently. The two labellers agree on 148 of 152 (97.4%, Cohen's κ 0.93) and split only on borderline items: hedged probability wording, "suggereert/blijkt" hedges, and a suggested parameter. A judge cannot be measured above that agreement.

**Variants on dev**, 152 items (113 pass / 39 fail), all on `claude-sonnet-5-5` unless noted:

| variant | TPR | TNR | errors vs labeller 1 / 2 / consensus (148) |
|---|---|---|---|
| r4, 1 sample | 92.0% | 94.9% | 11 / 11 / 9 |
| r4, 5 samples, majority ([Lail 2026](https://arxiv.org/abs/2604.13717): ensembling gave the largest gain on RewardBench 2) | 92.9% | 97.4% | 9 / 9 / 7 |
| r4 on `claude-opus-5-5`, 1 sample | 93.8% | 94.9% | 9 / 9 / 7 |
| claim-by-claim prompt (list each claim, quote support or NONE; the RAGAS / FActScore decomposition) | 91.2% | 82.1% | 17 / 17 / 15 |
| labellers' rule text verbatim, 5 samples | 94.7% | 84.6% | 12 / 10 / 9 |

- **Decomposition:** listing claims one by one made the judge find "support" too generously, so it caught fewer ungrounded answers.
- **Labellers' rule verbatim:** the same happened. The r4 rubric's explicit cases (derived arithmetic, units read off column names) do the work.
- **Choice:** r4 with a 5-sample majority vote: it ties Opus on errors and has the best TNR. It was frozen in `fd57bb8`, before the pool-3 labels existed. None of these variants separates from r4 with 1 sample on dev: the differences are 1–3 items.

**Final test, pool 3**, run once ([`final-p3/`](final-p3/)). Labels by a fresh agent told to read every tool result in full; the read tool truncates long lines, which earlier labellers had flagged.

| | case-bootstrap 95% CI | Wilson 95% |
|---|---|---|
| TPR, 48 / 52 (29 cases) | 92.3% [80.8, 100] | [81.8, 97.0] |
| TNR, 22 / 24 (15 cases) | 91.7% [80.0, 100] | [74.2, 97.7] |
| Sonnet 4.5 answers | TPR 92.9%, TNR 100% (10 fails) | |
| Haiku 4.5 answers | TPR 91.7%, TNR 85.7% (14 fails) | |

- **The 5-sample vote added nothing on test.** 97% of items got 5 identical votes, and the first vote alone scores TPR 94.2% and TNR 91.7%. One sample costs a fifth as much and is as good.
- **Compared with the r4 one-sample result on pool 2** (88.2% / 96.0%), the difference is inside the intervals. No variant tested here measurably beats r4.
- **All 6 test errors are rule-boundary cases:**
  - 3 hedged guesses at a failure's cause ("possible causes…", "typically happens before…") that the judge fails and the labeller passes;
  - Gouda's "approximately 52.0° N, 4.7° E" and a timezone, offered as defaults to confirm: the judge passes them as hedged world knowledge, while the rule lists coordinates;
  - a conditional "lat/long or timezone are common blockers";
  - "600 s = 10 min".

  Narrowing the error further needs a decision on those boundaries, not a better prompt.

**Recommendation:** run with `--samples 1` from now on. The vote buys nothing measurable at 5× the cost; the unanimity rate shows that without using labels.

**Limit of the pool 1–2 labels:** the agents' read tool cuts JSONL lines at about 768 bytes, and the second dev labeller said it did not re-read cut-off tool results. A labeller that missed support written past that point would label a fail where the judge (full text) passes. That pattern shows up as missed fails, and those are rare (TNR 95–97% on dev), so the effect looks small. The pool-3 labeller was told to read every tool result in full.

## Round 3: one rule for labellers and judge

**Problem.** In Round 2 every remaining error was a rule-boundary case. Labellers and the judge resolved those boundaries differently because the rule never decided them.

**Rule v2** ([`rule-v2.md`](rule-v2.md)) decides each boundary:
- hedged explanations with no number, field or system rule pass;
- defaults offered for confirmation pass;
- every unit conversion fails, time units included (as the owner did in x076);
- support anywhere in the tool results counts;
- capability statements stay out of scope.

The judge now uses the same file as its rubric.

**Labels.** Each item is a pretty-printed Markdown file, so no tool result is cut. Two agents labelled every item independently, and a third decided their splits.

| pools | items | labellers agree | Cohen's κ | adjudicated |
|---|---|---|---|---|
| 1–3 (train, dev, pool-3 test) | 436 | 97.0% | 0.93 | 13 |
| 4–5 (final test) | 152 | 92.8% | 0.82 | 11 |

**Tuning, one sample each, against the v2 gold.** Pool 3 was read at this step, so it is tuning data now. The boundary decisions in rule v2 are the maintainer's: the owner was asked and did not answer. They were written after reading the pool-3 errors.

| rubric | train (56) | dev, pools 1–2 (152) | pool 3 (76) |
|---|---|---|---|
| r4 | 2 errors | TPR 93.8%, TNR 100%, 7 errors | TPR 96.2%, TNR 95.8%, 3 errors |
| **rule v2** | 2 errors | **TPR 97.3%, TNR 100%, 3 errors** | **TPR 98.1%, TNR 100%, 1 error** |

Rule v2 was frozen in `1b2a127`. That commit came before any pool-4/5 label existed and before the judge saw pools 4–5. Pools 4–5 are new sessions of the same 38 test cases whose pool-3 sessions were used for tuning. The test is therefore held out by session, not by case.

**Final test, pools 4–5**, run once ([`final-p45/`](final-p45/)):

| | value | case-bootstrap 95% CI | Wilson 95% |
|---|---|---|---|
| TPR, 100 / 107 (35 cases) | 93.5% | [86.9, 98.3] | [87.1, 96.8] |
| TNR, 45 / 45 (20 cases) | 100% | (no misses to resample) | [92.1, 100] |
| Sonnet 4.5 answers (18 fail) | TPR 96.6%, TNR 100% | TPR [90.9, 100] | |
| Haiku 4.5 answers (27 fail) | TPR 89.8%, TNR 100% | TPR [78.7, 98.0] | |
| without the 11 adjudicated items | TPR 93.4% (99/106), TNR 100% (35/35) | TPR [86.7, 98.2] | |
| r4 prompt on the same items and labels ([`r4-p45/`](r4-p45/)) | TPR 92.5%, TNR 97.8%, 9 errors | | |

- **Agreement:** the judge agrees with labeller A on 143/152 items and with labeller B on 136/152. A and B agree with each other on 141/152. On these items the judge is as consistent with the labels as a second labeller.
- **Adjudication does not drive the result.** The adjudicator chose fail on 10 of the 11 splits, and the judge matches the adjudicated label on all 11. Dropping those items leaves TPR and TNR unchanged within 0.1 point.
- **Errors:** all 7 are labelled passes that the judge failed, so the judge is stricter, not looser. Six fail a mild inference the labellers accepted, about system behaviour or a config field (`lead_hours`). Examples:
  - "terminated without saving intermediate metrics", read off `metrics: null`;
  - a "guaranteed" D-1 availability.

  The seventh, p015, is a parsing artifact: the reply hit `Judge`'s default `max_tokens=1024` before its `SCORE:` line, so it counts as a fail. Its reasoning passes the answer. The frozen result keeps it as a fail; future runs can raise `max_tokens`.
- **Where the gain over Round 2 comes from:**
  - (a) Relabelling: on pool 3 the same r4 prompt drops from 5 errors (Round 2 labels) to 3 (v2 gold) with no prompt change.
  - (b) The prompt: on pools 4–5 against the same gold, rule v2 has 7 errors and r4 has 9. The paired, case-clustered accuracy gain is +1.3 points [0.0, +3.3]. r4 alone misses n023, n068 and p042; rule v2 alone misses p070.
  - The headline 91.7% → 100% TNR is therefore mostly a change of target: the boundaries are now decided. A better judge on a fixed target accounts for a small part.
- **Per model:** the judge wrongly fails 10.2% of good Haiku answers and 3.4% of good Sonnet ones. The case-bootstrap intervals overlap ([78.7, 98.0] vs [90.9, 100]), and TNR is 100% for both. The pooled correction in `judge-correct` assumes equal error rates. That is not rejected here, but if the gap is real, raw verdicts widen the Haiku − Sonnet gap by a few points.
- **Caveats:**
  - The labels are agent labels.
  - Labellers and judge read the same rule text, so part of their agreement comes from shared wording. The two labellers still agree with each other only at κ 0.82 on test.
  - Either/or cause guesses ("training didn't complete or couldn't log") are still undecided in the rule. The adjudicator passed n068 and flagged it.
  - Interval width is bounded by the 38 test cases, not by the session count. More reruns of these cases will barely narrow it; new test cases (new worlds or prompts) would.
- **Cost:** about 0.92M input and 0.14M output judge tokens, plus $1.27 for the pool-4/5 sessions.

## Round 4: rule v3 and a world-held-out test

**Changes, frozen in `b5ff681`:**
1. `max_tokens` 1024 → 4096. In Round 3, p015's reasoning was cut off before its `SCORE:` line.
2. [`rule-v3.md`](rule-v3.md) keeps v2 and adds 6 boundary decisions. They write down how the Round 3 labellers already decided recurring cases:
   - plain-language readings of this session's results;
   - what the tools return counts as a capability statement;
   - either/or guesses count as hedged;
   - qualitative judgements of returned numbers;
   - fields named only to look them up;
   - unit by reference.

   The maintainer wrote them after reading the pool 1–5 errors. The owner was not asked.

**Tuning (pools 1–5, all read).** The first v3 draft listed "generalising fails" and "a wrong sign fails". It made the judge fail 4 more dev passes than v2, so it was dropped. The second draft let hedged claims about what an unseen field holds pass, which missed 6 train fails; it was tightened. Final draft vs the v2 rubric, on the 436 items both were run on (v3 gold):

| rubric | missed fails | false fails | errors |
|---|---|---|---|
| rule v2 | 1/139 | 13/297 | 14 |
| rule v3 | 1/139 | 6/297 | 7 |

**Why the pools 1–5 gold was not relabelled.** Four agents were asked to recheck every v2 label against v3. All four were refused within seconds by a usage-policy filter. Instead, v3 was written to match the existing labels. The 54 fail labels whose notes touch a v3 boundary (units, fields, system or tool behaviour) were checked by hand, and one changed: n023, "in load_kw eenheden", is unit by reference. The other fail labels and all 398 pass labels were not rechecked, so the tuning numbers rest partly on v2 labels.

**Final test, heldout-v4 (pools 6–7), run once** ([`final-v4/`](final-v4/)).
- Labels: two blind labellers agree on 158/160 (κ 0.97). An adjudicator passed both splits (q046, r003).
- The rule-v2 rubric ran on the same items afterwards for comparison ([`v2-on-v4/`](v2-on-v4/)). It uses the same `max_tokens=4096`.

| | rule v3 (frozen) | rule v2 |
|---|---|---|
| TPR, 96 passes (31 cases), case bootstrap | **93.8% [87.6, 98.9]** | 90.6% [82.3, 97.1] |
| TNR, 64 fails (23 cases), case bootstrap | **95.3% [87.5, 100]** | 95.3% [86.7, 100] |
| errors / 160 | 9 | 12 |
| agrees with labeller A / B | 153 / 151 | 150 / 148 |
| Sonnet 4.5 answers, TPR / TNR | 93.8% / 96.9% | |
| Haiku 4.5 answers, TPR / TNR | 93.8% / 93.8% | |

- **v3 vs v2:** the paired, case-clustered accuracy difference is +1.9 points [−1.9, +5.6]. That is the right direction, but it does not separate.
- **Per model:** the error rates are equal, so the pooled correction in `judge-correct` fits here. (On pools 4–5 Haiku's TPR was lower.)
- **The 9 errors** form 3 clusters, all fixable only by a rule decision:
  1. A day count read off two dates or a row count ("2 dagen", "192 rows = 2 days"): the labellers fail it under rule 4, the judge passes it. This accounts for all 3 missed fails.
  2. A design rationale or system behaviour stated as fact ("so the model has no access to leakage", "the run will record the weather model", M2/M3 offered as options, "lookback 7 is the default"): the judge fails these, the labellers pass them.
  3. "Would be in kW, based on load_kw": is "would be … based on" a hedge?
- **Compared with Round 3:** the numbers are close (TPR 93.5%, TNR 100% on pools 4–5). This test is harder, because it is held out by world and case and has more fail cases (64 vs 45). It is also cleaner: the labellers agree at κ 0.97, not 0.82.
- **Caveats:**
  - Labels come from agents, and the boundary decisions are the maintainer's.
  - The labellers read rule v3, and so does the judge.
  - Cost: about 5.3M input and 0.6M output judge tokens for the Round 4 runs, plus $1.48 for the heldout-v4 sessions.

## Owner decisions on the Round 4 clusters (2026-11-22)

The owner decided two of the three clusters; [`rule-v4.md`](rule-v4.md) is rule v3 plus these decisions.

| cluster | decision | effect on the heldout-v4 gold |
|---|---|---|
| 2. design rationale or system behaviour stated as fact | **fail** (rule 3 as written) | q009, q025, q031, q046, r036 change from pass to fail ([`labels-67-owner.jsonl`](labels-67-owner.jsonl)) |
| 3. "would be in kW, based on load_kw" | **pass**, it is a hedge | r003 stays pass; the judge's fail is an error |
| 1. day count read off two dates or a row count | open | q062, q078, r078 stay fail; the judge passes them |

With the 5 labels changed, the frozen rule-v3 judgments ([`final-v4/`](final-v4/)) have 4 errors instead of 9: TPR 90/91 (98.9%), TNR 66/69 (95.7%). No judge was rerun.

- **This is not a held-out result.** Only the 5 items where judge and labellers disagreed were relabelled. Other items of the same kind, where both passed the answer, were not searched for, so the new figures favour the judge.
- **Rule v4 has not been run.** It should fix r003. Whether it changes any other verdict is unknown until a judge reads it on new sessions.
- **The labellers applied rule 3 more loosely than its text.** The owner's decision restores the text, so earlier pass labels in pools 1–5 that rest on the same reading may also be wrong.

## Haiku 5.5 as judge on pools 6 and 7 (2026-11-25)

Same script, 160 items, one sample, `--judge claude-haiku-5-5` with `--rule rule-v3.md` and `--rule rule-v4.md` ([`haiku-v3-p67/`](haiku-v3-p67/), [`haiku-v4-p67/`](haiku-v4-p67/)). Positive = pass.

| Judge, rule | labels | TPR | TNR | errors of 160 |
|---|---|---|---|---|
| Sonnet 5.5, rule v3 (Round 4, frozen) | v3 | 90/96 | 61/64 | 9 |
| Haiku 5.5, rule v3 | v3 | 89/96 | 54/64 | 17 |
| Haiku 5.5, rule v4 | v3 | 86/96 | 60/64 | 14 |
| Sonnet 5.5, rule v3 | owner | 90/91 | 66/69 | 4 |
| Haiku 5.5, rule v3 | owner | 85/91 | 55/69 | 20 |
| Haiku 5.5, rule v4 | owner | 85/91 | 64/69 | 11 |

- **Haiku is the weaker judge here**; Sonnet 5.5 with rule v3 stays the judge. Rule v4 cuts Haiku's false passes (TNR 54/64 to 60/64 on the v3 labels).
- **Pools 6 and 7 are not held out for rule v4**: it was written from the judge's errors on them, and the owner labels changed six of them. The rule v4 rows favour the rule.
- **Haiku 4.5 wrote half of the graded sessions**; Haiku 5.5 judging them was not tested for self-preference.
- **The blind recheck of the owner labels was not done.** It was planned with codex (`gpt-6-luna`), which hit its usage limit until 2026-11-27. The owner-label rows keep the bias stated in the section above.
