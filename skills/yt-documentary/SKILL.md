---
name: yt-documentary
description: >-
  Plan and produce a YouTube documentary or explainer from a topic, script,
  narration and footage using the local Flow MCP tools. Use for documentary
  video production, visual storyboards, Flow scene generation, narration,
  assembly or captions; automatically apply the user's saved documentary
  visual standards to every new project. Does not require an Anthropic API key
  or call an Anthropic API.
---

# yt-documentary

Turn a topic, script and optional voice recording into a reviewed documentary
video. The host assistant directs the story; the skill makes no separate
Anthropic API calls. Flow MCP drives Google Flow for generated visuals,
narration, assembly and captions. Pexels is a separate, optional source for
real stock footage and photos.

This skill does **not** bundle or install Flow MCP. It does not call an
Anthropic API, use an `ANTHROPIC_API_KEY`, or publish anything. Flow must
already be connected as an MCP server in the assistant. If its tools are
unavailable, do not pretend to run them: provide the scene plan and say that
Flow MCP must be connected to generate the video. Setup instructions are in
the [Flow MCP guide](https://github.com/GTAI-1/flow-mcp).

## What to preserve

- Preserve the user's edit, source media, interview footage and narration.
  Never replace or overwrite originals; make new outputs in the Flow project.
- Match each visual to the specific narration it illustrates. Keep interview
  and evidence footage visible when it is central to the story.
- Do not invent facts, quotations, statistics, sources or historical details.
  Mark uncertainty and distinguish generated reconstructions from real
  evidence. Use maps, dates and factual labels only when supported by reliable
  sources.
- Treat crime, tragedy and other sensitive subjects respectfully. Avoid
  sensationalized reenactments or gratuitous imagery.
- Do not publish or delete project assets. `flow_trash` is destructive and
  requires a separate, explicit user request and confirmation.

## Documentary visual standards

Treat the user's standing brief below as a production requirement for this and
all future documentary projects, not an optional style suggestion. Apply it
automatically at project start without waiting for the user to repeat it.

> حلل جميع المشاهد بدقة  من المفروض تمشي هلى هذا المنهاج فيديوهات و صور حقيقية و ارشيفية و ان لم تجد بعضها تولدها و ايضا الاساعانة بدراسات علمية و تضعها في قوالب احترافية و خلفيات مميزة و بطاقات معلومات مع كتابة متحركة للمعلومات ، خرائط حقيقية و ايضا مولدة بما يتناسب مع الستايل باسلوب مميز ، كتابات مهمة بالوان متناسقة ، صور الرشيفية حقيقية ، مقاطع و صور حسب الكلام و ليست عشوائية ، تعرف متى تستدعي كل شيء في الوقت المناسب ، جرافيكس ، انتقالات ، ستوك فوتايج ، تماما مثل في الصور للفيديو الخاص بي انتقالات كما في الوثائقيات الاحترافية مدروسة مؤثرات بصرية و صوتية متناسقة مع الكلام و المشاهد ، تحديد و تركيز على العناصر المهمة ، زوم احترافي ، خطوط و قوالب احترافية متحركة ، كل شيء محسوب و عندما لا تستطيع تنفيذ شيء بالحرف الواحد قم بكتابة اكواد احترافية للوصول الى ذلك الشكل ، هذه المهارات من المفروض موجودة في السكيل و لا يجب تذكيرك بها في كل مرة ، تحليل الكلام بدقة و معرفة المعنى ليسهل جلب الافكار في المونتاج و سهولة التطبيق ، كل شيء يجب ان يكون محسوب و ليس عشوائي

Apply it as this scene-by-scene checklist:

- For every long-form documentary, build a timestamped coverage ledger before
  editing: map every spoken sentence and distinct idea to its exact narration
  start/end, exact words, and one or more matching visual beats. Use trusted
  word timings where available; split a sentence when its meaning changes.
  After assembly, record the timeline clip ID(s) covering each row and verify
  that their intervals overlap the words. One clip may cover adjoining words
  only while the same idea remains active. Leave no narration uncovered and no
  unexplained gaps or placeholder holds.
- Analyze the narration for its literal meaning, context, factual claims,
  emotional beat and important objects or places before choosing visuals.
  Record the exact narration range and the reason each shot belongs there.
  Never use unrelated or interchangeable filler: footage, photographs,
  graphics and effects must illustrate the words at the moment they are
  spoken.
- Match each scene to the exact spoken idea, not merely the topic: confirm
  that the source depicts the named subject or action, or is clearly justified
  context for it. Avoid repeating a scene or source shot; find distinct,
  reliable alternatives when available. Reuse only for deliberate continuity,
  a necessary comparison, or when no credible, relevant alternative exists.
  Never replace repetition with unrelated imagery just to make the edit look
  varied.
- Prefer relevant real footage and genuine archival photographs or video.
  Research and use scientific studies and reliable primary sources for
  factual claims. Record source, date, location, attribution and license.
  Display credits as small plain text along the bottom of the image (18 px at
  1920×1080, scaled proportionally at other resolutions), without a frame,
  background, panel, box or border; use subtle shadow only when needed for
  contrast.
- When a specific visual cannot be found, choose deliberately between a
  licensed stock asset, a clearly labeled generated reconstruction, or a
  coded explanatory graphic. Generate only to fill a real visual gap or make
  an abstract idea understandable; never pass generated imagery off as
  archival evidence.
- Build real maps from verified geographic data. A stylized or generated map
  must still reflect verified geography; never trust an image model to invent
  borders, routes, scale or place labels. Design maps, studies and other
  evidence graphics to match the documentary's established visual style.
- Default to full-frame relevant evidence, photographs or illustrations and
  only brief emphasis words when they clarify the narration. Use split layouts
  and information cards only when presenting a factual statistic or quantified
  comparison, not as a routine scene treatment. When a statistics card is
  warranted, use the project's deep cobalt/navy blueprint ground, fine
  low-contrast grid, bold readable Arabic type, pale cyan structure and
  restrained amber/gold emphasis. Keep real footage natural; do not put a
  persistent frame, border or corner-registration marks around the whole
  video. Any useful frame or grid belongs inside a supporting graphic.
- Animate concise, important text with deliberate timing; use legible Arabic
  typography and consistent hierarchy. Still photographs and illustrations
  receive a subtle 3–4% zoom with smooth, soft easing and minimal pan by
  default, provided the move does not crop or obscure important evidence.
  No still image or unchanged composition may be held for more than 8 seconds
  by default; a subtle zoom by itself does not count as a new visual beat.
  Preserve a precisely bounded, user-approved locked section unchanged when
  the user explicitly requires it, document that exception, and do not extend
  it to other sections. Split all other longer narration into distinct,
  relevant shots or use verified, licensed moving footage. "Soft" means
  smooth easing, not blur: do not add blur or soft-focus unless explicitly
  requested. Keep graphic text separate from generated media so wording and
  facts remain accurate and editable.
- Do not add full-sentence subtitles by default. Keep emphasis words brief and
  free-standing. For the word “مرعب”, use a red stamp in clear negative space
  and one restrained impact sound; never cover an animal, a person, or
  evidence.
- Never display the name of any generation model, provider or tool in the
  video. Identify every generated image or video with exactly “مشهد تمثيلي”.
  Keep any real scientific citation separate on the bottom source line, and
  never present a reconstruction as archival evidence.
- Plan stock footage, stills, maps, graphics, transitions, focus cues and
  controlled zooms against the narration and shot changes. Use visual and
  sound effects only when they clarify or reinforce the specific scene; sync
  them thoughtfully with speech and visible action. Vary pacing intentionally
  and direct attention to the relevant subject rather than decorating every
  shot.
- Calculate scene timing, holds, transitions, text entrances and sound cues
  rather than applying them randomly. If a desired visual cannot be made
  directly with available tools, implement it with clean, editable code and
  validate the result in the actual render.

## Workflow

### 1. Gather the brief

Identify the topic, audience, language, target platform/aspect ratio, runtime,
script, narration and any existing footage, music, brand assets or edits. Reuse
an existing script and media when supplied. If only a topic is provided, draft
a fact-conscious script and scene outline before generating media. For a
YouTube script, use `yt-script`; for an edit decision list from a recording,
use `yt-edit`.

Ask only for missing decisions that materially affect the result. Do not
silently assume a factual claim, a narration voice, or a spending limit.

### 2. Check Flow before production

Call `flow_status` first. Confirm that Flow is signed in, a project is open,
and note the available plan, credits and output path. If setup is incomplete,
stop generation and direct the user to the Flow MCP setup guide; do not ask for
an Anthropic key.

If a voice recording exists, use `flow_transcribe` for word-level timings.
Check uncertain names, numbers and Arabic wording against the supplied script
or audio rather than silently correcting them.

### 3. Direct the scenes

Make a concise scene plan before rendering. For long-form work, also prepare a
coverage ledger and a chapter-by-chapter template matrix. The ledger must
account for every spoken sentence and distinct idea across the full runtime;
the matrix must show where each relevant visual skill or template is used.
Do not confine templates to the opening, and do not force a template where it
would not clarify the narration.

| Field | Include |
|---|---|
| Scene | Sequential number and narration beat |
| Purpose | The fact, emotion or question the scene carries |
| Visual | Exact asset, subject and action; source in/out or frame; identify direct evidence, context, stock, illustration or reenactment |
| Framing | Wide, medium, close-up or detail; camera direction where useful |
| Timing | Exact narration start/end and spoken words, plus planned visual start/end |
| Text | Exact on-screen words, if needed; keep labels short |
| Sources | Asset URL/catalog ID, creator and license; separately cite the source supporting each factual claim, date or location |

Use a strong opening image, vary shot scale and visual form, and change the
visual when the narration meaning changes—not just on a fixed timer. Prefer
one clear idea per scene. Flow video durations are model-dependent: Omni
supports 4, 6, 8 or 10 seconds; Veo 3.1 clips are fixed at 8 seconds.

Generated imagery is not evidence. Do not ask Flow to render readable
paragraphs, precise charts or authoritative maps; add accurate wording and
graphics in a separate, reviewable step. Avoid fabricated logos, watermarks,
quotes, signage and text.

Before rendering, verify that the planned timeline has no uncovered narration
and no still or unchanged composition longer than 8 seconds, except for a
documented, precisely bounded user-approved locked section. Each change must
remain relevant to the spoken idea; do not satisfy the timing limit with
arbitrary crops, zooms or unrelated cutaways. Preserve approved edits and
timing outside the explicitly authorized change range.

### 4. Storyboard with generated and real media

Use `flow_agent_images` for a free storyboard when appropriate (up to 50
scenes per batch). Use `flow_character` and reference assets only when a
consistent recurring character is useful. For real stock footage or photos,
search Pexels using the bundled helper:

```bash
python3 "$HOME/.claude/skills/yt-documentary/pexels.py" search "specific subject and action" --kind video
python3 "$HOME/.claude/skills/yt-documentary/pexels.py" download 123456 --kind video --out /path/to/project/assets
```

Set `PEXELS_API_KEY` in the environment or in a local `.env` file in the
current project directory. The helper reads it without executing the file,
never prints the key, downloads only from HTTPS Pexels hosts, and writes
attribution details to `pexels-credits.json`. Review the source and license
before using an asset; keep the credit manifest with the final project. Flow
MCP does not replace Pexels, and Pexels does not replace Flow MCP.

Review the storyboard and selected stock assets for relevance, continuity,
license and sensitive content before moving on.

Video generation spends the user's Google Flow credits. Before calling
`flow_generate`, show the planned number of clips, model, resolution, durations
and estimated total spend, then obtain the user's approval and a total budget
or per-clip cap. Set `max_credits` on every scene and use one variant unless
the user approves otherwise. The tool's cap is per scene, not a substitute for
the agreed total budget. Never call `flow_edit` or `flow_continue` without
separately explaining that Flow does not quote their cost beforehand and
getting approval.

Use specific prompts with subject, action, setting, composition, camera move
and lighting. Use `reference_images` for visual consistency; `chain_previous`
only when the next scene should continue from the prior clip. Flow's video
composer cannot use first/last frames and reference images together; do not
promise otherwise.

### 5. Generate and recover safely

Call `flow_generate` with the approved settings, then use `flow_wait` for the
returned job IDs. If a call returns `still_working`, poll with `flow_wait`;
never submit the same generation again just because it is still running.
Check `flow_assets` or the returned file paths before retrying. Use
`flow_retry` only for confirmed failed jobs, so a completed paid scene is not
generated twice.

If Flow's output is irrelevant, inconsistent, or visually misleading, revise
the prompt or storyboard and show the change before spending additional
credits. Do not treat generated depictions of real people, crime scenes,
locations or historical events as authentic footage.

### 6. Narrate and assemble

Use the user's own narration when supplied. If they request text-to-speech,
check `flow_voices` and use `flow_narrate` with its local Kokoro engine where
the requested language and voice are supported. The documented Kokoro voices
are English; for other languages, prefer a user recording or ask before using
another provider. Gemini narration is optional and requires a separate Google
AI Studio key; do not enable it by default.

Assemble with `flow_assemble`, using the actual ordered Flow and Pexels clip
paths, the approved voiceover and optional licensed music. Duck music under
speech, keep clip audio low when narration is present, and avoid an unintended
frozen ending. Preserve separate source and final files. Use `flow_transcribe`
on the assembled film to check dialogue and timing if needed.

### Optional HyperFrames timeline and render

Use this path when the user requests HyperFrames, provides an existing
HyperFrames project, or needs an editable HTML timeline. Flow remains the
generation path described above; do not imply a Flow assembly is a HyperFrames
project or switch editing backends without a reason.

- For an existing project, read `npx hyperframes timeline --json` and
  `npx hyperframes history --since mine --who <you>` before editing. Preserve
  user-authored changes and use absolute clip times when comparing nested
  compositions. Open the project with `npx hyperframes open <project-dir>`.
- For a new HyperFrames project, use
  `npx hyperframes init <dir> --skip-skills --skill=hyperframes`. Keep the root
  `index.html` to project variables, media/audio and scene hosts; put each
  scene in an editable sub-composition. A project opened in the desktop app is
  not thereby visually reviewed or accepted.
- Keep each timed item in the HTML with a stable `id`, `class="clip"`,
  `data-start` and `data-duration` in seconds. The root `data-duration` is the
  film length. Register each paused GSAP timeline after its tweens as
  `window.__timelines["<data-composition-id>"] = tl`. All visible output must
  be deterministic and seek-safe: no timers, network fetches, `Date.now()`,
  unseeded randomness, infinite repeats, or media play/pause/seek calls.
- Keep assets project-relative (`assets/...`). Use bundled fonts or define
  local font files with `@font-face`. Give every audio element an `id`; mark
  video audio explicitly with `data-has-audio="true"` or mute it. Do not tween
  `display`, `visibility` or `autoAlpha` on a clip, and do not put CSS
  transforms on elements whose transforms GSAP controls. Apply footage grades,
  grain, blur or vignettes through `npx hyperframes media-treatment`, not CSS
  filters.
- Use `npx hyperframes lint` while editing and `npx hyperframes check --json`
  after structural changes; fix errors and review warnings. Snapshot and
  inspect every scene and both sides of changed cuts or overlays; a clean
  check alone is not editorial approval. Preview the actual project and wait
  for approval unless the user asked for a file or no stops. Render only after
  the editorial gates pass, then verify the output is non-empty, decodes, has
  the expected duration and streams, and inspect frames from the rendered
  file.

### 7. Captions and final review

Before calling `flow_captions`, call `flow_transcribe`, show the transcript
(especially names, numbers and Arabic text) and get the user's approval of
corrections. Then pass the agreed language and caption settings. Keep the
returned subtitle file for YouTube.

Review the actual assembled output scene by scene: inspect every visual clip
at least once and both sides of every cut, overlay or source transition. Check
the spoken words against the visible action, continuity, pacing, chronology,
voice/music balance, caption timing and spelling, generated-media disclosures,
credits and factual labels. Reconcile this inspection with the full narration
ledger and record the actual timeline clip IDs reviewed. Verify 100% narration
coverage and the 8-second maximum for still or unchanged compositions,
including the final section; record only explicitly user-approved locked
section exceptions. A successful generation, assembly or technical check does
not by itself pass editorial review. If any clip, cut or narration beat cannot
be inspected, block final acceptance and report the exact gap. Do not claim a
visual or audio check that was not performed. Keep human approval in the loop
and never publish automatically.

## Final handoff

Report the final video path, runtime, aspect ratio, scene count, credits spent
(if returned by Flow), caption/subtitle paths, Pexels credit-manifest path (if
used), and any factual or visual limitations still needing review. Clearly
label generated scenes and any remaining unverified claims.
