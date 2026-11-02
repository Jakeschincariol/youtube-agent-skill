from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import wave
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from animatube.audio.cache import AudioCache
from animatube.audio.edge_tts_wrapper import EdgeTTS
from animatube.audio.human_voice import HumanVoiceImporter, measure_audio_duration
from animatube.audio.mixer import AudioMixer
from animatube.audio.piper_tts import PiperTTS, create_mock_wav, get_wav_duration_seconds
from animatube.audio.speech_preparer import (
    NarrationStyle,
    SpeechPreparer,
    TECHNICAL_PRONUNCIATION_MAP,
)
from animatube.audio.worker import AudioGenerationWorker
from animatube.core.models import Project, Scene
from animatube.export.compiler import (
    CompilationOptions,
    ProbeResult,
    compile_scenes,
    probe_video,
)


class NaturalNarrationAndAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["animatube_audio_tests"])

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory(prefix="animatube_audio_test_")
        self.temp_dir = Path(self.temp_dir_obj.name)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    # -------------------------------------------------------------
    # 1. Speech Preparation & Technical Pronunciation Tests
    # -------------------------------------------------------------

    def test_technical_terminology_pronunciation_normalization(self):
        """Technical terms and acronyms must be expanded for natural pronunciation."""
        preparer = SpeechPreparer(style=NarrationStyle.EDUCATIONAL)

        sample_script = (
            "We will build a CI/CD pipeline using Docker, K8s, and Jenkins on AWS. "
            "We'll configure YAML manifests, set up Nginx reverse proxy, and query a PostgreSQL database."
        )

        normalized = preparer.normalize_technical_terms(sample_script)

        self.assertIn("C-I C-D", normalized)
        self.assertIn("Kubernetes", normalized)
        self.assertIn("A-W-S", normalized)
        self.assertIn("Yam-el", normalized)
        self.assertIn("Engine-X", normalized)
        self.assertIn("Postgres Q-L", normalized)

    def test_natural_pause_insertion_and_sentence_splitting(self):
        """Sentence splitting must preserve abbreviations and insert natural breath pauses."""
        preparer = SpeechPreparer(style=NarrationStyle.EDUCATIONAL)

        text = "DevOps engineers automate deployments, e.g. using Jenkins. Do you want to learn? Yes, start today!"
        sentences = preparer.split_into_sentences(text)

        self.assertEqual(len(sentences), 3)
        self.assertIn("e.g. using Jenkins.", sentences[0])
        self.assertEqual(sentences[1], "Do you want to learn?")
        self.assertEqual(sentences[2], "Yes, start today!")

        # Verify SSML output with break tags
        ssml = preparer.prepare_ssml(text, voice="en-IN-PrabhatNeural")
        self.assertIn('<prosody rate="-5%" pitch="+0Hz">', ssml)
        self.assertIn('<break time="350ms"/>', ssml)
        self.assertIn('<break time="180ms"/>', ssml)
        self.assertTrue(ssml.startswith("<speak"))
        self.assertTrue(ssml.endswith("</speak>"))

    # -------------------------------------------------------------
    # 2. Audio Caching & Zero Regeneration Tests
    # -------------------------------------------------------------

    def test_audio_caching_and_reuse_unchanged_scenes(self):
        """AudioCache must return cached audio without re-synthesis when text/voice is unchanged."""
        cache = AudioCache(cache_dir=self.temp_dir / "cache")

        # Create dummy synthesized audio
        source_wav = self.temp_dir / "source.wav"
        create_mock_wav(source_wav, duration_seconds=3.2)

        cache.put(
            text="Welcome to DevOps 2027",
            source_audio_path=source_wav,
            duration=3.2,
            voice="en-IN-PrabhatNeural",
            style="educational",
            engine="edge_tts",
        )

        # Lookup with exact match
        found = cache.get(
            text="Welcome to DevOps 2027",
            voice="en-IN-PrabhatNeural",
            style="educational",
            engine="edge_tts",
            extension=".wav",
        )
        self.assertIsNotNone(found)
        cached_file, cached_duration = found
        self.assertTrue(cached_file.is_file())
        self.assertAlmostEqual(cached_duration, 3.2, places=1)

        # Lookup with altered text must miss cache
        miss = cache.get(
            text="Welcome to DevOps 2028 (Modified)",
            voice="en-IN-PrabhatNeural",
            style="educational",
            engine="edge_tts",
            extension=".wav",
        )
        self.assertIsNone(miss)

    # -------------------------------------------------------------
    # 3. Human Voice Recording Support Tests
    # -------------------------------------------------------------

    def test_human_voice_import_validation_and_timeline_sync(self):
        """Human voice importer must validate formats, measure duration and synchronize timeline."""
        importer = HumanVoiceImporter()

        # Create human recording dummy WAV
        human_raw = self.temp_dir / "human_voice.wav"
        create_mock_wav(human_raw, duration_seconds=4.5)

        # Validate format
        validated = importer.validate_format(human_raw)
        self.assertEqual(validated, human_raw.resolve())

        # Unsupported format raises ValueError
        invalid_file = self.temp_dir / "recording.txt"
        invalid_file.write_text("not audio", encoding="utf-8")
        with self.assertRaises(ValueError):
            importer.validate_format(invalid_file)

        # Process recording
        dest = self.temp_dir / "processed_human.wav"
        processed_path, duration = importer.process_recording(human_raw, dest)
        self.assertTrue(processed_path.is_file())
        self.assertAlmostEqual(duration, 4.5, places=1)

        # Test Timeline synchronization with grace margin (+0.35s)
        scene = Scene(name="Introduction", duration_frames=30)
        frames = HumanVoiceImporter.sync_scene_duration(scene, duration, fps=30, tail_grace_seconds=0.35)
        expected_frames = int(round((4.5 + 0.35) * 30))
        self.assertEqual(scene.duration_frames, expected_frames)
        self.assertEqual(frames, expected_frames)

    def test_silence_trim_preserves_original_when_filter_outputs_empty_audio(self):
        """An empty FFmpeg result must fall back to the source take and its duration."""
        source = self.temp_dir / "silent_source.wav"
        create_mock_wav(source, duration_seconds=4.5)
        destination = self.temp_dir / "trimmed_empty.wav"
        importer = HumanVoiceImporter(ffmpeg_path="ffmpeg")

        def write_empty_output(cmd, *args, **kwargs):
            output = Path(cmd[-1])
            with wave.open(str(output), "wb") as wav_file:
                wav_file.setnchannels(2)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(b"")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        with patch("animatube.audio.human_voice.subprocess.run", side_effect=write_empty_output):
            processed_path, duration = importer.process_recording(source, destination)

        self.assertEqual(processed_path, destination.resolve())
        self.assertAlmostEqual(duration, 4.5, places=1)
        self.assertEqual(destination.read_bytes(), source.read_bytes())

    # -------------------------------------------------------------
    # 4. Background Music & Mixing Tests
    # -------------------------------------------------------------

    def test_audio_mixer_voice_and_music_ratios(self):
        """Audio mixer must mix voice and music while keeping music volume lower."""
        mixer = AudioMixer()

        narr_file = self.temp_dir / "narration.wav"
        music_file = self.temp_dir / "music.wav"
        create_mock_wav(narr_file, duration_seconds=5.0)
        create_mock_wav(music_file, duration_seconds=10.0)

        out_mix = self.temp_dir / "mixed_output.wav"
        result = mixer.mix(
            narr_file,
            out_mix,
            music_path=music_file,
            narration_volume=1.0,
            music_volume=0.15,
            target_duration_seconds=5.0,
        )

        self.assertTrue(result.is_file())
        self.assertGreater(result.stat().st_size, 0)

    # -------------------------------------------------------------
    # 5. Background Worker Responsiveness & Cancellation Tests
    # -------------------------------------------------------------

    def test_audio_generation_worker_cancellation(self):
        """Worker must handle cooperative cancellation gracefully without freezing UI."""
        s1 = Scene(name="Scene 1", duration_frames=60)
        s2 = Scene(name="Scene 2", duration_frames=60)
        s3 = Scene(name="Scene 3", duration_frames=60)

        worker = AudioGenerationWorker(
            scenes=[s1, s2, s3],
            output_dir=self.temp_dir / "worker_out",
            cache_dir=self.temp_dir / "cache",
        )

        cancelled_events = []
        worker.cancelled.connect(lambda: cancelled_events.append(True))

        # Cancel immediately before or during start
        worker.cancel()
        worker.run()

        self.assertTrue(len(cancelled_events) > 0)

    # -------------------------------------------------------------
    # 6. Full Compilation with Audio & FFprobe Stream Validation
    # -------------------------------------------------------------

    def test_compile_scenes_with_audio_and_probe_validation(self):
        """compile_scenes with audio_path must mux AAC audio and validate both video and audio streams."""
        s1 = Scene(name="S1", duration_frames=30)
        proj = Project(fps=30, scenes=[s1])

        audio_track = self.temp_dir / "master.wav"
        create_mock_wav(audio_track, duration_seconds=1.0)

        def fake_run(cmd, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = ""
            mock_res.stderr = ""
            target_arg = cmd[-1]
            if isinstance(target_arg, str) and (target_arg.endswith(".mp4") or "normalized" in target_arg or "muxed" in target_arg):
                Path(target_arg).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")

            if "ffprobe" in str(cmd[0]):
                data = {
                    "streams": [
                        {
                            "codec_type": "video",
                            "codec_name": "h264",
                            "width": 1920,
                            "height": 1080,
                            "r_frame_rate": "30/1",
                            "duration": "1.0",
                        },
                        {
                            "codec_type": "audio",
                            "codec_name": "aac",
                            "sample_rate": "44100",
                            "channels": 2,
                            "duration": "1.0",
                        },
                    ],
                    "format": {"duration": "1.0", "size": "1048576"},
                }
                mock_res.stdout = json.dumps(data)
            return mock_res

        class FakePopen:
            def __init__(self, cmd, *args, **kwargs):
                self.stdin = MagicMock()
                self.stderr = MagicMock()
                target_file = cmd[-1]
                Path(target_file).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")

            def wait(self):
                return 0

            def poll(self):
                return 0

        opts = CompilationOptions(
            width=1920,
            height=1080,
            fps=30,
            audio_path=audio_track,
            ffmpeg_path="ffmpeg",
            ffprobe_path="ffprobe",
        )

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with patch("animatube.export.compiler.get_ffprobe_executable", return_value="ffprobe"):
                with patch("subprocess.run", side_effect=fake_run):
                    with patch("subprocess.Popen", side_effect=FakePopen):
                        dest = self.temp_dir / "final_with_audio.mp4"
                        out_path = compile_scenes(proj, dest, options=opts)

                        self.assertTrue(out_path.is_file())
                        probe = probe_video(out_path, ffprobe_executable="ffprobe")
                        self.assertTrue(probe.has_video_stream)
                        self.assertTrue(probe.has_audio_stream)
                        self.assertEqual(probe.audio_codec, "aac")
                        self.assertEqual(probe.sample_rate, 44100)
                        self.assertEqual(probe.channels, 2)

    def test_missing_voice_models_fallback_handling(self):
        """When voice model is not configured, PiperTTS falls back gracefully or errors if disabled."""
        tts = PiperTTS(executable_path=None, model_path=None)
        target = self.temp_dir / "fallback.wav"

        # allow_fallback=True must generate valid WAV without crashing
        dur = tts.synthesize("Welcome to the video", target, allow_fallback=True)
        self.assertTrue(target.is_file())
        self.assertGreater(dur, 0.5)

        # allow_fallback=False must raise RuntimeError
        target_err = self.temp_dir / "err.wav"
        with self.assertRaises(RuntimeError):
            tts.synthesize("Welcome to the video", target_err, allow_fallback=False)

    def test_narration_styles_prosody_configs(self):
        """Educational, conversational and professional styles must produce distinct rate/pitch configurations."""
        preparer = SpeechPreparer()
        text = "Hello DevOps"

        ssml_edu = preparer.prepare_ssml(text, style=NarrationStyle.EDUCATIONAL)
        ssml_conv = preparer.prepare_ssml(text, style=NarrationStyle.CONVERSATIONAL)
        ssml_prof = preparer.prepare_ssml(text, style=NarrationStyle.PROFESSIONAL)

        self.assertIn('rate="-5%"', ssml_edu)
        self.assertIn('rate="+0%"', ssml_conv)
        self.assertIn('rate="-2%"', ssml_prof)

    def test_audio_studio_dialog_headless_instantiation(self):
        """AudioStudioDialog must initialize tabs, controls and scene table cleanly."""
        from animatube.ui.audio_studio_dialog import AudioStudioDialog
        proj = Project(name="Test Audio Project", scenes=[
            Scene(name="Intro Scene", duration_frames=60),
            Scene(name="Tools Scene", duration_frames=90),
        ])

        dialog = AudioStudioDialog(proj)
        self.assertEqual(dialog.tabs.count(), 3)
        self.assertEqual(dialog.table_scenes.rowCount(), 2)
        self.assertTrue(dialog.btn_generate_all.isEnabled())
        dialog.close()


if __name__ == "__main__":
    unittest.main()
