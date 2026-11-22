"""Score a judge on FaithBench summaries with the HaluBench prompt, zero-shot.

FaithBench (Bao et al., NAACL 2025, CC BY-NC-SA 4.0, vectara/FaithBench): summaries of 75
articles by ten LLMs, with hallucination spans marked by human annotators. Labels and texts are
read from the FaithJudge repo (Tamber et al. 2025, arXiv 2505.04847), which publishes 720 of the
750 summaries with the authors' majority label. As in that paper, Benign and Questionable
summaries are left out of the score: the task is Unwanted (hallucinated) against Consistent, the
metrics are balanced accuracy and macro F1. Intervals bootstrap over articles.

    uv run --extra llm python scripts/faithbench_judge.py --out runs/faithbench/x
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from halubench_judge import LONG_WORDS, MAX_TOKENS, P_FAIL, prompt, verdict

from evalkit.llmcache import CachedCompleter
from evalkit.models import Completer, get_model

REV = "69cdd25843a9b63825b991c182975e4c584a3b43"
URL = (
    f"https://raw.githubusercontent.com/vectara/FaithJudge/{REV}/eval_data/faithbench_summary.jsonl"
)
DATA = Path.home() / ".cache" / "evalkit" / "faithbench" / f"faithjudge-{REV[:7]}.jsonl"
# the summarisation request of Vectara's leaderboard, which the FaithBench summaries answer
QUESTION = (
    "Provide a concise summary of the following passage, covering the core pieces of "
    "information described."
)


def load() -> list[dict]:
    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, DATA)
    rows = []
    with DATA.open(encoding="utf-8") as f:
        for article in map(json.loads, f):
            for s in article["summaries"]:
                rows.append(
                    {
                        "id": s["sample_id"],
                        "article": article["source_id"],
                        "question": QUESTION,
                        "passage": article["source"],
                        "answer": s["summary"],
                        "label": s["computed_ground_truth_label_majority"],
                    }
                )
    return rows


def scores(pred: np.ndarray, gold: np.ndarray) -> tuple[float, float]:
    """Balanced accuracy and macro F1 of flagged (True) against hallucinated (True)."""
    tp, tn = (pred & gold).sum(), (~pred & ~gold).sum()
    fp, fn = (pred & ~gold).sum(), (~pred & gold).sum()
    bacc = (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)) / 2
    f1 = (2 * tp / max(2 * tp + fp + fn, 1) + 2 * tn / max(2 * tn + fp + fn, 1)) / 2
    return float(bacc), float(f1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--judge", default="claude-haiku-5-5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rule", help="text file added to the prompt, as in halubench_judge.py")
    ap.add_argument("--cut", type=float, help="flag P_FAIL >= cut instead of SCORE")
    ap.add_argument("--cut-long", type=float, help=f"cut for summaries over {LONG_WORDS} words")
    args = ap.parse_args()

    rows = load()
    rule = Path(args.rule).read_text(encoding="utf-8") if args.rule else ""
    backend = get_model(f"anthropic:{args.judge}")
    assert isinstance(backend, Completer)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    completer = CachedCompleter(
        backend, out / "judge-cache.jsonl", model_id=args.judge, max_calls=len(rows)
    )
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        texts = list(
            pool.map(
                lambda r: completer.complete(prompt(r, rule), max_tokens=MAX_TOKENS).text, rows
            )
        )
    found = [verdict(t) for t in texts]
    if args.cut is not None:
        p_fail = [float(m[-1]) if (m := P_FAIL.findall(t)) else None for t in texts]
        long_cut = args.cut if args.cut_long is None else args.cut_long
        cuts = [long_cut if len(r["answer"].split()) > LONG_WORDS else args.cut for r in rows]
        trio = zip(found, p_fail, cuts, strict=True)
        found = [s if p is None else "FAIL" if p >= c else "PASS" for s, p, c in trio]
    with (out / "verdicts.jsonl").open("w") as f:
        for r, v in zip(rows, found, strict=True):
            f.write(json.dumps({"id": r["id"], "label": r["label"], "verdict": v}) + "\n")

    # a reply without a verdict counts as flagged
    flagged = np.array([v != "PASS" for v in found])
    label = np.array([r["label"] for r in rows])
    article = np.array([r["article"] for r in rows])
    print(len(rows), "summaries,", sum(v is None for v in found), "replies without a verdict")
    for name in ("Unwanted", "Questionable", "Benign", "Consistent"):
        m = label == name
        print(f"{name:13} {m.sum():4}  flagged {flagged[m].mean():6.1%}")
    keep = (label == "Unwanted") | (label == "Consistent")
    pred, gold, art = flagged[keep], label[keep] == "Unwanted", article[keep]
    bacc, f1 = scores(pred, gold)
    groups = [np.flatnonzero(art == a) for a in sorted(set(art))]
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(1000):
        idx = np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])
        boots.append(scores(pred[idx], gold[idx]))
    (b_lo, f_lo), (b_hi, f_hi) = np.percentile(np.array(boots), [2.5, 97.5], axis=0)
    print(f"Unwanted vs Consistent, n = {keep.sum()} ({len(groups)} articles)")
    print(f"balanced accuracy {bacc:6.1%} [{b_lo:5.1%}, {b_hi:5.1%}]")
    print(f"macro F1          {f1:6.1%} [{f_lo:5.1%}, {f_hi:5.1%}]")


if __name__ == "__main__":
    main()
