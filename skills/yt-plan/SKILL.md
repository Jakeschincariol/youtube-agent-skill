---
name: yt-plan
description: >-
  Build a realistic weekly or monthly YouTube content calendar from the
  creator's available time, existing assets, publishing goals, and constraints.
  Use for "plan my week", "content calendar", "what should I post", or
  "I have no idea what to make next".
---

# yt-plan

A useful content plan fits the creator's real week. Plan around capacity and
existing work; never impose an upload quota.

## Gather only what is needed

1. Read `~/.claude/youtube/voice.md` if it exists. Use it to keep topics,
   formats, and wording consistent with the creator. Do not require three
   videos or block planning if the file is absent.
2. Establish the planning period (week or month), available production hours,
   and any fixed publishing dates or deadlines.
3. Identify work already in progress or assets that can be reused: scripts,
   recordings, long-form videos, transcripts, clips, thumbnails, and ideas.
4. If the creator has not supplied their publishing goal or preferred
   cadence, ask one concise clarification when it would materially change
   the plan. Do not interrogate them for analytics they do not have.
5. Ask about the hours available and existing work together when both are
   missing. If the user wants a quick draft, state reasonable assumptions
   explicitly and make the plan easy to revise.

## Build the plan

- Start with the creator's stated goal and capacity. There is no default
  requirement for one long video, one extra upload, three Shorts, or daily
  posting. A plan may contain one upload, several uploads, or no new upload
  in a week if that is what the available time supports.
- Prefer finishing useful work already underway before adding new production.
  Do not count an idea, an unrecorded script, or an unfinished edit as a
  ready-to-publish asset.
- Reuse long-form footage for Shorts only when a transcript or source video
  exists and the extracted moment works as a self-contained Short. Do not
  invent clips, timestamps, or claim that a clip has been found without
  inspecting the source. Use `/yt-shorts` when the user supplies the source
  material and wants clip candidates.
- Choose publishing dates from the user's stated schedule or supplied channel
  analytics. Do not claim a day or time is optimal without relevant evidence.
  If analytics are unavailable, label proposed dates as practical suggestions,
  not performance-based recommendations.
- Separate production tasks from publication events. Include the work needed
  to make each item publishable: research, outline/script, recording,
  editing, thumbnail, description, review, and scheduling as applicable.
- Estimate effort per item and sum the estimates across the period. Label
  estimates as estimates; do not invent precise durations when the format or
  workflow is unknown. Ask for a missing estimate only if it materially
  changes whether the plan fits.
- Keep the total workload within the hours the creator says they have.
  Account for existing commitments and leave room for review or unexpected
  delays. If the requested output exceeds capacity, show the shortfall and
  propose what to defer rather than silently overbooking.
- For a monthly plan, organize the work into weeks and account for unfinished
  work carried forward. Do not multiply a weekly cadence into a month without
  checking capacity, holidays, deadlines, and production dependencies.
- Never invent metrics, audience insights, results, sources, or content assets.
  Mark unsupported assumptions clearly and leave analytics-based conclusions
  out when the required data is unavailable.

## What to hand back

For each planned item, provide a compact calendar with:

| Publish date / target | Format | Working title or topic | Viewer promise | Asset status | Production effort | Dependencies / priority |
|---|---|---|---|---|---|---|

Use actual dates only when the period and timezone are known; otherwise use
relative day or week labels. Distinguish ready, in progress, and not started.
For a month, group rows by week.

Below the calendar, include:

- Total estimated production hours and the available-hours budget.
- Any capacity gap, assumptions, and dependencies.
- The first item or task to defer if the week goes wrong.
- A small next-action list ordered by what unblocks the most work.

Do not fill empty days just to make the calendar look busy. Explain briefly
when leaving a day or week unscheduled is the sensible choice.

## Final check

Before handing over the plan, verify that the effort total fits the stated
budget, every scheduled publication has a plausible production path, reused
assets actually exist, and no unsupported analytics claim is presented as
fact.

Nothing here publishes. This skill plans; the creator reviews and publishes.
End with a copy-ready plan and ask: **ship it, or change it?**
