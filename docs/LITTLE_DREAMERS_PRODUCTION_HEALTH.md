# Little Dreamers production health checks

Run the read-only preflight from the repository root:

    py -3.15 -m animatube.pipeline.production_health

It checks Python dependencies, FFmpeg, all six locked character reference sheets and six Flow anchor images, and Episode 1 storyboard structure, unique shot IDs, timing totals, approved character names and referenced image paths. Ollama is checked at its local /api/tags endpoint. Ollama is a warning when offline by default because CI does not start a local model service.

Optional local checks:

    py -3.15 -m animatube.pipeline.production_health --require-ollama
    py -3.15 -m animatube.pipeline.production_health --check-exports
    py -3.15 -m animatube.pipeline.production_health --require-ollama --check-exports --json

--require-ollama makes an unavailable server or configured model a failure. --check-exports decodes rendered videos in the Episode 1 exports folder with FFmpeg. If no exports exist, this is a warning rather than a false failure.

Exit code is 0 when no checks fail and 1 when a required check fails. Warnings are non-blocking. This does not replace the full unit suite or human visual/audio approvals, and it never publishes content.
