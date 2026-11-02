#!/usr/bin/env python3
"""Analyze a YouTube Studio audience-retention CSV.

Examples:
    python retention.py retention.csv
    python retention.py retention.csv --duration 600
    python retention.py retention.csv --axis seconds
    python retention.py retention.csv --transcript transcript.srt --json

The CSV must contain position and percentage-still-watching columns. Positions may
be seconds or percentages. Use --axis when automatic detection is ambiguous.
"""
import argparse
import csv
import json
import math
import os
import sys


def load_csv(path):
    """Read position/retention pairs, skipping headers and non-data rows."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, row in enumerate(csv.reader(handle), start=1):
            numbers = []
            for cell in row:
                value = cell.strip().replace("%", "").replace(",", "")
                try:
                    number = float(value)
                except ValueError:
                    continue
                if math.isfinite(number):
                    numbers.append(number)
            if len(numbers) >= 2:
                position, retention = numbers[:2]
                if position < 0:
                    raise ValueError(f"CSV line {line_number}: position cannot be negative")
                if not 0 <= retention <= 100:
                    raise ValueError(
                        f"CSV line {line_number}: retention must be between 0 and 100"
                    )
                rows.append((position, retention))

    if len(rows) < 2:
        raise ValueError("CSV must contain at least two numeric position/retention rows")
    for previous, current in zip(rows, rows[1:]):
        if current[0] <= previous[0]:
            raise ValueError("CSV positions must be strictly increasing")
    return rows


def infer_axis(xs, duration=None, requested="auto"):
    """Return 'seconds' or 'percent'; avoid guessing for short/ambiguous charts."""
    if requested != "auto":
        if requested not in ("seconds", "percent"):
            raise ValueError("axis must be auto, seconds, or percent")
        return requested

    maximum = xs[-1]
    if duration is not None:
        tolerance = max(2.0, duration * 0.03)
        looks_like_seconds = abs(maximum - duration) <= tolerance
        looks_like_percent = abs(maximum - 100.0) <= 5.0
        if looks_like_seconds and not looks_like_percent:
            return "seconds"
        if looks_like_percent and not looks_like_seconds:
            return "percent"
        if looks_like_seconds and looks_like_percent:
            raise ValueError(
                "axis is ambiguous for this duration; specify --axis seconds or --axis percent"
            )
        if maximum > 100.5:
            return "seconds"
        raise ValueError(
            "could not infer whether positions are seconds or percentages; "
            "specify --axis seconds or --axis percent"
        )

    if 95.0 <= maximum <= 100.5:
        return "percent"
    if maximum > 100.5:
        return "seconds"
    raise ValueError(
        "positions end below 95, so seconds vs percentage is ambiguous; "
        "specify --axis seconds or --axis percent (and --duration for percent-to-time conversion)"
    )


def interpolate(rows, position):
    """Linearly estimate retention at a position between exported samples."""
    if position < rows[0][0] or position > rows[-1][0]:
        raise ValueError(
            f"retention data does not cover the required hook cutoff ({position:g})"
        )
    for (left_x, left_y), (right_x, right_y) in zip(rows, rows[1:]):
        if left_x <= position <= right_x:
            if position == left_x:
                return left_y
            ratio = (position - left_x) / (right_x - left_x)
            return left_y + ratio * (right_y - left_y)
    return rows[-1][1]


def analyze(rows, duration=None, axis="auto"):
    """Return retention metrics from validated (position, percentage) rows."""
    if duration is not None and (not math.isfinite(duration) or duration <= 0):
        raise ValueError("duration must be a positive number of seconds")
    if len(rows) < 8:
        raise ValueError("at least 8 data points are required")

    xs = [row[0] for row in rows]
    ys = [row[1] for row in rows]
    if any(not math.isfinite(x) or not math.isfinite(y) for x, y in rows):
        raise ValueError("positions and retention values must be finite")
    if any(x < 0 for x in xs) or any(not 0 <= y <= 100 for y in ys):
        raise ValueError("positions must be nonnegative and retention must be 0–100")
    if any(right <= left for left, right in zip(xs, xs[1:])):
        raise ValueError("positions must be strictly increasing")

    axis = infer_axis(xs, duration, axis)
    if axis == "percent" and xs[-1] > 100.5:
        raise ValueError("percentage-axis positions cannot exceed 100")
    if axis == "seconds" and duration is not None and xs[-1] > duration * 1.05:
        raise ValueError("CSV positions exceed the supplied video duration")

    start = ys[0]
    if axis == "seconds":
        cutoff = 30.0
        unit_seconds = 1.0
    elif duration is not None:
        cutoff = 30.0 / duration * 100.0
        unit_seconds = duration / 100.0
    else:
        cutoff = 10.0
        unit_seconds = None

    hook_end = interpolate(rows, cutoff)
    hook_leak = start - hook_end

    intervals = []
    for (left_x, left_y), (right_x, right_y) in zip(rows, rows[1:]):
        span = right_x - left_x
        loss = left_y - right_y
        seconds = span * unit_seconds if unit_seconds is not None else span
        intervals.append({
            "from": left_x,
            "to": right_x,
            "lost": loss,
            "rate": loss / seconds if seconds > 0 else 0.0,
            "midpoint": (left_x + right_x) / 2.0,
        })

    steepest = sorted(intervals, key=lambda item: item["rate"], reverse=True)
    cliffs = []
    for item in steepest:
        if item["lost"] <= 0.8:
            continue
        midpoint = item["midpoint"]
        at_seconds = (
            midpoint if axis == "seconds"
            else midpoint * duration / 100.0 if duration is not None
            else None
        )
        cliffs.append({
            "from": round(item["from"], 2),
            "to": round(item["to"], 2),
            "lost": round(item["lost"], 2),
            "at_seconds": round(at_seconds, 1) if at_seconds is not None else None,
            "loss_per_second": round(item["rate"], 4),
        })
        if len(cliffs) == 5:
            break

    middle_rates = [
        item["rate"] for item in intervals
        if item["midpoint"] > cutoff and item["lost"] > 0
    ]
    slide = sum(middle_rates) / len(middle_rates) if middle_rates else 0.0
    slide_unit = "second" if axis == "seconds" or duration is not None else "percentage point"

    return {
        "points": len(rows),
        "axis": axis,
        "start": round(start, 2),
        "hook_cutoff": round(cutoff, 3),
        "hook_end": round(hook_end, 2),
        "hook_leak": round(hook_leak, 2),
        "end": round(ys[-1], 2),
        "cliffs": cliffs,
        "slide_per_unit": round(slide, 4),
        "slide_unit": slide_unit,
        "said": {},
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="YouTube Studio audience-retention CSV")
    parser.add_argument("--duration", type=float, help="video duration in seconds")
    parser.add_argument(
        "--axis", choices=("auto", "seconds", "percent"), default="auto",
        help="position axis; use this when automatic detection is ambiguous",
    )
    parser.add_argument("--transcript", help="optional SRT, VTT, or Whisper JSON transcript")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rows = load_csv(args.csv_file)
        report = analyze(rows, duration=args.duration, axis=args.axis)

        if args.transcript:
            if not os.path.isfile(args.transcript):
                raise ValueError(f"transcript file not found: {args.transcript}")
            if report["axis"] == "percent" and args.duration is None:
                raise ValueError("--transcript with a percentage axis requires --duration")
            sys.path.insert(
                0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-edit")
            )
            from deadair import load as load_cues

            cues = load_cues(args.transcript)
            said = {}
            for cliff in report["cliffs"]:
                timestamp = cliff["at_seconds"]
                if timestamp is None:
                    continue
                nearby = [
                    cue[2] for cue in cues
                    if cue[0] <= timestamp + 4 and cue[1] >= timestamp - 4
                ]
                said[str(cliff["from"])] = " ".join(nearby)[:140]
            report["said"] = said

        if args.json:
            print(json.dumps(report, indent=2))
            return 0

        print(
            f"\n  {args.csv_file}   {report['points']} points   "
            f"{report['start']:.1f}% -> {report['end']:.1f}%\n"
        )
        hook = report["hook_leak"]
        verdict = "healthy" if hook < 25 else "leaking" if hook < 40 else "severe"
        print(f"  HOOK LEAK   {hook:.1f}% lost by the 30-second mark   [{verdict}]")
        print("              Treat this as a diagnostic heuristic, not a universal benchmark.\n")
        print("  CLIFFS      the steepest sampled drops")
        for cliff in report["cliffs"]:
            where = (
                f"{cliff['at_seconds']:.1f}s"
                if cliff["at_seconds"] is not None else f"{cliff['from']}–{cliff['to']}"
            )
            spoken = report["said"].get(str(cliff["from"]), "")
            print(
                f"    -{cliff['lost']:5.1f}%  near {where:>10}"
                + (f'   "{spoken}"' if spoken else "")
            )
        if not report["cliffs"]:
            print("    no sampled interval lost more than 0.8 percentage points")
        print(
            f"\n  SLIDE       {report['slide_per_unit']:.3f}% per {report['slide_unit']} "
            "across the remaining samples\n"
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"retention analysis failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
