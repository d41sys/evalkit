"""ezcross bridge: the committed floor fixture and cost/latency Pareto marking."""

from __future__ import annotations

from pathlib import Path

from evalkit.cli import main
from evalkit.runner import EvalRecord, generate_leaderboard

FLOOR = Path(__file__).parent.parent / "data" / "ezc" / "floor-results.jsonl"


def test_floor_fixture_all_pairs(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["compare", str(FLOOR), "--all-pairs"]) == 0
    rows = {
        ln.split("|")[1].strip(): ln for ln in capsys.readouterr().out.splitlines() if " vs " in ln
    }
    assert "| 20 |" in rows["local-scripted vs local-donothing"]
    assert "| 20 / 0 / 0 |" in rows["local-scripted vs local-donothing"]
    assert rows["local-scripted vs local-donothing"].rstrip().endswith("| resolved |")
    assert rows["local-scripted vs local-refuseall"].rstrip().endswith("| resolved |")
    assert "unresolved (needs n≈157)" in rows["local-donothing vs local-refuseall"]


def _rec(model: str, ex: str, score: float, cost: float | None, lat: float | None) -> EvalRecord:
    return EvalRecord(
        task="t",
        model=model,
        example_id=ex,
        score=score,
        metrics={},
        prediction="",
        targets=[],
        confidence=0.5,
        correct=int(score),
        cost_usd=cost,
        latency_s=lat,
    )


def test_pareto_marking_and_columns() -> None:
    # (mean score, mean cost): A (1.0, 3), B (0.5, 1), C ties B, D (0.5, 2) is dominated by B and C
    spec = {"A": (1.0, 3.0), "B": (0.5, 1.0), "C": (0.5, 1.0), "D": (0.5, 2.0)}
    recs = [
        _rec(m, f"e{i}", 1.0 if (s == 1.0 or i == 0) else 0.0, c, 2.0)
        for m, (s, c) in spec.items()
        for i in range(2)
    ]
    # a model without cost is neither marked nor allowed to dominate
    recs += [_rec("E", f"e{i}", 1.0, None, None) for i in range(2)]
    board = generate_leaderboard(recs)
    by = {m.model_name: m for m in board.models}
    assert {k for k, m in by.items() if m.pareto} == {"A", "B", "C"}
    assert by["B"].mean_cost == 1.0 and by["E"].mean_cost is None
    md = board.to_markdown()
    assert "Mean cost (USD)" in md and "Mean latency (s)" in md and "Pareto" in md


def test_no_cost_columns_without_fields() -> None:
    md = generate_leaderboard([_rec("A", "e0", 1.0, None, None)]).to_markdown()
    assert "Pareto" not in md and "Mean cost" not in md


def test_cost_roundtrip() -> None:
    r = _rec("A", "e0", 1.0, 0.25, 3.5)
    back = EvalRecord.from_dict(r.to_dict())
    assert (back.cost_usd, back.latency_s) == (0.25, 3.5)
    assert "cost_usd" not in _rec("A", "e0", 1.0, None, None).to_dict()


def test_partially_priced_model_is_unpriced() -> None:
    # F has cost on one of two rows: its mean would come from a different subset, so no cost
    recs = [_rec("F", "e0", 1.0, 0.01, None), _rec("F", "e1", 1.0, None, None)]
    recs += [_rec("G", f"e{i}", 0.5, 1.0, None) for i in range(2)]
    by = {m.model_name: m for m in generate_leaderboard(recs).models}
    assert by["F"].mean_cost is None and not by["F"].pareto
    assert by["G"].pareto
