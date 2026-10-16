"""Tests for the Hugging Face adapter.

The offline tests use a fake tokenizer and override the two torch-touching methods, so they
run without torch/transformers installed. The real-model test is marked ``slow``.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from evalkit.hf import (
    CHOICE_INSTRUCTION,
    CODE_INSTRUCTION,
    GENERATION_INSTRUCTION,
    HFModel,
    build_user_message,
    parse_descriptor,
    softmax,
)
from evalkit.models import get_model

EOS = 0


class FakeTokenizer:
    """Char-level tokenizer; id 0 is EOS, other ids are ord(c) + 1."""

    eos_token_id = EOS
    pad_token_id = EOS

    def apply_chat_template(
        self, messages: list[dict[str, str]], tokenize: bool, add_generation_prompt: bool
    ) -> str:
        assert tokenize is False
        assert add_generation_prompt is True
        body = "".join(f"<{m['role']}>{m['content']}</s>" for m in messages)
        return body + "<assistant>"

    def encode(self, text: str, add_special_tokens: bool = True) -> list[int]:
        assert add_special_tokens is False
        return [ord(c) + 1 for c in text]

    def decode(self, ids: list[int], skip_special_tokens: bool = True) -> str:
        return "".join(chr(i - 1) for i in ids if i != EOS)


class FakeLM:
    config: Any = None
    generation_config: Any = None


class ScriptedHF(HFModel):
    """HFModel whose low-level calls return scripted values and record their inputs."""

    def __init__(
        self, reply: str = "", per_char_lp: float = -0.1, scores: dict[str, float] | None = None
    ):
        super().__init__("fake/model", tokenizer=FakeTokenizer(), model=FakeLM())
        self.reply = reply
        self.per_char_lp = per_char_lp
        self.scores = scores or {}
        self.seen_prefixes: list[str] = []
        self.seen_limits: list[int] = []

    def _generate_ids(
        self, prompt_ids: list[int], max_new_tokens: int
    ) -> tuple[list[int], list[float]]:
        self.seen_prefixes.append(self.tokenizer.decode(prompt_ids))
        self.seen_limits.append(max_new_tokens)
        ids = [*self.tokenizer.encode(self.reply, add_special_tokens=False), EOS]
        return ids, [self.per_char_lp] * len(ids)

    def _continuation_logprobs(self, prefix_ids: list[int], cont_ids: list[int]) -> list[float]:
        self.seen_prefixes.append(self.tokenizer.decode(prefix_ids))
        text = self.tokenizer.decode(cont_ids)
        total = self.scores.get(text, -5.0)
        return [total / len(cont_ids)] * len(cont_ids)


def test_user_message_per_task_type() -> None:
    assert build_user_message("Q?", "generation").endswith(GENERATION_INSTRUCTION)
    assert build_user_message("def f():", "code").endswith(CODE_INSTRUCTION)
    msg = build_user_message("Sentiment?", "classification", ["negative", "positive"])
    assert msg.endswith(f"{CHOICE_INSTRUCTION}negative, positive")
    # Choice tasks without a label set fall back to free generation.
    assert build_user_message("Q?", "multiple_choice", None).endswith(GENERATION_INSTRUCTION)


def test_parse_descriptor_and_names() -> None:
    assert parse_descriptor("Qwen/Qwen2.5-0.5B-Instruct") == ("Qwen/Qwen2.5-0.5B-Instruct", None)
    assert parse_descriptor("org/m@abcdef1234567890") == ("org/m", "abcdef1234567890")
    with pytest.raises(ValueError):
        parse_descriptor("@abc")
    assert ScriptedHF().name == "hf:fake/model"


def test_get_model_hf_without_extra_raises_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name in ("torch", "transformers"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match=r"evalkit\[hf\]"):
        get_model("hf:org/model")


def test_generation_uses_chat_template_strips_eos_and_reports_logprobs() -> None:
    m = ScriptedHF(reply="  42\n", per_char_lp=-0.5)
    pred = m.predict("Question: 15 + 27?\nAnswer:", "generation")
    assert pred.text == "42"  # whitespace stripped, EOS dropped
    # Prompt reached the model through the chat template with the instruction appended.
    assert m.seen_prefixes[0] == (
        f"<user>Question: 15 + 27?\nAnswer:\n\n{GENERATION_INSTRUCTION}</s><assistant>"
    )
    # EOS log-prob is dropped together with the EOS token: 5 reply chars remain.
    assert len(pred.logprobs) == 5
    assert pred.token_nll == pytest.approx(2.5)
    assert pred.token_count == 5
    assert pred.confidence == pytest.approx(math.exp(-0.5))
    assert m.seen_limits == [48]


def test_code_task_gets_longer_budget_and_keeps_fence_for_extraction() -> None:
    reply = "```python\ndef add(a, b):\n    return a + b\n```"
    m = ScriptedHF(reply=reply)
    pred = m.predict("def add(a, b):\n", "code")
    assert pred.text == reply  # run_code_exec extracts the block; the adapter does not
    assert m.seen_limits == [384]
    assert CODE_INSTRUCTION in m.seen_prefixes[0]


def test_choice_task_returns_member_of_label_set_with_softmax_confidence() -> None:
    m = ScriptedHF(scores={"negative": -4.0, "positive": -0.5})
    labels = ["negative", "positive"]
    pred = m.predict("Text: great\nSentiment:", "classification", labels)
    assert pred.text == "positive"
    assert pred.text in labels
    expected = softmax([-4.0, -0.5])[1]
    assert pred.confidence == pytest.approx(expected)
    assert pred.token_nll == pytest.approx(0.5)
    # Both options were scored after the same chat prefix that lists the options.
    assert len(m.seen_prefixes) == 2
    assert all(
        p.endswith(f"{CHOICE_INSTRUCTION}negative, positive</s><assistant>")
        for p in m.seen_prefixes
    )
    assert m.seen_limits == []  # no free-form generation happened


def test_multiple_choice_choose_picks_argmax() -> None:
    m = ScriptedHF(scores={"London": -3.0, "Paris": -0.2, "Berlin": -6.0})
    assert m.choose("Capital of France?", ["London", "Paris", "Berlin"]) == "Paris"
    assert m.choose("x", []) == ""


def test_logprobs_scores_candidate_after_generation_prompt() -> None:
    m = ScriptedHF(scores={"42": -1.0})
    lps = m.logprobs("Q", "42")
    assert lps == [-0.5, -0.5]
    assert m.logprobs("Q", "") == []


def test_softmax_normalises() -> None:
    p = softmax([0.0, 0.0, math.log(2.0)])
    assert sum(p) == pytest.approx(1.0)
    assert p[2] == pytest.approx(0.5)


@pytest.mark.slow
def test_real_model_end_to_end() -> None:  # pragma: no cover - needs torch + downloaded weights
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    m = get_model("hf:Qwen/Qwen2.5-0.5B-Instruct")
    pred = m.predict(
        "Classify the sentiment of the following text as positive or negative.\n\n"
        "Text: Terrible customer service and the device broke within two days.\nSentiment:",
        "classification",
        ["negative", "positive"],
    )
    assert pred.text in {"negative", "positive"}
    assert 0.5 <= pred.confidence <= 1.0
    assert pred.logprobs and all(lp <= 0.0 for lp in pred.logprobs)
