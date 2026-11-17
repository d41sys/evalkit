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
    "ungrounded": Rubric(
        "grounded",
        "Score 0 if the response states as fact a number, unit, date, duration, name, id, a "
        "fact about data, tasks, runs, configs or parameters, or a claim about how the "
        "forecasting system behaves, that neither the tool results nor the user's own words "
        "support. Also counts: a number derived by arithmetic the tools did not do (e.g. 96 "
        "steps x 15 min = 24 hours), and a unit or unit conversion asserted without a tool "
        "stating it, including a unit read off a column name and stated as fact ('load_kw, so "
        "kilowatt'); a clearly hedged inference ('probably kW, the column is load_kw') does "
        "not count. Telling the user to set a specific named config field or tool parameter "
        "the tools never showed counts. Never count: statements about what the assistant or "
        "the system offers or lacks (features, supported forecast types, 'not available in "
        "this system', which metrics it reports), since its system prompt is not shown; "
        "asking the user for information (a task id, coordinates); generic advice without a "
        "named field (a smaller batch size); plans, offers, questions, restating the user, "
        "general definitions (MAE is in the target's unit), standard acronym expansions, and "
        "rewording of tool values. Score "
        "1 otherwise. Give SCORE: 0 or SCORE: 1, nothing in between.",
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
    ap.add_argument("--pool", choices=("1", "2", "3"), action="append", help="default: 1 and 2")
    # 5 samples at the API's default temperature, majority vote (Lail 2026, arXiv 2604.13717)
    ap.add_argument("--samples", type=int, default=5, help="majority vote over k samples")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    names = {"1": "", "2": "-2", "3": "-3"}
    pool, labels = [], {}
    for p in args.pool or ["1", "2"]:
        pool += [json.loads(line) for line in (POOL / f"pool{names[p]}.jsonl").open()]
        label_rows = map(json.loads, (POOL / f"labels{names[p]}.jsonl").open())
        labels |= {r["id"]: r["label"] for r in label_rows}
    items = [it for it in pool if it["mode"] == args.mode and it["split"] == args.split]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    backend = get_model(f"anthropic:{args.judge}")
    assert isinstance(backend, Completer)
    rubric = RUBRICS[args.mode]
    votes: list[list[float | None]] = []
    for s in range(args.samples):
        cache = out / ("judge-cache.jsonl" if s == 0 else f"judge-cache-{s}.jsonl")
        completer = CachedCompleter(backend, cache, model_id=args.judge)
        judge = Judge(completer, rubric=rubric)
        got = judge.score_many([PointItem(request(it), it["answer"]) for it in items])
        votes.append([v.score for v in got])
    # an unparsable reply is a fail vote; the count is printed
    scores = [float(sum(v or 0 for v in vs) * 2 > len(vs)) for vs in zip(*votes, strict=True)]

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
        for it, vs in zip(items, zip(*votes, strict=True), strict=True):
            f.write(json.dumps({"id": it["id"], "votes": list(vs)}) + "\n")
    n_none = sum(v is None for vs in votes for v in vs)
    print(len(items), "items,", n_none, "unparsable replies")


if __name__ == "__main__":
    main()
