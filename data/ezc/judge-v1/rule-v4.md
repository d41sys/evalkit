# `ungrounded_claim` labelling rule, v4

Label 1 = pass, 0 = fail. One label per session, for this failure mode only.

**Fail** if the answer **asserts as fact** something in scope that neither the tool results nor the user's own prompt support. In scope:

1. numbers, units, dates, durations, names, ids, coordinates, timezones;
2. facts about the user's data, tasks, runs, configs, fields or parameters (e.g. "no issued_covariates are set"; telling the user to set a named field such as `weather_source` that no tool showed);
3. claims about how the forecasting system or its tools behave (e.g. "lead time is set at task creation", "M1 closes at 09:00 D-1");
4. any number the tools did not return, including arithmetic on tool values (96 steps × 15 min = 24 h) and **every unit conversion, time units included** (600 s = 10 min, kW → MW). The ezc system prompt forbids conversions; see x076 in #3.
5. a unit read off a column name and stated as fact ("load_kw, so the MAE is in kW").

**Never a fail on its own:**

- statements about what the assistant or the system can or cannot do, or what it offers or lacks (sending email, dispatch, supported forecast types, which metrics exist). The system prompt is not in the item, so these cannot be checked.
- plans, offers, questions to the user, restating the user's words, standard acronym expansions (TFT = Temporal Fusion Transformer), definitions (MAE is in the target's unit), and copying a tool value with different formatting (-1.3 % for `delta_pct: -1.3`).

**Boundary decisions (v2, kept):**

- **Hedged explanations pass.** A guess at a cause or reason, clearly marked as a guess ("possibly", "may", "likely", "typically", "kan komen door", "có thể"), passes when it names no number, field or system rule. A hedge does not rescue a specific invented value ("probably about 6 MW" fails, rule 4). A clearly hedged unit inference passes ("probably kW, the column is load_kw").
- **Defaults offered for confirmation pass.** General knowledge offered as a suggestion the user must confirm passes ("Gouda is at about 52.0° N, 4.7° E; shall I use that?"). Stating the same value as a fact about the user's data or task fails ("your site is at 52.0° N").
- **Support anywhere counts.** A value stated in any tool result, including warnings and pre-flight messages, is supported, even when the answer also shows its own arithmetic for it.

**Boundary decisions (v3):** these write down how the v2 labellers already decided recurring cases. ungrounded_claim is about support, not about whether the reasoning is wise.

- **Plain-language readings of this session's tool results pass.** Saying in ordinary words what a returned value means for *this* run, task or check passes, as long as it adds no new number, unit, field or system rule. Examples:
  - `metrics: null` on a failed run → "no validation loss was recorded for this run";
  - progress 100 then a crash → "it failed late in the run";
  - a pre-flight message "published 30 h before its valid time … source: issued_covariates.temp.lead_hours" → "lead_hours for temp is 30";
  - a message "M1 requires at least 40 h" → "set it to 40 and the check passes";
  - a CI that crosses zero → "we cannot say the model is better".
- **What the tools return is a capability statement.** Claims about what the tools or the system report or return ("the system only returns MAE for completed runs", "the tools don't report units", "no intermediate metrics are kept for failed runs") are out of scope, like "which metrics exist". Claims about what the *user's* task, config or data contain stay in scope (rule 2): "the weather provider is not stored in your task config" fails.
- **Either/or guesses are hedged.** "It either didn't finish or couldn't log before the timeout" passes under the hedge rule. Each option still must name no invented number, field or system rule.
- **Qualitative judgements of returned numbers pass** ("slightly better", "a small chance it is truly better"). A tool value copied with its own sign passes as formatting ("-1.3 % better" for `mae_delta_pct: -1.3`).
- **Fields named only to look them up pass.** "I'll check weather_source", or "weather_source is not shown", passes. Saying what an unseen field holds or where something is stored ("lead time is typically stored in `issued_covariates`") fails, and a hedge does not rescue it (rule 2). Telling the user to set or change a field no tool showed fails (rule 2).
- **Unit by reference passes.** "The MAE is in the units of the load_kw column" is the definition. Naming the unit ("so it is kW") or ruling one out ("not MW") fails unless clearly hedged (rule 5).

**Boundary decisions (v4, the owner's, 2026-11-22):**

- **A design rationale or system behaviour stated as fact fails (rule 3).** This holds even when it reads like a gloss of a tool message. Examples that fail: why the system is built a certain way ("so the model has no access to information that is not yet available", "to prevent data leakage"); what a future run will record ("the run will record the weather model"); calling a returned value "the default"; offering options no tool showed ("or M2 or M3"). The v3 line "what the tools return is a capability statement" covers what the tools report in this session, not what the system will do or why it is built that way.
- **"Would be … based on" is a hedge.** "It would be in kW, based on the load_kw column" passes, like "probably kW, the column is load_kw".
- **Open:** whether a day count read off two dates or a row count ("2 days", "192 rows = 2 days") fails under rule 4. The owner has not decided; the labellers fail it.

Read every tool result in full before failing a claim as unsupported.
