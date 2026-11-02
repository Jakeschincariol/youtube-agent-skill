---
name: yt-seo
description: >-
  Prepare accurate YouTube titles, descriptions, tags, chapters, and search
  query research for a supplied video. Use for "write my description", "tags",
  "SEO", "help this video get found", or "nobody is finding this".
---

# yt-seo

Prepare metadata that accurately explains the video and helps the intended viewer recognize
whether it answers their query. Metadata can improve relevance and clarity; it cannot guarantee
rankings, impressions, views, or a position in search.

YouTube search considers relevance, engagement, and quality. Relevance can include how well the
title, tags, description, and video content match a query. Search results are personalized and
competition and viewer response matter, so do not promise that a video will "win" a query.

## 1. Understand the video and audience

Before drafting:

1. Use the supplied video, transcript, outline, title, or creator notes. State what source material
   was actually reviewed. If the video or transcript is unavailable, do not pretend to know its
   contents; ask for the minimum material needed to write accurate metadata.
2. Identify the intended viewer, the video's actual subject, its specific value or answer, and
   relevant language/region when known. Do not infer audience demographics or search intent without
   evidence.
3. Read an available creator voice profile if supplied or accessible in the current workspace.
   If none exists, follow the user's instructions and supplied examples. Do not require three videos,
   block the task, or create/save a profile unless explicitly requested.
4. Separate verified facts from opinions, estimates, and claims needing confirmation. Never invent
   statistics, credentials, product features, citations, links, timestamps, results, or guarantees.
5. If a factual or time-sensitive claim matters, ask for a source or verify it using trustworthy,
   current sources when browsing is available. Attribute external facts where appropriate. If
   unverified, omit the claim or mark it clearly for creator review.

Ask only for missing information that materially changes the metadata. Do not turn the task into
a keyword-research exercise when the user simply needs a usable description.

## 2. Search intent and query research

When search research is requested or useful:

- Start with the viewer's likely problem or question, not a list of high-volume keywords.
- Draft a small set of distinct query formulations: the main topic, a specific question, and a
  relevant long-tail variation where supported by the video's content.
- Distinguish researched queries from hypotheses. Use YouTube Studio's Research/Analytics tools
  or other suitable keyword sources only when data is available; report the source and date.
- Do not invent search volume, difficulty, competition, ranking position, traffic estimates, or
  search intent. If no keyword data was provided or retrieved, call the queries "candidate
  searches", not proven opportunities.
- Do not claim that the video will rank first or "win" a query. A query fit is an editorial
  relevance check, not a ranking prediction.
- Check that the video genuinely answers the query. Do not force unrelated phrases into metadata.

## 3. Title alignment

Coordinate with `/yt-package` when title and thumbnail concepts are also being developed.

- Keep the title accurate, clear, and representative of the actual video.
- Put the central topic or promise early when natural; do not awkwardly repeat keywords.
- The current YouTube title field limit is 100 characters. Validate against the current official
  upload guidance if platform limits are material to the task.
- Do not imply that matching an exact query phrase is mandatory or that title wording alone
  determines search placement.
- Avoid misleading, sensational, or unsupported claims. A title must not promise an answer,
  outcome, demonstration, or result the video does not deliver.

## 4. Description

Draft a unique description for this specific video.

- Use the opening lines to explain what the video covers and why the intended viewer may find it
  useful. These lines are prominent before the viewer expands the full description on some
  surfaces, but display varies by device and context; they are not the only text that matters.
- Naturally include one or two central topic terms in the title and description when they accurately
  describe the video. Do not stuff exact-match phrases or repeat keywords unnaturally.
- Explain the actual scope, important steps or topics, intended audience, prerequisites, and
  limitations where relevant.
- Include only links, resources, products, credits, and calls to action that the creator supplied
  or that have been verified. Never invent URLs or imply a resource is attached when it is not.
- Add chapters only when valid timestamps and meaningful section titles are supplied or can be
  grounded in the transcript. Use `/yt-chapters` when appropriate; do not fabricate timestamps.
- Add relevant playlist links, collaboration credits, and other useful context when available.
- Keep within YouTube's current description field limit (currently documented as 5,000 characters);
  verify official guidance if a strict limit is material.
- Review how the opening and links appear in search, watch-page, and mobile contexts when possible.

Do not assert that the first two lines are the only lines people read or that they are guaranteed
to become the search snippet. YouTube recommends using the first few lines to describe the video
because viewers see them first.

## 5. Tags, without tag stuffing

Tags are a minor discovery signal. YouTube says they are primarily useful for common misspellings
and otherwise play a minimal role in discovery.

- Suggest tags only when they serve a clear purpose: common misspellings, alternate spellings,
  abbreviations, or ambiguous names that genuinely describe the video.
- Do not impose an arbitrary quota such as 15 tags. A short list or no tags may be the right answer.
- Do not use unrelated trending terms, competitor names, repeated keyword variants, or long
  keyword strings to manipulate discovery.
- Keep tags in the tags field; do not stuff them into the description.
- Explain briefly why each non-obvious tag is included. If there are no useful tags, say so.

## 6. Final metadata review

Before handing off, check:

- The title and description accurately match the supplied video material.
- The opening description lines make the topic and viewer value clear.
- Any query suggestions are supported by the video's actual content.
- Tags are limited to useful spelling/disambiguation cases, not arbitrary volume.
- Links, chapter timestamps, names, numbers, and claims are grounded.
- The title and description fit current platform field limits when verified.
- No ranking, traffic, CTR, or view outcome is promised.

## 7. Output

Provide a copy-ready package with:

1. Recommended title, plus alternatives only when useful.
2. A complete description with verified links and valid chapters if supplied.
3. A concise tag list, or an explanation that tags are unnecessary.
4. A small list of candidate viewer searches, clearly marked as researched or unverified hypotheses.
5. A brief accuracy/source note and any items the creator must verify.

Nothing here uploads or publishes. The creator reviews and enters the metadata in YouTube Studio.

## Official references

Check these sources when platform behavior or limits are material; they may change:

- [Tips for video descriptions](https://support.google.com/youtube/answer/12948449)
- [How YouTube Search works](https://support.google.com/youtube/answer/16090438)
- [Add tags to your YouTube videos](https://support.google.com/youtube/answer/146402)
- [Upload YouTube videos](https://support.google.com/youtube/answer/57407)
