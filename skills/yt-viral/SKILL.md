---
name: yt-viral
description: >-
  Find what is working in a YouTube niche by comparing videos against
  comparable uploads on their own channel. Use for competitor research,
  viral-video analysis, trend discovery, or building a swipe file.
---

# yt-viral

Raw view counts reflect both channel size and time since publication. This utility compares each
video with a cohort from the same channel and the same format. It does not claim that a title
formula caused a video's performance.

## Run

    python3 skills/yt-viral/swipe.py collected.json --min 2.0
    python3 skills/yt-viral/swipe.py collected.json --min 2.0 --json

## Input

Provide a JSON list, or an object containing a videos list. Each item needs channel, title,
and nonnegative views.

Optional fields:
- format: short or long (preferred when known).
- is_short: boolean alternative to format.
- duration: seconds. If no explicit format is supplied, duration at or below 180 seconds is
  treated as a heuristic for Shorts, not a definitive classification.
- age_days or ISO-8601 published_at: enables comparison by views per day.
- url: source link for the video.

Example:

    {
      "videos": [
        {"channel":"Creator","title":"Example title","views":412000,
         "format":"long","age_days":14,"url":"https://www.youtube.com/watch?v=..."}
      ]
    }

## Comparison rules

- Videos are never compared across channels.
- Shorts, long-form and unknown-format videos are separate cohorts.
- Age-provided videos are compared by views/day; videos without age data are compared by raw views.
  These metric groups are never mixed.
- Each cohort needs at least four videos. Smaller cohorts are skipped and explained.
- The channel median is a descriptive baseline, not a prediction or proof of virality. A single
  snapshot of views/day does not account for traffic sources, impressions, upload promotion,
  seasonality or the full view trajectory.
- When format is inferred from duration, the report labels it as inferred. Supply format or
  is_short when you know the actual format.

## Reading the output

The multiple is relative to the comparable cohort median. The formula label is a title-text match
against the hook patterns in ../yt-script/hooks.json, not an explanation of why the video performed
well. Treat outliers as research leads, then inspect the video, its topic, packaging and context.

Hand back the top five useful examples, explain the limits of the comparison, and identify one
structure the creator could adapt in their own voice. Use publicly available listings only; never
request or use the user's account credentials.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: ship it, or change it?
