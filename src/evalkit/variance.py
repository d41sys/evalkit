"""Trial and prompt-variant variance of a model's score (``evalkit variance``).

A row of ``results.jsonl`` may carry ``prompt_variant`` (which wording of the prompt was used);
repeats of one (item, variant) are the trials. The score of one observation is modelled as

    y_ivt = mu + a_i + b_iv + e_ivt

with item effect ``a_i`` (variance ``item``), prompt-variant effect within the item ``b_iv``
(variance ``variant``: how much one item's score moves between equivalent wordings) and
trial noise ``e_ivt`` (variance ``trial``). Items are the unit of analysis, as everywhere in
evalkit. Items are pooled over tasks.

Estimator: method of moments on the nested random-effects ANOVA (Searle 1971, ch. 10; the
"ANOVA method" for unbalanced nested designs). With ``N`` items, ``C`` (item, variant) cells
and ``M`` observations, ``n_iv`` observations per cell and ``n_i`` per item:

    MSE = SS_within_cell / (M - C)                E[MSE] = trial
    MSV = SS_cell_within_item / (C - N)           E[MSV] = trial + k1 variant
    MSA = SS_item / (N - 1)                       E[MSA] = trial + k2 variant + k3 item

with ``k1 = (M - S1) / (C - N)``, ``k2 = (S1 - S2) / (N - 1)``,
``k3 = (M - sum n_i^2 / M) / (N - 1)``, ``S1 = sum n_iv^2 / n_i`` and ``S2 = sum n_iv^2 / M``.
Solving the three equations gives
unbiased estimates for any unbalanced counts; negative estimates are truncated to 0 after
solving. Components that the data cannot separate are NaN: ``trial`` without repeated
samples (then ``within`` is variant + trial together), ``variant`` with one prompt variant.

Power. Miller (2024, arXiv 2411.00640, sec. 5): Var(mean) = (item + trial / K) / n. With V variants
per item and K trials per variant this becomes

    Var(mean) = (item + variant / V + trial / (V K)) / n

(equal V, K per item; the observed ``C / N`` and ``M / C`` stand in for unbalanced runs).
The MDE is for the difference of two models whose item scores are independent
(``Var(diff) = 2 Var(mean)``), the conservative case: pairing on items removes part of the
item variance, so a paired comparison does better.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Container, Iterable
from dataclasses import dataclass
from pathlib import Path

from .aggregate import minimum_detectable_effect
from .results import ItemKey

Observation = tuple[ItemKey, str, float]
"""(item key, prompt variant, score); variant is ``""`` when the row has none."""


@dataclass(frozen=True)
class VarianceComponents:
    n_items: int
    n_variants: int
    n_cells: int
    n_obs: int
    item: float
    variant: float
    trial: float
    within: float

    @property
    def variants_per_item(self) -> float:
        return self.n_cells / self.n_items

    @property
    def trials_per_cell(self) -> float:
        return self.n_obs / self.n_cells


def load_observations(path: str | Path) -> dict[str, list[Observation]]:
    """Rows per model as (item, ``prompt_variant`` or ``""``, score)."""
    out: dict[str, list[Observation]] = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            variant = row.get("prompt_variant")
            out[row["model"]].append(
                (
                    (str(row["task"]), str(row["example_id"])),
                    "" if variant is None else str(variant),
                    float(row["score"]),
                )
            )
    return dict(out)


def _cells(obs: Iterable[Observation]) -> dict[tuple[ItemKey, str], list[float]]:
    cells: dict[tuple[ItemKey, str], list[float]] = defaultdict(list)
    for item, variant, score in obs:
        cells[(item, variant)].append(score)
    return cells


def variance_components(obs: Iterable[Observation]) -> VarianceComponents:
    """Item, variant and trial variance of one model's scores (see the module docstring)."""
    cells = _cells(obs)
    by_item: dict[ItemKey, list[tuple[float, int]]] = defaultdict(list)
    sse = 0.0
    for (item, _), ys in cells.items():
        mean = sum(ys) / len(ys)
        sse += sum((y - mean) ** 2 for y in ys)
        by_item[item].append((mean, len(ys)))
    n, c = len(by_item), len(cells)
    m = sum(len(ys) for ys in cells.values())
    df_e, df_v = m - c, c - n
    if n < 2:
        raise ValueError("need at least two items")
    if df_e == 0 and df_v == 0:
        raise ValueError("one observation per item: give repeated samples or prompt variants")

    ss_v = ss_a = 0.0
    s1 = s2 = 0.0
    grand = sum(mean * k for cs in by_item.values() for mean, k in cs) / m
    sq_item = 0.0
    for cs in by_item.values():
        n_i = sum(k for _, k in cs)
        item_mean = sum(mean * k for mean, k in cs) / n_i
        ss_v += sum(k * (mean - item_mean) ** 2 for mean, k in cs)
        ss_a += n_i * (item_mean - grand) ** 2
        s1 += sum(k * k for _, k in cs) / n_i
        s2 += sum(k * k for _, k in cs) / m
        sq_item += n_i * n_i
    k2, k3 = (s1 - s2) / (n - 1), (m - sq_item / m) / (n - 1)

    mse = sse / df_e if df_e else 0.0  # no replicates: trial is folded into the variant term
    var_v = (ss_v / df_v - mse) / ((m - s1) / df_v) if df_v else 0.0
    var_a = (ss_a / (n - 1) - mse - k2 * var_v) / k3
    var_v, var_a, mse = max(var_v, 0.0), max(var_a, 0.0), max(mse, 0.0)
    return VarianceComponents(
        n_items=n,
        n_variants=len({v for _, v in cells}),
        n_cells=c,
        n_obs=m,
        item=var_a,
        variant=var_v if df_e and df_v else math.nan,
        trial=mse if df_e else math.nan,
        within=var_v + mse,
    )


def variant_means(
    obs: Iterable[Observation], items: Container[ItemKey] | None = None
) -> dict[str, float]:
    """Mean score per prompt variant: the mean over items of the item's mean in that variant."""
    per_variant: dict[str, list[float]] = defaultdict(list)
    for (item, variant), ys in _cells(obs).items():
        if items is None or item in items:
            per_variant[variant].append(sum(ys) / len(ys))
    return {v: sum(xs) / len(xs) for v, xs in per_variant.items()}


def precision_table(
    vc: VarianceComponents, alpha: float = 0.05, power: float = 0.8
) -> dict[str, tuple[str, float, float]]:
    """{key: (design, SE of the mean, MDE between two models)}.

    Keys: ``now``, ``2n``, ``2K`` and ``2V`` (K and V only when the data can separate that
    component) and ``floor`` (unlimited trials and variants: item variance only). Doubling n,
    K or V costs the same number of model calls.
    """
    has_k = not math.isnan(vc.trial)
    has_v = vc.n_variants > 1
    a = vc.item
    e = vc.trial if has_k else 0.0
    v = (vc.variant if has_k else vc.within) if has_v else 0.0
    v_now, k_now = vc.variants_per_item, vc.trials_per_cell

    def row(label: str, n: int, vs: float, ks: float) -> tuple[str, float, float]:
        var_mean = (a + v / vs + e / (vs * ks)) / n
        sd = math.sqrt(2.0 * var_mean * n)
        return label, math.sqrt(var_mean), minimum_detectable_effect(sd, n, alpha, power)

    n0 = vc.n_items
    rows = {
        "now": row(f"now (n={n0}, V={v_now:.3g}, K={k_now:.3g})", n0, v_now, k_now),
        "2n": row(f"2n (n={2 * n0})", 2 * n0, v_now, k_now),
    }
    if has_k:
        rows["2K"] = row(f"2K (K={2 * k_now:.3g})", n0, v_now, 2 * k_now)
    if has_v:
        rows["2V"] = row(f"2V (V={2 * v_now:.3g})", n0, 2 * v_now, k_now)
    rows["floor"] = row("K, V -> infinity (item variance only)", n0, math.inf, math.inf)
    return rows
