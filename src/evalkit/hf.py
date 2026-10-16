"""Hugging Face transformers adapter (requires extra ``[hf]``).

Selected with ``hf:<model_id>`` or ``hf:<model_id>@<revision>``.

How each task type is answered
------------------------------
* ``generation`` / ``reasoning`` / ``code``: the prompt is wrapped in the model's chat template
  with a short task-type instruction appended, then decoded greedily (no sampling, no repetition
  penalty).
  ``Prediction.logprobs`` are the *raw* (pre-processor) log-probabilities of the generated
  tokens, ``token_nll`` is their negated sum, and ``confidence`` is the geometric-mean token
  probability ``exp(mean(logprobs))``. That confidence is a heuristic derived from real
  log-probs; it is not a calibrated probability (the ECE the leaderboard reports measures how
  far off it is). ``reasoning`` is free generation with a longer token budget and no adapter
  instruction: the task prompt asks for step-by-step work and fixes the answer format.
* ``multiple_choice`` / ``classification``: no free-form generation. Every option in the label
  set is scored as the assistant's reply (sum of token log-probs, rank classification) and the
  argmax is returned, so the output is always a member of the label set, exactly like the
  built-in mock models. ``confidence`` is the softmax over the option scores (probability
  renormalised over the label set), not the probability mass the model gives that option in
  the full vocabulary.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .models import _CHOICE_TASKS, Prediction

GENERATION_INSTRUCTION = "Reply with only the final answer, with no explanation."
CODE_INSTRUCTION = (
    "Complete the function above. Reply with only the complete Python function "
    "in a single ```python code block."
)
CHOICE_INSTRUCTION = "Reply with exactly one of the following options and nothing else: "

DEFAULT_MAX_NEW_TOKENS = {"generation": 48, "reasoning": 256, "code": 384}


def build_user_message(prompt: str, task_type: str, choices: Sequence[str] | None = None) -> str:
    """Task prompt plus the adapter's one-line instruction for this task type."""
    if task_type in _CHOICE_TASKS and choices:
        return f"{prompt}\n\n{CHOICE_INSTRUCTION}{', '.join(choices)}"
    if task_type == "code":
        return f"{prompt}\n\n{CODE_INSTRUCTION}"
    if task_type == "reasoning":
        return prompt  # the task prompt itself asks for step-by-step work and the answer format
    return f"{prompt}\n\n{GENERATION_INSTRUCTION}"


def pick_device() -> str:
    """mps when available (Apple silicon), otherwise cpu."""
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


def parse_descriptor(descriptor: str) -> tuple[str, str | None]:
    """``'Qwen/Qwen2.5-0.5B-Instruct@abc123'`` -> ``('Qwen/Qwen2.5-0.5B-Instruct', 'abc123')``."""
    model_id, sep, revision = descriptor.partition("@")
    if not model_id:
        raise ValueError(
            "hf: model descriptor needs a model id, e.g. hf:Qwen/Qwen2.5-0.5B-Instruct"
        )
    return model_id, (revision if sep and revision else None)


def softmax(scores: Sequence[float]) -> list[float]:
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


class HFModel:
    """Chat-template + greedy-decoding adapter around a transformers causal LM."""

    def __init__(
        self,
        model_id: str,
        revision: str | None = None,
        device: str | None = None,
        max_new_tokens: dict[str, int] | None = None,
        name: str | None = None,
        batch_size: int = 1,
        *,
        tokenizer: Any = None,
        model: Any = None,
    ) -> None:
        """Load ``model_id``. ``tokenizer``/``model`` may be injected (used by offline tests)."""
        self.model_id = model_id
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")
        # How many free-generation prompts the runner may decode together (``predict_batch``).
        self.batch_size = batch_size
        self.max_new_tokens = {**DEFAULT_MAX_NEW_TOKENS, **(max_new_tokens or {})}
        self._lock = threading.Lock()  # one model instance; torch/MPS calls are serialised

        self.revision: str | None = None  # commit hash of the snapshot actually loaded
        if tokenizer is None or model is None:
            try:
                import torch
                from huggingface_hub import hf_hub_download
                from transformers import AutoModelForCausalLM, AutoTokenizer
            except ImportError as exc:
                raise ImportError(
                    "torch/transformers not found. Install evalkit with `evalkit[hf]`."
                ) from exc
            self.device = device or pick_device()
            dtype = torch.float32 if self.device == "cpu" else torch.bfloat16
            tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
            model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, dtype=dtype)
            model.to(self.device)
            model.eval()
            # <cache>/snapshots/<commit hash>/config.json: the directory name is the commit.
            self.revision = Path(
                hf_hub_download(model_id, "config.json", revision=revision, local_files_only=True)
            ).parent.name
        else:
            self.device = device or "cpu"

        self.tokenizer = tokenizer
        self.model = model
        short = f"@{revision[:8]}" if revision else ""
        self.name = name or f"hf:{model_id}{short}"

    # -- prompt construction -------------------------------------------------------------

    def render_chat(self, prompt: str, task_type: str, choices: Sequence[str] | None) -> str:
        """Chat-template text ending at the start of the assistant turn."""
        messages = [{"role": "user", "content": build_user_message(prompt, task_type, choices)}]
        return str(
            self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        )

    def _encode(self, text: str) -> list[int]:
        # The chat template already contains the special tokens as text.
        return [int(t) for t in self.tokenizer.encode(text, add_special_tokens=False)]

    def _eos_ids(self) -> set[int]:
        ids: set[int] = set()
        gen_cfg = getattr(self.model, "generation_config", None)
        for source in (gen_cfg, self.tokenizer):
            eos = getattr(source, "eos_token_id", None)
            if isinstance(eos, int):
                ids.add(eos)
            elif isinstance(eos, list):
                ids.update(int(e) for e in eos)
        return ids

    # -- low-level model calls (the only places that touch torch) ---------------------------

    def _generate_ids(
        self, prompt_ids: list[int], max_new_tokens: int
    ) -> tuple[list[int], list[float]]:
        """Greedy decode. Returns new token ids and the raw-logit log-prob of each."""
        import torch

        input_ids = torch.tensor([prompt_ids], device=self.device)
        with self._lock, torch.inference_mode():
            out = self.model.generate(
                input_ids=input_ids,
                attention_mask=torch.ones_like(input_ids),
                do_sample=False,
                max_new_tokens=max_new_tokens,
                temperature=None,
                top_p=None,
                top_k=None,
                repetition_penalty=1.0,
                return_dict_in_generate=True,
                output_logits=True,
                pad_token_id=getattr(self.tokenizer, "pad_token_id", None),
            )
            new_ids = [int(t) for t in out.sequences[0, len(prompt_ids) :].tolist()]
            logps = [
                float(torch.log_softmax(logits[0].float(), dim=-1)[tok].item())
                for logits, tok in zip(out.logits, new_ids, strict=True)
            ]
        return new_ids, logps

    def _generate_ids_batch(
        self, prompts_ids: list[list[int]], max_new_tokens: int
    ) -> list[tuple[list[int], list[float]]]:
        """Greedy decode a left-padded batch. Per prompt: new token ids (up to and including
        the first EOS) and the raw-logit log-prob of each."""
        import torch

        pad = getattr(self.tokenizer, "pad_token_id", None)
        pad = int(pad) if pad is not None else 0
        eos = self._eos_ids()
        width = max(len(p) for p in prompts_ids)
        ids = torch.tensor([[pad] * (width - len(p)) + p for p in prompts_ids], device=self.device)
        mask = torch.tensor(
            [[0] * (width - len(p)) + [1] * len(p) for p in prompts_ids], device=self.device
        )
        with self._lock, torch.inference_mode():
            out = self.model.generate(
                input_ids=ids,
                attention_mask=mask,
                do_sample=False,
                max_new_tokens=max_new_tokens,
                temperature=None,
                top_p=None,
                top_k=None,
                repetition_penalty=1.0,
                return_dict_in_generate=True,
                output_logits=True,
                pad_token_id=pad,
            )
            new = out.sequences[:, width:]
            step_lps = torch.stack(
                [
                    torch.log_softmax(logits.float(), dim=-1).gather(1, new[:, i : i + 1])[:, 0]
                    for i, logits in enumerate(out.logits)
                ],
                dim=1,
            )
            new_rows = new.tolist()
            lp_rows = step_lps.tolist()
        results: list[tuple[list[int], list[float]]] = []
        for toks, lps in zip(new_rows, lp_rows, strict=True):
            cut = next((i + 1 for i, t in enumerate(toks) if t in eos), len(toks))
            results.append(([int(t) for t in toks[:cut]], [float(v) for v in lps[:cut]]))
        return results

    def _continuation_logprobs(self, prefix_ids: list[int], cont_ids: list[int]) -> list[float]:
        """Log-prob of each token of ``cont_ids`` given ``prefix_ids`` (one forward pass)."""
        import torch

        ids = torch.tensor([prefix_ids + cont_ids], device=self.device)
        with self._lock, torch.inference_mode():
            logits = self.model(input_ids=ids).logits[0].float()
            logp = torch.log_softmax(logits[len(prefix_ids) - 1 : -1], dim=-1)
            target = ids[0, len(prefix_ids) :]
            return [float(v) for v in logp.gather(1, target[:, None])[:, 0].tolist()]

    # -- Model protocol ---------------------------------------------------------------------

    def _finish_generation(self, new_ids: list[int], logps: list[float]) -> tuple[str, list[float]]:
        eos = self._eos_ids()
        while new_ids and new_ids[-1] in eos:  # drop the stop token(s) from text and log-probs
            new_ids.pop()
            logps.pop()
        text = str(self.tokenizer.decode(new_ids, skip_special_tokens=True)).strip()
        return text, logps

    def _generate(self, prompt: str, task_type: str) -> tuple[str, list[float]]:
        prompt_ids = self._encode(self.render_chat(prompt, task_type, None))
        limit = self.max_new_tokens.get(task_type, self.max_new_tokens["generation"])
        new_ids, logps = self._generate_ids(prompt_ids, limit)
        return self._finish_generation(new_ids, logps)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self._generate(prompt, str(kwargs.get("task_type", "generation")))[0]

    def logprobs(self, prompt: str, candidate: str) -> list[float]:
        prefix = self._encode(self.render_chat(prompt, "generation", None))
        cont = self._encode(candidate)
        return self._continuation_logprobs(prefix, cont) if cont else []

    def _score_choices(
        self, prompt: str, task_type: str, choices: Sequence[str]
    ) -> list[list[float]]:
        prefix = self._encode(self.render_chat(prompt, task_type, choices))
        return [self._continuation_logprobs(prefix, self._encode(ch)) for ch in choices]

    def choose(self, prompt: str, choices: Sequence[str], **kwargs: Any) -> str:
        if not choices:
            return ""
        scores = [sum(lp) for lp in self._score_choices(prompt, "multiple_choice", choices)]
        return choices[max(range(len(choices)), key=scores.__getitem__)]

    def predict(
        self,
        prompt: str,
        task_type: str,
        choices: Sequence[str] | None = None,
        example: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Prediction:
        if task_type in _CHOICE_TASKS and choices:
            per_choice = self._score_choices(prompt, task_type, choices)
            totals = [sum(lp) for lp in per_choice]
            best = max(range(len(choices)), key=totals.__getitem__)
            lps = per_choice[best]
            return Prediction(
                text=choices[best],
                confidence=float(softmax(totals)[best]),
                logprobs=lps,
                token_nll=float(-sum(lps)),
                n_tokens=max(1, len(lps)),
            )
        return self._generation_prediction(*self._generate(prompt, task_type))

    @staticmethod
    def _generation_prediction(text: str, lps: list[float]) -> Prediction:
        confidence = math.exp(sum(lps) / len(lps)) if lps else 0.0
        return Prediction(
            text=text,
            confidence=float(confidence),
            logprobs=lps,
            token_nll=float(-sum(lps)),
            n_tokens=max(1, len(lps)),
        )

    def predict_batch(self, prompts: Sequence[str], task_type: str) -> list[Prediction]:
        """Free-generation ``predict`` for several prompts decoded together (left-padded).

        Same prompts, greedy decoding and token budget as ``predict``; only the batch
        composition differs. Batched bf16 kernels are not bit-identical to batch size 1, so a
        greedy continuation can differ from the unbatched one (and between batch sizes).
        """
        limit = self.max_new_tokens.get(task_type, self.max_new_tokens["generation"])
        prompts_ids = [self._encode(self.render_chat(p, task_type, None)) for p in prompts]
        preds: list[Prediction] = []
        for new_ids, logps in self._generate_ids_batch(prompts_ids, limit):
            text, lps = self._finish_generation(new_ids, logps)
            preds.append(self._generation_prediction(text, lps))
        return preds
