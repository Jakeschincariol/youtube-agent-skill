#!/usr/bin/env python3
"""Draft YouTube chapters from a timestamped transcript.

Usage:
    python chapters.py transcript.srt
    python chapters.py transcript.vtt --target 8 --json

The output is a draft. Review and retitle every chapter before publishing.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-edit"))
from deadair import load  # noqa: E402

STOP = set(
    "the a an of for to in on and or is are was were be been with this that it as at by from "
    "you your i my we our they them he she but so if then than there here what which who how "
    "when where why not no yes do does did just really very like about into over out up down "
    "can could will would should have has had get got make made go going went one two".split()
)
MIN_CHAPTER_SECONDS = 10


def keywords(text):
    return {
        word for word in re.findall(r"[a-z']{4,}", text.lower())
        if word not in STOP
    }


def mmss(seconds):
    """Format a non-negative timestamp as YouTube's M:SS or H:MM:SS."""
    total = int(seconds)
    hours, minutes, secs = total // 3600, (total % 3600) // 60, total % 60
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def analyze(cues, target=7):
    """Return a chapter draft and validation details for parsed transcript cues."""
    if isinstance(target, bool) or not isinstance(target, int) or target < 3:
        raise ValueError("target must be an integer of at least 3")
    if not cues:
        raise ValueError("transcript contains no cues")

    duration = max(cue[1] for cue in cues)
    if duration <= 0:
        raise ValueError("transcript duration must be greater than zero")

    candidates = []
    for index in range(1, len(cues)):
        start = cues[index][0]
        if start <= 0 or start >= duration - MIN_CHAPTER_SECONDS:
            continue
        gap = max(0.0, start - cues[index - 1][1])
        before = " ".join(cue[2] for cue in cues[max(0, index - 12):index])
        after = " ".join(cue[2] for cue in cues[index:index + 12])
        before_words, after_words = keywords(before), keywords(after)
        union = before_words | after_words
        shift = 1 - (len(before_words & after_words) / len(union)) if union else 0
        # YouTube chapter timestamps are whole seconds. Score and validate the
        # timestamp users will actually paste, not the fractional cue time.
        timestamp = int(start)
        if timestamp <= 0 or timestamp >= int(duration) - MIN_CHAPTER_SECONDS:
            continue
        candidates.append((gap * 1.6 + shift * 3.2, timestamp, index))

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    picked = [0]
    for _, timestamp, _ in candidates:
        if len(picked) >= target:
            break
        if all(abs(timestamp - existing) >= MIN_CHAPTER_SECONDS for existing in picked):
            picked.append(timestamp)

    picked.sort()
    chapters = []
    for number, timestamp in enumerate(picked):
        next_start = picked[number + 1] if number + 1 < len(picked) else duration
        section_cues = [
            cue for cue in cues
            if timestamp <= (cue[0] + cue[1]) / 2 < next_start
        ]
        section_text = " ".join(cue[2] for cue in section_cues)
        counts = {}
        for word in keywords(section_text):
            counts[word] = section_text.lower().count(word)
        ordered_words = sorted(counts, key=lambda word: (-counts[word], word))
        title = " ".join(word.capitalize() for word in ordered_words[:3]) or "Section"
        chapters.append({
            "start": timestamp,
            "label": mmss(timestamp),
            "draft_title": title,
            "seconds": round(next_start - timestamp, 2),
        })

    errors = []
    if len(chapters) < 3:
        errors.append("YouTube chapters require at least three entries")
    if not chapters or chapters[0]["start"] != 0:
        errors.append("the first chapter must start at 00:00")
    if any(chapter["seconds"] < MIN_CHAPTER_SECONDS for chapter in chapters):
        errors.append("each chapter must be at least 10 seconds long")

    return {
        "valid": not errors,
        "errors": errors,
        "duration": round(duration, 2),
        "chapters": chapters,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draft chapters from SRT, VTT, or Whisper JSON.")
    parser.add_argument("transcript", help="Path to a transcript file")
    parser.add_argument("--target", type=int, default=7, help="Maximum chapter count (minimum 3)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON output")
    args = parser.parse_args(argv)

    if args.target < 3:
        parser.error("--target must be at least 3")
    if not os.path.isfile(args.transcript):
        parser.error(f"transcript file not found: {args.transcript}")

    try:
        report = analyze(load(args.transcript), target=args.target)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))

    if args.as_json:
        print(json.dumps(report, indent=2))
        return 0

    print()
    for chapter in report["chapters"]:
        print(f"  {chapter['label']} {chapter['draft_title']}")
    print(f"\n  {len(report['chapters'])} chapters")
    if report["errors"]:
        print("  -- INVALID: " + "; ".join(report["errors"]))
    print("  Retitle every line before pasting. These are topic-word drafts, not final titles.\n")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
