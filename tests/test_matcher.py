"""Tests for CandidateJobMatcher scoring system."""
import unittest
from models.candidate import CandidateProfile
from models.job import JobDescription
from services.matcher import CandidateJobMatcher


class TestCandidateJobMatcher(unittest.TestCase):
    def setUp(self):
        self.target_job = JobDescription(
            id="job_test",
            title="Senior Python Backend Engineer",
            description="Looking for a Python Backend Engineer with FastAPI, Docker, and PostgreSQL experience.",
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            preferred_skills=["AWS", "Redis"],
            min_experience_years=4.0
        )

    def test_matcher_perfect_fit(self):
        cand = CandidateProfile(
            id="cand_1",
            file_name="perfect.pdf",
            name="Alex Rivera",
            email="alex@example.com",
            all_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis", "Git"],
            total_experience_years=5.0,
            raw_text="Senior Python Backend Engineer with 5 years experience in FastAPI, Docker, PostgreSQL, AWS, and Redis."
        )

        result = CandidateJobMatcher.match(cand, self.target_job)
        self.assertGreaterEqual(result.overall_score, 80.0)
        self.assertEqual(result.category, "Excellent Match")
        self.assertEqual(result.skills_score, 60.0)
        self.assertEqual(result.experience_score, 20.0)
        self.assertEqual(len(result.matching_required_skills), 4)
        self.assertEqual(len(result.missing_required_skills), 0)

    def test_matcher_partial_fit(self):
        cand = CandidateProfile(
            id="cand_2",
            file_name="partial.pdf",
            name="Junior Dev",
            email="junior@example.com",
            all_skills=["Python", "Git"],
            total_experience_years=2.0,
            raw_text="Junior developer with Python and Git experience."
        )

        result = CandidateJobMatcher.match(cand, self.target_job)
        self.assertLess(result.overall_score, 60.0)
        self.assertIn(result.category, ["Moderate Match", "Low Match"])
        self.assertIn("Python", result.matching_required_skills)
        self.assertIn("PostgreSQL", result.missing_required_skills)
        self.assertEqual(result.experience_score, 10.0)

    def test_matcher_zero_skills_in_job(self):
        job = JobDescription(
            id="job_empty_skills",
            title="General Contributor",
            description="General software development position.",
            required_skills=[],
            preferred_skills=[],
            min_experience_years=0.0
        )
        cand = CandidateProfile(
            id="cand_3",
            file_name="cand3.pdf",
            name="Candidate 3",
            all_skills=["Python"],
            total_experience_years=1.0,
            raw_text="Software developer."
        )
        result = CandidateJobMatcher.match(cand, job)
        self.assertGreaterEqual(result.overall_score, 80.0)
        self.assertEqual(result.category, "Excellent Match")


if __name__ == "__main__":
    unittest.main()
