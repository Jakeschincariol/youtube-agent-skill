import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from animatube.ai import (
    AICredentialManager,
    AIGenerationJob,
    AIProviderRegistry,
    GenerationCapability,
    JobStatus,
    MediaType,
    MockMusicProvider,
    MockVideoProvider,
    MockVoiceProvider,
    MusicPrompt,
    UsageMetadata,
    VideoPrompt,
    VoicePrompt,
)


class AIProviderFrameworkTests(unittest.TestCase):
    def test_video_prompt_validation(self):
        # Valid prompt
        vp = VideoPrompt(prompt="Toddler running in preschool playground", aspect_ratio="16:9", duration_seconds=5.0)
        vp.validate()

        # Empty prompt and no reference image
        with self.assertRaises(ValueError):
            VideoPrompt(prompt="   ").validate()

        # Invalid aspect ratio
        with self.assertRaises(ValueError):
            VideoPrompt(prompt="Valid prompt", aspect_ratio="21:9").validate()

        # Out-of-bounds duration
        with self.assertRaises(ValueError):
            VideoPrompt(prompt="Valid prompt", duration_seconds=0.5).validate()
        with self.assertRaises(ValueError):
            VideoPrompt(prompt="Valid prompt", duration_seconds=500.0).validate()

    def test_voice_prompt_validation(self):
        vp = VoicePrompt(text="Welcome to Little Dreamers!", character_name="Aarav")
        vp.validate()

        with self.assertRaises(ValueError):
            VoicePrompt(text="").validate()

    def test_music_prompt_validation(self):
        mp = MusicPrompt(prompt="Cheerful nursery rhyme melody", mood="cheerful", duration_seconds=15.0)
        mp.validate()

        with self.assertRaises(ValueError):
            MusicPrompt(prompt="", mood="", duration_seconds=15.0).validate()

        with self.assertRaises(ValueError):
            MusicPrompt(prompt="Song", duration_seconds=0.0).validate()

    def test_mock_video_provider_job_lifecycle_and_output(self):
        provider = MockVideoProvider()
        self.assertEqual(provider.media_type, MediaType.VIDEO)
        self.assertTrue(provider.capabilities.text_to_video)
        self.assertTrue(provider.capabilities.image_to_video)
        self.assertTrue(provider.capabilities.cancellation_supported)

        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt = VideoPrompt(prompt="Aarav pointing at stars", duration_seconds=2.0)
            job = provider.submit_job(prompt, tmp_dir)

            self.assertEqual(job.status, JobStatus.COMPLETED)
            self.assertEqual(job.progress, 1.0)
            self.assertTrue(Path(job.result_path).is_file())
            self.assertTrue(Path(job.result_path).name.endswith(".mp4"))
            self.assertGreater(job.usage.cost_usd, 0.0)
            self.assertEqual(job.usage.duration_generated, 2.0)

            # Polling job status
            polled = provider.get_job_status(job.job_id)
            self.assertEqual(polled.job_id, job.job_id)

    def test_mock_video_provider_simulated_error(self):
        provider = MockVideoProvider()
        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt = VideoPrompt(prompt="Test error", extra_params={"simulate_error": "API quota exceeded"})
            job = provider.submit_job(prompt, tmp_dir)
            self.assertEqual(job.status, JobStatus.FAILED)
            self.assertIn("quota exceeded", job.error_message)

    def test_mock_video_provider_cancellation(self):
        provider = MockVideoProvider()
        job = AIGenerationJob(media_type=MediaType.VIDEO, provider_id="mock_video", status=JobStatus.PROCESSING)
        provider.jobs[job.job_id] = job

        cancelled = provider.cancel_job(job.job_id)
        self.assertTrue(cancelled)
        self.assertEqual(job.status, JobStatus.CANCELLED)

    def test_mock_voice_provider_output_and_voices(self):
        provider = MockVoiceProvider()
        self.assertEqual(provider.media_type, MediaType.VOICE)
        voices = provider.list_voices()
        self.assertGreaterEqual(len(voices), 6)
        voice_ids = [v["id"] for v in voices]
        self.assertIn("aarav_boy", voice_ids)
        self.assertIn("twinkle_star", voice_ids)

        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt = VoicePrompt(text="Hello Little Dreamers! Let us find the magic star.", voice_id="aarav_boy")
            job = provider.submit_job(prompt, tmp_dir)
            self.assertEqual(job.status, JobStatus.COMPLETED)
            self.assertTrue(Path(job.result_path).is_file())
            self.assertTrue(Path(job.result_path).name.endswith(".wav"))
            self.assertGreater(job.usage.duration_generated, 0.5)

    def test_mock_music_provider_output(self):
        provider = MockMusicProvider()
        self.assertEqual(provider.media_type, MediaType.MUSIC)
        self.assertTrue(provider.capabilities.instrumental_music)

        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt = MusicPrompt(prompt="Lullaby night theme", mood="lullaby", duration_seconds=5.0)
            job = provider.submit_job(prompt, tmp_dir)
            self.assertEqual(job.status, JobStatus.COMPLETED)
            self.assertTrue(Path(job.result_path).is_file())
            self.assertTrue(Path(job.result_path).name.endswith(".wav"))
            self.assertEqual(job.usage.duration_generated, 5.0)

    def test_provider_registry(self):
        registry = AIProviderRegistry()
        video_prov = registry.get_video_provider()
        self.assertIsInstance(video_prov, MockVideoProvider)

        voice_prov = registry.get_voice_provider()
        self.assertIsInstance(voice_prov, MockVoiceProvider)

        music_prov = registry.get_music_provider()
        self.assertIsInstance(music_prov, MockMusicProvider)

        # Listing providers
        all_provs = registry.list_providers()
        self.assertGreaterEqual(len(all_provs), 3)

        # Register custom mock
        custom_prov = MockVideoProvider(provider_id="custom_video", name="Custom Studio")
        registry.register_provider(custom_prov)
        retrieved = registry.get_video_provider("custom_video")
        self.assertEqual(retrieved.provider_id, "custom_video")

    def test_credential_manager(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "ai_creds.json"
            cm = AICredentialManager(config_file=config_file)

            # Initially empty
            self.assertFalse(cm.has_key("luma"))
            self.assertEqual(cm.masked_key("luma"), "")

            # Set key locally
            cm.set_key("luma", "secret_luma_key_123456789")
            self.assertTrue(cm.has_key("luma"))
            self.assertEqual(cm.get_key("luma"), "secret_luma_key_123456789")
            masked = cm.masked_key("luma")
            self.assertTrue(masked.startswith("secr..."))
            self.assertTrue(masked.endswith("6789"))

            # Environment variable takes priority
            with patch.dict(os.environ, {"LUMA_API_KEY": "env_override_key_9999"}):
                self.assertEqual(cm.get_key("luma"), "env_override_key_9999")


if __name__ == "__main__":
    unittest.main()
