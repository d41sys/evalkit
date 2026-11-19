"""Run evalkit's pointwise judge on RAGTruth (response-level hallucination).

RAGTruth (Niu et al., ACL 2024, https://github.com/ParticleMedia/RAGTruth, MIT): 2,700 test
responses from 6 LLMs on QA, data-to-text and summarization, each labelled by two annotators
(91.8% response-level agreement). A response is hallucinated when it has any labelled span.
The default rubric is the paper's annotation rule (section 3), not tuned (v1); `--rule` takes
another rule text. `--split train --sources-per-task K --part P` judges a seeded sample of K
train sources per task (parts are disjoint), for tuning a rule without touching test.
`--samples K` asks the judge K times (temperature default) and flags a response when at least
`--min-fails` of the K replies fail it (per task; default a majority).
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


def bacc(pred: np.ndarray, gold: np.ndarray) -> float:
    tnr = float((~pred & ~gold).sum() / max((~gold).sum(), 1))
    return (prf(pred, gold)[1] + tnr) / 2


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
    ap.add_argument("--samples", type=int, default=1, help="judge calls per response")
    ap.add_argument("--min-fails", default="", help="fail votes to flag, e.g. QA=3,Summary=2")
    args = ap.parse_args()
    need = {t: args.samples // 2 + 1 for t in ("QA", "Data2txt", "Summary")}
    for kv in filter(None, args.min_fails.split(",")):
        t, n = kv.split("=")
        need[t] = int(n)

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
    items = [PointItem(sources[r["source_id"]]["prompt"], r["response"]) for r in rows]
    samples = []
    for s in range(args.samples):
        cache = out / ("judge-cache.jsonl" if s == 0 else f"judge-cache-{s}.jsonl")
        completer = CachedCompleter(backend, cache, model_id=args.judge)
        samples.append(Judge(completer, rubric=rubric, max_tokens=4096).score_many(items))
    verdicts = samples[0]
    # an unparsable reply counts as a fail vote ("hallucinated")
    fails = np.array([sum((v.score or 0) == 0 for v in vs) for vs in zip(*samples, strict=True)])

    with (out / "judgments.jsonl").open("w") as f:
        for r, v, n in zip(rows, verdicts, fails, strict=True):
            row = {
                "id": r["id"],
                "source_id": r["source_id"],
                "model": r["model"],
                "task": sources[r["source_id"]]["task_type"],
                "gold": int(bool(r["labels"])),
                "score": v.score,
                "fails": int(n),
                "text": v.text,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # positive = hallucinated
    gold = np.array([bool(r["labels"]) for r in rows])
    task = np.array([sources[r["source_id"]]["task_type"] for r in rows])
    pred = fails >= np.array([need[t] for t in task])
    src = np.array([r["source_id"] for r in rows])
    bad = sum(v.score is None for vs in samples for v in vs)
    print(len(rows), "responses,", args.samples, "samples,", bad, "unparsable; min fails", need)
    print("task       n    P     R     F1   [95% CI]        BAcc")
    for t in ("QA", "Data2txt", "Summary", "all"):
        m = np.ones_like(gold) if t == "all" else task == t
        p, r, f1 = prf(pred[m], gold[m])
        lo, hi = f1_ci(pred[m], gold[m], src[m])
        ba = bacc(pred[m], gold[m])
        print(f"{t:9} {m.sum():4} {p:5.1%} {r:5.1%} {f1:5.1%} [{lo:5.1%}, {hi:5.1%}] {ba:5.1%}")
    if args.samples > 1:
        ks = range(1, args.samples + 1)
        print("BAcc / F1 by min fail votes:", *ks)
        for t in ("QA", "Data2txt", "Summary"):
            m = task == t
            cells = [(bacc(fails[m] >= k, gold[m]), prf(fails[m] >= k, gold[m])[2]) for k in ks]
            print(f"{t:9}", "  ".join(f"{b:5.1%}/{f:5.1%}" for b, f in cells))


if __name__ == "__main__":
    main()
