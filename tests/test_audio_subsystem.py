from pathlib import Path
import tempfile
import unittest

from animatube.audio.piper_tts import (
    PiperTTS,
    create_mock_wav,
    get_wav_duration_seconds,
)
from animatube.audio.subtitles import (
    SubtitleGenerator,
    format_timestamp_srt,
    format_timestamp_vtt,
    generate_subtitles_from_text,
)


class AudioSubsystemTests(unittest.TestCase):
    def test_mock_wav_and_duration_reading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = Path(temp_dir) / "test.wav"
            dur = create_mock_wav(wav_path, duration_seconds=2.5, sample_rate=16000)
            self.assertAlmostEqual(dur, 2.5, places=2)

            measured = get_wav_duration_seconds(wav_path)
            self.assertAlmostEqual(measured, 2.5, places=2)

    def test_piper_tts_fallback_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = Path(temp_dir) / "narration.wav"
            tts = PiperTTS()
            self.assertFalse(tts.is_available())

            text = "Why are you wasting your next six months before learning what five DevOps tools actually matter in 2027?"
            duration = tts.synthesize(text, wav_path, words_per_minute=150.0, allow_fallback=True)
            self.assertTrue(wav_path.is_file())
            # 17 words at 150 wpm = (17/150)*60 = 6.8 seconds
            self.assertAlmostEqual(duration, 6.8, delta=0.5)

    def test_timestamp_formatting(self):
        self.assertEqual(format_timestamp_srt(0.0), "00:00:00,000")
        self.assertEqual(format_timestamp_srt(65.5), "00:01:05,500")
        self.assertEqual(format_timestamp_vtt(3661.125), "01:01:01.125")

    def test_subtitles_from_text_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            srt_path = Path(temp_dir) / "subs.srt"
            text = "Welcome to this complete DevOps roadmap for Indian freshers and beginners."
            generate_subtitles_from_text(text, duration_seconds=5.0, output_path=srt_path, words_per_cue=4)

            self.assertTrue(srt_path.is_file())
            content = srt_path.read_text(encoding="utf-8")
            self.assertIn("1\n00:00:00,000 -->", content)
            self.assertIn("Welcome to this complete", content)

    def test_subtitle_generator_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = Path(temp_dir) / "speech.wav"
            create_mock_wav(wav_path, duration_seconds=3.0)

            srt_path = Path(temp_dir) / "output.srt"
            gen = SubtitleGenerator()
            self.assertFalse(gen.is_available())

            gen.generate(
                audio_path=wav_path,
                output_srt_path=srt_path,
                reference_text="This is a test subtitle generation.",
                duration_seconds=3.0,
                allow_fallback=True,
            )
            self.assertTrue(srt_path.is_file())
            content = srt_path.read_text(encoding="utf-8")
            self.assertIn("This is a test", content)


if __name__ == "__main__":
    unittest.main()
