"""Write a simulated results.jsonl with clustered items and several samples per item.

Simulation only: no model is run and no data is downloaded. 40 "passages" of 5 questions each;
three models whose per-passage success probability is ``clip(q_c + shift_m + 0.15 z_mc)``, with
``q_c ~ U(0.2, 0.8)`` the passage difficulty shared by every model and ``z_mc ~ N(0, 1)`` a
model x passage interaction (this is what makes paired differences cluster). Every question is
answered 3 times (independent Bernoulli draws, ``sample`` = 0, 1, 2). Seed 0.

    uv run --offline python scripts/make_clustered_demo.py runs/clustered-demo/results.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

MODELS = {"model_a": 0.06, "model_b": 0.0, "model_c": -0.06}
PASSAGES = 40
QUESTIONS = 5
SAMPLES = 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", type=Path)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    difficulty = rng.uniform(0.2, 0.8, PASSAGES)
    p = {
        name: np.clip(difficulty + shift + 0.15 * rng.standard_normal(PASSAGES), 0.02, 0.98)
        for name, shift in MODELS.items()
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for c in range(PASSAGES):
            for q in range(QUESTIONS):
                for name in MODELS:
                    for s in range(SAMPLES):
                        row = {
                            "task": "passage_qa",
                            "model": name,
                            "example_id": f"p{c:02d}_q{q}",
                            "score": float(rng.random() < p[name][c]),
                            "cluster_id": f"passage_{c:02d}",
                            "sample": s,
                        }
                        f.write(json.dumps(row) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
