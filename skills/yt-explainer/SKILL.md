---
name: yt-explainer
description: >-
  Write a narrated "weird science" explainer from a topic - shock open,
  question, numbered reasons, twist, human angle, strangest case, reflective
  close - with an illustration prompt for every scene and a scored hook. Use
  for faceless or voice-over channels, animated explainers, "why do animals...",
  "the science of...", "make a video about [strange fact]", or any narrated
  video script.
---

# yt-explainer

A narrated explainer the viewer finishes, in the shape that already works on this channel. Built
on `/yt-script`: same tools, same gate, a fixed structure for voice-over.

```bash
python3 ../yt-script/hookscore.py --narrated hooks.txt   # always --narrated for voice-over
python3 ../yt-package/title.py --title "..." --thumb "..."
```

## Before you write

1. Read `~/.claude/youtube/voice.md`. No file? Use
   [`templates/voice.curio-explorer.md`](../../templates/voice.curio-explorer.md) as the default and
   say so.
2. **Research before writing.** Every claim in this format is a fact someone will check in the
   comments. Find the source for each one. If you cannot find it, cut the line - never round a
   number up, never write "scientists say" without knowing which ones.
3. Pick the **anchor example**: the single most visual, most surprising case in the topic. It opens
   the video AND comes back later (the callback). For cannibalism that was the sand tiger shark.

## The shape

Times are for a ~5 minute video at ~150 words per minute (about 750 words). Scale to the length asked.

| Beat | Time | Job |
|---|---|---|
| **1. Shock open** | 0:00-0:07 | The anchor example in one flat sentence, then flip it: "That's not a mistake. It's a survival strategy." |
| **2. The question** | 0:07-0:12 | The title, said out loud as a question. |
| **3. Scale + promise** | 0:12-0:22 | One verified number that proves it is not a fluke, the count of reasons, and a teaser for the strangest case. **Nothing else.** No "don't worry", no "today we answer", no "let's start". |
| **4. Reasons 1-N** | 0:22-~2:40 | "Reason number one." then a one- or two-word label, said alone. Each reason: the rule, one named example, one line of why it works. Bust one myth along the way. |
| **5. Callback** | inside the last reason | Return to the anchor example with the part you held back. |
| **6. The twist** | ~2:40 | "Now a twist." If it is so useful, why isn't it everywhere? The cost side. |
| **7. The human angle** | ~3:00 | "Now, humans." Real cases with context and respect, never shock for its own sake. |
| **8. Strangest case** | ~3:40 | "Now for the strangest case of all." The teaser from beat 3, paid off in full. |
| **9. Recap** | ~4:40 | The N reasons in one breath. |
| **10. Close** | last 15s | A line of wisdom, then a question the viewer takes away. No subscribe pitch. |

The spoken signposts ("Reason number two", "Now a twist", "Now, humans") are not decoration:
`/yt-chapters` reads them, so the chapters write themselves.

## Writing rules

- Sentences under 12 words. One idea per line. It is read aloud.
- Every reason gets a **named** example (a species, a place, a year), not "some animals".
- Plant the strangest case in beat 3 and pay it off in beat 8. That open question is what carries
  viewers through the middle.
- Treat dark topics as science, not gore. Respect for human cases is part of the voice.

## Scenes

Mark every line or pair of lines with a scene for the illustrator or image model:

```
[SCENE 03 | 0:12-0:16] Hand-drawn doodle, cream background, soft pastels. A sand tiger shark
seen side-on with two glowing womb chambers, one embryo in each, one showing a tiny tooth.
Mood: curious, slightly ominous - not cute.
```

- Keep the channel style in every prompt (copy it from `voice.md`), so images match across the video.
- **Match the mood to the words.** A line about something grim gets an image with a hint of tension
  (a tooth, a shadow, a worried face), not a smiling mascot.
- Aim for a new scene every 4-6 seconds.

## What to hand back

1. Two hooks (beats 1-3) with their `--narrated` panels.
2. Three title + thumbnail-text pairings from `title.py`, best first.
3. The full script, beat by beat, every line with its `[SCENE]`.
4. Word count and runtime at 150 wpm.
5. A source list: one line per factual claim, with where it comes from.
6. The chapter block, from the signposts.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
