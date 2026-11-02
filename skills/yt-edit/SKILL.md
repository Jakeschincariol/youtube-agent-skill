---
name: yt-edit
description: >-
  Turn a raw recording's timestamped transcript into a reviewable edit decision
  list for dead air, filler cues and possible retakes. Use for editing plans,
  dead-space cleanup, tightening a video, or shortening footage from a transcript.
---

# yt-edit

Create a reviewable edit decision list (EDL) from a timestamped transcript.
The utility prints suggestions; it never changes media or transcript files.

## Run

    python3 skills/yt-edit/deadair.py transcript.srt
    python3 skills/yt-edit/deadair.py transcript.vtt --floor 0.35 --json
    python3 skills/yt-edit/deadair.py whisper.json --floor 0.5

Supported formats are SRT, WebVTT and Whisper-style JSON (a root list of segments
or an object containing a `segments` list). Provide a transcript first; never
guess timings from an un-timestamped script.

## What it finds

- **DEAD** — gaps longer than the configured floor. The suggested cut preserves
  half the floor on either side of the gap as breathing room.
- **FILLER** — cues made entirely of configured filler expressions such as
  "um", "uh" or "basically". Review the footage: some conversational words are
  meaningful in context and should not automatically be removed.
- **REPEAT** — possible repeated sentence openings. These are **review-only
  candidates**, not automatic cuts. A transcript cannot tell which take is
  better, and a repeated opening may be intentional emphasis.

The reported removable duration counts only DEAD and FILLER intervals and
merges overlapping intervals so time is not counted twice. REPEAT candidates
are excluded from the removable-time estimate.

## Important limitations

- Captions and transcripts are not a waveform. They cannot establish whether a
  gap is truly dead air, whether a breath should remain, or whether a filler
  word is expressive.
- The estimate describes transcript intervals only. It cannot account for
  B-roll, screen recordings, music, silent demonstrations or other visual
  content. Check every suggestion against the footage and audio before editing.
- Transcript cue starts must be chronological. Overlapping captions are allowed.
- This tool produces an EDL for a human editor; it does not cut, render, or publish
  media.

## Review gate

Inspect each proposed interval in the original recording, preserve context and
natural pacing, then apply only the edits you approve. Do not claim that the
suggested runtime is the final video runtime.
