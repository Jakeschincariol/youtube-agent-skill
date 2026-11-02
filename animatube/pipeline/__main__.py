from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from animatube.pipeline.orchestrator import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AnimaTube Local-First AI Video Production Pipeline",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="output/devops_2027",
        help="Directory to save generated video and production assets",
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default="DevOps_2027_Roadmap",
        help="Name of the video project",
    )
    parser.add_argument(
        "--dry-run-render",
        action="store_true",
        help="Skip heavy frame-by-frame FFmpeg encoding (useful for quick asset checks and CI)",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Use deterministic built-in script rather than querying Ollama",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print("=================================================================")
    print("  AnimaTube: Local-First YouTube Production Pipeline")
    print(f"  Project: {args.project_name}")
    print(f"  Target: {args.output_dir}")
    print("=================================================================")

    manifest = run_pipeline(
        output_directory=args.output_dir,
        project_name=args.project_name,
        use_ollama=not args.no_ollama,
        dry_run_render=args.dry_run_render,
    )

    print("\nProduction complete! Generated assets:")
    print(f"  - Manifest:     {Path(args.output_dir) / 'manifest.json'}")
    print(f"  - Script:       {manifest.script_file}")
    print(f"  - Storyboard:   {manifest.storyboard_file}")
    print(f"  - AnimaTube:    {manifest.anima_project_file}")
    print(f"  - Kdenlive:     {manifest.kdenlive_project_file}")
    print(f"  - Thumbnail:    {manifest.thumbnail_file}")
    print(f"  - Metadata:     {manifest.metadata_file}")
    print(f"  - Video (MP4):  {manifest.output_video_file}")
    print(f"  - Total Assets: {len(manifest.assets)}")
    print("=================================================================")


if __name__ == "__main__":
    main()
