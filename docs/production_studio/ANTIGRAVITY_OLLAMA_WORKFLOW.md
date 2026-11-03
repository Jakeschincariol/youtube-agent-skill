# Antigravity + Ollama Local Workflow

**Purpose:** Use Google Antigravity as the engineering workspace and Ollama as the local language-model service for Little Dreamers. Antigravity is not a runtime dependency of AnimaVideo; the desktop app talks directly to Ollama on the creator's computer.

## 1. Runtime boundaries

- Antigravity edits and tests this repository in its workspace terminal.
- Ollama serves the selected local model on `http://127.0.0.1:11434`.
- `OllamaClient` performs model discovery and structured JSON chat.
- `LittleDreamersStoryPlanner` is for creating *new* episode plans and validates ages 2–5, the six approved character IDs, scene/shot structure and durations.
- Existing AnimaVideo, FFmpeg, voice/audio modules and provider adapters remain the production pipeline.
- Do not expose Ollama's unauthenticated API to the public internet. Keep the host on loopback.
- CI uses mocked Ollama HTTP responses. CI must never require a running local model or make paid cloud AI calls.

## 2. Verify Ollama on the creator's computer

Open the repository folder in Antigravity, then open its integrated terminal (PowerShell on Windows).

```powershell
ollama --version
ollama list
```

If the intended model is not installed, pull it once:

```powershell
ollama pull qwen3:1.7b
```

Start the Ollama service if it is not already running:

```powershell
ollama serve
```

Keep that terminal running if Ollama is not installed as a background service. In a second Antigravity terminal, verify the API and selected model:

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "qwen3:1.7b"
Invoke-RestMethod http://127.0.0.1:11434/api/tags
python -c "from animatube.ai import OllamaClient; print(OllamaClient().health_check())"
```

Expected result: `available: True` and the installed model list includes `qwen3:1.7b`. If the model name differs, set `OLLAMA_MODEL` to the exact name shown by `ollama list`.

## 3. Verify the repository integration

Run from the repository root:

```powershell
python -m compileall -q animatube tests
python -m unittest discover -s tests -p "test_ollama_client.py" -v
python -m unittest discover -s tests -p "test_little_dreamers_planner.py" -v
```

These tests use mocked model responses. They verify application logic without consuming local inference time. The live health check above is the separate machine-specific connectivity check.

## 4. Antigravity task prompt

Paste this into Antigravity when continuing implementation:

> Work only in the existing `chandra0000/youtube-agent-skill` repository. First inspect the current branch, working tree, README, Little Dreamers production roadmap, canonical Episode 1 storyboard and assets. Do not regenerate, redesign, rename or overwrite the six approved character references or any canonical Episode 1 files. Keep Ollama bound to `127.0.0.1:11434`; use the existing `OllamaClient` and `LittleDreamersStoryPlanner`; never add paid cloud LLM calls or secrets. Run compileall and the focused Ollama/planner tests before changing code, then add focused tests for any change. For Episode 1, consume the existing approved 11-scene, 600-second production specification and continue the existing AnimaVideo/FFmpeg pipeline. Do not use the generic 3–6-scene new-episode planner to rewrite Episode 1. Preserve human approval gates for story, storyboard, visuals, voice and final render. Run the complete test suite and report exact commands, results, changed files and any remaining failures. Do not claim a video is production-ready until technical QA and human viewing/listening approval pass.

## 5. Episode 1 production guardrails

The canonical `The Magic ABC Train` episode remains the source of truth:

- 11 scenes and 600 seconds in the approved production specification.
- 1920×1080 at 24 fps for the existing production target.
- Use the six approved character references as-is: Aarav, Mia, Ellie, Gigi, Bobo and Twinkle.
- Preserve the existing storyboard, shot list, reference assets and Scene 1 sample preview.
- Treat any new Ollama output as a proposal saved to a new versioned path. Never write it over canonical files.
- Continue from the existing sample render and QA report; generate missing scene assets, assemble through the existing FFmpeg path, run technical QA, then request human review.
- No automatic YouTube publishing.

## 6. Troubleshooting

| Symptom | Check |
| --- | --- |
| Connection refused | Confirm Ollama is running and `OLLAMA_HOST` is loopback. |
| No models found | Run `ollama list` and pull the selected model. |
| Model not installed | Match `OLLAMA_MODEL` exactly to `ollama list`. |
| More than one model | Set `OLLAMA_MODEL` explicitly for reproducible output. |
| CI fails trying to contact Ollama | Tests must mock HTTP; do not add live-model calls to CI. |

