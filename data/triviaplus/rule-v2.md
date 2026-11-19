the answer must be fully supported by the article in the user request. Judge each sentence of the answer against the article only, as TRIVIA+'s annotators did:
- supports: the article confirms the sentence, explicitly or by direct inference;
- contradicts: the article disagrees with the sentence;
- not mentioned: the article neither confirms nor refutes the sentence;
- supplementary: the sentence adds nothing that pertains to the question, such as "The answer is based on my understanding of the article".
If conflicting information appears in different parts of the article, weigh the source, recency and authority. The answer is unfaithful if any sentence contradicts the article or is not mentioned in it, and faithful if every sentence is supported or supplementary.

The annotators accepted arithmetic and counting that the article supports up to rounding or approximation ("about 300" for 296; "2.0%" for 1.9 points; "4157" for 4156.8; "almost 6 years"), and a span of years or months counted either inclusively or exclusively (1599 to 1606 as 7 or 8 years). Treat these as supported. A number that no reasonable reading of the article gives is still a contradiction.

The score is your probability, from 0 to 1, that the annotators labelled the answer faithful: 1 when every sentence is clearly supported, 0 when a sentence clearly contradicts the article or is clearly not in it, and in between when it depends on a judgement call. Use the whole range.
