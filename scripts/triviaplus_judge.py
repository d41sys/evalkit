"""Run evalkit's pointwise judge on TRIVIA+ (response-level hallucination, long-context RAG QA).

TRIVIA+ (Chen et al., ACL 2026, CC BY-NC-ND 4.0,
https://github.com/amazon-science/hallucination-benchmark-trivialplus):
3,224 answers from Mixtral 8x7B, Gemma 7B and Claude to questions over articles
up to 95K characters, labelled per sentence by 2-6 annotators. A response is unfaithful when any
sentence is "contradicts" or "not-mentioned". The default rubric (v1) is the annotation guideline
(paper appendix A.5), not tuned. Only ids and verdicts may be committed (NoDerivatives licence).
Prints precision / recall / F1 for the unfaithful class, accuracy and balanced accuracy, overall
and by generating model, context length and source; intervals bootstrap over articles.

    uv run --extra llm --with pyarrow python scripts/triviaplus_judge.py --out runs/triviaplus/v1
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from ragtruth_judge import bacc, f1_ci, prf

from evalkit.judge import Judge, PointItem, Rubric
from evalkit.llmcache import CachedCompleter
from evalkit.models import Completer, get_model

COMMIT = "c133bbf1fe751b7c0d04ea79f92cfbc9bef8f611"
URL = (
    "https://github.com/amazon-science/hallucination-benchmark-trivialplus/raw/"
    f"{COMMIT}/triviaplus_dataset.parquet"
)
DATA = Path.home() / ".cache" / "evalkit" / "triviaplus" / "triviaplus_dataset.parquet"
RUBRIC = Rubric(
    "faithful to the article",
    "the answer must be fully supported by the article in the user request. Judge each sentence "
    "of the answer against the article only, as TRIVIA+'s annotators did:\n"
    "- supports: the article confirms the sentence, explicitly or by direct inference;\n"
    "- contradicts: the article disagrees with the sentence;\n"
    "- not mentioned: the article neither confirms nor refutes the sentence;\n"
    "- supplementary: the sentence adds nothing that pertains to the question, such as "
    '"The answer is based on my understanding of the article".\n'
    "If conflicting information appears in different parts of the article, weigh the source, "
    "recency and authority. Score 0 if any sentence contradicts the article or is not mentioned "
    "in it; score 1 if every sentence is supported or supplementary.",
    0,
    1,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--judge", default="claude-sonnet-5-5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", choices=("train", "valid", "test"), default="test")
    ap.add_argument("--rule", help="rubric text file (default: the annotation guideline, v1)")
    args = ap.parse_args()

    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, DATA)
    rows = [r for r in pq.read_table(DATA).to_pylist() if r["split"] == args.split]
    rubric = RUBRIC
    if args.rule:
        rubric = Rubric(RUBRIC.name, Path(args.rule).read_text(encoding="utf-8"), 0, 1)
    backend = get_model(f"anthropic:{args.judge}")
    assert isinstance(backend, Completer)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    completer = CachedCompleter(backend, out / "judge-cache.jsonl", model_id=args.judge)
    judge = Judge(completer, rubric=rubric, max_tokens=4096)
    items = [
        PointItem(f"Question: {r['question']}\n\nArticle:\n{r['article']}", r["answer"])
        for r in rows
    ]
    verdicts = judge.score_many(items)

    with (out / "judgments.jsonl").open("w") as f:
        for r, v in zip(rows, verdicts, strict=True):
            row = {
                "id": r["__index_level_0__"],
                "model": r["model"],
                "gold": r["response_level_label_binary"],
                "score": v.score,
                "text": v.text,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # positive = unfaithful. The judge sometimes answers between 0 and 1 (0.2, 0.9); the scale's
    # midpoint is the fixed cut, not tuned. An unparsable reply counts as unfaithful.
    pred = np.array([v.score is None or v.score < 0.5 for v in verdicts])
    gold = np.array([r["response_level_label_binary"] == 1 for r in rows])
    art = np.array([r["article"] for r in rows])
    n = np.array([len(r["article"]) for r in rows])
    groups = {"all": np.ones_like(gold)}
    for key in ("model", "source"):
        for val in sorted({r[key].replace("ms_marco", "msmarco") for r in rows}):
            groups[val] = np.array([r[key].replace("ms_marco", "msmarco") == val for r in rows])
    groups |= {"<1K": n < 1000, "1K-5K": (n >= 1000) & (n <= 5000), ">5K": n > 5000}
    print(len(rows), "responses,", sum(v.score is None for v in verdicts), "unparsable")
    print("group         n    P      R      F1    [95% CI]          Acc    BAcc")
    for name, m in groups.items():
        p, r, f1 = prf(pred[m], gold[m])
        lo, hi = f1_ci(pred[m], gold[m], art[m])
        acc = float((pred[m] == gold[m]).mean())
        ba = bacc(pred[m], gold[m])
        print(
            f"{name:12} {m.sum():4} {p:6.1%} {r:6.1%} {f1:6.1%} [{lo:6.1%}, {hi:6.1%}] "
            f"{acc:6.1%} {ba:6.1%}"
        )


if __name__ == "__main__":
    main()
