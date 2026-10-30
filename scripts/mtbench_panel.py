"""PoLL-style judge panel and self-preference test on MT-Bench human judgments.

Protocol: docs/protocol-judge-panel.md (committed before any scored run).

Subcommands (``uv run --offline python scripts/mtbench_panel.py <cmd>``):

* ``select``  draw the seeded, stratified subsample of the 1,000 test items and write
  ``data/mtbench/panel-subsample.json`` (ids only; chosen without looking at any verdict).
* ``run``     judge the pilot (dev items) or the subsample (test items) with ``haiku`` or
  ``opus`` in both orders through the call cache ``data/mtbench/cache-panel-<judge>[-pilot].jsonl``
  (needs ANTHROPIC_API_KEY unless every request is cached). Hard caps: ``--max-calls`` and
  ``--max-usd`` (assumed list prices).
* ``project`` project the cost of a subsample from the pilot token ratios.
* ``score``   cache-only (no key, no network): agreement / kappa / flip / cost / self-preference
  report with cluster-bootstrap CIs -> ``docs/results/judge-panel-mtbench.{md,json}``.

The Sonnet verdicts are the already recorded ``data/mtbench/cache-test.jsonl`` (same prompt
``judge-v1``, same cache key); they are referenced, not copied. The API key is read from the
environment only and is never written anywhere.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from evalkit.judge import (
    PAIRWISE_SYSTEM,
    Decision,
    Judge,
    PairVerdict,
    pair_item_from_row,
    prompt_fingerprint,
)
from evalkit.judge_stats import AgreementData, Estimate, ValItem, cluster_bootstrap
from evalkit.llmcache import CachedCompleter, read_cache
from evalkit.models import AnthropicModel
from evalkit.panel import (
    TIE_BAND,
    JudgeOrders,
    PanelVerdict,
    Price,
    codes,
    cohen_kappa,
    cost_per_1k,
    excess,
    panel_cost_per_1k,
    panel_majority,
    panel_mean,
    reference_side,
    stratified_sample,
    usage_cost,
    weighted_mean,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "mtbench"
SUBSAMPLE = DATA / "panel-subsample.json"
OUT_MD = ROOT / "docs" / "results" / "judge-panel-mtbench.md"
SEED = 0
BOOT = 2000
MARGIN = 0.05
REFERENCE_MODEL = "claude-v1"
PILOT_ITEMS = 15

# ASSUMED list prices, US dollars per million tokens. They were not read from the API: the
# owner-given model ids are not in any price list I can query. Tier prices of the current
# Haiku / Sonnet / Opus generation.
PRICES: dict[str, Price] = {
    "haiku": Price(1.0, 5.0),
    "sonnet": Price(3.0, 15.0),
    "opus": Price(5.0, 25.0),
}
MODEL_IDS = {
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
}
# Haiku's pilot replies hit the 1,024-token cap in 3 of 30 calls (empty or cut-off text, so no
# verdict); its cap is 2,048. Sonnet's cached run and Opus keep 1,024.
MAX_TOKENS = {"haiku": 2048, "sonnet": 1024, "opus": 1024}
LABELS = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus"}
CACHES: dict[str, Path] = {
    "haiku": DATA / "cache-panel-haiku.jsonl",
    "sonnet": DATA / "cache-test.jsonl",  # referenced, not copied
    "opus": DATA / "cache-panel-opus.jsonl",
}
PILOT_CACHES = {
    "haiku": DATA / "cache-panel-haiku-pilot.jsonl",
    "opus": DATA / "cache-panel-opus-pilot.jsonl",
}
PANEL_NAMES = ("panel_majority", "panel_mean")
PANEL_LABELS = {"panel_majority": "Panel (a) majority", "panel_mean": "Panel (b) mean"}
OPPONENT_GROUPS = {
    "vs gpt-4": ("gpt-4",),
    "vs gpt-3.5-turbo": ("gpt-3.5-turbo",),
    "vs llama-13b / alpaca-13b / vicuna-13b-v1.2": ("llama-13b", "alpaca-13b", "vicuna-13b-v1.2"),
}


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _has_ref(r: dict[str, Any]) -> bool:
    return REFERENCE_MODEL in (r["model_a"], r["model_b"])


def _strata(rows: Sequence[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return [(r["turn"], r["category"]) for r in rows]


# --------------------------------------------------------------------------- select


def select(args: argparse.Namespace) -> int:
    rows = _read_rows(DATA / "test.jsonl")
    ref = [i for i, r in enumerate(rows) if _has_ref(r)]
    oth = [i for i, r in enumerate(rows) if not _has_ref(r)]
    pick_ref = stratified_sample(_strata([rows[i] for i in ref]), args.n_claude, SEED)
    pick_oth = stratified_sample(_strata([rows[i] for i in oth]), args.n_other, SEED)
    chosen = sorted([ref[i] for i in pick_ref] + [oth[i] for i in pick_oth])
    doc = {
        "seed": SEED,
        "stratify": "turn x category, largest-remainder proportional, random.Random(0)",
        "reference_model": REFERENCE_MODEL,
        "n_claude": len(pick_ref),
        "n_other": len(pick_oth),
        "claude_pairs_in_test": len(ref),
        "ids": [rows[i]["id"] for i in chosen],
    }
    SUBSAMPLE.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"subsample: {len(pick_ref)} claude-v1 items + {len(pick_oth)} other = {len(chosen)}")
    return 0


def _subsample_rows() -> list[dict[str, Any]]:
    doc = json.loads(SUBSAMPLE.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in _read_rows(DATA / "test.jsonl")}
    return [by_id[i] for i in doc["ids"]]


def _pilot_rows() -> list[dict[str, Any]]:
    rows = _read_rows(DATA / "dev.jsonl")
    return [rows[i] for i in stratified_sample(_strata(rows), PILOT_ITEMS, SEED)]


# --------------------------------------------------------------------------- run


def _stats_cost(completer: CachedCompleter, price: Price) -> float:
    s = completer.stats
    return usage_cost(s.input_tokens, s.output_tokens, price)


def run(args: argparse.Namespace) -> int:
    pilot = args.stage == "pilot"
    rows = _pilot_rows() if pilot else _subsample_rows()
    cache = (PILOT_CACHES if pilot else CACHES)[args.judge]
    model = MODEL_IDS[args.judge]
    backend = None if args.cache_only else AnthropicModel(model_id=model)
    completer = CachedCompleter(backend, cache, model_id=model, max_calls=args.max_calls)
    judge = Judge(completer, workers=args.workers, max_tokens=MAX_TOKENS[args.judge])
    price = PRICES[args.judge]
    done = 0
    for lo in range(0, len(rows), args.chunk):
        chunk = rows[lo : lo + args.chunk]
        judge.compare_many([pair_item_from_row(r) for r in chunk])
        done += len(chunk)
        if _stats_cost(completer, price) > args.max_usd:
            print(f"stopping: assumed cost passed --max-usd {args.max_usd} after {done} items")
            break
    s = completer.stats
    print(
        f"{args.stage} {model}: {done}/{len(rows)} items, live calls {s.live_calls}, cache hits "
        f"{s.hits}, tokens in/out {s.input_tokens}/{s.output_tokens}, "
        f"assumed cost ${_stats_cost(completer, price):.3f}"
    )
    return 0


# --------------------------------------------------------------------------- shared


@dataclass
class JudgeRun:
    """One judge's cached verdicts and token use on a list of rows."""

    name: str
    verdicts: list[PairVerdict]
    input_tokens: int
    output_tokens: int
    returned: set[str]


def _collect(name: str, rows: Sequence[dict[str, Any]], cache: Path) -> JudgeRun:
    completer = CachedCompleter(None, cache, model_id=MODEL_IDS[name])
    judge = Judge(completer, max_tokens=MAX_TOKENS[name])
    items = [pair_item_from_row(r) for r in rows]
    verdicts = judge.compare_many(items)
    tin = tout = 0
    returned: set[str] = set()
    for it in items:
        for swapped in (False, True):
            # replay of the exact request Judge.compare makes; a cache hit, never a call
            c = completer.complete(
                judge._pair_prompt(it, swapped), system=PAIRWISE_SYSTEM, max_tokens=judge.max_tokens
            )
            tin += c.input_tokens
            tout += c.output_tokens
            returned.add(c.model)
    return JudgeRun(name, verdicts, tin, tout, returned)


def _orders(v: PairVerdict) -> JudgeOrders:
    return JudgeOrders(v.first, v.second)


def _val_item(
    r: dict[str, Any], resolved: Decision, flipped: bool, same_slot: bool, valid: bool
) -> ValItem:
    return ValItem(
        cluster=r["cluster_id"],
        verdict=resolved,
        votes=tuple((j, lab) for j, lab in r["human_votes"]),
        length_diff=float(r["length_a"] - r["length_b"]),
        flipped=flipped,
        same_slot=same_slot,
        both_valid=valid,
        other=r["gpt4_verdict"],
    )


def _single_items(rows: Sequence[dict[str, Any]], run_: JudgeRun) -> list[ValItem]:
    return [
        _val_item(r, v.resolved, v.flipped, v.same_slot, v.both_valid)
        for r, v in zip(rows, run_.verdicts, strict=True)
    ]


def _panel_verdicts(runs: dict[str, JudgeRun], n: int) -> dict[str, list[PanelVerdict]]:
    names = ("haiku", "sonnet", "opus")
    per_item = [[_orders(runs[nm].verdicts[i]) for nm in names] for i in range(n)]
    return {
        "panel_majority": [panel_majority(js) for js in per_item],
        "panel_mean": [panel_mean(js, TIE_BAND) for js in per_item],
    }


def _panel_items(rows: Sequence[dict[str, Any]], pv: Sequence[PanelVerdict]) -> list[ValItem]:
    return [
        _val_item(r, v.resolved, v.flipped, v.same_slot, v.valid)
        for r, v in zip(rows, pv, strict=True)
    ]


def _fmt(e: Estimate, pct: bool = True) -> str:
    if pct:
        return f"{100 * e.value:.1f}% [{100 * e.lo:.1f}, {100 * e.hi:.1f}]"
    return f"{e.value:+.3f} [{e.lo:+.3f}, {e.hi:+.3f}]"


def _fmt_pp(e: Estimate) -> str:
    return f"{100 * e.value:+.1f} pp [{100 * e.lo:+.1f}, {100 * e.hi:+.1f}]"


def _rule(e: Estimate) -> str:
    """Decision rule of the protocol applied to a difference with margin ``MARGIN``."""
    if np.isnan(e.lo) or np.isnan(e.hi):
        return "undefined"
    if e.lo > 0:
        return "superior"
    if e.hi < 0:
        return "inferior"
    if e.lo > -MARGIN:
        return "non-inferior (CI includes 0)"
    return "inconclusive"


# --------------------------------------------------------------------------- statistics

JUDGES = ("haiku", "sonnet", "opus")
SYSTEMS = (*JUDGES, *PANEL_NAMES)
DIFF_METRICS = ("jh_s1", "jh_s2", "jh_kappa_s1", "jh_kappa_s2", "flip_rate")


def _group_estimates(
    items: dict[str, list[ValItem]], n_boot: int
) -> tuple[dict[str, Estimate], AgreementData]:
    """Every metric of every system plus paired differences and judge-judge kappas, one resample
    stream (so every difference is paired)."""
    data = {k: AgreementData(v) for k, v in items.items()}
    resolved = {k: codes([it.verdict for it in v]) for k, v in items.items()}

    def stat(w: np.ndarray) -> dict[str, float]:
        out: dict[str, float] = {}
        for k, d in data.items():
            for m, v in d.statistics(w).items():
                out[f"{k}.{m}"] = v
        for p in PANEL_NAMES:
            for j in JUDGES:
                for m in DIFF_METRICS:
                    out[f"diff.{p}-{j}.{m}"] = out[f"{p}.{m}"] - out[f"{j}.{m}"]
        for i, a in enumerate(JUDGES):
            for b in JUDGES[i + 1 :]:
                out[f"kappa.{a}.{b}"] = cohen_kappa(resolved[a], resolved[b], w)
        return out

    first = next(iter(data.values()))
    return cluster_bootstrap(stat, first.cluster, n_boot=n_boot, seed=SEED), first


def _metric_table(est: dict[str, Estimate]) -> list[str]:
    cols = [LABELS[j] for j in JUDGES] + [PANEL_LABELS[p] for p in PANEL_NAMES]
    lines = [
        "| Metric | " + " | ".join(cols) + " | GPT-4 (released) | human-human |",
        "|---|" + "---|" * (len(cols) + 2),
    ]
    rows: list[tuple[str, str, bool, str | None, str | None]] = [
        ("judge-human agreement S1", "jh_s1", True, "other_s1", "hh_s1"),
        ("judge-human agreement S2", "jh_s2", True, "other_s2", "hh_s2"),
        ("Cohen's kappa S1 (3 labels)", "jh_kappa_s1", False, "other_kappa_s1", None),
        ("Cohen's kappa S2 (A/B)", "jh_kappa_s2", False, "other_kappa_s2", None),
        ("position-flip rate", "flip_rate", True, None, None),
        ("same-slot rate", "same_slot_rate", True, None, None),
        ("resolved-tie rate", "judge_tie_rate", True, None, None),
        ("rho verdict vs length diff", "len_rho_judge", False, None, None),
    ]
    for label, key, pct, other, hh in rows:
        cells = [_fmt(est[f"{s}.{key}"], pct) for s in SYSTEMS]
        cells.append(_fmt(est[f"haiku.{other}"], pct) if other else "")
        cells.append(_fmt(est[f"haiku.{hh}"], pct) if hh else "")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def _diff_table(est: dict[str, Estimate], single: str | None = None) -> list[str]:
    lines = [
        "| Panel minus | metric | difference [95% CI] | rule (margin 5 pp) |",
        "|---|---|---|---|",
    ]
    names = {"jh_s1": "S1", "jh_s2": "S2", "jh_kappa_s1": "kappa S1", "jh_kappa_s2": "kappa S2"}
    for p in PANEL_NAMES:
        for j in JUDGES:
            if single and j != single:
                continue
            for m in ("jh_s1", "jh_s2", "jh_kappa_s1", "jh_kappa_s2", "flip_rate"):
                e = est[f"diff.{p}-{j}.{m}"]
                if m.startswith("jh_kappa"):
                    lines.append(
                        f"| {LABELS[j]} ({PANEL_LABELS[p]}) | {names[m]} | "
                        f"{e.value:+.3f} [{e.lo:+.3f}, {e.hi:+.3f}] | |"
                    )
                elif m == "flip_rate":
                    lines.append(
                        f"| {LABELS[j]} ({PANEL_LABELS[p]}) | position-flip rate | {_fmt_pp(e)} | |"
                    )
                else:
                    lines.append(
                        f"| {LABELS[j]} ({PANEL_LABELS[p]}) | {names[m]} | {_fmt_pp(e)} | "
                        f"{_rule(e)} |"
                    )
    return lines


# --------------------------------------------------------------------------- self-preference


def _excess_vectors(
    rows: Sequence[dict[str, Any]], verdicts: dict[str, Sequence[Decision]]
) -> dict[str, np.ndarray]:
    """Per-item excess for each named verdict list, plus the released GPT-4 verdicts."""
    sides = [reference_side(r["model_a"], r["model_b"], REFERENCE_MODEL) for r in rows]
    votes = [[lab for _, lab in r["human_votes"]] for r in rows]
    out: dict[str, np.ndarray] = {}
    for name, vs in verdicts.items():
        out[name] = np.array([excess(v, vo, s) for v, vo, s in zip(vs, votes, sides, strict=True)])
    out["gpt4"] = np.array(
        [excess(r["gpt4_verdict"], vo, s) for r, vo, s in zip(rows, votes, sides, strict=True)]
    )
    return out


def _self_pref(
    rows: Sequence[dict[str, Any]], verdicts: dict[str, Sequence[Decision]], n_boot: int
) -> tuple[dict[str, Estimate], dict[str, int]]:
    vec = _excess_vectors(rows, verdicts)
    clusters = sorted({r["cluster_id"] for r in rows})
    idx = {c: i for i, c in enumerate(clusters)}
    cl = np.array([idx[r["cluster_id"]] for r in rows])
    opponents = [r["model_b"] if r["model_a"] == REFERENCE_MODEL else r["model_a"] for r in rows]
    masks = {
        g: np.array([o in ms for o in opponents], dtype=np.float64)
        for g, ms in OPPONENT_GROUPS.items()
    }

    def stat(w: np.ndarray) -> dict[str, float]:
        out: dict[str, float] = {}
        for name, x in vec.items():
            out[f"{name}"] = weighted_mean(x, w)
            for g, m in masks.items():
                out[f"{name}|{g}"] = weighted_mean(x, w * m)
            if name != "gpt4":
                d = x - vec["gpt4"]
                out[f"{name}-gpt4"] = weighted_mean(d, w)
                for g, m in masks.items():
                    out[f"{name}-gpt4|{g}"] = weighted_mean(d, w * m)
        return out

    est = cluster_bootstrap(stat, cl, n_boot=n_boot, seed=SEED)
    counts = {"items": len(rows), "clusters": len(clusters)}
    counts.update({g: int(m.sum()) for g, m in masks.items()})
    return est, counts


def _interpret(e: Estimate) -> str:
    if np.isnan(e.lo):
        return "undefined"
    if e.lo > 0:
        return "CI above 0: favours the Claude answer beyond human preference"
    if e.hi < 0:
        return "CI below 0: favours the Claude answer less than humans do"
    return "CI includes 0: no detectable effect"


def _self_pref_lines(
    est: dict[str, Estimate], counts: dict[str, int], names: Sequence[str], title: str
) -> list[str]:
    lines = [
        f"#### {title}",
        "",
        f"{counts['items']} items with {REFERENCE_MODEL}, {counts['clusters']} questions; "
        "by opponent: " + ", ".join(f"{g} {counts[g]}" for g in OPPONENT_GROUPS) + ".",
        "",
        "| Judge | mean excess [95% CI] | interpretation |",
        "|---|---|---|",
    ]
    for n in names:
        lines.append(f"| {_label(n)} | {_fmt(est[n], False)} | {_interpret(est[n])} |")
    lines.append(
        f"| GPT-4 (released, control) | {_fmt(est['gpt4'], False)} | {_interpret(est['gpt4'])} |"
    )
    lines += [
        "",
        "Claude judge excess minus GPT-4 excess (same items, paired):",
        "",
        "| Judge | difference [95% CI] | interpretation |",
        "|---|---|---|",
    ]
    for n in names:
        e = est[f"{n}-gpt4"]
        lines.append(f"| {_label(n)} | {_fmt(e, False)} | {_interpret(e)} |")
    lines += ["", "Descriptive, by opponent (mean excess [95% CI]; n = items):", ""]
    cols = list(OPPONENT_GROUPS)
    lines += [
        "| Judge | " + " | ".join(f"{g} (n={counts[g]})" for g in cols) + " |",
        "|---|" + "---|" * len(cols),
    ]
    for n in [*names, "gpt4"]:
        lines.append(
            f"| {_label(n)} | " + " | ".join(_fmt(est[f"{n}|{g}"], False) for g in cols) + " |"
        )
    lines.append("")
    return lines


def _label(name: str) -> str:
    if name == "gpt4":
        return "GPT-4 (released)"
    return LABELS.get(name) or PANEL_LABELS.get(name, name)


# --------------------------------------------------------------------------- ledger / cost


def _ledger_row(path: Path, price: Price) -> tuple[int, int, int, float, str]:
    recs = read_cache(path)
    tin = sum(int(r["usage"]["input_tokens"]) for r in recs)
    tout = sum(int(r["usage"]["output_tokens"]) for r in recs)
    span = (
        f"{min(r['timestamp'] for r in recs)[:10]} to {max(r['timestamp'] for r in recs)[:10]}"
        if recs
        else "-"
    )
    return len(recs), tin, tout, usage_cost(tin, tout, price), span


# --------------------------------------------------------------------------- score


def score(args: argparse.Namespace) -> int:
    rows = _subsample_rows()
    n = len(rows)
    runs = {j: _collect(j, rows, CACHES[j]) for j in JUDGES}
    pv = _panel_verdicts(runs, n)
    items: dict[str, list[ValItem]] = {j: _single_items(rows, runs[j]) for j in JUDGES}
    for p in PANEL_NAMES:
        items[p] = _panel_items(rows, pv[p])
    all_idx = list(range(n))
    groups: list[tuple[str, list[int]]] = [
        ("All subsample items", all_idx),
        (f"Items that include {REFERENCE_MODEL}", [i for i in all_idx if _has_ref(rows[i])]),
        (f"Items without {REFERENCE_MODEL}", [i for i in all_idx if not _has_ref(rows[i])]),
        ("Turn 1", [i for i in all_idx if rows[i]["turn"] == 1]),
        ("Turn 2", [i for i in all_idx if rows[i]["turn"] == 2]),
    ]
    results: dict[str, Any] = {}
    lines: list[str] = []
    for name, idx in groups:
        est, data = _group_estimates({k: [v[i] for i in idx] for k, v in items.items()}, args.boot)
        c = data.counts()
        lines += [
            f"#### {name}",
            "",
            f"{c['items']} items, {c['clusters']} questions, {c['votes']} human votes; "
            f"S2 judge-human items {c['items_s2']}; human-human items S1 {c['items_hh_s1']} / "
            f"S2 {c['items_hh_s2']}.",
            "",
            *_metric_table(est),
            "",
            "Paired differences, panel minus single judge (same items, same resamples):",
            "",
            *_diff_table(est),
            "",
        ]
        results[name] = {k: [e.value, e.lo, e.hi] for k, e in est.items()}
        if name == "All subsample items":
            all_est = est
            kap = [
                "Pairwise Cohen's kappa between judges (resolved verdicts, 3 labels, all "
                "subsample items):",
                "",
                "| Pair | kappa [95% CI] |",
                "|---|---|",
            ]
            for i, a in enumerate(JUDGES):
                for b in JUDGES[i + 1 :]:
                    kap.append(
                        f"| {LABELS[a]} - {LABELS[b]} | {_fmt(est[f'kappa.{a}.{b}'], False)} |"
                    )
            lines += [*kap, ""]

    # Sonnet on all 1000 test items (the existing run), for context
    full_rows = _read_rows(DATA / "test.jsonl")
    full = _collect("sonnet", full_rows, CACHES["sonnet"])
    full_est = cluster_bootstrap_single(_single_items(full_rows, full), args.boot)
    results["Sonnet, all 1000 test items"] = {k: [e.value, e.lo, e.hi] for k, e in full_est.items()}

    # self-preference
    ref_idx = [i for i in all_idx if _has_ref(rows[i])]
    ref_rows = [rows[i] for i in ref_idx]
    verd: dict[str, list[Decision]] = {
        j: [runs[j].verdicts[i].resolved for i in ref_idx] for j in JUDGES
    }
    for p in PANEL_NAMES:
        verd[p] = [pv[p][i].resolved for i in ref_idx]
    sp_est, sp_counts = _self_pref(ref_rows, verd, args.boot)
    results["self_preference_subsample"] = {k: [e.value, e.lo, e.hi] for k, e in sp_est.items()}
    full_ref = [r for r in full_rows if _has_ref(r)]
    full_ref_idx = [i for i, r in enumerate(full_rows) if _has_ref(r)]
    sp_full, sp_full_counts = _self_pref(
        full_ref, {"sonnet": [full.verdicts[i].resolved for i in full_ref_idx]}, args.boot
    )
    results["self_preference_all_claude_pairs_sonnet"] = {
        k: [e.value, e.lo, e.hi] for k, e in sp_full.items()
    }

    # cost
    cost_lines = [
        "| Judge | calls | input tokens | output tokens | cost on subsample | "
        "cost per 1,000 resolved verdicts |",
        "|---|---|---|---|---|---|",
    ]
    per_1k: dict[str, float] = {}
    for j in JUDGES:
        r_ = runs[j]
        per_1k[j] = cost_per_1k(r_.input_tokens, r_.output_tokens, PRICES[j], n)
        cost_lines.append(
            f"| {LABELS[j]} | {2 * n} | {r_.input_tokens} | {r_.output_tokens} | "
            f"${usage_cost(r_.input_tokens, r_.output_tokens, PRICES[j]):.2f} | ${per_1k[j]:.2f} |"
        )
    panel_1k = panel_cost_per_1k([per_1k[j] for j in JUDGES])
    cost_lines.append(
        f"| Panel (all three) | {6 * n} | {sum(runs[j].input_tokens for j in JUDGES)} | "
        f"{sum(runs[j].output_tokens for j in JUDGES)} | "
        f"${panel_1k * n / 1000:.2f} | ${panel_1k:.2f} |"
    )
    results["cost_per_1k"] = {**per_1k, "panel": panel_1k}

    # ledger (live calls made for this task; Sonnet is reused, not re-called)
    ledger = [
        "| Cache file | calls | input tokens | output tokens | assumed cost | recorded |",
        "|---|---|---|---|---|---|",
    ]
    tot_calls, tot_cost = 0, 0.0
    for j in ("haiku", "opus"):
        for path in (PILOT_CACHES[j], CACHES[j]):
            c_, ti, to, usd, span = _ledger_row(path, PRICES[j])
            tot_calls += c_
            tot_cost += usd
            ledger.append(
                f"| `{path.relative_to(ROOT)}` | {c_} | {ti} | {to} | ${usd:.2f} | {span} |"
            )
    ledger.append(
        f"| **total live calls this task** | {tot_calls} | | | **${tot_cost:.2f}** | "
        "cap 1,800 calls / about $10 |"
    )
    results["ledger"] = {"calls": tot_calls, "assumed_usd": tot_cost}

    invalid = {j: sum(1 for v in runs[j].verdicts if not v.both_valid) for j in JUDGES}
    n_ref = len(ref_idx)
    header = [
        "### Judge panel vs MT-Bench human judgments (and self-preference), test subsample",
        "",
        "Protocol: `docs/protocol-judge-panel.md`. "
        f"Prompt `judge-v1` (fingerprint `{prompt_fingerprint()}`), "
        f"no logprobs, no sampling parameter. Models returned: "
        + "; ".join(f"{LABELS[j]} {sorted(runs[j].returned)}" for j in JUDGES)
        + f". Subsample: {n} of 1,000 test items ({n_ref} with {REFERENCE_MODEL}, "
        f"{n - n_ref} without). "
        f"Items with an unparsable reply (resolved to tie by that judge): "
        + ", ".join(f"{LABELS[j]} {invalid[j]}" for j in JUDGES)
        + f". Panel tie band for aggregation (b): {TIE_BAND}. Intervals: cluster bootstrap over "
        f"questions, {args.boot} resamples, seed {SEED}. Prices are ASSUMED list prices "
        + ", ".join(f"{LABELS[j]} ${PRICES[j].input:g}/${PRICES[j].output:g}" for j in JUDGES)
        + " per million input/output tokens.",
        "",
    ]
    p_s1 = all_est["diff.panel_majority-sonnet.jh_s1"]
    p_s2 = all_est["diff.panel_majority-sonnet.jh_s2"]
    m_s1 = all_est["diff.panel_mean-sonnet.jh_s1"]
    m_s2 = all_est["diff.panel_mean-sonnet.jh_s2"]
    primary = [
        "#### Pre-registered decisions (panel minus Sonnet, same subsample, margin 5 pp)",
        "",
        "| Aggregation | S1 difference | S1 rule | S2 difference | S2 rule |",
        "|---|---|---|---|---|",
        f"| (a) majority (primary) | {_fmt_pp(p_s1)} | **{_rule(p_s1)}** | {_fmt_pp(p_s2)} | "
        f"{_rule(p_s2)} |",
        f"| (b) mean (secondary) | {_fmt_pp(m_s1)} | {_rule(m_s1)} | {_fmt_pp(m_s2)} | "
        f"{_rule(m_s2)} |",
        "",
        "The rule is applied mechanically to the pre-registered contrast only. Every other row "
        "(subgroups, other single judges, kappas, flips, opponent splits) is descriptive; no "
        "correction for multiple looks is made. The panel is also compared with Opus alone in the "
        "paired tables below: a panel gain over Sonnet is not a gain over its best member. "
        "Sonnet's 320 calls on the subsample were recorded earlier "
        "(`data/mtbench/cache-test.jsonl`) and are not in the ledger; the cost tables price them "
        "at the same assumed prices.",
        "",
    ]
    ref_header = [
        "#### Sonnet on all 1,000 test items (existing run, for context)",
        "",
        f"agreement S1 {_fmt(full_est['jh_s1'])}, S2 {_fmt(full_est['jh_s2'])}; kappa S1 "
        f"{_fmt(full_est['jh_kappa_s1'], False)}, S2 {_fmt(full_est['jh_kappa_s2'], False)}; "
        "released GPT-4 on the "
        f"same items S1 {_fmt(full_est['other_s1'])}, S2 {_fmt(full_est['other_s2'])}.",
        "",
    ]
    sp = ["### Self-preference (pre-registered)", ""]
    sp += _self_pref_lines(
        sp_est, sp_counts, [*JUDGES, *PANEL_NAMES], "Primary: claude-v1 items of the subsample"
    )
    sp += _self_pref_lines(
        sp_full,
        sp_full_counts,
        ["sonnet"],
        "Sonnet on all claude-v1 pairs of the test file (extra)",
    )
    text = "\n".join(
        header
        + primary
        + ["### Agreement with human votes", ""]
        + lines
        + ref_header
        + sp
        + ["### Cost", "", *cost_lines, "", "### Ledger", "", *ledger, ""]
    )
    print(text)
    if args.out:
        out = Path(args.out)
        out.write_text(text + "\n", encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0


def cluster_bootstrap_single(items: list[ValItem], n_boot: int) -> dict[str, Estimate]:
    d = AgreementData(items)
    return cluster_bootstrap(d.statistics, d.cluster, n_boot=n_boot, seed=SEED)


# --------------------------------------------------------------------------- project


def project(args: argparse.Namespace) -> int:
    """Cost projection of the test subsample from the pilot (dev items) token ratios."""
    pilot = _pilot_rows()
    son_dev = _collect("sonnet", pilot, DATA / "cache-dev.jsonl")
    test_rows = _read_rows(DATA / "test.jsonl")
    ref = [i for i, r in enumerate(test_rows) if _has_ref(r)]
    oth = [i for i, r in enumerate(test_rows) if not _has_ref(r)]
    pick = [
        ref[i] for i in stratified_sample(_strata([test_rows[i] for i in ref]), args.n_claude, SEED)
    ]
    pick += [
        oth[i] for i in stratified_sample(_strata([test_rows[i] for i in oth]), args.n_other, SEED)
    ]
    sub = [test_rows[i] for i in sorted(pick)]
    son_sub = _collect("sonnet", sub, CACHES["sonnet"])
    total = 0.0
    print(f"pilot items {len(pilot)}; subsample {len(sub)}")
    for j in ("haiku", "opus"):
        run_ = _collect(j, pilot, PILOT_CACHES[j])
        r_in = run_.input_tokens / son_dev.input_tokens
        r_out = run_.output_tokens / son_dev.output_tokens
        p_in = son_sub.input_tokens * r_in
        p_out = son_sub.output_tokens * r_out
        usd = usage_cost(p_in, p_out, PRICES[j])
        total += usd
        pilot_usd = usage_cost(run_.input_tokens, run_.output_tokens, PRICES[j])
        print(
            f"{j}: token ratio vs Sonnet in {r_in:.2f} out {r_out:.2f}; pilot ${pilot_usd:.3f}; "
            f"projected subsample in/out {p_in:.0f}/{p_out:.0f} = ${usd:.2f}"
        )
    print(f"projected total ${total:.2f} for {4 * len(sub)} calls")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--n-claude", type=int, required=True)
    s.add_argument("--n-other", type=int, required=True)
    s.set_defaults(fn=select)
    r = sub.add_parser("run")
    r.add_argument("--judge", choices=("haiku", "opus"), required=True)
    r.add_argument("--stage", choices=("pilot", "panel"), required=True)
    r.add_argument("--max-calls", type=int, required=True)
    r.add_argument("--max-usd", type=float, required=True)
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--chunk", type=int, default=16)
    r.add_argument("--cache-only", action="store_true")
    r.set_defaults(fn=run)
    pr = sub.add_parser("project")
    pr.add_argument("--n-claude", type=int, required=True)
    pr.add_argument("--n-other", type=int, required=True)
    pr.set_defaults(fn=project)
    sc = sub.add_parser("score")
    sc.add_argument("--boot", type=int, default=BOOT)
    sc.add_argument("--out", default=str(OUT_MD))
    sc.set_defaults(fn=score)
    args = p.parse_args(argv)
    fn: Callable[[argparse.Namespace], int] = args.fn
    return fn(args)


if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" in os.environ and not os.environ["ANTHROPIC_API_KEY"]:
        sys.exit("ANTHROPIC_API_KEY is set but empty")
    sys.exit(main())
