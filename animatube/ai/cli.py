from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any

from animatube.ai.credentials import AICredentialManager
from animatube.ai.models import MediaType, MusicPrompt, VideoPrompt, VoicePrompt
from animatube.ai.registry import AIProviderRegistry

logger = logging.getLogger("animatube.ai.cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m animatube.ai.cli",
        description="AnimaVideo CLI for AI Video, Voice, and Music Generation",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 1. Video Subcommand
    video_p = subparsers.add_parser("video", help="Generate AI video from text or reference image")
    video_p.add_argument("--prompt", "-p", required=True, help="Scene description and motion prompt")
    video_p.add_argument("--negative-prompt", default="", help="Negative prompt to prevent artifacts")
    video_p.add_argument("--reference-image", "-i", default="", help="Path to character reference image or first frame")
    video_p.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "1:1", "9:16", "4:3"], help="Video aspect ratio")
    video_p.add_argument("--duration", "-d", type=float, default=4.0, help="Clip duration in seconds (1.0 to 30.0)")
    video_p.add_argument("--camera", default="none", choices=["none", "pan_left", "pan_right", "tilt_up", "tilt_down", "zoom_in", "zoom_out", "orbit"], help="Camera movement preset")
    video_p.add_argument("--motion-strength", type=float, default=0.5, help="Motion intensity (0.1 to 1.0)")
    video_p.add_argument("--output-dir", "-o", default="output/ai_videos", help="Directory to save generated video")
    video_p.add_argument("--provider", default="", help="AI Video provider ID (default: mock_video)")

    # 2. Voice Subcommand
    voice_p = subparsers.add_parser("voice", help="Generate character dialogue or narration audio")
    voice_p.add_argument("--text", "-t", required=True, help="Spoken dialogue text")
    voice_p.add_argument("--character", "-c", default="Narrator", help="Character name (e.g. Aarav, Mia, Ellie, Twinkle)")
    voice_p.add_argument("--voice-id", default="default", help="Voice identifier (e.g. aarav_boy, mia_girl, twinkle_star)")
    voice_p.add_argument("--style", default="conversational", help="Delivery style (e.g. cheerful, adventurous, gentle)")
    voice_p.add_argument("--rate", default="+0%", help="Speech rate adjustment (e.g. +5%%, -10%%)")
    voice_p.add_argument("--pitch", default="+0Hz", help="Speech pitch adjustment (e.g. +10Hz, -5Hz)")
    voice_p.add_argument("--output-dir", "-o", default="output/ai_audio", help="Directory to save generated audio")
    voice_p.add_argument("--provider", default="", help="AI Voice provider ID (default: mock_voice)")

    # 3. Music Subcommand
    music_p = subparsers.add_parser("music", help="Generate original music, BGM, or sound effects")
    music_p.add_argument("--prompt", "-p", default="", help="Description of musical style, mood, or sound effect")
    music_p.add_argument("--mood", default="cheerful", choices=["cheerful", "playful", "curious", "calm", "adventurous", "lullaby", "dramatic"], help="Emotional mood")
    music_p.add_argument("--genre", default="preschool_orchestral", help="Arrangement genre")
    music_p.add_argument("--duration", "-d", type=float, default=30.0, help="Duration in seconds (1.0 to 180.0)")
    music_p.add_argument("--tempo", default="medium", choices=["slow", "medium", "upbeat"], help="Tempo setting")
    music_p.add_argument("--sfx", action="store_true", help="Generate sound effect rather than music track")
    music_p.add_argument("--output-dir", "-o", default="output/ai_music", help="Directory to save generated audio")
    music_p.add_argument("--provider", default="", help="AI Music provider ID (default: mock_music)")

    # 4. Providers Subcommand
    prov_p = subparsers.add_parser("providers", help="List registered AI providers and their capabilities")
    prov_p.add_argument("--type", choices=["all", "video", "voice", "music"], default="all", help="Filter by media type")

    # 5. Credentials Subcommand
    cred_p = subparsers.add_parser("credentials", help="Manage API credentials for external providers")
    cred_sub = cred_p.add_subparsers(dest="cred_action", required=True)
    cred_set = cred_sub.add_parser("set", help="Store an API key securely")
    cred_set.add_argument("provider_id", help="Provider ID (e.g. elevenlabs, runpod, luma)")
    cred_set.add_argument("api_key", help="API Key / Token")
    cred_get = cred_sub.add_parser("get", help="Check if an API key is configured (masked)")
    cred_get.add_argument("provider_id", help="Provider ID")
    cred_sub.add_parser("list", help="List all configured provider keys (masked)")

    return parser


def run_video_cli(args: argparse.Namespace) -> int:
    registry = AIProviderRegistry.get_instance()
    provider = registry.get_video_provider(args.provider or None)

    prompt = VideoPrompt(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        reference_image_path=args.reference_image,
        aspect_ratio=args.aspect_ratio,
        duration_seconds=args.duration,
        camera_motion=args.camera,
        motion_strength=args.motion_strength,
    )

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Submitting Video Job to provider: {provider.provider_name} ({provider.provider_id})")
    print(f"Prompt: {prompt.prompt}")
    if prompt.reference_image_path:
        print(f"Reference: {prompt.reference_image_path}")

    job = provider.submit_job(prompt, out_dir)
    print(f"Job Status: {job.status.value.upper()} (Job ID: {job.job_id})")
    if job.result_path:
        print(f"Output Video: {job.result_path}")
        print(f"Duration: {job.usage.duration_generated:.2f}s | Credits: {job.usage.credits_used}")
    return 0 if job.status.value == "completed" else 1


def run_voice_cli(args: argparse.Namespace) -> int:
    registry = AIProviderRegistry.get_instance()
    provider = registry.get_voice_provider(args.provider or None)

    prompt = VoicePrompt(
        text=args.text,
        character_name=args.character,
        voice_id=args.voice_id,
        style=args.style,
        rate=args.rate,
        pitch=args.pitch,
    )

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Submitting Voice Job to provider: {provider.provider_name} ({provider.provider_id})")
    print(f"Character: {prompt.character_name} [{prompt.voice_id}] | Text: {prompt.text}")

    job = provider.submit_job(prompt, out_dir)
    print(f"Job Status: {job.status.value.upper()} (Job ID: {job.job_id})")
    if job.result_path:
        print(f"Output Audio: {job.result_path}")
        print(f"Duration: {job.usage.duration_generated:.2f}s | Credits: {job.usage.credits_used}")
    return 0 if job.status.value == "completed" else 1


def run_music_cli(args: argparse.Namespace) -> int:
    registry = AIProviderRegistry.get_instance()
    provider = registry.get_music_provider(args.provider or None)

    prompt_text = args.prompt or f"{args.mood} {args.genre} {'sound effect' if args.sfx else 'music'}"
    prompt = MusicPrompt(
        prompt=prompt_text,
        mood=args.mood,
        genre=args.genre,
        duration_seconds=args.duration,
        is_instrumental=not args.sfx,
        tempo=args.tempo,
        sound_effect=args.sfx,
    )

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Submitting Music/SFX Job to provider: {provider.provider_name} ({provider.provider_id})")
    print(f"Mode: {'Sound Effect' if args.sfx else 'Music'} | Mood: {prompt.mood} | Genre: {prompt.genre}")

    job = provider.submit_job(prompt, out_dir)
    print(f"Job Status: {job.status.value.upper()} (Job ID: {job.job_id})")
    if job.result_path:
        print(f"Output Track: {job.result_path}")
        print(f"Duration: {job.usage.duration_generated:.2f}s | Credits: {job.usage.credits_used}")
    return 0 if job.status.value == "completed" else 1


def run_providers_cli(args: argparse.Namespace) -> int:
    registry = AIProviderRegistry.get_instance()
    mt = None
    if args.type == "video":
        mt = MediaType.VIDEO
    elif args.type == "voice":
        mt = MediaType.VOICE
    elif args.type == "music":
        mt = MediaType.MUSIC

    providers = registry.list_providers(mt)
    print(f"\nRegistered AI Providers ({len(providers)} total):\n")
    print(f"{'Media Type':<12} {'Provider ID':<16} {'Provider Name':<28} {'Available':<10} {'Default'}")
    print("-" * 75)
    for p in providers:
        print(
            f"{p['media_type']:<12} {p['provider_id']:<16} {p['provider_name']:<28} "
            f"{str(p['is_available']):<10} {str(p['is_default'])}"
        )
    print()
    return 0


def run_credentials_cli(args: argparse.Namespace) -> int:
    mgr = AICredentialManager.get_instance()
    if args.cred_action == "set":
        mgr.set_key(args.provider_id, args.api_key)
        print(f"Successfully saved API key for provider '{args.provider_id}'")
        return 0
    elif args.cred_action == "get":
        masked = mgr.get_masked_key(args.provider_id)
        if masked:
            print(f"Provider '{args.provider_id}' key: {masked}")
        else:
            print(f"No key configured for provider '{args.provider_id}'")
        return 0
    elif args.cred_action == "list":
        configured = mgr.list_configured_providers()
        print(f"\nConfigured Provider Credentials ({len(configured)}):")
        for pid in configured:
            print(f"  - {pid}: {mgr.get_masked_key(pid)}")
        print()
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "video":
        return run_video_cli(args)
    elif args.subcommand == "voice":
        return run_voice_cli(args)
    elif args.subcommand == "music":
        return run_music_cli(args)
    elif args.subcommand == "providers":
        return run_providers_cli(args)
    elif args.subcommand == "credentials":
        return run_credentials_cli(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
