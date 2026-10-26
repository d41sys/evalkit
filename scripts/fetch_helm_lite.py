"""Download HELM Lite per-instance results (public GCS bucket, stdlib + evalkit only).

Source: https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output (HELM Lite release).
For every model row of the release's `core_scenarios` leaderboard table it fetches each run's
`display_predictions.json` and the family's `instances.json`, and keeps only a compact extract
(see `evalkit.helm`): the headline metric of the evaluation split's instances, the references, and
the predicted text for every `--text-stride`-th model (for the metric cross-check). The raw files
are not kept. Resumable: runs whose compact file exists are skipped. Files left in the legacy raw
layout (`runs/<run>/predictions.json`) are compacted in place instead of downloaded again.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from evalkit.helm import (
    SCENARIOS,
    compact_references,
    compact_run,
    family_of,
    read_table,
    reference_file,
    run_file,
)

BASE = "https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output"
METRIC = {s.task: s for s in SCENARIOS}


def get(url: str, retries: int = 5) -> bytes:
    for attempt in range(retries):
        try:
            with urlopen(url, timeout=120) as resp:
                data: bytes = resp.read()
            return data
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            time.sleep(2 + 3 * attempt)
        except OSError:
            time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"failed: {url}")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", default="v1.13.0")
    ap.add_argument("--out", default="data/raw/helm-lite")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--text-stride", type=int, default=8)
    args = ap.parse_args()
    out = Path(args.out)
    rel = f"{BASE}/releases/{args.release}"
    for name, url in {
        "core_scenarios.json": f"{rel}/groups/core_scenarios.json",
        "schema.json": f"{rel}/schema.json",
        "runs_to_run_suites.json": f"{rel}/runs_to_run_suites.json",
    }.items():
        if not (out / name).exists():
            (out / name).parent.mkdir(parents=True, exist_ok=True)
            (out / name).write_bytes(get(url))
    table = read_table(out)
    suites: dict[str, str] = json.loads((out / "runs_to_run_suites.json").read_text())
    text_models = set(table.models[:: args.text_stride])

    # (run name, task, keep_text), one entry per run
    runs: list[tuple[str, str, bool]] = []
    for model in table.models:
        for task, names in table.runs[model].items():
            runs.extend((n, task, model in text_models and task != "wmt14") for n in names)
    task_of = {n: t for n, t, _ in runs}
    run_url = lambda run: f"{BASE}/runs/{suites[run]}/{urllib.parse.quote(run)}"  # noqa: E731

    families: dict[str, str] = {}
    for run, _, _ in runs:
        families.setdefault(family_of(run), run)

    def fetch_refs(run: str) -> None:
        dest = reference_file(out, run)
        if dest.exists():
            return
        instances = json.loads(get(f"{run_url(run)}/instances.json"))
        write_json(dest, compact_references(instances, METRIC[task_of[run]].split))

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(fetch_refs, families.values()))

    stats = {"downloaded": 0, "recompacted": 0, "missing": 0}

    def fetch_run(job: tuple[str, str, bool]) -> None:
        run, task, keep_text = job
        dest = run_file(out, run)
        if dest.exists():
            return
        legacy = out / "runs" / urllib.parse.quote(run, safe="")
        if (legacy / "predictions.json").exists():
            raw = (legacy / "predictions.json").read_bytes()
            stats["recompacted"] += 1
        else:
            try:
                raw = get(f"{run_url(run)}/display_predictions.json")
            except urllib.error.HTTPError:
                stats["missing"] += 1
                return
            stats["downloaded"] += len(raw)
        keep_ids = set(json.loads(reference_file(out, run).read_text()))
        write_json(dest, compact_run(json.loads(raw), METRIC[task].metric, keep_ids, keep_text))

    print(f"{len(runs)} runs, {len(families)} families", file=sys.stderr)
    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(fetch_run, runs))
    for legacy in (out / "runs").iterdir():
        if legacy.is_dir():
            shutil.rmtree(legacy)
    shutil.rmtree(out / "instances", ignore_errors=True)
    print(
        f"downloaded {stats['downloaded'] / 1e6:.1f} MB, recompacted {stats['recompacted']} legacy "
        f"files, missing {stats['missing']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
