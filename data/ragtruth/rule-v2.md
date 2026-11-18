the response must contain no hallucination relative to the context in the user request (passages, structured JSON data, or a news article). Judge the way RAGTruth's annotators did: they marked specific wrong or added content, and almost never marked shifts in tone, emphasis or certainty.

Score 0 if you can quote a specific phrase in the response that is one of:
1. Conflict: it states a specific fact differently from the context, such as a wrong number, date, time, name, place, attribute, or opening hours, or it attributes something to the wrong person, review, passage or entity.
2. Added information: it states a fact, detail, name, date, place, cause, outcome or event that the context does not contain, even if it might be true in the world. Added descriptive claims about a business or a person count too ("cozy atmosphere", "popular dishes", "known for", "offers catering", "highly recommended"), unless a review or the data says so.
3. JSON null: it states a field that is null in the data as yes, no, available or unavailable.

Do not score 0 for:
- dropping a qualifier, condition, date or hedge from the context (that is an omission, not a hallucination);
- a slightly stronger or weaker wording of something the context does say, or a change of tone or emphasis;
- a summary judgement that fairly sums up the context ("mixed reviews" when reviews disagree, "praised" when a review praises);
- combining facts that each appear in the context, even from different passages;
- statements about the response itself (its length, word count, or that it is a summary);
- paraphrase, reordering, restating the question, or saying the context does not answer it.

Score 1 if no phrase meets 1-3. Give SCORE: 0 or SCORE: 1, nothing in between.
