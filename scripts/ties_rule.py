"""Before/after table and the pre-registered decision rule of ``docs/protocol-ties.md``.

    uv run --offline python scripts/ties_rule.py runs/stats-check/ties-before-seed101.md \
        runs/stats-check/ties-after-seed101.md

Reads two ``evalkit stats-check`` markdown reports (same seed, grid and replications; only the
tie path differs) and prints the 36 H0 cells and the power cells before and after, then the
rule: adopt iff every H0 randomisation Type-I point estimate is <= 0.06 and the mean power
loss (before - after, signed mean over the power cells) is <= 0.03. Every number is read from
the reports; the only computation is the differences and their summary.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from stats_check_compare import read_tables, section

CELL = re.compile(r"^(?P<v>[0-9.]+) \[(?P<lo>[0-9.]+), (?P<hi>[0-9.]+)\]")
REPS = re.compile(r"replications: H0 (?P<h0>\d+), power (?P<power>\d+)")
TYPE1_LIMIT = 0.06
LOSS_LIMIT = 0.03
Z99 = 2.576


def rate(cell: str) -> tuple[float, float, float]:
    m = CELL.match(cell)
    if m is None:
        raise ValueError(f"unparseable cell {cell!r}")
    return float(m["v"]), float(m["lo"]), float(m["hi"])


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write(__doc__ or "")
        return 2
    texts = [Path(p).read_text(encoding="utf-8") for p in argv[1:]]
    tables = [read_tables(Path(p)) for p in argv[1:]]
    reps = [REPS.search(t) for t in texts]
    if any(r is None for r in reps):
        raise ValueError("replication counts not found in the report header")
    n_power = [int(r["power"]) for r in reps if r is not None]

    key_h0 = ("kind", "tie rate", "n")
    h0 = [{tuple(r[k] for k in key_h0): r for r in section(t, "Type-I")} for t in tables]
    print("### H0 cells: randomisation Type-I error (99% Wilson), before -> after\n")
    print("| kind | tie rate | n | before | after |\n|---|---|---|---|---|")
    above = [0, 0]
    failing: list[str] = []
    binary_same = True
    for key, row in h0[0].items():
        b, a = rate(row["randomisation"]), rate(h0[1][key]["randomisation"])
        above[0] += b[0] > TYPE1_LIMIT
        above[1] += a[0] > TYPE1_LIMIT
        if a[0] > TYPE1_LIMIT:
            failing.append(f"{key[0]} tie {key[1]} n={key[2]}: {a[0]:.3f}")
        if key[0] == "binary":
            binary_same &= row["randomisation"] == h0[1][key]["randomisation"]
        print(
            f"| {key[0]} | {key[1]} | {key[2]} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] "
            f"| {a[0]:.3f} [{a[1]:.3f}, {a[2]:.3f}] |"
        )

    key_pw = ("group", "kind", "tie rate", "true effect")
    pw = [{tuple(r[k] for k in key_pw): r for r in section(t, "Power")} for t in tables]
    print("\n### Power cells: randomisation power at n*, before -> after\n")
    print("| group | kind | tie rate | true effect | n* | before | after | loss |")
    print("|---|---|---|---|---|---|---|---|")
    losses: list[float] = []
    var = 0.0
    worst = (0.0, "")
    for key, row in pw[0].items():
        other = pw[1][key]
        if row["n*"] != other["n*"]:
            raise ValueError(f"n* differs for {key}: {row['n*']} vs {other['n*']}")
        b, a = rate(row["randomisation"]), rate(other["randomisation"])
        loss = b[0] - a[0]
        losses.append(loss)
        var += b[0] * (1 - b[0]) / n_power[0] + a[0] * (1 - a[0]) / n_power[1]
        if loss > worst[0]:
            worst = (loss, f"{key[1]} tie {key[2]} effect {key[3]}")
        if key[1] == "binary":
            binary_same &= row["randomisation"] == other["randomisation"]
        print(
            f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | {row['n*']} | {b[0]:.3f} | {a[0]:.3f} "
            f"| {loss:+.3f} |"
        )
    mean_loss = sum(losses) / len(losses)
    half = Z99 * math.sqrt(var) / len(losses)

    ok1 = not failing
    ok2 = mean_loss <= LOSS_LIMIT
    print("\n### Pre-registered rule\n")
    print(
        f"* H0 cells with point estimate > {TYPE1_LIMIT}: before {above[0]}, after {above[1]} of 36"
    )
    print(f"* condition 1 (all 36 <= {TYPE1_LIMIT}): {'PASS' if ok1 else 'FAIL'}")
    if failing:
        print("  failing cells: " + "; ".join(failing))
    print(
        f"* mean power loss over {len(losses)} cells: {mean_loss:+.4f} "
        f"(approximate 99% interval {mean_loss - half:+.4f} to {mean_loss + half:+.4f}, "
        f"unpaired SE so conservative); largest single-cell loss {worst[0]:+.3f} ({worst[1]})"
    )
    print(f"* condition 2 (mean loss <= {LOSS_LIMIT}): {'PASS' if ok2 else 'FAIL'}")
    print(f"* binary cells identical before and after: {binary_same}")
    print(f"* decision: {'ADOPT as default' if ok1 and ok2 else 'KEEP OPT-IN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
