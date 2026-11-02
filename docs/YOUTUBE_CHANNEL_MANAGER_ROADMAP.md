# AnimaTube YouTube Channel Manager — implementation roadmap

## Product direction
A local-first workspace for a faceless animation and storytelling channel publishing in Telugu and English, with a long-term monetized-channel objective. AnimaTube prepares and organizes assets; the creator creates the actual channel in YouTube, reviews content, and approves publishing.

## Architecture principles
- Keep the desktop application local-first and CPU-friendly.
- Store channel profiles separately from editable .anima video projects.
- Support multiple channel profiles.
- Never store Google passwords, OAuth tokens, refresh tokens, or client secrets in profile JSON.
- No automatic account creation, upload, scheduling, commenting, or publishing in Phase 1.
- Use versioned schemas and atomic JSON writes.
- Deliver changes through a feature branch; keep main unchanged.

## Phase 1 — Channel Setup Wizard (current)
- Create, list, edit, and delete local channel profiles.
- Prefill animation/storytelling, Telugu + English, faceless, and long-term monetization.
- Capture channel name/handle, audience, audience need, content pillars, About description, tagline, brand colours/fonts, profile/banner/watermark asset paths, trailer script, featured video, and starter playlists.
- Persist a creator-controlled launch checklist.
- Explain clearly that this local profile does not create/connect/publish a YouTube channel.
- Validate fields and reject unknown fields and profile paths outside the channel library.
- Add unit tests and desktop smoke tests.

Acceptance: create/edit/reopen/delete; correct defaults; checklist persistence; validation; separation from .anima projects; full CI green; manual Windows desktop acceptance.

## Phase 2 — Brand Kit and Channel Assets
Add image dimension/aspect-ratio and file-size validation against current official YouTube guidance; editable colour/font tokens; reusable thumbnail templates; preview and revision history. Never silently overwrite source assets.

## Phase 3 — Channel Strategy and 30-day Plan
Define 3–5 Telugu/English storytelling pillars; audience positioning; 30-day calendar based on actual weekly capacity; source records and fact-check status; long-form and Shorts plans as separate formats. Do not promise virality or monetization.

## Phase 4 — End-to-End Production Workspace
Extend stages to idea, research, script, storyboard, voice, animation, edit, packaging, QA, approval, and publish-ready. Link scripts, assets, audio, subtitles, thumbnails and exports to channel/episode. Add bilingual subtitle, pronunciation and glossary review, plus quality gates for rights and factual accuracy.

## Phase 5 — YouTube Account Integration
Read-only Google OAuth first with minimum scopes and secure OS credential storage. Add authorized channel data; only then consider resumable uploads, metadata and thumbnail management. Require explicit creator approval per video, visible progress/retries and audit logs. Follow current API policies and quota limits.

## Phase 6 — Analytics and Community
Import authorized analytics; compare performance by format and topic without causal or growth guarantees. Add comment triage and draft replies with safety flags and creator approval. Convert viewer questions into candidate ideas, never automatic publishing.

## Delivery sequence
1. Implement Phase 1 and CI.
2. Validate locally on Windows.
3. Review and merge Phase 1 only after creator approval.
4. Begin Phase 2 on a new branch after acceptance.
