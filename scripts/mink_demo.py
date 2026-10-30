"""Min-K% Prob DEMO on a tiny local model (not a contamination audit of any model or benchmark).

Protocol: docs/protocol-mink.md. Run with ``uv run --offline python scripts/mink_demo.py <cmd>``.

* ``paraphrase``  select 150 GSM8K test questions (``random.Random(0)``), paraphrase each once
  with claude-haiku-5-5 through the JSONL cache, check the number multiset, write
  ``data/mink/pairs.jsonl``. Needs ANTHROPIC_API_KEY (environment only) unless every request is
  cached; ``--cache-only`` never calls the API; ``--limit N`` does the pilot on the first N.
* ``score``       load Qwen/Qwen2.5-0.5B lazily (optional ``hf`` extra), compute per-token
  log-probs under teacher forcing, write ``data/mink/logprobs-qwen2.5-0.5b.jsonl``.
  Convention: input = ``[<|endoftext|>] + tokens(text)``; every text token is scored, the
  prepended end-of-text token only provides context (Qwen has no BOS token).
* ``report``      numpy-only replay from the committed files: ``docs/results/mink-demo.md``
  and ``.json``. Needs neither the model, the key nor the network.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

from evalkit.llmcache import CachedCompleter, summarize_cache
from evalkit.mink import (
    auroc,
    classify_auroc,
    length_matched_mask,
    masked_auroc,
    mean_logprob,
    min_k_prob,
    pair_wins,
    paired_bootstrap,
    percentile_ci,
    residualize,
    same_numbers,
    zlib_length,
    zlib_ratio,
)

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "raw" / "gsm8k_test.jsonl"
OUT = ROOT / "data" / "mink"
PAIRS = OUT / "pairs.jsonl"
CACHE = OUT / "paraphrase-cache.jsonl"
LOGPROBS = OUT / "logprobs-qwen2.5-0.5b.jsonl"
RESULT_MD = ROOT / "docs" / "results" / "mink-demo.md"
RESULT_JSON = ROOT / "docs" / "results" / "mink-demo.json"

N_ITEMS = 150
SEED = 0
PARAPHRASER = "claude-haiku-5-5"
MAX_CALLS = 200
# ASSUMED list prices in USD per million tokens (not read from the API).
ASSUMED_PRICE = {"input": 1.00, "output": 5.00}
MODEL_ID = "Qwen/Qwen2.5-0.5B"
MODEL_REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"
MAX_TOKENS = 512
KS = (10, 20, 30, 50)
PRIMARY_K = 20
MATCH_DIFF = 5
N_BOOT = 2000

SYSTEM = "You rewrite math word problems. Output only the rewritten problem."
PROMPT = """Rewrite the following math word problem.
Rules:
- Keep every number, quantity, name and entity exactly. Digits stay digits; do not spell numbers out, round, or convert units.
- Change the wording and the sentence structure (reorder clauses, use different verbs and connectors, split or merge sentences).
- Add no new information and no hints, remove nothing, and do not solve it.
- Output only the rewritten problem, with no preamble.

Problem:
{question}"""  # noqa: E501


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _norm(s: str) -> str:
    return " ".join(s.split())


def select_questions(
    source: Path = SOURCE, n: int = N_ITEMS, seed: int = SEED
) -> list[dict[str, Any]]:
    """First ``n`` rows of ``random.Random(seed).shuffle`` of the split (as build_gsm8k_subset)."""
    rows = _read_jsonl(source)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    return [{"id": f"gsm8k_test_{i:04d}", "original": rows[i]["question"]} for i in order[:n]]


def cmd_paraphrase(args: argparse.Namespace) -> None:
    items = select_questions()[: args.limit or N_ITEMS]
    backend = None
    if not args.cache_only:
        from evalkit.models import AnthropicModel

        backend = AnthropicModel(PARAPHRASER)
    completer = CachedCompleter(backend, CACHE, model_id=PARAPHRASER, max_calls=MAX_CALLS)
    pairs: list[dict[str, Any]] = []
    for item in items:
        out = completer.complete(PROMPT.format(question=item["original"]), system=SYSTEM)
        para = out.text.strip()
        if not para:
            status = "empty"
        elif _norm(para) == _norm(item["original"]):
            status = "identical"
        elif not same_numbers(item["original"], para):
            status = "numbers_differ"
        else:
            status = "kept"
        pairs.append({**item, "paraphrase": para, "status": status})
    _write_jsonl(PAIRS, pairs)
    kept = sum(p["status"] == "kept" for p in pairs)
    st = completer.stats
    print(
        f"{len(pairs)} paraphrased, {kept} kept; live calls {st.live_calls}, hits {st.hits}, "
        f"tokens in/out {st.input_tokens}/{st.output_tokens}",
        file=sys.stderr,
    )


def cmd_score(args: argparse.Namespace) -> None:
    import torch  # lazy: optional `hf` extra, never imported on the default path
    from transformers import AutoModelForCausalLM, AutoTokenizer

    pairs = [p for p in _read_jsonl(PAIRS) if p["status"] == "kept"]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, dtype=torch.float32, use_safetensors=True
    ).to(device)
    model.eval()
    eos = tok.convert_tokens_to_ids("<|endoftext|>")
    rows: list[dict[str, Any]] = []
    for p in pairs:
        for kind in ("original", "paraphrase"):
            text = p[kind]
            ids = tok(text, add_special_tokens=False)["input_ids"][:MAX_TOKENS]
            inp = torch.tensor([[eos, *ids]], device=device)
            with torch.no_grad():
                logits = model(inp).logits[0, :-1].float()
            logp = torch.log_softmax(logits, dim=-1)
            tgt = torch.tensor(ids, device=device)
            lp = logp[torch.arange(len(ids), device=device), tgt].cpu().tolist()
            rows.append(
                {
                    "id": p["id"],
                    "kind": kind,
                    "text": text,
                    "token_ids": ids,
                    "tokens": tok.convert_ids_to_tokens(ids),
                    "logprobs": lp,
                    "model": MODEL_ID,
                    "revision": MODEL_REVISION,
                    "device": device,
                    "dtype": "float32",
                    "context_token": "<|endoftext|>",
                }
            )
    _write_jsonl(LOGPROBS, rows)
    print(f"scored {len(rows)} texts on {device} -> {LOGPROBS}", file=sys.stderr)


def _scores(rows: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    out: dict[str, list[float]] = {f"minK{k}": [] for k in KS}
    out["mean_logprob"] = []
    out["zlib_ratio"] = []
    for r in rows:
        lp = r["logprobs"]
        for k in KS:
            out[f"minK{k}"].append(min_k_prob(lp, k))
        out["mean_logprob"].append(mean_logprob(lp))
        out["zlib_ratio"].append(zlib_ratio(lp, r["text"]))
    return {k: np.asarray(v, dtype=np.float64) for k, v in out.items()}


def _ci(samples: np.ndarray) -> list[float]:
    lo, hi = percentile_ci(samples)
    return [round(lo, 4), round(hi, 4)]


def compute(pairs_path: Path = PAIRS, logprobs_path: Path = LOGPROBS) -> dict[str, Any]:
    pairs = _read_jsonl(pairs_path)
    status: dict[str, int] = {}
    for p in pairs:
        status[p["status"]] = status.get(p["status"], 0) + 1
    by_key = {(r["id"], r["kind"]): r for r in _read_jsonl(logprobs_path)}
    ids = [p["id"] for p in pairs if p["status"] == "kept"]
    orig_rows = [by_key[(i, "original")] for i in ids]
    para_rows = [by_key[(i, "paraphrase")] for i in ids]
    n = len(ids)
    so, sp = _scores(orig_rows), _scores(para_rows)
    lo_len = np.array([len(r["logprobs"]) for r in orig_rows], dtype=np.float64)
    lp_len = np.array([len(r["logprobs"]) for r in para_rows], dtype=np.float64)

    def boot(fn: Any) -> np.ndarray:
        return paired_bootstrap(fn, n, n_boot=N_BOOT, seed=SEED)

    mask = length_matched_mask(lo_len, lp_len, MATCH_DIFF)
    n_matched = int(mask.sum())
    res: dict[str, Any] = {"scores": {}}
    samples: dict[str, np.ndarray] = {}
    for name in so:
        a, b = so[name], sp[name]
        wins = pair_wins(a, b)
        s_main = boot(lambda idx, a=a, b=b: auroc(a[idx], b[idx]))
        samples[name] = s_main
        s_match = boot(lambda idx, w=wins: masked_auroc(w, mask, idx, idx))

        def resid(idx: np.ndarray, a: np.ndarray = a, b: np.ndarray = b) -> float:
            score = np.concatenate([a[idx], b[idx]])
            length = np.concatenate([lo_len[idx], lp_len[idx]])
            r = residualize(score, length)
            return auroc(r[:n], r[n:])

        s_resid = boot(resid)
        full = np.arange(n)
        point = auroc(a, b)
        point_match = masked_auroc(wins, mask, full, full)
        score_all = np.concatenate([a, b])
        len_all = np.concatenate([lo_len, lp_len])
        r_all = residualize(score_all, len_all)
        point_resid = auroc(r_all[:n], r_all[n:])
        win_rate = float(((a > b) + 0.5 * (a == b)).mean())
        s_win = boot(
            lambda idx, a=a, b=b: float(((a[idx] > b[idx]) + 0.5 * (a[idx] == b[idx])).mean())
        )
        ci = _ci(s_main)
        res["scores"][name] = {
            "auroc": round(point, 4),
            "ci": ci,
            "verdict": classify_auroc(*ci),
            "auroc_matched": round(point_match, 4),
            "ci_matched": _ci(s_match),
            "auroc_residualised": round(point_resid, 4),
            "ci_residualised": _ci(s_resid),
            "paired_win_rate": round(win_rate, 4),
            "ci_paired_win_rate": _ci(s_win),
            "mean_original": round(float(a.mean()), 4),
            "mean_paraphrase": round(float(sp[name].mean()), 4),
        }
    prim = f"minK{PRIMARY_K}"
    res["difference_vs_primary"] = {}
    for other in ("mean_logprob", "zlib_ratio", "minK10", "minK30", "minK50"):
        d = samples[prim] - samples[other]
        point = auroc(so[prim], sp[prim]) - auroc(so[other], sp[other])
        res["difference_vs_primary"][other] = {
            "diff": round(point, 4),
            "ci": _ci(d),
            "excludes_0": bool(_ci(d)[0] > 0 or _ci(d)[1] < 0),
        }
    len_samples = boot(lambda idx: auroc(lo_len[idx], lp_len[idx]))
    res["token_count"] = {
        "median_original": float(np.median(lo_len)),
        "median_paraphrase": float(np.median(lp_len)),
        "mean_original": round(float(lo_len.mean()), 2),
        "mean_paraphrase": round(float(lp_len.mean()), 2),
        "auroc_of_length_alone": round(auroc(lo_len, lp_len), 4),
        "ci": _ci(len_samples),
        "zlib_bytes_median_original": float(np.median([zlib_length(r["text"]) for r in orig_rows])),
        "zlib_bytes_median_paraphrase": float(
            np.median([zlib_length(r["text"]) for r in para_rows])
        ),
    }
    res.update(
        {
            "n_selected": len(pairs),
            "status_counts": status,
            "n_pairs": n,
            "n_matched_pairs": n_matched,
            "n_possible_pairs": n * n,
            "match_diff_tokens": MATCH_DIFF,
            "n_boot": N_BOOT,
            "seed": SEED,
            "primary": prim,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
        }
    )
    return res


def ledger() -> dict[str, Any]:
    s = summarize_cache(CACHE)
    cost = (
        s["input_tokens"] * ASSUMED_PRICE["input"] + s["output_tokens"] * ASSUMED_PRICE["output"]
    ) / 1e6
    return {
        "live_calls": s["calls"],
        "input_tokens": s["input_tokens"],
        "output_tokens": s["output_tokens"],
        "models_returned": s["models_returned"],
        "assumed_price_usd_per_million": ASSUMED_PRICE,
        "cost_usd_assumed": round(cost, 4),
    }


def _fmt(v: float, ci: list[float]) -> str:
    return f"{v:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"


def outcome_lines(res: dict[str, Any]) -> list[str]:
    """Pre-registered predictions (docs/protocol-mink.md) checked against the numbers."""
    sc = res["scores"]
    prim = sc[res["primary"]]
    lo, hi = prim["ci"]
    p1 = "met" if hi < 0.5 or (lo < 0.5 and prim["auroc"] < 0.5) else "not met"
    shrink = abs(prim["auroc_matched"] - 0.5) < abs(prim["auroc"] - 0.5) and abs(
        prim["auroc_residualised"] - 0.5
    ) < abs(prim["auroc"] - 0.5)
    dml = res["difference_vs_primary"]["mean_logprob"]
    tl = res["token_count"]
    length_off = tl["ci"][0] > 0.5 or tl["ci"][1] < 0.5
    return [
        f"1. K=20 AUROC below 0.5: **{p1}**. AUROC {prim['auroc']:.3f} "
        f"[{lo:.3f}, {hi:.3f}] -> {prim['verdict']}.",
        "2. If the K=20 CI is above 0.5, matched-length and residualised AUROC shrink towards "
        f"0.5: **{'met' if shrink else 'not met'}**"
        f"{'' if lo > 0.5 else ' (moot: the K=20 CI is not above 0.5)'} "
        f"(matched {prim['auroc_matched']:.3f}, residualised {prim['auroc_residualised']:.3f}).",
        f"3. Min-K% does not beat mean log-prob (difference CI includes 0): "
        f"**{'not met' if dml['excludes_0'] else 'met'}**; AUROC difference "
        f"{dml['diff']:+.3f} [{dml['ci'][0]:+.3f}, {dml['ci'][1]:+.3f}] "
        f"({'mean log-prob scores higher' if dml['diff'] < 0 else 'Min-K% scores higher'}).",
        f"4. Token count alone differs from 0.5: **{'met' if length_off else 'not met'}** "
        f"(AUROC {tl['auroc_of_length_alone']:.3f} [{tl['ci'][0]:.3f}, {tl['ci'][1]:.3f}]; "
        "paraphrases are longer).",
        "",
        "No multiplicity correction is applied across scores and K. Any 'separates' verdict "
        "means only that the originals score higher than the paraphrases under this model; it "
        "is confounded with style and vocabulary and is not evidence of memorisation.",
        "",
    ]


def render(res: dict[str, Any], led: dict[str, Any]) -> str:
    sc = res["scores"]
    names = [f"minK{k}" for k in KS] + ["mean_logprob", "zlib_ratio"]
    label = {f"minK{k}": f"Min-K% (K={k})" + (" **primary**" if k == PRIMARY_K else "") for k in KS}
    label["mean_logprob"] = "mean log-prob (baseline)"
    label["zlib_ratio"] = "zlib ratio (baseline)"
    lines = [
        "# Min-K% Prob demo (Qwen2.5-0.5B, GSM8K test vs Claude paraphrases)",
        "",
        "**A DEMO of the Min-K% Prob method on a tiny model. It is not a contamination audit of "
        "Qwen2.5-0.5B, of any other model, or of GSM8K.** Protocol: `docs/protocol-mink.md` "
        "(committed before scoring). Reproduce: `uv run --offline python scripts/mink_demo.py "
        "report` (replays committed caches; no model, key or network).",
        "",
        f"- Model `{res['model']}` revision `{res['revision']}`, float32; log-probs under teacher "
        "forcing after a prepended `<|endoftext|>` context token.",
        f"- {res['n_selected']} questions selected (`random.Random(0)`), "
        f"{res['n_pairs']} kept after the number-multiset check; dropped: "
        f"{ {k: v for k, v in res['status_counts'].items() if k != 'kept'} or 'none' }.",
        "- Statistic: AUROC of originals (label 1) vs paraphrases (label 0); 95% paired "
        f"cluster-bootstrap CI over source questions, {res['n_boot']} resamples, "
        f"seed {res['seed']}.",
        "",
        "## Primary result and baselines",
        "",
        "| score | AUROC [95% CI] | verdict | matched-length AUROC | residualised AUROC | "
        "orig > para (win rate) |",
        "|---|---|---|---|---|---|",
    ]
    for nm in names:
        r = sc[nm]
        lines.append(
            f"| {label[nm]} | {_fmt(r['auroc'], r['ci'])} | {r['verdict']} | "
            f"{_fmt(r['auroc_matched'], r['ci_matched'])} | "
            f"{_fmt(r['auroc_residualised'], r['ci_residualised'])} | "
            f"{_fmt(r['paired_win_rate'], r['ci_paired_win_rate'])} |"
        )
    tc = res["token_count"]
    lines += [
        "",
        f"Matched-length AUROC uses the {res['n_matched_pairs']} of {res['n_possible_pairs']} "
        f"(original, paraphrase) pairs whose token counts differ by at most "
        f"{res['match_diff_tokens']}. Residualised: OLS of the score on token count, refit in "
        "every resample.",
        "",
        "## AUROC of the primary score minus another score (same resamples)",
        "",
        "| other score | difference [95% CI] | CI excludes 0 |",
        "|---|---|---|",
    ]
    for nm, d in res["difference_vs_primary"].items():
        lines.append(f"| {label[nm]} | {_fmt(d['diff'], d['ci'])} | {d['excludes_0']} |")
    lines += [
        "",
        "## Length",
        "",
        f"Token count (Qwen tokens): originals median {tc['median_original']:.0f} "
        f"(mean {tc['mean_original']}), paraphrases median {tc['median_paraphrase']:.0f} "
        f"(mean {tc['mean_paraphrase']}). AUROC of token count alone "
        f"{_fmt(tc['auroc_of_length_alone'], tc['ci'])}. Median zlib bytes: originals "
        f"{tc['zlib_bytes_median_original']:.0f}, paraphrases "
        f"{tc['zlib_bytes_median_paraphrase']:.0f}.",
        "",
        "## API ledger (paraphrases)",
        "",
        f"{led['live_calls']} live calls to `{PARAPHRASER}` (returned model id(s): "
        f"{', '.join(led['models_returned'])}), {led['input_tokens']} input and "
        f"{led['output_tokens']} output tokens, approx. ${led['cost_usd_assumed']:.4f} at ASSUMED "
        f"list prices of ${ASSUMED_PRICE['input']:.2f} / ${ASSUMED_PRICE['output']:.2f} per "
        "million input / output tokens (not read from the API). Cap: 200 calls, about $0.50.",
        "",
        "## Outcome against the pre-registered predictions",
        "",
        *outcome_lines(res),
        "",
        "## Reading and limits",
        "",
        "Decision rule (protocol): CI above 0.5 means the score separates originals from "
        "paraphrases, which is not proof of memorisation; CI including 0.5 means no detectable "
        "effect; CI below 0.5 means the paraphrases look more likely than the originals. "
        "Confounds: paraphrase style and length differ from the originals, the paraphrases come "
        "from one LLM with one prompt, the originals are only candidate members, and the model "
        "may have seen GSM8K-like data without the test split.",
    ]
    return "\n".join(lines) + "\n"


def cmd_report(_args: argparse.Namespace) -> None:
    res = compute()
    led = ledger()
    RESULT_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULT_MD.write_text(render(res, led), encoding="utf-8")
    RESULT_JSON.write_text(
        json.dumps({"results": res, "ledger": led}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {RESULT_MD} and {RESULT_JSON}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("paraphrase")
    p.add_argument("--limit", type=int, help="pilot: only the first N questions")
    p.add_argument("--cache-only", action="store_true")
    p.set_defaults(fn=cmd_paraphrase)
    sub.add_parser("score").set_defaults(fn=cmd_score)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    args = ap.parse_args()
    if args.cmd == "paraphrase" and not args.cache_only and "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY not set; only cached requests will succeed", file=sys.stderr)
    args.fn(args)


if __name__ == "__main__":
    main()
