"""GSM8K contamination probe: templates, solver checks, variants, scoring. Offline, no key."""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

from evalkit.contamination import (
    Template,
    TemplateReject,
    build_prompt,
    build_template,
    check_template,
    check_variant,
    drop_analysis,
    drop_difference,
    exact_mcnemar_p,
    find_slots,
    holm_adjust,
    make_variants,
    neutrality,
    render,
    score_reply,
    slot_grid,
    solve,
    verdict,
)
from evalkit.llmcache import CachedCompleter, CacheMiss
from evalkit.models import Completion

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contamination"

JANET_Q = (
    "Janet\u2019s ducks lay 16 eggs per day. She eats three for breakfast every morning and "
    "bakes muffins for her friends every day with four. She sells the remainder at the "
    "farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every "
    "day at the farmers' market?"
)
JANET_A = (
    "Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.\n"
    "She makes 9 * 2 = $<<9*2=18>>18 every day at the farmer\u2019s market.\n#### 18"
)


def _rows(name: str) -> list[dict[str, Any]]:
    return [json.loads(x) for x in (DATA / name).read_text(encoding="utf-8").splitlines() if x]


# ------------------------------------------------------------------------------ construction


def test_janet_template_and_variants() -> None:
    t = build_template("janet", JANET_Q, JANET_A)
    assert [s.text for s in t.slots] == ["16", "three", "four", "2"]
    assert t.steps == ("s0-s1-s2", "r0*s3")
    assert solve(t)[-1] == 18 and not check_template(t)
    variants = make_variants(t)
    assert len(variants) == 2
    for v in variants:
        assert v.gold > 0 and not check_variant(t, v.values)
        assert v.gold == int(solve(t, v.values)[-1])
        assert v.question == render(t, v.values) and v.question != JANET_Q
    assert variants[0].gold != variants[1].gold and variants[0].values != variants[1].values
    assert make_variants(t) == variants  # deterministic under the seed


def test_slots_keep_digit_class_and_formatting() -> None:
    t = build_template("janet", JANET_Q, JANET_A)
    for v in make_variants(t):
        for s, x in zip(t.slots, v.values, strict=True):
            assert x.denominator == 1 and x >= 2
            assert len(str(int(x))) == len(str(int(s.value)))
    big = build_template(
        "big",
        "A shop has 1,200 pens and sells 300 of them. How many pens are left?",
        "1,200 - 300 = <<1200-300=900>>900 pens\n#### 900",
    )
    for v in make_variants(big):
        assert "," in v.question.split(" pens")[0]  # thousands comma kept


@pytest.mark.parametrize(
    ("question", "answer", "reason"),
    [
        ("Ann has 5 apples.", "She has 5 apples.\n#### 5", "no_annotations"),
        (
            "Ann has 5 apples and buys 7 more. How many?",
            "5 + 7 + 9 = <<5+7+9=21>>21\n#### 21",
            "unmapped_constant",
        ),
        (
            "Ann has 5 apples and buys 7 more. How many?",
            "5 + 7 = <<5+7=12>>12\n#### 13",
            "final_mismatch",
        ),
        (
            "Ann has 5 apples and buys 7 more. How many?",
            "5 + 7 = <<5+7=13>>13\n#### 13",
            "annotation_mismatch",
        ),
        (
            "Ann ran 3-4 miles and 6 more. How many?",
            "3 + 6 = <<3+6=9>>9\n#### 9",
            "unsupported_question_format",
        ),
        (
            "Ann has 5 apples and 7 pears. How many?",
            "5 ** 2 = <<5**2=25>>25\n#### 25",
            "unsupported_expression",
        ),
    ],
)
def test_rejections(question: str, answer: str, reason: str) -> None:
    with pytest.raises(TemplateReject) as e:
        build_template("x", question, answer)
    assert e.value.reason == reason


def test_ambiguous_operand_is_rejected() -> None:
    # 9 is both the first result and a literal that coincides with a perturbable number
    q = "Ann has 4 red and 5 blue marbles and finds 9 more. How many?"
    a = "4 + 5 = <<4+5=9>>9\n9 + 9 = <<9+9=18>>18\n#### 18"
    with pytest.raises(TemplateReject) as e:
        build_template("x", q, a)
    assert e.value.reason == "ambiguous_operand"


def test_implicit_constant_slots_are_frozen() -> None:
    q = "Tom has 2 cats and buys twice as many dogs. He then buys 8 fish. How many pets?"
    slots = {s.text: s for s in find_slots(q)}
    assert slots["2"].frozen and not slots["8"].frozen  # "twice" licenses the constant 2
    q2 = "Sam has 12 cards, and 12 pens, and 7 books."
    assert all(s.frozen for s in find_slots(q2) if s.text == "12")  # duplicate value


def test_small_reused_slot_is_frozen_and_unused_slot_too() -> None:
    q = "A family has 3 kids. Each kid eats 5 apples. The family also has 40 plums."
    a = "3 * 5 = <<3*5=15>>15\n15 / 3 = <<15/3=5>>5\n#### 5"
    t = build_template("fam", q, a)
    by_text = {s.text: s for s in t.slots}
    assert by_text["3"].frozen and "twice" in by_text["3"].freeze_reason
    assert by_text["40"].frozen and "not used" in by_text["40"].freeze_reason
    assert not by_text["5"].frozen


def test_slot_grid_preserves_roundness() -> None:
    q = "A tank holds 40 liters and 2.5 liters leak per hour for 6 hours."
    slots = {s.text: s for s in find_slots(q)}
    g, lo, hi = slot_grid(slots["40"]) or (Fraction(0), 0, 0)
    assert g % 5 == 0 and all(20 <= k * g <= 60 and (k * g) % 5 == 0 for k in range(lo, hi + 1))
    g2, lo2, hi2 = slot_grid(slots["2.5"]) or (Fraction(0), 0, 0)
    assert all(Fraction(5, 4) <= k * g2 <= Fraction(15, 4) for k in range(lo2, hi2 + 1))


# ------------------------------------------------------------------- the committed dataset


@pytest.fixture(scope="module")
def templates() -> list[Template]:
    return [Template.from_json(r) for r in _rows("templates.jsonl")]


def test_dataset_sizes_and_split(templates: list[Template]) -> None:
    rows = _rows("templates.jsonl")
    items = _rows("items.jsonl")
    n_dev = sum(r["split"] == "dev" for r in rows)
    n_test = sum(r["split"] == "test" for r in rows)
    assert (n_dev, n_test) == (6, 140)
    assert len(items) == 3 * len(rows) == 3 * len(templates)
    dev_ids = {r["id"] for r in rows if r["split"] == "dev"}
    test_ids = {r["id"] for r in rows if r["split"] == "test"}
    assert not dev_ids & test_ids
    assert {i["source_id"] for i in items if i["split"] == "dev"} == dev_ids


def test_solver_reproduces_original_gold_for_every_template(templates: list[Template]) -> None:
    assert templates
    for t in templates:
        assert not check_template(t), t.id
        assert solve(t)[-1] == t.gold
        assert render(t, t.original_values) == t.question


def test_every_variant_is_a_valid_positive_integer(templates: list[Template]) -> None:
    items = {i["id"]: i for i in _rows("items.jsonl")}
    for t in templates:
        orig = items[f"{t.id}#v0"]
        assert orig["gold"] == t.gold and orig["question"] == t.question
        golds = {t.gold}
        for k in (1, 2):
            row = items[f"{t.id}#v{k}"]
            values = tuple(Fraction(x) for x in row["values"])
            assert not check_variant(t, values), (t.id, k)
            gold = solve(t, values)[-1]
            assert gold.denominator == 1 and gold > 0 and int(gold) == row["gold"]
            assert row["question"] == render(t, values)
            assert row["gold"] not in golds
            golds.add(row["gold"])


def test_variants_regenerate_identically_from_the_seed(templates: list[Template]) -> None:
    items = {i["id"]: i for i in _rows("items.jsonl")}
    for t in templates[:25]:
        for k, v in enumerate(make_variants(t), 1):
            assert items[f"{t.id}#v{k}"]["question"] == v.question
            assert items[f"{t.id}#v{k}"]["gold"] == v.gold


def test_perturbed_numbers_keep_digit_count(templates: list[Template]) -> None:
    items = {i["id"]: i for i in _rows("items.jsonl")}
    for t in templates:
        for k in (1, 2):
            values = [Fraction(x) for x in items[f"{t.id}#v{k}"]["values"]]
            for s, x in zip(t.slots, values, strict=True):
                if s.frozen:
                    assert x == s.value
                else:
                    assert len(str(math.floor(x))) == len(str(math.floor(s.value)))
                    assert s.value / 2 <= x <= 3 * s.value / 2


def test_gold_magnitude_is_roughly_neutral(templates: list[Template]) -> None:
    items = {i["id"]: i for i in _rows("items.jsonl") if i["split"] == "test"}
    ids = sorted({i["source_id"] for i in items.values()})
    o = [items[f"{s}#v0"]["gold"] for s in ids]
    p = [[items[f"{s}#v{k}"]["gold"] for k in (1, 2)] for s in ids]
    n = neutrality(o, p)
    assert n["share_same_digit_count"] > 0.6
    assert abs(n["mean_log10_ratio"]) < 0.2


# ----------------------------------------------------------------------------------- scoring


def test_score_reply_modes() -> None:
    assert score_reply("so 6+12 = 18\nAnswer: 18", 18) == 1.0
    assert score_reply("Answer: 1,200", 1200) == 1.0
    assert score_reply("Answer: 17", 18) == 0.0
    assert score_reply("Answer: 18", 18, "helm") == 1.0
    assert score_reply("Answer: 19", 18, "helm") == 0.0
    with pytest.raises(ValueError):
        score_reply("x", 1, "nope")


def test_exact_mcnemar() -> None:
    assert exact_mcnemar_p(0, 0) == 1.0
    assert exact_mcnemar_p(5, 5) == 1.0
    assert exact_mcnemar_p(10, 0) == pytest.approx(2 / 1024)
    assert exact_mcnemar_p(8, 2) == pytest.approx(2 * (1 + 10 + 45) / 1024)


def test_drop_analysis_detects_a_planted_drop() -> None:
    rng = random.Random(1)
    n = 120
    orig = [1.0 if rng.random() < 0.95 else 0.0 for _ in range(n)]
    v1 = [1.0 if rng.random() < 0.7 else 0.0 for _ in range(n)]
    v2 = [1.0 if rng.random() < 0.7 else 0.0 for _ in range(n)]
    r = drop_analysis(orig, [v1, v2], resamples=2000)
    assert 0.15 < r.drop < 0.35 and r.ci95[0] > 0 and r.p_signflip < 0.001
    assert r.orig_right_pert_wrong[0] > r.orig_wrong_pert_right[0]
    assert r.mde_80 > 0 and r.ci975[0] <= r.ci95[0]
    holm = holm_adjust({"a": r, "b": r})
    assert verdict(r, holm["a"]) == "significant drop"


def test_drop_analysis_no_effect_and_negative() -> None:
    rng = random.Random(2)
    n = 100
    orig = [1.0 if rng.random() < 0.8 else 0.0 for _ in range(n)]
    same = [[1.0 if rng.random() < 0.8 else 0.0 for _ in range(n)] for _ in range(2)]
    r = drop_analysis(orig, same, resamples=2000)
    assert r.ci95[0] < 0 < r.ci95[1]
    exact = drop_analysis(orig, [orig, orig], resamples=200)
    assert exact.drop == 0.0 and verdict(exact, 1.0) == "no detectable drop"
    assert verdict(r, 0.9).startswith(("no detectable", "negative drop"))
    better = drop_analysis([0.0] * 50 + [1.0] * 50, [[1.0] * 100, [1.0] * 100], resamples=500)
    assert better.drop < 0
    assert verdict(better, 0.5) == "negative drop (perturbed accuracy higher), not significant"
    assert verdict(better, 0.001).startswith("significant negative drop")


# ----------------------------------------------------- cache-only scoring with a fixture


class _FakeModel:
    """Answers every prompt with a chain of thought and a final line from a lookup."""

    def __init__(self, answers: dict[str, int], model_id: str) -> None:
        self.answers = answers
        self.model_id = model_id
        self.name = model_id

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion:
        for question, answer in self.answers.items():
            if prompt == build_prompt(question):
                return Completion(f"Reasoning.\nAnswer: {answer}", self.model_id, 120, 30)
        raise AssertionError("unexpected prompt")


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "contamination_probe", ROOT / "scripts" / "contamination_probe.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["contamination_probe"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_score_from_fixture_cache_without_key_or_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_script()
    items: list[dict[str, Any]] = []
    n = 12
    for i in range(n):
        for k in range(3):
            items.append(
                {
                    "id": f"src{i:02d}#v{k}",
                    "source_id": f"src{i:02d}",
                    "split": "test",
                    "variant": k,
                    "question": f"Question {i} variant {k}: what is {i + 10 * k + 1} plus 0?",
                    "gold": i + 10 * k + 1,
                    "values": [],
                }
            )
    (tmp_path / "items.jsonl").write_text(
        "\n".join(json.dumps(r) for r in items) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(mod, "OUT", tmp_path)
    monkeypatch.setattr(mod, "RESULTS", tmp_path / "results")
    models = tuple(mod.MODELS)
    for m_i, model in enumerate(models):
        # model 0 fails on one original + all perturbed of three sources; model 1 is perfect
        answers = {}
        for r in items:
            wrong = m_i == 0 and r["source_id"] in {"src00", "src01", "src02"} and r["variant"] > 0
            answers[r["question"]] = r["gold"] + (1 if wrong else 0)
        backend = _FakeModel(answers, model)
        c = CachedCompleter(backend, tmp_path / f"cache-{model}.jsonl", model_id=model)
        for r in items:
            c.complete(build_prompt(r["question"]), max_tokens=mod.MAX_TOKENS)
    assert mod.score(None) == 0  # type: ignore[arg-type]
    payload = json.loads((tmp_path / "results" / "contamination-gsm.json").read_text())
    r0 = payload["results"]["numeric"][models[0]]
    r1 = payload["results"]["numeric"][models[1]]
    assert r0["n"] == n and r0["acc_original"] == 1.0
    assert r0["drop"] == pytest.approx(3 / 12)
    assert r1["drop"] == 0.0
    assert payload["results"]["helm"][models[0]]["drop"] == pytest.approx(3 / 12)
    assert payload["ledger"]["total"]["calls"] == 2 * len(items)
    assert (tmp_path / "results" / "contamination-gsm.md").read_text().startswith("# Contamination")


def test_cache_only_completer_raises_on_a_miss(tmp_path: Path) -> None:
    c = CachedCompleter(None, tmp_path / "empty.jsonl", model_id="m")
    with pytest.raises(CacheMiss):
        c.complete(build_prompt("anything"), max_tokens=1024)


def test_neutrality_arrays() -> None:
    n = neutrality([10, 20, 300], [[12, 25], [9, 40], [250, 400]])
    assert n["n_sources"] == 3
    assert 0.0 <= n["share_same_digit_count"] <= 1.0
    assert np.isfinite(n["mean_log10_ratio"])


def test_drop_difference_signs() -> None:
    orig = [1.0] * 40
    flat = [[1.0] * 40, [1.0] * 40]
    hurt = [[1.0] * 20 + [0.0] * 20, [1.0] * 20 + [0.0] * 20]
    mean, lo, hi = drop_difference(orig, hurt, orig, flat, resamples=500)
    assert mean == pytest.approx(0.5) and lo > 0.3 and hi < 0.7
    mean0, lo0, hi0 = drop_difference(orig, flat, orig, flat, resamples=500)
    assert (mean0, lo0, hi0) == (0.0, 0.0, 0.0)
