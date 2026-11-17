"""``evalkit monitor``: per-period pass rate, Wilson interval, alert on the latest period."""

import json
from pathlib import Path

from evalkit.cli import main
from evalkit.monitor import period_rates, render_monitor


def _write(path: Path, weeks: dict[str, tuple[int, int]]) -> Path:
    rows = [
        {"task": w, "model": "agent", "example_id": f"s{i}", "score": float(i < k)}
        for w, (k, n) in weeks.items()
        for i in range(n)
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_rates_sorted_by_period_and_alert_uses_latest_lower_bound(tmp_path: Path) -> None:
    f = _write(tmp_path / "r.jsonl", {"2026-W48": (30, 50), "2026-W47": (49, 50)})
    rates = period_rates(f)
    got = [(r.period, r.passed, r.n) for r in rates]
    assert got == [("2026-W47", 49, 50), ("2026-W48", 30, 50)]
    assert rates[1].lo < 0.6 < rates[1].hi
    _, alert = render_monitor(rates, threshold=0.8)
    assert alert  # W48: 30/50, lower bound about 0.46
    _, alert = render_monitor(rates[:1], threshold=0.8)
    assert not alert  # W47: 49/50, lower bound about 0.89


def test_cli_exit_code_signals_alert(tmp_path: Path, capsys) -> None:
    f = _write(tmp_path / "r.jsonl", {"2026-W47": (49, 50), "2026-W48": (30, 50)})
    assert main(["monitor", str(f), "--threshold", "0.8"]) == 3
    assert "ALERT: 2026-W48" in capsys.readouterr().out
    assert main(["monitor", str(f), "--threshold", "0.3"]) == 0
    assert main(["monitor", str(f), "--threshold", "0.3", "--model", "other"]) == 1
