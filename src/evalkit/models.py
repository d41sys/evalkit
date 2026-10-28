from __future__ import annotations

import os
import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class Prediction:
    text: str
    confidence: float = 0.5
    logprobs: list[float] = field(default_factory=list)
    token_nll: float = 0.0
    # Real tokenizer token count when known; otherwise token_count falls back to whitespace words.
    n_tokens: int | None = None

    @property
    def token_count(self) -> int:
        if self.n_tokens is not None:
            return self.n_tokens
        return max(1, len(self.text.split()))


DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"


@dataclass(frozen=True)
class Completion:
    """One chat completion: the text, the model id the API reported and its token usage."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int


@runtime_checkable
class Completer(Protocol):
    """What the LLM judge needs from a model: one system+user completion with usage.

    ``temperature=None`` sends no sampling parameter: claude-sonnet-5-5 rejects ``temperature``
    ("Extra inputs are not permitted", 400), so its decoding is the API default.
    """

    model_id: str

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion: ...


@runtime_checkable
class Model(Protocol):
    name: str

    def generate(self, prompt: str, **kwargs: Any) -> str: ...

    def logprobs(self, prompt: str, candidate: str) -> list[float]: ...

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str: ...

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction: ...


@runtime_checkable
class BatchModel(Model, Protocol):
    """A model that can decode several free-generation prompts at once (``batch_size`` > 1)."""

    batch_size: int

    def predict_batch(self, prompts: Sequence[str], task_type: str) -> list[Prediction]: ...


def _get_target_from_example(example: dict[str, Any] | None) -> str:
    if not example:
        return ""
    if "canonical_solution" in example:
        return str(example["canonical_solution"]).strip()
    if example.get("targets"):
        return str(example["targets"][0]).strip()
    if "target" in example:
        return str(example["target"]).strip()
    if "answer" in example:
        return str(example["answer"]).strip()
    return ""


_CHOICE_TASKS = frozenset({"multiple_choice", "classification"})


class OracleModel:
    """Perfect model that always outputs ground truth when available."""

    def __init__(self, name: str = "oracle") -> None:
        self.name = name

    def generate(self, prompt: str, **kwargs: Any) -> str:
        example = kwargs.get("example")
        ans = _get_target_from_example(example)
        return ans if ans else "correct"

    def logprobs(self, prompt: str, candidate: str) -> list[float]:
        tokens = max(1, len(candidate.split()))
        return [-0.02] * tokens

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str:
        example = kwargs.get("example")
        ans = _get_target_from_example(example)
        if ans:
            # Check if ans is choice letter like 'A', 'B'
            if ans in choices:
                return ans
            # Or match against text of choices
            for ch in choices:
                if ans.lower() in ch.lower() or ch.lower() in ans.lower():
                    return ch
        return choices[0] if choices else ""

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction:
        if task_type in _CHOICE_TASKS and choices:
            text = self.choose(prompt, choices, example=example, **kwargs)
        else:
            text = self.generate(prompt, example=example, **kwargs)

        lps = self.logprobs(prompt, text)
        confidence = 0.99
        nll = float(-sum(lps))
        return Prediction(text=text, confidence=confidence, logprobs=lps, token_nll=nll)


class NoisyModel:
    """Outputs ground truth with probability (1 - noise_rate); otherwise corrupted output."""

    def __init__(self, noise_rate: float = 0.3, seed: int = 42, name: str | None = None) -> None:
        self.noise_rate = float(noise_rate)
        self.seed = seed
        self.name = name or f"noisy:{self.noise_rate}"

    def _rng(self, prompt: str, sample: int = 0) -> random.Random:
        # Per-prompt RNG: results are independent of thread scheduling order. Sample 0 keeps
        # the original seed string; later samples of the same prompt draw independently.
        tag = f"{sample}:" if sample else ""
        return random.Random(f"{self.seed}:{tag}{prompt}")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        example = kwargs.get("example")
        if self._rng(prompt, int(kwargs.get("sample", 0))).random() >= self.noise_rate:
            ans = _get_target_from_example(example)
            if ans:
                return ans
        if example and "canonical_solution" in example:
            return "    return None"
        return "I am not certain"

    def logprobs(self, prompt: str, candidate: str) -> list[float]:
        tokens = max(1, len(candidate.split()))
        return [-0.4] * tokens

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str:
        rng = self._rng(prompt, int(kwargs.get("sample", 0)))
        example = kwargs.get("example")
        target = _get_target_from_example(example)
        correct_choice = choices[0] if choices else ""
        if target:
            for ch in choices:
                if target.lower() in ch.lower() or ch.lower() in target.lower():
                    correct_choice = ch
                    break

        if rng.random() >= self.noise_rate and correct_choice:
            return correct_choice

        wrong_choices = [c for c in choices if c != correct_choice]
        if wrong_choices:
            return rng.choice(wrong_choices)
        return rng.choice(choices) if choices else ""

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction:
        if task_type in _CHOICE_TASKS and choices:
            text = self.choose(prompt, choices, example=example, **kwargs)
        else:
            text = self.generate(prompt, example=example, **kwargs)

        lps = self.logprobs(prompt, text)
        confidence = float(
            self._rng(prompt + "\x00conf", int(kwargs.get("sample", 0))).uniform(0.65, 0.85)
        )
        nll = float(-sum(lps))
        return Prediction(text=text, confidence=confidence, logprobs=lps, token_nll=nll)


class RandomModel:
    """Model that outputs random guesses."""

    def __init__(self, seed: int = 42, name: str = "random") -> None:
        self.seed = seed
        self.name = name

    def _rng(self, prompt: str, sample: int = 0) -> random.Random:
        tag = f"{sample}:" if sample else ""
        return random.Random(f"{self.seed}:{tag}{prompt}")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        example = kwargs.get("example")
        if example and "canonical_solution" in example:
            return "    pass"
        return str(self._rng(prompt, int(kwargs.get("sample", 0))).randint(0, 100))

    def logprobs(self, prompt: str, candidate: str) -> list[float]:
        tokens = max(1, len(candidate.split()))
        return [-2.0] * tokens

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str:
        return self._rng(prompt, int(kwargs.get("sample", 0))).choice(choices) if choices else ""

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction:
        if task_type in _CHOICE_TASKS and choices:
            text = self.choose(prompt, choices, example=example, **kwargs)
        else:
            text = self.generate(prompt, example=example, **kwargs)

        lps = self.logprobs(prompt, text)
        confidence = float(
            self._rng(prompt + "\x00conf", int(kwargs.get("sample", 0))).uniform(0.2, 0.45)
        )
        nll = float(-sum(lps))
        return Prediction(text=text, confidence=confidence, logprobs=lps, token_nll=nll)


class AnthropicModel:
    """Real LLM model calling Anthropic API (requires extra [llm]).

    The API returns no token logprobs: ``logprobs`` is a constant proxy, not a measurement.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_ANTHROPIC_MODEL,
        api_key: str | None = None,
        name: str | None = None,
        max_retries: int = 8,
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic package not found. Install evalkit with `evalkit[llm]`."
            ) from exc

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is missing and no api_key was provided."
            )

        # The SDK retries 408/409/429/5xx (529 included) with exponential backoff.
        self.client = anthropic.Anthropic(api_key=key, max_retries=max_retries)
        self.model_id = model_id
        self.name = name or f"anthropic:{model_id}"

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion:
        extra: dict[str, Any] = {} if temperature is None else {"temperature": temperature}
        if system is None:
            resp = self.client.messages.create(
                model=self.model_id,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                extra_body=extra,
            )
        else:
            resp = self.client.messages.create(
                model=self.model_id,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                extra_body=extra,
            )
        text = "".join(getattr(block, "text", "") for block in resp.content)
        return Completion(
            text=text,
            model=str(resp.model),
            input_tokens=int(resp.usage.input_tokens),
            output_tokens=int(resp.usage.output_tokens),
        )

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self.complete(
            prompt,
            system=kwargs.get("system"),
            max_tokens=kwargs.get("max_tokens", 256),
            temperature=kwargs.get("temperature"),
        ).text

    def logprobs(self, prompt: str, candidate: str) -> list[float]:
        # Anthropic API does not expose token logprobs; return proxy estimate
        tokens = max(1, len(candidate.split()))
        return [-0.5] * tokens

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str:
        choice_list = ", ".join(choices)
        formatted_prompt = (
            f"{prompt}\n\nChoices: {choice_list}\n"
            "Respond with only the selected choice letter or text."
        )
        ans = self.generate(formatted_prompt, **kwargs).strip()
        for ch in choices:
            if ans.lower() == ch.lower() or ans.startswith(ch):
                return ch
        return ans

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction:
        if task_type in _CHOICE_TASKS and choices:
            text = self.choose(prompt, choices, example=example, **kwargs)
        else:
            text = self.generate(prompt, example=example, **kwargs)

        lps = self.logprobs(prompt, text)
        confidence = 0.8
        nll = float(-sum(lps))
        return Prediction(text=text, confidence=confidence, logprobs=lps, token_nll=nll)


def get_model(spec_str: str, **kwargs: Any) -> Model:
    """Parse model descriptor string like 'oracle', 'noisy:0.3', 'random', 'anthropic:model_id'."""
    raw = spec_str.strip()
    if raw == "oracle":
        return OracleModel()
    if raw.startswith("noisy"):
        parts = raw.split(":")
        rate = float(parts[1]) if len(parts) > 1 else 0.3
        return NoisyModel(noise_rate=rate, **kwargs)
    if raw == "random":
        return RandomModel(**kwargs)
    if raw.startswith("anthropic"):
        parts = raw.split(":", 1)
        model_id = parts[1] if len(parts) > 1 else DEFAULT_ANTHROPIC_MODEL
        return AnthropicModel(model_id=model_id, **kwargs)
    if raw.startswith("hf:"):
        from .hf import HFModel, parse_descriptor

        model_id, revision = parse_descriptor(raw[len("hf:") :])
        return HFModel(model_id, revision=revision, **kwargs)
    raise ValueError(f"Unknown model descriptor: {spec_str}")
