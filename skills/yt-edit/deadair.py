#!/usr/bin/env python3
"""deadair.py - an edit decision list from a timestamped transcript.

    python3 deadair.py transcript.srt            # or .vtt, or whisper .json
    python3 deadair.py transcript.srt --floor 0.35 --json

Finds dead-air gaps, filler-only cues and repeated sentence openings. It prints an
edit decision list; it never modifies media or transcript files.
"""
import json
import math
import os
import re
import sys

FILLER_ONLY = re.compile(
    r"^[\s,.-]*((um+|uh+|er+|ah+|so|okay|ok|right|yeah|like|anyway|basically|"
    r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$",
    re.I,
)


def parse_ts(value):
    """Parse an SRT/VTT timestamp (MM:SS.mmm or HH:MM:SS.mmm)."""
    parts = value.strip().replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), float(parts[2])
        if minutes >= 60 or seconds >= 60:
            raise ValueError(f"invalid timestamp: {value!r}")
        return hours * 3600 + minutes * 60 + seconds
    if len(parts) == 2:
        minutes, seconds = int(parts[0]), float(parts[1])
        if seconds >= 60:
            raise ValueError(f"invalid timestamp: {value!r}")
        return minutes * 60 + seconds
    raise ValueError(f"invalid timestamp: {value!r}")


def _load_whisper_json(raw):
    data = json.loads(raw)
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
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Whisper segment {index} needs numeric start and end values") from exc
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end < start:
            raise ValueError(f"Whisper segment {index} has an invalid time range")
        text = segment.get("text") or ""
        if not isinstance(text, str):
            text = str(text)
        cues.append((start, end, text.strip()))
    return cues


def load(path):
    """Load SRT, VTT or Whisper JSON into (start, end, text) tuples."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        raw = handle.read()

    if path.lower().endswith(".json"):
        return _load_whisper_json(raw)

    cues, current = [], None
    for line in raw.splitlines():
        match = re.match(r"\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)", line)
        if match:
            current = [parse_ts(match.group(1)), parse_ts(match.group(2)), []]
            if current[1] < current[0]:
                raise ValueError("transcript cue ends before it starts")
            cues.append(current)
        elif current is not None and line.strip() and not line.strip().isdigit():
            current[2].append(line.strip())
    return [(start, end, " ".join(text)) for start, end, text in cues if text]


def norm(text):
    return re.sub(r"[^a-z ]", "", text.lower()).split()


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [item for item in args if item != "--json"]
    floor = float(args[args.index("--floor") + 1]) if "--floor" in args else 0.45
    args = [item for item in args if not item.startswith("--") and not re.match(r"^[\d.]+$", item)]
    if not args or not os.path.exists(args[0]):
        print(__doc__)
        sys.exit(1)

    try:
        cues = load(args[0])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"could not read transcript: {exc}", file=sys.stderr)
        sys.exit(2)
    if not cues:
        print("no cues found - is this an srt, vtt or whisper json?")
        sys.exit(1)

    duration = cues[-1][1]
    cuts = []
    for index, (start, end, text) in enumerate(cues):
        if FILLER_ONLY.match(text):
            cuts.append({"kind": "FILLER", "start": start, "end": end, "why": text.strip()[:48]})
        if index:
            gap = start - cues[index - 1][1]
            if gap > floor:
                keep = floor / 2
                cuts.append({
                    "kind": "DEAD",
                    "start": round(cues[index - 1][1] + keep, 3),
                    "end": round(start - keep, 3),
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
                        "why": f'restart of "{" ".join(first)}"',
                    })

    cuts = [cut for cut in cuts if cut["end"] > cut["start"]]
    cuts.sort(key=lambda cut: cut["start"])
    removed = sum(cut["end"] - cut["start"] for cut in cuts)
    if as_json:
        print(json.dumps({
            "source": args[0],
            "duration": duration,
            "cuts": cuts,
            "removed": round(removed, 3),
            "out": round(duration - removed, 3),
        }, indent=1))
        return

    print(f"\n  {args[0]}   {duration:.2f}s in, {len(cues)} cues, dead-air floor {floor}s\n")
    for cut in cuts:
        print(
            f"    {cut['kind']:<7} {cut['start']:8.2f} -> {cut['end']:8.2f}   "
            f"{cut['end']-cut['start']:5.2f}s   {cut['why']}"
        )
    shorter = removed / duration * 100 if duration else 0
    print(f"\n  {len(cuts)} cuts, {removed:.2f}s removed, {duration - removed:.2f}s out "
          f"({shorter:.1f}% shorter)\n")


if __name__ == "__main__":
    main()
