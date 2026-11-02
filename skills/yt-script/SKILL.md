---
name: yt-script
description: >-
  Draft a YouTube video script from an idea, generate hook options using
  21 editorial formulas, and score those hooks with a transparent heuristic.
  Use when the user asks for a video script, hook, opening line, or recording
  outline.
---

# yt-script

Turn an idea into a usable, fact-checked script in the creator's voice.

The folder contains one executable utility, `hookscore.py`, and one data file,
`hooks.json` (the 21 hook-formula reference). The scorer ranks wording against
five editorial criteria. It does not predict views, click-through rate,
watch time, retention, or audience response.

```bash
python3 hookscore.py hooks.txt              # one hook per line, ranked
python3 hookscore.py --hook "one line"      # score a single hook
python3 hookscore.py --json hooks.txt       # machine-readable output
```

## Before drafting

1. Read `~/.claude/youtube/voice.md` if it exists. Use it for the creator's
   natural phrasing, audience, preferences, and claims they will not make.
   If it does not exist, ask for examples or a short description of their voice.
   Do not require three videos if the user cannot provide them.
2. Identify the target viewer, video promise, format, and intended length.
   Ask only for missing details that materially affect the script.
3. Separate supplied facts, sourced facts, opinions, and hypotheses. Never
   invent numbers, results, quotations, case studies, credentials, product
   capabilities, dates, or sources.
4. For time-sensitive or externally verifiable claims, request a source or
   research them when browsing is available. Attribute claims in the script
   or provide a source note. If evidence is unavailable, omit the claim or
   mark it clearly as `[VERIFY: ...]`; never present a placeholder as fact.
5. Treat every example in `hooks.json` as illustrative wording only. Its
   example statistics and outcomes are not evidence and must never be reused
   as factual claims without independent verification.

## The script

The opening matters, but it is not the whole video and no structure guarantees
retention. Use this sequence as a flexible editorial framework:

1. **Hook.** Draft five genuinely different options using relevant formulas
   from `hooks.json`. Score them with `hookscore.py`, then show the top two
   with their five-property panels. Explain that the score is a wording
   heuristic, not a prediction. Do not distort the idea merely to obtain a
   higher score. If options tie, say so.
2. **The turn.** Quickly clarify what the video will deliver and begin
   delivering it. Avoid unnecessary channel introductions or pitches.
3. **The body.** Organize the material into clear beats. For each beat include
   the spoken point and a useful `[ON SCREEN: ...]` visual suggestion.
   Do not invent screen evidence, dashboards, demos, or artifacts.
4. **The payoff.** Deliver the promised information or demonstrate the
   promised artifact. Do not claim an artifact is attached, linked, or shown
   unless it actually is.
5. **The close.** Use one relevant call to action, or none if it would feel
   forced.

## What to hand back

- The two strongest hook drafts, their scores, and a brief heuristic caveat.
- A beat-by-beat spoken script with a meaningful `[ON SCREEN: ...]` cue
  for each beat.
- A runtime estimate calculated from spoken words only, using 150 words per
  minute as an explicit planning assumption. Exclude headings and visual cues;
  label the result an estimate, not a guarantee.
- The formula used by the leading hook and why it fits.
- A short source/verification note for factual claims, including any
  `[VERIFY: ...]` items.

## Final review

Check that the script fulfills its title and hook promise, that factual claims
are supported, that examples are not mistaken for evidence, and that the
spoken wording sounds natural. Nothing is published by this skill. End with
a copy-ready script and ask: **ship it, or change it?**
