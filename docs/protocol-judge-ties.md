# Protocol: a tie margin for the pointwise judge (Phase P)

Committed before any agreement number of the margin is computed, on development or confirmation questions. The grid, the split, the selection rule, the decision rule, the sensitivity analysis and the predictions below are fixed. The result is reported against the rule whatever it shows, a negative one included. Cache replay only: no API call is made (`CachedCompleter` without a backend raises on a miss).

## Problem (from `docs/protocol-judge-mtbench.md` and the README "Does it agree with humans?" section, no new run)

On the 1,000 test items the pairwise judge resolves 14.5% [11.1, 17.9] of items to tie against 23.3% [19.6, 27.2] for the humans (per vote), and 11 of the 1,000 items had an unparsable reply in one order (counted as tie). S1 counts a tie as a label, so a judge that is more decisive than the humans loses S1 on every item the humans call a tie.

The pairwise path has only categorical verdicts (`A`, `B`, `TIE` per order), so it has no scalar a margin could act on. The cached data that does is the **pointwise** run: 600 calls, two 1-10 scores per item, on the first 300 test items (71 questions). Its derived verdict is `A` if score A > score B, `B` if lower, `tie` if equal (`judge.point_verdict`; an unparsable score gives tie). Its tie rate at margin 0 is 23.7% [17.7, 30.6] against 26.6% [21.6, 31.9] for the humans (`docs/results/judge-mtbench-pointwise.md`).

## Change under test

A tie margin $\delta$: the derived verdict is `tie` when $|s_A - s_B| \le \delta$, else `A` if $s_A > s_B$, else `B`. $\delta = 0$ is the current behaviour. Scores are integers in 1-10 in the cache, so $|s_A - s_B|$ is an integer and a non-integer $\delta$ equals its floor.

**Grid** (fixed): $\delta \in \{0, 1, 2, 3\}$. Nothing else is tried.

## Metrics (unchanged definitions, `evalkit.judge_stats`)

**S1** = judge-human agreement with ties counted as a label; **S2** = the same with every (judge, vote) pair dropped where either side is a tie. Both are exactly `jh_s1` and `jh_s2` of `AgreementData` (README: "S1 counts ties as a label; S2 drops them"; per item the share of its human votes matched, mean over items). Judge tie rate and human tie rate (per vote) are reported with them. Intervals: percentile 95%, cluster bootstrap over questions, 2,000 resamples, seed 0, and the margin arms, the difference between them and every other statistic are computed on the same resample (`cluster_bootstrap`).

## Splits (seed 0, questions never split across portions)

The 71 questions of the first 300 test items are sorted as strings, shuffled with `random.Random(0).shuffle`, and the first 36 form the **dev portion**; the remaining 35 form the **confirmation portion**. The dev portion chooses $\delta$. The confirmation portion is scored once, after $\hat\delta$ is written to disk. (The repository's 8-question dev split has pairwise calls only; it has no pointwise scores, and none can be bought.)

## Selection of $\hat\delta$ (dev portion only)

Leave-question-out cross-validation: for each dev question, hold it out, score it with each $\delta$ in the grid, and pool the held-out items. A fixed-threshold rule has nothing fitted on the training questions, so the pooled held-out S1 of a $\delta$ equals its S1 on the dev portion; that is the **CV score**. $\hat\delta$ is the $\delta$ with the largest CV score S1; ties go to the smaller $\delta$.

For an honest estimate of *selecting from the grid* (reported, not part of the rule), the selection is also nested inside the folds: for each held-out question the best $\delta$ on the other dev questions (same tie-break) scores the held-out question; the pooled out-of-fold S1 is compared with $\delta = 0$ on the same items. The fold-wise chosen $\delta$ values are counted.

If $\hat\delta = 0$ the confirmation portion is not scored and the outcome is "no margin helps on dev".

## Decision rule (confirmation portion; written before any scoring)

Let $\Delta S1 = \mathrm{S1}(\hat\delta) - \mathrm{S1}(0)$ and $\Delta S2 = \mathrm{S2}(\hat\delta) - \mathrm{S2}(0)$ on the confirmation portion, each with its question-clustered bootstrap 95% CI (paired, same resamples).

**Ship $\hat\delta$ as an opt-in if both hold:**

1. the lower bound of the CI of $\Delta S1$ is **above 0**, and
2. the upper bound of the CI of $\Delta S2$ is **>= 0** (S2 shows no detectable drop).

**Otherwise** the result is documented and the code, the CLI and every default are left unchanged.

"Ship as an opt-in" means: `point_verdict(..., tie_margin=0.0)` and `evalkit judge --mode pointwise --tie-margin D`, with default 0 (behaviour unchanged unless asked). It is **not** made the default in this phase whatever the numbers: one 35-question confirmation split does not justify changing the default verdicts. A CI that includes 0 is reported as "no detectable effect".

## Sensitivity analysis: the unparsable replies (pre-registered, so not post-hoc)

1. Pairwise, 1,000 test items: S1, S2, judge tie rate, human tie rate (per vote) with and without the 11 items that have an unparsable reply, and the change in S1 and S2 from dropping them (paired cluster bootstrap).
2. Pointwise, 300 items: the same at $\delta = 0$ and at $\hat\delta$, with and without the pairs that contain an unparsable score (1 of 600 scores).

Reported with the rule, not part of it.

## Everything else is post-hoc

Any look at the results beyond the tables listed above (for example $\delta$ chosen or inspected on the pooled 300 items, subgroups, or other margins) is labelled post-hoc in the README and carries no claim.

## Predictions (written before scoring; the histogram of $|s_A - s_B|$ over the 300 items was seen, no agreement number was)

The cached histogram gives tie rates of 23.7% ($\delta = 0$), 47.0% (1), 65.3% (2), 77.0% (3) over the 300 items (the one unparsable pair counted as tie) against a human tie rate near 27%. So:

1. Every $\delta \ge 1$ makes the judge far more tie-prone than the humans, S1 falls, and $\hat\delta = 0$ on dev. [PREDICTION, not tested]
2. If a $\delta \ge 1$ is chosen anyway, the rule fails at condition 1. [PREDICTION, not tested]
3. The 11 unparsable replies move S1 by less than 0.5 pp, since they are 1.1% of items. [PREDICTION, not tested]

## Files

`scripts/mtbench_tie_margin.py` (`dev`, `confirm`, `sensitivity`; reads `data/mtbench/test.jsonl` and `data/mtbench/cache-test.jsonl` only), outputs in `docs/results/judge-mtbench-tie-margin.{md,json}`, tests in `tests/test_evalkit_judge_ties.py`. Checks: ruff, ruff format --check, mypy src, pytest -q.

## Outcome (written after scoring; `scripts/mtbench_tie_margin.py`, cache replay, no API call)

Dev portion: 36 questions, 164 items; confirmation portion: 35 questions, 136 items. Dev S1 by margin (CV score, pooled held-out): $\delta$ 0: 71.1%, 1: 66.8%, 2: 59.7%, 3: 51.1%; judge tie rate 24.4%, 47.6%, 62.2%, 72.0% against a human tie rate of 27.4% (S2 rises, 89.4% to 94.0%, because it keeps fewer and clearer pairs). **$\hat\delta = 0$.** The nested leave-question-out selection chose 0 in all 36 folds (out-of-fold S1 71.1%, equal to $\delta = 0$). By the protocol the confirmation portion is **not scored** and no margin is shipped.

**Rule outcome: not met, nothing changed** (no code, CLI or default). Not "no detectable effect" but "no margin helps on dev": the S1 change is negative at every $\delta \ge 1$.

**Sensitivity (pre-registered).** Pairwise, 1,000 items: dropping the 11 items with an unparsable reply moves S1 from 67.8% [64.9, 70.7] to 68.3% [65.4, 71.2] (+0.5 pp [+0.1, +1.1]; unrounded +0.52 pp), S2 unchanged (those items are ties, so they never enter S2), judge tie rate 14.5% to 13.5%. Pointwise, 300 items, $\delta = 0$: dropping the 1 pair with an unparsable score moves S1 by +0.1 pp [+0.0, +0.4]. The tie gap to the humans (23.3%) stays: it is not caused by the unparsable replies.

**Predictions.** 1 held (dev S1 falls with every step of $\delta$, $\hat\delta = 0$). 2 was not tested ($\hat\delta = 0$). 3 missed by a hair: the unparsable replies move pairwise S1 by +0.52 pp, not less than 0.5. The tie rates quoted for $\delta$ = 1, 2, 3 in the predictions paragraph were 0.3 pp high (an addition slip, 47.0%, 65.3%, 77.0%); the correct pooled rates are 46.7%, 65.0%, 76.7% (post-hoc table).

**Post-hoc (not pre-registered), `docs/results/judge-mtbench-tie-margin-posthoc.md`.** All margins on the pooled 300 items against $\delta = 0$: S1 change -3.7 pp [-8.4, +1.3] ($\delta$ = 1), -13.9 pp [-20.6, -7.2] (2), -21.4 pp [-29.5, -13.5] (3); S2 change +4.3, +6.8, +7.7 pp (intervals above 0). Pooled data cannot be held out, so this is descriptive. It agrees with dev: the judge's pointwise tie rate at $\delta = 0$ (23.7%) is already close to the humans' (26.6%), so a margin overshoots. The 14.5% against 23.3% gap is a property of the pairwise resolution (both orders must agree), which has no scalar to put a margin on; a margin on the pointwise scores does not close it, it replaces it with a larger gap in the other direction.
