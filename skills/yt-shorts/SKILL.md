---
name: yt-shorts
description: >-
  Identify self-contained short-form moments in a supplied long-form video or
  transcript, then prepare accurate clip briefs and draft packaging. Use for
  "cut this into shorts", "clip this", "repurpose this video", or "what should I clip".
---

# yt-shorts

Find moments that make sense to a viewer who has not watched the full video. A high-energy
sentence is not automatically a good clip: the moment must preserve the original meaning,
provide enough context, and deliver a complete payoff.

This skill proposes clips and drafts their packaging. It does not edit, render, upload, schedule,
or publish video.

## 1. Confirm the source and constraints

- Use the supplied transcript, source video, or both. If only a transcript is supplied, be clear
  that visual composition, speaker changes, audio quality, and exact cut points cannot be verified.
- Preserve the source filename or video identifier and transcript timecodes. Never invent
  timestamps, quotations, scenes, reactions, or visual details.
- Check that timestamps are parseable, ordered, non-negative, and within the known source
  duration. If duration or timecode origin is unknown, flag it instead of claiming validation.
- Ask for the target platform or duration only when it materially changes the requested output.
  Treat any requested duration as a constraint to verify, not as permission to pad or distort a clip.
- Do not hard-code a supposedly universal platform duration limit. If the user asks for current
  platform eligibility or a strict maximum, verify the current official platform guidance when
  browsing is available; otherwise label the limit unverified.

## 2. Select candidate moments

Find candidate spans that have:

1. **A standalone opening:** the first spoken line can be understood without an earlier sentence,
   missing question, unexplained pronoun, or unseen setup.
2. **A clear development:** a useful explanation, demonstration, story turn, contrast, or proof
   follows the opening.
3. **A satisfying ending:** the moment reaches a complete point rather than cutting off a sentence,
   caveat, or essential qualification.
4. **Faithful meaning:** the cut does not reverse the speaker's intent, remove a necessary
   disclaimer, imply a false cause-and-effect relationship, or turn speculation into fact.
5. **Clip value:** it teaches, demonstrates, entertains, or resolves a specific viewer question.

Prefer a concise complete thought over an arbitrary target length. A 20–55 second span can be a
useful initial search window, not a platform rule or a required duration. Expand or shorten only
when the context and payoff remain intact.

Do not manufacture five candidates. Return only defensible candidates; if fewer than five qualify,
say how many were found and why the remaining source material did not pass.

Rank candidates using explicit editorial reasons (clarity, completeness, usefulness, distinctiveness,
and edit feasibility). Do not imply that this ranking predicts views, retention, virality, or reach.

## 3. Candidate review

Show a shortlist before writing all clip packages. For each candidate include:

- Candidate number and concise working title.
- Exact source in/out timecodes and calculated duration, if the source timing supports it.
- The first spoken line, quoted exactly from the transcript.
- One-sentence summary of the viewer payoff.
- Any missing context, visual dependency, audio concern, or factual caveat.
- Why it passed the standalone-context and complete-ending checks.

If exact boundaries are uncertain because transcript cues are coarse, label them approximate and
request source-video review. Do not present cue boundaries as frame-accurate edit points.

## 4. Package each approved clip

For each candidate the creator selects, provide:

- **Original clip:** source identifier, in/out timecodes, duration, and verbatim transcript excerpt.
- **Context check:** explain whether the clip stands alone; include any caveat that must remain.
- **New opening:** draft a truthful first line suited to a viewer without the long-video context.
  It may rephrase the idea but must not add facts, stronger certainty, or a promise the clip does
  not fulfill.
- **On-screen text:** a short readable overlay for the opening. It can complement the spoken line,
  but must not contradict it or imply unsupported results.
- **Payoff / ending:** identify the exact line or moment that completes the idea. Do not force a
  loop if it makes the message confusing or misleading.
- **Vertical framing note:** state what needs to remain visible, what may be cropped from 16:9,
  and whether the source appears to need reframing, captions, b-roll, or a new shot. If the video
  was not inspected, label this as a recommendation, not an observation.
- **Caption and CTA:** optional, relevant, and consistent with the creator's intent. Do not invent
  links, offers, dates, product features, or audience outcomes.
- **Review flags:** list unresolved context, rights, privacy, safety, music, or factual issues.

Where useful, run the proposed opening through the sibling editorial heuristic:

```bash
python3 skills/yt-script/hookscore.py --hook "Draft opening line"
```

Describe its result only as a wording heuristic. It is not a performance prediction and should
not override accuracy or natural delivery.

## 5. Accuracy and rights safeguards

- Keep the original speaker's meaning, uncertainty, qualifications, and attribution.
- Do not splice separate statements in a way that implies they were one continuous statement.
- Do not fabricate subtitles, quotations, metrics, testimonials, or visual evidence.
- Flag third-party footage, music, images, private information, and identifiable people for
  appropriate permission and privacy review. Do not declare a clip legally cleared.
- Do not recommend removing safety-critical context or disclosures merely to make a stronger hook.
- Distinguish what the transcript proves from what requires watching or listening to the source.

## 6. Final handoff

Deliver the shortlist first. After the creator chooses, provide a copy-ready clip brief for each
approved moment and a checklist of unresolved edit decisions. The creator reviews the cut and
handles all editing and publishing.

End with: **Which clip should I package first, or what should I change?**
