"""Reading ``results.jsonl``: per-item scores, cluster ids and repeated samples.

A row is one scored sample: ``task``, ``model``, ``example_id``, ``score`` and optionally
``cluster_id`` (items that share a passage or source document) and ``sample`` (the sample
index when an item was queried several times). Rows with the same (model, task, example_id)
are samples of one item.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ItemKey = tuple[str, str]
"""(task, example_id)."""
ClusterLabel = tuple[str, str]
"""(task, cluster_id): the same cluster id in two tasks is two clusters."""


@dataclass
class ResultsTable:
    """Scores of every model as lists of samples per item, plus the item -> cluster map."""

    samples: dict[str, dict[ItemKey, list[float]]] = field(default_factory=dict)
    clusters: dict[ItemKey, ClusterLabel] = field(default_factory=dict)

    @property
    def has_clusters(self) -> bool:
        return bool(self.clusters)

    def models(self) -> list[str]:
        """Model names in order of first appearance."""
        return list(self.samples)

    def item_scores(self, model: str) -> dict[ItemKey, float]:
        """Mean score over each item's samples (the item is the unit of analysis)."""
        return {k: float(np.mean(v)) for k, v in self.samples.get(model, {}).items()}

    def all_item_scores(self) -> dict[str, dict[object, float]]:
        return {m: {k: v for k, v in self.item_scores(m).items()} for m in self.samples}

    def sample_counts(self, models: Sequence[str] | None = None) -> tuple[int, int]:
        """(fewest, most) samples per item over ``models`` (all models by default)."""
        counts = [
            len(v)
            for m in (self.samples if models is None else models)
            for v in self.samples.get(m, {}).values()
        ]
        return (min(counts), max(counts)) if counts else (0, 0)


def load_results(path: str | Path) -> ResultsTable:
    """Parse a results file. Raises ValueError when one item has two different cluster ids."""
    table = ResultsTable()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (str(row["task"]), str(row["example_id"]))
            table.samples.setdefault(row["model"], {}).setdefault(key, []).append(
                float(row["score"])
            )
            cid = row.get("cluster_id")
            if cid is not None:
                label = (key[0], str(cid))
                if table.clusters.setdefault(key, label) != label:
                    raise ValueError(
                        f"{path}: item {key} has two cluster ids "
                        f"({table.clusters[key][1]!r} and {label[1]!r})"
                    )
    return table


def merge_clusters(*tables: ResultsTable) -> dict[ItemKey, ClusterLabel]:
    """One item -> cluster map from several files; ValueError on a disagreement."""
    merged: dict[ItemKey, ClusterLabel] = {}
    for table in tables:
        for key, label in table.clusters.items():
            if merged.setdefault(key, label) != label:
                raise ValueError(
                    f"item {key} has different cluster ids in different files "
                    f"({merged[key][1]!r} and {label[1]!r})"
                )
    return merged
