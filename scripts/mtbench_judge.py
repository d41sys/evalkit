"""MT-Bench human-judgment validation of the evalkit LLM judge.

Protocol: docs/protocol-judge-mtbench.md.

Subcommands (stdlib + evalkit only; ``uv run --offline python scripts/mtbench_judge.py <cmd>``):

* ``fetch``  download ``lmsys/mt_bench_human_judgments`` (CC-BY-4.0) through the Hugging Face
  datasets-server rows API into ``data/raw/mtbench/`` (no parquet reader is installed).
* ``build``  canonicalise pairs, split off the dev items, sample the test items (seed 0) and
  write ``data/mtbench/dev.jsonl`` and ``data/mtbench/test.jsonl`` (pairs files for
  ``evalkit judge``, with the human votes and the released GPT-4 verdict attached).
* ``run``    judge a split in both orders through the cache (needs ANTHROPIC_API_KEY unless
  every request is already cached; ``--cache-only`` never calls the API).
* ``score``  agreement / kappa / flip / length report with cluster-bootstrap CIs from the cache.

The API key is read from the environment only and is never written anywhere.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

from evalkit.judge import (
    DEFAULT_RUBRIC,
    Judge,
    PointItem,
    PointVerdict,
    pair_item_from_row,
    point_verdict,
    prompt_fingerprint,
)
from evalkit.judge_stats import AgreementData, Estimate, ValItem, cluster_bootstrap
from evalkit.llmcache import CachedCompleter, summarize_cache
from evalkit.models import DEFAULT_ANTHROPIC_MODEL, AnthropicModel

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "mtbench"
OUT = ROOT / "data" / "mtbench"
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows?dataset=lmsys/mt_bench_human_judgments"
    "&config=default&split={split}&offset={offset}&length=100"
)
DATASET_REVISION = "f7d2896d2cc5d80f8b55c2bbc722613555233c25"
CATEGORIES = {
    range(81, 91): "writing",
    range(91, 101): "roleplay",
    range(101, 111): "reasoning",
    range(111, 121): "math",
    range(121, 131): "coding",
    range(131, 141): "extraction",
    range(141, 151): "stem",
    range(151, 161): "humanities",
}
REFERENCE_CATEGORIES = frozenset({"reasoning", "math", "coding"})
SEED = 0
DEV_ITEMS = 60
TEST_ITEMS = 1000
POINTWISE_ITEMS = 300
TURN2_INSTRUCTION = (
    "Each response block is a full two-turn conversation between the user and one assistant. "
    "Judge only the assistant's reply to the user's SECOND message, taking the first turn as "
    "context."
)


def category(qid: int) -> str:
    return next(name for r, name in CATEGORIES.items() if qid in r)


def fetch() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    for split in ("human", "gpt4_pair"):
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            for attempt in range(10):
                try:
                    with urllib.request.urlopen(
                        ROWS_URL.format(split=split, offset=offset), timeout=60
                    ) as r:
                        page = json.load(r)
                    break
                except urllib.error.HTTPError as exc:
                    if exc.code != 429:
                        raise
                    time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit("datasets-server kept answering 429")
            rows += [x["row"] for x in page["rows"]]
            offset += 100
            time.sleep(1.0)
            if offset >= page["num_rows_total"]:
                break
        with (RAW / f"{split}.jsonl").open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{split}: {len(rows)} rows")
    return 0


def _load(split: str) -> list[dict[str, Any]]:
    with (RAW / f"{split}.jsonl").open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _label(winner: str, swapped: bool) -> str:
    if winner.startswith("tie"):
        return "tie"
    a_wins = winner == "model_a"
    return "B" if a_wins == swapped else "A"


def _transcript(conv: list[dict[str, str]], turn: int) -> str:
    parts: list[str] = []
    for msg in conv[: 2 * turn]:
        who = "User" if msg["role"] == "user" else "Assistant"
        parts.append(f"### {who}:\n{msg['content']}")
    return "\n\n".join(parts)


def build() -> int:
    human, gpt4 = _load("human"), _load("gpt4_pair")
    items: dict[tuple[int, str, str, int], dict[str, Any]] = {}
    for row in human:
        a, b = row["model_a"], row["model_b"]
        swapped = a > b
        ma, mb = (b, a) if swapped else (a, b)
        conv_a, conv_b = (
            (row["conversation_b"], row["conversation_a"])
            if swapped
            else (row["conversation_a"], row["conversation_b"])
        )
        key = (row["question_id"], ma, mb, row["turn"])
        item = items.get(key)
        if item is None:
            turn = row["turn"]
            last_a = conv_a[2 * turn - 1]["content"]
            last_b = conv_b[2 * turn - 1]["content"]
            qid = row["question_id"]
            if turn == 1:
                prompt, resp_a, resp_b, instruction = (
                    conv_a[0]["content"],
                    last_a,
                    last_b,
                    None,
                )
            else:
                prompt = "Second user message of a two-turn conversation:\n" + conv_a[2]["content"]
                resp_a, resp_b = _transcript(conv_a, 2), _transcript(conv_b, 2)
                instruction = TURN2_INSTRUCTION
            item = {
                "id": f"q{qid}-t{turn}-{ma}-vs-{mb}",
                "task": f"mt-bench-turn{turn}",
                "cluster_id": f"q{qid}",
                "question_id": qid,
                "category": category(qid),
                "turn": turn,
                "model_a": ma,
                "model_b": mb,
                "prompt": prompt,
                "instruction": instruction,
                "response_a": resp_a,
                "response_b": resp_b,
                "length_a": len(last_a.split()),
                "length_b": len(last_b.split()),
                "human_votes": [],
                "gpt4_verdict": None,
            }
            items[key] = item
        item["human_votes"].append([row["judge"], _label(row["winner"], swapped)])
    for row in gpt4:
        a, b = row["model_a"], row["model_b"]
        swapped = a > b
        key = (row["question_id"], *((b, a) if swapped else (a, b)), row["turn"])
        if key in items:
            items[key]["gpt4_verdict"] = _label(row["winner"], swapped)

    rng = random.Random(SEED)
    by_cat: dict[str, list[int]] = defaultdict(list)
    for qid in sorted({k[0] for k in items}):
        by_cat[category(qid)].append(qid)
    dev_questions = sorted(rng.choice(qs) for _, qs in sorted(by_cat.items()))
    dev_pool = sorted((v for k, v in items.items() if k[0] in dev_questions), key=lambda v: v["id"])
    test_pool = sorted(
        (v for k, v in items.items() if k[0] not in dev_questions), key=lambda v: v["id"]
    )
    dev = rng.sample(dev_pool, min(DEV_ITEMS, len(dev_pool)))
    test = rng.sample(test_pool, min(TEST_ITEMS, len(test_pool)))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("dev", dev), ("test", test)):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for order, row in enumerate(rows):
                f.write(json.dumps({**row, "order": order}, ensure_ascii=False) + "\n")
    votes = sum(len(v["human_votes"]) for v in test)
    print(
        f"items {len(items)}; dev questions {dev_questions}; dev {len(dev)} of {len(dev_pool)}; "
        f"test {len(test)} of {len(test_pool)} ({votes} human votes, "
        f"{len({v['question_id'] for v in test})} questions)"
    )
    return 0


def _read_pairs(split: str) -> list[dict[str, Any]]:
    with (OUT / f"{split}.jsonl").open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _completer(args: argparse.Namespace) -> CachedCompleter:
    cache = Path(args.cache)
    if args.cache_only:
        return CachedCompleter(None, cache, model_id=args.model, max_calls=args.max_calls)
    return CachedCompleter(
        AnthropicModel(model_id=args.model), cache, model_id=args.model, max_calls=args.max_calls
    )


def run(args: argparse.Namespace) -> int:
    rows = _read_pairs(args.split)
    if args.limit:
        rows = rows[: args.limit]
    completer = _completer(args)
    judge = Judge(completer, workers=args.workers)
    if args.mode == "pairwise":
        judge.compare_many([pair_item_from_row(r) for r in rows])
    else:
        pts: list[PointItem] = []
        for r in rows:
            pts.append(PointItem(r["prompt"], r["response_a"], instruction=r["instruction"]))
            pts.append(PointItem(r["prompt"], r["response_b"], instruction=r["instruction"]))
        judge.score_many(pts)
    s = completer.stats
    print(
        f"{args.split} {args.mode}: {len(rows)} items, live calls {s.live_calls}, cache hits "
        f"{s.hits}, tokens in/out {s.input_tokens}/{s.output_tokens}"
    )
    return 0


def _val_items(rows: list[dict[str, Any]], judge: Judge, with_gpt4: bool = True) -> list[ValItem]:
    verdicts = judge.compare_many([pair_item_from_row(r) for r in rows])
    out: list[ValItem] = []
    for r, v in zip(rows, verdicts, strict=True):
        out.append(
            ValItem(
                cluster=r["cluster_id"],
                verdict=v.resolved,
                votes=tuple((j, lab) for j, lab in r["human_votes"]),
                length_diff=float(r["length_a"] - r["length_b"]),
                flipped=v.flipped,
                same_slot=v.same_slot,
                both_valid=v.both_valid,
                other=r["gpt4_verdict"] if with_gpt4 else None,
            )
        )
    return out


def _fmt(e: Estimate, pct: bool = True) -> str:
    if pct:
        return f"{100 * e.value:.1f}% [{100 * e.lo:.1f}, {100 * e.hi:.1f}]"
    return f"{e.value:+.3f} [{e.lo:+.3f}, {e.hi:+.3f}]"


def _fmt_pp(e: Estimate) -> str:
    return f"{100 * e.value:+.1f} pp [{100 * e.lo:+.1f}, {100 * e.hi:+.1f}]"


PAPER = {  # Zheng et al. 2023, Table 5 (a)/(b): G4-Pair vs Human and Human vs Human
    1: {"g4_s1": 0.66, "g4_s2": 0.85, "hh_s1": 0.63, "hh_s2": 0.81},
    2: {"g4_s1": 0.66, "g4_s2": 0.84, "hh_s1": 0.67, "hh_s2": 0.82},
}


def _group_table(name: str, est: dict[str, Estimate], counts: dict[str, int]) -> list[str]:
    lines = [
        f"#### {name}",
        "",
        f"{counts['items']} items, {counts['clusters']} questions, {counts['votes']} human votes; "
        f"S2 judge-human items {counts['items_s2']}, human-human items "
        f"S1 {counts['items_hh_s1']} / S2 {counts['items_hh_s2']}.",
        "",
        "| Metric | Estimate [95% CI] |",
        "|---|---|",
        f"| judge-human agreement S1 (ties count) | {_fmt(est['jh_s1'])} |",
        f"| judge-human agreement S2 (no ties) | {_fmt(est['jh_s2'])} |",
        f"| Cohen's kappa S1 (3 labels) | {_fmt(est['jh_kappa_s1'], False)} |",
        f"| Cohen's kappa S2 (A/B only) | {_fmt(est['jh_kappa_s2'], False)} |",
        f"| human-human agreement S1 | {_fmt(est['hh_s1'])} |",
        f"| human-human agreement S2 | {_fmt(est['hh_s2'])} |",
        f"| judge minus human-human S1, matched items | {_fmt_pp(est['diff_s1_vs_human'])} |",
        f"| judge minus human-human S2, matched items | {_fmt_pp(est['diff_s2_vs_human'])} |",
    ]
    if "other_s1" in est:
        lines += [
            f"| released GPT-4 (pair) vs human S1, same items | {_fmt(est['other_s1'])} |",
            f"| released GPT-4 (pair) vs human S2, same items | {_fmt(est['other_s2'])} |",
            f"| judge minus GPT-4 S1 | {_fmt_pp(est['diff_s1_vs_other'])} |",
            f"| judge minus GPT-4 S2 | {_fmt_pp(est['diff_s2_vs_other'])} |",
        ]
    lines += [
        f"| position-flip rate (orders disagree) | {_fmt(est['flip_rate'])} |",
        f"| same-slot rate (same position wins in both orders) | {_fmt(est['same_slot_rate'])} |",
        f"| resolved-tie rate, judge | {_fmt(est['judge_tie_rate'])} |",
        f"| tie rate, humans (per vote) | {_fmt(est['human_tie_rate'])} |",
        f"| Spearman rho, judge verdict vs length diff | {_fmt(est['len_rho_judge'], False)} |",
        f"| Spearman rho, mean human vote vs length diff | {_fmt(est['len_rho_human'], False)} |",
        f"| rho judge minus rho human | {_fmt(est['len_rho_diff'], False)} |",
        f"| longer response wins, judge (decided pairs) | {_fmt(est['longer_wins_judge'])} |",
        f"| longer response wins, humans (per vote) | {_fmt(est['longer_wins_human'])} |",
        "",
    ]
    return lines


def score(args: argparse.Namespace) -> int:
    rows = _read_pairs(args.split)
    completer = CachedCompleter(None, args.cache, model_id=args.model)
    judge = Judge(completer)
    items = _val_items(rows, judge)
    lines: list[str] = []
    groups: list[tuple[str, list[int]]] = [
        ("All items", list(range(len(rows)))),
        ("Turn 1", [i for i, r in enumerate(rows) if r["turn"] == 1]),
        ("Turn 2", [i for i, r in enumerate(rows) if r["turn"] == 2]),
        (
            "Categories without reference need (writing, roleplay, extraction, STEM, humanities)",
            [i for i, r in enumerate(rows) if r["category"] not in REFERENCE_CATEGORIES],
        ),
        (
            "Categories where Zheng et al. gave GPT-4 a reference (reasoning, math, coding)",
            [i for i, r in enumerate(rows) if r["category"] in REFERENCE_CATEGORIES],
        ),
        (
            "Items that include claude-v1 (self-preference check, descriptive)",
            [i for i, r in enumerate(rows) if "claude-v1" in (r["model_a"], r["model_b"])],
        ),
        (
            "Items without claude-v1",
            [i for i, r in enumerate(rows) if "claude-v1" not in (r["model_a"], r["model_b"])],
        ),
    ]
    results: dict[str, Any] = {}
    for name, idx in groups:
        data = AgreementData([items[i] for i in idx])
        est = cluster_bootstrap(data.statistics, data.cluster, n_boot=args.boot, seed=SEED)
        lines += _group_table(name, est, data.counts())
        results[name] = {k: [e.value, e.lo, e.hi] for k, e in est.items()}
    invalid = sum(1 for it in items if not it.both_valid)
    summary = summarize_cache(args.cache)
    header = [
        f"### Judge validation on MT-Bench human judgments, split `{args.split}`",
        "",
        f"claude-sonnet-5-5 via Anthropic API, models returned {summary['models_returned']}, "
        f"calls recorded {summary['first']} to {summary['last']}, no logprobs. "
        f"Prompt fingerprint `{prompt_fingerprint()}`. Items where a reply had no parsable "
        f"verdict: {invalid} of {len(items)} (resolved to tie).",
        f"Cache: {summary['calls']} calls, {summary['input_tokens']} input and "
        f"{summary['output_tokens']} output tokens.",
        "",
    ]
    text = "\n".join(header + lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(
            json.dumps(results, indent=1) + "\n", encoding="utf-8"
        )
    return 0


def score_pointwise(args: argparse.Namespace) -> int:
    """Agreement of pairwise verdicts derived from two pointwise scores (G4-Single style)."""
    rows = _read_pairs(args.split)[: args.limit]
    completer = CachedCompleter(None, args.cache, model_id=args.model)
    judge = Judge(completer, rubric=DEFAULT_RUBRIC)
    pts: list[PointItem] = []
    for r in rows:
        pts.append(PointItem(r["prompt"], r["response_a"], instruction=r["instruction"]))
        pts.append(PointItem(r["prompt"], r["response_b"], instruction=r["instruction"]))
    scored: list[PointVerdict] = judge.score_many(pts)
    items: list[ValItem] = []
    for i, r in enumerate(rows):
        sa, sb = scored[2 * i].score, scored[2 * i + 1].score
        items.append(
            ValItem(
                cluster=r["cluster_id"],
                verdict=point_verdict(sa, sb),
                votes=tuple((j, lab) for j, lab in r["human_votes"]),
                length_diff=float(r["length_a"] - r["length_b"]),
                other=r["gpt4_verdict"],
            )
        )
    data = AgreementData(items)
    est = cluster_bootstrap(data.statistics, data.cluster, n_boot=args.boot, seed=SEED)
    missing = sum(1 for p in scored if p.score is None)
    lines = [
        f"### Pointwise-derived verdicts, first {len(rows)} test items (secondary)",
        "",
        f"Unparsable scores {missing} of {len(scored)} (the pair is then a tie).",
        "",
        *_group_table("Pointwise (score A vs score B; equal = tie)", est, data.counts()),
    ]
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    sub.add_parser("build")
    for name in ("run", "score", "score-pointwise"):
        sp = sub.add_parser(name)
        sp.add_argument("--split", choices=["dev", "test"], default="dev")
        sp.add_argument("--cache", default=None, help="default: data/mtbench/cache-<split>.jsonl")
        sp.add_argument("--model", default=DEFAULT_ANTHROPIC_MODEL)
        sp.add_argument("--limit", type=int, default=0)
        sp.add_argument("--max-calls", type=int, default=4000)
        sp.add_argument("--workers", type=int, default=8)
        sp.add_argument("--cache-only", action="store_true")
        sp.add_argument("--mode", choices=["pairwise", "pointwise"], default="pairwise")
        sp.add_argument("--boot", type=int, default=2000)
        sp.add_argument("--out", default=None)
    args = p.parse_args(argv)
    if getattr(args, "cache", "x") is None:
        args.cache = str(OUT / f"cache-{args.split}.jsonl")
    if args.cmd == "fetch":
        return fetch()
    if args.cmd == "build":
        return build()
    if args.cmd == "run":
        return run(args)
    if args.cmd == "score":
        return score(args)
    if args.cmd == "score-pointwise":
        args.limit = args.limit or POINTWISE_ITEMS
        return score_pointwise(args)
    return 1


if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" in os.environ and not os.environ["ANTHROPIC_API_KEY"]:
        sys.exit("ANTHROPIC_API_KEY is set but empty")
    sys.exit(main())
