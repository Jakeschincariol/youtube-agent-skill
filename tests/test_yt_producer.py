import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-producer" / "SKILL.md"


class YtProducerSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_declares_orchestrator_and_not_a_replacement(self):
        self.assertIn("name: yt-producer", self.content)
        self.assertIn("not a replacement for the specialist skills", self.content)
        self.assertIn("never run every skill by default", self.content)

    def test_routes_all_eleven_specialist_skills(self):
        for name in (
            "yt-plan", "yt-script", "yt-package", "yt-seo", "yt-edit",
            "yt-chapters", "yt-shorts", "yt-retention", "yt-audit",
            "yt-viral", "yt-comment",
        ):
            with self.subTest(skill=name):
                self.assertIn(f"`{name}`", self.content)

    def test_routing_covers_source_boundaries(self):
        for phrase in (
            "Timestamped SRT, VTT", "retention export", "actual comments",
            "timestamped transcript", "public/creator-supplied material",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), self.content.lower())

    def test_new_video_sequence_is_optional_and_ordered(self):
        self.assertIn("### New video from an idea", self.content)
        self.assertIn("Use `yt-plan` only if", self.content)
        self.assertIn("Use `yt-script`", self.content)
        self.assertIn("Use `yt-package`", self.content)
        self.assertIn("Use `yt-seo`", self.content)

    def test_existing_recording_route_requires_source_material(self):
        self.assertIn("### Existing recording or long-form video", self.content)
        self.assertIn("when a timestamped transcript exists", self.content)
        self.assertIn("supplied source material", self.content)

    def test_published_video_route_requires_analytics_evidence(self):
        self.assertIn("### Published-video improvement", self.content)
        self.assertIn("compatible retention export is supplied", self.content)

    def test_handoffs_preserve_evidence_and_creator_context(self):
        self.assertIn("Preserve handoffs between skills", self.content)
        self.assertIn("Verified facts and their sources", self.content)
        self.assertIn("Do not turn an earlier draft into verified evidence", self.content)

    def test_missing_specialist_is_not_claimed_as_executed(self):
        self.assertIn("If a specialist skill is unavailable", self.content)
        self.assertIn("Do not claim that it ran", self.content)

    def test_stages_are_reviewable_and_require_meaningful_approval(self):
        self.assertIn("Execute in small, reviewable stages", self.content)
        self.assertIn("Continue only to the next relevant stage", self.content)
        self.assertIn("never silently override a creator decision", self.content)

    def test_publication_and_channel_actions_are_out_of_scope(self):
        self.assertIn("Nothing in this orchestrator uploads, publishes, schedules", self.content)
        self.assertIn("The creator retains control", self.content)
        self.assertIn("Do not request account passwords", self.content)

    def test_does_not_invent_missing_assets_or_metrics(self):
        self.assertIn("Do not invent a missing transcript", self.content)
        self.assertIn("metric, link or timestamp", self.content)

    def test_final_handoff_summarizes_next_decision(self):
        self.assertIn("single next creator decision", self.content)
        self.assertIn("ship it, or change it?", self.content)


if __name__ == "__main__":
    unittest.main()
