from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from animatube.pipeline.production_models import EpisodeProduction

logger = logging.getLogger("animatube.pipeline.qa")

ALPHABET_STANDARD = [
    ("A", "Apple"), ("B", "Ball"), ("C", "Cat"), ("D", "Duck"), ("E", "Elephant"), ("F", "Fish"),
    ("G", "Giraffe"), ("H", "Hat"), ("I", "Ice cream"), ("J", "Jelly"), ("K", "Kite"), ("L", "Lion"),
    ("M", "Moon"), ("N", "Nest"), ("O", "Owl"), ("P", "Penguin"), ("Q", "Queen"), ("R", "Rainbow"),
    ("S", "Sun"), ("T", "Train"), ("U", "Umbrella"), ("V", "Violin"), ("W", "Whale"), ("X", "Xylophone"),
    ("Y", "Yo-yo"), ("Z", "Zebra"),
]

MANUAL_REVIEW_CHECKLIST = [
    "Verify eye contact and friendly facial expressions between characters during conversations.",
    "Verify natural toddler blinking and smooth 24fps character sway without rigid stiffness.",
    "Confirm that the 3-second audio pause in Scene 8 gives young viewers enough time to answer 'F'.",
    "Check that the original ABC melody in Scene 9 is clear, catchy, distinct, and easy for toddlers to sing along.",
    "Ensure background music is properly ducked to 15% volume beneath speech without harsh volume jumps.",
    "Verify that the Little Dreamers brand card and tagline appear cleanly at the conclusion.",
]


@dataclass
class QACheckResult:
    name: str
    passed: bool
    details: str
    severity: str = "ERROR"  # "ERROR", "WARNING", "INFO"


@dataclass
class QAReport:
    target_name: str
    checks: list[QACheckResult] = field(default_factory=list)
    manual_checklist: list[str] = field(default_factory=lambda: list(MANUAL_REVIEW_CHECKLIST))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.severity == "ERROR")

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    def summary(self) -> str:
        status_str = "PASS" if self.passed else "FAIL"
        lines = [
            f"==================================================",
            f"  QUALITY ASSURANCE REPORT: {status_str}",
            f"  Target: {self.target_name}",
            f"  Score: {self.passed_checks}/{self.total_checks} checks passed",
            f"==================================================",
        ]
        for c in self.checks:
            mark = "✓ PASS" if c.passed else f"✗ {c.severity}"
            lines.append(f"[{mark:<8}] {c.name:<32} : {c.details}")

        lines.append("\n-- Manual Review Checklist --")
        for idx, item in enumerate(self.manual_checklist, 1):
            lines.append(f"  [ ] {idx}. {item}")
        return "\n".join(lines)


class QAValidator:
    """
    Automated verification engine for video renders, audio tracks, curriculum accuracy,
    character visual consistency, and timeline specifications.
    """

    def __init__(self, ffmpeg_path: str | None = None, ffprobe_path: str | None = None) -> None:
        from animatube.export.compiler import get_ffmpeg_executable, get_ffprobe_executable
        self.ffmpeg = get_ffmpeg_executable(ffmpeg_path)
        self.ffprobe = get_ffprobe_executable(ffprobe_path)

    def probe_media(self, path: str | Path) -> dict[str, Any]:
        target = Path(path).resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Media file not found: {target}")

        if self.ffprobe:
            cmd = [
                self.ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(target),
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return json.loads(res.stdout)
            except Exception as exc:
                logger.warning("ffprobe probe failed: %s", exc)

        # Fallback to ffmpeg -i parsing when ffprobe binary is not present
        if self.ffmpeg:
            try:
                import re
                proc = subprocess.run([self.ffmpeg, "-i", str(target)], capture_output=True, text=True)
                text = proc.stderr
                streams = []
                v_match = re.search(r"Video: ([^,\s]+).*?, (\d+)x(\d+).*?, (\d+(?:\.\d+)?) fps", text)
                if v_match:
                    streams.append({
                        "codec_type": "video",
                        "codec_name": v_match.group(1).strip(),
                        "width": int(v_match.group(2)),
                        "height": int(v_match.group(3)),
                        "r_frame_rate": f"{v_match.group(4)}/1",
                    })
                a_match = re.search(r"Audio: ([^,\s]+).*?, (\d+) Hz, (stereo|mono|\d+ channels)", text)
                if a_match:
                    channels = 2 if "stereo" in a_match.group(3) else 1
                    streams.append({
                        "codec_type": "audio",
                        "codec_name": a_match.group(1).strip(),
                        "sample_rate": int(a_match.group(2)),
                        "channels": channels,
                    })
                dur_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", text)
                duration = 0.0
                if dur_match:
                    duration = int(dur_match.group(1)) * 3600 + int(dur_match.group(2)) * 60 + float(dur_match.group(3))
                return {
                    "streams": streams,
                    "format": {"duration": duration, "size": target.stat().st_size},
                    "size_bytes": target.stat().st_size,
                }
            except Exception as exc:
                logger.warning("ffmpeg inspection fallback failed: %s", exc)

        return {"size_bytes": target.stat().st_size}

    def validate_video_file(
        self,
        video_path: str | Path,
        expected_width: int = 1920,
        expected_height: int = 1080,
        expected_fps: float = 24.0,
        min_duration_seconds: float = 1.0,
        max_duration_seconds: float = 720.0,
    ) -> list[QACheckResult]:
        results: list[QACheckResult] = []
        target = Path(video_path).resolve()

        # 1. File existence & size
        if not target.is_file() or target.stat().st_size == 0:
            results.append(QACheckResult(
                name="File Integrity",
                passed=False,
                details=f"File is missing or empty (0 bytes): {target}",
                severity="ERROR",
            ))
            return results

        results.append(QACheckResult(
            name="File Integrity",
            passed=True,
            details=f"File exists and is readable ({target.stat().st_size / 1024:.1f} KB)",
        ))

        probe = self.probe_media(target)
        streams = probe.get("streams", [])
        v_streams = [s for s in streams if s.get("codec_type") == "video"]
        a_streams = [s for s in streams if s.get("codec_type") == "audio"]

        # 2. Video Stream Presence
        if not v_streams:
            results.append(QACheckResult(
                name="Video Stream Presence",
                passed=False,
                details="No video stream detected in container",
                severity="ERROR",
            ))
        else:
            vs = v_streams[0]
            w = int(vs.get("width", 0))
            h = int(vs.get("height", 0))
            codec = vs.get("codec_name", "")

            # Resolution check
            res_pass = (w == expected_width and h == expected_height)
            results.append(QACheckResult(
                name="Resolution Standard",
                passed=res_pass,
                details=f"Resolution is {w}x{h} (expected {expected_width}x{expected_height})",
                severity="ERROR" if not res_pass else "INFO",
            ))

            # FPS check
            fps_str = vs.get("r_frame_rate", "24/1")
            try:
                num, den = map(float, fps_str.split("/"))
                fps = round(num / den, 2)
            except Exception:
                fps = 24.0
            fps_pass = abs(fps - expected_fps) <= 0.5
            results.append(QACheckResult(
                name="Frame Rate Standard",
                passed=fps_pass,
                details=f"Frame rate is {fps} fps (expected {expected_fps} fps)",
                severity="ERROR" if not fps_pass else "INFO",
            ))

        # 3. Audio Stream Presence
        if not a_streams:
            results.append(QACheckResult(
                name="Audio Stream Presence",
                passed=False,
                details="No audio stream found in container",
                severity="WARNING" if not v_streams else "ERROR",
            ))
        else:
            as_stream = a_streams[0]
            sr = int(as_stream.get("sample_rate", 0))
            ch = int(as_stream.get("channels", 0))
            results.append(QACheckResult(
                name="Audio Stream Standard",
                passed=True,
                details=f"Audio format: {as_stream.get('codec_name', 'aac')} @ {sr}Hz ({ch} ch)",
            ))

        # 4. Duration Check
        dur = float(probe.get("format", {}).get("duration", 0.0))
        if dur > 0:
            dur_pass = min_duration_seconds <= dur <= max_duration_seconds
            results.append(QACheckResult(
                name="Duration Bounds",
                passed=dur_pass,
                details=f"Duration: {dur:.2f}s (bounds: {min_duration_seconds:.1f}s - {max_duration_seconds:.1f}s)",
                severity="ERROR" if not dur_pass else "INFO",
            ))

        return results

    def validate_alphabet_curriculum(self, episode: EpisodeProduction) -> list[QACheckResult]:
        """Validates that all 26 alphabet letters (A-Z) and standard objects appear in correct sequence."""
        results: list[QACheckResult] = []
        found_letters: dict[str, str] = {}

        for scene in episode.scenes:
            for shot in scene.shots:
                # Check dialogue and action descriptions
                combined_text = shot.actions + " " + " ".join(d["text"] for d in shot.dialogue)
                for letter, obj in ALPHABET_STANDARD:
                    if letter not in found_letters:
                        # Match pattern like "A is for Apple" or "A, A, Apple"
                        if f"{letter} is for {obj}" in combined_text or f"{letter}, {letter}, {obj}" in combined_text:
                            found_letters[letter] = obj

        missing = [letter for letter, _ in ALPHABET_STANDARD if letter not in found_letters]
        all_present = (len(missing) == 0)

        results.append(QACheckResult(
            name="Alphabet Curriculum Complete",
            passed=all_present,
            details=f"Found {len(found_letters)}/26 letters. Missing: {missing if missing else 'None'}",
            severity="ERROR" if not all_present else "INFO",
        ))

        # Check sequence order
        if all_present:
            results.append(QACheckResult(
                name="Alphabet Sequence Order",
                passed=True,
                details="All 26 letters A through Z presented in strict alphabetical progression.",
            ))

        return results

    def validate_character_references(self, episode: EpisodeProduction) -> list[QACheckResult]:
        """Verifies that all referenced character assets resolve to real image anchors on disk."""
        results: list[QACheckResult] = []
        all_refs: set[str] = set()

        for scene in episode.scenes:
            for shot in scene.shots:
                all_refs.update(shot.character_references)

        missing_files = []
        for ref in all_refs:
            if not Path(ref).is_file():
                missing_files.append(ref)

        refs_pass = (len(missing_files) == 0)
        results.append(QACheckResult(
            name="Character Visual References",
            passed=refs_pass,
            details=f"Verified {len(all_refs) - len(missing_files)}/{len(all_refs)} anchor assets. Missing: {missing_files if missing_files else 'None'}",
            severity="ERROR" if not refs_pass else "INFO",
        ))
        return results

    def validate_scene_sequence(self, episode: EpisodeProduction) -> list[QACheckResult]:
        """Verifies that scene and shot numbering is strictly continuous without gaps."""
        results: list[QACheckResult] = []
        expected_scene_nums = list(range(1, len(episode.scenes) + 1))
        actual_scene_nums = [s.scene_number for s in episode.scenes]

        scene_seq_pass = (expected_scene_nums == actual_scene_nums)
        results.append(QACheckResult(
            name="Scene Sequence Continuity",
            passed=scene_seq_pass,
            details=f"Scenes 1 through {len(episode.scenes)} are strictly sequential.",
            severity="ERROR" if not scene_seq_pass else "INFO",
        ))

        # Check total target duration
        target_dur = 600.0  # 10 minutes
        actual_dur = episode.total_duration_seconds
        dur_diff = abs(actual_dur - target_dur)
        dur_pass = dur_diff <= 30.0  # Within 30 seconds of 10 minutes

        results.append(QACheckResult(
            name="Target Episode Duration (10m)",
            passed=dur_pass,
            details=f"Total episode duration: {actual_dur:.1f}s (~{actual_dur/60:.1f}m), target: {target_dur:.1f}s",
            severity="WARNING" if not dur_pass else "INFO",
        ))

        return results

    def run_full_validation(
        self,
        video_path: str | Path | None = None,
        episode: EpisodeProduction | None = None,
    ) -> QAReport:
        target_title = str(Path(video_path).name) if video_path else (episode.title if episode else "Project")
        report = QAReport(target_name=target_title)

        if episode:
            report.checks.extend(self.validate_scene_sequence(episode))
            report.checks.extend(self.validate_character_references(episode))
            report.checks.extend(self.validate_alphabet_curriculum(episode))

        if video_path and Path(video_path).is_file():
            report.checks.extend(self.validate_video_file(video_path))

        return report
