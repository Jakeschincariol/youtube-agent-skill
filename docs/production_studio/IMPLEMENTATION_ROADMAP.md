# Little Dreamers Hybrid Production — Implementation Roadmap

**Repository:** chandra0000/youtube-agent-skill  
**Application:** animatube/ (AnimaVideo desktop editor)  
**Architecture:** Local Ollama + cloud media adapters + existing local FFmpeg rendering  
**Delivery rule:** Small, reviewable changes with tests at every phase.

## Phase 0 — Repository audit and architecture baseline

**Status:** Completed for this implementation branch.

- Confirmed the existing PySide6 application, AI provider interfaces/registry, mock providers, pipeline, episode models, QA validator and Episode 1 assets.
- Confirmed all six character references and the official Character Bible are already present.
- Confirmed the current generic Ollama script generator is DevOps-specific and must not be reused as the Little Dreamers story planner.
- Documented runtime boundaries, hybrid data flow, security, approval rules and non-goals.

**Acceptance:** Architecture documentation matches the current repository and protects existing assets.

## Phase 1 — Local Ollama foundation

**Status:** In progress.

- Add a standard-library Ollama client with configurable host, model and timeout.
- Default to loopback; discover installed models through /api/tags.
- Require explicit selection if multiple models are installed; never hard-code an assumed model.
- Support structured JSON chat through /api/chat with JSON mode.
- Provide non-throwing health status for the UI and actionable exceptions for generation calls.
- Add unit tests using mocked HTTP responses; no live Ollama service is required in CI.

**Acceptance:**
- Health check returns available/unavailable and installed models.
- Model selection handles zero, one and multiple installed models.
- JSON generation rejects empty prompts, invalid model responses and non-object JSON.
- Existing AI provider and pipeline tests remain unchanged and passing.

## Phase 2 — Little Dreamers production planning

- Add a dedicated episode brief and planning service; do not reuse DevOps script defaults.
- Define typed schemas for episode brief, story, dialogue, scene, shot and character assignment.
- Include audience 2–5, approved character IDs, episode language, duration and learning objective.
- Validate every character against the six-name allowlist and resolve visual references from the locked Character Bible.
- Keep Episode 1 canonical files read-only; generate new episodes under new IDs.
- Store prompt version, selected Ollama model and generated content version.

**Acceptance:** A new episode idea produces schema-valid brief/story/scene JSON; unknown characters, missing dialogue speakers and invalid shot timings are rejected.

## Phase 3 — Production Architect and resumable job state

- Implement a workflow state machine and stage dependency graph.
- Persist episode, scene, shot and asset job state using the existing project/storage conventions.
- Add bounded retry, cancellation, failure diagnostics and idempotent resumption.
- Preserve accepted outputs; retry only the failed stage/shot.
- Add human approval gates for story, storyboard, visual assets, voice and final render.

**Acceptance:** A simulated failure can be retried without changing already-approved assets or rerunning completed stages.

## Phase 4 — Cloud media adapter integration

- Audit provider support and current terms before selecting concrete image/video/voice/music vendors.
- Add provider adapters behind the existing interfaces; extend interfaces only where a capability is genuinely missing (for example, image generation).
- Keep Google Flow optional and avoid undocumented endpoints.
- Keep mock providers as the default in CI and local demo mode.
- Add secure credential configuration, cost visibility, provider capability discovery and job polling/cancellation.

**Acceptance:** Each connected provider can submit, poll, cancel and persist a real job; missing credentials produce a clear unavailable state rather than fake success.

## Phase 5 — Audio, animation, assembly and media QA

- Connect approved storyboard shots to image/video generation.
- Reuse the existing voice/audio modules and the approved Little Dreamers narrator direction.
- Generate per-scene dialogue/audio and subtitles; validate duration and synchronization.
- Assemble scenes through the existing FFmpeg renderer and preserve Kdenlive handoff.
- Run technical QA for file integrity, codecs, resolution, frame rate, duration, audio presence, clipping and missing scenes.
- Require creator listening/viewing approval for creative quality and character consistency.

**Acceptance:** A pilot episode renders with a complete manifest, technical QA report and human approval record.

## Phase 6 — Production Studio UI and first pilot

- Add a production dashboard within the existing PySide6 editor.
- Show episode stages, local/cloud provider, model, cost estimate where available, progress, errors and retry controls.
- Add character reference selection, storyboard review and asset version comparison.
- Produce the first approved Little Dreamers pilot through the new workflow.
- Keep publishing manual; export YouTube metadata and assets for creator review.

**Acceptance:** The creator can create, pause, resume, review, retry and export an episode without leaving AnimaVideo.

## Current branch deliverables

- animatube/ai/ollama_client.py
- tests/test_ollama_client.py
- docs/production_studio/HYBRID_AI_PRODUCTION_ARCHITECTURE.md
- docs/production_studio/IMPLEMENTATION_ROADMAP.md

## Verification commands

Run from the repository root on a development machine:

~~~powershell
python -m compileall -q animatube tests
python -m unittest discover -s tests -p "test_ollama_client.py" -v
python -m unittest discover -s tests -v
~~~

Optional local connection check after starting Ollama:

~~~powershell
python -c "from animatube.ai import OllamaClient; print(OllamaClient().health_check())"
~~~

The unit tests mock Ollama HTTP calls and must not require a running model or network access.
