#!/usr/bin/env python3
"""Normalize waypoint names in a CUP file.

Behavior:
- Removes leading digits (and adjacent separators) from the name field.
- Converts the remaining name to title case.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from pathlib import Path

from charset_normalizer import from_bytes

NAME_COLUMNS = {"name", "waypoint", "wpname"}
LEADING_NUMBER_RE = re.compile(r"^\s*\d+\s*[-._]*\s*")


def decode_content(raw: bytes) -> str:
    """Decode bytes to text using charset-normalizer."""
    results = from_bytes(raw)
    chosen: str | None = None
    for result in results:
        enc = getattr(result, "encoding", None)
        if result.chaos == 0 and isinstance(enc, str) and enc.lower().startswith(("cp", "iso")):
            chosen = str(result)
            break
    return chosen if chosen is not None else str(results.best())


def normalize_name(value: str) -> str:
    value = LEADING_NUMBER_RE.sub("", value.strip())
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value.title()


def split_waypoints_and_tasks(lines: list[str]) -> tuple[list[str], list[str]]:
    for i, line in enumerate(lines):
        if "related tasks" in line.lower():
            return lines[:i], lines[i:]
    return lines, []


def find_name_column(header: list[str]) -> int:
    for i, column in enumerate(header):
        if column.strip().lower() in NAME_COLUMNS:
            return i
    raise ValueError("Could not find a name column in the CUP header.")


def normalize_waypoint_section(waypoint_lines: list[str]) -> str:
    if not waypoint_lines:
        return ""

    reader = csv.reader(waypoint_lines, delimiter=",", quotechar='"')
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

    header = next(reader, None)
    if header is None:
        return ""
    name_idx = find_name_column(header)
    writer.writerow(header)

    for row in reader:
        if not row:
            writer.writerow(row)
            continue
        if row[0].lstrip().startswith("#"):
            writer.writerow(row)
            continue
        if len(row) > name_idx:
            row[name_idx] = normalize_name(row[name_idx])
        writer.writerow(row)

    return output.getvalue().rstrip("\n")


def normalize_cup_content(content: str) -> str:
    lines = content.splitlines()
    waypoint_lines, task_lines = split_waypoints_and_tasks(lines)

    normalized_waypoints = normalize_waypoint_section(waypoint_lines)
    if not task_lines:
        return normalized_waypoints + "\n"

    return normalized_waypoints + "\n" + "\n".join(task_lines) + "\n"


def resolve_output_path(input_path: Path, output: str | None, in_place: bool) -> Path:
    if in_place:
        return input_path
    if output:
        return Path(output)
    return input_path.with_name(f"{input_path.stem}_normalized{input_path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize waypoint names in a CUP file.")
    parser.add_argument("input", help="Input .cup file path")
    parser.add_argument("-o", "--output", help="Output .cup file path")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file in place",
    )
    args = parser.parse_args()

    if args.in_place and args.output:
        parser.error("Use either --in-place or --output, not both.")

    input_path = Path(args.input)
    output_path = resolve_output_path(input_path, args.output, args.in_place)

    raw = input_path.read_bytes()
    content = decode_content(raw)
    normalized = normalize_cup_content(content)
    output_path.write_text(normalized, encoding="utf-8")

    print(f"Normalized CUP written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
