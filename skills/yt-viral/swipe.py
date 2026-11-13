#!/usr/bin/env python3
"""swipe.py - rank collected videos by how far each beat its OWN channel, then name the formula.

    python3 swipe.py collected.json
    python3 swipe.py collected.json --min 2.0 --format long --json
    python3 swipe.py collected.json --format shorts --shorts-max 180

Input is a list you collected - one object per video:

    [{"channel":"Some Channel","title":"...","views":412000,"url":"...","duration":613}, ...]

Raw view counts rank channel size, not ideas. A 400k video on a 2M-subscriber channel is a normal
Tuesday; a 400k video on a channel whose median is 30k is the thing worth studying. So every video
is scored as a MULTIPLE OF ITS OWN CHANNEL'S MEDIAN, which needs at least four videos per channel
(and format bucket) to mean anything - the tool says so rather than quietly ranking on noise.

Shorts and long-form videos have completely different view distributions on the same channel, so
when `duration` is present, medians are computed separately for Shorts (<= --shorts-max seconds,
default 60) and long-form (> --shorts-max seconds). Videos missing `duration` are grouped together
as "unknown" so inputs without durations still work identically.

The formula comes from skills/yt-script/hooks.json, matched against the TITLE. It is a judgement
about the words on screen, not a claim about why the video worked.
"""
import argparse
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_formulas(path=None):
    target = path or os.path.join(HERE, "..", "yt-script", "hooks.json")
    with open(target, encoding="utf-8") as fh:
        return json.load(fh)["hooks"]


FORMULAS = load_formulas()


def classify(title):
    scored = []
    for f in FORMULAS:
        n = sum(1 for p in f["match"] if re.search(p, title, re.I))
        if n:
            scored.append((n, f["name"]))
    scored.sort(reverse=True)
    return scored[0][1] if scored else "Unclassified"


def video_format(duration, shorts_max=60):
    if duration is None or duration == "":
        return "unknown"
    try:
        d = float(duration)
    except (TypeError, ValueError):
        return "unknown"
    if d <= 0:
        return "unknown"
    return "shorts" if d <= shorts_max else "long"


def analyze(rows, min_multiple=1.5, fmt_filter="all", shorts_max=60):
    by_bucket = {}
    for r in rows:
        ch = r.get("channel", "?")
        fmt = video_format(r.get("duration"), shorts_max=shorts_max)
        if fmt_filter != "all" and fmt != fmt_filter:
            continue
        by_bucket.setdefault((ch, fmt), []).append(r)

    out, thin = [], []
    for (ch, fmt), vids in by_bucket.items():
        if len(vids) < 4:
            thin.append((ch, fmt, len(vids)))
            continue
        views = [float(v.get("views", 0) or 0) for v in vids]
        med = statistics.median(views) if views else 0
        for v in vids:
            view_count = float(v.get("views", 0) or 0)
            m = (view_count / med) if med else 0
            out.append({
                "channel": ch,
                "format": fmt,
                "title": v.get("title", ""),
                "views": int(view_count),
                "median": int(med),
                "multiple": round(m, 2),
                "duration": v.get("duration"),
                "formula": classify(v.get("title", "")),
                "url": v.get("url", ""),
            })

    out = [r for r in out if r["multiple"] >= min_multiple]
    out.sort(key=lambda r: -r["multiple"])
    return out, thin, len(by_bucket)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Rank collected videos by multiple over each channel's own median."
    )
    p.add_argument("file", help="Path to collected.json")
    p.add_argument("--min", type=float, default=1.5, dest="min_multiple",
                   help="Minimum multiple over channel median (default: 1.5)")
    p.add_argument("--format", choices=("all", "long", "shorts"), default="all",
                   help="Filter by video format using duration (default: all)")
    p.add_argument("--shorts-max", type=int, default=60,
                   help="Max duration in seconds classified as Shorts (default: 60)")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Output machine-readable JSON")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not os.path.exists(args.file):
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    with open(args.file, encoding="utf-8") as fh:
        rows = json.load(fh)
    if isinstance(rows, dict):
        rows = rows.get("videos", [])

    out, thin, bucket_count = analyze(
        rows,
        min_multiple=args.min_multiple,
        fmt_filter=args.format,
        shorts_max=args.shorts_max,
    )

    if args.as_json:
        print(json.dumps({
            "outliers": out,
            "skipped_thin_channels": [
                {"channel": c, "format": f, "count": n} for c, f, n in thin
            ],
        }, indent=1, ensure_ascii=False))
        return

    channels_seen = len({c for c, _ in [(r["channel"], r["format"]) for r in out]} | {c for c, _, _ in thin})
    print(f"\n  {len(rows)} videos across {channels_seen or bucket_count} channel(s) "
          f"[format={args.format}], outliers at {args.min_multiple}x or better\n")
    for r in out[:25]:
        tag = f"[{r['format']}]" if r["format"] != "unknown" else ""
        print(f"    {r['multiple']:5.2f}x  {r['views']:>9,}  vs {r['median']:>9,} median   "
              f"{r['channel'][:20]:<20} {tag:<8} {r['title'][:48]}")
        print(f"            {r['formula']}")
    if not out:
        print("    nothing cleared the threshold - collect more per channel or lower --min")
    if thin:
        print(f"\n  skipped {len(thin)} channel/format bucket(s) with under 4 videos collected - "
              "a median off one or two videos is not a median:")
        print("  " + ", ".join(f"{c} [{f}] ({n})" for c, f, n in thin[:6]))

    counts = {}
    for r in out:
        counts[r["formula"]] = counts.get(r["formula"], 0) + 1
    if counts:
        print("\n  formulas among the outliers")
        for f, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {n:2d}x  {f}")
    print()


if __name__ == "__main__":
    main()
