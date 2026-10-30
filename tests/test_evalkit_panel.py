"""Judge panel aggregation, self-preference excess, cost arithmetic, and cache-only scoring.

No network and no key: a fake completer writes tiny caches, scoring replays them.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

from evalkit.judge import Judge, Verdict, pair_item_from_row
from evalkit.llmcache import CachedCompleter
from evalkit.models import Completion
from evalkit.panel import (
    JudgeOrders,
    Price,
    codes,
    cohen_kappa,
    cost_per_1k,
    decision_score,
    excess,
    human_score,
    majority_vote,
    mean_vote,
    panel_cost_per_1k,
    panel_majority,
    panel_mean,
    reference_side,
    resolved_verdict,
    signed,
    stratified_sample,
    usage_cost,
)

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "mtbench_panel.py"


# --- aggregation -----------------------------------------------------------------------------


def test_signed_codes() -> None:
    assert [signed(v) for v in ("A", "B", "tie", "invalid")] == [1, -1, 0, 0]


def test_resolved_verdict_both_orders() -> None:
    assert resolved_verdict("A", "A") == "A"
    assert resolved_verdict("B", "B") == "B"
    assert resolved_verdict("tie", "tie") == "tie"
    assert resolved_verdict("A", "B") == "tie"  # position flip
    assert resolved_verdict("A", "tie") == "tie"
    assert resolved_verdict("invalid", "invalid") == "tie"
    assert resolved_verdict("A", None) == "A"  # one order only


@pytest.mark.parametrize(
    ("votes", "want"),
    [
        (["A", "A", "A"], "A"),
        (["A", "A", "B"], "A"),
        (["B", "A", "B"], "B"),
        (["A", "A", "tie"], "A"),
        (["A", "B", "tie"], "tie"),  # 3-way split
        (["A", "tie", "tie"], "tie"),  # one vote is not a majority
        (["tie", "tie", "tie"], "tie"),
        (["B", "tie", "tie"], "tie"),
        (["A", "invalid", "invalid"], "tie"),
    ],
)
def test_majority_vote_edge_cases(votes: list[Verdict], want: str) -> None:
    assert majority_vote(votes) == want


def test_majority_vote_needs_strictly_more_than_half() -> None:
    assert majority_vote(["A", "B"]) == "tie"
    assert majority_vote(["A", "A", "B", "B"]) == "tie"
    assert majority_vote(["A"]) == "A"
    with pytest.raises(ValueError):
        majority_vote([])


def test_mean_vote_band() -> None:
    # six per-order verdicts: net margin of 1 stays a tie, margin of 2 decides (band 0.2)
    assert mean_vote(["A", "A", "B", "tie", "tie", "tie"]) == "tie"  # net 1: mean 1/6 <= 0.2
    assert mean_vote(["A", "A", "A", "B", "tie", "tie"]) == "A"  # net 2: mean 2/6 > 0.2
    assert mean_vote(["B", "B", "B", "A", "tie", "tie"]) == "B"
    assert mean_vote(["A", "A", "A", "A", "A", "A"]) == "A"
    assert mean_vote(["A", "A", "A", "B", "B", "B"]) == "tie"
    assert mean_vote(["A", "A", "B", "tie", "tie", "tie"], band=0.0) == "A"
    assert mean_vote(["invalid", "A", "tie", "tie", "tie", "tie"]) == "tie"
    with pytest.raises(ValueError):
        mean_vote([])
    with pytest.raises(ValueError):
        mean_vote(["A"], band=-0.1)


def test_panel_both_orders_and_halves() -> None:
    # Haiku flips with position, Sonnet and Opus say A in both orders
    judges = [JudgeOrders("A", "B"), JudgeOrders("A", "A"), JudgeOrders("A", "A")]
    maj = panel_majority(judges)
    assert maj.resolved == "A"  # resolved: tie, A, A -> 2 of 3
    assert (maj.first, maj.second) == ("A", "A")
    assert not maj.flipped
    mean = panel_mean(judges)
    assert mean.resolved == "A"  # five A, one B -> mean 4/6
    assert mean.valid


def test_panel_three_way_split_is_tie_in_majority_but_not_always_in_mean() -> None:
    judges = [JudgeOrders("A", "A"), JudgeOrders("B", "B"), JudgeOrders("tie", "tie")]
    assert panel_majority(judges).resolved == "tie"
    assert panel_mean(judges).resolved == "tie"  # 2 A, 2 B, 2 tie
    judges = [JudgeOrders("A", "A"), JudgeOrders("A", "A"), JudgeOrders("B", "tie")]
    assert panel_majority(judges).resolved == "A"
    judges = [JudgeOrders("A", "A"), JudgeOrders("tie", "tie"), JudgeOrders("B", "tie")]
    assert panel_majority(judges).resolved == "tie"  # A, tie, tie
    assert panel_mean(judges).resolved == "tie"  # net +1 of 6 stays inside the band


def test_panel_position_flip_and_invalid() -> None:
    # the panel flips: A wins in the first order, B in the second
    judges = [JudgeOrders("A", "B"), JudgeOrders("A", "B"), JudgeOrders("tie", "B")]
    maj = panel_majority(judges)
    assert (maj.first, maj.second) == ("A", "B")  # firsts A, A, tie; seconds B, B, B
    assert maj.resolved == "tie"  # tie, tie, tie
    judges = [JudgeOrders("A", "invalid"), JudgeOrders("A", "A"), JudgeOrders("A", "A")]
    maj = panel_majority(judges)
    assert not maj.valid and not maj.flipped
    assert maj.resolved == "A"  # first judge resolves to tie, the other two say A
    with pytest.raises(ValueError):
        panel_majority([JudgeOrders("A", None)])


def test_panel_flip_rate_halves() -> None:
    judges = [JudgeOrders("A", "B"), JudgeOrders("A", "B"), JudgeOrders("B", "A")]
    # firsts A, A, B -> A; seconds B, B, A -> B
    maj = panel_majority(judges)
    assert (maj.first, maj.second) == ("A", "B")
    assert maj.flipped and maj.same_slot


# --- self-preference excess ------------------------------------------------------------------


def test_reference_side() -> None:
    assert reference_side("claude-v1", "gpt-4") == 1
    assert reference_side("alpaca-13b", "claude-v1") == -1
    with pytest.raises(ValueError):
        reference_side("gpt-4", "llama-13b")
    with pytest.raises(ValueError):
        reference_side("claude-v1", "claude-v1")


def test_excess_sign_convention() -> None:
    # claude is A: judge says A (claude wins, +1), humans split A, B -> mean 0 -> excess +1
    assert excess("A", ["A", "B"], 1) == pytest.approx(1.0)
    # claude is B: judge says A (claude loses, -1), both humans say B (claude wins, +1) -> -2
    assert excess("A", ["B", "B"], -1) == pytest.approx(-2.0)
    # judge tie vs humans all for claude (A, claude is A): 0 - 1
    assert excess("tie", ["A", "A", "A"], 1) == pytest.approx(-1.0)
    # claude is B, both agree claude wins: no excess
    assert excess("B", ["B"], -1) == pytest.approx(0.0)
    # a judge that favours claude more than the humans gives a positive excess
    assert excess("B", ["tie", "A"], -1) > 0
    assert decision_score("A", 1) == 1 and decision_score("A", -1) == -1
    assert decision_score("tie", -1) == 0
    assert math.isnan(human_score([], 1))
    with pytest.raises(ValueError):
        decision_score("A", 0)


# --- kappa, cost, sampling -------------------------------------------------------------------


def test_cohen_kappa() -> None:
    a = codes(["A", "B", "tie", "A", "B", "tie"])
    assert cohen_kappa(a, a) == pytest.approx(1.0)
    b = codes(["B", "A", "tie", "tie", "A", "B"])
    assert cohen_kappa(a, b) < 0.1
    assert cohen_kappa(a, a, np.array([1, 1, 1, 0, 0, 0], dtype=float)) == pytest.approx(1.0)
    assert math.isnan(cohen_kappa(np.array([], dtype=np.int64), np.array([], dtype=np.int64)))


def test_cost_arithmetic() -> None:
    price = Price(3.0, 15.0)
    assert usage_cost(1_000_000, 0, price) == pytest.approx(3.0)
    assert usage_cost(0, 2_000_000, price) == pytest.approx(30.0)
    # 100 resolved verdicts using 400k input and 60k output tokens at $3/$15 per million
    c = cost_per_1k(400_000, 60_000, price, 100)
    assert c == pytest.approx((1.2 + 0.9) / 100 * 1000)
    assert panel_cost_per_1k([8.6, 17.4, 33.8]) == pytest.approx(59.8)
    with pytest.raises(ValueError):
        cost_per_1k(1, 1, price, 0)


def test_stratified_sample_is_seeded_and_stratified() -> None:
    keys = [(t, c) for t in (1, 2) for c in "abcd" for _ in range(10)]
    s1 = stratified_sample(keys, 16, seed=0)
    assert s1 == stratified_sample(keys, 16, seed=0)
    assert s1 != stratified_sample(keys, 16, seed=1)
    assert len(s1) == 16 and s1 == sorted(s1)
    cells = {keys[i] for i in s1}
    assert len(cells) == 8  # 2 per cell
    assert stratified_sample(keys, 1000) == list(range(len(keys)))
    # largest remainder: 5 over cells of size 4, 4, 2 -> 2, 2, 1
    assert len(stratified_sample([(0,)] * 4 + [(1,)] * 4 + [(2,)] * 2, 5)) == 5


# --- cache-only scoring through the script ----------------------------------------------------


class _Scripted:
    """Fake judge model: the verdict depends on the response texts, and on the judge's bias."""

    def __init__(self, model_id: str, favour: str) -> None:
        self.model_id = model_id
        self.favour = favour

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion:
        shown_a = prompt.split("[Response A]")[1].split("[End of Response A]")[0]
        pick = "TIE" if "question 3" in prompt else ("A" if self.favour in shown_a else "B")
        text = f"explanation\nVERDICT: {pick}"
        return Completion(text, self.model_id, 100 + len(prompt) % 7, 20)


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mtbench_panel_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _rows() -> list[dict[str, Any]]:
    rows = []
    models = [("claude-v1", "gpt-4"), ("alpaca-13b", "claude-v1"), ("gpt-4", "llama-13b")]
    for q in range(1, 7):
        for t in (1, 2):
            ma, mb = models[(q + t) % 3]
            a = f"alpha answer {q} {t} " * (1 + q % 3)
            b = f"beta answer {q} {t}"
            votes = [
                ["expert_1", "A" if (q + t) % 2 else "B"],
                ["expert_2", "tie" if q % 3 == 0 else "A"],
            ]
            rows.append(
                {
                    "id": f"q{q}-t{t}",
                    "task": f"mt-bench-turn{t}",
                    "cluster_id": f"q{q}",
                    "question_id": q,
                    "category": "writing" if q % 2 else "math",
                    "turn": t,
                    "model_a": ma,
                    "model_b": mb,
                    "prompt": f"question {q}",
                    "instruction": "judge",
                    "response_a": a,
                    "response_b": b,
                    "length_a": len(a.split()),
                    "length_b": len(b.split()),
                    "human_votes": votes,
                    "gpt4_verdict": ["A", "B", "tie"][(q + t) % 3],
                }
            )
    return rows


def test_score_runs_from_caches_without_a_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_script()
    rows = _rows()
    (tmp_path / "test.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    chosen = [r["id"] for r in rows if r["id"] not in {"q1-t1", "q6-t2"}]
    (tmp_path / "panel-subsample.json").write_text(json.dumps({"ids": chosen}))
    caches = {j: tmp_path / f"cache-{j}.jsonl" for j in ("haiku", "sonnet", "opus")}
    monkeypatch.setattr(mod, "DATA", tmp_path)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "SUBSAMPLE", tmp_path / "panel-subsample.json")
    monkeypatch.setattr(mod, "CACHES", caches)
    monkeypatch.setattr(
        mod, "PILOT_CACHES", {j: tmp_path / f"pilot-{j}.jsonl" for j in ("haiku", "opus")}
    )
    favour = {"haiku": "alpha", "sonnet": "alpha", "opus": "beta"}
    by_id = {r["id"]: r for r in rows}
    for j, path in caches.items():
        comp = CachedCompleter(
            _Scripted(mod.MODEL_IDS[j], favour[j]), path, model_id=mod.MODEL_IDS[j]
        )
        judge = Judge(comp, max_tokens=mod.MAX_TOKENS[j])
        todo = rows if j == "sonnet" else [by_id[i] for i in chosen]
        judge.compare_many([pair_item_from_row(r) for r in todo])
    out = tmp_path / "report.md"
    args = argparse.Namespace(boot=40, out=str(out))
    assert mod.score(args) == 0  # replays the caches; any miss would raise CacheMiss
    text = out.read_text()
    assert "Pre-registered decisions" in text and "Self-preference" in text
    assert "cost per 1,000 resolved verdicts" in text
    res = json.loads(out.with_suffix(".json").read_text())
    assert set(res["cost_per_1k"]) == {"haiku", "sonnet", "opus", "panel"}
    assert res["cost_per_1k"]["panel"] == pytest.approx(
        res["cost_per_1k"]["haiku"] + res["cost_per_1k"]["sonnet"] + res["cost_per_1k"]["opus"]
    )
    assert res["ledger"]["calls"] == 2 * len(chosen) * 2  # haiku + opus, 2 orders each
    sp = res["self_preference_subsample"]
    assert "sonnet" in sp and "gpt4" in sp and "sonnet-gpt4" in sp
    assert res["All subsample items"]["haiku.jh_s1"][0] >= 0.0
