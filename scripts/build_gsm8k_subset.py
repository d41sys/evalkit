"""Build a seeded GSM8K subset as an evalkit task dataset.

Source: https://github.com/openai/grade-school-math (MIT licence, Copyright (c) 2021 OpenAI;
Cobbe et al. 2021, "Training Verifiers to Solve Math Word Problems", arXiv 2110.14168).

Download grade_school_math/data/test.jsonl (and train.jsonl) from that repo to
data/raw/gsm8k_test.jsonl (gitignored), then:

    python scripts/build_gsm8k_subset.py --split test --n 300 --seed 0 \\
        --out tasks_hard/gsm8k/data.jsonl

The subset is the first ``n`` rows of a seeded permutation of the split, so a smaller ``n`` is
a prefix of a larger one. Row ``id`` carries the index in the original file. ``target`` is the
number after ``####`` with thousands commas removed.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path


def build(source: Path, n: int, seed: int, split: str) -> list[dict[str, str]]:
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    out: list[dict[str, str]] = []
    for idx in order[:n]:
        final = rows[idx]["answer"].split("####")[-1].strip().replace(",", "")
        if not re.fullmatch(r"-?\d+", final):
            raise ValueError(f"row {idx}: unexpected final answer {final!r}")
        out.append(
            {
                "id": f"gsm8k_{split}_{idx:04d}",
                "question": rows[idx]["question"],
                "target": final,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path, help="default: data/raw/gsm8k_<split>.jsonl")
    ap.add_argument("--split", choices=["test", "train"], default="test")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    source = args.source or Path(f"data/raw/gsm8k_{args.split}.jsonl")
    rows = build(source, args.n, args.seed, args.split)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
