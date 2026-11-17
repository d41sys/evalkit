"""Build the label pool and fixed split for the ezc answer judge (issue #5).

Items are every kept session (both models) from the heldout-v1..v3 runs whose case targets a
text failure mode (`ungrounded`, `omitted`): the user prompt, every tool result, and all
assistant text of the turn. The split is per case, so a case's two sessions share a split:
cases are stratified by whether any session fails the code check, then 15% train,
42.5% dev, 42.5% test. Seeded: rerunning gives the same pool and split.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "ezc"
RUNS = ["2026-11-17-heldout-v1", "2026-11-17-heldout-v2", "2026-11-17-heldout-v3"]
RERUN = "2026-11-17-judge-rerun"  # pool 2: the `ungrounded` cases run again, new sessions
MODES = ("ungrounded", "omitted")
TRAIN, DEV_END = 0.15, 0.575
SEED = 5


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    texts = (c.get("text", "") for c in content if isinstance(c, dict) and c["type"] == "text")
    return "".join(texts)


def _tool_data(text: str) -> str:
    m = re.search(r"<tool_data[^>]*>\s*(.*?)\s*</tool_data>", text, re.S)
    return m.group(1) if m else text


def session(path: Path) -> dict:
    prompt, tools, answer = "", [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("type") != "message":
            continue
        msg = row["message"]
        if msg["role"] == "user" and not prompt:
            prompt = _text(msg["content"])
        elif msg["role"] == "toolResult":
            tools.append({"tool": msg.get("toolName"), "result": _tool_data(_text(msg["content"]))})
        elif msg["role"] == "assistant":
            t = _text(msg["content"]).strip()
            if t:
                answer.append(t)
    return {"prompt": prompt, "tool_results": tools, "answer": "\n\n".join(answer)}


def main() -> None:
    rng = random.Random(SEED)
    pool: list[dict] = []
    for mode in MODES:
        cases: dict[str, list[dict]] = {}
        for run in RUNS:
            review = (ROOT / run / "broken-review.jsonl").read_text().splitlines()
            dropped = {r["id"] for r in map(json.loads, review) if r["verdict"] == "drop"}
            for res in sorted((ROOT / run).glob("anthropic-*/results.json")):
                report = json.loads(res.read_text())
                for case in report["cases"]:
                    if f"-{mode}-" not in case["id"] or case["id"] in dropped:
                        continue
                    item = {
                        "case": case["id"],
                        "model": report["ref"],
                        "mode": mode,
                        "code_pass": int(case["pass"]),
                    }
                    item |= session(res.parent / f"{case['id']}.jsonl")
                    cases.setdefault(case["id"], []).append(item)
        for any_fail in (True, False):
            ids = sorted(
                c for c, its in cases.items() if any_fail != all(i["code_pass"] for i in its)
            )
            rng.shuffle(ids)
            for i, case_id in enumerate(ids):
                frac = i / len(ids)
                split = "train" if frac < TRAIN else "dev" if frac < DEV_END else "test"
                pool += [dict(it, split=split) for it in cases[case_id]]
    rng.shuffle(pool)
    for n, it in enumerate(pool, 1):
        it["id"] = f"j{n:03d}"
    out = ROOT / "judge-v1" / "pool.jsonl"
    out.parent.mkdir(exist_ok=True)
    lines = (json.dumps(it, ensure_ascii=False) + "\n" for it in pool)
    out.write_text("".join(lines), encoding="utf-8")
    counts: dict[tuple, int] = {}
    for it in pool:
        key = (it["mode"], it["split"], it["code_pass"])
        counts[key] = counts.get(key, 0) + 1
    for key in sorted(counts):
        print(*key, counts[key])

    # pool 2 keeps each case's pool-1 split, so its test sessions share no case with train/dev
    case_split = {it["case"]: it["split"] for it in pool}
    pool2: list[dict] = []
    for res in sorted((ROOT / RERUN).glob("anthropic-*/results.json")):
        report = json.loads(res.read_text())
        for case in report["cases"]:
            item = {
                "case": case["id"],
                "model": report["ref"],
                "mode": "ungrounded",
                "code_pass": int(case["pass"]),
                "split": case_split[case["id"]],
            }
            pool2.append(item | session(res.parent / f"{case['id']}.jsonl"))
    rng.shuffle(pool2)
    for n, it in enumerate(pool2, 1):
        it["id"] = f"k{n:03d}"
    lines = (json.dumps(it, ensure_ascii=False) + "\n" for it in pool2)
    (ROOT / "judge-v1" / "pool-2.jsonl").write_text("".join(lines), encoding="utf-8")
    print("pool-2", len(pool2))


if __name__ == "__main__":
    main()
