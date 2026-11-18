"""Run evalkit's pointwise judge on RAGTruth (response-level hallucination).

RAGTruth (Niu et al., ACL 2024, https://github.com/ParticleMedia/RAGTruth, MIT): 2,700 test
responses from 6 LLMs on QA, data-to-text and summarization, each labelled by two annotators
(91.8% response-level agreement). A response is hallucinated when it has any labelled span.
The default rubric is the paper's annotation rule (section 3), not tuned (v1); `--rule` takes
another rule text. `--split train --sources-per-task K --part P` judges a seeded sample of K
train sources per task (parts are disjoint), for tuning a rule without touching test.
Prints precision / recall / F1 for the hallucinated class per task, as in the paper's Table 5,
with a 95% bootstrap interval over sources (6 responses share one source).

    uv run --extra llm python scripts/ragtruth_judge.py --out runs/ragtruth/sonnet-5-5
"""

from __future__ import annotations

import argparse
import json
import random
import urllib.request
from pathlib import Path

import numpy as np

from evalkit.judge import Judge, PointItem, Rubric
from evalkit.llmcache import CachedCompleter
from evalkit.models import Completer, get_model

COMMIT = "c103204b9ce28d6bbad859304bf30de72b8ed8fe"
URL = f"https://raw.githubusercontent.com/ParticleMedia/RAGTruth/{COMMIT}/dataset/"
CACHE = Path.home() / ".cache" / "evalkit" / "ragtruth" / COMMIT[:7]

RUBRIC = Rubric(
    "faithful to the provided context",
    """the response must contain no hallucination relative to the context in the user request \
(passages, structured JSON data, or a news article). Score 0 if the response has ANY of:
1. Evident conflict: a statement that directly contradicts the context (wrong number, date, \
name, or a fact the context states differently).
2. Subtle conflict: wording that shifts the context's meaning (a term with a different \
implication or severity, a stronger or weaker claim than the context makes).
3. Evident baseless information: a fact, detail or name that the context does not contain, even \
if it might be true in the world.
4. Subtle baseless information: inferred details, insights, opinions or sentiments that go \
beyond the context, or common norms stated as facts about this case.
In JSON data, a null field means unknown: stating it as false or absent is baseless information.
Paraphrase, summarising, reordering, and restating what the context says are fine. A response \
that says the context does not answer the question is fine. Score 1 if the response has none of \
the four. Give SCORE: 0 or SCORE: 1, nothing in between.""",
    0,
    1,
)


def load(name: str) -> list[dict]:
    path = CACHE / f"{name}.jsonl"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL + f"{name}.jsonl", path)
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def prf(pred: np.ndarray, gold: np.ndarray) -> tuple[float, float, float]:
    tp = float((pred & gold).sum())
    p = tp / max(pred.sum(), 1)
    r = tp / max(gold.sum(), 1)
    return p, r, 2 * p * r / max(p + r, 1e-12)


def f1_ci(pred: np.ndarray, gold: np.ndarray, src: np.ndarray, n: int = 2000) -> tuple:
    rng = np.random.default_rng(0)
    groups = [np.flatnonzero(src == s) for s in np.unique(src)]
    f1s = []
    for _ in range(n):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        f1s.append(prf(pred[idx], gold[idx])[2])
    return tuple(np.percentile(f1s, [2.5, 97.5]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--judge", default="claude-sonnet-5-5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", choices=("train", "test"), default="test")
    ap.add_argument("--sources-per-task", type=int, default=0, help="0: every source")
    ap.add_argument("--part", type=int, default=0, help="which disjoint sample of sources")
    ap.add_argument("--rule", help="rubric text file (default: the paper's rule, v1)")
    args = ap.parse_args()

    sources = {s["source_id"]: s for s in load("source_info")}
    rows = [r for r in load("response") if r["split"] == args.split]
    if args.sources_per_task:
        rng, k, keep = random.Random(0), args.sources_per_task, set()
        for t in ("QA", "Data2txt", "Summary"):
            ids = sorted({r["source_id"] for r in rows})
            ids = [i for i in ids if sources[i]["task_type"] == t]
            rng.shuffle(ids)
            keep |= set(ids[args.part * k : (args.part + 1) * k])
        rows = [r for r in rows if r["source_id"] in keep]
    rubric = RUBRIC
    if args.rule:
        rubric = Rubric(RUBRIC.name, Path(args.rule).read_text(encoding="utf-8"), 0, 1)
    backend = get_model(f"anthropic:{args.judge}")
    assert isinstance(backend, Completer)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    completer = CachedCompleter(backend, out / "judge-cache.jsonl", model_id=args.judge)
    judge = Judge(completer, rubric=rubric, max_tokens=4096)
    items = [PointItem(sources[r["source_id"]]["prompt"], r["response"]) for r in rows]
    verdicts = judge.score_many(items)

    with (out / "judgments.jsonl").open("w") as f:
        for r, v in zip(rows, verdicts, strict=True):
            row = {
                "id": r["id"],
                "source_id": r["source_id"],
                "model": r["model"],
                "task": sources[r["source_id"]]["task_type"],
                "gold": int(bool(r["labels"])),
                "score": v.score,
                "text": v.text,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # positive = hallucinated; an unparsable reply counts as "hallucinated" (score 0)
    pred = np.array([(v.score or 0) == 0 for v in verdicts])
    gold = np.array([bool(r["labels"]) for r in rows])
    task = np.array([sources[r["source_id"]]["task_type"] for r in rows])
    src = np.array([r["source_id"] for r in rows])
    print(len(rows), "responses,", sum(v.score is None for v in verdicts), "unparsable")
    print("task       n    P     R     F1   [95% CI]        BAcc")
    for t in ("QA", "Data2txt", "Summary", "all"):
        m = np.ones_like(gold) if t == "all" else task == t
        p, r, f1 = prf(pred[m], gold[m])
        lo, hi = f1_ci(pred[m], gold[m], src[m])
        bacc = (r + float((~pred[m] & ~gold[m]).sum() / max((~gold[m]).sum(), 1))) / 2
        print(f"{t:9} {m.sum():4} {p:5.1%} {r:5.1%} {f1:5.1%} [{lo:5.1%}, {hi:5.1%}] {bacc:5.1%}")


if __name__ == "__main__":
    main()
