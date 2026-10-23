"""Before/after tables from two ``evalkit stats-check`` markdown reports.

    uv run python scripts/stats_check_compare.py runs/stats-check/report-round1.md \
        runs/stats-check/report.md

Prints markdown: flag counts per kind, binary power at n*, H0 bootstrap coverage and
skewed type-I error (with the warning rate when the second report has one). Every
number is read from the two reports; nothing is recomputed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CELL = re.compile(r"^(?P<v>[0-9.]+) \[[0-9., ]+\](?: \*\*(?P<flag>[a-z-]+)\*\*)?$")
GRID_NS = (20, 50, 115, 240)
FLAG_SHORT = {
    "anti-conservative": "A",
    "conservative": "c",
    "undercovers": "u",
    "overcovers": "v",
    "optimistic": "o",
    "pessimistic": "p",
}

Row = dict[str, str]


def read_tables(path: Path) -> dict[str, list[Row]]:
    """Section title -> rows (dict by header), for every markdown table in the report."""
    out: dict[str, list[Row]] = {}
    title = ""
    header: list[str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            title, header = line[4:], None
        elif line.startswith("|---"):
            continue
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if header is None:
                header = cells
            else:
                out.setdefault(title, []).append(dict(zip(header, cells, strict=True)))
    return out


def section(tables: dict[str, list[Row]], prefix: str) -> list[Row]:
    for title, rows in tables.items():
        if title.startswith(prefix):
            return rows
    raise KeyError(prefix)


def parse(cell: str) -> tuple[float, str]:
    m = CELL.match(cell)
    if m is None:
        raise ValueError(f"unparseable cell {cell!r}")
    return float(m["v"]), m["flag"] or ""


def fmt(cell: str) -> str:
    v, flag = parse(cell)
    return f"{v:.3f}{FLAG_SHORT.get(flag, '')}"


def nominal_n(n: int) -> int:
    """MDE cells run at n* = n or n + 1; map back to the grid size."""
    return min(GRID_NS, key=lambda g: abs(g - n))


def flag_count_exact(
    tables: dict[str, list[Row]], title: str, col: str, flag: str
) -> dict[str, int]:
    out = {"binary": 0, "continuous": 0, "skewed": 0}
    for r in section(tables, title):
        if parse(r[col])[1] == flag:
            out[r["kind"]] += 1
    return out


def summary(a: dict[str, list[Row]], b: dict[str, list[Row]]) -> list[str]:
    spec = [
        (
            "type-I randomisation anti-conservative (of 12)",
            "Type-I",
            "randomisation",
            "anti-conservative",
        ),
        (
            "CI undercovers (of 26 coverage cells)",
            "Bootstrap CI coverage",
            "coverage",
            "undercovers",
        ),
        ("CI overcovers (of 26)", "Bootstrap CI coverage", "coverage", "overcovers"),
        ("power optimistic", "Power", "randomisation", "optimistic"),
        ("power pessimistic", "Power", "randomisation", "pessimistic"),
    ]
    lines = [
        "| flagged cells, before -> after | binary | continuous | skewed |",
        "|---|---|---|---|",
    ]
    for label, title, col, flag in spec:
        x = flag_count_exact(a, title, col, flag)
        y = flag_count_exact(b, title, col, flag)
        lines.append(f"| {label} | " + " | ".join(f"{x[k]} -> {y[k]}" for k in x) + " |")
    return lines


def power_table(a: dict[str, list[Row]], b: dict[str, list[Row]]) -> list[str]:
    def index(rows: list[Row]) -> dict[tuple[str, float, str], Row]:
        out: dict[tuple[str, float, str], Row] = {}
        for r in rows:
            if r["kind"] != "binary":
                continue
            key = nominal_n(int(r["n*"])) if r["group"] == "mde" else r["true effect"]
            out[(r["group"], float(r["tie rate"]), str(key))] = r
        return out

    x, y = index(section(a, "Power")), index(section(b, "Power"))
    lines = [
        "| group | tie rate | n (mde) / effect (fixed) | n* before | power before | n* after "
        "| power after |",
        "|---|---|---|---|---|---|---|",
    ]
    for key in sorted(set(x) | set(y), key=lambda k: (k[0] != "mde", k[1], float(k[2]))):
        rb, ra = x.get(key), y.get(key)
        lines.append(
            f"| {key[0]} | {key[1]:g} | {key[2]} "
            f"| {rb['n*'] if rb else '-'} | {fmt(rb['randomisation']) if rb else '-'} "
            f"| {ra['n*'] if ra else '-'} | {fmt(ra['randomisation']) if ra else '-'} |"
        )
    return lines


def coverage_table(a: dict[str, list[Row]], b: dict[str, list[Row]]) -> list[str]:
    def index(rows: list[Row]) -> dict[tuple[str, float, int], Row]:
        return {
            (r["kind"], float(r["tie rate"]), int(r["n"])): r for r in rows if r["group"] == "h0"
        }

    x, y = index(section(a, "Bootstrap CI coverage")), index(section(b, "Bootstrap CI coverage"))
    ns = sorted({k[2] for k in x} & {k[2] for k in y})
    head = "| kind | tie rate | " + " | ".join(f"n = {n}" for n in ns) + " |"
    lines = [head, "|---|---|" + "---|" * len(ns)]
    for kind in ("binary", "continuous", "skewed"):
        for tie in sorted({k[1] for k in x}):
            cells = [
                f"{fmt(x[(kind, tie, n)]['coverage'])} -> {fmt(y[(kind, tie, n)]['coverage'])}"
                for n in ns
                if (kind, tie, n) in x and (kind, tie, n) in y
            ]
            if cells:
                lines.append(f"| {kind} | {tie:g} | " + " | ".join(cells) + " |")
    return lines


def skew_table(a: dict[str, list[Row]], b: dict[str, list[Row]]) -> list[str]:
    x = {(r["kind"], float(r["tie rate"]), int(r["n"])): r for r in section(a, "Type-I")}
    y = {(r["kind"], float(r["tie rate"]), int(r["n"])): r for r in section(b, "Type-I")}
    head = "| kind | tie rate | n | randomisation before | randomisation after | warn rate |"
    lines = [head, "|---|---|---|---|---|---|"]
    for key in sorted(k for k in x if k[0] != "binary" and k in y):
        warn = y[key].get("warn rate")
        lines.append(
            f"| {key[0]} | {key[1]:g} | {key[2]} | {fmt(x[key]['randomisation'])} "
            f"| {fmt(y[key]['randomisation'])} | {fmt(warn) if warn else '-'} |"
        )
    return lines


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write(__doc__ or "")
        return 2
    a, b = read_tables(Path(argv[1])), read_tables(Path(argv[2]))
    blocks = [
        ("Flag counts", summary(a, b)),
        ("Binary power at n*", power_table(a, b)),
        ("Bootstrap coverage, H0 cells (before -> after)", coverage_table(a, b)),
        ("Randomisation type-I error, non-binary kinds", skew_table(a, b)),
    ]
    for title, lines in blocks:
        print(f"### {title}\n")
        print("\n".join(lines))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
