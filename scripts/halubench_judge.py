"""Score a judge on HaluBench with the Lynx paper's own evaluation prompt.

HaluBench (Ravi et al. 2024, "Lynx", arXiv 2407.08488, CC BY-NC 2.0, PatronusAI/HaluBench on
HuggingFace): 14,900 (question, passage, answer) triples from HaluEval, RAGTruth, FinanceBench,
DROP, CovidQA and PubMedQA, labelled PASS (faithful) or FAIL. The prompt is the paper's Appendix
A.2 evaluation prompt (verbatim from the Lynx-8B model card on HuggingFace), zero-shot, answered
as JSON with "REASONING" and "SCORE". The paper reports accuracy per source (Table 3); intervals
here bootstrap over passages within each source, since the perturbed DROP/CovidQA/PubMedQA
samples share passages with their originals.

    uv run --extra llm --with pyarrow python scripts/halubench_judge.py --out runs/halubench/x
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from evalkit.llmcache import CachedCompleter
from evalkit.models import Completer, get_model

REV = "5966a87929f51c204ab3cbef986b449495cc97b6"
URL = (
    "https://huggingface.co/datasets/PatronusAI/HaluBench/resolve/"
    f"{REV}/data/test-00000-of-00001.parquet"
)
DATA = Path.home() / ".cache" / "evalkit" / "halubench" / f"test-{REV[:7]}.parquet"
PROMPT = """Given the following QUESTION, DOCUMENT and ANSWER you must analyze the provided answer and determine whether it is faithful to the contents of the DOCUMENT. The ANSWER must not offer new information beyond the context provided in the DOCUMENT. The ANSWER also must not contradict information provided in the DOCUMENT. Output your final verdict by strictly following this format: "PASS" if the answer is faithful to the DOCUMENT and "FAIL" if the answer is not faithful to the DOCUMENT. Show your reasoning.

--
QUESTION (THIS DOES NOT COUNT AS BACKGROUND INFORMATION):
{question}

--
DOCUMENT:
{context}

--
ANSWER:
{answer}

--

Your output should be in JSON FORMAT with the keys "REASONING" and "SCORE":
{{"REASONING": <your reasoning as bullet points>, "SCORE": <your final score>}}
"""  # noqa: E501
MAX_TOKENS = 1024
SCORE = re.compile(r'"?SCORE"?\s*:\s*"?(PASS|FAIL)', re.IGNORECASE)
P_FAIL = re.compile(r'"?P_FAIL"?\s*:\s*"?([01](?:\.\d+)?|\.\d+)')
LONG_WORDS = 30


def load() -> list[dict]:
    import pyarrow.parquet as pq

    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, DATA)
    return pq.read_table(DATA).to_pylist()


def prompt(r: dict, rule: str = "") -> str:
    """The paper's prompt; a rule's text, if any, goes right after "Show your reasoning.".

    `{extract_check}` in a rule (rule v4) becomes whether the answer is, whitespace aside, a
    word-for-word substring of the passage.
    """
    text = PROMPT.format(question=r["question"], context=r["passage"], answer=r["answer"])
    extract = " ".join(r["answer"].split()) in " ".join(r["passage"].split())
    rule = rule.replace("{extract_check}", "appears" if extract else "does not appear")
    anchor = "Show your reasoning.\n"
    return text.replace(anchor, f"{anchor}\n{rule.strip()}\n", 1) if rule else text


def is_dev(r: dict) -> bool:
    """Seeded 30% tuning split, grouped by passage so a passage never sits on both sides."""
    digest = hashlib.sha256(("hb-dev|" + r["passage"]).encode()).hexdigest()
    return int(digest, 16) % 10 < 3


def verdict(text: str) -> str | None:
    """The last SCORE in the reply: PASS, FAIL, or None if there is none."""
    hits = SCORE.findall(text)
    return hits[-1].upper() if hits else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--judge", default="claude-sonnet-5-5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rule", help="text file appended to the paper's instructions")
    ap.add_argument("--split", choices=("all", "dev", "held"), default="all")
    ap.add_argument("--cut", type=float, help="flag P_FAIL >= cut instead of SCORE (rule v3)")
    ap.add_argument("--cut-long", type=float, help=f"cut for answers over {LONG_WORDS} words")
    ap.add_argument("--fallback", help="another run's verdicts.jsonl, used where this one has none")
    args = ap.parse_args()

    rows = [r for r in load() if args.split == "all" or is_dev(r) == (args.split == "dev")]
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
        # a reply without P_FAIL (or a refusal) counts as FAIL, like one without a SCORE
        p_fail = [float(m[-1]) if (m := P_FAIL.findall(t)) else None for t in texts]
        long_cut = args.cut if args.cut_long is None else args.cut_long
        cuts = [long_cut if len(r["answer"].split()) > LONG_WORDS else args.cut for r in rows]
        pairs = zip(p_fail, cuts, strict=True)
        found = [None if p is None else "FAIL" if p >= c else "PASS" for p, c in pairs]
    missing = sum(v is None for v in found)
    if args.fallback:
        with open(args.fallback) as f:
            other = {row["id"]: row["verdict"] for row in map(json.loads, f)}
        found = [other[r["id"]] if v is None else v for r, v in zip(rows, found, strict=True)]
    # an unparsable reply counts as FAIL (hallucination flagged)
    pred = np.array([v != "PASS" for v in found])
    with (out / "verdicts.jsonl").open("w") as f:
        for r, v in zip(rows, found, strict=True):
            f.write(json.dumps({"id": r["id"], "source": r["source_ds"], "verdict": v}) + "\n")

    gold = np.array([r["label"] == "FAIL" for r in rows])
    src = np.array([r["source_ds"] for r in rows])
    passage = np.array([r["passage"] for r in rows])
    names = sorted(set(src))
    rng = np.random.default_rng(0)
    boots = np.zeros((len(names), 1000))
    print(len(rows), "items,", missing, "replies without a verdict (before any fallback)")
    print("source             n    Acc  [95% CI]        BAcc")
    for k, name in enumerate(names):
        m = np.flatnonzero(src == name)
        inv = np.unique(passage[m], return_inverse=True)[1]
        groups = [m[inv == g] for g in range(inv.max() + 1)]
        for b in range(boots.shape[1]):
            idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
            boots[k, b] = (pred[idx] == gold[idx]).mean()
        lo, hi = np.percentile(boots[k], [2.5, 97.5])
        acc = (pred[m] == gold[m]).mean()
        bacc = np.mean([(pred[m][gold[m] == c] == c).mean() for c in (False, True)])
        print(f"{name:14} {len(m):5} {acc:6.1%} [{lo:5.1%}, {hi:5.1%}] {bacc:6.1%}")
    lo, hi = np.percentile(boots.mean(axis=0), [2.5, 97.5])
    mean = np.mean([(pred[src == n] == gold[src == n]).mean() for n in names])
    print(f"{'mean of sources':14} {len(rows):5} {mean:6.1%} [{lo:5.1%}, {hi:5.1%}]")
    print(f"{'pooled':14} {len(rows):5} {(pred == gold).mean():6.1%}")


if __name__ == "__main__":
    main()
