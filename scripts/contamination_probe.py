"""GSM-Symbolic-style contamination probe on GSM8K (protocol: docs/protocol-contamination.md).

    python scripts/contamination_probe.py build               # data/contamination/*, needs raw data
    python scripts/contamination_probe.py review --start 0 --count 40   # print items to eyeball
    python scripts/contamination_probe.py run --split dev      # live API calls, cached
    python scripts/contamination_probe.py run --split test
    python scripts/contamination_probe.py score                # cache only, no key, no network

Raw data: download ``grade_school_math/data/test.jsonl`` from
https://github.com/openai/grade-school-math (MIT) to ``data/raw/gsm8k_test.jsonl`` (gitignored),
as ``scripts/build_gsm8k_subset.py`` documents.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from evalkit.contamination import (
    PROMPT_VERSION,
    REASONS,
    DropResult,
    Template,
    TemplateReject,
    as_dict,
    build_prompt,
    build_template,
    check_template,
    check_variant,
    drop_analysis,
    drop_difference,
    exact_mcnemar_p,
    holm_adjust,
    make_variants,
    neutrality,
    score_reply,
    trace_text,
    verdict,
)
from evalkit.llmcache import CachedCompleter, CacheMiss, read_cache, summarize_cache
from evalkit.models import AnthropicModel

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "gsm8k_test.jsonl"
OUT = ROOT / "data" / "contamination"
RESULTS = ROOT / "docs" / "results"
SEED = 0
DEV_N = 6
TEST_N = 140
N_VARIANTS = 2
MAX_TOKENS = 1024
CALL_CAP = 900
MODELS = ("claude-haiku-5-5", "claude-sonnet-4-5-20250929")
# ASSUMED list prices, USD per million tokens (input, output); not read from the API.
PRICES = {"claude-haiku-5-5": (1.0, 5.0), "claude-sonnet-4-5-20250929": (3.0, 15.0)}


def _cache_path(model: str) -> Path:
    return OUT / f"cache-{model}.jsonl"


def _rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------------------------- build


def _pool() -> tuple[list[tuple[Template, list[Any]]], Counter[str], int, str]:
    """Templates (with variants) in seeded permutation order, rejection counts, n rows, sha256."""
    raw = RAW.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    order = list(range(len(rows)))
    random.Random(SEED).shuffle(order)
    rejected: Counter[str] = Counter()
    pool: list[tuple[Template, list[Any]]] = []
    for idx in order:
        tid = f"gsm8k_test_{idx:04d}"
        try:
            t = build_template(tid, rows[idx]["question"], rows[idx]["answer"])
            variants = make_variants(t, N_VARIANTS)
        except TemplateReject as e:
            rejected[e.reason] += 1
            continue
        bad = check_template(t) + [m for v in variants for m in check_variant(t, v.values)]
        if bad:
            raise RuntimeError(f"{tid}: {bad}")
        pool.append((t, variants))
    return pool, rejected, len(rows), hashlib.sha256(raw).hexdigest()


def build(_: argparse.Namespace) -> int:
    pool, rejected, n_rows, sha = _pool()
    drops: dict[str, str] = {}
    drops_path = OUT / "eyeball_drops.json"
    if drops_path.exists():
        drops = json.loads(drops_path.read_text(encoding="utf-8"))
    kept: list[tuple[Template, list[Any], str]] = []
    examined = 0
    dropped_examined = 0
    for t, variants in pool:
        if len(kept) == DEV_N + TEST_N:
            break
        examined += 1
        if t.id in drops:
            dropped_examined += 1
            continue
        kept.append((t, variants, "dev" if len(kept) < DEV_N else "test"))
    if len(kept) < DEV_N + TEST_N:
        raise RuntimeError(f"only {len(kept)} items kept; review more of the pool")
    unknown = set(drops) - {t.id for t, _ in pool}
    if unknown:
        raise RuntimeError(f"drops for ids not in the pool: {sorted(unknown)}")
    OUT.mkdir(parents=True, exist_ok=True)
    _write_jsonl(OUT / "templates.jsonl", [{**t.to_json(), "split": s} for t, _, s in kept])
    items: list[dict[str, Any]] = []
    for t, variants, split in kept:
        base = {"source_id": t.id, "template_id": t.id, "split": split}
        items.append(
            {
                **base,
                "id": f"{t.id}#v0",
                "variant": 0,
                "question": t.question,
                "gold": t.gold,
                "values": [str(x) for x in t.original_values],
            }
        )
        for k, v in enumerate(variants, 1):
            items.append(
                {
                    **base,
                    "id": f"{t.id}#v{k}",
                    "variant": k,
                    "question": v.question,
                    "gold": v.gold,
                    "values": [str(x) for x in v.values],
                }
            )
    _write_jsonl(OUT / "items.jsonl", items)
    n_frozen = sum(s.frozen for t, _, _ in kept for s in t.slots)
    n_slots = sum(len(t.slots) for t, _, _ in kept)
    report = {
        "raw_file_sha256": sha,
        "raw_rows": n_rows,
        "permutation_seed": SEED,
        "funnel": {
            "candidates": n_rows,
            "rejected_by_reason": {r: rejected.get(r, 0) for r in REASONS},
            "templates_kept_by_solver_checks": len(pool),
        },
        "eyeball": {
            "pool_items_examined_in_order": examined,
            "dropped_as_incoherent": dropped_examined,
            "dropped_ids": {
                k: v for k, v in drops.items() if k in {t.id for t, _ in pool[:examined]}
            },
            "kept": len(kept),
        },
        "split_sizes": {"dev": DEV_N, "test": TEST_N},
        "variants_per_source": N_VARIANTS,
        "slots_total": n_slots,
        "slots_frozen": n_frozen,
        "prompts": len(items),
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def review(args: argparse.Namespace) -> int:
    """Print pool items for the eyeball pass (slots marked, trace, variant numbers)."""
    pool, _, _, _ = _pool()
    seen = set(Path(args.seen).read_text().split()) if args.seen else set()
    for n, (t, variants) in enumerate(pool[args.start : args.start + args.count], args.start):
        text = t.question
        if t.id in seen:
            changes = [
                ", ".join(
                    f"{s.text}>{v.values[s.index]}" for s in t.slots if v.values[s.index] != s.value
                )
                for v in variants
            ]
            golds = f"{t.gold}->{variants[0].gold},{variants[1].gold}"
            print(f"## {n} {t.id} gold={golds} | {changes[0]} | {changes[1]}")
            continue
        for s in reversed(t.slots):
            mark = f"[{s.text}*]" if s.frozen else f"[{s.text}]"
            text = text[: s.start] + mark + text[s.end :]
        print(f"## {n} {t.id} gold={t.gold}")
        print(text)
        print("   TRACE:", trace_text(t))
        for k, v in enumerate(variants, 1):
            changed = ", ".join(
                f"{s.text}->{v.values[s.index]}" for s in t.slots if v.values[s.index] != s.value
            )
            print(f"   V{k} gold={v.gold}: {changed}")
        if args.full:
            for v in variants:
                print("   >>", v.question)
    return 0


# ------------------------------------------------------------------------------------------ run


def _completer(model: str, live: bool, max_calls: int) -> CachedCompleter:
    backend = AnthropicModel(model_id=model) if live else None
    return CachedCompleter(backend, _cache_path(model), model_id=model, max_calls=max_calls)


def _recorded_calls() -> int:
    return sum(len(read_cache(_cache_path(m))) for m in MODELS)


def _call(c: CachedCompleter, row: dict[str, Any], *, max_tokens: int) -> str | None:
    try:
        c.complete(build_prompt(row["question"]), max_tokens=max_tokens)
    except Exception as exc:  # report and go on; the cache keeps what succeeded
        return f"{row['id']}: {type(exc).__name__}: {str(exc)[:120]}"
    return None


def run(args: argparse.Namespace) -> int:
    if "ANTHROPIC_API_KEY" not in os.environ:
        sys.exit("ANTHROPIC_API_KEY not set (load it inline; never print it)")
    items = [r for r in _rows(OUT / "items.jsonl") if r["split"] == args.split]
    if args.limit:
        keep = {r["source_id"] for r in items}
        keep = set(sorted(keep)[: args.limit]) if args.limit < len(keep) else keep
        items = [r for r in items if r["source_id"] in keep]
    remaining = CALL_CAP - _recorded_calls()
    print(f"{args.split}: {len(items)} prompts x {len(args.models)} models; cap left {remaining}")
    for model in args.models:
        remaining = CALL_CAP - _recorded_calls()
        c = _completer(model, True, max(remaining, 0))

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            errors = [
                e
                for e in pool.map(functools.partial(_call, c, max_tokens=args.max_tokens), items)
                if e
            ]
        s = c.stats
        print(
            f"{model}: live calls {s.live_calls}, hits {s.hits}, tokens in/out "
            f"{s.input_tokens}/{s.output_tokens}, errors {len(errors)}"
        )
        for e in errors[:5]:
            print("  ", e)
    print(f"total recorded calls: {_recorded_calls()} / cap {CALL_CAP}")
    return 0


# ----------------------------------------------------------------------------------------- score


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _ci(ci: tuple[float, float]) -> str:
    return f"[{100 * ci[0]:+.1f}, {100 * ci[1]:+.1f}]"


def _scores(
    model: str, items: list[dict[str, Any]], mode: str
) -> tuple[dict[str, float], dict[str, Any]]:
    c = _completer(model, False, 0)
    out: dict[str, float] = {}
    info = {"truncated": 0, "no_answer_line": 0, "missing": 0}
    for row in items:
        try:
            r = c.complete(build_prompt(row["question"]), max_tokens=MAX_TOKENS)
        except CacheMiss:
            info["missing"] += 1
            continue
        out[row["id"]] = score_reply(r.text, row["gold"], mode)
        info["truncated"] += int(r.output_tokens >= MAX_TOKENS)
        info["no_answer_line"] += int("answer:" not in r.text.lower())
    return out, info


def _matrix(
    scores: dict[str, float], sources: list[str]
) -> tuple[list[float], list[list[float]]] | None:
    try:
        orig = [scores[f"{s}#v0"] for s in sources]
        var = [[scores[f"{s}#v{k}"] for s in sources] for k in range(1, N_VARIANTS + 1)]
    except KeyError:
        return None
    return orig, var


def _ledger() -> tuple[list[str], dict[str, Any]]:
    lines = [
        "| model | calls | input tokens | output tokens | cost (USD, ASSUMED prices) | "
        "first | last |",
        "|---|---|---|---|---|---|---|",
    ]
    total_calls, total_cost = 0, 0.0
    detail: dict[str, Any] = {}
    for m in MODELS:
        s = summarize_cache(_cache_path(m))
        pin, pout = PRICES[m]
        cost = (s["input_tokens"] * pin + s["output_tokens"] * pout) / 1e6
        total_calls += s["calls"]
        total_cost += cost
        detail[m] = {**s, "cost_usd": cost, "price_in_out_per_mtok_ASSUMED": [pin, pout]}
        lines.append(
            f"| {m} (returned {', '.join(s['models_returned'])}) | {s['calls']} | "
            f"{s['input_tokens']:,} | {s['output_tokens']:,} | {cost:.2f} | {s['first']} | "
            f"{s['last']} |"
        )
    lines.append(f"| **total** | **{total_calls}** | | | **{total_cost:.2f}** | | |")
    detail["total"] = {"calls": total_calls, "cost_usd": total_cost, "call_cap": CALL_CAP}
    return lines, detail


def score(_: argparse.Namespace) -> int:
    items = [r for r in _rows(OUT / "items.jsonl") if r["split"] == "test"]
    sources = sorted({r["source_id"] for r in items})
    gold = {r["id"]: r["gold"] for r in items}
    originals = [gold[f"{s}#v0"] for s in sources]
    perturbed = [[gold[f"{s}#v{k}"] for s in sources] for k in range(1, N_VARIANTS + 1)]
    neut = neutrality(
        originals, [[perturbed[k][i] for k in range(N_VARIANTS)] for i in range(len(sources))]
    )
    results: dict[str, dict[str, DropResult]] = {"numeric": {}, "helm": {}}
    extra: dict[str, dict[str, Any]] = {}
    mats: dict[str, dict[str, Any]] = {"numeric": {}, "helm": {}}
    for model in MODELS:
        for mode in ("numeric", "helm"):
            sc, info = _scores(model, items, mode)
            extra.setdefault(model, {})[mode] = info
            mat = _matrix(sc, sources)
            if mat is None:
                print(f"{model} {mode}: incomplete cache ({info['missing']} missing); skipped")
                continue
            results[mode][model] = drop_analysis(*mat)
            mats[mode][model] = mat
    diff: dict[str, float] | None = None
    if len(mats["numeric"]) == len(MODELS):
        ma, mb = (mats["numeric"][m] for m in (MODELS[1], MODELS[0]))
        mean, lo, hi = drop_difference(ma[0], ma[1], mb[0], mb[1])
        diff = {"mean": mean, "ci95_lo": lo, "ci95_hi": hi}
    holm = {mode: holm_adjust(r) for mode, r in results.items() if len(r) == len(MODELS)}
    ledger_lines, ledger = _ledger()
    lines = _report(results, holm, extra, neut, sources, items, ledger_lines, diff)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "contamination-gsm.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {
        "protocol": "docs/protocol-contamination.md",
        "prompt_version": PROMPT_VERSION,
        "max_tokens": MAX_TOKENS,
        "n_sources": len(sources),
        "models": list(MODELS),
        "neutrality": neut,
        "results": {mode: {m: as_dict(r) for m, r in rs.items()} for mode, rs in results.items()},
        "holm_adjusted_p": holm,
        "drop_difference_second_minus_first_model": diff,
        "verdicts": {
            mode: {m: verdict(r, holm[mode][m]) for m, r in rs.items()}
            for mode, rs in results.items()
            if mode in holm
        },
        "reply_info": extra,
        "ledger": ledger,
    }
    (RESULTS / "contamination-gsm.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


def _report(
    results: dict[str, dict[str, DropResult]],
    holm: dict[str, dict[str, float]],
    extra: dict[str, dict[str, Any]],
    neut: dict[str, float],
    sources: list[str],
    items: list[dict[str, Any]],
    ledger_lines: list[str],
    diff: dict[str, float] | None,
) -> list[str]:
    n = len(sources)
    L = [
        "# Contamination probe: GSM8K, program-built number variants",
        "",
        "Protocol: `docs/protocol-contamination.md` (committed before the scored run). Scored",
        f"offline from the call caches. {n} source problems, original + {N_VARIANTS} variants",
        "each,",
        f"prompt `{PROMPT_VERSION}`, max_tokens {MAX_TOKENS}, one sample per prompt, no sampling",
        "parameter sent. Drop = accuracy(original) minus mean accuracy(perturbed variants),",
        "item = source problem; CIs are cluster bootstraps over sources (10,000 resamples,",
        "seed 0).",
        "",
    ]
    for mode, title in (
        ("numeric", "Primary: evalkit `numeric_match`"),
        ("helm", "Robustness: HELM `final_number_exact_match`"),
    ):
        rs = results[mode]
        if not rs:
            continue
        L += [
            f"## {title}",
            "",
            "| model | acc original | acc v1 | acc v2 | drop (pp) | 95% CI | 97.5% CI | "
            "sign-flip p | Holm p | reading |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for m, r in rs.items():
            hp = holm[mode][m]
            L.append(
                f"| {m} | {_pct(r.acc_original)} | {_pct(r.acc_variants[0])} | "
                f"{_pct(r.acc_variants[1])} | {100 * r.drop:+.1f} | {_ci(r.ci95)} | "
                f"{_ci(r.ci975)} | {r.p_signflip:.4f} | {hp:.4f} | {verdict(r, hp)} |"
            )
        L += [
            "",
            "| model | orig right, v1 wrong | orig wrong, v1 right | orig right, v2 wrong | "
            "orig wrong, v2 right | McNemar exact p (orig vs v1) | "
            "McNemar exact p (orig vs v2) | drop orig-v1 (pp) [95% CI] | "
            "SD of per-source diff | MDE 80% power (alpha .05 / .025), pp |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for m, r in rs.items():
            L.append(
                f"| {m} | {r.orig_right_pert_wrong[0]} | {r.orig_wrong_pert_right[0]} | "
                f"{r.orig_right_pert_wrong[1]} | {r.orig_wrong_pert_right[1]} | "
                f"{r.mcnemar_p_first:.4f} | "
                f"{exact_mcnemar_p(r.orig_right_pert_wrong[1], r.orig_wrong_pert_right[1]):.4f} | "
                f"{100 * r.drop_first:+.1f} {_ci(r.ci95_first)} | "
                f"{r.sd_diff:.3f} | {100 * r.mde_80:.1f} / {100 * r.mde_80_alpha025:.1f} |"
            )
        L.append("")
    if results["numeric"]:
        L += ["## Reading (numeric mode, pre-registered rules)", ""]
        for m, r in results["numeric"].items():
            word = (
                "the 95% CI includes 0" if r.ci95[0] <= 0 <= r.ci95[1] else "the 95% CI excludes 0"
            )
            L.append(
                f"- {m}: {verdict(r, holm['numeric'][m])}; drop {100 * r.drop:+.1f} pp, {word}; "
                f"MDE at 80% power {100 * r.mde_80_alpha025:.1f} pp (alpha .025). A drop smaller "
                "than the MDE could not be excluded."
            )
        L.append("")
    if diff is not None:
        L += [
            "## Difference of drops (descriptive, numeric mode)",
            "",
            f"{MODELS[1]} minus {MODELS[0]}: {100 * diff['mean']:+.1f} pp "
            f"[95% CI {100 * diff['ci95_lo']:+.1f}, {100 * diff['ci95_hi']:+.1f}], "
            "cluster bootstrap over sources.",
            "",
        ]
    L += [
        "## Difficulty neutrality of the golds (test sources)",
        "",
        "| statistic | value |",
        "|---|---|",
    ]
    for k, v in neut.items():
        L.append(f"| {k} | {v:.3f} |")
    L += [
        "",
        "## Reply diagnostics (numeric mode)",
        "",
        "| model | missing | truncated at max_tokens | no `Answer:` line |",
        "|---|---|---|---|",
    ]
    for m in MODELS:
        i = extra[m]["numeric"]
        L.append(f"| {m} | {i['missing']} | {i['truncated']} | {i['no_answer_line']} |")
    L += [
        "",
        "## API ledger (all calls, dev pilot included; prices ASSUMED, not read from the API)",
        "",
    ]
    L += ledger_lines
    L += [
        "",
        "Reading rules (pre-registered): a significant drop is consistent with memorisation of the",
        "original items OR brittleness to number changes (this probe cannot separate the two); no",
        "detectable drop is no evidence of contamination by this probe, not proof of none.",
    ]
    return L


# ------------------------------------------------------------------------------------------ main


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("review")
    r.add_argument("--start", type=int, default=0)
    r.add_argument("--count", type=int, default=40)
    r.add_argument("--full", action="store_true", help="also print the perturbed questions")
    r.add_argument("--seen", help="file of ids whose question text is not printed again")
    ru = sub.add_parser("run")
    ru.add_argument("--split", choices=["dev", "test"], required=True)
    ru.add_argument("--models", nargs="+", default=list(MODELS))
    ru.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ru.add_argument("--workers", type=int, default=6)
    ru.add_argument("--limit", type=int, default=0, help="first N sources only")
    sub.add_parser("score")
    args = p.parse_args(argv)
    return {"build": build, "review": review, "run": run, "score": score}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
