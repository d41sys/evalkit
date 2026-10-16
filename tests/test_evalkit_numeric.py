from __future__ import annotations

from pathlib import Path

import pytest

from evalkit.cli import find_task_specs
from evalkit.hf import build_user_message
from evalkit.metrics.classical import extract_final_number, numeric_match, score_classical
from evalkit.models import OracleModel, RandomModel
from evalkit.runner import run

# (model output, expected extracted number). Shapes seen in step-by-step answers.
EXTRACTION_FIXTURE: list[tuple[str, float | None]] = [
    ("18", 18.0),
    ("The answer is 18", 18.0),
    ("The answer is 18.", 18.0),
    ("The answer is: $18", 18.0),
    ("Janet makes $18 dollars every day.", 18.0),
    ("She earns 1,234 dollars", 1234.0),
    ("Total: 1,234,567.50 USD", 1234567.5),
    ("18.0", 18.0),
    ("-5", -5.0),
    ("The temperature dropped to -5 degrees", -5.0),
    ("= -12.5 meters", -12.5),
    ("**18**", 18.0),
    ("\\boxed{42}", 42.0),
    ("#### 7", 7.0),
    ("25%", 25.0),
    ("16 - 3 - 4 = 9 eggs, 9 * 2 = 18", 18.0),
    ("Step 1: 3 apples. Step 2: 5 more.", 5.0),
    # the number after the marker wins over numbers elsewhere
    ("The answer is 18 (check: 9 * 2)", 18.0),
    # the last marker wins over an earlier one
    ("The answer is 3. Wait, recount. The answer is 4.", 4.0),
    ("5-3 = 2", 2.0),
    ("no digits here", None),
    ("", None),
    ("The answer is unknown", None),
]


@pytest.mark.parametrize(("text", "expected"), EXTRACTION_FIXTURE)
def test_extract_final_number(text: str, expected: float | None) -> None:
    assert extract_final_number(text) == expected


def test_numeric_match() -> None:
    assert numeric_match("So she makes $18 a day. The answer is 18.", ["18"]) == 1.0
    assert numeric_match("18.0", "18") == 1.0
    assert numeric_match("The answer is 2,125", ["2125"]) == 1.0
    assert numeric_match("The answer is 19", ["18"]) == 0.0
    assert numeric_match("no idea", ["18"]) == 0.0
    assert numeric_match("18", []) == 0.0
    # a second target that matches
    assert numeric_match("18", ["17", "18"]) == 1.0
    assert score_classical("numeric_match", "answer: 18", ["18"]) == 1.0


def test_reasoning_prompt_is_not_wrapped_with_final_answer_instruction() -> None:
    assert build_user_message("Solve it.", "reasoning") == "Solve it."


def test_bundled_gsm8k_task_loads_and_scores(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent
    specs = find_task_specs(repo / "tasks_hard")
    assert [s.name for s in specs] == ["gsm8k"]
    spec = specs[0]
    assert spec.type == "reasoning"
    rows = spec.load_dataset()
    assert len(rows) >= 100
    assert all(r["target"].lstrip("-").isdigit() for r in rows)
    assert "The answer is" in spec.render_prompt(rows[0])

    summary = run(specs, [OracleModel(), RandomModel()], tmp_path, max_workers=2)
    means = {m.model_name: m.macro_mean for m in summary.leaderboard.models}
    assert means["oracle"] == 1.0
    assert means["random"] < 0.1
