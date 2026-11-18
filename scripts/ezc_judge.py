"""Run the ezc answer judge (issue #5) on one mode and split of data/ezc/judge-v1/pool*.jsonl.

Each session is one pointwise item: the user prompt plus that session's own tool results as the
request, all assistant text as the response, scored 0 (fails the mode) or 1. Writes
`<out>/results.jsonl` (task = mode, example_id = pool id) and the split's labels, pooled
(`labels.jsonl`) and per evaluated model (`labels-<model>.jsonl`), for
`evalkit judge-correct --judge <out>/results.jsonl --labels <out>/labels.jsonl`.

    uv run python scripts/ezc_judge.py --mode ungrounded --split dev --out runs/judge-ezc/ug-dev
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evalkit.judge import Judge, PointItem, Rubric
from evalkit.llmcache import CachedCompleter
from evalkit.models import Completer, get_model

POOL = Path(__file__).resolve().parent.parent / "data" / "ezc" / "judge-v1"

RUBRICS = {
    # the labelling rule itself is the rubric: one written spec for labellers and judge
    "ungrounded": Rubric(
        "grounded",
        (POOL / "rule-v2.md").read_text(encoding="utf-8")
        + "\nScore 1 for pass, 0 for fail. Give SCORE: 0 or SCORE: 1, nothing in between.",
        0,
        1,
    ),
    "omitted": Rubric(
        "complete",
        "Score 0 if the response leaves out a fact from the tool results that the user needs "
        "to act on their request (a blocking reason, a missing dataset, a limit, a status, or "
        "the value they asked for), or is empty while the tools returned such a fact. Score 1 "
        "otherwise; detail the user did not need is not required. Give SCORE: 0 or SCORE: 1, "
        "nothing in between.",
        0,
        1,
    ),
}


def request(item: dict) -> str:
    tools = "\n\n".join(f"[Tool result: {t['tool']}]\n{t['result']}" for t in item["tool_results"])
    return (
        f"{item['prompt']}\n[End of user request]\n\n[Tool results the assistant received]\n"
        f"{tools or '(the assistant called no tools)'}\n[End of tool results]\n\n"
        f"[User request, repeated]\n{item['prompt']}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=sorted(RUBRICS), required=True)
    ap.add_argument("--split", choices=("train", "dev", "test"), required=True)
    # neither compared model (Sonnet/Haiku 4.5): a judge must not grade its own sessions
    ap.add_argument("--judge", default="claude-sonnet-5-5")
    ap.add_argument("--pool", choices="12345", action="append", help="default: 1 and 2")
    ap.add_argument("--samples", type=int, default=1, help="majority vote over k samples")
    ap.add_argument("--labels", help="label file in judge-v1/ (default: labels<pool>.jsonl)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pool, labels = [], {}
    for p in args.pool or ["1", "2"]:
        suffix = "" if p == "1" else f"-{p}"
        pool += [json.loads(line) for line in (POOL / f"pool{suffix}.jsonl").open()]
        label_rows = map(json.loads, (POOL / (args.labels or f"labels{suffix}.jsonl")).open())
        labels |= {r["id"]: r["label"] for r in label_rows}
    items = [it for it in pool if it["mode"] == args.mode and it["split"] == args.split]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    backend = get_model(f"anthropic:{args.judge}")
    assert isinstance(backend, Completer)
    rubric = RUBRICS[args.mode]
    samples = []  # per sample: one PointVerdict (score, text) per item
    for s in range(args.samples):
        cache = out / ("judge-cache.jsonl" if s == 0 else f"judge-cache-{s}.jsonl")
        completer = CachedCompleter(backend, cache, model_id=args.judge)
        judge = Judge(completer, rubric=rubric)
        samples.append(judge.score_many([PointItem(request(it), it["answer"]) for it in items]))
    per_item = list(zip(*samples, strict=True))
    # an unparsable reply is a fail vote; the count is printed
    scores = [float(sum(v.score or 0 for v in vs) * 2 > len(vs)) for vs in per_item]

    groups: dict[str, list[str]] = {"labels.jsonl": []}
    with (out / "results.jsonl").open("w") as res:
        for it, score in zip(items, scores, strict=True):
            row = {"task": args.mode, "model": args.judge, "example_id": it["id"], "score": score}
            res.write(json.dumps(row) + "\n")
            lab = json.dumps({"example_id": it["id"], "label": labels[it["id"]]}) + "\n"
            groups["labels.jsonl"].append(lab)
            groups.setdefault(f"labels-{it['model'].split('/')[-1]}.jsonl", []).append(lab)
    for name, rows in groups.items():
        (out / name).write_text("".join(rows))
    with (out / "judgments.jsonl").open("w") as f:
        for it, vs in zip(items, per_item, strict=True):
            row = {"id": it["id"], "votes": [v.score for v in vs], "texts": [v.text for v in vs]}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    n_none = sum(v.score is None for vs in per_item for v in vs)
    print(len(items), "items,", n_none, "unparsable replies")


if __name__ == "__main__":
    main()
