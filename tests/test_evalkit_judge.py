"""LLM judge, call cache, agreement statistics and the `judge` CLI. No network: a fake model."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from evalkit import cli
from evalkit.judge import (
    DEFAULT_RUBRIC,
    Judge,
    PairItem,
    PairVerdict,
    PointItem,
    Rubric,
    length_bias,
    parse_score,
    parse_verdict,
    point_verdict,
    position_flip_rate,
    prompt_fingerprint,
    resolve,
    spearman,
)
from evalkit.judge_stats import AgreementData, ValItem, cluster_bootstrap
from evalkit.llmcache import (
    CachedCompleter,
    CacheMiss,
    CallBudgetExceeded,
    read_cache,
    request_key,
    summarize_cache,
)
from evalkit.models import DEFAULT_ANTHROPIC_MODEL, AnthropicModel, Completer, Completion

_RESP = re.compile(r"\[Response( A| B|)\]\n(.*?)\n\[End of Response", re.DOTALL)


class FakeModel:
    """Judges from the prompt text. ``policy``: ``longer`` (the longer response wins),
    ``first`` (always slot A), ``tie``, ``junk`` (no verdict line), ``score`` (pointwise: the
    number of words, capped to the scale)."""

    model_id = "fake-judge"

    def __init__(self, policy: str = "longer") -> None:
        self.policy = policy
        self.prompts: list[str] = []
        self.systems: list[str | None] = []
        self.calls = 0

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion:
        self.calls += 1
        self.prompts.append(prompt)
        self.systems.append(system)
        assert temperature is None
        if "`SCORE:" in prompt:
            n = len(prompt.split("[Response]\n")[1].split("\n[End")[0].split())
            text = f"Fine.\nSCORE: {min(n, 10)}"
        elif "[Response A]" not in prompt:
            text = "ok"
        else:
            blocks = {m.group(1).strip(): m.group(2) for m in _RESP.finditer(prompt)}
            la, lb = len(blocks["A"].split()), len(blocks["B"].split())
            if self.policy == "first":
                v = "A"
            elif self.policy == "tie" or la == lb:
                v = "TIE"
            elif self.policy == "junk":
                return Completion("I cannot decide.", "fake-judge-v2", 10, 3)
            else:
                v = "A" if la > lb else "B"
            text = f"Reasoning.\nVERDICT: {v}"
        return Completion(text, "fake-judge-v2", 100, 7)


def _cached(tmp_path: Path, policy: str = "longer", **kw: Any) -> tuple[CachedCompleter, FakeModel]:
    fake = FakeModel(policy)
    return CachedCompleter(fake, tmp_path / "cache.jsonl", **kw), fake


def test_fake_is_a_completer() -> None:
    assert isinstance(FakeModel(), Completer)


def test_default_anthropic_model_and_no_temperature() -> None:
    assert DEFAULT_ANTHROPIC_MODEL == "claude-sonnet-5-5"
    pytest.importorskip("anthropic")
    model = AnthropicModel(api_key="not-a-real-key")
    assert model.model_id == "claude-sonnet-5-5"
    seen: dict[str, Any] = {}

    class _Resp:
        model = "claude-sonnet-5-5"
        content = (type("B", (), {"text": "hi"})(),)
        usage = type("U", (), {"input_tokens": 3, "output_tokens": 2})()

    class _Messages:
        def create(self, **kw: Any) -> _Resp:
            seen.update(kw)
            return _Resp()

    model.client = type("C", (), {"messages": _Messages()})()  # type: ignore[assignment]
    out = model.complete("q", system="s")
    assert (out.text, out.model, out.input_tokens, out.output_tokens) == (
        "hi",
        model.model_id,
        3,
        2,
    )
    assert seen["extra_body"] == {} and "temperature" not in seen and seen["system"] == "s"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("blah\nVERDICT: A", "A"),
        ("verdict: b", "B"),
        ("Reasoning ... VERDICT: TIE", "tie"),
        ("VERDICT: **A**", "A"),
        ("VERDICT: A\nOn reflection\nVERDICT: B", "B"),
        ("VERDICT: [[A]]", "A"),
        ("no verdict here", "invalid"),
        ("VERDICT: AB", "invalid"),
    ],
)
def test_parse_verdict(text: str, expected: str) -> None:
    assert parse_verdict(text) == expected


def test_parse_score_range_and_last_wins() -> None:
    assert parse_score("SCORE: 7", 1, 10) == 7.0
    assert parse_score("SCORE: 3\nSCORE: 8.5", 1, 10) == 8.5
    assert parse_score("SCORE: 11", 1, 10) is None
    assert parse_score("no score", 1, 10) is None


def test_resolve_inconsistent_is_tie() -> None:
    assert resolve("A", "A") == "A"
    assert resolve("B", "B") == "B"
    assert resolve("A", "B") == "tie"
    assert resolve("A", "tie") == "tie"
    assert resolve("tie", "tie") == "tie"
    assert resolve("A", "invalid") == "tie"
    assert resolve("invalid", "invalid") == "tie"
    assert resolve("A", None) == "A"
    assert resolve("invalid", None) == "tie"


def test_pairwise_runs_both_orders_and_agrees_when_not_position_biased(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path)
    judge = Judge(cached)
    v = judge.compare(PairItem("q", "short one", "a much longer response with many words"))
    assert (v.first, v.second, v.resolved, v.flipped) == ("B", "B", "B", False)
    assert fake.calls == 2
    assert len({p for p in fake.prompts}) == 2  # the two orders are different prompts
    first, second = fake.prompts
    assert first.index("short one") < first.index("a much longer")
    assert second.index("a much longer") < second.index("short one")


def test_position_biased_judge_flips_and_resolves_to_tie(tmp_path: Path) -> None:
    cached, _ = _cached(tmp_path, policy="first")
    judge = Judge(cached)
    items = [PairItem(f"q{i}", f"r{i} a", f"r{i} b c") for i in range(5)]
    verdicts = judge.compare_many(items)
    assert all(v.resolved == "tie" and v.flipped and v.same_slot for v in verdicts)
    assert position_flip_rate(verdicts) == (1.0, 5, 0)


def test_one_order_mode_has_no_flip(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path, policy="first")
    v = Judge(cached, both_orders=False).compare(PairItem("q", "a", "b c"))
    assert (v.first, v.second, v.resolved, v.flipped) == ("A", None, "A", False)
    assert fake.calls == 1
    assert position_flip_rate([v]) == (0.0, 0, 0)


def test_unparsable_reply_is_counted_and_tied(tmp_path: Path) -> None:
    cached, _ = _cached(tmp_path, policy="junk")
    v = Judge(cached).compare(PairItem("q", "a b", "c"))
    assert v.resolved == "tie" and not v.both_valid
    assert position_flip_rate([v]) == (0.0, 0, 1)


def test_reference_and_instruction_reach_the_prompt(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path)
    Judge(cached).compare(
        PairItem("q", "x y", "z", reference="REFERENCE-ANSWER", instruction="Judge turn two.")
    )
    assert all("REFERENCE-ANSWER" in p and "Judge turn two." in p for p in fake.prompts)
    fake.prompts.clear()
    Judge(cached).compare(PairItem("q2", "x y", "z"))
    assert not any("Reference answer" in p for p in fake.prompts)
    assert all(s and "impartial" in s for s in fake.systems)


def test_pointwise_default_and_custom_rubric(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path)
    out = Judge(cached).score(PointItem("q", "one two three"))
    assert out.score == 3.0
    custom = Rubric("brevity", "shorter is better", low=1, high=5)
    Judge(cached, rubric=custom).score(PointItem("q", "one two three four five six seven"))
    assert "brevity" in fake.prompts[-1] and "from 1 (worst) to 5 (best)" in fake.prompts[-1]
    # 7 words but the scale tops out at 5: the fake answers 7, which is out of range
    assert Judge(cached, rubric=custom).score(PointItem("q", "a b c d e f g")).score is None
    assert DEFAULT_RUBRIC.high == 10


def test_point_verdict() -> None:
    assert point_verdict(7, 3) == "A"
    assert point_verdict(3, 7) == "B"
    assert point_verdict(5, 5) == "tie"
    assert point_verdict(None, 5) == "tie"


def test_cache_hits_are_free_and_persisted(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path)
    a = cached.complete("p", system="s", max_tokens=10)
    b = cached.complete("p", system="s", max_tokens=10)
    assert a == b and fake.calls == 1
    s = cached.stats
    assert (s.live_calls, s.hits, s.input_tokens, s.output_tokens) == (1, 1, 100, 7)
    # a new object on the same file replays without a backend
    replay = CachedCompleter(None, tmp_path / "cache.jsonl", model_id="fake-judge")
    assert replay.complete("p", system="s", max_tokens=10) == a
    with pytest.raises(CacheMiss):
        replay.complete("other", system="s", max_tokens=10)
    cached.complete("p", system="s2", max_tokens=10)  # different system: different entry
    cached.complete("p", system="s", max_tokens=11)  # different params: different entry
    assert fake.calls == 3
    rec = read_cache(tmp_path / "cache.jsonl")
    assert len(rec) == 3 and set(rec[0]) == {
        "key",
        "request",
        "response",
        "model_returned",
        "usage",
        "timestamp",
    }
    assert rec[0]["request"] == {
        "model": "fake-judge",
        "system": "s",
        "prompt": "p",
        "params": {"max_tokens": 10, "temperature": None},
    }
    assert rec[0]["model_returned"] == "fake-judge-v2"
    assert summarize_cache(tmp_path / "cache.jsonl")["calls"] == 3
    assert summarize_cache(tmp_path / "cache.jsonl")["models_returned"] == ["fake-judge-v2"]


def test_request_key_depends_on_every_field() -> None:
    base = request_key("m", "s", "p", {"max_tokens": 1})
    assert base == request_key("m", "s", "p", {"max_tokens": 1})
    assert len({base, request_key("m2", "s", "p", {"max_tokens": 1})}) == 2
    assert request_key("m", None, "p", {"max_tokens": 1}) != base
    assert request_key("m", "s", "p2", {"max_tokens": 1}) != base
    assert request_key("m", "s", "p", {"max_tokens": 2}) != base


def test_call_cap_stops_live_calls_but_not_hits(tmp_path: Path) -> None:
    cached, fake = _cached(tmp_path, max_calls=2)
    cached.complete("a")
    cached.complete("b")
    with pytest.raises(CallBudgetExceeded):
        cached.complete("c")
    assert cached.complete("a").text and fake.calls == 2


def test_cache_never_holds_a_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-SECRET-VALUE")
    cached, _ = _cached(tmp_path)
    Judge(cached).compare(PairItem("q", "a", "b c"))
    assert "SECRET-VALUE" not in (tmp_path / "cache.jsonl").read_text()


def test_concurrent_judging_is_deterministic(tmp_path: Path) -> None:
    cached, _ = _cached(tmp_path)
    items = [PairItem(f"q{i}", "w " * (i % 4), "w " * ((i + 1) % 4 + 1)) for i in range(40)]
    seq = [Judge(cached, workers=1).compare(it) for it in items]
    par = Judge(cached, workers=8).compare_many(items)
    assert seq == par
    assert Judge(cached, workers=100).workers == 8


def test_spearman_and_length_bias() -> None:
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert math.isnan(spearman([1, 1, 1], [1, 2, 3]))
    lb = length_bias(["A", "B", "A", "tie", "B"], [5, -3, 2, 1, -7])
    assert lb.longer_wins == 1.0 and lb.rho > 0.8 and lb.n == 5
    anti = length_bias(["B", "A", "B", "A"], [5, -3, 2, -1])
    assert anti.longer_wins == 0.0 and anti.rho < -0.8
    with pytest.raises(ValueError):
        length_bias(["A"], [1.0, 2.0])


def test_pair_item_length_diff_defaults_to_words() -> None:
    assert PairItem("q", "a b c", "d").length_diff == 2.0
    assert PairItem("q", "a b c", "d", length_a=10, length_b=4).length_diff == 6.0


def test_position_flip_rate_counts_only_parsed_pairs() -> None:
    vs = [
        PairVerdict("A", "A", "A"),
        PairVerdict("A", "B", "tie"),
        PairVerdict("A", "tie", "tie"),
        PairVerdict("invalid", "A", "tie"),
    ]
    assert position_flip_rate(vs) == (pytest.approx(2 / 3), 3, 1)


def test_prompt_fingerprint_is_stable() -> None:
    assert prompt_fingerprint() == prompt_fingerprint() and len(prompt_fingerprint()) == 16


# --- agreement statistics -------------------------------------------------------------------


def _toy_items() -> list[ValItem]:
    return [
        ValItem("c1", "A", (("h1", "A"), ("h2", "A")), 5.0),
        ValItem("c2", "A", (("h1", "B"), ("h2", "tie")), -2.0),
        ValItem("c3", "tie", (("h1", "A"),), 1.0),
        ValItem("c4", "B", (("h1", "B"), ("h2", "A")), -4.0),
    ]


def test_agreement_matches_hand_computation() -> None:
    data = AgreementData(_toy_items())
    s = data.statistics(np.ones(4))
    assert s["jh_s1"] == pytest.approx((1 + 0 + 0 + 0.5) / 4)
    assert s["jh_s2"] == pytest.approx((1 + 0 + 0.5) / 3)
    assert s["hh_s1"] == pytest.approx((1 + 0 + 0) / 3)
    assert s["hh_s2"] == pytest.approx((1 + 0) / 2)
    assert s["diff_s1_vs_human"] == pytest.approx((1 + 0 + 0.5) / 3 - (1 + 0 + 0) / 3)
    assert data.counts() == {
        "items": 4,
        "clusters": 4,
        "votes": 7,
        "items_s2": 3,
        "items_hh_s1": 3,
        "items_hh_s2": 2,
    }


def test_same_human_voting_twice_is_not_a_pair() -> None:
    it = ValItem("c", "A", (("h1", "A"), ("h1", "B")), 0.0)
    data = AgreementData([it, ValItem("d", "A", (("h2", "A"),), 1.0)])
    assert math.isnan(data.statistics(np.ones(2))["hh_s1"])


def test_kappa_perfect_and_chance() -> None:
    labels = ["A", "B", "A", "B", "tie", "A", "B", "tie"]
    perfect = [ValItem(f"c{i}", v, ((f"h{i}", v),), 0.0) for i, v in enumerate(labels)]  # type: ignore[arg-type]
    s = AgreementData(perfect).statistics(np.ones(8))
    assert s["jh_kappa_s1"] == pytest.approx(1.0)
    assert s["jh_kappa_s2"] == pytest.approx(1.0)
    # judge says A everywhere: agreement with humans is at chance, kappa 0
    const = [ValItem(f"c{i}", "A", ((f"h{i}", v),), 0.0) for i, v in enumerate(labels)]  # type: ignore[arg-type]
    assert AgreementData(const).statistics(np.ones(8))["jh_kappa_s1"] == pytest.approx(0.0)


def test_second_judge_columns_and_difference() -> None:
    items = [
        ValItem("c1", "A", (("h1", "A"),), 1.0, other="B"),
        ValItem("c2", "B", (("h1", "B"),), -1.0, other="B"),
    ]
    s = AgreementData(items).statistics(np.ones(2))
    assert s["judge_on_other_items_s1"] == 1.0 and s["other_s1"] == 0.5
    assert s["diff_s1_vs_other"] == pytest.approx(0.5)


def test_flip_and_length_statistics() -> None:
    items = [
        ValItem("c1", "A", (("h", "A"),), 5.0, flipped=True, same_slot=True),
        ValItem("c2", "B", (("h", "B"),), -5.0),
        ValItem("c3", "A", (("h", "tie"),), 3.0),
        ValItem("c4", "B", (("h", "A"),), -3.0, both_valid=False),
    ]
    s = AgreementData(items).statistics(np.ones(4))
    assert s["flip_rate"] == pytest.approx(1 / 3)
    assert s["same_slot_rate"] == pytest.approx(1 / 3)
    assert s["len_rho_judge"] > 0.85
    assert s["longer_wins_judge"] == 1.0
    assert s["longer_wins_human"] == pytest.approx(
        2 / 3
    )  # votes A, B, (tie skipped), A on a shorter A: 2 of 3 decided
    assert s["judge_tie_rate"] == 0.0 and s["human_tie_rate"] == 0.25


def test_cluster_bootstrap_resamples_whole_clusters() -> None:
    rng = np.random.default_rng(1)
    items: list[ValItem] = []
    for c in range(30):
        # a cluster is all-agree or all-disagree: clustering must widen the interval
        agree = bool(rng.integers(0, 2))
        for k in range(4):
            items.append(ValItem(f"c{c}", "A", ((f"h{k}", "A" if agree else "B"),), 1.0))
    data = AgreementData(items)
    est = cluster_bootstrap(data.statistics, data.cluster, n_boot=300, seed=0)["jh_s1"]
    assert est.lo <= est.value <= est.hi
    assert (
        est.hi - est.lo > 0.15
    )  # item-level SE would be about 0.045 -> width 0.18; clusters: wider
    again = cluster_bootstrap(data.statistics, data.cluster, n_boot=300, seed=0)["jh_s1"]
    assert again == est
    other = cluster_bootstrap(data.statistics, data.cluster, n_boot=300, seed=1)["jh_s1"]
    assert other != est


def test_empty_items_rejected() -> None:
    with pytest.raises(ValueError):
        AgreementData([])


# --- CLI -----------------------------------------------------------------------------------


def _write_pairs(path: Path) -> None:
    rows = []
    # model "big" always writes more words than "mid", which beats "small"
    for q in range(6):
        for ma, mb, na, nb in (
            ("big", "mid", 9, 5),
            ("mid", "small", 5, 2),
            ("big", "small", 9, 2),
        ):
            rows.append(
                {
                    "id": f"q{q}-{ma}-{mb}",
                    "task": "toy",
                    "cluster_id": f"q{q}",
                    "prompt": f"question {q}",
                    "response_a": " ".join(["w"] * na),
                    "response_b": " ".join(["w"] * nb),
                    "model_a": ma,
                    "model_b": mb,
                }
            )
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_cli_judge_pairwise_feeds_compare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pairs = tmp_path / "pairs.jsonl"
    _write_pairs(pairs)
    fake = FakeModel()
    monkeypatch.setattr(cli, "get_model", lambda spec, **kw: fake)
    out = tmp_path / "out"
    code = cli.main(
        ["judge", "--pairs", str(pairs), "--out", str(out), "--judge", "anthropic:fake-judge"]
    )
    assert code == 0
    text = capsys.readouterr().out
    assert "Position-flip rate 0.0%" in text and "Spearman rho" in text and "Elo" in text
    assert "Self-preference is not controlled" in text
    assert fake.calls == 2 * 18
    rows = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
    assert len(rows) == 36 and all(r["cluster_id"].startswith("q") for r in rows)
    big = [r["score"] for r in rows if r["model"] == "big"]
    assert big == [1.0] * 12 and {r["task"] for r in rows} == {"toy"}
    assert len(read_cache(out / "judge-cache.jsonl")) == 36
    # the existing machinery reads the output, clustered by question
    assert cli.main(["compare", str(out / "results.jsonl"), "--all-pairs"]) == 0
    cmp = capsys.readouterr().out
    assert "big vs mid" in cmp and "clustered SE" in cmp
    # re-running from the cache costs nothing and needs no model
    monkeypatch.setattr(cli, "get_model", lambda spec, **kw: pytest.fail("no backend"))
    assert (
        cli.main(
            [
                "judge",
                "--pairs",
                str(pairs),
                "--out",
                str(out),
                "--cache-only",
                "--judge",
                "anthropic:fake-judge",
            ]
        )
        == 0
    )
    assert "0 live, 36 cache hits" in capsys.readouterr().out


def test_cli_judge_pointwise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pairs = tmp_path / "pairs.jsonl"
    _write_pairs(pairs)
    fake = FakeModel()
    monkeypatch.setattr(cli, "get_model", lambda spec, **kw: fake)
    out = tmp_path / "out"
    code = cli.main(
        [
            "judge",
            "--pairs",
            str(pairs),
            "--mode",
            "pointwise",
            "--out",
            str(out),
            "--judge",
            "anthropic:fake-judge",
        ]
    )
    assert code == 0 and fake.calls == 18  # identical (prompt, response) requests are shared
    rows = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
    assert {r["score"] for r in rows if r["model"] == "small"} == {2.0}
    assert {r["score"] for r in rows if r["model"] == "big"} == {9.0}
    assert "rubric points" in capsys.readouterr().out
    assert cli.main(["compare", str(out / "results.jsonl"), "--a", "big", "--b", "mid"]) == 0


def test_cli_judge_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pairs = tmp_path / "pairs.jsonl"
    _write_pairs(pairs)
    assert cli.main(["judge", "--pairs", str(pairs), "--judge", "oracle"]) == 1
    assert "anthropic:<model id>" in capsys.readouterr().err
    code = cli.main(
        [
            "judge",
            "--pairs",
            str(pairs),
            "--out",
            str(tmp_path / "o"),
            "--cache-only",
            "--judge",
            "anthropic:fake-judge",
        ]
    )
    assert code == 1 and "not in cache" in capsys.readouterr().err
    assert cli.main(["judge", "--pairs", str(tmp_path / "missing.jsonl")]) == 1


@pytest.mark.network
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY unset")
def test_live_judge_one_pair(tmp_path: Path) -> None:
    pytest.importorskip("anthropic")
    cached = CachedCompleter(AnthropicModel(), tmp_path / "live.jsonl", max_calls=2)
    v = Judge(cached).compare(
        PairItem("What is 2+2?", "4", "The moon is made of cheese and the answer is 5.")
    )
    assert v.first in {"A", "B", "tie"}
    rec = read_cache(tmp_path / "live.jsonl")
    assert rec and rec[0]["model_returned"].startswith("claude-sonnet-5-5")
