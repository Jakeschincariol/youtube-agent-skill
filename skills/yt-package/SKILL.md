---
name: yt-package
description: >-
  Write and lint the title and thumbnail for a YouTube video as one pairing,
  checking the platform title limit, clarity, duplication and readability.
  Use for title ideas, thumbnail text, packaging, or repackaging an existing video.
---

# yt-package

Treat the title and thumbnail as one packaging decision. They should work together:
the title can state the topic or promise while the thumbnail adds a complementary
visual idea, emotion or short phrase. Some wording overlap can be useful for clarity;
avoid repeating the entire message.

## Run

    python3 skills/yt-package/title.py --title "How I Automated a Deployment"
    python3 skills/yt-package/title.py --title "How I Automated a Deployment" --thumb "NO MORE MANUAL WORK"
    python3 skills/yt-package/title.py titles.txt --json

The input file contains one title per line. Add `--thumb` to compare each title
with the same proposed thumbnail text.

## Before you write

1. Read the creator's voice profile if one is available in the current project
   or workspace. Do not assume a Claude-specific file path. If no profile exists,
   ask for examples of the creator's own videos before claiming to have matched
   their voice.
2. Never invent a number, result, credential or source. Use concrete details only
   when they are supported by the video or source material.
3. Keep the title accurate and succinct. Put the most important words near the
   beginning. Choose a searchable title or an intriguing title based on the
   intended audience and discovery context.

## What the checker validates

- YouTube's title limit is 100 characters. A title over that limit is an error.
- Titles over 70 characters receive an advisory to consider shortening and
  front-loading the subject. This is an editorial prompt, not a platform limit.
- Repeated all-caps words, generic adjectives, substantial title/thumbnail
  duplication and dense thumbnail text are suggestions to review, not automatic
  evidence that a package will perform poorly.
- The score is a transparent editorial heuristic. It is not a CTR estimate,
  search ranking, or prediction of views. A high score cannot verify factual
  accuracy; the creator must check that the package represents the video.

YouTube says titles should be accurate and succinct, with important words early.
It also recommends limiting ALL CAPS and emoji. Display truncation varies across
devices and surfaces, so this skill does not present fixed 40- or 60-character
cutoffs as platform rules.

## Write ten, keep two

Generate a range of distinct, accurate title/thumbnail concepts. Use the checker
to identify obvious issues, then show the creator a small shortlist with the
trade-offs. Do not select a winner solely by the heuristic score.

When available, use YouTube Studio's native title and thumbnail A/B testing to
compare up to three variants. The native experiment determines a winner using
watch-time share, not this utility's score.

## The gate

Nothing here publishes. This skill writes and you publish. Ask the creator to
review factual accuracy, voice and packaging before use.
