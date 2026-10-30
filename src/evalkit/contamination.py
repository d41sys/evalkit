"""GSM-Symbolic-style contamination probe: program-built number variants of GSM8K items.

A *template* is derived from a GSM8K item and its own annotated reference solution
(``<<expr=result>>`` calculator annotations): every number in the question becomes a *slot*, every
annotation a *step* whose operands are slots (``s3``), earlier step results (``r1``) or constants
(``2``), and the template is kept only if replaying the steps on the original slot values
reproduces the annotation of every step and the GSM8K gold exactly, and every operand is
unambiguous. A *variant* resamples the non-frozen slots under constraints and replays the steps to
recompute the answer. No language model writes or checks a gold.

Everything here is exact (:class:`fractions.Fraction`) and deterministic under a seed. Scoring
helpers at the end take model replies from a cache and compare variants with the original.
"""

from __future__ import annotations

import ast
import functools
import math
import random
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

import numpy as np

from .aggregate import holm_bonferroni, minimum_detectable_effect, randomization_test_p
from .clustered import cluster_bootstrap_ci
from .metrics.classical import numeric_match
from .metrics.helm_compat import helm_final_number_exact_match

# --------------------------------------------------------------------------- rejection reasons

REASONS = (
    "no_annotations",
    "unsupported_question_format",
    "unsupported_expression",
    "annotation_mismatch",
    "final_mismatch",
    "ambiguous_operand",
    "unmapped_constant",
    "no_perturbable_slot",
    "no_feasible_variants",
)


class TemplateReject(Exception):
    """A GSM8K item that cannot be turned into a verified template; ``reason`` is in REASONS."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


# --------------------------------------------------------------------------- question slots

_UNITS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
]
NUMBER_WORDS: dict[str, int] = {w: i for i, w in enumerate(_UNITS)}
NUMBER_WORDS.update(
    {
        w: 10 * i
        for i, w in enumerate(
            ["thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"], 3
        )
    }
)
_WORD_OF = {v: k for k, v in NUMBER_WORDS.items()}
_TENS = "thirty|forty|fifty|sixty|seventy|eighty|ninety|twenty"
_NUM_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?")
_WORD_RE = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r")\b", re.IGNORECASE)
_BAD_FORMAT = (
    (re.compile(r"\d\s?[-\u2013]\s?\d"), "numeric range or hyphenated digits"),
    (re.compile(r"(?<!\d)\.\d"), "decimal without leading digit"),
    (
        re.compile(r"\b(" + _TENS + r")[- ](one|two|three|four|five|six|seven|eight|nine)\b", re.I),
        "compound number word",
    ),
    (re.compile(r"\b(hundred|thousand|million|billion|trillion)s?\b", re.I), "scale word"),
)
_FRACTION_AFTER = re.compile(
    r"\s*[-\u2013]?\s*(thirds?|fourths?|fifths?|sixths?|sevenths?|eighths?|ninths?|tenths?"
    r"|quarters?|halves|half)\b",
    re.I,
)
_ATTACHED_AFTER = re.compile(r"\s?(am|pm|a\.m|p\.m|st|nd|rd|th|o'?clock)\b|:\d|/\d", re.I)
_BOUNDED_AFTER = re.compile(
    r"\s+(days?|nights?)\s+(a|per|each|every)\s+week\b"
    r"|\s+weeks?\s+(a|per|each|every|in a)\s+year\b"
    r"|\s+months?\s+(a|per|each|every|in a)\s+year\b"
    r"|\s+hours?\s+(a|per|each|every)\s+day\b",
    re.I,
)
_PERCENT_AFTER = re.compile(r"\s*(%|percent\b|per cent\b)", re.I)

# Implicit constants a solution may use without the number being in the question, with the word
# that licenses each. A question slot whose value equals such a constant while the question holds
# the word is frozen (the solution's operand could be the constant), and an operand that matches
# no slot is accepted as a constant only with its licence (or the value 1).
_CUES: dict[Fraction, re.Pattern[str]] = {
    Fraction(2): re.compile(
        r"\b(twice|doubl\w*|half|halves|halved|pairs?|couple|both|twins?)\b|\bthe two\b", re.I
    ),
    Fraction(3): re.compile(r"\b(tripl\w*|thrice|thirds|(a|one|1)[- ]third|yards?|feet)\b", re.I),
    Fraction(4): re.compile(
        r"\b(quadrupl\w*|quarters?|fourths|(a|one|1)[- ]fourth|gallons?|quarts?)\b", re.I
    ),
    Fraction(5): re.compile(r"\b(nickels?|fifths?|weekdays?)\b", re.I),
    Fraction(7): re.compile(r"\b(week|weeks|weekly|weekends?)\b", re.I),
    Fraction(8): re.compile(r"\b(pints?|eighths?|ounces?|oz)\b", re.I),
    Fraction(10): re.compile(r"\b(dimes?|tenths?|decades?)\b", re.I),
    Fraction(12): re.compile(
        r"\b(dozens?|months?|monthly|years?|annual\w*|inch|inches|foot|feet|ft)\b", re.I
    ),
    Fraction(16): re.compile(r"\b(pounds?|lbs?|ounces?|oz|gallons?)\b", re.I),
    Fraction(24): re.compile(r"\b(day|days|daily|hours?)\b", re.I),
    Fraction(25): re.compile(r"\b(quarters?)\b", re.I),
    Fraction(30): re.compile(r"\b(months?|monthly|days?)\b", re.I),
    Fraction(31): re.compile(
        r"\b(months?|monthly|january|march|may|july|august|october|december)\b", re.I
    ),
    Fraction(52): re.compile(r"\b(weeks?|years?|annual\w*|cards?)\b", re.I),
    Fraction(60): re.compile(r"\b(hours?|minutes?|mins?|hrs?|seconds?)\b", re.I),
    Fraction(100): re.compile(r"%|\b(percent\w*|cents?)\b", re.I),
    Fraction(365): re.compile(r"\b(years?|annual\w*)\b", re.I),
    Fraction(1000): re.compile(r"\b(kilo\w*|km|kg|thousand|liters?|litres?|ml|mm|grams?)\b", re.I),
    Fraction(1, 2): re.compile(r"\b(half|halves|halved)\b", re.I),
    Fraction(1, 4): re.compile(r"\b(quarters?|fourths|(a|one|1)[- ]fourth)\b", re.I),
    Fraction(3, 4): re.compile(r"\b(quarters?|fourths|three[- ]quarters)\b", re.I),
    Fraction(1, 3): re.compile(r"\b(thirds|(a|one|1)[- ]third)\b", re.I),
}


# A slot of at most this value that two or more steps use is frozen: one of its uses may be an
# implicit constant (a person, a rectangle's two sides) that happens to equal it.
SMALL_REUSED = 12


@dataclass(frozen=True)
class Slot:
    """One number of the question: its span, original surface form and parsed value."""

    index: int
    start: int
    end: int
    text: str
    value: Fraction
    kind: str  # "int", "dec" or "word"
    decimals: int
    commas: bool
    capital: bool
    percent: bool
    frozen: bool
    freeze_reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "kind": self.kind,
            "percent": self.percent,
            "frozen": self.frozen,
            "freeze_reason": self.freeze_reason,
        }


def _slot_value(text: str, kind: str) -> tuple[Fraction, int, bool]:
    if kind == "word":
        return Fraction(NUMBER_WORDS[text.lower()]), 0, False
    commas = "," in text
    clean = text.replace(",", "")
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    return Fraction(clean), decimals, commas


def find_slots(question: str) -> list[Slot]:
    """All numbers of ``question`` in text order, with the freeze decisions made.

    Raises :class:`TemplateReject` for formats the machinery does not handle (ranges, compound
    or scale number words, decimals without a leading digit).
    """
    for pattern, why in _BAD_FORMAT:
        if pattern.search(question):
            raise TemplateReject("unsupported_question_format", why)
    raw: list[tuple[int, int, str, str]] = []
    for m in _NUM_RE.finditer(question):
        raw.append((m.start(), m.end(), m.group(), "dec" if m.group(2) else "int"))
    for m in _WORD_RE.finditer(question):
        raw.append((m.start(), m.end(), m.group(), "word"))
    raw.sort()
    parsed = [(s, e, t, k, *_slot_value(t, k)) for s, e, t, k in raw]
    value_count: dict[Fraction, int] = {}
    for p in parsed:
        value_count[p[4]] = value_count.get(p[4], 0) + 1
    out: list[Slot] = []
    for i, (s, e, text, kind, value, decimals, commas) in enumerate(parsed):
        after, before = question[e:], question[:s]
        reason = ""
        if value <= 1:
            reason = "value 0 or 1"
        elif value_count[value] > 1:
            reason = "value occurs twice in the question"
        elif any(rx.search(question) for v, rx in _CUES.items() if v == value):
            reason = "value is an implicit constant licensed by a word in the question"
        elif _FRACTION_AFTER.match(after) or before.endswith("/"):
            reason = "part of a fraction"
        elif _ATTACHED_AFTER.match(after) or re.search(r"\d:$", before) or before.endswith("#"):
            reason = "time, ordinal, fraction or label"
        elif _BOUNDED_AFTER.match(after):
            reason = "count bounded by the calendar (days per week, weeks per year, ...)"
        elif kind == "int" and not commas and 1900 <= value <= 2100 and not before.endswith("$"):
            reason = "year-like"
        out.append(
            Slot(
                index=i,
                start=s,
                end=e,
                text=text,
                value=value,
                kind=kind,
                decimals=decimals,
                commas=commas,
                capital=text[0].isupper(),
                percent=bool(_PERCENT_AFTER.match(after)),
                frozen=bool(reason),
                freeze_reason=reason,
            )
        )
    return out


# --------------------------------------------------------------------------- exact arithmetic


@functools.lru_cache(maxsize=4096)
def _parse(expr: str) -> ast.expr:
    return ast.parse(expr, mode="eval").body


def _num(value: int | float) -> Fraction:
    return Fraction(value) if isinstance(value, int) else Fraction(repr(value))


def _eval(node: ast.expr, env: Mapping[str, Fraction]) -> Fraction:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return _num(node.value)
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _eval(node.operand, env)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        a, b = _eval(node.left, env), _eval(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        return a / b
    raise ValueError(f"unsupported syntax: {ast.dump(node)}")


def evaluate(expr: str, env: Mapping[str, Fraction]) -> Fraction:
    """Exact value of a symbolic expression (``+ - * /``, parentheses, numbers, names)."""
    return _eval(_parse(expr), env)


@dataclass(frozen=True)
class Template:
    """A GSM8K item as a program: question text with slots plus symbolic computation steps."""

    id: str
    question: str
    gold: int
    slots: tuple[Slot, ...]
    steps: tuple[str, ...]  # symbolic: s<i> slot, r<j> earlier step result, numeric constants

    @property
    def original_values(self) -> tuple[Fraction, ...]:
        return tuple(s.value for s in self.slots)

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "gold": self.gold,
            "slots": [s.to_json() for s in self.slots],
            "steps": list(self.steps),
        }

    @staticmethod
    def from_json(row: Mapping[str, Any]) -> Template:
        """Rebuild from :meth:`to_json`; slot values are re-parsed from the question text."""
        question = str(row["question"])
        slots: list[Slot] = []
        for d in row["slots"]:
            text = question[d["start"] : d["end"]]
            if text != d["text"]:
                raise ValueError(f"slot text mismatch in {row['id']}")
            value, decimals, commas = _slot_value(text, d["kind"])
            slots.append(
                Slot(
                    index=d["index"],
                    start=d["start"],
                    end=d["end"],
                    text=text,
                    value=value,
                    kind=d["kind"],
                    decimals=decimals,
                    commas=commas,
                    capital=text[0].isupper(),
                    percent=bool(d["percent"]),
                    frozen=bool(d["frozen"]),
                    freeze_reason=str(d["freeze_reason"]),
                )
            )
        return Template(
            id=str(row["id"]),
            question=question,
            gold=int(row["gold"]),
            slots=tuple(slots),
            steps=tuple(str(s) for s in row["steps"]),
        )


def solve(template: Template, values: Sequence[Fraction] | None = None) -> list[Fraction]:
    """All step results when the slots take ``values`` (default: the original numbers).

    The last entry is the answer. Raises ``ZeroDivisionError`` on a division by zero.
    """
    vals = template.original_values if values is None else tuple(values)
    if len(vals) != len(template.slots):
        raise ValueError("one value per slot is required")
    env: dict[str, Fraction] = {f"s{i}": v for i, v in enumerate(vals)}
    results: list[Fraction] = []
    for j, expr in enumerate(template.steps):
        r = evaluate(expr, env)
        env[f"r{j}"] = r
        results.append(r)
    return results


# --------------------------------------------------------------------------- template building

_ANNOT_RE = re.compile(r"<<([^<>=]*)=([^<>]*)>>")
_EXPR_OK = re.compile(r"^[0-9.+\-*/() ]+$")
_LITERAL_RE = re.compile(r"\d+(?:\.\d+)?|\.\d+")


def _decimals(x: Fraction) -> int:
    d = 0
    while (x * 10**d).denominator != 1:
        d += 1
        if d > 12:
            return 99
    return d


def _licensed(value: Fraction, question: str) -> bool:
    if value == 1:
        return True
    rx = _CUES.get(value)
    return rx is not None and rx.search(question) is not None


def build_template(source_id: str, question: str, answer: str) -> Template:
    """Template from a GSM8K ``question`` and its annotated ``answer``, or :class:`TemplateReject`.

    Checks, in order: slots parse; annotations exist and use ``+ - * /`` only; every operand maps
    to exactly one source (a question slot, an earlier result, a percent slot divided by 100) or
    is a licensed constant; replay on the original numbers reproduces every annotated result and
    the GSM8K gold; at least one slot can be perturbed.
    """
    gold_text = answer.split("####")[-1].strip().replace(",", "")
    if not re.fullmatch(r"\d+", gold_text) or int(gold_text) <= 0:
        raise TemplateReject("final_mismatch", f"gold {gold_text!r} is not a positive integer")
    gold = int(gold_text)
    slots = find_slots(question)
    notes = _ANNOT_RE.findall(answer.split("####")[0])
    if not notes:
        raise TemplateReject("no_annotations")
    # Freezing a slot can change which operands are ambiguous, so trace again until stable.
    while True:
        steps, results, invariant = _trace(question, slots, notes)
        uses = Counter(int(i) for step in steps for i in re.findall(r"s(\d+)", step))
        slots_new = list(slots)
        for s in slots:
            reason = ""
            if uses[s.index] == 0:
                reason = "not used by the reference solution"
            elif s.value <= SMALL_REUSED and uses[s.index] >= 2:
                reason = "small number used twice: one use may be an implicit constant"
            if reason and not s.frozen:
                slots_new[s.index] = replace(s, frozen=True, freeze_reason=reason)
        if slots_new == slots:
            break
        slots = slots_new
    if results[-1] != gold:
        raise TemplateReject("final_mismatch", f"last step {results[-1]} != gold {gold}")
    if all(s.frozen for s in slots) or invariant[-1]:
        raise TemplateReject("no_perturbable_slot")
    template = Template(source_id, question, gold, tuple(slots), tuple(steps))
    if _perturbable(template) == []:
        raise TemplateReject("no_perturbable_slot", "no alternative value for any slot")
    return template


def _may_be_derived(
    lit: Fraction, slots: list[Slot], results: list[Fraction], invariant: list[bool]
) -> bool:
    """True if ``lit`` is the sum, difference, product or quotient of two available numbers, one
    of which a perturbation changes: the solution may have computed it in its head."""
    pool = [(s.value, s.frozen) for s in slots] + list(zip(results, invariant, strict=True))
    for i, (a, fa) in enumerate(pool):
        for b, fb in pool[i + 1 :]:
            if fa and fb:
                continue
            if (
                lit in (a + b, a * b, abs(a - b))
                or (b != 0 and a / b == lit)
                or (a != 0 and b / a == lit)
            ):
                return True
    return False


def _trace(
    question: str, slots: list[Slot], notes: list[tuple[str, str]]
) -> tuple[list[str], list[Fraction], list[bool]]:
    """Symbolic steps, their original values and whether each is unaffected by any perturbation."""
    results: list[Fraction] = []
    invariant: list[bool] = []
    steps: list[str] = []
    for expr, res_text in notes:
        expr = expr.strip()
        if not _EXPR_OK.match(expr) or "**" in expr or "//" in expr:
            raise TemplateReject("unsupported_expression", expr)
        if not re.search(r"[+\-*/]", expr):
            raise TemplateReject("unsupported_expression", f"step without an operation: {expr}")
        try:
            recorded = Fraction(res_text.strip().replace(",", ""))
        except (ValueError, ZeroDivisionError):
            raise TemplateReject("unsupported_expression", f"result {res_text!r}") from None
        pieces: list[str] = []
        used_inv: list[bool] = []
        last = 0
        for m in _LITERAL_RE.finditer(expr):
            pieces.append(expr[last : m.start()])
            last = m.end()
            lit = Fraction(m.group())
            licensed = _licensed(lit, question)
            cands: list[tuple[str, bool]] = []
            for s in slots:
                if s.value == lit:
                    cands.append((f"s{s.index}", s.frozen))
                elif s.percent and s.value / 100 == lit:
                    cands.append((f"(s{s.index}/100)", s.frozen))
            for j, r in enumerate(results):
                if r == lit:
                    cands.append((f"r{j}", invariant[j]))
            if licensed and any(not inv for _, inv in cands):
                # the literal may be the implicit constant that equals a computed value by chance
                raise TemplateReject("ambiguous_operand", f"{m.group()} in {expr}")
            if not cands:
                if not licensed:
                    raise TemplateReject("unmapped_constant", f"{m.group()} in {expr}")
                if lit >= 7 and _may_be_derived(lit, slots, results, invariant):
                    raise TemplateReject("ambiguous_operand", f"constant {m.group()} in {expr}")
                pieces.append(m.group())
                used_inv.append(True)
            elif len(cands) == 1:
                pieces.append(cands[0][0])
                used_inv.append(cands[0][1])
            elif all(inv for _, inv in cands):
                pieces.append(m.group())  # every candidate is fixed: the literal is a constant
                used_inv.append(True)
            else:
                raise TemplateReject("ambiguous_operand", f"{m.group()} in {expr}")
        pieces.append(expr[last:])
        sym = "".join(pieces)
        try:
            env = {f"s{s.index}": s.value for s in slots}
            env.update({f"r{j}": r for j, r in enumerate(results)})
            value = evaluate(sym, env)
        except (SyntaxError, ValueError, ZeroDivisionError):
            raise TemplateReject("unsupported_expression", expr) from None
        if value != recorded:
            raise TemplateReject("annotation_mismatch", f"{expr} = {value} != {recorded}")
        raw_percent = [
            s for s in slots if s.percent and re.search(rf"s{s.index}(?!\d)(?!/100)", sym)
        ]
        if raw_percent and "/100" not in sym.replace(" ", ""):
            raise TemplateReject("ambiguous_operand", f"percent used as an amount in {expr}")
        steps.append(sym)
        results.append(value)
        invariant.append(all(used_inv))
    return steps, results, invariant


# --------------------------------------------------------------------------- perturbation

_GRIDS = tuple(Fraction(g) for g in ("10", "5", "1", "0.5", "0.25", "0.1", "0.05", "0.01"))


def _magnitude(x: Fraction) -> int:
    """Integer-digit count; 0 for values below 1."""
    return len(str(math.floor(x))) if x >= 1 else 0


def slot_grid(slot: Slot) -> tuple[Fraction, int, int] | None:
    """(step g, lo, hi): candidate values are ``k * g`` for ``lo <= k <= hi``, k*g != original.

    New values keep the integer-digit count and the number of decimals, stay within -50%/+50%
    of the original (symmetric, so numbers do not drift upward), are at least 2 when the
    original is, and keep the original's roundness (a multiple of 10, 5, 0.5, ... stays one).
    The coarsest grid that leaves 3 or more alternatives is used. ``None`` for a frozen slot or
    one without any alternative.
    """
    if slot.frozen:
        return None
    v = slot.value
    unit = Fraction(1, 10**slot.decimals)
    lo_v, hi_v = v / 2, v * 3 / 2
    mag = _magnitude(v)
    if mag >= 1:
        lo_v, hi_v = max(lo_v, Fraction(10 ** (mag - 1))), min(hi_v, Fraction(10**mag - 1))
    else:
        hi_v = min(hi_v, 1 - unit)
    if v >= 2:
        lo_v = max(lo_v, Fraction(2))
    elif v > 1:
        lo_v = max(lo_v, 1 + unit)
    if slot.percent:
        hi_v = min(hi_v, Fraction(99))
    best: tuple[Fraction, int, int] | None = None
    for g in _GRIDS:
        if (g / unit).denominator != 1 or v % g != 0 or g > v / 2:
            continue
        lo, hi = math.ceil(lo_v / g), math.floor(hi_v / g)
        count = hi - lo + 1 - (1 if lo <= v / g <= hi else 0)
        if count >= 1:
            best = (g, lo, hi)
        if count >= 3:
            return best
    if best is None:
        g = unit
        lo, hi = math.ceil(lo_v / g), math.floor(hi_v / g)
        if hi - lo + 1 - (1 if lo <= v / g <= hi else 0) >= 1:
            return (g, lo, hi)
    return best


def _perturbable(template: Template) -> list[int]:
    return [s.index for s in template.slots if slot_grid(s) is not None]


def _draw(template: Template, rng: random.Random) -> tuple[Fraction, ...]:
    out: list[Fraction] = []
    for s in template.slots:
        grid = slot_grid(s)
        if grid is None:
            out.append(s.value)
            continue
        g, lo, hi = grid
        while True:
            k = rng.randint(lo, hi)
            if k * g != s.value:
                break
        out.append(k * g)
    return tuple(out)


def check_variant(template: Template, values: Sequence[Fraction]) -> list[str]:
    """Violations of the variant constraints (empty list = valid).

    Per slot: unchanged if frozen; else same integer-digit count, same decimals, within -50%/+50%.
    The strict order of every pair of numbers of the problem, question numbers and step results
    alike, is kept when it is strict in the original (a goal stays above the amount raised so
    far, a remainder stays below the whole).
    Per step result ``r`` (original) vs ``r'``: same sign; integer stays integer, otherwise at
    most ``max(2, decimals of r)`` decimals; ``1/4 <= r'/r <= 4``. Final: a positive integer
    different from the original gold.
    """
    bad: list[str] = []
    for s, x in zip(template.slots, values, strict=True):
        if s.frozen:
            if x != s.value:
                bad.append(f"frozen slot s{s.index} changed")
            continue
        if _magnitude(x) != _magnitude(s.value) or _decimals(x) > s.decimals:
            bad.append(f"slot s{s.index} changes digit count or decimals")
        if not (s.value / 2 <= x <= s.value * 3 / 2):
            bad.append(f"slot s{s.index} outside the +-50% range")
    old_vals = template.original_values
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if (values[i] > values[j]) - (values[i] < values[j]) != (old_vals[i] > old_vals[j]) - (
                old_vals[i] < old_vals[j]
            ):
                bad.append(f"order of s{i} and s{j} changed")
    if bad:
        return bad
    try:
        old, new = solve(template), solve(template, values)
    except ZeroDivisionError:
        return [*bad, "division by zero"]
    all_old, all_new = [*old_vals, *old], [*values, *new]
    for i in range(len(all_old)):
        for j in range(max(i + 1, len(old_vals)), len(all_old)):
            if all_old[i] != all_old[j] and (all_old[i] < all_old[j]) != (all_new[i] < all_new[j]):
                bad.append("order of two numbers of the problem changed")
    if bad:
        return bad
    for j, (r0, r1) in enumerate(zip(old, new, strict=True)):
        if (r0 > 0) != (r1 > 0) or (r0 < 0) != (r1 < 0):
            bad.append(f"step {j} changes sign")
        if r0.denominator == 1:
            if r1.denominator != 1:
                bad.append(f"step {j} is not an integer")
        elif _decimals(r1) > max(2, _decimals(r0)):
            bad.append(f"step {j} has too many decimals")
        if r0 != 0 and not (Fraction(1, 4) <= r1 / r0 <= 4):
            bad.append(f"step {j} outside the 4x magnitude band")
    final = new[-1]
    if final.denominator != 1 or final <= 0:
        bad.append("answer is not a positive integer")
    if final == template.gold:
        bad.append("answer equals the original gold")
    return bad


@dataclass(frozen=True)
class Variant:
    values: tuple[Fraction, ...]
    gold: int
    question: str


def render_slot(slot: Slot, x: Fraction) -> str:
    """Surface form of ``x`` for ``slot`` (word, integer with optional commas, fixed decimals)."""
    if slot.kind == "word":
        if x.denominator == 1 and int(x) in _WORD_OF:
            w = _WORD_OF[int(x)]
            return w.capitalize() if slot.capital else w
        return str(int(x))
    scaled = x * 10**slot.decimals
    if scaled.denominator != 1:
        raise ValueError(f"{x} is not representable with {slot.decimals} decimals")
    digits = str(int(scaled)).rjust(slot.decimals + 1, "0")
    whole, frac = digits[: len(digits) - slot.decimals], digits[len(digits) - slot.decimals :]
    if slot.commas:
        whole = f"{int(whole):,}"
    return f"{whole}.{frac}" if slot.decimals else whole


def render(template: Template, values: Sequence[Fraction]) -> str:
    """The question with every slot rewritten to ``values``."""
    text = template.question
    for s, x in reversed(list(zip(template.slots, values, strict=True))):
        shown = s.text if x == s.value else render_slot(s, x)
        text = text[: s.start] + shown + text[s.end :]
    return text


def make_variants(template: Template, n: int = 2, max_tries: int = 10000) -> list[Variant]:
    """``n`` valid variants with pairwise different numbers and different answers.

    Variant ``k`` (1-based) is drawn with ``random.Random(f"{template.id}|variant|{k}")``, so the
    same template always yields the same variants. Raises ``no_feasible_variants`` if no valid
    draw is found within ``max_tries``.
    """
    out: list[Variant] = []
    seen_vals: set[tuple[Fraction, ...]] = {template.original_values}
    seen_gold = {template.gold}
    for k in range(1, n + 1):
        rng = random.Random(f"{template.id}|variant|{k}")
        for _ in range(max_tries):
            vals = _draw(template, rng)
            if vals in seen_vals or check_variant(template, vals):
                continue
            gold = int(solve(template, vals)[-1])
            if gold in seen_gold:
                continue
            seen_vals.add(vals)
            seen_gold.add(gold)
            out.append(Variant(vals, gold, render(template, vals)))
            break
        else:
            raise TemplateReject("no_feasible_variants", f"variant {k}")
    return out


def check_template(template: Template) -> list[str]:
    """Solver check on the original numbers: replay reproduces the gold and the question."""
    bad: list[str] = []
    try:
        if solve(template)[-1] != template.gold:
            bad.append("replay on the original numbers differs from the gold")
    except ZeroDivisionError:
        bad.append("division by zero on the original numbers")
    if render(template, template.original_values) != template.question:
        bad.append("rendering the original numbers does not give the original question")
    return bad


def trace_text(template: Template) -> str:
    """Human-readable computation (for review): steps with slot values substituted."""
    names = {f"s{s.index}": f"{s.text}{'*' if s.frozen else ''}" for s in template.slots}
    lines = []
    for j, step in enumerate(template.steps):
        shown = re.sub(r"s\d+", lambda m: names[m.group()], step)
        lines.append(f"r{j} = {shown}")
    return "; ".join(lines)


# --------------------------------------------------------------------------- prompt


PROMPT_VERSION = "gsm-cot-v1"
PROMPT = (
    "Solve the following math problem. Think step by step, then write the final answer on the "
    "last line in exactly this format: Answer: <number>\n"
    "Use digits only in the final line (no units, no commas, no words).\n\n"
    "Problem: {question}"
)


def build_prompt(question: str) -> str:
    return PROMPT.format(question=question)


# --------------------------------------------------------------------------- scoring


def score_reply(reply: str, gold: int, mode: str = "numeric") -> float:
    """1.0 if the reply's final number is the gold: evalkit ``numeric_match`` or HELM mode."""
    if mode == "numeric":
        return numeric_match(reply, str(gold))
    if mode == "helm":
        return helm_final_number_exact_match(str(gold), reply)
    raise ValueError(f"unknown scoring mode {mode!r}")


def exact_mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p from the discordant counts (binomial sign test, p = 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (1 << n)
    return min(1.0, 2 * tail)


@dataclass(frozen=True)
class DropResult:
    """Paired accuracy drop of one model: original minus the mean of the perturbed variants."""

    n: int
    acc_original: float
    acc_variants: tuple[float, ...]
    drop: float
    ci95: tuple[float, float]
    ci975: tuple[float, float]
    p_signflip: float
    sd_diff: float
    mde_80: float
    mde_80_alpha025: float
    orig_right_pert_wrong: tuple[int, ...]  # per variant
    orig_wrong_pert_right: tuple[int, ...]
    mcnemar_p_first: float
    drop_first: float
    ci95_first: tuple[float, float]


def drop_analysis(
    original: Sequence[float], variants: Sequence[Sequence[float]], resamples: int = 10000
) -> DropResult:
    """All pre-registered per-model statistics from 0/1 scores; item = source problem.

    ``original[i]`` is the score on source ``i``; ``variants[k][i]`` the score on its variant
    ``k``. The primary difference is ``original[i] - mean_k variants[k][i]``; its CI is a
    percentile cluster bootstrap over sources (one cluster per source), the p-value a sign-flip
    randomisation test; McNemar (exact) compares the original with variant 1 only.
    """
    o = np.asarray(original, dtype=np.float64)
    v = np.asarray(variants, dtype=np.float64)
    n = int(o.size)
    codes = np.arange(n)
    d = o - v.mean(axis=0)
    mean, lo, hi = cluster_bootstrap_ci(d, codes, num_resamples=resamples, seed=0)
    _, lo2, hi2 = cluster_bootstrap_ci(
        d, codes, num_resamples=resamples, confidence_level=0.975, seed=0
    )
    d1 = o - v[0]
    m1, l1, h1 = cluster_bootstrap_ci(d1, codes, num_resamples=resamples, seed=0)
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    return DropResult(
        n=n,
        acc_original=float(o.mean()),
        acc_variants=tuple(float(x) for x in v.mean(axis=1)),
        drop=mean,
        ci95=(lo, hi),
        ci975=(lo2, hi2),
        p_signflip=randomization_test_p(d, seed=0),
        sd_diff=sd,
        mde_80=minimum_detectable_effect(sd, n, alpha=0.05, power=0.8),
        mde_80_alpha025=minimum_detectable_effect(sd, n, alpha=0.025, power=0.8),
        orig_right_pert_wrong=tuple(int(((o == 1) & (row == 0)).sum()) for row in v),
        orig_wrong_pert_right=tuple(int(((o == 0) & (row == 1)).sum()) for row in v),
        mcnemar_p_first=exact_mcnemar_p(
            int(((o == 1) & (v[0] == 0)).sum()), int(((o == 0) & (v[0] == 1)).sum())
        ),
        drop_first=m1,
        ci95_first=(l1, h1),
    )


def verdict(result: DropResult, holm_p: float) -> str:
    """Pre-registered reading of one model's drop (``holm_p``: Holm-adjusted sign-flip p)."""
    if result.drop > 0 and holm_p < 0.05 and result.ci975[0] > 0:
        return "significant drop"
    if result.drop > 0 and (holm_p < 0.05 or result.ci975[0] > 0):
        return "borderline (the Holm test and the 97.5% CI disagree)"
    if result.drop < 0:
        if holm_p < 0.05 and result.ci975[1] < 0:
            return "significant negative drop (perturbed accuracy higher)"
        return "negative drop (perturbed accuracy higher), not significant"
    return "no detectable drop"


def drop_difference(
    original_a: Sequence[float],
    variants_a: Sequence[Sequence[float]],
    original_b: Sequence[float],
    variants_b: Sequence[Sequence[float]],
    resamples: int = 10000,
) -> tuple[float, float, float]:
    """Mean and 95% cluster-bootstrap CI of (drop of A) minus (drop of B), source = cluster."""
    da = np.asarray(original_a, dtype=np.float64) - np.asarray(variants_a, dtype=np.float64).mean(
        axis=0
    )
    db = np.asarray(original_b, dtype=np.float64) - np.asarray(variants_b, dtype=np.float64).mean(
        axis=0
    )
    return cluster_bootstrap_ci(da - db, np.arange(da.size), num_resamples=resamples, seed=0)


def holm_adjust(results: Mapping[str, DropResult]) -> dict[str, float]:
    """Holm-adjusted sign-flip p-values over the models."""
    names = list(results)
    adj = holm_bonferroni([results[m].p_signflip for m in names])
    return dict(zip(names, adj, strict=True))


def neutrality(originals: Sequence[int], perturbed: Sequence[Sequence[int]]) -> dict[str, float]:
    """Difficulty-neutrality of the golds: digit counts and magnitude, original vs perturbed."""
    o = np.asarray(originals, dtype=np.float64)[:, None]
    p = np.asarray(perturbed, dtype=np.float64)

    def digits(a: np.ndarray) -> np.ndarray:
        return np.floor(np.log10(a)) + 1

    od, pd = digits(o), digits(p)
    return {
        "n_sources": float(o.shape[0]),
        "mean_digits_original": float(od.mean()),
        "mean_digits_perturbed": float(pd.mean()),
        "share_same_digit_count": float((pd == od).mean()),
        "share_perturbed_more_digits": float((pd > od).mean()),
        "share_perturbed_fewer_digits": float((pd < od).mean()),
        "median_gold_original": float(np.median(o)),
        "median_gold_perturbed": float(np.median(p)),
        "mean_log10_ratio": float(np.log10(p / o).mean()),
        "share_perturbed_larger": float((p > o).mean()),
    }


def as_dict(obj: Any) -> Any:
    """JSON-friendly view of dataclasses and tuples (Fractions as strings)."""
    if isinstance(obj, Fraction):
        return str(obj)
    if hasattr(obj, "__dataclass_fields__"):
        return {k: as_dict(getattr(obj, k)) for k in obj.__dataclass_fields__}
    if isinstance(obj, (list, tuple)):
        return [as_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: as_dict(x) for k, x in obj.items()}
    return obj
