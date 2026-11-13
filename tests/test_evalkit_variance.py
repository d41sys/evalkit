from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from evalkit.cli import main
from evalkit.variance import (
    Observation,
    VarianceComponents,
    load_observations,
    precision_table,
    variance_components,
    variant_means,
)

TRUE = {"item": 0.04, "variant": 0.02, "trial": 0.03}


def _synthetic(n: int, v: int, k: int, seed: int = 0, drop: float = 0.0) -> list[Observation]:
    rng = np.random.default_rng(seed)
    a = rng.normal(0, math.sqrt(TRUE["item"]), n)
    b = rng.normal(0, math.sqrt(TRUE["variant"]), (n, v))
    obs = []
    for i in range(n):
        for j in range(v):
            for _ in range(k):
                if drop and rng.random() < drop:
                    continue
                y = 0.5 + a[i] + b[i, j] + rng.normal(0, math.sqrt(TRUE["trial"]))
                obs.append((("t", str(i)), f"v{j}", float(y)))
    return obs


def _assert_recovers(vc) -> None:
    for name, true in TRUE.items():
        assert getattr(vc, name) == pytest.approx(true, rel=0.10), name


def test_balanced_known_answer():
    # N=2 items, V=2 variants, K=2 trials; hand-computed mean squares:
    # MSE=2, MSV=16, MSA=50, k1=k2=2, k3=4 -> trial 2, variant 7, item (50-2-14)/4 = 8.5
    cells = {
        ("a", "v1"): [1, 3],
        ("a", "v2"): [5, 7],
        ("b", "v1"): [6, 8],
        ("b", "v2"): [10, 12],
    }
    obs = [(("t", i), v, float(y)) for (i, v), ys in cells.items() for y in ys]
    vc = variance_components(obs)
    assert (vc.item, vc.variant, vc.trial) == pytest.approx((8.5, 7.0, 2.0))
    assert vc.within == pytest.approx(9.0)
    assert variant_means(obs) == pytest.approx({"v1": 4.5, "v2": 8.5})


def test_recovers_components_balanced():
    vc = variance_components(_synthetic(2000, 5, 4))
    _assert_recovers(vc)


def test_recovers_components_unbalanced():
    # 30% of observations missing at random: unequal trials per cell and cells per item
    vc = variance_components(_synthetic(2000, 5, 4, seed=1, drop=0.3))
    _assert_recovers(vc)


def test_trials_only_has_no_variant_component():
    obs = [(k, "", y) for k, _, y in _synthetic(2000, 1, 5, seed=2)]
    vc = variance_components(obs)
    assert math.isnan(vc.variant)
    assert vc.item == pytest.approx(TRUE["item"] + TRUE["variant"], rel=0.10)
    assert vc.trial == pytest.approx(TRUE["trial"], rel=0.10)


def test_variants_without_trials_report_within_only():
    obs = _synthetic(2000, 4, 1, seed=3)
    vc = variance_components(obs)
    assert math.isnan(vc.trial) and math.isnan(vc.variant)
    assert vc.within == pytest.approx(TRUE["variant"] + TRUE["trial"], rel=0.10)
    assert vc.item == pytest.approx(TRUE["item"], rel=0.15)


def test_one_observation_per_item_is_rejected():
    with pytest.raises(ValueError, match="one observation per item"):
        variance_components([(("t", str(i)), "", float(i)) for i in range(5)])


def _gain_share(**comp: float) -> float:
    vc = VarianceComponents(
        n_items=100, n_variants=4, n_cells=400, n_obs=800, within=0.0, variant=0.01, **comp
    )
    t = precision_table(vc)
    return (t["now"][2] - t["2K"][2]) / (t["now"][2] - t["2n"][2])


def test_power_trials_help_only_when_trial_variance_dominates():
    assert _gain_share(item=0.01, trial=1.0) > 0.8
    assert _gain_share(item=1.0, trial=0.01) < 0.05


def test_power_known_answer():
    # item-only variance 1, n=100: SE 0.1, MDE = 2.8016 * sqrt(2) * 0.1; 2n shrinks it by sqrt(2)
    vc = VarianceComponents(
        n_items=100,
        n_variants=1,
        n_cells=100,
        n_obs=200,
        item=1.0,
        variant=math.nan,
        trial=0.0,
        within=0.0,
    )
    t = precision_table(vc)
    assert t["now"][1] == pytest.approx(0.1)
    assert t["now"][2] == pytest.approx(2.8016 * math.sqrt(2) * 0.1, rel=1e-3)
    assert t["2n"][2] == pytest.approx(t["now"][2] / math.sqrt(2))
    assert t["floor"][2] == pytest.approx(t["now"][2])
    assert "2V" not in t


def _write(path: Path, obs, model: str = "m") -> None:
    with open(path, "w", encoding="utf-8") as f:
        for (task, ex), variant, y in obs:
            row = {"task": task, "model": model, "example_id": ex, "score": y}
            if variant:
                row["prompt_variant"] = variant
            f.write(json.dumps(row) + "\n")


def test_load_observations_reads_variant(tmp_path):
    p = tmp_path / "r.jsonl"
    _write(p, [(("t", "1"), "v1", 1.0), (("t", "2"), "", 0.0)])
    assert load_observations(p) == {"m": [(("t", "1"), "v1", 1.0), (("t", "2"), "", 0.0)]}


def test_cli_variance_and_compare_show_variants(tmp_path, capsys):
    p = tmp_path / "r.jsonl"
    obs = _synthetic(60, 3, 2, seed=4)
    _write(p, obs, "a")
    _write(tmp_path / "b.jsonl", [(k, v, y - 0.05) for k, v, y in obs], "b")
    with open(p, "a", encoding="utf-8") as f:
        f.write((tmp_path / "b.jsonl").read_text())
    assert main(["variance", str(p), "--model", "a"]) == 0
    out = capsys.readouterr().out
    assert "prompt variant (within item)" in out and "2K (K=4)" in out
    assert main(["compare", str(p), "--a", "a", "--b", "b"]) == 0
    out = capsys.readouterr().out
    assert "Prompt variants" in out and "A - B per variant" in out
    assert main(["variance", str(p), "--model", "zzz"]) == 1
