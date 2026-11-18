# `ungrounded_claim` labelling rule, v2

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

**Boundary decisions (v2):**

- **Hedged explanations pass.** A guess at a cause or reason, clearly marked as a guess ("possibly", "may", "likely", "typically", "kan komen door", "có thể"), passes when it names no number, field or system rule. A hedge does not rescue a specific invented value ("probably about 6 MW" fails, rule 4). A clearly hedged unit inference passes ("probably kW, the column is load_kw").
- **Defaults offered for confirmation pass.** General knowledge offered as a suggestion the user must confirm passes ("Gouda is at about 52.0° N, 4.7° E; shall I use that?"). Stating the same value as a fact about the user's data or task fails ("your site is at 52.0° N").
- **Support anywhere counts.** A value stated in any tool result, including warnings and pre-flight messages, is supported, even when the answer also shows its own arithmetic for it.

Read every tool result in full before failing a claim as unsupported.
