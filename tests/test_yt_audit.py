import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-audit" / "SKILL.md"


class YtAuditSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_scope_and_sources_must_be_disclosed(self):
        self.assertIn("State which sources and date range were reviewed", self.content)
        self.assertIn("State the sample size and selection method", self.content)

    def test_public_and_private_analytics_are_distinguished(self):
        self.assertIn("Distinguish public observations from private YouTube Studio analytics", self.content)
        self.assertIn("Do not imply access to a creator's Studio account", self.content)

    def test_no_fixed_video_count_or_forced_voice_profile(self):
        self.assertIn("Do not require a fixed number of videos", self.content)
        self.assertIn("Never create or save a profile unless", self.content)

    def test_no_fabricated_metrics_or_explanations(self):
        self.assertIn("Never invent metrics, results, audience demographics", self.content)
        self.assertIn("Label estimates and inferences", self.content)

    def test_thumbnail_claims_require_visual_source(self):
        self.assertIn("Inspect thumbnails visually only when the image itself is available", self.content)
        self.assertIn("A title list or transcript cannot establish thumbnail readability", self.content)

    def test_hook_score_is_not_retention_measurement(self):
        self.assertIn("editorial heuristic", self.content)
        self.assertIn("not measured retention", self.content)

    def test_transcript_only_review_limits_visual_claims(self):
        self.assertIn("If a transcript alone is supplied", self.content)
        self.assertIn("do not make claims about visual pacing", self.content)

    def test_no_universal_opening_loss_claim(self):
        self.assertIn("Avoid universal claims that a fixed number of seconds", self.content)

    def test_upload_rhythm_does_not_claim_causation(self):
        self.assertIn("without asserting a universal best posting frequency", self.content)
        self.assertIn("Do not claim inconsistency caused poor performance", self.content)

    def test_retention_interpretation_does_not_claim_cause(self):
        self.assertIn("does not by itself prove why", self.content)
        self.assertIn("Pair dips or spikes with the content at those timestamps", self.content)

    def test_findings_separate_observation_evidence_and_interpretation(self):
        for phrase in ("Observation:", "Evidence:", "Interpretation:", "Confidence or limitation:"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.content)

    def test_correlation_is_not_presented_as_causation(self):
        self.assertIn("Do not confuse correlation with causation", self.content)
        self.assertIn("without appropriate comparative evidence", self.content)

    def test_priority_is_evidence_based_and_actionable(self):
        self.assertIn("Identify one highest-priority action when the evidence supports a clear choice", self.content)
        self.assertIn("what signal would indicate whether the change helped", self.content)

    def test_no_forced_three_positives(self):
        self.assertIn("Do not manufacture three positives", self.content)

    def test_missing_evidence_can_be_the_recommendation(self):
        self.assertIn("smallest useful evidence-gathering step", self.content)

    def test_output_discloses_scope_and_unavailable_material(self):
        self.assertIn("Scope and sources:", self.content)
        self.assertIn("what was unavailable", self.content)

    def test_creator_retains_implementation_and_publishing_control(self):
        self.assertIn("Nothing here publishes or changes the channel", self.content)
        self.assertIn("the creator reviews and acts on them", self.content)


if __name__ == "__main__":
    unittest.main()
