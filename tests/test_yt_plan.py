import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yt-plan" / "SKILL.md"


class YtPlanSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_supports_weekly_and_monthly_planning(self):
        self.assertIn("week or month", self.content.lower())
        self.assertIn("For a monthly plan", self.content)

    def test_does_not_impose_fixed_upload_quota(self):
        self.assertIn("never impose an upload quota", self.content)
        self.assertIn("There is no default", self.content)
        self.assertNotIn("Three uploads on a seven-day week", self.content)

    def test_capacity_budget_and_effort_are_explicit(self):
        self.assertIn("available production hours", self.content)
        self.assertIn("sum the estimates", self.content)
        self.assertIn("capacity gap", self.content)
        self.assertIn("silently overbooking", self.content)

    def test_existing_assets_must_be_verified(self):
        self.assertIn("Identify work already in progress", self.content)
        self.assertIn("Do not count an idea", self.content)
        self.assertIn("reused assets actually exist", self.content)

    def test_shorts_are_optional_and_require_source_material(self):
        self.assertIn("only when a transcript or source video exists", self.content)
        self.assertIn("Do not invent clips, timestamps", self.content)

    def test_analytics_recommendations_require_evidence(self):
        self.assertIn("supplied channel analytics", self.content)
        self.assertIn("not performance-based recommendations", self.content)
        self.assertIn("Never invent metrics, audience insights", self.content)

    def test_calendar_has_production_and_dependency_fields(self):
        for heading in (
            "Publish date / target", "Format", "Viewer promise", "Asset status",
            "Production effort", "Dependencies / priority",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_over_capacity_plan_must_defer_work(self):
        self.assertIn("show the shortfall", self.content)
        self.assertIn("propose what to defer", self.content)
        self.assertIn("first item or task to defer", self.content)

    def test_does_not_require_voice_profile_to_proceed(self):
        self.assertIn("Do not require three videos or block planning", self.content)


if __name__ == "__main__":
    unittest.main()
