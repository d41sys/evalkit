"""Tie margin for the pointwise MT-Bench judge (protocol: docs/protocol-judge-ties.md).

Cache replay only (no backend, no key, no network): a request that is not in
``data/mtbench/cache-test.jsonl`` raises ``CacheMiss``.

    uv run --offline python scripts/mtbench_tie_margin.py dev
    uv run --offline python scripts/mtbench_tie_margin.py confirm
    uv run --offline python scripts/mtbench_tie_margin.py sensitivity
    uv run --offline python scripts/mtbench_tie_margin.py posthoc

``dev`` chooses the margin by leave-question-out cross-validation on the dev portion of the 71
questions of the first 300 test items and writes ``docs/results/judge-mtbench-tie-margin-dev.json``.
``confirm`` reads that file and scores the confirmation portion once against the pre-registered
rule. ``sensitivity`` drops the unparsable replies (pre-registered). ``posthoc`` looks at the
pooled 300 items (not pre-registered). S1 and S2 are ``jh_s1`` / ``jh_s2`` of
``evalkit.judge_stats.AgreementData``, unchanged.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtbench_judge import (
    DEFAULT_ANTHROPIC_MODEL,
    OUT,
    POINTWISE_ITEMS,
    SEED,
    _fmt,
    _fmt_pp,
    _read_pairs,
    _val_items,
)

from evalkit.judge import DEFAULT_RUBRIC, Judge, PointItem
from evalkit.judge_stats import (
    AgreementData,
    Estimate,
    Label,
    ValItem,
    cluster_bootstrap,
)
from evalkit.llmcache import CachedCompleter

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "docs" / "results"
DEV_JSON = RESULTS / "judge-mtbench-tie-margin-dev.json"
SCORES_JSONL = OUT / "tie-margin-scores.jsonl"
GRID = (0.0, 1.0, 2.0, 3.0)
DEV_QUESTIONS = 36
BOOT = 2000
WORKERS = 2


def margin_verdict(score_a: float | None, score_b: float | None, delta: float) -> Label:
    """``tie`` when ``|score_a - score_b| <= delta`` (or a score is missing), else the higher."""
    if score_a is None or score_b is None or abs(score_a - score_b) <= delta:
        return "tie"
    return "A" if score_a > score_b else "B"


def split_questions(clusters: Sequence[str], seed: int = SEED) -> tuple[list[str], list[str]]:
    """(dev, confirmation) question ids: sorted as strings, shuffled with ``random.Random(seed)``,
    the first :data:`DEV_QUESTIONS` are dev."""
    ids = sorted(set(clusters))
    random.Random(seed).shuffle(ids)
    return ids[:DEV_QUESTIONS], ids[DEV_QUESTIONS:]


def val_items(
    rows: Sequence[Mapping[str, Any]],
    scores: Sequence[tuple[float | None, float | None]],
    delta: float,
) -> list[ValItem]:
    """One :class:`ValItem` per row with the margin verdict of its two pointwise scores."""
    return [
        ValItem(
            cluster=str(r["cluster_id"]),
            verdict=margin_verdict(sa, sb, delta),
            votes=tuple((j, lab) for j, lab in r["human_votes"]),
            length_diff=float(r["length_a"] - r["length_b"]),
            other=r["gpt4_verdict"],
        )
        for r, (sa, sb) in zip(rows, scores, strict=True)
    ]


def choose_delta(per_item_s1: Mapping[float, np.ndarray], idx: np.ndarray) -> float:
    """Grid value with the largest mean S1 over ``idx``; ties go to the smaller margin."""
    best = max(per_item_s1, key=lambda d: (round(float(per_item_s1[d][idx].mean()), 12), -d))
    return float(best)


def loqo_selection(
    per_item_s1: Mapping[float, np.ndarray], clusters: Sequence[str]
) -> dict[str, Any]:
    """Leave-question-out selection on one portion.

    ``cv`` is the pooled held-out S1 of each fixed margin (nothing is fitted on the training
    questions, so it equals the portion's S1). ``nested`` selects the margin inside every fold on
    the other questions and scores the held-out question with it.
    """
    cl = np.asarray(clusters)
    questions = sorted(set(clusters))
    n = cl.size
    everything = np.arange(n)
    cv = {d: float(per_item_s1[d].mean()) for d in per_item_s1}
    delta_hat = choose_delta(per_item_s1, everything)
    out_of_fold = np.empty(n)
    chosen: dict[float, int] = {d: 0 for d in per_item_s1}
    for q in questions:
        held = cl == q
        d = choose_delta(per_item_s1, np.flatnonzero(~held))
        chosen[d] += 1
        out_of_fold[held] = per_item_s1[d][held]
    return {
        "cv_s1": cv,
        "delta_hat": delta_hat,
        "nested_s1": float(out_of_fold.mean()),
        "zero_s1": cv[0.0],
        "fold_choices": {str(d): c for d, c in chosen.items()},
        "folds": len(questions),
    }


def load_scores() -> tuple[list[dict[str, Any]], list[tuple[float | None, float | None]]]:
    """The first 300 test rows and their cached pointwise scores (A, B); replay only."""
    rows = _read_pairs("test")[:POINTWISE_ITEMS]
    completer = CachedCompleter(None, OUT / "cache-test.jsonl", model_id=DEFAULT_ANTHROPIC_MODEL)
    judge = Judge(completer, rubric=DEFAULT_RUBRIC, workers=WORKERS)
    pts: list[PointItem] = []
    for r in rows:
        pts.append(PointItem(r["prompt"], r["response_a"], instruction=r["instruction"]))
        pts.append(PointItem(r["prompt"], r["response_b"], instruction=r["instruction"]))
    scored = judge.score_many(pts)
    scores = [(scored[2 * i].score, scored[2 * i + 1].score) for i in range(len(rows))]
    return rows, scores


def write_scores(
    rows: Sequence[Mapping[str, Any]],
    scores: Sequence[tuple[float | None, float | None]],
    portion: Mapping[str, str],
) -> None:
    SCORES_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with SCORES_JSONL.open("w", encoding="utf-8") as f:
        for r, (sa, sb) in zip(rows, scores, strict=True):
            rec = {
                "id": r["id"],
                "question": str(r["cluster_id"]),
                "portion": portion[str(r["cluster_id"])],
                "score_a": sa,
                "score_b": sb,
            }
            f.write(json.dumps(rec) + "\n")


def _pp(x: float) -> str:
    return f"{100 * x:.1f}%"


def _estimates(est: Mapping[str, Estimate]) -> dict[str, list[float]]:
    return {k: [e.value, e.lo, e.hi] for k, e in est.items()}


def dev(args: argparse.Namespace) -> int:
    rows, scores = load_scores()
    portion = _portions(rows)
    idx = [i for i, r in enumerate(rows) if portion[str(r["cluster_id"])] == "dev"]
    d_rows, d_scores = [rows[i] for i in idx], [scores[i] for i in idx]
    per_s1: dict[float, np.ndarray] = {}
    table: dict[str, dict[str, float]] = {}
    for d in GRID:
        data = AgreementData(val_items(d_rows, d_scores, d))
        per_s1[d] = data.judge.a1.copy()
        stats = data.statistics(np.ones(data.n))
        table[str(d)] = {
            "s1": stats["jh_s1"],
            "s2": stats["jh_s2"],
            "judge_tie_rate": stats["judge_tie_rate"],
            "human_tie_rate": stats["human_tie_rate"],
        }
    sel = loqo_selection(per_s1, [str(r["cluster_id"]) for r in d_rows])
    result = {
        "protocol": "docs/protocol-judge-ties.md",
        "dev_questions": sorted({str(r["cluster_id"]) for r in d_rows}),
        "dev_items": len(d_rows),
        "grid": table,
        **sel,
    }
    write_scores(rows, scores, portion)
    lines = [
        "### Tie margin, dev portion (leave-question-out selection)",
        "",
        f"Dev portion: {len(result['dev_questions'])} questions, {len(d_rows)} items "
        "(first 300 test items, pointwise scores from the cache). CV score = pooled held-out S1 "
        "of a fixed margin, which equals its S1 on the dev portion.",
        "",
        "| delta | CV S1 | S2 | judge tie rate | human tie rate (per vote) |",
        "|---|---|---|---|---|",
    ]
    for d in GRID:
        t = table[str(d)]
        lines.append(
            f"| {d:g} | {_pp(t['s1'])} | {_pp(t['s2'])} | {_pp(t['judge_tie_rate'])} | "
            f"{_pp(t['human_tie_rate'])} |"
        )
    lines += [
        "",
        f"**Selected delta-hat: {sel['delta_hat']:g}** (largest CV S1; ties to the smaller delta).",
        "",
        f"Nested leave-question-out (selection inside each of {sel['folds']} folds): out-of-fold "
        f"S1 {_pp(sel['nested_s1'])} against {_pp(sel['zero_s1'])} at delta 0 on the same items "
        f"({100 * (sel['nested_s1'] - sel['zero_s1']):+.1f} pp, no interval: descriptive). "
        f"Fold choices (delta: folds): {sel['fold_choices']}.",
    ]
    if sel["delta_hat"] == 0:
        lines += ["", "delta-hat = 0: the confirmation portion is not scored (protocol)."]
    _emit(lines, args.out, result, DEV_JSON)
    return 0


def _portions(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    dev_q, conf_q = split_questions([str(r["cluster_id"]) for r in rows])
    return {**dict.fromkeys(dev_q, "dev"), **dict.fromkeys(conf_q, "confirm")}


def _emit(lines: list[str], out: str | None, result: dict[str, Any], default_json: Path) -> None:
    text = "\n".join(lines) + "\n"
    print(text)
    md = Path(out) if out else default_json.with_suffix(".md")
    md.write_text(text, encoding="utf-8")
    default_json.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")


def paired_stat(
    a: AgreementData, b: AgreementData, b_mask: np.ndarray | None = None
) -> Callable[[np.ndarray], dict[str, float]]:
    """Statistic over resample weights: arm ``a``, arm ``b`` (optionally restricted to the items
    in ``b_mask`` by zero weights) and the differences b - a, all on the same weights."""

    def stat(w: np.ndarray) -> dict[str, float]:
        sa = a.statistics(w)
        sb = b.statistics(w if b_mask is None else w * b_mask)
        out: dict[str, float] = {}
        for key in ("jh_s1", "jh_s2", "judge_tie_rate", "human_tie_rate"):
            out[f"a_{key}"] = sa[key]
            out[f"b_{key}"] = sb[key]
        out["d_s1"] = sb["jh_s1"] - sa["jh_s1"]
        out["d_s2"] = sb["jh_s2"] - sa["jh_s2"]
        return out

    return stat


def rule_outcome(d_s1: Estimate, d_s2: Estimate) -> tuple[bool, bool, bool]:
    """(condition 1, condition 2, ship): the pre-registered rule of the protocol."""
    c1 = d_s1.lo > 0
    c2 = d_s2.hi >= 0
    return c1, c2, c1 and c2


RULE = (
    "Ship delta-hat as an opt-in if both hold: 1. the lower bound of the CI of the S1 change "
    "is above 0, and 2. the upper bound of the CI of the S2 change is >= 0. Otherwise the "
    "result is documented and the code, the CLI and every default are left unchanged."
)


def confirm(args: argparse.Namespace) -> int:
    if not DEV_JSON.exists():
        sys.stderr.write("run `dev` first\n")
        return 1
    dev_res = json.loads(DEV_JSON.read_text(encoding="utf-8"))
    delta_hat = float(dev_res["delta_hat"])
    if delta_hat == 0:
        text = "delta-hat = 0 on dev: the confirmation portion is not scored (protocol).\n"
        print(text)
        out = Path(args.out) if args.out else RESULTS / "judge-mtbench-tie-margin-confirm.md"
        out.write_text(text, encoding="utf-8")
        return 0
    rows, scores = load_scores()
    portion = _portions(rows)
    idx = [i for i, r in enumerate(rows) if portion[str(r["cluster_id"])] == "confirm"]
    c_rows, c_scores = [rows[i] for i in idx], [scores[i] for i in idx]
    base = AgreementData(val_items(c_rows, c_scores, 0.0))
    arm = AgreementData(val_items(c_rows, c_scores, delta_hat))
    est = cluster_bootstrap(paired_stat(base, arm), base.cluster, n_boot=BOOT, seed=SEED)
    c1, c2, ship = rule_outcome(est["d_s1"], est["d_s2"])
    lines = [
        "### Tie margin, confirmation portion (scored once)",
        "",
        f"{base.n} items, {base.n_clusters} questions; delta-hat = {delta_hat:g}.",
        "",
        "| Metric | delta 0 | delta-hat | change |",
        "|---|---|---|---|",
        f"| S1 | {_fmt(est['a_jh_s1'])} | {_fmt(est['b_jh_s1'])} | {_fmt_pp(est['d_s1'])} |",
        f"| S2 | {_fmt(est['a_jh_s2'])} | {_fmt(est['b_jh_s2'])} | {_fmt_pp(est['d_s2'])} |",
        f"| judge tie rate | {_fmt(est['a_judge_tie_rate'])} | {_fmt(est['b_judge_tie_rate'])} | |",
        f"| human tie rate (per vote) | {_fmt(est['a_human_tie_rate'])} | | |",
        "",
        f'Rule (verbatim): "{RULE}"',
        "",
        f"* Condition 1 (S1 change lower bound > 0): {'pass' if c1 else 'fail'} "
        f"(lower bound {100 * est['d_s1'].lo:+.1f} pp).",
        f"* Condition 2 (S2 change upper bound >= 0): {'pass' if c2 else 'fail'} "
        f"(upper bound {100 * est['d_s2'].hi:+.1f} pp).",
        f"* **Decision: {'ship as opt-in' if ship else 'not shipped; nothing changes'}.**",
    ]
    result = {
        "delta_hat": delta_hat,
        "items": base.n,
        "questions": base.n_clusters,
        "estimates": _estimates(est),
        "condition_1": c1,
        "condition_2": c2,
        "ship": ship,
        "rule": RULE,
    }
    _emit(lines, args.out, result, RESULTS / "judge-mtbench-tie-margin-confirm.json")
    return 0


def _drop_table(
    label: str, est: Mapping[str, Estimate], dropped: int, total: int, unit: str
) -> list[str]:
    return [
        f"{label}: {dropped} of {total} {unit} dropped.",
        "",
        "| Metric | all items | without the unparsable | change |",
        "|---|---|---|---|",
        f"| S1 | {_fmt(est['a_jh_s1'])} | {_fmt(est['b_jh_s1'])} | {_fmt_pp(est['d_s1'])} |",
        f"| S2 | {_fmt(est['a_jh_s2'])} | {_fmt(est['b_jh_s2'])} | {_fmt_pp(est['d_s2'])} |",
        f"| judge tie rate | {_fmt(est['a_judge_tie_rate'])} | {_fmt(est['b_judge_tie_rate'])} | |",
        f"| human tie rate (per vote) | {_fmt(est['a_human_tie_rate'])} | "
        f"{_fmt(est['b_human_tie_rate'])} | |",
        "",
    ]


def sensitivity(args: argparse.Namespace) -> int:
    """Pre-registered: the unparsable replies dropped, pairwise (1,000) and pointwise (300)."""
    rows = _read_pairs("test")
    completer = CachedCompleter(None, OUT / "cache-test.jsonl", model_id=DEFAULT_ANTHROPIC_MODEL)
    items = _val_items(rows, Judge(completer, workers=WORKERS))
    data = AgreementData(items)
    valid = np.array([it.both_valid for it in items], dtype=np.float64)
    est = cluster_bootstrap(paired_stat(data, data, valid), data.cluster, n_boot=BOOT, seed=SEED)
    lines = [
        "### Sensitivity: unparsable replies dropped (pre-registered)",
        "",
        "#### Pairwise, 1,000 test items (unparsable reply in either order counted as tie)",
        "",
        *_drop_table("Pairwise", est, int((1 - valid).sum()), len(items), "items"),
    ]
    result: dict[str, Any] = {
        "pairwise": {"dropped": int((1 - valid).sum()), "n": len(items), "est": _estimates(est)}
    }
    p_rows, p_scores = load_scores()
    ok = np.array([sa is not None and sb is not None for sa, sb in p_scores], dtype=np.float64)
    dev_res = json.loads(DEV_JSON.read_text(encoding="utf-8")) if DEV_JSON.exists() else None
    margins = [0.0] if dev_res is None else sorted({0.0, float(dev_res["delta_hat"])})
    for d in margins:
        pd = AgreementData(val_items(p_rows, p_scores, d))
        pe = cluster_bootstrap(paired_stat(pd, pd, ok), pd.cluster, n_boot=BOOT, seed=SEED)
        lines += [
            f"#### Pointwise, first 300 items, delta {d:g}",
            "",
            *_drop_table(f"Pointwise delta {d:g}", pe, int((1 - ok).sum()), len(p_rows), "pairs"),
        ]
        result[f"pointwise_delta_{d:g}"] = {"dropped": int((1 - ok).sum()), "est": _estimates(pe)}
    _emit(lines, args.out, result, RESULTS / "judge-mtbench-tie-margin-sensitivity.json")
    return 0


def posthoc(args: argparse.Namespace) -> int:
    """Not pre-registered: every margin of the grid on the pooled 300 items, against delta 0."""
    rows, scores = load_scores()
    base = AgreementData(val_items(rows, scores, 0.0))
    lines = [
        "### Post-hoc (not pre-registered): every margin on the pooled 300 items",
        "",
        f"{base.n} items, {base.n_clusters} questions. Dev and confirmation questions are pooled, "
        "so nothing here is a held-out result and nothing is selected from it.",
        "",
        "| delta | S1 | S2 | S1 change vs 0 | S2 change vs 0 | judge tie rate | human tie rate |",
        "|---|---|---|---|---|---|---|",
    ]
    result: dict[str, Any] = {}
    for d in GRID:
        arm = AgreementData(val_items(rows, scores, d))
        est = cluster_bootstrap(paired_stat(base, arm), base.cluster, n_boot=BOOT, seed=SEED)
        lines.append(
            f"| {d:g} | {_fmt(est['b_jh_s1'])} | {_fmt(est['b_jh_s2'])} | {_fmt_pp(est['d_s1'])} | "
            f"{_fmt_pp(est['d_s2'])} | {_fmt(est['b_judge_tie_rate'])} | "
            f"{_fmt(est['b_human_tie_rate'])} |"
        )
        result[f"{d:g}"] = _estimates(est)
    _emit(lines, args.out, result, RESULTS / "judge-mtbench-tie-margin-posthoc.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("dev", "confirm", "sensitivity", "posthoc"):
        sp = sub.add_parser(name)
        sp.add_argument("--out", default=None, help="markdown output (JSON goes next to it)")
    args = p.parse_args(argv)
    return {"dev": dev, "confirm": confirm, "sensitivity": sensitivity, "posthoc": posthoc}[
        args.cmd
    ](args)


if __name__ == "__main__":
    sys.exit(main())
