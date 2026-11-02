#!/usr/bin/env python3
"""Rank competitor videos against comparable uploads on their own channel.

Input JSON is a list of video objects, or an object with a "videos" list.
Required fields: channel, title, views. Optional: duration (seconds), format
("short" or "long"), is_short (boolean), age_days, published_at (ISO-8601),
and url.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "..", "yt-script", "hooks.json"), encoding="utf-8") as handle:
    FORMULAS = json.load(handle).get("hooks", [])


def classify(title):
    scored = []
    for formula in FORMULAS:
        count = sum(1 for pattern in formula.get("match", []) if re.search(pattern, title, re.I))
        if count:
            scored.append((count, formula.get("name", "Unclassified")))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored[0][1] if scored else "Unclassified"


def number(value, field, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number") from None
    if not math.isfinite(result) or result < minimum:
        raise ValueError(f"{field} must be finite and at least {minimum:g}")
    return result


def age_days(row):
    if row.get("age_days") is not None:
        age = number(row["age_days"], "age_days")
        if age == 0:
            raise ValueError("age_days must be greater than zero")
        return age
    published = row.get("published_at")
    if not published:
        return None
    if not isinstance(published, str):
        raise ValueError("published_at must be an ISO-8601 string")
    try:
        published_at = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"invalid published_at timestamp: {published}") from None
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=dt.timezone.utc)
    age = (dt.datetime.now(dt.timezone.utc) - published_at.astimezone(dt.timezone.utc)).total_seconds() / 86400
    if age <= 0:
        raise ValueError("published_at must be in the past")
    return age


def video_format(row):
    explicit = row.get("format")
    if explicit is not None:
        if not isinstance(explicit, str) or explicit.lower() not in ("short", "long"):
            raise ValueError("format must be 'short' or 'long'")
        return explicit.lower(), "provided"
    is_short = row.get("is_short")
    if is_short is not None:
        if not isinstance(is_short, bool):
            raise ValueError("is_short must be true or false")
        return ("short" if is_short else "long"), "provided"
    duration = row.get("duration")
    if duration is None:
        return "unknown", "unknown"
    duration = number(duration, "duration")
    if duration == 0:
        raise ValueError("duration must be greater than zero")
    return ("short" if duration <= 180 else "long"), "inferred_from_duration"


def load_videos_from_data(data):
    """Validate an already-decoded list of video records."""
    if isinstance(data, dict):
        data = data.get("videos")
    if not isinstance(data, list):
        raise ValueError("input JSON must be a list or an object containing a 'videos' list")
    videos = []
    for index, row in enumerate(data):
        label = f"video at index {index}"
        if not isinstance(row, dict):
            raise ValueError(f"{label} must be an object")
        channel, title = row.get("channel"), row.get("title")
        if not isinstance(channel, str) or not channel.strip():
            raise ValueError(f"{label}: channel must be a non-empty string")
        if not isinstance(title, str):
            raise ValueError(f"{label}: title must be a string")
        views = number(row.get("views"), f"{label} views")
        duration = row.get("duration")
        if duration is not None:
            duration = number(duration, f"{label} duration")
            if duration == 0:
                raise ValueError(f"{label} duration must be greater than zero")
        fmt, format_source = video_format(row)
        videos.append({
            "channel": channel.strip(), "title": title.strip(), "views": views,
            "duration": duration, "format": fmt, "format_source": format_source,
            "age_days": age_days(row),
            "url": row.get("url", "") if isinstance(row.get("url", ""), str) else "",
        })
    return videos


def load_videos(path):
    with open(path, encoding="utf-8-sig") as handle:
        return load_videos_from_data(json.load(handle))


def analyze(videos, minimum=1.5):
    """Compare only within channel, format and age-data cohorts."""
    minimum = number(minimum, "minimum multiple")
    if minimum == 0:
        raise ValueError("minimum multiple must be greater than zero")
    groups = {}
    for video in videos:
        metric = "views_per_day" if video["age_days"] is not None else "views"
        key = (video["channel"], video["format"], metric)
        groups.setdefault(key, []).append(video)

    outliers, skipped = [], []
    for (channel, fmt, metric), group in groups.items():
        if len(group) < 4:
            skipped.append({
                "channel": channel, "format": fmt, "metric": metric,
                "video_count": len(group), "reason": "fewer than four comparable videos",
            })
            continue
        values = [
            row["views"] / row["age_days"] if metric == "views_per_day" else row["views"]
            for row in group
        ]
        median = statistics.median(values)
        if median <= 0:
            skipped.append({
                "channel": channel, "format": fmt, "metric": metric,
                "video_count": len(group), "reason": "cohort median is zero; relative multiples are undefined",
            })
            continue
        for row, value in zip(group, values):
            multiple = value / median
            if multiple < minimum:
                continue
            outliers.append({
                "channel": channel, "title": row["title"], "views": int(row["views"]),
                "format": fmt, "format_source": row["format_source"], "metric": metric,
                "value": round(value, 2), "median": round(median, 2),
                "multiple": round(multiple, 2),
                "age_days": round(row["age_days"], 2) if row["age_days"] is not None else None,
                "age_adjusted": metric == "views_per_day",
                "formula": classify(row["title"]), "url": row["url"],
            })
    outliers.sort(key=lambda row: (-row["multiple"], row["channel"], row["title"]))
    return {
        "video_count": len(videos),
        "channel_count": len({row["channel"] for row in videos}),
        "outliers": outliers,
        "skipped_cohorts": skipped,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file containing competitor videos")
    parser.add_argument("--min", type=float, default=1.5, dest="minimum",
                        help="minimum multiple over comparable cohort median (default: 1.5)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = analyze(load_videos(args.input), minimum=args.minimum)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"viral analysis failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"\n  {report['video_count']} videos across {report['channel_count']} channels")
    print(f"  Outliers at {args.minimum:g}x or better against comparable cohort median\n")
    for row in report["outliers"][:25]:
        unit = "views/day" if row["age_adjusted"] else "views"
        print(f"  {row['multiple']:5.2f}x  {row['views']:>10,} views  {row['format']:<7} {row['channel'][:20]:<20} {row['title'][:48]}")
        print(f"         {row['value']:,.2f} {unit} vs {row['median']:,.2f} median · {row['formula']}")
    if not report["outliers"]:
        print("  No videos cleared the threshold in cohorts with enough comparable data.")
    if report["skipped_cohorts"]:
        print("\n  Skipped cohorts:")
        for cohort in report["skipped_cohorts"]:
            print(f"    {cohort['channel']} / {cohort['format']} / {cohort['metric']}: {cohort['reason']} ({cohort['video_count']} videos)")
    print("\n  Age-adjusted comparisons use views/day only when age data is supplied.")
    print("  Duration-based format classification is a heuristic; provide format/is_short when known.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
