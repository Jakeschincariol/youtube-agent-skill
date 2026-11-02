import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-shorts" / "SKILL.md"


class YtShortsSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_source_and_timecodes_must_be_grounded(self):
        self.assertIn("Never invent timestamps", self.content)
        self.assertIn("source duration", self.content)
        self.assertIn("timecode origin is unknown", self.content)

    def test_transcript_only_limits_visual_claims(self):
        self.assertIn("If only a transcript is supplied", self.content)
        self.assertIn("cannot be verified", self.content)

    def test_platform_duration_is_not_hard_coded_as_a_rule(self):
        self.assertIn("Do not hard-code a supposedly universal platform duration limit", self.content)
        self.assertIn("official platform guidance", self.content)

    def test_standalone_context_and_complete_payoff_are_required(self):
        self.assertIn("A standalone opening", self.content)
        self.assertIn("A satisfying ending", self.content)
        self.assertIn("missing question", self.content)

    def test_clips_must_preserve_original_meaning(self):
        self.assertIn("Faithful meaning", self.content)
        self.assertIn("remove a necessary disclaimer", self.content)
        self.assertIn("Do not splice separate statements", self.content)

    def test_candidate_count_is_not_fabricated(self):
        self.assertIn("Do not manufacture five candidates", self.content)
        self.assertIn("fewer than five qualify", self.content)

    def test_duration_window_is_advisory_not_mandatory(self):
        self.assertIn("20–55 second span", self.content)
        self.assertIn("not a platform rule or a required duration", self.content)

    def test_ranking_is_editorial_not_predictive(self):
        self.assertIn("explicit editorial reasons", self.content)
        self.assertIn("Do not imply that this ranking predicts views, retention, virality, or reach", self.content)

    def test_candidate_briefs_include_source_boundaries_and_caveats(self):
        for field in ("source in/out timecodes", "first spoken line", "viewer payoff",
                      "missing context", "approximate"):
            with self.subTest(field=field):
                self.assertIn(field, self.content)

    def test_package_contains_hook_overlay_ending_and_framing(self):
        for field in ("New opening", "On-screen text", "Payoff / ending",
                      "Vertical framing note", "Review flags"):
            with self.subTest(field=field):
                self.assertIn(field, self.content)

    def test_hookscore_is_described_as_a_heuristic(self):
        self.assertIn("hookscore.py --hook", self.content)
        self.assertIn("not a performance prediction", self.content)

    def test_rights_privacy_and_safety_are_flagged(self):
        self.assertIn("rights, privacy, safety, music", self.content)
        self.assertIn("Do not declare a clip legally cleared", self.content)

    def test_no_editing_or_publishing_claims(self):
        self.assertIn("does not edit, render, upload, schedule, or publish", self.content)
        self.assertIn("creator reviews the cut", self.content)


if __name__ == "__main__":
    unittest.main()
