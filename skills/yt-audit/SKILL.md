---
name: yt-audit
description: >-
  Review a YouTube channel or supplied video set using available public,
  creator-provided, and analytics evidence. Identify strengths, limitations,
  and the highest-priority actionable improvement. Use for "audit my channel",
  "review my videos", or "why isn't my channel growing".
---

# yt-audit

A useful audit distinguishes observations from explanations. It should help the creator decide
what to investigate or improve next—not pretend that a small set of public signals explains an
entire channel or guarantees growth.

End with one clearly prioritized next action when the evidence supports one. If the evidence is
too thin to rank issues confidently, say what is missing and give the safest useful next step.

## 1. Establish scope and evidence

Before auditing, establish what the creator wants reviewed: the whole channel, a recent upload
cohort, selected videos, packaging, openings, publishing rhythm, or performance analytics.

Use only material actually available in the current task or workspace, such as:

- Public channel and video pages that can be accessed.
- Creator-supplied video URLs, titles, thumbnails, scripts, transcripts, and upload dates.
- YouTube Studio exports or screenshots supplied by the creator, including impressions, click-
  through rate, watch time, audience retention, traffic sources, and returning viewers.
- Creator goals, target audience, language/region, production constraints, and intended format.

State which sources and date range were reviewed. Distinguish public observations from private
YouTube Studio analytics. Do not imply access to a creator's Studio account, private analytics,
unlisted videos, or unavailable media. Ask for an export or relevant details if they are needed.

Do not require a fixed number of videos or a voice-profile file. Read a creator voice profile only
if one is supplied or accessible in the current workspace. Never create or save a profile unless
the creator explicitly asks.

Never invent metrics, results, audience demographics, sources, upload dates, or explanations.
Label estimates and inferences. If a claim cannot be verified, omit it or flag it for creator review.

## 2. Review in evidence-aware layers

Review only the layers supported by the supplied material. A full channel audit does not require
every layer to be available.

### A. Channel and video positioning

- Review the available titles and topics as a set. Look for clear audience promises, repeated
  subjects, and whether the channel's stated focus matches the videos reviewed.
- State the sample size and selection method. If fewer than ten relevant uploads are available,
  review what exists; do not imply it is a representative ten-video sample.
- Avoid declaring that a channel has a "format problem" or lacks a niche from titles alone.
  Treat patterns as hypotheses to validate with the creator and audience data.

### B. Titles and thumbnails

- Review titles for accuracy, clarity, specificity, and consistency with the actual video.
- Inspect thumbnails visually only when the image itself is available. A title list or transcript
  cannot establish thumbnail readability, contrast, or feed-size legibility.
- If thumbnails are available, assess them at realistic small display sizes and explain what
  remains legible. Do not claim that a visual feature caused a CTR result without suitable
  experiment or analytics evidence.
- Use `../yt-package/title.py` when available as an editorial linting aid. Its score is a
  heuristic, not a prediction of clicks, views, or search placement.

### C. Video opening and content delivery

- Review the opening of the supplied video or transcript. State whether the review was based on
  video, audio, transcript, or creator notes.
- If a transcript alone is supplied, do not make claims about visual pacing, editing, sound,
  facial expression, or on-screen proof.
- Use `../yt-script/hookscore.py` only as an editorial heuristic. Do not present its score as
  measured retention or proof that viewers leave in the opening.
- Connect an opening critique to the video's actual promise and delivery. Avoid universal claims
  that a fixed number of seconds is where most channels lose viewers.

### D. Publishing rhythm

- Summarize only the upload dates and period that are actually available.
- Describe observed gaps or bursts without asserting a universal best posting frequency.
- Do not claim inconsistency caused poor performance unless the available evidence supports that
  relationship. Consider production capacity and the creator's stated goals.

### E. Analytics and audience retention

- Use `/yt-retention` when a compatible retention export is supplied and the creator wants a
  retention review.
- Identify the metric, date range, video cohort, and relevant comparison baseline. Do not mix
  different formats, traffic contexts, or periods without explaining the limitation.
- A retention curve can show where viewers stopped watching; it does not by itself prove why.
  Pair dips or spikes with the content at those timestamps before suggesting explanations.
- Do not infer CTR, impressions, traffic sources, returning viewers, or audience demographics
  from public view counts or from a transcript.

## 3. Separate findings from hypotheses

For each important finding, provide:

1. **Observation:** what the reviewed material directly shows.
2. **Evidence:** the source, sample, metric, or timestamp supporting it.
3. **Interpretation:** what the observation may mean, labelled as an inference where appropriate.
4. **Confidence or limitation:** what the sample cannot establish and what would validate it.

Do not confuse correlation with causation. Do not claim that a title, thumbnail, schedule, hook,
or editing choice caused a performance change without appropriate comparative evidence, such as
a relevant controlled experiment or sufficiently contextualized analytics.

## 4. Prioritize the next action

- Identify one highest-priority action when the evidence supports a clear choice.
- Explain why it outranks the other observed opportunities, what the creator can do this week,
  and what signal would indicate whether the change helped.
- Prefer a specific, feasible experiment over a sweeping channel rebrand.
- If no issue can be ranked confidently, state that plainly and recommend the smallest useful
  evidence-gathering step instead.
- Preserve strengths that are directly visible in the material. Do not manufacture three positives
  or generic praise to fill a quota.
- Say what not to change yet only when there is a reason grounded in the audit.

## 5. Output

Provide a concise, reviewable report:

- **Scope and sources:** what was reviewed, sample size, date range, and what was unavailable.
- **What is working:** specific strengths supported by evidence; omit this section if none can be
  established.
- **Findings:** the most relevant observations, with evidence and limitations.
- **Priority:** one next action, or the evidence needed before choosing one.
- **This week's experiment:** the concrete change and the signal to monitor.
- **Creator checks:** factual, strategic, or contextual questions that only the creator can answer.

Keep recommendations proportional to the evidence. The creator decides whether to implement them.

## The gate

Nothing here publishes or changes the channel. This skill produces an audit and recommendations;
the creator reviews and acts on them. End with a clear invitation to approve the proposed next
action or request a revision, without implying that any change has already been made.
