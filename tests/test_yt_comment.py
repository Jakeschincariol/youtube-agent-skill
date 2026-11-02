import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-comment" / "SKILL.md"


class YtCommentSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_voice_profile_is_optional_and_not_created_implicitly(self):
        self.assertIn("Do not require three videos", self.content)
        self.assertIn("create or save a file unless the creator explicitly asks", self.content)

    def test_requires_evidence_for_factual_replies(self):
        self.assertIn("Never invent a number, result, source", self.content)
        self.assertIn("say what is unknown", self.content)

    def test_four_triage_categories_are_preserved(self):
        for category in ("Questions", "Corrections", "Praise", "Bait / no-reply"):
            with self.subTest(category=category):
                self.assertIn(category, self.content)

    def test_empty_or_non_thread_input_does_not_get_fake_counts(self):
        self.assertIn("contains no comments", self.content)
        self.assertIn("do not fabricate counts", self.content)

    def test_safety_moderation_is_separate_from_bait(self):
        self.assertIn("Safety and moderation pass", self.content)
        self.assertIn("Keep safety/moderation flags separate", self.content)
        self.assertIn("ordinary disagreement", self.content)

    def test_private_information_is_not_repeated(self):
        self.assertIn("Do not reveal or repeat private information", self.content)
        self.assertIn("do not quote it in the reply", self.content)

    def test_does_not_claim_to_take_platform_actions(self):
        self.assertIn("Do not engage with threats or harassment", self.content)
        self.assertIn("claim that you have moderated, reported, hidden, or blocked anything", self.content)
        self.assertIn("creator makes those decisions in YouTube", self.content)

    def test_no_unapproved_promises_or_off_platform_pressure(self):
        self.assertIn("unless the creator has explicitly approved", self.content)
        self.assertIn("Do not pressure viewers to share personal information", self.content)

    def test_pin_is_optional_and_reasoned(self):
        self.assertIn("If none stands out, say no pin is recommended", self.content)
        self.assertIn("Suggest a comment to heart or pin only when", self.content)

    def test_replies_prioritize_quality_over_arbitrary_word_limit(self):
        self.assertIn("Accuracy and a natural response matter more", self.content)
        self.assertIn("Aim for fewer than 30 words", self.content)

    def test_drafts_remain_reviewed_by_creator(self):
        self.assertIn("The creator reviews every draft", self.content)
        self.assertIn("Nothing here publishes or moderates", self.content)


if __name__ == "__main__":
    unittest.main()
