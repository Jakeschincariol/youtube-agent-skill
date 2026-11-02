---
name: yt-chapters
description: >-
  Draft YouTube chapters from a transcript and validate the required
  chapter structure. Use for "add chapters", "timestamps", or
  "break this video into sections".
---

# yt-chapters

```bash
python3 skills/yt-chapters/chapters.py transcript.srt --target 8
python3 skills/yt-chapters/chapters.py transcript.vtt --json
```

## Validation

The generator checks the chapter structure before presenting it as valid:

- The first entry starts at **00:00**.
- There are at least **three** entries.
- Each chapter is at least **10 seconds** long.
- Timestamps are emitted as whole seconds, and validation uses those displayed timestamps.
- `--target` must be an integer of at least three; it is a maximum, not a promise that the transcript contains enough usable boundaries.

A short transcript may not contain enough distinct boundaries to produce three valid chapters. In that case the tool reports the output as invalid instead of inventing chapter boundaries.

## How boundaries are drafted

Candidate boundaries are transcript cue starts. The tool scores pauses and changes in vocabulary between nearby transcript windows. This is a heuristic for proposing review points, not a semantic understanding of the video and not a claim about retention or ranking.

## Retitle every line

The generated titles are topic-word drafts. Rewrite them as clear, accurate descriptions of the section in the creator's voice. Do not publish keyword fragments as final chapter titles.

## The gate

Nothing here publishes. Review the timestamps and titles, then copy the approved block into the video description yourself.
