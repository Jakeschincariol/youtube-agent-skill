# Little Dreamers — Voice Studio Implementation Brief

**Status:** Approved voice direction; implementation pending  
**Product:** AnimaVideo / Little Dreamers  
**Primary narrator:** Youthful female voice  
**Accent:** Neutral international English

## 1. Voice direction

The default Little Dreamers narrator must sound youthful, warm, sweet, cheerful, friendly and engaging for children aged 2–5.

The delivery should be expressive and natural without sounding robotic, overly squeaky, exaggerated or tiring. Use clear, easy-to-understand international English pronunciation. Avoid strongly regional pronunciation unless a later project explicitly requests it.

Use:
- Gentle warmth for introductions and explanations.
- Bright, playful energy for discoveries, alphabet reveals and character interactions.
- Calm, reassuring delivery for transitions and goodbyes.
- Natural pauses, varied emphasis and age-appropriate pacing.

The voice should be recognisable and consistent across scenes and episodes. Do not change narrator identity between scenes unless the creator explicitly chooses a different voice.

## 2. Voice presets

Provide these selectable styles while retaining the approved default direction:

1. **Youthful Little Dreamers Narrator — DEFAULT:** youthful female, warm, sweet, cheerful, clear neutral international English.
2. **Gentle Storyteller:** softer, calmer female delivery for quiet story moments.
3. **Playful Character Energy:** more animated and expressive female delivery for excitement, games and discoveries.

A singing voice is a separate capability. Only offer it when the configured provider genuinely supports singing generation; ordinary speech TTS must not be presented as singing.

## 3. Voice Studio user experience

The creator should be able to:
- Select a provider and inspect its actual available voices.
- Preview a short sample before choosing a voice.
- Compare the three delivery presets where supported.
- Generate narration per scene or for the full approved script.
- Regenerate one scene without unnecessarily regenerating all other audio.
- Adjust speaking rate, pauses, emphasis and pronunciation where supported.
- Review and correct pronunciations of names such as Aarav, Mia, Ellie, Gigi, Bobo and Twinkle.
- Listen to the generated audio before accepting it.
- Save accepted audio, provider/voice identifiers, settings and script version as reusable metadata.
- Replace a voice deliberately while clearly warning that it may affect timing.

Do not hard-code a voice identifier from an assumed provider. Discover the provider's real voice catalogue and persist the selected stable identifier. If a provider does not expose a requested control, show that limitation rather than pretending it is supported.

## 4. Audio and narration quality checks

For each generated voice track:
- Confirm the file exists, is readable and has non-zero duration.
- Check sample rate, channels, encoding and clipping.
- Detect unexpected silence, truncation and abrupt endings.
- Compare speech duration with the scene timing and flag overflow.
- Preserve natural pauses; do not remove all silence.
- Provide a listening review for pronunciation, emotion, clarity and suitability.
- Keep dialogue intelligible above background music and sound effects.
- Synchronise narration with scene events and subtitles.
- Never mark a track approved based only on successful file generation.

Automated checks can flag technical problems, but a human listening review is required before final approval.

## 5. Provider and licensing requirements

Use a provider adapter so the editor is not coupled to one TTS vendor. Audit existing integrations before adding a new one.

For every provider:
- Verify current API support, authentication requirements, voice availability, usage limits and pricing.
- Use documented, authorised interfaces only.
- Keep API keys in environment variables or a secure secrets store; never commit credentials.
- Record the provider, voice identifier, generation settings and relevant licensing/usage terms.
- Do not clone real children's voices or use voices without appropriate rights.
- Do not claim a provider is connected or audio was generated unless the operation actually succeeded.

## 6. Production defaults

- Default narrator direction: **youthful female voice, neutral international English**.
- Audience: children aged 2–5.
- Language: English.
- Delivery: clear, warm, cheerful and expressive.
- Consistency: one selected narrator identity across the episode.
- Approval: creator listens to and approves the voice before final video export.

## 7. First acceptance test

Use a short approved Little Dreamers script (approximately 20–30 seconds) to:
1. Generate a preview using the default narrator direction.
2. Generate one alternative delivery preset if the provider supports it.
3. Compare pronunciation, warmth, clarity, pacing and emotional expression.
4. Check audio integrity and scene timing.
5. Let the creator select and approve the voice.
6. Reuse the selected voice identity for the 60-second pilot.

Do not generate narration for the full 10-minute episode until the preview voice is approved.

## 8. Implementation constraints

- First audit existing AnimaVideo, Producer Orchestration, YouTube Agent Skills, scripts and audio modules.
- Reuse existing components; do not create duplicate orchestration or editing systems.
- Keep rendering and generation sequential on the target 8 GB RAM machine.
- Add tests for provider failures, retries, missing audio, invalid audio, timing overflow and saved voice metadata.
- Separate automated technical QA from creator approval.
- Report implemented functionality, provider limitations, tests and actual preview asset paths honestly.

**Approval record:** The creator selected a youthful female narrator with an international English accent. This is the default voice direction for Little Dreamers unless the creator changes it.
