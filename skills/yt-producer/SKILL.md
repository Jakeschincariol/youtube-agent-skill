---
name: yt-producer
description: >-
  Orchestrate the YouTube creator workflow by selecting the existing yt-* skills
  that fit a request, ordering their handoffs, and keeping creator approval in control.
  Use for end-to-end video production, coordinating multiple YouTube tasks, or
  deciding which creator skills to run next.
---

# yt-producer

Coordinate the existing YouTube skills into a clear, evidence-aware workflow. This is a
router and handoff guide, not a replacement for the specialist skills. Select only the
work needed for the creator's request; never run every skill by default.

## 1. Understand the requested outcome

Identify the creator's immediate goal before selecting skills:

- Plan a publishing period or choose the next topic.
- Turn an idea or supplied material into a script.
- Package a video with a title and thumbnail concept.
- Prepare metadata or chapters.
- Review a recording/transcript, identify Shorts, or interpret retention.
- Review channel evidence, compare niche examples, or respond to comments.

Use the material already supplied. Ask only for missing information that materially
changes the route or prevents a reliable deliverable. If the creator asks for a quick
draft, state reasonable assumptions and keep the workflow easy to revise.

## 2. Route by task

| Creator request / input | Skill to use | Required source or boundary |
| --- | --- | --- |
| Weekly or monthly content calendar | `yt-plan` | Planning period, available hours, goals and known assets; state assumptions for missing details. |
| Idea, outline or script | `yt-script` | Topic and intended viewer; ask only for details that materially change the script. |
| Title and thumbnail pairing | `yt-package` | Video promise and supporting source material; do not treat its score as a performance prediction. |
| Description, tags or search query ideas | `yt-seo` | Video, transcript, outline or creator notes; do not invent content, links, metrics or rankings. |
| Transcript-based edit decision list | `yt-edit` | Timestamped SRT, VTT or supported Whisper JSON; suggestions require footage/audio review. |
| Chapter timestamps | `yt-chapters` | Timestamped transcript; invalid or insufficient boundaries must not be fabricated. |
| Short-form clip candidates | `yt-shorts` | Source video or timestamped transcript; preserve context and mark visual/timecode limits. |
| Audience-retention export | `yt-retention` | Compatible YouTube Studio retention export; drops are diagnostic clues, not proven causes. |
| Channel or selected-video audit | `yt-audit` | Public/creator-supplied material and any supplied analytics; state sample, date range and evidence limits. |
| Niche examples or outlier research | `yt-viral` | Collected public video data; compare only eligible same-channel/format cohorts. |
| Supplied comment thread | `yt-comment` | Actual comments; protect private information and flag safety/moderation concerns. |

If a request spans multiple rows, choose the smallest useful set of skills. A request
for a script does not automatically require a calendar, channel audit, competitor
research, or comments review.

## 3. Use practical workflow sequences

These are optional routes, not mandatory production checklists:

### New video from an idea
1. Use `yt-plan` only if the creator wants a schedule, capacity plan, or topic prioritization.
2. Use `yt-script` to develop the approved idea into a script.
3. Use `yt-package` when title and thumbnail concepts are requested or useful.
4. Use `yt-seo` for metadata when the creator supplies enough source material to describe
   the actual video accurately.
5. Use `yt-chapters` only after a timestamped transcript exists and chapters are wanted.

### Existing recording or long-form video
1. Use `yt-edit` for transcript-based edit suggestions when a timestamped transcript exists.
2. Use `yt-shorts` when the creator wants short-form candidates from supplied source material.
3. Use `yt-chapters` when chapters are requested and the transcript supports valid boundaries.
4. Use `yt-seo` for metadata based on the reviewed source material.

### Published-video improvement
1. Use `yt-retention` only when a compatible retention export is supplied.
2. Use `yt-audit` when the creator wants a broader evidence-based review.
3. Use `yt-package` if title/thumbnail packaging is a relevant review target.
4. Use `yt-viral` only when comparable public examples are requested or useful.

### Community response
Use `yt-comment` for supplied comments. Do not route comments through unrelated
production skills unless the creator separately asks for that work.

## 4. Preserve handoffs between skills

Before moving from one skill to another, carry forward only relevant, supported artifacts:

- Creator's stated goal, audience, language/region, format and constraints.
- Approved topic, viewer promise and script version.
- Source identifiers, filenames, transcript excerpts and original timecodes.
- Verified facts and their sources, plus claims still marked for verification.
- Draft title/thumbnail/metadata options and the creator's decisions.
- Known limitations, unresolved questions and the next approval needed.

Keep source facts separate from assumptions, editorial suggestions and heuristic scores.
Do not turn an earlier draft into verified evidence. Do not invent a missing transcript,
recording, thumbnail, analytics export, comment, metric, link or timestamp.

If a specialist skill is unavailable in the current environment, say so and provide its
command or ask the creator to load that skill. Do not claim that it ran or that an
artifact was created.

## 5. Execute in small, reviewable stages

For each selected skill:

1. State the purpose of the stage and the input it will use.
2. Run or hand off to the specialist skill.
3. Return its deliverable and clearly label assumptions, evidence limits and review flags.
4. Ask for creator approval or requested changes before treating a draft as approved.
5. Continue only to the next relevant stage after the required source or approval exists.

Do not ask the creator to approve every internal routing decision. Ask at meaningful
creative or factual decision points, and never silently override a creator decision.

## 6. Safety and publication boundary

- Nothing in this orchestrator uploads, publishes, schedules, edits media, deletes content,
  replies to comments, or changes channel settings.
- The creator retains control of final scripts, edits, packaging, metadata, moderation and
  publication.
- Do not request account passwords, OAuth secrets or other credentials.
- Respect each specialist skill's evidence, privacy, rights and safety limitations.
- If a requested action is outside the available skills, explain the limitation instead
  of implying it was completed.

## 7. Final handoff

Summarize the stages used, artifacts produced, unresolved verification items and the
single next creator decision. If no further stage is justified, say so rather than
adding work to make the workflow appear complete.

End with a concise approval question: **ship it, or change it?**
