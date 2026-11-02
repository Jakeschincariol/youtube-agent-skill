# The YouTube agent skill

Eleven Claude skills that run a YouTube channel. Free, MIT, no signup, no API key, nothing to
connect.

One of them writes your script off 21 hook formulas and scores the hook before you waste a take on
it. One lints the title and the thumbnail as a single pairing, because writing them separately is
why half of your click surface says the same thing twice. One reads your audience-retention export
and tells you the exact second people left and what you were saying when they did. One turns a
transcript into an edit decision list. One finds the Shorts already hiding inside a long video. One
goes and finds what is working in your niche and ranks it by how far each video beat its own
channel, not by how big the channel is.

**Nothing gets published until you do it.** These skills write. You upload.

## Install

Paste this into Claude:

```
https://github.com/Jakeschincariol/youtube-agent-skill

Install this skill, then confirm /yt-script works.
```

Or do it yourself, in Claude Code:

```bash
git clone https://github.com/Jakeschincariol/youtube-agent-skill.git
cp -r youtube-agent-skill/skills/yt-* ~/.claude/skills/
```

Or as a plugin:

```
/plugin marketplace add Jakeschincariol/youtube-agent-skill
/plugin install youtube-agent
```

Project-local instead of global: copy the same folders into your repo's `.claude/skills/`. No Claude
Code at all? Paste any single `SKILL.md` at the top of a chat and it runs as a mode. You lose the six
Python tools, which is most of the point of `/yt-script`, `/yt-retention` and `/yt-edit`, but the
rest works.

Then spend ten minutes on [`templates/voice.md`](templates/voice.md). Copy it to
`~/.claude/youtube/voice.md` and fill it in, or send Claude three of your own videos and say "write
my voice.md from these". Every skill reads that file. It matters more here than anywhere else,
because you have to say the words out loud.

## The eleven

| command | what it does |
| --- | --- |
| `/yt-script` | One idea into a script. Five hooks off [21 formulas](skills/yt-script/hooks.json), scored, then the spoken script with the retention beats marked. |
| `/yt-package` | Title and thumbnail as one pairing, linted for truncation, duplication and vagueness. |
| `/yt-edit` | A transcript into an edit decision list: dead air, filler cues, retakes, with timecodes. |
| `/yt-comment` | Comments triaged into four groups, with safety flags and evidence-aware replies in your voice. Suggests a pin when warranted. |
| `/yt-plan` | A weekly or monthly content calendar sized to your available hours, existing assets, and publishing goals. |
| `/yt-viral` | What is working in your niche, ranked by multiple over each channel's own median. |
| `/yt-retention` | Your retention export read properly: hook leak, the cliffs, the slide, and what to change. |
| `/yt-shorts` | Self-contained clip candidates with source timecodes, context checks, accurate hooks, and vertical-framing notes. |
| `/yt-seo` | Accurate titles, descriptions, useful tags, and evidence-labelled candidate search queries—without ranking promises. |
| `/yt-chapters` | Chapters from a transcript, validated against YouTube's own rules so they render. |
| `/yt-audit` | The whole channel, ending in ONE fix rather than twenty. |

## The six tools

Every one of these runs on a clean Python 3 with no dependencies. They are the reason the skills are
not just prompts.

```bash
python3 skills/yt-script/hookscore.py --hook "one line"        # 5-property hook panel
python3 skills/yt-package/title.py --title "..." --thumb "..." # title + thumbnail linter
python3 skills/yt-edit/deadair.py transcript.srt               # edit decision list
python3 skills/yt-chapters/chapters.py transcript.srt          # validated chapters
python3 skills/yt-retention/retention.py retention.csv         # where they left, and why
python3 skills/yt-viral/swipe.py collected.json --min 2.0      # outliers by own-channel multiple
```

## The fine print

The part most packs leave out.

**It does not publish.** YouTube's Data API would allow it with your own OAuth, which makes this
pack different from the LinkedIn and Instagram ones, where posting is not available at all. It is
still not built here: every skill ends in a block you copy and a question — ship it, or change it?
Anything that claims to run your channel unattended should be read with that distinction in mind.

**`hookscore.py` is an editorial heuristic, not a predictor.** It applies fixed keyword and
length rules to five writing criteria. The repository does not include a validation dataset or
methodology that would support claims about predictive accuracy. A score is a prompt for editorial
review, not evidence that a hook will improve views, click-through rate, watch time, or retention.

**The formula classifier is about the words, not the result.** When `/yt-viral` says a title used
The Statistic, that is a judgement about the title you can see, not a claim about why the video got
its views.

**`/yt-viral` reads, it does not scrape.** Public listings only. It never logs in as you and never
touches your credentials.

**Tags barely matter** and this pack says so instead of selling you a tag generator.

**Nothing invents a number.** If a skill wants a figure it does not have, it asks you for it or
writes the line without it.

## Licence

MIT. Use it, change it, ship it.

## Install in Google Antigravity

The skills use the open `SKILL.md` format and can also be loaded by Google Antigravity.

On Windows PowerShell, clone the repository and copy the skill folders into the global skills directory:

```powershell
git clone https://github.com/chandra0000/youtube-agent-skill.git
New-Item -ItemType Directory -Force "$HOME\\.gemini\\config\\skills" | Out-Null
Copy-Item ".\\youtube-agent-skill\\skills\\yt-*" "$HOME\\.gemini\\config\\skills\\" -Recurse -Force
```

If the repository is already cloned, run the copy command from its parent directory, or change into the repository and use:

```powershell
Copy-Item ".\\skills\\yt-*" "$HOME\\.gemini\\config\\skills\\" -Recurse -Force
```

Restart Antigravity or start a new session, then ask it to list the available skills and test one skill with a small prompt. Skill discovery confirms that the instructions are visible; it does not by itself validate the Python utilities or every workflow.

The global path above is the path verified in the Antigravity CLI setup used for this repository. If a future Antigravity release changes its supported skills directory, follow the current Antigravity documentation.

The six Python utilities require Python 3 and use only the standard library. They can be run directly from the repository; no third-party Python packages are required.
