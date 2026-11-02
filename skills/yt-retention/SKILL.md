---
name: yt-retention
description: >-
  Read a YouTube Studio audience-retention export and find where viewers
  actually leave, then say what to change. Use for "why do people stop
  watching", "my retention is bad", a pasted retention chart or CSV, or "fix
  my pacing".
---

# yt-retention

The retention graph is useful audience feedback, but individual charts need to be interpreted in context.

```bash
python3 skills/yt-retention/retention.py retention.csv
python3 skills/yt-retention/retention.py retention.csv --duration 600
python3 skills/yt-retention/retention.py retention.csv --axis seconds
python3 skills/yt-retention/retention.py retention.csv --duration 600 --transcript transcript.srt
```

Getting the file: Studio -> a video -> Analytics -> Engagement -> the audience-retention chart ->
the download icon -> "Audience retention".

## Read the report carefully

- **HOOK LEAK** - estimated loss between the first exported point and the 30-second mark. The
  utility interpolates between samples when the export does not contain a point at exactly 30
  seconds. Treat the result as a diagnostic, not a universal benchmark: video length, format,
  traffic source and audience intent all affect retention.
- **CLIFFS** - the steepest sampled drops. A cliff is a candidate moment to inspect, not proof of
  why viewers left. With --transcript, the tool shows nearby spoken text to help investigate.
- **SLIDE** - average positive loss rate across the samples after the hook window. It is expressed
  per second when the chart uses seconds or a duration is supplied, otherwise per percentage point.

## Position axis

The tool accepts exports whose position column is in seconds or percentage points.

- Automatic detection works when the chart clearly spans approximately 0–100% or extends beyond
  100 seconds.
- Short time-based exports and partial percentage exports can be ambiguous. Specify --axis seconds
  or --axis percent rather than relying on a guess.
- For percentage-axis exports, pass --duration to translate cliff positions into seconds and to
  align the hook window to 30 seconds. --transcript with a percentage axis requires duration.

## What to hand back

Name the single biggest leak and one change for it. Do not present a sampled cliff as a confirmed
cause. If the hook is healthy and the slide is gradual, consider whether the title/thumbnail
promise matches the video before recommending a rewrite; use /yt-package when packaging needs review.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
