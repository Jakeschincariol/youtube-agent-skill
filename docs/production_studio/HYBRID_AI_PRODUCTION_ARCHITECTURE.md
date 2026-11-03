# Little Dreamers Hybrid AI Production Architecture

**Status:** Approved architecture baseline  
**Product:** AnimaVideo / Little Dreamers  
**Architecture decision:** Hybrid — local Ollama for language intelligence, cloud providers for media generation  
**Existing application:** PySide6 desktop editor, existing AnimaTube/AnimaVideo pipeline and FFmpeg renderer

## 1. Architecture principles

1. Extend the existing AnimaVideo application. Do not create a parallel application or replace the editor.
2. Google Antigravity is the engineering environment used to inspect, implement, test and maintain the repository. It is not a runtime dependency of the shipped Cartoon Studio.
3. The Cartoon Studio Production Architect is an application service inside AnimaVideo. It owns episode workflow state, stage dependencies, approvals, retries and asset handoffs.
4. Ollama runs on the creator's computer and is used for local text intelligence: episode briefs, story drafts, dialogue, shot descriptions, prompt preparation and AI-assisted review.
5. Cloud media providers are accessed only through provider adapters. Video, image, voice and music generation must be independently replaceable.
6. Existing local rendering, FFmpeg compilation, Kdenlive handoff, mock providers and tests remain available.
7. The six approved Little Dreamers character designs are locked references. AI may describe or select them, but must not silently redesign, regenerate or replace them.
8. Episode 1, The Magic ABC Train, is an approved production asset and regression fixture. Do not regenerate or overwrite its canonical storyboard or character references during the foundation work.
9. A successful API response is not the same as an approved production asset. Every generated artifact must pass technical validation and the creator's required review.
10. Paid provider calls must never run in ordinary CI tests.

## 2. Runtime topology

~~~text
AnimaVideo desktop application (PySide6)
  |
  +-- Production Studio UI
  |     +-- Episode brief and settings
  |     +-- Character Bible / reference browser
  |     +-- Storyboard and shot review
  |     +-- Asset and job monitor
  |     +-- Approval and export controls
  |
  +-- Production Architect (in-process Python services)
  |     +-- Workflow state machine
  |     +-- Episode/scene job manager
  |     +-- Stage dependency and retry policy
  |     +-- Asset manifest and provenance
  |     +-- Human approval gates
  |
  +-- Local intelligence adapter
  |     +-- OllamaClient -> http://127.0.0.1:11434
  |     +-- Model discovery and explicit model selection
  |     +-- Structured JSON generation
  |     +-- Prompt templates and output validation
  |
  +-- Media provider registry / adapters
  |     +-- Cloud image generation (adapter to be added/selected)
  |     +-- Cloud video generation (existing provider interface)
  |     +-- Cloud voice generation (existing provider interface)
  |     +-- Cloud music/SFX generation (existing provider interface)
  |     +-- Mock providers for offline development and CI
  |
  +-- Existing local production tools
        +-- AnimaVideo project/timeline
        +-- FFmpeg compiler and media probes
        +-- Audio/subtitle utilities
        +-- Kdenlive handoff
~~~

The desktop application remains the user-facing product. The Production Architect coordinates work; it does not replace the current timeline editor or media compiler.

## 3. Responsibility boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| Antigravity | Repository engineering, code changes, test execution and review | Runtime episode state or media credentials |
| Production Architect | Workflow state, dependencies, retry, approvals and asset references | Provider-specific HTTP details |
| Ollama adapter | Local model discovery and text/JSON inference | Cloud image/video/audio generation |
| Character Bible | Approved identity, personality, voice direction and visual references | Generated per-shot media |
| Media adapters | Provider requests, job polling, cancellation and usage metadata | Story canon or approval decisions |
| FFmpeg/rendering | Deterministic assembly, encoding and media validation | Creative script decisions |
| Creator | Final creative and publishing approval | Manual tracking of every background job |

## 4. Episode workflow

~~~text
IDEA
  -> EPISODE_BRIEF
  -> STORY_DRAFT
  -> CHARACTER_ASSIGNMENT
  -> DIALOGUE_DRAFT
  -> STORYBOARD_DRAFT
  -> CREATOR_STORY_APPROVAL
  -> VISUAL_ASSET_GENERATION
  -> VISUAL_ASSET_REVIEW
  -> ANIMATION_GENERATION
  -> VOICE_AND_MUSIC_GENERATION
  -> LIP_SYNC_AND_SOUND_MIX
  -> VIDEO_ASSEMBLY
  -> AUTOMATED_QA
  -> CREATOR_FINAL_REVIEW
  -> EXPORT_READY
~~~

Stages must be resumable. A failed shot should be retried independently; it must not force regeneration of accepted scenes or dialogue. Regeneration creates a new asset version and never destroys the prior accepted version.

## 5. Character identity and Episode 1 protection

The canonical character source is:

- little-dreamers/characters/CHARACTER_BIBLE.md
- little-dreamers/characters/<character>/
- little-dreamers/flow_ready/

Approved roster: Aarav, Mia, Ellie, Gigi, Bobo and Twinkle.

The canonical Episode 1 production specification is:

- animatube/presets/ep01_magic_abc_train.py
- little-dreamers/episodes/ep01_magic_abc_train/storyboard.json
- little-dreamers/episodes/ep01_magic_abc_train/SHOT_LIST.md

These files are read-only inputs to the new workflow unless the creator explicitly requests a revision. New episode generation must write to a new episode ID and output directory.

## 6. Hybrid data and security model

- Ollama defaults to loopback at http://127.0.0.1:11434. Do not expose its unauthenticated API to the public internet.
- The selected local model is explicit when multiple models are installed. Use OLLAMA_MODEL or a UI selection; do not assume llama3 is installed.
- Cloud provider keys remain in the existing credential manager or environment-backed secret configuration. Never place secrets in prompts, project JSON, manifests, logs or source control.
- Send only the minimum shot prompt and required approved reference assets to a cloud provider.
- Record provider, model, voice ID, generation parameters, job ID, cost/usage metadata where supplied, asset checksum and source storyboard version.
- The app must clearly show whether a stage is local or cloud-backed and whether it may incur usage charges.
- Do not make paid provider requests in CI. Use mock adapters and recorded fixtures.

## 7. Reliability and approval rules

Use explicit states: PENDING, RUNNING, VALIDATING, APPROVAL_REQUIRED, APPROVED, COMPLETED, FAILED, CANCELLED.

A stage can move to COMPLETED only after its required output exists and passes its technical validator. Human approval is a separate state and must be recorded with timestamp, asset version and reviewer decision.

Retries must be bounded, preserve error details and use idempotency keys where supported. Never silently substitute mock output for a requested cloud generation in a real production run.

## 8. Existing baseline and implementation boundary

The repository already contains:
- A PySide6 AnimaVideo desktop editor and FFmpeg export path.
- An AI provider interface/registry for video, voice and music, with mock providers for CI.
- An Ollama-backed script generator currently tailored to the DevOps sample pipeline.
- Little Dreamers' locked Character Bible, reference anchors and Episode 1 storyboard.
- Episode production models and a QA validator.
- A separate Voice Studio implementation brief with an approved narrator direction.

The new Ollama client is a reusable foundation. The DevOps-specific script generator must not be treated as the Little Dreamers story planner. A dedicated Little Dreamers planner and workflow integration are later implementation stages.

## 9. Non-goals for the foundation milestone

- Replacing PySide6 with a web application or adding FastAPI solely for orchestration.
- Rebuilding the existing 3D animation pipeline.
- Making Google Flow mandatory; keep it an optional provider path.
- Automatically publishing to YouTube.
- Regenerating approved character designs or Episode 1.
- Claiming cloud providers are connected before their real adapters and credentials are configured.
