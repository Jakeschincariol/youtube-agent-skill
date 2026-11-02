import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-seo" / "SKILL.md"


class YtSeoSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_does_not_guarantee_rankings_or_views(self):
        self.assertIn("cannot guarantee rankings, impressions, views", self.content)
        self.assertIn("do not promise that a video will", self.content)

    def test_search_query_opportunities_require_evidence(self):
        self.assertIn("Distinguish researched queries from hypotheses", self.content)
        self.assertIn("Do not invent search volume, difficulty", self.content)
        self.assertIn("candidate searches", self.content)

    def test_does_not_require_three_videos_or_create_voice_profile(self):
        self.assertIn("Do not require three videos", self.content)
        self.assertIn("create/save a profile unless explicitly requested", self.content)

    def test_source_material_and_factual_claims_are_grounded(self):
        self.assertIn("State what source material was actually reviewed", self.content)
        self.assertIn("Never invent statistics, credentials, product features", self.content)
        self.assertIn("mark it clearly for creator review", self.content)

    def test_title_accuracy_and_limit_are_explicit(self):
        self.assertIn("100 characters", self.content)
        self.assertIn("Avoid misleading, sensational, or unsupported claims", self.content)

    def test_description_opening_is_not_overstated(self):
        self.assertIn("display varies by device and context", self.content)
        self.assertIn("not the only text that matters", self.content)
        self.assertNotIn("The first two lines are the only ones anyone reads", self.content)

    def test_description_is_unique_and_within_documented_limit(self):
        self.assertIn("unique description for this specific video", self.content)
        self.assertIn("5,000 characters", self.content)

    def test_no_fabricated_links_or_chapter_timestamps(self):
        self.assertIn("Never invent URLs", self.content)
        self.assertIn("do not fabricate timestamps", self.content)

    def test_tags_are_optional_and_not_arbitrarily_limited(self):
        self.assertIn("common misspellings", self.content)
        self.assertIn("Do not impose an arbitrary quota such as 15 tags", self.content)
        self.assertIn("A short list or no tags", self.content)

    def test_tags_are_not_stuffed_into_description(self):
        self.assertIn("do not stuff them into the description", self.content)
        self.assertIn("unrelated trending terms", self.content)

    def test_queries_must_match_actual_video_content(self):
        self.assertIn("Check that the video genuinely answers the query", self.content)
        self.assertIn("Do not force unrelated phrases", self.content)

    def test_recommendations_are_not_confused_with_proven_opportunities(self):
        self.assertIn("not a ranking prediction", self.content)
        self.assertIn("not arbitrary volume", self.content)

    def test_current_platform_limits_require_official_verification(self):
        self.assertIn("verify the current official upload guidance", self.content)
        self.assertIn("verify official guidance if a strict limit is material", self.content)

    def test_creator_retains_upload_and_publish_control(self):
        self.assertIn("Nothing here uploads or publishes", self.content)
        self.assertIn("creator reviews and enters the metadata", self.content)

    def test_official_references_are_included(self):
        for url in (
            "https://support.google.com/youtube/answer/12948449",
            "https://support.google.com/youtube/answer/16090438",
            "https://support.google.com/youtube/answer/146402",
            "https://support.google.com/youtube/answer/57407",
        ):
            with self.subTest(url=url):
                self.assertIn(url, self.content)


if __name__ == "__main__":
    unittest.main()
