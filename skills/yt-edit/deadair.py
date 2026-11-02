#!/usr/bin/env python3
"""deadair.py - create a reviewable edit decision list from a transcript.

    python3 deadair.py transcript.srt
    python3 deadair.py transcript.vtt --floor 0.35 --json
    python3 deadair.py whisper.json --floor 0.5

Supported inputs: SRT, WebVTT and Whisper-style JSON. This utility never
modifies media or transcript files. Repeated openings are review suggestions,
not automatic cuts, because a transcript alone cannot identify the better take.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

FILLER_ONLY = re.compile(
    r"^[\s,.-]*((um+|uh+|er+|ah+|so|okay|ok|right|yeah|like|anyway|basically|"
    r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$",
    re.I,
)
TIMESTAMP_LINE = re.compile(r"\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)")


def parse_ts(value):
    """Parse an SRT/VTT timestamp (MM:SS.mmm or HH:MM:SS.mmm)."""
    if not isinstance(value, str):
        raise ValueError(f"invalid timestamp: {value!r}")
    parts = value.strip().replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            if not parts[0].isdigit() or not parts[1].isdigit():
                raise ValueError
            hours, minutes, seconds = int(parts[0]), int(parts[1]), float(parts[2])
            if minutes >= 60 or not 0 <= seconds < 60:
                raise ValueError
            result = hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            if not parts[0].isdigit():
                raise ValueError
            minutes, seconds = int(parts[0]), float(parts[1])
            if not 0 <= seconds < 60:
                raise ValueError
            result = minutes * 60 + seconds
        else:
            raise ValueError
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"invalid timestamp: {value!r}")
    return result


def _load_whisper_json(raw):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid Whisper JSON: {exc.msg}") from exc
    if isinstance(data, list):
        segments = data
    elif isinstance(data, dict):
        segments = data.get("segments")
    else:
        raise ValueError("Whisper JSON must contain a list or an object with a 'segments' list")

    if not isinstance(segments, list):
        raise ValueError("Whisper JSON 'segments' must be a list")

    cues = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"Whisper segment {index} must be an object")
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Whisper segment {index} needs numeric start and end values"
            ) from exc
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end < start:
            raise ValueError(f"Whisper segment {index} has an invalid time range")
        text = segment.get("text") or ""
        if not isinstance(text, str):
            raise ValueError(f"Whisper segment {index} text must be a string")
        cues.append((start, end, text.strip()))
    return _validate_cue_order(cues)


def _validate_cue_order(cues):
    """Require chronological cue starts; overlapping captions remain valid."""
    previous_start = -1.0
    for index, (start, end, _text) in enumerate(cues):
        if start < previous_start:
            raise ValueError(
                f"transcript cues are out of order at cue {index}; "
                "sort cues by start time before editing"
            )
        previous_start = start
    return cues


def load(path):
    """Load SRT, VTT or Whisper JSON into (start, end, text) tuples."""
    path = str(path)
    try:
        raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        raise

    if path.lower().endswith(".json"):
        return _load_whisper_json(raw)

    cues, current = [], None
    for line in raw.splitlines():
        match = TIMESTAMP_LINE.match(line)
        if match:
            start, end = parse_ts(match.group(1)), parse_ts(match.group(2))
            if end < start:
                raise ValueError("transcript cue ends before it starts")
            current = [start, end, []]
            cues.append(current)
        elif current is not None and line.strip() and not line.strip().isdigit():
            current[2].append(line.strip())

    parsed = [
        (start, end, " ".join(text).strip())
        for start, end, text in cues
        if " ".join(text).strip()
    ]
    return _validate_cue_order(parsed)


def norm(text):
    return re.sub(r"[^a-z ]", "", text.lower()).split()


def _merged_duration(intervals):
    """Return the union length of intervals, avoiding double-counting overlap."""
    intervals = sorted((start, end) for start, end in intervals if end > start)
    if not intervals:
        return 0.0
    total = 0.0
    current_start, current_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + current_end - current_start


def analyze(cues, floor=0.45):
    """Build edit suggestions. REPEAT candidates are review-only, not counted as cuts."""
    if not isinstance(floor, (int, float)) or not math.isfinite(floor) or floor <= 0:
        raise ValueError("dead-air floor must be a finite number greater than zero")
    if not cues:
        raise ValueError("no cues found - is this an srt, vtt or whisper json?")
    _validate_cue_order(cues)

    duration = max(end for _start, end, _text in cues)
    cuts = []
    for index, (start, end, text) in enumerate(cues):
        if FILLER_ONLY.match(text):
            cuts.append({
                "kind": "FILLER", "start": start, "end": end,
                "why": text.strip()[:48],
            })
        if index:
            gap = start - cues[index - 1][1]
            if gap > floor:
                keep = floor / 2
                cut_start = cues[index - 1][1] + keep
                cut_end = start - keep
                if cut_end > cut_start:
                    cuts.append({
                        "kind": "DEAD",
                        "start": round(cut_start, 3),
                        "end": round(cut_end, 3),
                        "why": f"{gap:.2f}s gap",
                    })
        if text.strip() and not FILLER_ONLY.match(text):
            previous = index - 1
            while previous >= 0 and (
                FILLER_ONLY.match(cues[previous][2]) or not cues[previous][2].strip()
            ):
                previous -= 1
            if previous >= 0:
                first = norm(cues[previous][2])[:5]
                second = norm(text)[:5]
                if len(first) >= 3 and first == second:
                    cuts.append({
                        "kind": "REPEAT",
                        "start": cues[previous][0],
                        "end": cues[previous][1],
                        "why": f'review possible restart of "{" ".join(first)}"',
                        "review_only": True,
                    })

    cuts.sort(key=lambda cut: (cut["start"], cut["end"], cut["kind"]))
    removable = [
        (cut["start"], cut["end"])
        for cut in cuts if cut["kind"] in {"DEAD", "FILLER"}
    ]
    removed = _merged_duration(removable)
    return {
        "duration": duration,
        "cuts": cuts,
        "removed": round(removed, 3),
        "out": round(max(0.0, duration - removed), 3),
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Create a reviewable edit decision list from SRT, VTT or Whisper JSON."
    )
    parser.add_argument("transcript", help="path to .srt, .vtt or Whisper .json")
    parser.add_argument(
        "--floor", type=float, default=0.45,
        help="minimum gap in seconds to flag as dead air (default: 0.45)",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.floor) or args.floor <= 0:
        parser.error("--floor must be a finite number greater than zero")

    try:
        cues = load(args.transcript)
        report = analyze(cues, args.floor)
    except (OSError, ValueError) as exc:
        print(f"could not analyze transcript: {exc}", file=sys.stderr)
        return 2

    report["source"] = args.transcript
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    duration = report["duration"]
    cuts = report["cuts"]
    removed = report["removed"]
    print(
        f"\n  {args.transcript}   {duration:.2f}s in, {len(cues)} cues, "
        f"dead-air floor {args.floor}s\n"
    )
    for cut in cuts:
        label = "REVIEW" if cut["kind"] == "REPEAT" else cut["kind"]
        print(
            f"    {label:<7} {cut['start']:8.2f} -> {cut['end']:8.2f}   "
            f"{cut['end'] - cut['start']:5.2f}s   {cut['why']}"
        )
    shorter = removed / duration * 100 if duration else 0
    print(
        f"\n  {len(cuts)} suggestions, {removed:.2f}s removable "
        f"({shorter:.1f}% of transcript duration), "
        f"{report['out']:.2f}s estimated out\n"
    )
    print("  REPEAT items are review-only and are not included in removable time.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
